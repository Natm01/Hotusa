#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Inventario de Datos Contables - Hotusa
=================================================

Este script analiza el contenido de la carpeta 'datos_originales' y genera
un reporte detallado de todas las sociedades y sus archivos contables.

Estructura esperada:
    datos_originales/
        ├── Sociedad 1/
        │   ├── LD FECHA.XLS  (Libro Diario)
        │   └── SYS FECHA.XLS (Sumas y Saldos)
        ├── Sociedad 2/
        │   ├── LD FECHA.XLS
        │   └── SYS FECHA.XLS
        └── ...

Autor: Script generado para análisis de datos contables
Fecha: 2025-10-31
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import sys


def formatear_tamano(tamano_bytes: int) -> str:
    """
    Convierte un tamaño en bytes a una representación legible.

    Args:
        tamano_bytes: Tamaño en bytes

    Returns:
        String con el tamaño formateado (ej: "8.25 MB", "89.49 KB")
    """
    for unidad in ['B', 'KB', 'MB', 'GB']:
        if tamano_bytes < 1024.0:
            return f"{tamano_bytes:.2f} {unidad}"
        tamano_bytes /= 1024.0
    return f"{tamano_bytes:.2f} TB"


def obtener_tipo_archivo(nombre_archivo: str) -> str:
    """
    Identifica el tipo de archivo contable según su nombre.

    Args:
        nombre_archivo: Nombre del archivo

    Returns:
        Tipo de archivo: 'Libro Diario', 'Sumas y Saldos', u 'Otro'
    """
    nombre_upper = nombre_archivo.upper()

    if nombre_upper.startswith('LD '):
        return 'Libro Diario'
    elif nombre_upper.startswith('SYS '):
        return 'Sumas y Saldos'
    else:
        return 'Otro'


def analizar_sociedad(ruta_sociedad: Path) -> Dict:
    """
    Analiza una carpeta de sociedad y extrae información de sus archivos.

    Args:
        ruta_sociedad: Path de la carpeta de la sociedad

    Returns:
        Diccionario con información de la sociedad y sus archivos
    """
    info_sociedad = {
        'nombre': ruta_sociedad.name,
        'ruta': str(ruta_sociedad),
        'archivos': [],
        'tiene_libro_diario': False,
        'tiene_sumas_saldos': False,
        'tamano_total': 0,
        'errores': []
    }

    try:
        # Listar todos los archivos en la carpeta de la sociedad
        archivos = [f for f in ruta_sociedad.iterdir() if f.is_file()]

        for archivo in archivos:
            try:
                stats = archivo.stat()
                tipo_archivo = obtener_tipo_archivo(archivo.name)

                info_archivo = {
                    'nombre': archivo.name,
                    'tipo': tipo_archivo,
                    'tamano': stats.st_size,
                    'tamano_formateado': formatear_tamano(stats.st_size),
                    'fecha_modificacion': datetime.fromtimestamp(stats.st_mtime)
                }

                info_sociedad['archivos'].append(info_archivo)
                info_sociedad['tamano_total'] += stats.st_size

                # Marcar si tiene los archivos principales
                if tipo_archivo == 'Libro Diario':
                    info_sociedad['tiene_libro_diario'] = True
                elif tipo_archivo == 'Sumas y Saldos':
                    info_sociedad['tiene_sumas_saldos'] = True

            except Exception as e:
                info_sociedad['errores'].append(f"Error al leer {archivo.name}: {str(e)}")

    except Exception as e:
        info_sociedad['errores'].append(f"Error al acceder a la carpeta: {str(e)}")

    return info_sociedad


