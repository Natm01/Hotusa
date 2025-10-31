#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Mapeo de Archivos Contables - Hotusa
===============================================

Este script analiza la estructura de datos_originales e identifica:
- Sociedades
- Libros Diario
- Sumas y Saldos
- Estructura por años (cuando aplica)

Genera un archivo Excel con el mapeo completo para la reorganización
a la carpeta datos_tratados.

Estructura destino propuesta:
    datos_tratados/
        ├── libro_diario/
        │   ├── Sociedad_libro_diario.csv
        │   ├── 2023_Sociedad_Con_Anos_libro_diario.csv
        │   └── ...
        └── sumas_saldos/
            ├── Sociedad_sumas_saldos.csv
            ├── 2023_Sociedad_Con_Anos_sumas_saldos.csv
            └── ...

Autor: Script de mapeo y organización
Fecha: 2025-10-31
"""

import os
from pathlib import Path
from datetime import datetime
import re
import pandas as pd
from typing import List, Dict, Tuple, Optional


def normalizar_nombre(nombre: str) -> str:
    """
    Normaliza un nombre para usar en nombres de archivo.

    Args:
        nombre: Nombre original

    Returns:
        Nombre normalizado (sin espacios, sin caracteres especiales)
    """
    # Reemplazar espacios por guiones bajos
    nombre = nombre.replace(' ', '_')
    # Eliminar caracteres especiales excepto guiones bajos y puntos
    nombre = re.sub(r'[^\w.]', '', nombre)
    return nombre


def es_carpeta_ano(nombre: str) -> Optional[int]:
    """
    Verifica si el nombre de una carpeta corresponde a un año.

    Args:
        nombre: Nombre de la carpeta

    Returns:
        Año como entero si es válido, None si no
    """
    # Verificar si es un número de 4 dígitos entre 2000 y 2099
    if re.match(r'^20\d{2}$', nombre):
        return int(nombre)
    return None


def identificar_tipo_archivo(nombre_archivo: str) -> Tuple[str, int]:
    """
    Identifica si un archivo es Libro Diario o Sumas y Saldos.

    Args:
        nombre_archivo: Nombre del archivo

    Returns:
        Tupla (tipo, prioridad) donde:
        - tipo: 'Libro Diario', 'Sumas y Saldos', o 'Desconocido'
        - prioridad: número que indica confianza (mayor = más confianza)
    """
    nombre_upper = nombre_archivo.upper()

    # Patrones para Libro Diario (orden de prioridad)
    patrones_ld = [
        (r'\bLD\b', 10),                    # LD como palabra completa
        (r'^LD[_\s]', 9),                   # LD al inicio
        (r'LIBRO[\s_]*DIARIO', 8),          # "Libro Diario"
        (r'\bDIARIO\b', 7),                 # "Diario" como palabra
        (r'^DIARIO[\s_]', 6),               # "Diario" al inicio
    ]

    # Patrones para Sumas y Saldos (orden de prioridad)
    patrones_sys = [
        (r'\bSYS\b', 10),                   # SYS como palabra completa
        (r'^SYS[\s_]', 9),                  # SYS al inicio
        (r'SUMAS[\s_]+Y[\s_]+SALDOS', 8),   # "Sumas y Saldos"
        (r'BALANCE.*SUMAS', 7),             # "Balance de sumas y saldos"
        (r'\bBALANCE\b', 6),                # "Balance" como palabra
    ]

    # Buscar coincidencias en Libro Diario
    max_prioridad_ld = 0
    for patron, prioridad in patrones_ld:
        if re.search(patron, nombre_upper):
            max_prioridad_ld = max(max_prioridad_ld, prioridad)

    # Buscar coincidencias en Sumas y Saldos
    max_prioridad_sys = 0
    for patron, prioridad in patrones_sys:
        if re.search(patron, nombre_upper):
            max_prioridad_sys = max(max_prioridad_sys, prioridad)

    # Determinar el tipo según la mayor prioridad
    if max_prioridad_ld > max_prioridad_sys:
        return ('Libro Diario', max_prioridad_ld)
    elif max_prioridad_sys > 0:
        return ('Sumas y Saldos', max_prioridad_sys)
    else:
        return ('Desconocido', 0)


def generar_nombre_destino(sociedad: str, tipo: str, ano: Optional[int] = None,
                          indice: Optional[int] = None) -> str:
    """
    Genera el nombre de archivo destino según las reglas establecidas.

    Args:
        sociedad: Nombre de la sociedad
        tipo: 'Libro Diario' o 'Sumas y Saldos'
        ano: Año (opcional, para sociedades con subcarpetas por año)
        indice: Índice para archivos múltiples (opcional)

    Returns:
        Nombre del archivo destino (sin extensión)
    """
    # Normalizar nombre de sociedad
    sociedad_norm = normalizar_nombre(sociedad)

    # Determinar sufijo según tipo
    if tipo == 'Libro Diario':
        sufijo = 'libro_diario'
    elif tipo == 'Sumas y Saldos':
        sufijo = 'sumas_saldos'
    else:
        sufijo = 'desconocido'

    # Construir nombre
    partes = []

    # Añadir año si existe
    if ano is not None:
        partes.append(str(ano))

    # Añadir sociedad
    partes.append(sociedad_norm)

    # Añadir sufijo de tipo
    partes.append(sufijo)

    # Construir nombre base
    nombre_base = '_'.join(partes)

    # Añadir índice si hay múltiples archivos
    if indice is not None and indice > 1:
        nombre_base += f'_parte{indice}'

    return nombre_base


def analizar_sociedad(ruta_sociedad: Path, nombre_sociedad: str) -> List[Dict]:
    """
    Analiza una carpeta de sociedad y extrae información de sus archivos.

    Args:
        ruta_sociedad: Path de la carpeta de la sociedad
        nombre_sociedad: Nombre de la sociedad

    Returns:
        Lista de diccionarios con información de cada archivo
    """
    registros = []

    # Verificar si tiene subcarpetas de años
    subcarpetas = [d for d in ruta_sociedad.iterdir() if d.is_dir()]
    carpetas_anos = {d.name: es_carpeta_ano(d.name) for d in subcarpetas}
    carpetas_anos = {k: v for k, v in carpetas_anos.items() if v is not None}

    if carpetas_anos:
        # Procesar cada año por separado
        for carpeta_nombre, ano in sorted(carpetas_anos.items(), key=lambda x: x[1]):
            carpeta_path = ruta_sociedad / carpeta_nombre
            archivos = [f for f in carpeta_path.iterdir() if f.is_file()]

            # Agrupar archivos por tipo
            archivos_por_tipo = {'Libro Diario': [], 'Sumas y Saldos': [], 'Desconocido': []}

            for archivo in archivos:
                tipo, prioridad = identificar_tipo_archivo(archivo.name)
                archivos_por_tipo[tipo].append((archivo, prioridad))

            # Procesar cada tipo
            for tipo, lista_archivos in archivos_por_tipo.items():
                if not lista_archivos:
                    continue

                # Ordenar por prioridad (mayor primero)
                lista_archivos.sort(key=lambda x: x[1], reverse=True)

                # Numerar si hay múltiples archivos del mismo tipo
                for idx, (archivo, prioridad) in enumerate(lista_archivos, start=1):
                    indice = idx if len(lista_archivos) > 1 else None
                    nombre_destino = generar_nombre_destino(nombre_sociedad, tipo, ano, indice)

                    # Determinar subcarpeta destino
                    if tipo == 'Libro Diario':
                        subcarpeta_destino = 'libro_diario'
                    elif tipo == 'Sumas y Saldos':
                        subcarpeta_destino = 'sumas_saldos'
                    else:
                        subcarpeta_destino = 'desconocido'

                    registro = {
                        'Ruta Original': str(archivo.relative_to(Path('./datos_originales'))),
                        'Ruta Completa': str(archivo),
                        'Sociedad': nombre_sociedad,
                        'Año': ano,
                        'Tipo': tipo,
                        'Nombre Original': archivo.name,
                        'Extensión Original': archivo.suffix,
                        'Tamaño (bytes)': archivo.stat().st_size,
                        'Nombre Destino': nombre_destino + '.csv',
                        'Subcarpeta Destino': subcarpeta_destino,
                        'Ruta Destino': f'datos_tratados/{subcarpeta_destino}/{nombre_destino}.csv',
                        'Confianza': prioridad,
                        'Múltiple': 'Sí' if len(lista_archivos) > 1 else 'No',
                        'Notas': ''
                    }

                    registros.append(registro)

    else:
        # Procesar archivos directamente (sin subcarpetas de años)
        archivos = [f for f in ruta_sociedad.iterdir() if f.is_file()]

        # Agrupar archivos por tipo
        archivos_por_tipo = {'Libro Diario': [], 'Sumas y Saldos': [], 'Desconocido': []}

        for archivo in archivos:
            tipo, prioridad = identificar_tipo_archivo(archivo.name)
            archivos_por_tipo[tipo].append((archivo, prioridad))

        # Procesar cada tipo
        for tipo, lista_archivos in archivos_por_tipo.items():
            if not lista_archivos:
                continue

            # Ordenar por prioridad y nombre
            lista_archivos.sort(key=lambda x: (-x[1], x[0].name))

            # Numerar si hay múltiples archivos del mismo tipo
            for idx, (archivo, prioridad) in enumerate(lista_archivos, start=1):
                indice = idx if len(lista_archivos) > 1 else None
                nombre_destino = generar_nombre_destino(nombre_sociedad, tipo, None, indice)

                # Determinar subcarpeta destino
                if tipo == 'Libro Diario':
                    subcarpeta_destino = 'libro_diario'
                elif tipo == 'Sumas y Saldos':
                    subcarpeta_destino = 'sumas_saldos'
                else:
                    subcarpeta_destino = 'desconocido'

                # Agregar nota si es archivo múltiple (trimestre, código, etc.)
                notas = []
                if 'Q1' in archivo.name.upper() or '01.01' in archivo.name or '31.03' in archivo.name:
                    notas.append('Trimestre 1')
                elif 'Q2' in archivo.name.upper() or '01.04' in archivo.name or '30.06' in archivo.name:
                    notas.append('Trimestre 2')
                elif 'Q3' in archivo.name.upper() or '01.07' in archivo.name or '30.09' in archivo.name:
                    notas.append('Trimestre 3')
                elif 'Q4' in archivo.name.upper() or '01.10' in archivo.name or '31.12' in archivo.name:
                    notas.append('Trimestre 4')

                # Detectar códigos especiales (ej: LD_4200)
                match_codigo = re.search(r'_(\d{4})_', archivo.name)
                if match_codigo:
                    notas.append(f'Código: {match_codigo.group(1)}')

                # Detectar partes (ej: AA00, AA01)
                match_parte = re.search(r'AA(\d{2})', archivo.name.upper())
                if match_parte:
                    notas.append(f'Parte: AA{match_parte.group(1)}')

                registro = {
                    'Ruta Original': str(archivo.relative_to(Path('./datos_originales'))),
                    'Ruta Completa': str(archivo),
                    'Sociedad': nombre_sociedad,
                    'Año': None,
                    'Tipo': tipo,
                    'Nombre Original': archivo.name,
                    'Extensión Original': archivo.suffix,
                    'Tamaño (bytes)': archivo.stat().st_size,
                    'Nombre Destino': nombre_destino + '.csv',
                    'Subcarpeta Destino': subcarpeta_destino,
                    'Ruta Destino': f'datos_tratados/{subcarpeta_destino}/{nombre_destino}.csv',
                    'Confianza': prioridad,
                    'Múltiple': 'Sí' if len(lista_archivos) > 1 else 'No',
                    'Notas': '; '.join(notas) if notas else ''
                }

                registros.append(registro)

    return registros


def formatear_tamano(tamano_bytes: int) -> str:
    """
    Convierte un tamaño en bytes a una representación legible.

    Args:
        tamano_bytes: Tamaño en bytes

    Returns:
        String con el tamaño formateado
    """
    for unidad in ['B', 'KB', 'MB', 'GB']:
        if tamano_bytes < 1024.0:
            return f"{tamano_bytes:.2f} {unidad}"
        tamano_bytes /= 1024.0
    return f"{tamano_bytes:.2f} TB"


def generar_mapeo(ruta_base: str = './datos_originales',
                  archivo_salida: str = 'mapeo_archivos.xlsx') -> None:
    """
    Genera el mapeo completo de archivos y lo guarda en Excel.

    Args:
        ruta_base: Ruta a la carpeta de datos originales
        archivo_salida: Nombre del archivo Excel de salida
    """
    print("=" * 80)
    print("GENERACIÓN DE MAPEO DE ARCHIVOS CONTABLES".center(80))
    print("=" * 80)
    print(f"\nFecha y hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"Carpeta analizada: {os.path.abspath(ruta_base)}")
    print("\nAnalizando estructura...")

    # Verificar que existe la carpeta
    ruta_datos = Path(ruta_base)
    if not ruta_datos.exists():
        print(f"\nERROR: No se encuentra la carpeta '{ruta_base}'")
        return

    # Obtener todas las sociedades
    sociedades = [d for d in ruta_datos.iterdir() if d.is_dir()]
    sociedades.sort(key=lambda x: x.name)

    print(f"Sociedades encontradas: {len(sociedades)}")
    print()

    # Analizar cada sociedad
    todos_registros = []

    for idx, sociedad in enumerate(sociedades, 1):
        print(f"  [{idx}/{len(sociedades)}] Procesando: {sociedad.name}")
        registros = analizar_sociedad(sociedad, sociedad.name)
        todos_registros.extend(registros)

    # Crear DataFrame
    df = pd.DataFrame(todos_registros)

    # Añadir columna de tamaño legible
    df['Tamaño'] = df['Tamaño (bytes)'].apply(formatear_tamano)

    # Reordenar columnas
    columnas_orden = [
        'Sociedad',
        'Año',
        'Tipo',
        'Nombre Original',
        'Extensión Original',
        'Tamaño',
        'Nombre Destino',
        'Ruta Destino',
        'Ruta Original',
        'Múltiple',
        'Confianza',
        'Notas'
    ]

    df = df[columnas_orden]

    # Guardar en Excel con formato
    with pd.ExcelWriter(archivo_salida, engine='openpyxl') as writer:
        # Hoja principal con todos los datos
        df.to_excel(writer, sheet_name='Mapeo Completo', index=False)

        # Hoja de resumen por sociedad
        resumen_sociedad = df.groupby('Sociedad').agg({
            'Nombre Original': 'count',
            'Tipo': lambda x: f"LD: {(x=='Libro Diario').sum()}, SYS: {(x=='Sumas y Saldos').sum()}"
        }).rename(columns={'Nombre Original': 'Total Archivos', 'Tipo': 'Distribución'})
        resumen_sociedad.to_excel(writer, sheet_name='Resumen por Sociedad')

        # Hoja de resumen por tipo
        resumen_tipo = df.groupby('Tipo').size().to_frame('Total')
        resumen_tipo.to_excel(writer, sheet_name='Resumen por Tipo')

        # Hoja de archivos con problemas potenciales
        problemas = df[
            (df['Tipo'] == 'Desconocido') |
            (df['Confianza'] < 5) |
            (df['Múltiple'] == 'Sí')
        ].copy()
        if not problemas.empty:
            problemas.to_excel(writer, sheet_name='Revisar', index=False)

        # Ajustar anchos de columna
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width

    # Mostrar resumen
    print("\n" + "=" * 80)
    print("RESUMEN DEL MAPEO".center(80))
    print("=" * 80)
    print(f"\nTotal de archivos procesados: {len(df)}")
    print(f"  - Libros Diario:            {(df['Tipo'] == 'Libro Diario').sum()}")
    print(f"  - Sumas y Saldos:           {(df['Tipo'] == 'Sumas y Saldos').sum()}")
    print(f"  - Desconocidos:             {(df['Tipo'] == 'Desconocido').sum()}")
    print(f"\nArchivos múltiples:           {(df['Múltiple'] == 'Sí').sum()}")
    print(f"Archivos con año:             {df['Año'].notna().sum()}")
    print(f"\nArchivo generado: {os.path.abspath(archivo_salida)}")
    print("\n" + "=" * 80)
    print("\nRevisa el archivo Excel para ver el mapeo completo y planificar")
    print("la reorganización a la carpeta 'datos_tratados'.")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    """
    Punto de entrada principal del script.
    """
    import sys

    # Permitir especificar ruta personalizada
    ruta = sys.argv[1] if len(sys.argv) > 1 else './datos_originales'

    # Permitir especificar archivo de salida
    salida = sys.argv[2] if len(sys.argv) > 2 else 'mapeo_archivos.xlsx'

    try:
        generar_mapeo(ruta, salida)
    except KeyboardInterrupt:
        print("\n\nOperación cancelada por el usuario.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
