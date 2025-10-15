import json
import os
import re
import pandas as pd
import pdfplumber
from pathlib import Path

# Cargar diccionario
_palabras_espanol = None

def cargar_mapeo_categorias():
    """Carga las reglas de categorización desde el archivo JSON."""
    ruta_config = os.path.join('..', 'config', 'config_categorias.json')
    try:
        with open(ruta_config, 'r', encoding='utf-8') as f:
            config = json.load(f)
        # Convertir la lista de reglas a un diccionario para una búsqueda más rápida
        mapeo = {regla['palabra_clave']: (regla['categoria'], regla['subcategoria']) for regla in config['mapeo_categorias']}
        return mapeo
    except Exception as e:
        print(f"❌ Error cargando la configuración de categorías: {e}")
        return {}

Mapeo_CATEGORIAS = cargar_mapeo_categorias()


def determinar_categoria(operacion, nombre_empresa):
    """Determina la categoría y subcategoría basada en la operación y empresa"""

    # Primero verificar operaciones específicas
    if operacion == "BIZUM":
        return "BIZUM", ""

    if "TRANSFERENCIA" in operacion:
        return "TRANSFERENCIAS", ""

    if "NOMINA" in operacion:
        return "TRANSFERENCIAS", "NÓMINA"

    # Buscar en el nombre de la empresa
    nombre_empresa_upper = nombre_empresa.upper()

    for palabra, (categoria, subcategoria) in Mapeo_CATEGORIAS.items():
        if palabra in nombre_empresa_upper:
            return categoria, subcategoria

    # Buscar en la operación
    operacion_upper = operacion.upper()
    for palabra, (categoria, subcategoria) in Mapeo_CATEGORIAS.items():
        if palabra in operacion_upper:
            return categoria, subcategoria

    # Categorías por tipo de operación
    if "PAGO CON TARJETA" in operacion:
        if "RESTAURANTES" in operacion:
            return "COMIDA", "RESTAURANTE"
        elif "SUPERMERCADOS" in operacion:
            return "COMIDA", "SUPERMERCADO"
        elif "COMPRAS" in operacion:
            return "COMPRAS", "VARIOS"

    # Categoría por defecto
    return "OTROS", "VARIOS"


def cargar_diccionario():
    global _palabras_espanol
    if _palabras_espanol is not None:
        return _palabras_espanol

    _palabras_espanol = set()
    directorio_dics = Path("dics")

    if not directorio_dics.exists():
        return set()

    for archivo_txt in directorio_dics.glob("*.txt"):
        try:
            with open(archivo_txt, 'r', encoding='utf-8') as f:
                for linea in f:
                    palabra = linea.strip().upper()
                    if palabra and len(palabra) > 1:
                        _palabras_espanol.add(palabra)
        except Exception:
            continue

    return _palabras_espanol