def generar_reporte(ruta_base: str = './datos_originales') -> None:
    """
    Genera un reporte completo del inventario de datos contables.

    Args:
        ruta_base: Ruta a la carpeta de datos originales
    """
    print("=" * 80)
    print("INVENTARIO DE DATOS CONTABLES - HOTUSA".center(80))
    print("=" * 80)
    print(f"\nFecha y hora del análisis: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"Carpeta analizada: {os.path.abspath(ruta_base)}")
    print("\n" + "-" * 80 + "\n")

    # Verificar que existe la carpeta
    ruta_datos = Path(ruta_base)
    if not ruta_datos.exists():
        print(f"ERROR: No se encuentra la carpeta '{ruta_base}'")
        sys.exit(1)

    if not ruta_datos.is_dir():
        print(f"ERROR: '{ruta_base}' no es una carpeta")
        sys.exit(1)

    # Obtener todas las carpetas de sociedades
    sociedades = [d for d in ruta_datos.iterdir() if d.is_dir()]

    if not sociedades:
        print("ADVERTENCIA: No se encontraron carpetas de sociedades")
        return

    # Analizar cada sociedad
    resultados = []
    for sociedad in sorted(sociedades, key=lambda x: x.name):
        info = analizar_sociedad(sociedad)
        resultados.append(info)

    # Mostrar información detallada de cada sociedad
    for idx, sociedad in enumerate(resultados, 1):
        print(f"{idx}. SOCIEDAD: {sociedad['nombre']}")
        print(f"   {'─' * 70}")

        if sociedad['errores']:
            print(f"   ⚠ ERRORES:")
            for error in sociedad['errores']:
                print(f"      - {error}")

        if sociedad['archivos']:
            print(f"   Archivos encontrados: {len(sociedad['archivos'])}")

            for archivo in sociedad['archivos']:
                tipo_emoji = "📊" if archivo['tipo'] == 'Libro Diario' else \
                            "📈" if archivo['tipo'] == 'Sumas y Saldos' else "📄"
                print(f"      {tipo_emoji} {archivo['nombre']}")
                print(f"         Tipo: {archivo['tipo']}")
                print(f"         Tamaño: {archivo['tamano_formateado']}")
                print(f"         Fecha: {archivo['fecha_modificacion'].strftime('%d/%m/%Y %H:%M')}")
                print()

            # Estado de completitud
            completa = sociedad['tiene_libro_diario'] and sociedad['tiene_sumas_saldos']
            estado = "✓ COMPLETA" if completa else "⚠ INCOMPLETA"
            print(f"   Estado: {estado}")

            if not completa:
                faltantes = []
                if not sociedad['tiene_libro_diario']:
                    faltantes.append("Libro Diario")
                if not sociedad['tiene_sumas_saldos']:
                    faltantes.append("Sumas y Saldos")
                print(f"   Archivos faltantes: {', '.join(faltantes)}")

            print(f"   Tamaño total: {formatear_tamano(sociedad['tamano_total'])}")
        else:
            print(f"   ⚠ CARPETA VACÍA")

        print("\n" + "-" * 80 + "\n")

    # Generar resumen estadístico
    print("=" * 80)
    print("RESUMEN ESTADÍSTICO".center(80))
    print("=" * 80)
    print()

    total_sociedades = len(resultados)
    sociedades_completas = sum(1 for s in resultados if s['tiene_libro_diario'] and s['tiene_sumas_saldos'])
    sociedades_incompletas = total_sociedades - sociedades_completas
    total_archivos = sum(len(s['archivos']) for s in resultados)
    tamano_total = sum(s['tamano_total'] for s in resultados)
    libros_diario = sum(1 for s in resultados if s['tiene_libro_diario'])
    sumas_saldos = sum(1 for s in resultados if s['tiene_sumas_saldos'])

    print(f"Total de sociedades:          {total_sociedades}")
    print(f"  - Completas (LD + SYS):     {sociedades_completas}")
    print(f"  - Incompletas:              {sociedades_incompletas}")
    print()
    print(f"Total de archivos:            {total_archivos}")
    print(f"  - Libros Diario (LD):       {libros_diario}")
    print(f"  - Sumas y Saldos (SYS):     {sumas_saldos}")
    print()
    print(f"Tamaño total de datos:        {formatear_tamano(tamano_total)}")
    print()

    # Listar sociedades incompletas si las hay
    if sociedades_incompletas > 0:
        print("SOCIEDADES INCOMPLETAS:")
        for s in resultados:
            if not (s['tiene_libro_diario'] and s['tiene_sumas_saldos']):
                faltantes = []
                if not s['tiene_libro_diario']:
                    faltantes.append("LD")
                if not s['tiene_sumas_saldos']:
                    faltantes.append("SYS")
                print(f"  - {s['nombre']} (falta: {', '.join(faltantes)})")
        print()

    print("=" * 80)
    print("FIN DEL REPORTE".center(80))
    print("=" * 80)


if __name__ == "__main__":
    """
    Punto de entrada principal del script.
    """
    # Permitir especificar una ruta personalizada como argumento
    ruta = sys.argv[1] if len(sys.argv) > 1 else './datos_originales'

    try:
        generar_reporte(ruta)
    except KeyboardInterrupt:
        print("\n\nOperación cancelada por el usuario.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nERROR INESPERADO: {str(e)}")
        sys.exit(1)
