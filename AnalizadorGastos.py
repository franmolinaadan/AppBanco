import pandas as pd
import os
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict
import warnings
import json
import shutil

warnings.filterwarnings('ignore')


class ConfigManager:
    def __init__(self, config_dir="config"):
        self.config_dir = config_dir
        self.crear_directorio_config()

        # Archivos de configuración
        self.archivo_metas = os.path.join(config_dir, "config_metas.json")
        self.archivo_alertas = os.path.join(config_dir, "config_alertas.json")
        self.archivo_usuario = os.path.join(config_dir, "config_usuario.json")
        self.archivo_analisis = os.path.join(config_dir, "config_analisis.json") # NUEVO

        # Configuraciones por defecto
        self.metas_default = self._metas_por_defecto()
        self.alertas_default = self._alertas_por_defecto()
        self.usuario_default = self._usuario_por_defecto()
        self.analisis_default = self._analisis_por_defecto() # NUEVO

    def crear_directorio_config(self):
        """Crea el directorio de configuración si no existe"""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            print(f"✅ Directorio de configuración creado: {self.config_dir}")

    def _metas_por_defecto(self):
        """Configuración por defecto de metas financieras"""
        return {
            "version": "1.0",
            "fecha_actualizacion": datetime.now().isoformat(),
            "metas_mensuales": {
                "ahorro_mensual": 200,
                "limite_comidas_fuera": 150,
                "limite_ocio": 100,
                "limite_compras_online": 200,
                "limite_transporte": 50,
                "limite_suscripciones": 30
            },
            "metas_anuales": {
                "ahorro_anual": 2400,
                "inversion_objetivo": 1000,
                "fondo_emergencia": 3000
            },
            "categorias_personalizadas": {
                "esenciales": ["Alimentacion", "Transporte", "Servicios"],
                "discrecionales": ["Ocio", "Compras", "Restaurantes"],
                "ahorro_inversion": ["Ahorro", "Inversion"]
            }
        }

    def _alertas_por_defecto(self):
        """Configuración por defecto del sistema de alertas"""
        return {
            "version": "1.0",
            "fecha_actualizacion": datetime.now().isoformat(),
            "alertas_activadas": True,
            "umbrales_alertas": {
                "gasto_inesperado": 50,
                "porcentaje_limite": 0.8,
                "cambio_significativo": 0.2,
                "frecuencia_alerta": "diaria"
            },
            "notificaciones": {
                "email": False,
                "consola": True,
                "archivo_log": True
            }
        }

    def _usuario_por_defecto(self):
        """Configuración por defecto del usuario"""
        return {
            "version": "1.0",
            "fecha_actualizacion": datetime.now().isoformat(),
            "ruta_csv": "operaciones.csv", # MEJORA: Ruta del CSV configurable
            "preferencias": {
                "moneda": "EUR",
                "formato_fecha": "DD/MM/YYYY",
                "idioma": "es",
                "tema": "claro",
                "mostrar_graficos": True,
                "resumen_automatico": True
            }
        }

    def _analisis_por_defecto(self):
        """NUEVA: Configuración para el análisis de gastos recurrentes"""
        return {
            "version": "1.0",
            "fecha_actualizacion": datetime.now().isoformat(),
            "gastos_fijos_mensuales": [
                {"nombre": "Gimnasio", "palabra_clave": "FitnessPark", "importe_exacto": 47.00},
                {"nombre": "Suscripción Apple", "palabra_clave": "APPLE.COM/BILL", "importe_exacto": 0.99},
                {"nombre": "Spotify Empresa", "palabra_clave": "Spotify", "importe_exacto": 17.99}
            ],
            "gastos_especiales_anuales": [
                {"nombre": "Universidad (Anual)", "palabra_clave": "UNIVERSIDADMIGUELHERNAN", "importe_exacto": 520.20}
            ],
            "operaciones_a_excluir_de_variables": ["BIZUM", "TRANSFERENCIA"],
            "umbral_compra_grande": 150.00,
            "categorias_a_ignorar_en_compras_grandes": ["ALIMENTACION", "SUPERMERCADO"]
        }


    def cargar_configuracion(self, archivo, config_default):
        """Carga la configuración desde un archivo JSON"""
        try:
            if os.path.exists(archivo):
                with open(archivo, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"✅ Configuración cargada: {os.path.basename(archivo)}")
                return config
            else:
                print(f"📝 Creando configuración por defecto: {os.path.basename(archivo)}")
                self.guardar_configuracion(archivo, config_default)
                return config_default
        except Exception as e:
            print(f"❌ Error cargando {archivo}: {e}")
            return config_default

    def guardar_configuracion(self, archivo, config):
        """Guarda la configuración en un archivo JSON"""
        try:
            config['fecha_actualizacion'] = datetime.now().isoformat()
            with open(archivo, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            print(f"💾 Configuración guardada: {os.path.basename(archivo)}")
            return True
        except Exception as e:
            print(f"❌ Error guardando {archivo}: {e}")
            return False

    def cargar_todas_configuraciones(self):
        """Carga todas las configuraciones"""
        metas = self.cargar_configuracion(self.archivo_metas, self.metas_default)
        alertas = self.cargar_configuracion(self.archivo_alertas, self.alertas_default)
        usuario = self.cargar_configuracion(self.archivo_usuario, self.usuario_default)
        analisis = self.cargar_configuracion(self.archivo_analisis, self.analisis_default) # NUEVO

        return {
            'metas': metas,
            'alertas': alertas,
            'usuario': usuario,
            'analisis': analisis # NUEVO
        }

    def guardar_todas_configuraciones(self, configs):
        """Guarda todas las configuraciones"""
        resultados = {
            'metas': self.guardar_configuracion(self.archivo_metas, configs['metas']),
            'alertas': self.guardar_configuracion(self.archivo_alertas, configs['alertas']),
            'usuario': self.guardar_configuracion(self.archivo_usuario, configs['usuario']),
            'analisis': self.guardar_configuracion(self.archivo_analisis, configs['analisis']) # NUEVO
        }
        return resultados

    def mostrar_configuracion(self, config, nombre):
        """Muestra la configuración de forma legible"""
        print(f"\n{' ' + nombre.upper() + ' ':=^60}")
        self._mostrar_recursivo(config, "  ")
        print("=" * 60)

    def _mostrar_recursivo(self, data, prefijo):
        """Muestra datos recursivamente con formato"""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    print(f"{prefijo}├─ {key}:")
                    nuevo_prefijo = prefijo + "│  "
                    self._mostrar_recursivo(value, nuevo_prefijo)
                else:
                    print(f"{prefijo}├─ {key}: {value}")
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    print(f"{prefijo}├─ [{i}]:")
                    self._mostrar_recursivo(item, prefijo + "│  ")
                else:
                    print(f"{prefijo}├─ {item}")

    def resetear_configuracion(self, tipo):
        """Resetea una configuración a los valores por defecto"""
        archivos = {
            'metas': (self.archivo_metas, self.metas_default),
            'alertas': (self.archivo_alertas, self.alertas_default),
            'usuario': (self.archivo_usuario, self.usuario_default),
            'todo': None
        }

        if tipo == 'todo':
            for archivo, default in archivos.values():
                if archivo:  # Evitar el 'todo'
                    self.guardar_configuracion(archivo, default)
            print("✅ Todas las configuraciones reseteadas")
        elif tipo in archivos:
            archivo, default = archivos[tipo]
            self.guardar_configuracion(archivo, default)
            print(f"✅ Configuración {tipo} reseteada")
        else:
            print("❌ Tipo de configuración no válido")

    def crear_respaldo(self, ruta_destino=None):
        """Crea un respaldo de todas las configuraciones"""
        if ruta_destino is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ruta_destino = f"backup_config_{timestamp}"

        if not os.path.exists(ruta_destino):
            os.makedirs(ruta_destino)

        archivos = [self.archivo_metas, self.archivo_alertas, self.archivo_usuario]

        for archivo in archivos:
            if os.path.exists(archivo):
                nombre_archivo = os.path.basename(archivo)
                destino = os.path.join(ruta_destino, nombre_archivo)
                shutil.copy2(archivo, destino)
                print(f"📦 Respaldo creado: {destino}")

        print(f"✅ Respaldo completo en: {ruta_destino}")
        return ruta_destino


class AnalizadorGastos:
    def __init__(self):
        # Sistema de configuración
        self.config_manager = ConfigManager()
        self.configs = self.config_manager.cargar_todas_configuraciones()

        self.csv_path = self.configs['usuario']['ruta_csv']
        self.df = self.cargar_datos()

        # ---- INICIO DEL ARREGLO: Mover este bloque HACIA ARRIBA ----
        # Cargar configuraciones específicas ANTES de usarlas
        self.metas = self.configs['metas']['metas_mensuales']
        self.alertas_config = self.configs['alertas']
        self.preferencias = self.configs['usuario']['preferencias']
        self.analisis_config = self.configs['analisis']
        # ---- FIN DEL ARREGLO ----

        # Ahora este bloque funcionará porque self.preferencias ya existe
        if self.df is not None and not self.df.empty:
            ultimo_registro = self.df.sort_values(by=['año', 'mes']).iloc[-1]
            self.ultimo_mes = int(ultimo_registro['mes'])
            self.ultimo_año = int(ultimo_registro['año'])
            print(
                f"ℹ️  Análisis enfocado en el último mes con datos: {self.nombre_mes(self.ultimo_mes)} {self.ultimo_año}")
        else:
            self.ultimo_mes = datetime.now().month
            self.ultimo_año = datetime.now().year

        self.alertas_activas = []

    def cargar_datos(self):
        """Carga y limpia el CSV con los datos de gastos."""
        if not os.path.exists(self.csv_path):
            print(f"❌ Error: No se encuentra el archivo {self.csv_path}")
            return None

        try:
            df = pd.read_csv(self.csv_path, encoding='utf-8-sig')

            # ---- INICIO DEL ARREGLO: Renombrar columnas antiguas si existen ----
            columnas_a_renombrar = {
                'Categoria_Principal': 'categoria',
                'Subcategoria': 'subcategoria',
                'Año': 'año',
                'Mes': 'mes'
            }
            df.rename(columns=columnas_a_renombrar, inplace=True)
            # ---- FIN DEL ARREGLO ----

            # --- MEJORAS EN LIMPIEZA DE DATOS ---
            # 1. Convertir a datetime real
            df['fecha_operacion'] = pd.to_datetime(df['fecha_operacion'], format='%d/%m')

            # 2. Convertir mes de texto a número si es necesario
            if 'mes' in df.columns and df['mes'].dtype == 'object':
                meses_dict = {
                    'ENERO': 1, 'FEBRERO': 2, 'MARZO': 3, 'ABRIL': 4, 'MAYO': 5, 'JUNIO': 6,
                    'JULIO': 7, 'AGOSTO': 8, 'SEPTIEMBRE': 9, 'OCTUBRE': 10, 'NOVIEMBRE': 11, 'DICIEMBRE': 12
                }
                df['mes'] = df['mes'].str.upper().map(meses_dict)

            # 3. Asegurar que importe es numérico
            df['importe'] = pd.to_numeric(df['importe'], errors='coerce')
            df.dropna(subset=['importe'], inplace=True)  # Eliminar filas donde el importe no sea válido

            # ---- NUEVA LÍNEA: Guardar el índice original para desempates ----
            df.reset_index(inplace=True)
            # ----------------------------------------------------------------

            print(f"✅ Datos cargados: {len(df)} transacciones")
            return df

        except Exception as e:
            print(f"❌ Error cargando CSV: {e}")
            return None

    def obtener_resumen_ultimo_mes(self):
        """Calcula el resumen financiero del mes actual."""
        if self.df is None: return None

        mes_actual_df = self.df[
            (self.df['año'] == self.ultimo_año) &
            (self.df['mes'] == self.ultimo_mes)
            ]

        total_ingresos = mes_actual_df[mes_actual_df['tipo'] == 'INGRESO']['importe'].sum()
        total_gastos = mes_actual_df[mes_actual_df['tipo'] == 'GASTO']['importe'].sum()
        balance = total_ingresos - total_gastos

        # MEJORA: Obtener el saldo de forma segura ordenando por fecha e índice original
        if not mes_actual_df.empty:
            saldo_actual = mes_actual_df.sort_values(by=['fecha_operacion', 'index']).iloc[-1]['saldo']
        else:
            # Si el último mes no tiene datos (improbable), busca el último saldo detodo el historial
            saldo_actual = self.df.sort_values(by=['fecha_operacion', 'index']).iloc[-1][
                'saldo'] if not self.df.empty else 0

        return {
            'transacciones': len(mes_actual_df),
            'ingresos': total_ingresos,
            'gastos': total_gastos,
            'balance': balance,
            'saldo_actual': saldo_actual
        }

    def mostrar_cabecera(self):
        """Muestra la cabecera con el resumen del mes actual"""
        resumen = self.obtener_resumen_ultimo_mes()
        if resumen is None: return

        print("\n" + "=" * 70)
        print(f"💰 RESUMEN DEL ÚLTIMO MES - {self.nombre_mes(self.ultimo_mes).upper()} {self.ultimo_año}")
        print("=" * 70)
        print(f"💵 Total ingresos:        {resumen['ingresos']:>10.2f}€")
        print(f"💸 Total gastos:          {resumen['gastos']:>10.2f}€")
        print(f"⚖️  Balance:               {resumen['balance']:>10.2f}€")
        print(f"🏦 Saldo final del mes:   {resumen['saldo_actual']:>10.2f}€")
        print("=" * 70)

        self.mostrar_seguimiento_metas()

    def mostrar_seguimiento_metas(self):
        """
        NUEVA FUNCIÓN: Muestra el progreso visual de las metas de gasto para el último mes.
        """
        # Filtrar los datos para obtener solo los del último mes analizado
        df_mes = self.df[(self.df['año'] == self.ultimo_año) & (self.df['mes'] == self.ultimo_mes)]
        gastos_mes = df_mes[df_mes['tipo'] == 'GASTO']

        print(f"\n🎯 SEGUIMIENTO DE METAS - {self.nombre_mes(self.ultimo_mes).upper()} {self.ultimo_año}")
        print("-" * 70)

        if not self.metas:
            print("  No hay metas definidas en config_metas.json")
            return

        for meta, limite in self.metas.items():
            # Asegurarse de que solo procesamos las metas de límite de gasto
            if meta.startswith("limite_"):
                # Extraer el nombre de la categoría del nombre de la meta
                categoria = meta.replace("limite_", "").upper()

                # Calcular el gasto actual para esa categoría en el mes
                gasto_actual = gastos_mes[gastos_mes['categoria'].str.upper() == categoria]['importe'].sum()

                # Calcular el porcentaje y la barra de progreso
                porcentaje = (gasto_actual / limite) * 100 if limite > 0 else 0
                # Asegurarse de que la barra no exceda los 10 caracteres
                bloques_llenos = min(10, int(porcentaje / 10))
                barra = "█" * bloques_llenos + "-" * (10 - bloques_llenos)

                # Añadir un emoji de estado visual
                emoji = "⚠️" if porcentaje > 100 else "✅" if porcentaje <= 80 else "🤔"

                print(
                    f"  - {categoria.capitalize():15} [{barra}] {gasto_actual:.2f}€ / {limite:.2f}€ ({porcentaje:.0f}%) {emoji}")

        print("-" * 70)

    def mostrar_menu_principal(self):
        """Muestra el menú principal"""
        print("\n📋 MENÚ PRINCIPAL")
        print("1. 📄 Mostrar transacciones")
        print("2. 🏷️  Buscar por categoría")
        print("3. 🏢 Buscar por empresa")
        print("4. 📈 Estadísticas generales")
        print("5. ⚙️  Configuración")
        print("6. 🚪 Salir")

    def obtener_meses_disponibles(self):
        """Obtiene lista de meses/años disponibles ordenados"""
        if self.df is None:
            return []

        # CORREGIDO: Usar columnas en minúsculas
        meses = self.df[['año', 'mes']].drop_duplicates().sort_values(['año', 'mes'])
        return [(row['año'], row['mes']) for _, row in meses.iterrows()]

    def nombre_mes(self, numero_mes):
        """Devuelve el nombre del mes desde la configuración."""
        try:
            idioma = self.preferencias.get('idioma', 'es')
            meses = self.configs['usuario']['locale'][idioma]['meses']
            return meses.get(str(numero_mes), f'Mes {numero_mes}')
        except KeyError:
            # Si falla, usa un metodo de respaldo para no detener el programa
            return datetime(1900, numero_mes, 1).strftime('%B').capitalize()

    def mostrar_submenu_meses(self, titulo):
        """Muestra submenú para seleccionar mes"""
        meses = self.obtener_meses_disponibles()

        print(f"\n{titulo}")
        print("0. ↩️  Volver al menú anterior")
        print("1. 📅 Ver todos los meses")

        for i, (año, mes) in enumerate(meses, 2):
            print(f"{i}. {self.nombre_mes(mes)} {año}")

        return meses

    def mostrar_submenu_meses_con_totales(self, filtro_df, titulo):
        """
        Muestra un submenú de meses con el total del importe para cada mes.
        Utiliza un DataFrame ya filtrado para los cálculos.
        """
        if filtro_df is None or filtro_df.empty:
            print("\n❌ No hay transacciones para esta selección.")
            return []

        # Agrupar por año y mes para sumar los importes
        totales_por_mes = filtro_df.groupby(['año', 'mes'])['importe'].sum()

        # Obtener la lista de meses únicos de los datos ya filtrados
        meses_disponibles = filtro_df[['año', 'mes']].drop_duplicates().sort_values(['año', 'mes'])
        meses = [(row['año'], row['mes']) for _, row in meses_disponibles.iterrows()]

        print(f"\n{titulo}")
        print("0. ↩️  Volver al menú anterior")
        print("1. 📅 Ver todos los meses")

        # Muestra cada mes con su total correspondiente
        for i, (año, mes) in enumerate(meses, 2):
            total_mes = totales_por_mes.get((año, mes), 0)
            print(f"{i}. {self.nombre_mes(mes)} {año} (Total: {total_mes:.2f}€)")

        return meses

    def mostrar_transacciones_mes(self, año, mes):
        """Muestra transacciones de un mes específico - ACTUALIZADO"""
        if self.df is None:
            return

        transacciones_mes = self.df[
            (self.df['año'] == año) &
            (self.df['mes'] == mes)
            ].sort_values('fecha_operacion')

        print(f"\n📄 TRANSACCIONES - {self.nombre_mes(mes)} {año}")
        print("=" * 120)
        print(f"{'Fecha':10} {'Operación':15} {'Concepto':25} {'Empresa':20} {'Importe':>10} {'Categoría':15}")
        print("-" * 120)

        for _, trans in transacciones_mes.iterrows():
            # Para Bizums, mostrar concepto; para otros, mostrar operación
            if pd.notna(trans.get('concepto')) and trans['concepto'] != '':
                descripcion = trans['concepto'][:23] + '..' if len(trans['concepto']) > 25 else trans['concepto']
            else:
                descripcion = trans['operacion'][:23] + '..' if len(trans['operacion']) > 25 else trans['operacion']

            empresa = str(trans['nombre_empresa'])[:18] + '..' if len(str(trans['nombre_empresa'])) > 20 else str(
                trans['nombre_empresa'])

            # Formatear importe según tipo
            if trans['tipo'] == 'INGRESO':
                importe_str = f"+{trans['importe']:>7.2f}€"
            else:
                importe_str = f"-{trans['importe']:>7.2f}€"

            categoria = trans['categoria'][:13] + '..' if len(trans['categoria']) > 15 else trans['categoria']

            print(
                f"{trans['fecha_operacion']:10} {trans['operacion'][:13]:15} {descripcion:25} {empresa:20} {importe_str:>10} {categoria:15}")

        # Resumen del mes (actualizado)
        ingresos = transacciones_mes[transacciones_mes['tipo'] == 'INGRESO']['importe'].sum()
        gastos = transacciones_mes[transacciones_mes['tipo'] == 'GASTO']['importe'].sum()

        print("-" * 120)
        print(
            f"{'RESUMEN:':76} Ingresos: {ingresos:>8.2f}€ | Gastos: {gastos:>8.2f}€ | Balance: {(ingresos - gastos):>8.2f}€")

    def opcion_transacciones(self):
        """Maneja la opción de mostrar transacciones"""
        while True:
            meses = self.mostrar_submenu_meses("📅 SELECCIONAR MES")

            try:
                opcion = int(input("\n👉 Selecciona una opción: "))

                if opcion == 0:
                    break
                elif opcion == 1:
                    # Mostrar todos los meses
                    for año, mes in meses:
                        self.mostrar_transacciones_mes(año, mes)
                        input("\n⏎ Presiona Enter para continuar...")
                elif 2 <= opcion <= len(meses) + 1:
                    # Mostrar mes específico
                    año, mes = meses[opcion - 2]
                    self.mostrar_transacciones_mes(año, mes)
                    input("\n⏎ Presiona Enter para continuar...")
                else:
                    print("❌ Opción no válida")

            except ValueError:
                print("❌ Por favor, introduce un número válido")

    def opcion_buscar_categoria(self):
        """Maneja la opción de buscar por categoría - MEJORADO"""
        while True:
            print("\n🏷️  BUSCAR POR CATEGORÍA")
            print("0. ↩️  Volver al menú anterior")
            print("1. 💵 Ingresos")
            print("2. 💸 Gastos")

            try:
                opcion = int(input("\n👉 Selecciona una opción: "))

                if opcion == 0:
                    break
                elif opcion == 1:
                    self.mostrar_categorias_ingresos()
                elif opcion == 2:
                    self.mostrar_categorias_gastos()
                else:
                    print("❌ Opción no válida")

            except ValueError:
                print("❌ Por favor, introduce un número válido")

    def mostrar_categorias_ingresos(self):
        """Muestra categorías de ingresos - ACTUALIZADO"""
        if self.df is None:
            return

        # CAMBIO: Usar columna 'tipo' en lugar del signo de Importe
        categorias_ingresos = self.df[
            self.df['tipo'] == 'INGRESO'
            ]['categoria'].unique()  # CAMBIO: 'Categoria_Principal' → 'categoria'

        print("\n💵 CATEGORÍAS DE INGRESOS")
        print("0. ↩️  Volver al menú anterior")

        for i, cat in enumerate(sorted(categorias_ingresos), 1):
            print(f"{i}. {cat}")

        try:
            opcion = int(input("\n👉 Selecciona una opción: "))

            if opcion == 0:
                return
            elif 1 <= opcion <= len(categorias_ingresos):
                categoria_seleccionada = sorted(categorias_ingresos)[opcion - 1]
                self.mostrar_ingresos_categoria(categoria_seleccionada)
            else:
                print("❌ Opción no válida")

        except ValueError:
            print("❌ Por favor, introduce un número válido")

    def mostrar_categorias_gastos(self):
        """Muestra categorías de gastos - ACTUALIZADO"""
        if self.df is None:
            return

        # CAMBIO: Usar columna 'tipo' en lugar del signo de Importe
        categorias_gastos = self.df[
            self.df['tipo'] == 'GASTO'
            ]['categoria'].unique()  # CAMBIO: 'Categoria_Principal' → 'categoria'

        print("\n💸 CATEGORÍAS DE GASTOS")
        print("0. ↩️  Volver al menú anterior")
        print(f"{len(categorias_gastos) + 1}. 📊 Ver todas las subcategorías de gastos")

        for i, cat in enumerate(sorted(categorias_gastos), 1):
            print(f"{i}. {cat}")

        try:
            opcion = int(input("\n👉 Selecciona una opción: "))

            if opcion == 0:
                return
            elif 1 <= opcion <= len(categorias_gastos):
                categoria_seleccionada = sorted(categorias_gastos)[opcion - 1]
                self.mostrar_gastos_categoria(categoria_seleccionada)
            elif opcion == len(categorias_gastos) + 1:
                self.mostrar_subcategorias_gastos()
            else:
                print("❌ Opción no válida")

        except ValueError:
            print("❌ Por favor, introduce un número válido")

    def mostrar_ingresos_categoria(self, categoria):
        """Muestra ingresos por categoría - ACTUALIZADO"""
        filtro = self.df[
            (self.df['categoria'] == categoria) &
            (self.df['tipo'] == 'INGRESO')
            ]

        while True:
            # ANTES:
            # meses = self.mostrar_submenu_meses(f"💵 Ingresos - {categoria}")
            # AHORA: Usamos la nueva función con el DataFrame filtrado
            meses = self.mostrar_submenu_meses_con_totales(filtro, f"💵 Ingresos - {categoria}")

            try:
                opcion = int(input("\n👉 Selecciona una opción: "))

                if opcion == 0:
                    break
                elif opcion == 1:
                    # Mostrar todos los meses
                    for año, mes in meses:
                        self.mostrar_ingresos_categoria_mes(filtro, año, mes, categoria)
                        input("\n⏎ Presiona Enter para continuar...")
                elif 2 <= opcion <= len(meses) + 1:
                    # Mostrar mes específico
                    año, mes = meses[opcion - 2]
                    self.mostrar_ingresos_categoria_mes(filtro, año, mes, categoria)
                    input("\n⏎ Presiona Enter para continuar...")
                else:
                    print("❌ Opción no válida")

            except ValueError:
                print("❌ Por favor, introduce un número válido")

    def mostrar_ingresos_categoria_mes(self, filtro, año, mes, categoria):
        """Muestra ingresos de categoría por mes específico - ACTUALIZADO"""
        # CAMBIO: Usar nombres de columnas actualizados
        ingresos_mes = filtro[
            (filtro['año'] == año) &  # CAMBIO: 'Año' → 'año'
            (filtro['mes'] == mes)  # CAMBIO: 'Mes' → 'mes'
            ].sort_values('fecha_operacion')  # CAMBIO: 'Fecha_Operacion' → 'fecha_operacion'

        print(f"\n💵 {categoria} - {self.nombre_mes(mes)} {año}")
        print("=" * 100)
        print(f"{'Fecha':10} {'Concepto':40} {'Empresa':25} {'Importe':>10} {'Subcategoría':15}")
        print("-" * 100)

        total_ingresos = 0

        for _, ingreso in ingresos_mes.iterrows():
            # Para Bizums mostrar concepto, para otros mostrar operación
            if pd.notna(ingreso.get('concepto')) and ingreso['concepto'] != '':
                descripcion = ingreso['concepto'][:38] + '..' if len(ingreso['concepto']) > 40 else ingreso['concepto']
            else:
                descripcion = ingreso['operacion'][:38] + '..' if len(ingreso['operacion']) > 40 else ingreso[
                    'operacion']

            empresa = str(ingreso['nombre_empresa'])[:23] + '..' if len(str(ingreso['nombre_empresa'])) > 25 else str(
                ingreso['nombre_empresa'])

            # Importe siempre positivo para ingresos
            importe_str = f"+{ingreso['importe']:>7.2f}€"

            subcat = str(ingreso['subcategoria'])[:13] + '..' if len(str(ingreso['subcategoria'])) > 15 else str(ingreso['subcategoria'])

            print(f"{ingreso['fecha_operacion']:10} {descripcion:40} {empresa:25} {importe_str:>10} {subcat:15}")
            total_ingresos += ingreso['importe']  # CAMBIO: 'Importe' → 'importe'

        print("-" * 100)
        print(f"{'TOTAL INGRESOS:':76} {total_ingresos:>8.2f}€")

    def mostrar_gastos_categoria(self, categoria, subcategoria=None):
        """Muestra gastos por categoría - ACTUALIZADO"""
        if subcategoria:
            filtro = self.df[
                (self.df['subcategoria'] == subcategoria) &
                (self.df['tipo'] == 'GASTO')
                ]
            titulo = f"Gastos - {categoria} > {subcategoria}"
        else:
            filtro = self.df[
                (self.df['categoria'] == categoria) &
                (self.df['tipo'] == 'GASTO')
                ]
            titulo = f"Gastos - {categoria}"

        while True:
            # ANTES:
            # meses = self.mostrar_submenu_meses(f"📊 {titulo}")
            # AHORA: Usamos la nueva función con el DataFrame filtrado
            meses = self.mostrar_submenu_meses_con_totales(filtro, f"📊 {titulo}")

            try:
                opcion = int(input("\n👉 Selecciona una opción: "))

                if opcion == 0:
                    break
                elif opcion == 1:
                    # Mostrar todos los meses
                    for año, mes in meses:
                        self.mostrar_gastos_categoria_mes(filtro, año, mes, categoria, subcategoria)
                        input("\n⏎ Presiona Enter para continuar...")
                elif 2 <= opcion <= len(meses) + 1:
                    # Mostrar mes específico
                    año, mes = meses[opcion - 2]
                    self.mostrar_gastos_categoria_mes(filtro, año, mes, categoria, subcategoria)
                    input("\n⏎ Presiona Enter para continuar...")
                else:
                    print("❌ Opción no válida")

            except ValueError:
                print("❌ Por favor, introduce un número válido")

    def mostrar_gastos_categoria_mes(self, filtro, año, mes, categoria, subcategoria=None):
        """Muestra gastos de categoría por mes específico - ACTUALIZADO"""
        # CAMBIO: Usar nombres de columnas actualizados
        gastos_mes = filtro[
            (filtro['año'] == año) &  # CAMBIO: 'Año' → 'año'
            (filtro['mes'] == mes)  # CAMBIO: 'Mes' → 'mes'
            ].sort_values('fecha_operacion')  # CAMBIO: 'Fecha_Operacion' → 'fecha_operacion'

        if subcategoria:
            titulo = f"{categoria} > {subcategoria} - {self.nombre_mes(mes)} {año}"
        else:
            titulo = f"{categoria} - {self.nombre_mes(mes)} {año}"

        print(f"\n📊 {titulo}")
        print("=" * 100)
        print(f"{'Fecha':10} {'Concepto':40} {'Empresa':25} {'Importe':>10} {'Subcategoría':15}")
        print("-" * 100)

        total_gastos = 0

        for _, gasto in gastos_mes.iterrows():
            # Para Bizums mostrar concepto, para otros mostrar operación
            if pd.notna(gasto.get('concepto')) and gasto['concepto'] != '':
                descripcion = gasto['concepto'][:38] + '..' if len(gasto['concepto']) > 40 else gasto['concepto']
            else:
                descripcion = gasto['operacion'][:38] + '..' if len(gasto['operacion']) > 40 else gasto['operacion']

            empresa = str(gasto['nombre_empresa'])[:23] + '..' if len(str(gasto['nombre_empresa'])) > 25 else str(
                gasto['nombre_empresa'])

            # Importe siempre negativo para gastos
            importe_str = f"-{gasto['importe']:>7.2f}€"

            subcat = str(gasto['subcategoria'])[:13] + '..' if len(str(gasto['subcategoria'])) > 15 else str(gasto['subcategoria'])

            print(f"{gasto['fecha_operacion']:10} {descripcion:40} {empresa:25} {importe_str:>10} {subcat:15}")
            total_gastos += gasto['importe']  # CAMBIO: Eliminar abs() porque 'importe' es positivo

        print("-" * 100)
        print(f"{'TOTAL GASTOS:':76} {total_gastos:>8.2f}€")

    def mostrar_subcategorias_gastos(self):
        """Muestra submenú de subcategorías de gastos - ACTUALIZADO"""
        # CORREGIDO: Usar 'tipo' y columnas en minúsculas
        subcategorias = sorted(self.df[
                                   self.df['tipo'] == 'GASTO'
                                   ]['subcategoria'].unique())

        print("\n📊 SUBCATEGORÍAS DE GASTOS")
        print("0. ↩️  Volver al menú anterior")

        for i, subcat in enumerate(subcategorias, 1):
            # Obtener categoría principal para esta subcategoría - CORREGIDO
            cat_principal = self.df[self.df['subcategoria'] == subcat]['categoria'].iloc[0]
            print(f"{i}. {cat_principal} > {subcat}")

        try:
            opcion = int(input("\n👉 Selecciona una opción: "))

            if opcion == 0:
                return
            elif 1 <= opcion <= len(subcategorias):
                subcat_seleccionada = subcategorias[opcion - 1]
                cat_principal = self.df[self.df['subcategoria'] == subcat_seleccionada]['categoria'].iloc[0]
                self.mostrar_gastos_categoria(cat_principal, subcat_seleccionada)
            else:
                print("❌ Opción no válida")

        except ValueError:
            print("❌ Por favor, introduce un número válido")

    def opcion_buscar_empresa(self):
        """Maneja la opción de buscar por empresa - MEJORADO"""
        while True:
            print("\n🏢 BUSCAR POR EMPRESA")
            print("0. ↩️  Volver al menú anterior")
            print("1. 💵 Empresas de ingresos")
            print("2. 💸 Empresas de gastos")
            print("3. 🔍 Buscar empresa por nombre")

            try:
                opcion = int(input("\n👉 Selecciona una opción: "))

                if opcion == 0:
                    break
                elif opcion == 1:
                    self.mostrar_empresas_ingresos()
                elif opcion == 2:
                    self.mostrar_empresas_gastos()
                elif opcion == 3:
                    self.buscar_empresa_por_nombre()
                else:
                    print("❌ Opción no válida")

            except ValueError:
                print("❌ Por favor, introduce un número válido")

    def mostrar_empresas_ingresos(self):
        """Muestra empresas de ingresos - ACTUALIZADO"""
        if self.df is None:
            return

        # CAMBIO: Usar columna 'tipo' y nombres de columnas actualizados
        empresas_ingresos = self.df[
            (self.df['tipo'] == 'INGRESO') &  # CAMBIO: 'Importe' > 0 → 'tipo' == 'INGRESO'
            (self.df['nombre_empresa'] != '')  # CAMBIO: 'Nombre_Empresa' → 'nombre_empresa'
            ]['nombre_empresa'].value_counts().head(15)  # CAMBIO: 'Nombre_Empresa' → 'nombre_empresa'

        print("\n💵 EMPRESAS DE INGRESOS")
        print("0. ↩️  Volver al menú anterior")

        for i, (empresa, count) in enumerate(empresas_ingresos.items(), 1):
            print(f"{i}. {empresa[:40]:40} ({count} transacciones)")

        try:
            opcion = int(input("\n👉 Selecciona una opción: "))

            if opcion == 0:
                return
            elif 1 <= opcion <= len(empresas_ingresos):
                empresa_seleccionada = empresas_ingresos.index[opcion - 1]
                self.mostrar_ingresos_empresa(empresa_seleccionada)
            else:
                print("❌ Opción no válida")

        except ValueError:
            print("❌ Por favor, introduce un número válido")

    def mostrar_empresas_gastos(self):
        """Muestra empresas de gastos - ACTUALIZADO"""
        if self.df is None:
            return

        # CAMBIO: Usar columna 'tipo' y nombres de columnas actualizados
        empresas_gastos = self.df[
            (self.df['tipo'] == 'GASTO') &  # CAMBIO: 'Importe' < 0 → 'tipo' == 'GASTO'
            (self.df['nombre_empresa'] != '')  # CAMBIO: 'Nombre_Empresa' → 'nombre_empresa'
            ]['nombre_empresa'].value_counts().head(15)  # CAMBIO: 'Nombre_Empresa' → 'nombre_empresa'

        print("\n💸 EMPRESAS DE GASTOS")
        print("0. ↩️  Volver al menú anterior")

        for i, (empresa, count) in enumerate(empresas_gastos.items(), 1):
            print(f"{i}. {empresa[:40]:40} ({count} transacciones)")

        try:
            opcion = int(input("\n👉 Selecciona una opción: "))

            if opcion == 0:
                return
            elif 1 <= opcion <= len(empresas_gastos):
                empresa_seleccionada = empresas_gastos.index[opcion - 1]
                self.mostrar_gastos_empresa(empresa_seleccionada)
            else:
                print("❌ Opción no válida")

        except ValueError:
            print("❌ Por favor, introduce un número válido")

    def mostrar_ingresos_empresa(self, empresa):
        """Muestra ingresos por empresa - ACTUALIZADO"""
        # CAMBIO: Usar nombres de columnas actualizados y filtro por 'tipo'
        filtro = self.df[
            (self.df['nombre_empresa'] == empresa) &  # CAMBIO: 'Nombre_Empresa' → 'nombre_empresa'
            (self.df['tipo'] == 'INGRESO')  # CAMBIO: 'Importe' > 0 → 'tipo' == 'INGRESO'
            ]

        while True:
            meses = self.mostrar_submenu_meses(f"💵 {empresa}")

            try:
                opcion = int(input("\n👉 Selecciona una opción: "))

                if opcion == 0:
                    break
                elif opcion == 1:
                    # Mostrar todos los meses
                    for año, mes in meses:
                        self.mostrar_ingresos_empresa_mes(filtro, año, mes, empresa)
                        input("\n⏎ Presiona Enter para continuar...")
                elif 2 <= opcion <= len(meses) + 1:
                    # Mostrar mes específico
                    año, mes = meses[opcion - 2]
                    self.mostrar_ingresos_empresa_mes(filtro, año, mes, empresa)
                    input("\n⏎ Presiona Enter para continuar...")
                else:
                    print("❌ Opción no válida")

            except ValueError:
                print("❌ Por favor, introduce un número válido")

    def mostrar_ingresos_empresa_mes(self, filtro, año, mes, empresa):
        """Muestra ingresos de empresa por mes específico - ACTUALIZADO"""
        # CAMBIO: Usar nombres de columnas actualizados
        ingresos_mes = filtro[
            (filtro['año'] == año) &  # CAMBIO: 'Año' → 'año'
            (filtro['mes'] == mes)  # CAMBIO: 'Mes' → 'mes'
            ].sort_values('fecha_operacion')  # CAMBIO: 'Fecha_Operacion' → 'fecha_operacion'

        print(f"\n💵 {empresa} - {self.nombre_mes(mes)} {año}")
        print("=" * 100)
        print(f"{'Fecha':10} {'Concepto':40} {'Categoría':25} {'Importe':>10} {'Subcategoría':15}")
        print("-" * 100)

        total_ingresos = 0

        for _, trans in ingresos_mes.iterrows():
            # Para Bizums mostrar concepto, para otros mostrar operación
            if pd.notna(trans.get('concepto')) and trans['concepto'] != '':
                descripcion = trans['concepto'][:38] + '..' if len(trans['concepto']) > 40 else trans['concepto']
            else:
                descripcion = trans['operacion'][:38] + '..' if len(trans['operacion']) > 40 else trans['operacion']

            categoria = trans['categoria'][:23] + '..' if len(trans['categoria']) > 25 else trans['categoria']

            # Importe siempre positivo para ingresos
            importe_str = f"+{trans['importe']:>7.2f}€"

            subcat = str(trans['subcategoria'])[:13] + '..' if len(str(trans['subcategoria'])) > 15 else str(trans['subcategoria'])

            print(f"{trans['fecha_operacion']:10} {descripcion:40} {categoria:25} {importe_str:>10} {subcat:15}")
            total_ingresos += trans['importe']  # CAMBIO: 'Importe' → 'importe'

        print("-" * 100)
        print(f"{'TOTAL INGRESOS:':76} {total_ingresos:>8.2f}€")

    def buscar_empresa_por_nombre(self):
        """Busca empresa por nombre - ACTUALIZADO"""
        nombre_buscar = input("\n🔍 Introduce el nombre de la empresa a buscar: ").strip()

        if not nombre_buscar:
            return

        # CORREGIDO: Usar columna en minúsculas
        empresas_encontradas = self.df[
            self.df['nombre_empresa'].str.contains(nombre_buscar, case=False, na=False)
        ]['nombre_empresa'].value_counts()

        if empresas_encontradas.empty:
            print("❌ No se encontraron empresas con ese nombre")
            return

        print(f"\n📋 EMPRESAS ENCONTRADAS ({len(empresas_encontradas)})")
        print("0. ↩️  Volver al menú anterior")

        for i, (empresa, count) in enumerate(empresas_encontradas.items(), 1):
            print(f"{i}. {empresa[:50]:50} ({count} transacciones)")

        try:
            opcion = int(input("\n👉 Selecciona una empresa: "))

            if opcion == 0:
                return
            elif 1 <= opcion <= len(empresas_encontradas):
                empresa_seleccionada = empresas_encontradas.index[opcion - 1]
                # Determinar si mostrar ingresos o gastos basado en el tipo predominante - CORREGIDO
                transacciones_empresa = self.df[self.df['nombre_empresa'] == empresa_seleccionada]

                if len(transacciones_empresa[transacciones_empresa['tipo'] == 'INGRESO']) > len(
                        transacciones_empresa[transacciones_empresa['tipo'] == 'GASTO']):
                    self.mostrar_ingresos_empresa(empresa_seleccionada)
                else:
                    self.mostrar_gastos_empresa(empresa_seleccionada)
            else:
                print("❌ Opción no válida")

        except ValueError:
            print("❌ Por favor, introduce un número válido")

    def mostrar_gastos_empresa(self, empresa):
        """Muestra gastos por empresa - ACTUALIZADO"""
        # CAMBIO: Usar nombres de columnas actualizados y filtro por 'tipo'
        filtro = self.df[
            (self.df['nombre_empresa'] == empresa) &  # CAMBIO: 'Nombre_Empresa' → 'nombre_empresa'
            (self.df['tipo'] == 'GASTO')  # CAMBIO: 'Importe' < 0 → 'tipo' == 'GASTO'
            ]

        while True:
            meses = self.mostrar_submenu_meses(f"🏢 {empresa}")

            try:
                opcion = int(input("\n👉 Selecciona una opción: "))

                if opcion == 0:
                    break
                elif opcion == 1:
                    # Mostrar todos los meses
                    for año, mes in meses:
                        self.mostrar_gastos_empresa_mes(filtro, año, mes, empresa)
                        input("\n⏎ Presiona Enter para continuar...")
                elif 2 <= opcion <= len(meses) + 1:
                    # Mostrar mes específico
                    año, mes = meses[opcion - 2]
                    self.mostrar_gastos_empresa_mes(filtro, año, mes, empresa)
                    input("\n⏎ Presiona Enter para continuar...")
                else:
                    print("❌ Opción no válida")

            except ValueError:
                print("❌ Por favor, introduce un número válido")

    def mostrar_gastos_empresa_mes(self, filtro, año, mes, empresa):
        """Muestra gastos de empresa por mes específico - ACTUALIZADO"""
        # CAMBIO: Usar nombres de columnas actualizados
        gastos_mes = filtro[
            (filtro['año'] == año) &  # CAMBIO: 'Año' → 'año'
            (filtro['mes'] == mes)  # CAMBIO: 'Mes' → 'mes'
            ].sort_values('fecha_operacion')  # CAMBIO: 'Fecha_Operacion' → 'fecha_operacion'

        print(f"\n🏢 {empresa} - {self.nombre_mes(mes)} {año}")
        print("=" * 100)
        print(f"{'Fecha':10} {'Concepto':40} {'Categoría':25} {'Importe':>10} {'Subcategoría':15}")
        print("-" * 100)

        total_gastos = 0

        for _, trans in gastos_mes.iterrows():
            # Para Bizums mostrar concepto, para otros mostrar operación
            if pd.notna(trans.get('concepto')) and trans['concepto'] != '':
                descripcion = trans['concepto'][:38] + '..' if len(trans['concepto']) > 40 else trans['concepto']
            else:
                descripcion = trans['operacion'][:38] + '..' if len(trans['operacion']) > 40 else trans['operacion']

            categoria = trans['categoria'][:23] + '..' if len(trans['categoria']) > 25 else trans['categoria']

            # Importe siempre negativo para gastos (pero mostramos valor absoluto en total)
            importe_str = f"-{trans['importe']:>7.2f}€"

            subcat = str(trans['subcategoria'])[:13] + '..' if len(str(trans['subcategoria'])) > 15 else str(trans['subcategoria'])

            print(f"{trans['fecha_operacion']:10} {descripcion:40} {categoria:25} {importe_str:>10} {subcat:15}")
            total_gastos += trans['importe']  # CAMBIO: Ya no necesitamos abs() porque 'importe' es positivo

        print("-" * 100)
        print(f"{'TOTAL GASTOS:':76} {total_gastos:>8.2f}€")

    def opcion_estadisticas(self):
        """Muestra estadísticas generales - COMPLETAMENTE MEJORADO"""
        while True:
            print("\n📈 ESTADÍSTICAS GENERALES")
            print("0. ↩️  Volver al menú anterior")
            print("1. 📊 Estadísticas por mes (agrupado por Categoría)")  # Texto aclarado
            print("2. 📈 Análisis financiero detallado")
            print("3. 📑 Desglose mensual por Subcategoría")
            print("4. 🔄 Comparativa de gastos por categoría")
            print("5. 🐜 Análisis de 'Gastos Hormiga'")
            print("6. 📜 Informe de suscripciones y gastos fijos")
            try:
                opcion = int(input("\n👉 Selecciona una opción: "))

                if opcion == 0:
                    break
                elif opcion == 1:
                    self.estadisticas_por_mes()
                elif opcion == 2:
                    self.analisis_financiero_detallado()
                elif opcion == 3:
                    self.desglose_gastos_mensual_por_subcategoria()
                elif opcion == 4:
                    self.comparativa_gastos_categoria()
                elif opcion == 5:
                    self.analisis_gastos_hormiga()
                elif opcion == 6:
                    self.informe_gastos_fijos()
                else:
                    print("❌ Opción no válida")
                if opcion != 0:
                    input("\n⏎ Presiona Enter para continuar...")

            except ValueError:
                print("❌ Por favor, introduce un número válido")
                input("\n⏎ Presiona Enter para continuar...")

    def estadisticas_por_mes(self):
        """Estadísticas detalladas por mes"""
        while True:
            meses = self.mostrar_submenu_meses("📊 ESTADÍSTICAS POR MES")

            try:
                opcion = int(input("\n👉 Selecciona una opción: "))

                if opcion == 0:
                    break
                elif opcion == 1:
                    # Mostrar todos los meses
                    for año, mes in meses:
                        self.mostrar_estadisticas_mes_detalladas(año, mes)
                        input("\n⏎ Presiona Enter para continuar...")
                elif 2 <= opcion <= len(meses) + 1:
                    # Mostrar mes específico
                    año, mes = meses[opcion - 2]
                    self.mostrar_estadisticas_mes_detalladas(año, mes)
                    input("\n⏎ Presiona Enter para continuar...")
                else:
                    print("❌ Opción no válida")

            except ValueError:
                print("❌ Por favor, introduce un número válido")

    def mostrar_estadisticas_mes_detalladas(self, año, mes):
        """Muestra estadísticas detalladas de un mes - ACTUALIZADO"""
        # CORREGIDO: Usar columnas en minúsculas
        mes_df = self.df[
            (self.df['año'] == año) &
            (self.df['mes'] == mes)
            ]

        print(f"\n📈 ESTADÍSTICAS DETALLADAS - {self.nombre_mes(mes)} {año}")
        print("=" * 70)

        # GASTOS POR CATEGORÍA - CORREGIDO: Usar 'tipo' en lugar del signo de importe
        gastos_mes = mes_df[mes_df['tipo'] == 'GASTO']
        total_gastos = gastos_mes['importe'].sum()

        print(f"\n💸 GASTOS POR CATEGORÍA (Total: {total_gastos:.2f}€)")
        print("-" * 50)

        gastos_por_categoria = gastos_mes.groupby('categoria')['importe'].sum().sort_values(ascending=False)

        for categoria, gasto in gastos_por_categoria.items():
            porcentaje = (gasto / total_gastos) * 100 if total_gastos > 0 else 0
            print(f"  {categoria:20} {gasto:>8.2f}€ ({porcentaje:5.1f}%)")

        # INGRESOS POR CATEGORÍA - CORREGIDO: Usar 'tipo'
        ingresos_mes = mes_df[mes_df['tipo'] == 'INGRESO']
        total_ingresos = ingresos_mes['importe'].sum()

        print(f"\n💵 INGRESOS POR CATEGORÍA (Total: {total_ingresos:.2f}€)")
        print("-" * 50)

        ingresos_por_categoria = ingresos_mes.groupby('categoria')['importe'].sum().sort_values(ascending=False)

        for categoria, ingreso in ingresos_por_categoria.items():
            porcentaje = (ingreso / total_ingresos) * 100 if total_ingresos > 0 else 0
            print(f"  {categoria:20} {ingreso:>8.2f}€ ({porcentaje:5.1f}%)")

        # GASTOS POR EMPRESA - CORREGIDO: Usar columnas actualizadas
        print(f"\n🏢 TOP 10 EMPRESAS EN GASTOS")
        print("-" * 50)

        gastos_por_empresa = gastos_mes[
            gastos_mes['nombre_empresa'] != ''
            ].groupby('nombre_empresa')['importe'].sum().sort_values(ascending=False).head(10)

        for empresa, gasto in gastos_por_empresa.items():
            porcentaje = (gasto / total_gastos) * 100 if total_gastos > 0 else 0
            print(f"  {empresa[:30]:30} {gasto:>8.2f}€ ({porcentaje:5.1f}%)")

        # ANÁLISIS FINANCIERO
        print(f"\n📊 ANÁLISIS FINANCIERO DEL MES")
        print("-" * 50)

        balance = total_ingresos - total_gastos
        ahorro_porcentaje = (balance / total_ingresos) * 100 if total_ingresos > 0 else 0

        print(f"  Balance mensual:       {balance:>8.2f}€")
        print(f"  Tasa de ahorro:        {ahorro_porcentaje:>7.1f}%")

        if balance > 0:
            print(f"  ✅ Mes POSITIVO - Has ahorrado {balance:.2f}€")
        else:
            print(f"  ⚠️  Mes NEGATIVO - Has gastado {abs(balance):.2f}€ más de lo ingresado")

        # Comparación con meses anteriores (si existen) - CORREGIDO
        meses_anteriores = self.df[
            (self.df['año'] <= año) &
            ((self.df['año'] < año) | (self.df['mes'] < mes))
            ]

        if not meses_anteriores.empty:
            # CORREGIDO: Usar 'tipo' en lugar del signo de importe
            gasto_promedio = meses_anteriores[meses_anteriores['tipo'] == 'GASTO']['importe'].sum() / len(
                meses_anteriores['mes'].unique())

            if total_gastos > gasto_promedio * 1.2:
                print(f"  📈 Gastos ALTOS este mes (+{(total_gastos / gasto_promedio - 1) * 100:.1f}% vs promedio)")
            elif total_gastos < gasto_promedio * 0.8:
                print(f"  📉 Gastos BAJOS este mes ({(total_gastos / gasto_promedio - 1) * 100:.1f}% vs promedio)")

    def analisis_financiero_detallado(self):
        """Análisis financiero detallado general"""
        print("\n📈 ANÁLISIS FINANCIERO DETALLADO")
        print("=" * 60)

        # CORRECCIÓN: Usar la columna 'tipo' para filtrar
        total_ingresos = self.df[self.df['tipo'] == 'INGRESO']['importe'].sum()
        total_gastos = self.df[self.df['tipo'] == 'GASTO']['importe'].sum()
        balance_total = total_ingresos - total_gastos

        print("💰 BALANCE GENERAL:")
        print(f"  Total ingresos:  {total_ingresos:>10.2f}€")
        print(f"  Total gastos:    {total_gastos:>10.2f}€")
        print(f"  Balance total:   {balance_total:>10.2f}€")

        print("\n📅 EVOLUCIÓN MENSUAL (Últimos 6 meses):")

        # Agregación más robusta
        ingresos_mensuales = self.df[self.df['tipo'] == 'INGRESO'].groupby(['año', 'mes'])['importe'].sum()
        gastos_mensuales = self.df[self.df['tipo'] == 'GASTO'].groupby(['año', 'mes'])['importe'].sum()
        evolucion = pd.DataFrame({'Ingresos': ingresos_mensuales, 'Gastos': gastos_mensuales}).fillna(0)
        evolucion['Balance'] = evolucion['Ingresos'] - evolucion['Gastos']

        for (año, mes), datos in evolucion.tail(6).iterrows():
            print(
                f"  {self.nombre_mes(mes)} {año}: Balance {datos['Balance']:>8.2f}€ (I: {datos['Ingresos']:.0f}€, G: {datos['Gastos']:.0f}€)")

        print("\n🏷️  TOP 5 CATEGORÍAS DE GASTO:")
        gastos_por_categoria = self.df[self.df['tipo'] == 'GASTO'].groupby('categoria')['importe'].sum().sort_values(
            ascending=False)

        for categoria, gasto in gastos_por_categoria.head(5).items():
            porcentaje = (gasto / total_gastos) * 100 if total_gastos > 0 else 0
            print(f"  {categoria:20} {gasto:>8.2f}€ ({porcentaje:5.1f}%)")

    def comparativa_gastos_categoria(self):
        """
        NUEVA FUNCIÓN: Muestra una comparativa de gastos para una categoría seleccionada a lo largo del tiempo.
        """
        print("\n📈 COMPARATIVA DE GASTOS POR CATEGORÍA")

        # Obtener y mostrar la lista de categorías de gasto disponibles
        gastos_df = self.df[self.df['tipo'] == 'GASTO']
        if gastos_df.empty:
            print("❌ No hay datos de gastos para analizar.")
            return

        categorias_gastos = sorted(gastos_df['categoria'].unique())

        print("0. ↩️  Volver al menú anterior")
        for i, cat in enumerate(categorias_gastos, 1):
            print(f"{i}. {cat}")

        try:
            opcion = int(input("\n👉 Selecciona una categoría para comparar: "))

            if opcion == 0:
                return
            elif 1 <= opcion <= len(categorias_gastos):
                cat_seleccionada = categorias_gastos[opcion - 1]

                # Filtrar los datos para la categoría seleccionada y agrupar por mes
                filtro_df = self.df[
                    (self.df['tipo'] == 'GASTO') &
                    (self.df['categoria'] == cat_seleccionada)
                    ]
                gastos_mensuales = filtro_df.groupby(['año', 'mes'])['importe'].sum().sort_index()

                print(f"\n📈 COMPARATIVA - {cat_seleccionada.upper()}")
                print("-" * 45)

                gasto_anterior = None
                for (año, mes), gasto_actual in gastos_mensuales.items():
                    linea = f"- {self.nombre_mes(mes)} {año}: {gasto_actual:>8.2f}€"

                    # Calcular y añadir el cambio porcentual si no es el primer mes
                    if gasto_anterior is not None and gasto_anterior > 0:
                        cambio = ((gasto_actual - gasto_anterior) / gasto_anterior) * 100
                        linea += f" ({cambio:+.1f}%)"  # El '+' muestra el signo siempre

                    print(linea)
                    gasto_anterior = gasto_actual

                print("-" * 45)
            else:
                print("❌ Opción no válida.")

        except (ValueError, IndexError):
            print("❌ Opción no válida.")

    def analisis_gastos_hormiga(self):
        """
        FUNCIÓN ACTUALIZADA: Analiza gastos hormiga filtrando por un umbral de importe
        y permite desglosar las transacciones.
        """
        print("\n🐜 ANÁLISIS DE 'GASTOS HORMIGA'")

        subcategorias_hormiga = self.analisis_config.get('subcategorias_gastos_hormiga', [])
        # --- INICIO DEL CAMBIO ---
        # 1. Leer el umbral desde la configuración, con un valor por defecto de 20
        umbral = self.analisis_config.get('umbral_gasto_hormiga', 20)
        # --- FIN DEL CAMBIO ---

        if not subcategorias_hormiga:
            print("❌ No hay subcategorías definidas para 'gastos hormiga' en config_analisis.json")
            return

        print(f"Buscando gastos en: {', '.join(subcategorias_hormiga)} (menores a {umbral}€)")
        print("-" * 50)

        # --- INICIO DEL CAMBIO ---
        # 2. Añadir el filtro de importe al crear el DataFrame
        filtro_df = self.df[
            (self.df['subcategoria'].isin(subcategorias_hormiga)) &
            (self.df['importe'] <= umbral)
            ]
        # --- FIN DEL CAMBIO ---

        if filtro_df.empty:
            print(f"✅ ¡Felicidades! No se encontraron 'gastos hormiga' (menores a {umbral}€) en el periodo analizado.")
            return

        # El resto de la función sigue igual...
        gastos_agrupados = filtro_df.groupby(['año', 'mes', 'subcategoria'])['importe'].agg(
            ['sum', 'count']).sort_index()

        for (año, mes), grupo in gastos_agrupados.groupby(level=[0, 1]):
            print(f"\n--- {self.nombre_mes(mes)} {año} ---")
            total_mes = 0
            subcategorias_del_mes = []

            for (subcat), datos in grupo.droplevel([0, 1]).iterrows():
                subcategorias_del_mes.append(subcat)
                print(f"  - {subcat:15} {datos['sum']:>7.2f}€ ({int(datos['count'])} trans.)")
                total_mes += datos['sum']
            print(f"  {'TOTAL MES:':17} {total_mes:>7.2f}€")

            while True:
                print("\n  ¿Desglosar alguna subcategoría?")
                print("  0. ↩️  Continuar al siguiente mes")
                for i, subcat_menu in enumerate(subcategorias_del_mes, 1):
                    print(f"  {i}. {subcat_menu}")

                try:
                    opcion = int(input("\n  👉 Selecciona una opción: "))
                    if opcion == 0:
                        break
                    elif 1 <= opcion <= len(subcategorias_del_mes):
                        subcat_seleccionada = subcategorias_del_mes[opcion - 1]

                        transacciones_desglose = filtro_df[
                            (filtro_df['año'] == año) &
                            (filtro_df['mes'] == mes) &
                            (filtro_df['subcategoria'] == subcat_seleccionada)
                            ].sort_values('fecha_operacion')

                        print(f"\n--- Desglose de {subcat_seleccionada} en {self.nombre_mes(mes)} {año} ---")
                        total_desglose = 0
                        for _, trans in transacciones_desglose.iterrows():
                            fecha_str = trans['fecha_operacion'].strftime('%d/%m')
                            empresa = str(trans['nombre_empresa'])[:20] + '..' if len(
                                str(trans['nombre_empresa'])) > 22 else str(trans['nombre_empresa'])
                            print(f"    - {fecha_str} | {empresa:<22} | -{trans['importe']:>6.2f}€")
                            total_desglose += trans['importe']

                        print("    " + "-" * 38)
                        print(f"    {'TOTAL:':>32} -{total_desglose:>6.2f}€")

                        input("\n    ⏎ Presiona Enter para continuar...")
                    else:
                        print("    ❌ Opción no válida.")
                except ValueError:
                    print("    ❌ Por favor, introduce un número.")

        print("-" * 50)

    def informe_gastos_fijos(self):
        """
        NUEVA FUNCIÓN: Muestra un informe de los gastos fijos definidos en la configuración
        y su estado en el último mes (pagado o pendiente).
        """
        print("\n📜 INFORME DE SUSCRIPCIONES Y GASTOS FIJOS")
        print("-" * 70)

        # Cargar la lista de gastos fijos desde la configuración
        gastos_fijos_config = self.analisis_config.get('gastos_fijos_mensuales', [])

        if not gastos_fijos_config:
            print("❌ No hay gastos fijos definidos en config_analisis.json")
            return

        # Filtrar datos para el último mes
        df_mes = self.df[(self.df['año'] == self.ultimo_año) & (self.df['mes'] == self.ultimo_mes)]

        total_fijos_pagados = 0
        print(f"Estado para {self.nombre_mes(self.ultimo_mes)} {self.ultimo_año}:")

        for fijo in gastos_fijos_config:
            palabra_clave = fijo['palabra_clave']

            # Buscar la transacción que coincida con la palabra clave
            mask = (df_mes['nombre_empresa'].str.contains(palabra_clave, case=False, na=False)) | \
                   (df_mes['concepto'].str.contains(palabra_clave, case=False, na=False))

            transaccion_encontrada = df_mes[mask]

            if not transaccion_encontrada.empty:
                # Si se encuentra, se marca como pagado y se toma el importe real
                importe = transaccion_encontrada['importe'].iloc[0]
                estado = "✅ Pagado"
                total_fijos_pagados += importe
            else:
                # Si no se encuentra, se marca como pendiente y se usa el importe de la config si existe
                importe = fijo.get('importe_exacto', 0.0)
                estado = "⏳ Pendiente" if importe > 0 else "ℹ️  No detectado este mes"

            print(f"- {fijo['nombre']:25} | Importe: {importe:>6.2f}€ | Estado: {estado}")

        print("-" * 70)
        print(f"Total de gastos fijos pagados en el mes: {total_fijos_pagados:.2f}€")

    def mostrar_desglose_mes(self, año, mes):
        """
        NUEVA FUNCIÓN AUXILIAR: Muestra el desglose de gastos para un mes específico.
        """
        print(f"\n--- Desglose de {self.nombre_mes(mes)} {año} ---")

        # 1. Filtrar los datos para el mes y tipo de gasto seleccionados
        mes_df = self.df[(self.df['año'] == año) & (self.df['mes'] == mes) & (self.df['tipo'] == 'GASTO')]

        if mes_df.empty:
            print("  No hay gastos registrados en este mes.")
            return

        # 2. Agrupar por subcategoría, calculando la suma y el número de transacciones
        #    Rellenamos las subcategorías vacías para que no se pierdan en el análisis
        desglose = mes_df.fillna({'subcategoria': 'Sin Subcategoría'}) \
            .groupby('subcategoria')['importe'] \
            .agg(['sum', 'count']) \
            .sort_values('sum', ascending=False)

        # 3. Mostrar los resultados con el formato deseado
        for subcat, datos in desglose.iterrows():
            print(f"  - {subcat:<20} {datos['sum']:>8.2f}€ ({int(datos['count'])} trans.)")

        # 4. Mostrar el total del mes
        total_mes = mes_df['importe'].sum()
        print("-" * 45)
        print(f"  {'TOTAL MES:':<22} {total_mes:>8.2f}€")

    def desglose_gastos_mensual_por_subcategoria(self):
        """
        NUEVA FUNCIÓN PRINCIPAL: Permite al usuario seleccionar un mes para ver el desglose.
        """
        while True:
            meses = self.mostrar_submenu_meses("📑 DESGLOSE DE GASTOS POR SUBCATEGORÍA")

            if not meses:
                print("❌ No hay meses con datos disponibles.")
                break

            try:
                opcion = int(input("\n👉 Selecciona un mes para ver el desglose (o todos): "))

                if opcion == 0:
                    break
                elif opcion == 1:  # Opción para ver todos los meses
                    for año, mes in meses:
                        self.mostrar_desglose_mes(año, mes)
                        if (año, mes) != meses[-1]:  # Evitar la pausa en el último mes
                            input("\n⏎ Presiona Enter para ver el siguiente mes...")
                    break
                elif 2 <= opcion <= len(meses) + 1:  # Opción para un mes específico
                    año, mes = meses[opcion - 2]
                    self.mostrar_desglose_mes(año, mes)
                    break
                else:
                    print("❌ Opción no válida")

            except ValueError:
                print("❌ Por favor, introduce un número válido")

    def estimar_ingresos_mensuales(self):
        """Estima los ingresos mensuales basado en historial - ACTUALIZADO"""
        # CORREGIDO: Usar columnas actualizadas
        ingresos_regulares = self.df[
            (self.df['tipo'] == 'INGRESO') &
            (self.df['concepto'].str.contains('NOMINA|NÓMINA|SALARIO', case=False, na=False))
            ]

        if not ingresos_regulares.empty:
            return ingresos_regulares['importe'].mean()
        else:
            # Si no encuentra nóminas, usar promedio de ingresos - CORREGIDO
            return self.df[self.df['tipo'] == 'INGRESO']['importe'].mean()

    # =========================================================================
    # MÉTODOS DE CONFIGURACIÓN (los mismos que antes)
    # =========================================================================

    def menu_configuracion(self):
        """Menú completo de gestión de configuración"""
        while True:
            print(f"\n{'⚙️  GESTIÓN DE CONFIGURACIÓN ':═^60}")
            print("1. 📊 Ver configuración actual")
            print("2. ✏️  Editar metas financieras")
            print("3. 🔔 Configurar alertas")
            print("4. 👤 Preferencias de usuario")
            print("5. 💾 Guardar configuración")
            print("6. 📦 Crear respaldo")
            print("7. 🔄 Resetear configuración")
            print("0. ↩️  Volver al menú principal")

            try:
                opcion = input("\n👉 Selecciona una opción: ").strip()

                if opcion == '0':
                    break
                elif opcion == '1':
                    self.mostrar_configuracion_completa()
                elif opcion == '2':
                    self.editar_metas()
                elif opcion == '3':
                    self.configurar_alertas()
                elif opcion == '4':
                    self.configurar_preferencias()
                elif opcion == '5':
                    self.guardar_toda_configuracion()
                elif opcion == '6':
                    self.crear_respaldo_configuracion()
                elif opcion == '7':
                    self.resetear_configuracion_menu()
                else:
                    print("❌ Opción no válida")

            except (ValueError, KeyboardInterrupt):
                print("\n⏎ Volviendo al menú principal...")
                break

    def mostrar_configuracion_completa(self):
        """Muestra toda la configuración actual"""
        print(f"\n{' CONFIGURACIÓN ACTUAL ':═^60}")

        self.config_manager.mostrar_configuracion(self.configs['metas'], "METAS FINANCIERAS")
        self.config_manager.mostrar_configuracion(self.configs['alertas'], "CONFIGURACIÓN DE ALERTAS")
        self.config_manager.mostrar_configuracion(self.configs['usuario'], "PREFERENCIAS DE USUARIO")

        input("\n⏎ Presiona Enter para continuar...")

    def editar_metas(self):
        """Editor interactivo de metas financieras"""
        print(f"\n✏️  EDITAR METAS FINANCIERAS")
        print("=" * 50)

        metas_actuales = self.configs['metas']['metas_mensuales']

        print("Metas actuales:")
        for meta, valor in metas_actuales.items():
            print(f"  {meta}: {valor}€")

        print(f"\n¿Qué meta quieres modificar?")
        metas_lista = list(metas_actuales.keys())
        for i, meta in enumerate(metas_lista, 1):
            print(f"{i}. {meta}")
        print("0. ↩️  Cancelar")

        try:
            opcion = int(input("\n👉 Selecciona una meta: "))

            if opcion == 0:
                return
            elif 1 <= opcion <= len(metas_lista):
                meta_seleccionada = metas_lista[opcion - 1]
                nuevo_valor = float(input(f"Nuevo valor para {meta_seleccionada} (€): "))

                # Actualizar en memoria
                self.configs['metas']['metas_mensuales'][meta_seleccionada] = nuevo_valor
                self.metas[meta_seleccionada] = nuevo_valor  # Actualizar también en el objeto principal

                print(f"✅ Meta actualizada: {meta_seleccionada} = {nuevo_valor}€")

                # Preguntar si guardar
                if input("¿Guardar cambios? (s/n): ").lower() == 's':
                    self.guardar_toda_configuracion()
            else:
                print("❌ Opción no válida")

        except ValueError:
            print("❌ Valor no válido")

    def configurar_alertas(self):
        """Configuración del sistema de alertas"""
        print(f"\n🔔 CONFIGURAR SISTEMA DE ALERTAS")
        print("=" * 50)

        alertas_actuales = self.configs['alertas']

        print("Configuración actual:")
        print(f"  Alertas activadas: {alertas_actuales['alertas_activadas']}")
        print(f"  Frecuencia: {alertas_actuales['umbrales_alertas']['frecuencia_alerta']}")

        print(f"\nOpciones:")
        print("1. Activar/Desactivar alertas")
        print("2. Cambiar frecuencia")
        print("0. ↩️  Volver")

        try:
            opcion = int(input("\n👉 Selecciona una opción: "))

            if opcion == 0:
                return
            elif opcion == 1:
                nuevo_estado = not alertas_actuales['alertas_activadas']
                self.configs['alertas']['alertas_activadas'] = nuevo_estado
                estado = "activadas" if nuevo_estado else "desactivadas"
                print(f"✅ Alertas {estado}")

            elif opcion == 2:
                print("Frecuencias disponibles: diaria, semanal, mensual")
                nueva_frecuencia = input("Nueva frecuencia: ").strip().lower()
                if nueva_frecuencia in ['diaria', 'semanal', 'mensual']:
                    self.configs['alertas']['umbrales_alertas']['frecuencia_alerta'] = nueva_frecuencia
                    print(f"✅ Frecuencia actualizada: {nueva_frecuencia}")
                else:
                    print("❌ Frecuencia no válida")
            else:
                print("❌ Opción no válida")

            # Guardar cambios
            if input("¿Guardar cambios? (s/n): ").lower() == 's':
                self.guardar_toda_configuracion()

        except ValueError:
            print("❌ Valor no válido")

    def configurar_preferencias(self):
        """Configuración de preferencias de usuario"""
        print(f"\n👤 CONFIGURAR PREFERENCIAS DE USUARIO")
        print("=" * 50)

        preferencias = self.configs['usuario']['preferencias']

        print("Preferencias actuales:")
        for pref, valor in preferencias.items():
            print(f"  {pref}: {valor}")

        print(f"\n¿Qué preferencia quieres modificar?")
        prefs_lista = list(preferencias.keys())
        for i, pref in enumerate(prefs_lista, 1):
            print(f"{i}. {pref}")
        print("0. ↩️  Cancelar")

        try:
            opcion = int(input("\n👉 Selecciona una preferencia: "))

            if opcion == 0:
                return
            elif 1 <= opcion <= len(prefs_lista):
                pref_seleccionada = prefs_lista[opcion - 1]
                valor_actual = preferencias[pref_seleccionada]

                if isinstance(valor_actual, bool):
                    nuevo_valor = input(
                        f"{pref_seleccionada} (actual: {valor_actual}) - ¿Activar? (s/n): ").lower() == 's'
                else:
                    nuevo_valor = input(f"Nuevo valor para {pref_seleccionada} (actual: {valor_actual}): ").strip()
                    # Convertir a número si es posible
                    try:
                        nuevo_valor = float(nuevo_valor) if '.' in nuevo_valor else int(nuevo_valor)
                    except ValueError:
                        pass  # Mantener como string

                self.configs['usuario']['preferencias'][pref_seleccionada] = nuevo_valor
                self.preferencias[pref_seleccionada] = nuevo_valor
                print(f"✅ Preferencia actualizada: {pref_seleccionada} = {nuevo_valor}")

                # Guardar cambios
                if input("¿Guardar cambios? (s/n): ").lower() == 's':
                    self.guardar_toda_configuracion()
            else:
                print("❌ Opción no válida")

        except ValueError:
            print("❌ Valor no válido")

    def guardar_toda_configuracion(self):
        """Guarda toda la configuración actual"""
        resultado = self.config_manager.guardar_todas_configuraciones(self.configs)

        if all(resultado.values()):
            print("✅ Todas las configuraciones guardadas correctamente")
        else:
            print("⚠️  Algunas configuraciones no se pudieron guardar:")
            for tipo, exitoso in resultado.items():
                if not exitoso:
                    print(f"   ❌ {tipo}")

    def crear_respaldo_configuracion(self):
        """Crea un respaldo de la configuración"""
        print(f"\n📦 CREANDO RESPALDO DE CONFIGURACIÓN...")
        ruta_respaldo = self.config_manager.crear_respaldo()
        print(f"✅ Respaldo creado en: {ruta_respaldo}")

    def resetear_configuracion_menu(self):
        """Menú para resetear configuraciones"""
        print(f"\n🔄 RESETEAR CONFIGURACIÓN")
        print("=" * 50)
        print("¿Qué configuración quieres resetear?")
        print("1. Metas financieras")
        print("2. Configuración de alertas")
        print("3. Preferencias de usuario")
        print("4. TODO (reset completo)")
        print("0. ↩️  Cancelar")

        try:
            opcion = int(input("\n👉 Selecciona una opción: "))

            if opcion == 0:
                return
            elif opcion == 1:
                self.config_manager.resetear_configuracion('metas')
                self.configs['metas'] = self.config_manager.metas_default
                self.metas = self.configs['metas']['metas_mensuales']
            elif opcion == 2:
                self.config_manager.resetear_configuracion('alertas')
                self.configs['alertas'] = self.config_manager.alertas_default
                self.alertas_config = self.configs['alertas']
            elif opcion == 3:
                self.config_manager.resetear_configuracion('usuario')
                self.configs['usuario'] = self.config_manager.usuario_default
                self.preferencias = self.configs['usuario']['preferencias']
            elif opcion == 4:
                self.config_manager.resetear_configuracion('todo')
                self.configs = self.config_manager.cargar_todas_configuraciones()
                # Recargar configuraciones específicas
                self.metas = self.configs['metas']['metas_mensuales']
                self.alertas_config = self.configs['alertas']
                self.preferencias = self.configs['usuario']['preferencias']
            else:
                print("❌ Opción no válida")

        except ValueError:
            print("❌ Valor no válido")

    def ejecutar(self):
        """Ejecuta la aplicación principal"""
        if self.df is None:
            return

        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            self.mostrar_cabecera()
            self.mostrar_menu_principal()

            try:
                opcion = input("\n👉 Selecciona una opción: ").strip()
                if not opcion: continue
                opcion = int(opcion)

                if opcion == 1: self.opcion_transacciones()
                elif opcion == 2: self.opcion_buscar_categoria()
                elif opcion == 3: self.opcion_buscar_empresa()
                elif opcion == 4: self.opcion_estadisticas()
                elif opcion == 5: self.menu_configuracion()
                elif opcion == 6:
                    print("\n👋 ¡Hasta pronto!")
                    break
                else:
                    print("❌ Opción no válida")
                    input("⏎ Presiona Enter para continuar...")

            except ValueError:
                print("❌ Por favor, introduce un número válido")
                input("⏎ Presiona Enter para continuar...")
            except KeyboardInterrupt:
                print("\n\n👋 ¡Hasta pronto!")
                break


# Ejecutar la aplicación
if __name__ == "__main__":
    app = AnalizadorGastos()
    app.ejecutar()