def aplicar_reglas_bancarias(texto):
    """Aplica reglas específicas para conceptos bancarios comunes"""
    patrones = [
        (r'ABONODENOMINAPOR', 'ABONO DENOMINA POR '),
        (r'PAGOCONTARJETA', 'PAGO CON TARJETA '),
        (r'ENRESTAURANTES', 'EN RESTAURANTES '),
        (r'YCAFETERIAS', 'Y CAFETERIAS'),
        (r'ENESPECTACULOS', 'EN ESPECTACULOS '),
        (r'MUSEOSYDEPORTES', 'MUSEOS Y DEPORTES'),
        (r'DECOMPRAS', 'DE COMPRAS '),
        (r'ADISTANCIA', 'A DISTANCIA '),
        (r'YSUSCRIPCIONES', 'Y SUSCRIPCIONES'),
        (r'ADEUDOASUCARGO', 'ADEUDO A SU CARGO'),
        (r'ENSUPERMERCADOS', 'EN SUPERMERCADOS'),
        (r'DESERVICIOS', 'DE SERVICIOS '),
        (r'VARIOS', 'VARIOS'),
        (r'ENSECTORDEL', 'EN SECTOR DEL '),
        (r'AUTOMOVIL', 'AUTOMOVIL'),
        (r'RETEFECTIVO', 'RET EFECTIVO '),
        (r'ADEBITOCONTARJ', 'A DEBITO CONTARJ '),
        (r'ENCAJEROAUT', 'EN CAJERO AUT'),
        (r'CARGOPORCOMPRA', 'CARGO POR COMPRA '),
        (r'ENCOMERCIOS', 'EN COMERCIOS'),
        (r'ABONODELINEM', 'ABONO DELINEM '),
        (r'PAGODEDESEMPLEO', 'PAGO DE DESEMPLEO'),
        (r'ENMODA', 'EN MODA '),
        (r'CALZADOYCOMPLEMENTOS', 'CALZADO Y COMPLEMENTOS'),
        (r'ENDEPORTES', 'EN DEPORTES '),
        (r'YJUGUETES', 'Y JUGUETES'),
        (r'ENDISCOS', 'EN DISCOS '),
        (r'LIBROSFOTOS', 'LIBROS FOTOS '),
        (r'YPC', 'Y PC'),
        (r'ENHOGAR', 'EN HOGAR '),
        (r'MUEBLESDECORACION', 'MUEBLES DECORACION '),
        (r'YELECTR', 'Y ELECTR'),
        (r'ENDROGUERIAS', 'EN DROGUERIAS '),
        (r'YPERFUMERIAS', 'Y PERFUMERIAS'),
        (r'COMISIONESPORSERVICIOS', 'COMISIONES POR SERVICIOS'),
        (r'COMPRAENCOMERCIOEXTRANJERO', 'COMPRA EN COMERCIO EXTRANJERO '),
        (r'COMISION3%INCLUIDA', 'COMISION 3% INCLUIDA'),
        (r'ABONOBONIFICACION', 'ABONO BONIFICACION '),
        (r'PACKVIAJES', 'PACK VIAJES'),
    ]

    resultado = texto
    for patron, reemplazo in patrones:
        resultado = resultado.replace(patron, reemplazo)

    return resultado.strip()


def formatear_concepto(concepto):
    """Formatea conceptos bancarios con espacios"""
    if not concepto or len(concepto) < 4:
        return concepto

    concepto = concepto.upper()

    # Aplicar reglas bancarias primero
    concepto = aplicar_reglas_bancarias(concepto)

    # Si ya tiene espacios, está procesado
    if ' ' in concepto:
        return concepto

    # Intentar con diccionario si no hay espacios
    palabras_espanol = cargar_diccionario()
    if palabras_espanol:
        palabras_encontradas = []
        i = 0
        n = len(concepto)

        while i < n:
            encontrado = False
            for longitud in range(min(10, n - i), 2, -1):
                palabra = concepto[i:i + longitud]
                if palabra in palabras_espanol:
                    palabras_encontradas.append(palabra)
                    i += longitud
                    encontrado = True
                    break

            if not encontrado:
                if i == 0:
                    return concepto
                else:
                    palabras_encontradas.append(concepto[i:])
                    break

        return " ".join(palabras_encontradas)

    return concepto


def separar_empresa(detalle):
    """Separa el detalle de empresa en ID y Nombre"""
    if not detalle:
        return "", ""

    # Patrones para identificar IDs
    patrones_id = [
        r'^\d{16}',  # 16 dígitos (tarjeta)
        r'^N\d{13}',  # N + 13 dígitos (N20251950006340)
        r'^\d{12}',  # 12 dígitos
        r'^\d{9}',  # 9 dígitos
    ]

    id_empresa = ""
    nombre_empresa = detalle

    for patron in patrones_id:
        match = re.match(patron, detalle)
        if match:
            id_empresa = match.group()
            nombre_empresa = detalle[len(id_empresa):].strip()
            break

    # Si no se encontró patrón numérico, verificar si es solo nombre
    if not id_empresa:
        # Si parece ser solo un nombre (sin números al inicio)
        if not re.match(r'^\d', detalle):
            id_empresa = ""
            nombre_empresa = detalle
        else:
            # Intentar separar por el primer grupo de letras después de números
            match = re.match(r'^(\d+)([A-Z].*)', detalle)
            if match:
                id_empresa = match.group(1)
                nombre_empresa = match.group(2).strip()

    return id_empresa, nombre_empresa


def extraer_texto_pdf(ruta_pdf):
    """Extrae texto de un PDF"""
    try:
        with pdfplumber.open(ruta_pdf) as pdf:
            texto_total = f"ARCHIVO: {ruta_pdf.name}\n"
            for i, pagina in enumerate(pdf.pages):
                texto_pagina = pagina.extract_text() or ""
                texto_total += f"--- PÁGINA {i + 1} ---\n{texto_pagina}\n\n"
            return texto_total
    except Exception:
        return f"ARCHIVO: {ruta_pdf.name}\nERROR\n"


