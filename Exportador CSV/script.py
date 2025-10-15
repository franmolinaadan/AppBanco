import pdfplumber
import pandas as pd
import re
import os
from pathlib import Path
import glob
from datetime import datetime
import glob


def extract_bank_data_from_pdf(pdf_path):
    """
    Extrae datos de transacciones de un PDF bancario - VERSIÓN CORREGIDA
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            all_lines = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    lines = text.split('\n')
                    all_lines.extend(lines)

            full_text = '\n'.join(all_lines)
    except Exception as e:
        print(f"Error al abrir el PDF {pdf_path}: {e}")
        return []

    transactions = []
    lines = [line.strip() for line in all_lines if line.strip()]

    # EXTRAER MES Y AÑO CORRECTAMENTE del contenido del PDF
    month_year = extract_month_year_from_content(full_text)
    print(f"  Mes detectado: {month_year['month']}, Año: {month_year['year']}")

    # Encontrar sección de transacciones
    transaction_start = None
    for i, line in enumerate(lines):
        if "SALDOANTERIOR" in line.replace(" ", ""):
            transaction_start = i + 1
            break

    if transaction_start is None:
        print(f"  No se encontró sección de transacciones en {pdf_path}")
        return []

    # Procesar transacciones - FLUJO CORREGIDO
    i = transaction_start
    while i < len(lines):
        line = lines[i]

        # MEJOR FILTRADO: Excluir líneas con texto de control específico
        exclusion_patterns = [
            "Q000000", "Todoslosimportesdeesteextractoseexpresanen",
            "SALDOANUESTROFAVOR", "SALDOASUFAVOR", "F00201", "EURO"
        ]

        if not line or any(x in line for x in exclusion_patterns):
            i += 1
            continue

        # Buscar patrón de transacción
        transaction_pattern = r'(\d{2}/\d{2})\s+(\d{2}/\d{2})\s+(.+?)\s+(-?\d{1,3}(?:\.\d{3})*,\d{2})\s+(\d{1,3}(?:\.\d{3})*,\d{2})$'
        match = re.search(transaction_pattern, line)

        if match:
            f_oper, f_valor, concepto, importe, saldo = match.groups()

            # FILTRADO ADICIONAL: Verificar que el concepto no contenga texto de control
            if any(control in concepto for control in
                   ["Todoslosimportesdeesteextractoseexpresanen", "SALDOANUESTROFAVOR", "SALDOASUFAVOR"]):
                print(f"  ⚠️  Saltando transacción con texto de control: {concepto[:50]}...")
                i += 1
                continue

            # LIMPIAR CONCEPTO
            concepto_limpio = clean_concept(concepto)

            # EXTRAER EMPRESA/ESTABLECIMIENTO
            empresa, concepto_final = extract_empresa(concepto_limpio)

            # CREAR TRANSACCIÓN TEMPORAL SIN CATEGORIZAR
            transaction = {
                'Fecha_Operacion': f_oper,
                'Fecha_Valor': f_valor,
                'Concepto': concepto_final,
                'Empresa': empresa,
                'Importe': importe,
                'Saldo': saldo,
                'Mes': month_year['month'],
                'Año': month_year['year'],
                'Archivo_Origen': os.path.basename(pdf_path)
            }

            # PROCESAR LÍNEAS SIGUIENTES PARA CAPTURAR MÁS INFORMACIÓN (ESPECIALMENTE EMPRESA)
            j = i + 1
            while j < len(lines) and j < i + 5:
                next_line = lines[j].strip()

                # FILTRAR LÍNEAS DE DETALLE: Excluir texto de control
                if (not next_line or
                        any(control in next_line for control in exclusion_patterns) or
                        re.search(transaction_pattern, next_line) or
                        re.match(r'^\d{1,3}(?:\.\d{3})*,\d{2}$', next_line)):
                    break

                detalle_limpio = clean_concept(next_line)

                # ESTRATEGIA MEJORADA PARA CAPTURAR EMPRESA
                if not transaction['Empresa'] and len(detalle_limpio) > 3:
                    # Para ADEUDOS, la siguiente línea suele ser la empresa
                    if 'ADEUDO' in transaction['Concepto']:
                        transaction['Empresa'] = detalle_limpio
                    # Para TRANSFERENCIAS, capturar el destinatario
                    elif 'TRANSFERENCIA' in transaction['Concepto']:
                        transaction['Empresa'] = detalle_limpio
                    # Para TARJETAS, capturar establecimiento
                    elif 'TARJETA' in transaction['Concepto']:
                        transaction['Empresa'] = detalle_limpio
                    # Para BIZUM, añadir al concepto
                    elif 'BIZUM' in transaction['Concepto']:
                        transaction['Concepto'] += " - " + detalle_limpio
                    # Caso general - capturar como empresa
                    else:
                        transaction['Empresa'] = detalle_limpio
                elif transaction['Empresa'] and len(detalle_limpio) > 5:
                    # Si ya tenemos empresa, añadir detalles al concepto
                    transaction['Concepto'] += " - " + detalle_limpio

                j += 1

            # AHORA SÍ CATEGORIZAR CON TODA LA INFORMACIÓN DISPONIBLE
            tipo_operacion = calculate_operation_type(transaction['Importe'], transaction['Concepto'])
            categoria, subcategoria = categorize_transaction(transaction['Concepto'], transaction['Importe'], transaction['Empresa'])

            # Añadir las columnas categorizadas a la transacción
            transaction['Tipo_Operacion'] = tipo_operacion
            transaction['Categoria_Principal'] = categoria
            transaction['Subcategoria'] = subcategoria

            transactions.append(transaction)

            if j > i + 1:
                i = j
            else:
                i += 1

        else:
            i += 1

    print(f"  ✓ {len(transactions)} transacciones extraídas")
    return transactions


def extract_empresa(concepto):
    """
    Extrae la empresa/establecimiento del concepto - VERSIÓN MEJORADA
    """
    concepto_limpio = concepto.strip()

    # Para ADEUDOS, no extraer empresa aquí (se capturará en línea siguiente)
    if 'ADEUDO A SU CARGO' in concepto_limpio:
        return '', concepto_limpio

    # Patrón para tarjetas: número largo seguido de empresa
    patron_tarjeta = r'(\d{12,20})\s+(.+)'
    match_tarjeta = re.search(patron_tarjeta, concepto_limpio)
    if match_tarjeta:
        numero_tarjeta = match_tarjeta.group(1)
        empresa = match_tarjeta.group(2).strip()
        concepto_sin_empresa = concepto_limpio.replace(match_tarjeta.group(0), '').strip()
        return empresa, concepto_sin_empresa

    # Buscar empresas conocidas en el concepto
    empresas_conocidas = [
        'SPOTIFY', 'APPLE', 'CONSUM', 'LEROY MERLIN', 'GLOVO',
        'AMAZON', 'MERCADONA', 'CARREFOUR', 'ZARA', 'BERSHKA',
        'STARBUCKS', 'TICKETMASTER', 'MYPROTEIN', 'PLENOIL', 'BALLENOIL'
    ]

    for empresa in empresas_conocidas:
        if empresa in concepto_limpio.upper():
            # Extraer la empresa y todo lo que viene después
            inicio = concepto_limpio.upper().find(empresa)
            empresa_completa = concepto_limpio[inicio:].strip()
            concepto_sin_empresa = concepto_limpio[:inicio].strip().rstrip('-').strip()
            return empresa_completa, concepto_sin_empresa

    return '', concepto_limpio

    # Si no se encuentra empresa, devolver el concepto completo
    return '', concepto_limpio

def calculate_operation_type(importe, concepto):
    """
    Determina si es ingreso, gasto o transferencia
    """
    if float(importe.replace('.', '').replace(',', '.')) > 0:
        if 'BIZUM' in concepto and 'RECIBIDO' in concepto:
            return 'Ingreso_Bizum'
        elif 'NOMINA' in concepto or 'ABONO' in concepto:
            return 'Ingreso_Nomina'
        elif 'TRANSFERENCIA' in concepto:
            return 'Ingreso_Transferencia'
        else:
            return 'Ingreso_Varios'
    else:
        if 'BIZUM' in concepto and 'ENVIADO' in concepto:
            return 'Gasto_Bizum'
        elif 'TARJETA' in concepto:
            return 'Gasto_Tarjeta'
        elif 'ADEUDO' in concepto:
            return 'Gasto_Adeudo'
        else:
            return 'Gasto_Varios'


def categorize_transaction(concepto, importe, empresa):
    """
    Categoriza la transacción usando tanto concepto como empresa - VERSIÓN MEJORADA
    """
    concepto_upper = concepto.upper()
    empresa_upper = empresa.upper() if empresa else ""
    importe_num = float(importe.replace('.', '').replace(',', '.'))

    # Combinar concepto y empresa para búsqueda
    texto_busqueda = concepto_upper + " " + empresa_upper

    # DEBUG: Mostrar información para transacciones problemáticas
    debug_transactions = ['TARJETA', 'ADEUDO', 'BIZUM']
    if any(debug in concepto_upper for debug in debug_transactions):
        print(f"  🔍 DEBUG: Concepto: {concepto_upper[:50]}, Empresa: {empresa_upper[:30]}")

    # INGRESOS
    if importe_num > 0:
        if 'NOMINA' in texto_busqueda:
            return 'Ingresos', 'Nomina'
        elif 'DESEMPLEO' in texto_busqueda or 'INEM' in texto_busqueda or 'SUBSIDIO' in texto_busqueda:
            return 'Ingresos', 'Subsidio_Desempleo'
        elif 'BIZUM' in texto_busqueda and 'RECIBIDO' in texto_busqueda:
            return 'Ingresos', 'Bizum_Recibido'
        elif 'TRANSFERENCIA' in texto_busqueda:
            return 'Ingresos', 'Transferencia_Entrante'
        elif 'PENSION' in texto_busqueda:
            return 'Ingresos', 'Pension'
        else:
            return 'Ingresos', 'Otros_Ingresos'

    # GASTOS - ESTRATEGIA MEJORADA

    # 1. PRIMERO BUSCAR EN EMPRESA (más confiable)
    if empresa_upper:
        # GIMNASIO
        if any(gym in empresa_upper for gym in ['FITNESS', 'FITZE', 'GYM', 'DEPORTE']):
            return 'Servicios', 'Gimnasio'

        # STREAMING Y SUSCRIPCIONES
        if any(stream in empresa_upper for stream in ['SPOTIFY', 'APPLE', 'STEAM', 'ENEBA', 'DISTROKID', 'NETFLIX', 'PRIME']):
            return 'Servicios', 'Suscripciones'

        # SEGUROS
        if any(seguro in empresa_upper for seguro in ['MAPFRE', 'SEGURO', 'MUTUA', 'ASEGURADORA']):
            return 'Seguros', 'Seguros_Varios'

        # RESTAURANTES Y BARS
        restaurantes = [
            'CISTELLA', 'MARTIN', 'DOMINOS', 'SHOGUN', 'BURGUER', 'SAONA', 'RESTAURANT',
            'CHICKERS', 'PURAZEPA', 'JACKSON', 'PATRICK', 'COSI', 'SPHINX', 'BAR',
            'VERMUTERIA', 'BIERWINKEL', 'EDEN', 'CHARLIE', 'BURGER', 'PIZZA', 'CAFETERIA'
        ]
        if any(rest in empresa_upper for rest in restaurantes):
            return 'Alimentacion', 'Restaurantes'

        # DELIVERY
        if any(delivery in empresa_upper for delivery in ['GLOVO', 'JUSTEAT', 'UBER EATS', 'DELIVEROO']):
            return 'Alimentacion', 'Delivery'

        # SUPERMERCADOS
        supermercados = [
            'CONSUM', 'HIPERBER', 'MERCADONA', 'ALIMENTACION', 'MULTIMARKET',
            'MCDONALD', 'SOFIA', 'LIDL', 'CARREFOUR', 'ALDI', 'SUPERMERCADO'
        ]
        if any(super in empresa_upper for super in supermercados):
            return 'Alimentacion', 'Supermercado'

        # TRANSPORTE
        if any(trans in empresa_upper for trans in ['GASOLINERA', 'PLENOIL', 'BALLENOIL', 'REPSOL', 'SHELL']):
            return 'Transporte', 'Combustible'

        if any(trans in empresa_upper for trans in ['MOVILTIK', 'ORA', 'UBER', 'TAXI', 'BUS', 'RENFE']):
            return 'Transporte', 'Transporte_Publico'

        # OCIO
        if any(ocio in empresa_upper for ocio in ['DEPORTES', 'PADEL', 'TEATRO', 'TICKETMASTER', 'CINE', 'PELICULA']):
            return 'Ocio', 'Entretenimiento'

        # COMPRAS - ROPA
        if any(ropa in empresa_upper for ropa in ['ZARA', 'BERSHKA', 'LEFTIES', 'TEZENIS', 'PRIMARK', 'H&M', 'MANGO']):
            return 'Compras', 'Ropa'

        # COMPRAS - HOGAR
        if any(hogar in empresa_upper for hogar in ['LEROY', 'MERLIN', 'FERRETERIA', 'BAZAR', 'IKEA', 'DECORACION']):
            return 'Compras', 'Hogar'

        # COMPRAS - ONLINE
        if any(online in empresa_upper for online in ['AMAZON', 'TEMU', 'PAYPAL', 'ETSY', 'ALIEXPRESS', 'EBAY']):
            return 'Compras', 'Online'

        # EDUCACIÓN
        if any(edu in empresa_upper for edu in ['UNIVERSIDAD', 'MIGUEL', 'HERNANDEZ', 'COLEGIO', 'ESCUELA']):
            return 'Educacion', 'Formacion'

        # SALUD
        if any(salud in empresa_upper for salud in ['MYPROTEIN', 'HSN', 'FARMACIA', 'MEDICO', 'HOSPITAL']):
            return 'Salud', 'Salud_Bienestar'

        # TABACO
        if any(tabaco in empresa_upper for tabaco in ['ESTANCO', 'TABACO', 'EXPENDEDURIA', 'LABORES']):
            return 'Personales', 'Tabaco'

    # 2. LUEGO BUSCAR EN CONCEPTO (si no encontramos en empresa)
    # BIZUM GASTOS
    if 'BIZUM' in concepto_upper and 'ENVIADO' in concepto_upper:
        return 'Transferencias', 'Bizum_Enviado'

    # TRANSFERENCIAS
    if 'TRANSFERENCIA' in concepto_upper:
        return 'Transferencias', 'Transferencia_Saliente'

    # ADEUDOS
    if 'ADEUDO' in concepto_upper:
        # Intentar categorizar adeudos específicos
        if 'SPOTIFY' in texto_busqueda:
            return 'Servicios', 'Suscripciones'
        elif 'GYM' in texto_busqueda or 'FITNESS' in texto_busqueda:
            return 'Servicios', 'Gimnasio'
        elif 'SEGURO' in texto_busqueda:
            return 'Seguros', 'Seguros_Varios'
        else:
            return 'Servicios', 'Cargo_Automatico'

    # TARJETAS - Buscar en el concepto para categorizar
    if 'TARJETA' in concepto_upper:
        if 'RESTAURANT' in texto_busqueda or 'BAR' in texto_busqueda:
            return 'Alimentacion', 'Restaurantes'
        elif 'SUPERMERCADO' in texto_busqueda or 'ALIMENTACION' in texto_busqueda:
            return 'Alimentacion', 'Supermercado'
        elif 'GASOLINERA' in texto_busqueda:
            return 'Transporte', 'Combustible'
        elif 'ROPA' in texto_busqueda or 'MODA' in texto_busqueda:
            return 'Compras', 'Ropa'
        elif 'HOGAR' in texto_busqueda:
            return 'Compras', 'Hogar'
        elif 'OCIO' in texto_busqueda or 'ENTRETENIMIENTO' in texto_busqueda:
            return 'Ocio', 'Entretenimiento'
        else:
            return 'Compras', 'Varios'

    # COMISIONES
    if 'COMISION' in concepto_upper:
        return 'Bancario', 'Comisiones'

    if 'RET.EFECTIVO' in concepto_upper:
        return 'Bancario', 'Retirada_Efectivo'

    # Por defecto - categorizar por tipo de operación genérica
    if 'BIZUM' in concepto_upper:
        return 'Transferencias', 'Bizum_Enviado'
    elif 'TRANSFERENCIA' in concepto_upper:
        return 'Transferencias', 'Transferencia_Saliente'
    elif 'ADEUDO' in concepto_upper:
        return 'Servicios', 'Cargo_Automatico'
    elif 'TARJETA' in concepto_upper:
        return 'Compras', 'Varios'
    else:
        return 'Varios', 'Gastos_Generales'


def separar_id_empresa(empresa):
    """
    Separa el ID del nombre de la empresa
    """
    if not empresa or empresa == '':
        return '', ''

    # Patrones para identificar IDs
    patrones = [
        # ID numérico (16-20 dígitos) seguido de texto
        r'^(\d{16,20})(.+)$',
        # ID alfanumérico que empieza con letra (como N2025195000634023)
        r'^([A-Z]\d{14,20})(.+)$',
        # ID con formato específico (como AMZNMktpES*0Y44I4EL5)
        r'^([A-Z0-9*]{10,20})(.+)$',
        # ID con formato MONEYNET*
        r'^(MONEYNET\*\d+)(.+)$',
    ]

    for patron in patrones:
        match = re.match(patron, empresa.strip())
        if match:
            id_empresa = match.group(1).strip()
            nombre_empresa = match.group(2).strip()

            # Limpiar el nombre de la empresa (quitar espacios iniciales, guiones, etc.)
            nombre_empresa = re.sub(r'^[\s\-]+', '', nombre_empresa)

            return id_empresa, nombre_empresa

    # Si no encuentra patrón, asumir que es solo nombre de empresa
    return '', empresa

def extract_month_year_from_content(text):
    """
    Extrae el mes y año del contenido del PDF
    """
    patterns = [
        r'EXTRACTODE(\w+)(\d{4})',
        r'EXTRACTO DE (\w+) (\d{4})',
        r'EXTRACTODELMESDE(\w+)(\d{4})',
    ]

    for pattern in patterns:
        match = re.search(pattern, text.replace(" ", ""))
        if match:
            month_name = match.group(1).upper()
            year = int(match.group(2))

            month_dict = {
                'ENERO': 1, 'FEBRERO': 2, 'MARZO': 3, 'ABRIL': 4, 'MAYO': 5, 'JUNIO': 6,
                'JULIO': 7, 'AGOSTO': 8, 'SEPTIEMBRE': 9, 'OCTUBRE': 10, 'NOVIEMBRE': 11, 'DICIEMBRE': 12
            }

            if month_name in month_dict:
                return {'year': year, 'month': month_dict[month_name]}

    return {'year': 2025, 'month': 9}


def clean_concept(concepto):
    """
    Limpia y corrige errores OCR en los conceptos
    """
    # (Mantener el mismo diccionario de correcciones que antes)
    corrections = {
        '8TZUN': 'BIZUM',
        'BTZUN': 'BIZUM',
        'B1ZUM': 'BIZUM',
        'RECISI00': 'RECIBIDO',
        'ENVIA00': 'ENVIADO',
        'SINCENCEPTO': 'SIN CONCEPTO',
        'EXTRASBOBLAS': 'EXTRAS BEBIDAS',
        'NORINA': 'NOMINA',
        'CONSUN': 'CONSUM',
        'AGNOO': 'ABONO',
        'PORTARUSFERENCIA': 'POR TRANSFERENCIA',
        'PAGOCONTARJETAGN': 'PAGO CON TARJETA EN',
        'JUASEG': 'MUSEOS',
        'AGENDO': 'ADEUDO',
        'DEARGO': 'A CARGO',
        'AQISTANCIA': 'A DISTANCIA',
        'ABONODENOMINAPORTRANSFERENCIA': 'ABONO DE NOMINA POR TRANSFERENCIA',
        'PAGOCONTARJETAENESPECTACULOS,MUSEOSYDEPORTES': 'PAGO CON TARJETA EN ESPECTACULOS, MUSEOS Y DEPORTES',
        'PAGOCONTARJETAENRESTAURANTESYCAFETERIAS': 'PAGO CON TARJETA EN RESTAURANTES Y CAFETERIAS',
        'ADEUDOASUCARGO': 'ADEUDO A SU CARGO',
        'PAGOCONTARJETADECOMPRASADISTANCIAYSUSCRIPCIONES': 'PAGO CON TARJETA DE COMPRAS A DISTANCIA Y SUSCRIPCIONES',
        'PAGOCONTARJETAENSUPERMERCADOS': 'PAGO CON TARJETA EN SUPERMERCADOS',
        'PAGOCONTARJETADESERVICIOSVARIOS': 'PAGO CON TARJETA DE SERVICIOS VARIOS',
        'ORDENESPAGOEMITIDASENMONEDALOCAL': 'ORDENES PAGO EMITIDAS EN MONEDA LOCAL',
        'TRANSFERENCIAMENSUALBBVA': 'TRANSFERENCIA MENSUAL BBVA',
        'PAGOCONTARJETAENHOGAR,MUEBLES,DECORACIONYELECTR': 'PAGO CON TARJETA EN HOGAR, MUEBLES, DECORACION Y ELECTRODOMESTICOS',
        'PAGOCONTARJETAENSECTORDELAUTOMOVIL': 'PAGO CON TARJETA EN SECTOR DEL AUTOMOVIL',
        'CARGOPORCOMPRACONTARJETAENCOMERCIOS': 'CARGO POR COMPRA CON TARJETA EN COMERCIOS',
        'PAGOCONTARJETAENMEDICINA,FARMACIAYSANIDAD': 'PAGO CON TARJETA EN MEDICINA, FARMACIA Y SANIDAD',
        'PAGOCONTARJETAENGASOLINERAS': 'PAGO CON TARJETA EN GASOLINERAS',
        'PAGOCONTARJETAENMODA,CALZADOYCOMPLEMENTOS': 'PAGO CON TARJETA EN MODA, CALZADO Y COMPLEMENTOS',
        'TRANSFERENCIAS': 'TRANSFERENCIA',
        'SINCONCEPTO': 'SIN CONCEPTO',
        'RECIBIDO:EXTASBEBIDAS': 'RECIBIDO: EXTRAS BEBIDAS',
        'RECIBIDO:TASSI': 'RECIBIDO: TASSI',
        'RECIBIDO:GYM': 'RECIBIDO: GYM',
        'ENVIADO:GIFT': 'ENVIADO: GIFT',
        'ENVIADO:SINCONCEPTO': 'ENVIADO: SIN CONCEPTO',
        'RECIBIDO:SINCONCEPTO': 'RECIBIDO: SIN CONCEPTO',
        'RECIBIDO:100M': 'RECIBIDO: 100M',
        'RECIBIDO:CIENMON': 'RECIBIDO: CIEN MON',
        'RECIBIDO:CENA': 'RECIBIDO: CENA',
        'RECIBIDO:BIZUMDE CARMEN': 'RECIBIDO: BIZUM DE CARMEN',
        'RECIBIDO:PADRE': 'RECIBIDO: PADRE',
        'RECIBIDO:SPOTI': 'RECIBIDO: SPOTI',
        'RECIBIDO:SPOTY': 'RECIBIDO: SPOTY',
        'RECIBIDO:SPOTIFY': 'RECIBIDO: SPOTIFY',
        'EXPTE.MODTR': 'EXPEDIENTE MODTR',
        'LABORESDETABACO12': 'LABORES DE TABACO 12',
        'ESTANCONç26': 'ESTANCO Nº26',
        'ESTANCONç1': 'ESTANCO Nº1',
        'EXPENDEDURIAN.30': 'EXPENDEDURIA N.30',
        '24HORASCHIMENEAS': '24 HORAS CHIMENEAS',
        'CONSUMELXT.QUEVEDO': 'CONSUM ELX T. QUEVEDO',
        'TAPERIAMARTIN': 'TAPERIA MARTIN',
        'LACISTELLA': 'LA CISTELLA',
        'JACKSONIRISH': 'JACKSON IRISH',
        'STPATRICK': 'ST PATRICK',
        'COSI': 'COSI',
        'SPHINX': 'SPHINX',
        'STARBUCKS': 'STARBUCKS',
        'ESSALAMMARKET': 'ES SALAM MARKET',
        'IN TOWN RESTAURANT': 'IN TOWN RESTAURANT',
        'CAFETERIAEDEN': 'CAFETERIA EDEN',
        'GERMANIAS PAES': 'GERMANIAS PAES',
        'LIDLE-COMMERCE': 'LIDL E-COMMERCE',
        'MONTCADAIREES': 'MONTCADA I REIXAC ES',
        'HSNSTORE.COM': 'HSN STORE.COM',
        'ALBOLOTE ES': 'ALBOLOTE ES',
        'ORAELCHE': 'ORA ELCHE',
        'MNE*': 'MONEYNET*',
        'MONEYNET_S': 'MONEYNET S',
        'TEMU.COM': 'TEMU.COM',
        'PLENOILUS256': 'PLENOIL US256',
        'BALLENOILSL-ELCHE': 'BALLENOIL SL ELCHE',
        'AMZN MKTP': 'AMAZON MARKETPLACE',
        'JUST EAT': 'JUST EAT',
        'WWW.AMAZON.*': 'WWW.AMAZON.',
        'ENEBA.COM': 'ENEBA.COM',
        'REVOLUT**': 'REVOLUT ',
        'TM*TICKETMASTER': 'TICKETMASTER',
        'LEFTIES REISCATOLICSES': 'LEFTIES REUS CATOLICA ES',
        'BERSHKA': 'BERSHKA',
        'TEZENIS': 'TEZENIS',
        'THECAPITALSOUVENIR': 'THE CAPITAL SOUVENIR',
        'TRAVELSHOPPINGLTD': 'TRAVEL SHOPPING LTD',
        'AUTODOC AG': 'AUTODOC AG',
        'UNIVERSIDADMIGUELHERNANELCHE': 'UNIVERSIDAD MIGUEL HERNANDEZ ELCHE',
        'FERRETERIAFCOGARCIA': 'FERRETERIA FCO GARCIA',
        'NICALICANTE': 'NICOLAS ALICANTE',
        'LEROYMERLINELCHE': 'LEROY MERLIN ELCHE',
        'ELCHE/ELX': 'ELCHE/ELX',
    }

    concepto_limpio = concepto
    for error, correccion in corrections.items():
        concepto_limpio = concepto_limpio.replace(error, correccion)

    return concepto_limpio


def process_all_pdfs(folder_path="."):
    """
    Procesa todos los PDFs en la carpeta Archivos PDF
    """
    folder_path = Path("..") / "Archivos PDF"
    pdf_files = list(folder_path.glob("*.pdf"))

    if not pdf_files:
        print("No se encontraron archivos PDF en la carpeta")
        return

    print(f"Encontrados {len(pdf_files)} archivos PDF:")
    for pdf_file in pdf_files:
        print(f"  - {os.path.basename(pdf_file)}")

    # Procesar todos los PDFs
    all_transactions = []
    for pdf_file in pdf_files:
        print(f"\nProcesando: {os.path.basename(pdf_file)}")
        transactions = extract_bank_data_from_pdf(pdf_file)
        all_transactions.extend(transactions)

    if not all_transactions:
        print("No se pudieron extraer transacciones de ningún PDF")
        return

    # Crear DataFrame con todas las transacciones
    df_all = pd.DataFrame(all_transactions)

    # SEPARAR ID Y NOMBRE DE EMPRESA
    print("🔧 Separando IDs y nombres de empresas...")
    ids_empresas = []
    nombres_empresas = []

    for empresa in df_all['Empresa']:
        id_empresa, nombre_empresa = separar_id_empresa(empresa)
        ids_empresas.append(id_empresa)
        nombres_empresas.append(nombre_empresa)

    # Añadir las nuevas columnas al DataFrame
    df_all['ID_Empresa'] = ids_empresas
    df_all['Nombre_Empresa'] = nombres_empresas

    # Reordenar columnas para mejor visualización
    column_order = [
        'Fecha_Operacion', 'Fecha_Valor', 'Concepto', 'Empresa',
        'ID_Empresa', 'Nombre_Empresa', 'Importe', 'Saldo',
        'Tipo_Operacion', 'Categoria_Principal', 'Subcategoria',
        'Mes', 'Año', 'Archivo_Origen'
    ]

    # Mantener solo las columnas que existen en el DataFrame
    existing_columns = [col for col in column_order if col in df_all.columns]
    df_all = df_all[existing_columns]

    # Convertir formatos numéricos
    df_all['Importe'] = df_all['Importe'].str.replace('.', '').str.replace(',', '.').astype(float)
    df_all['Saldo'] = df_all['Saldo'].str.replace('.', '').str.replace(',', '.').astype(float)

    # Ordenar por año, mes y fecha de operación
    df_all = df_all.sort_values(['Año', 'Mes', 'Fecha_Operacion'])

    # Guardar CSV completo con todas las transacciones
    csv_path = Path("..") / "Archivos CSV" / "gastos_completo_categorizado.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)  # Crear carpeta si no existe
    df_all.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"\n✅ CSV completo guardado: 'gastos_completo_categorizado.csv'")
    print(f"   Total de transacciones: {len(df_all)}")
    print(f"   Columnas disponibles: {list(df_all.columns)}")

    # Mostrar ejemplos de separación
    print(f"\n🔍 Ejemplos de separación ID/Nombre:")
    ejemplos = df_all[df_all['ID_Empresa'] != ''].head(5)
    for _, row in ejemplos.iterrows():
        print(f"   {row['Empresa'][:40]:40} → ID: {row['ID_Empresa']:20} Nombre: {row['Nombre_Empresa'][:30]}")

    # Mostrar resumen de categorías
    show_categories_summary(df_all)


def show_categories_summary(df):
    """
    Muestra un resumen de las categorías encontradas
    """
    print(f"\n📊 RESUMEN DE CATEGORÍAS:")

    print(f"\n📈 CATEGORÍAS PRINCIPALES:")
    cat_summary = df['Categoria_Principal'].value_counts()
    for categoria, count in cat_summary.items():
        # CORREGIR: Usar paréntesis correctamente para las condiciones
        gasto_cat = abs(df[(df['Categoria_Principal'] == categoria) & (df['Importe'] < 0)]['Importe'].sum())
        print(f"  {categoria}: {count:>3} transacciones, {gasto_cat:>8.2f}€")

    print(f"\n🔍 SUBCATEGORÍAS MÁS COMUNES:")
    subcat_summary = df['Subcategoria'].value_counts().head(10)
    for subcat, count in subcat_summary.items():
        print(f"  {subcat}: {count} transacciones")


def main():
    """
    Función principal
    """
    print("🔄 INICIANDO PROCESAMIENTO DE PDFs BANCARIOS")
    print("=" * 50)

    # Procesar todos los PDFs en la carpeta actual
    process_all_pdfs()

    print("\n" + "=" * 50)
    print("✅ PROCESAMIENTO COMPLETADO")


if __name__ == "__main__":
    main()