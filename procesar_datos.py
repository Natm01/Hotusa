#!/usr/bin/env python3
"""
Script para procesar y normalizar archivos de datos contables de Hotusa.
Convierte archivos de formato "informe" a formato tabular CSV.
"""

import json
import csv
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any
from datetime import datetime
import pandas as pd
import tempfile
import os


class ProcesadorDatos:
    """Clase para procesar archivos de libro diario y sumas y saldos."""

    def __init__(self, ruta_estructura_json: str, ruta_datos_originales: str, ruta_datos_tratados: str):
        """
        Inicializa el procesador.

        Args:
            ruta_estructura_json: Ruta al archivo JSON con la estructura
            ruta_datos_originales: Ruta a la carpeta con datos originales
            ruta_datos_tratados: Ruta donde se guardarán los datos procesados
        """
        self.ruta_estructura_json = Path(ruta_estructura_json)
        self.ruta_datos_originales = Path(ruta_datos_originales)
        self.ruta_datos_tratados = Path(ruta_datos_tratados)

        # Cargar estructura
        with open(self.ruta_estructura_json, 'r', encoding='utf-8') as f:
            self.estructura = json.load(f)

    def normalizar_nombre_sociedad(self, nombre_sociedad: str) -> str:
        """Normaliza el nombre de la sociedad para uso en rutas."""
        # Reemplazar espacios por guiones bajos y quitar caracteres especiales
        nombre = nombre_sociedad.strip()
        nombre = re.sub(r'[^\w\s-]', '', nombre)
        nombre = re.sub(r'\s+', '_', nombre)
        return nombre

    def convertir_xlsx_a_texto(self, ruta_archivo: Path) -> List[str]:
        """
        Convierte un archivo .xlsx o .xlsm a formato de texto delimitado por tabs.
        Retorna lista de líneas simulando el formato de los archivos .XLS originales.
        """
        try:
            # Leer el archivo Excel
            df = pd.read_excel(ruta_archivo, sheet_name=0, header=None)

            # Convertir a formato de texto delimitado por tabs
            lineas = []
            for _, row in df.iterrows():
                valores = []
                for val in row:
                    if pd.isna(val):
                        valores.append('')
                    elif isinstance(val, (int, float)):
                        # Convertir números al formato europeo (coma como decimal)
                        # Esto mantiene compatibilidad con la lógica de limpieza existente
                        valores.append(str(val).replace('.', ','))
                    else:
                        valores.append(str(val))

                linea = '\t'.join(valores) + '\n'
                lineas.append(linea)

            return lineas
        except Exception as e:
            print(f"⚠️  Error convirtiendo {ruta_archivo.name} a texto: {e}")
            return []

    def leer_archivo_utf16(self, ruta_archivo: Path) -> List[str]:
        """Lee un archivo UTF-16 LE y retorna lista de líneas. Soporta .xlsx y .xlsm."""
        extension = ruta_archivo.suffix.lower()

        # Si es un archivo Excel moderno (.xlsx, .xlsm), usar pandas
        if extension in ['.xlsx', '.xlsm']:
            return self.convertir_xlsx_a_texto(ruta_archivo)

        # Para archivos .XLS (formato antiguo de Excel exportado a texto)
        try:
            with open(ruta_archivo, 'r', encoding='utf-16-le') as f:
                return f.readlines()
        except UnicodeDecodeError:
            # Intentar con UTF-8
            try:
                with open(ruta_archivo, 'r', encoding='utf-8') as f:
                    return f.readlines()
            except Exception as e:
                print(f"⚠️  Error leyendo {ruta_archivo.name}: {e}")
                return []

    def parsear_linea_tabs(self, texto: str) -> List[str]:
        """
        Parsea una línea con tabs, manteniendo la estructura pero limpiando espacios.
        NO colapsa tabs consecutivos.
        """
        # Split por tab (cada tab es una columna, incluso si está vacío)
        valores = texto.split('\t')
        # Limpiar solo espacios en blanco de cada valor
        return [v.strip() for v in valores]

    def detectar_inicio_datos_sys(self, lineas: List[str]) -> Tuple[int, List[str]]:
        """
        Detecta dónde empiezan los datos en un archivo de sumas y saldos.

        Returns:
            Tupla de (índice de inicio, lista de nombres de columnas)
        """
        for i, linea in enumerate(lineas):
            # Buscar línea que contenga "Soc." y "Cta.mayor"
            if '\tSoc.\t' in linea or linea.strip().startswith('Soc.'):
                # Esta es la línea de encabezados
                columnas = self.parsear_linea_tabs(linea)
                return i + 2, columnas  # Saltar línea vacía

        return 0, []

    def detectar_inicio_datos_ld(self, lineas: List[str]) -> Tuple[int, List[str], List[str]]:
        """
        Detecta dónde empiezan los datos en un archivo de libro diario.

        Returns:
            Tupla de (índice de inicio, columnas cabecera, columnas detalle)
        """
        cols_cabecera = []
        cols_detalle = []

        for i, linea in enumerate(lineas):
            # Buscar línea de encabezados de cabecera (Referencia, Número, etc.)
            if 'Referencia' in linea and 'Número' in linea and 'Registrado' in linea:
                cols_cabecera = self.parsear_linea_tabs(linea)

                # La siguiente línea no vacía debe tener los encabezados de detalle
                if i + 1 < len(lineas):
                    linea_detalle = lineas[i + 1]
                    if 'Cuenta' in linea_detalle and 'Debe' in linea_detalle:
                        cols_detalle = self.parsear_linea_tabs(linea_detalle)
                        return i + 3, cols_cabecera, cols_detalle  # Saltar línea vacía

        return 0, cols_cabecera, cols_detalle

    def procesar_sys(self, ruta_archivo: Path) -> List[Dict[str, Any]]:
        """
        Procesa un archivo de sumas y saldos y retorna lista de registros.
        """
        lineas = self.leer_archivo_utf16(ruta_archivo)
        inicio, columnas = self.detectar_inicio_datos_sys(lineas)

        if inicio == 0:
            print(f"⚠️  No se pudo detectar inicio de datos en {ruta_archivo.name}")
            return []

        registros = []
        for linea in lineas[inicio:]:
            # Solo eliminar salto de línea, NO los tabs
            linea = linea.rstrip('\n\r')
            if not linea.strip() or '=' in linea or 'Página' in linea:
                continue

            valores = self.parsear_linea_tabs(linea)
            # Filtrar solo si la línea tiene contenido significativo
            if not any(valores):
                continue

            # Crear registro solo con columnas que tienen nombre
            registro = {}
            for i in range(len(valores)):
                if i < len(columnas) and columnas[i]:  # Solo si la columna tiene nombre
                    valor = valores[i] if i < len(valores) else ''
                    # Limpiar valores numéricos (quitar separador de miles, cambiar coma a punto)
                    if valor and any(c.isdigit() for c in valor):
                        valor = valor.replace('.', '').replace(',', '.')
                    registro[columnas[i]] = valor

            # Solo agregar si tiene sociedad y cuenta
            if registro.get('Soc.') and registro.get('Cta.mayor'):
                registros.append(registro)

        return registros

    def procesar_ld(self, ruta_archivo: Path) -> List[Dict[str, Any]]:
        """
        Procesa un archivo de libro diario y retorna lista de registros.
        Convierte formato jerárquico a formato tabular plano.
        """
        lineas = self.leer_archivo_utf16(ruta_archivo)
        inicio, cols_cabecera, cols_detalle = self.detectar_inicio_datos_ld(lineas)

        if inicio == 0:
            print(f"⚠️  No se pudo detectar inicio de datos en {ruta_archivo.name}")
            return []

        registros = []
        asiento_actual = {}
        es_cabecera = True  # La primera línea de datos es siempre cabecera

        for linea in lineas[inicio:]:
            # Solo eliminar saltos de línea
            linea = linea.rstrip('\n\r')

            # Saltar separadores de página
            if '=' in linea or 'Página' in linea:
                continue

            # Línea vacía = siguiente línea es cabecera de nuevo asiento
            if not linea.strip():
                es_cabecera = True
                continue

            if es_cabecera:
                # Es una cabecera de asiento
                valores = self.parsear_linea_tabs(linea)

                # Crear diccionario de asiento
                asiento_actual = {}
                for i in range(len(valores)):
                    if i < len(cols_cabecera) and cols_cabecera[i]:
                        valor = valores[i]
                        asiento_actual[f'cab_{cols_cabecera[i]}'] = valor

                es_cabecera = False  # Las siguientes son detalles
            else:
                # Es una línea de detalle
                valores = self.parsear_linea_tabs(linea)

                # Crear registro combinando cabecera y detalle
                registro = asiento_actual.copy()

                for i in range(len(valores)):
                    if i < len(cols_detalle) and cols_detalle[i]:
                        valor = valores[i]
                        # Limpiar valores numéricos
                        if valor and any(c.isdigit() for c in valor):
                            valor = valor.replace('.', '').replace(',', '.')
                        registro[f'det_{cols_detalle[i]}'] = valor

                if registro.get('det_Cuenta'):  # Solo agregar si tiene cuenta
                    registros.append(registro)

        return registros

    def consolidar_archivos(self, archivos: List[Path], tipo: str) -> List[Dict[str, Any]]:
        """
        Consolida múltiples archivos (ej: trimestres) en uno solo.

        Args:
            archivos: Lista de rutas a archivos
            tipo: 'LD' o 'SYS'
        """
        todos_registros = []

        for archivo in sorted(archivos):
            if not archivo.exists():
                print(f"⚠️  Archivo no encontrado: {archivo}")
                continue

            print(f"   📄 Procesando: {archivo.name}")

            if tipo == 'SYS':
                registros = self.procesar_sys(archivo)
            else:  # LD
                registros = self.procesar_ld(archivo)

            todos_registros.extend(registros)

        return todos_registros

    def guardar_csv(self, registros: List[Dict[str, Any]], ruta_salida: Path):
        """Guarda registros en un archivo CSV."""
        if not registros:
            print(f"⚠️  No hay registros para guardar en {ruta_salida}")
            return

        # Crear directorio si no existe
        ruta_salida.parent.mkdir(parents=True, exist_ok=True)

        # Obtener todas las columnas
        columnas = set()
        for registro in registros:
            columnas.update(registro.keys())

        columnas = sorted(columnas)

        # Guardar CSV
        with open(ruta_salida, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columnas)
            writer.writeheader()
            writer.writerows(registros)

        print(f"✅ CSV guardado: {ruta_salida} ({len(registros)} registros)")

    def procesar_sociedad(self, sociedad_info: Dict[str, Any]) -> Dict[str, int]:
        """
        Procesa todos los archivos de una sociedad.

        Returns:
            Diccionario con estadísticas de procesamiento
        """
        nombre_sociedad = sociedad_info['sociedad']
        nombre_normalizado = self.normalizar_nombre_sociedad(nombre_sociedad)

        print(f"\n{'='*70}")
        print(f"📊 Procesando sociedad: {nombre_sociedad}")
        print(f"{'='*70}")

        stats = {'ld': 0, 'sys': 0, 'errores': 0}

        # Crear carpeta para la sociedad
        carpeta_sociedad_original = self.ruta_datos_originales / nombre_sociedad
        carpeta_sociedad_tratada = self.ruta_datos_tratados / nombre_normalizado

        if not carpeta_sociedad_original.exists():
            print(f"⚠️  Carpeta no encontrada: {carpeta_sociedad_original}")
            return stats

        # Procesar según estructura
        if 'por_anios' in sociedad_info:
            # Tiene estructura por años
            for anio_info in sociedad_info['por_anios']:
                anio = anio_info['anio']
                print(f"\n  📅 Año: {anio}")

                # Procesar libros diarios del año
                if anio_info['libros_diarios']:
                    archivos_ld = [
                        carpeta_sociedad_original / anio / item['archivo']
                        for item in anio_info['libros_diarios']
                    ]
                    registros_ld = self.consolidar_archivos(archivos_ld, 'LD')

                    if registros_ld:
                        ruta_csv = carpeta_sociedad_tratada / anio / f"libro_diario_{anio}.csv"
                        self.guardar_csv(registros_ld, ruta_csv)
                        stats['ld'] += 1

                # Procesar sumas y saldos del año
                if anio_info['sumas_saldos']:
                    archivos_sys = [
                        carpeta_sociedad_original / anio / item['archivo']
                        for item in anio_info['sumas_saldos']
                    ]
                    registros_sys = self.consolidar_archivos(archivos_sys, 'SYS')

                    if registros_sys:
                        ruta_csv = carpeta_sociedad_tratada / anio / f"sumas_saldos_{anio}.csv"
                        self.guardar_csv(registros_sys, ruta_csv)
                        stats['sys'] += 1

        else:
            # No tiene años, archivos directos
            # Procesar libros diarios
            if sociedad_info.get('libros_diarios'):
                archivos_ld = [
                    carpeta_sociedad_original / item['archivo']
                    for item in sociedad_info['libros_diarios']
                ]
                registros_ld = self.consolidar_archivos(archivos_ld, 'LD')

                if registros_ld:
                    # Extraer año del nombre del archivo si es posible
                    anio = self.extraer_anio_de_archivos(sociedad_info['libros_diarios'])
                    ruta_csv = carpeta_sociedad_tratada / f"libro_diario_{anio}.csv"
                    self.guardar_csv(registros_ld, ruta_csv)
                    stats['ld'] += 1

            # Procesar sumas y saldos
            if sociedad_info.get('sumas_saldos'):
                archivos_sys = [
                    carpeta_sociedad_original / item['archivo']
                    for item in sociedad_info['sumas_saldos']
                ]
                registros_sys = self.consolidar_archivos(archivos_sys, 'SYS')

                if registros_sys:
                    anio = self.extraer_anio_de_archivos(sociedad_info['sumas_saldos'])
                    ruta_csv = carpeta_sociedad_tratada / f"sumas_saldos_{anio}.csv"
                    self.guardar_csv(registros_sys, ruta_csv)
                    stats['sys'] += 1

        return stats

    def extraer_anio_de_archivos(self, archivos_info: List[Dict[str, str]]) -> str:
        """Extrae el año de los nombres de archivo."""
        for item in archivos_info:
            nombre = item['archivo']
            # Buscar años en el formato YYYY
            match = re.search(r'20\d{2}', nombre)
            if match:
                return match.group()
        return '2025'  # Por defecto

    def calcular_totales_sociedad(self, nombre_sociedad: str, nombre_normalizado: str) -> Dict[str, float]:
        """
        Calcula los totales de debe y haber para una sociedad a partir de sus archivos CSV de sumas y saldos.

        Returns:
            Diccionario con 'debe' y 'haber' totales
        """
        carpeta_sociedad = self.ruta_datos_tratados / nombre_normalizado

        if not carpeta_sociedad.exists():
            return {'debe': 0.0, 'haber': 0.0}

        total_debe = 0.0
        total_haber = 0.0

        # Buscar todos los archivos de sumas y saldos
        archivos_sys = list(carpeta_sociedad.glob('**/sumas_saldos_*.csv'))

        for archivo_csv in archivos_sys:
            try:
                df = pd.read_csv(archivo_csv)

                # Buscar columnas de saldos acumulados (puede ser negativo o positivo)
                col_saldo_acumulado = None

                # Buscar columnas de debe y haber (movimientos del período)
                col_debe = None
                col_haber = None

                for col in df.columns:
                    col_lower = col.lower()
                    # Priorizar "Saldo acumulado" si existe
                    if 'saldo acumulado' in col_lower or 'saldo final' in col_lower:
                        col_saldo_acumulado = col
                    # Buscar columnas de movimientos del período
                    elif ('período' in col_lower or 'periodo' in col_lower or 'per.inf' in col_lower) and 'debe' in col_lower and col_debe is None:
                        col_debe = col
                    elif ('período' in col_lower or 'periodo' in col_lower or 'per.inf' in col_lower) and 'haber' in col_lower and col_haber is None:
                        col_haber = col

                # Si existe "Saldo acumulado", usarlo para calcular debe y haber
                if col_saldo_acumulado and col_saldo_acumulado in df.columns:
                    saldos = pd.to_numeric(df[col_saldo_acumulado], errors='coerce').fillna(0)
                    # Saldos positivos = debe, saldos negativos = haber (en valor absoluto)
                    total_debe += saldos[saldos > 0].sum()
                    total_haber += abs(saldos[saldos < 0].sum())
                else:
                    # Si no hay saldo acumulado, usar las columnas de movimientos
                    if col_debe and col_debe in df.columns:
                        debe_serie = pd.to_numeric(df[col_debe], errors='coerce').fillna(0)
                        total_debe += debe_serie.sum()

                    if col_haber and col_haber in df.columns:
                        haber_serie = pd.to_numeric(df[col_haber], errors='coerce').fillna(0)
                        total_haber += haber_serie.sum()

            except Exception as e:
                print(f"⚠️  Error calculando totales de {archivo_csv.name}: {e}")

        return {'debe': total_debe, 'haber': total_haber}

    def generar_reporte_excel(self, datos_reporte: List[Dict[str, Any]]):
        """
        Genera un reporte Excel con los importes finales de debe y haber por sociedad.

        Args:
            datos_reporte: Lista de diccionarios con información de cada sociedad
        """
        # Crear DataFrame
        df = pd.DataFrame(datos_reporte)

        # Ordenar por sociedad
        df = df.sort_values('Sociedad')

        # Formatear números
        df['Importe Final Debe'] = df['Importe Final Debe'].apply(lambda x: f"{x:,.2f}")
        df['Importe Final Haber'] = df['Importe Final Haber'].apply(lambda x: f"{x:,.2f}")

        # Guardar en Excel
        ruta_reporte = self.ruta_datos_tratados / 'reporte_importes_finales.xlsx'

        # Usar ExcelWriter para mejor formato
        with pd.ExcelWriter(ruta_reporte, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Importes Finales', index=False)

            # Ajustar ancho de columnas
            worksheet = writer.sheets['Importes Finales']
            worksheet.column_dimensions['A'].width = 35
            worksheet.column_dimensions['B'].width = 25
            worksheet.column_dimensions['C'].width = 25

        print(f"\n✅ Reporte Excel generado: {ruta_reporte}")
        return ruta_reporte

    def procesar_todo(self):
        """Procesa todas las sociedades."""
        print("\n" + "="*70)
        print("🚀 INICIANDO PROCESAMIENTO DE DATOS")
        print("="*70)

        total_stats = {'ld': 0, 'sys': 0, 'errores': 0, 'sociedades': 0}
        datos_reporte = []

        for sociedad_info in self.estructura['sociedades']:
            nombre_sociedad = sociedad_info['sociedad']
            nombre_normalizado = self.normalizar_nombre_sociedad(nombre_sociedad)

            try:
                stats = self.procesar_sociedad(sociedad_info)
                total_stats['ld'] += stats['ld']
                total_stats['sys'] += stats['sys']
                total_stats['errores'] += stats['errores']
                total_stats['sociedades'] += 1

                # Calcular totales de debe y haber para el reporte
                totales = self.calcular_totales_sociedad(nombre_sociedad, nombre_normalizado)
                datos_reporte.append({
                    'Sociedad': nombre_sociedad,
                    'Importe Final Debe': totales['debe'],
                    'Importe Final Haber': totales['haber']
                })

            except Exception as e:
                print(f"❌ Error procesando {sociedad_info['sociedad']}: {e}")
                total_stats['errores'] += 1
                # Agregar al reporte con valores en 0
                datos_reporte.append({
                    'Sociedad': nombre_sociedad,
                    'Importe Final Debe': 0.0,
                    'Importe Final Haber': 0.0
                })

        print("\n" + "="*70)
        print("📈 RESUMEN FINAL")
        print("="*70)
        print(f"Sociedades procesadas: {total_stats['sociedades']}")
        print(f"Libros diarios generados: {total_stats['ld']}")
        print(f"Sumas y saldos generados: {total_stats['sys']}")
        print(f"Errores: {total_stats['errores']}")
        print("="*70)

        # Generar reporte Excel
        print("\n" + "="*70)
        print("📊 GENERANDO REPORTE DE IMPORTES FINALES")
        print("="*70)
        self.generar_reporte_excel(datos_reporte)


def main():
    """Función principal."""
    procesador = ProcesadorDatos(
        ruta_estructura_json='estructura_braide_json.json',
        ruta_datos_originales='datos_braide',
        ruta_datos_tratados='datos_tratados_braide'
    )

    procesador.procesar_todo()


if __name__ == '__main__':
    main()