def procesar_operaciones(texto_completo):
    """Procesa operaciones bancarias desde texto extraído"""
    archivos = texto_completo.split("ARCHIVO: ")[1:]
    operaciones = []

    for archivo in archivos:
        # Extraer mes y año
        mes_match = re.search(r'EXTRACTODE(\w+)2025', archivo)
        mes = mes_match.group(1) if mes_match else "DESCONOCIDO"
        año = "2025"

        for pagina in archivo.split("--- PÁGINA")[1:]:
            lineas = pagina.split('\n')
            i = 0

            while i < len(lineas):
                linea = lineas[i].strip()

                # Patrón MUCHO más simple y flexible
                patron = r'^(\d{2}/\d{2})\s+(\d{2}/\d{2})\s+([A-Z].*?)\s+(-?[\d.,]+)\s+(-?[\d.,]+)$'
                match = re.match(patron, linea)

                if match:
                    f_oper, f_valor, concepto, importe, saldo = match.groups()

                    # Buscar detalle en siguiente línea
                    detalle = ""
                    if i + 1 < len(lineas):
                        siguiente = lineas[i + 1].strip()
                        if (siguiente and
                                not re.match(r'^\d{2}/\d{2}', siguiente) and
                                not re.match(r'^SALDO', siguiente) and
                                not re.match(r'^Todoslosimportes', siguiente) and
                                not re.match(r'^F\d+', siguiente) and
                                len(siguiente) > 5):
                            detalle = siguiente
                            i += 1

                    # Separar empresa en ID y Nombre
                    id_empresa, nombre_empresa = separar_empresa(detalle)

                    # Procesar BIZUM
                    concepto_bizum = ""
                    operacion_limpia = formatear_concepto(concepto)
                    id_empresa_limpio = id_empresa
                    nombre_empresa_limpio = nombre_empresa

                    if "BIZUM" in concepto and detalle:
                        for prefijo in ["RECIBIDO:", "ENVIADO:", "COMPRA:"]:
                            if prefijo in detalle:
                                partes = detalle.split(prefijo, 1)
                                if len(partes) > 1:
                                    concepto_bizum = partes[1].strip()
                                break
                        operacion_limpia = "BIZUM"
                        id_empresa_limpio = ""
                        nombre_empresa_limpio = ""

                    # Determinar categoría y subcategoría
                    categoria, subcategoria = determinar_categoria(operacion_limpia, nombre_empresa_limpio)

                    # Limpiar importe y saldo (quitar puntos de miles)
                    importe_limpio = importe.replace('.', '').replace(',', '.')
                    saldo_limpio = saldo.replace('.', '').replace(',', '.')

                    try:
                        importe_float = float(importe_limpio)
                        saldo_float = float(saldo_limpio)
                        tipo = "INGRESO" if importe_float > 0 else "GASTO"

                        operaciones.append({
                            'año': año,
                            'mes': mes,
                            'fecha_operacion': f_oper,
                            'fecha_valor': f_valor,
                            'operacion': operacion_limpia,
                            'id_empresa': id_empresa_limpio,
                            'nombre_empresa': nombre_empresa_limpio,
                            'concepto': concepto_bizum,
                            'categoria': categoria,
                            'subcategoria': subcategoria,
                            'tipo': tipo,
                            'importe': abs(importe_float),
                            'saldo': saldo_float
                        })
                    except ValueError as e:
                        print(f"❌ Error convirtiendo números en línea: {linea}")
                        print(f"   Importe: {importe} -> {importe_limpio}")
                        print(f"   Saldo: {saldo} -> {saldo_limpio}")
                        print(f"   Error: {e}")

                i += 1

    return operaciones


def main():
    directorio = Path(".")
    archivos_pdf = list(directorio.glob("*.pdf"))

    if not archivos_pdf:
        return

    texto_completo = ""
    for archivo_pdf in archivos_pdf:
        texto_pdf = extraer_texto_pdf(archivo_pdf)
        texto_completo += texto_pdf + "\n" + "=" * 80 + "\n\n"

    if operaciones := procesar_operaciones(texto_completo):
        pd.DataFrame(operaciones).to_csv("../Archivos csv/operaciones.csv", index=False, encoding='utf-8')


if __name__ == "__main__":
    main()