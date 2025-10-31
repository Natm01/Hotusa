#!/usr/bin/env python3
"""
Script para analizar la estructura de archivos de Hotusa y generar JSON
con la organización de libros diarios y sumas y saldos por sociedad.
"""

import json
import re
from typing import Dict, List, Any
from pathlib import Path


def es_libro_diario(nombre_archivo: str) -> bool:
    """
    Identifica si un archivo es un libro diario.

    Patrones:
    - LD seguido de espacio o guión bajo
    - Palabra "Diario"
    - LIBRO DIARIO
    """
    nombre_upper = nombre_archivo.upper()
    patrones_ld = [
        r'\bLD[\s_]',  # LD como palabra seguido de espacio o _
        r'\bLD\b',     # LD como palabra completa
        r'DIARIO',     # Contiene "DIARIO"
        r'LIBRO.*DIARIO'  # LIBRO DIARIO
    ]

    for patron in patrones_ld:
        if re.search(patron, nombre_upper):
            return True
    return False


def es_sumas_saldos(nombre_archivo: str) -> bool:
    """
    Identifica si un archivo es de sumas y saldos.

    Patrones:
    - SyS o SYS
    - Balance de sumas y saldos
    - BALANCES SUMAS Y SALDOS
    - Sumas y saldos
    """
    nombre_upper = nombre_archivo.upper()
    patrones_sys = [
        r'\bSYS\b',  # SYS como palabra completa
        r'SUMAS.*SALDOS',  # Sumas y saldos
        r'BALANCE.*SUMAS',  # Balance de sumas
        r'S\sY\sS\b',  # S Y S
    ]

    for patron in patrones_sys:
        if re.search(patron, nombre_upper):
            return True
    return False


def extraer_anio(texto: str) -> str | None:
    """Extrae el año de un texto si existe."""
    # Buscar años en formato [2024] o [2024]
    match = re.search(r'\[(\d{4})\]', texto)
    if match:
        return match.group(1)

    # Buscar años en nombres de archivo (31.12.2024, 30.09.2025, etc.)
    match = re.search(r'(\d{4})', texto)
    if match:
        return match.group(1)

    return None


def extraer_info_archivo(linea: str) -> Dict[str, str] | None:
    """
    Extrae información de una línea que contiene un archivo.

    Retorna un dict con:
    - nombre: nombre del archivo
    - tamano: tamaño del archivo
    - fecha: fecha de modificación
    """
    # Primero, limpiar caracteres de árbol (incluyendo líneas horizontales)
    linea_limpia = re.sub(r'^[│├└─\s]+', '', linea).strip()

    # Patrón para archivos: nombre.ext [tamaño] [fecha]
    # Ejemplo: LD 30.09.2025.XLS [183.31 MB] [30/10/2025 19:27]
    patron = r'^([^/\[]+\.(XLS|xlsx|xlsm))(?:\s+\[([^\]]+)\])(?:\s+\[([^\]]+)\])?'
    match = re.search(patron, linea_limpia, re.IGNORECASE)

    if match:
        return {
            'nombre': match.group(1).strip(),
            'tamano': match.group(3).strip() if match.group(3) else '',
            'fecha': match.group(4).strip() if match.group(4) else ''
        }
    return None


def parsear_estructura(ruta_archivo: str) -> Dict[str, Any]:
    """
    Parsea el archivo de estructura y genera un diccionario con la información.
    """
    with open(ruta_archivo, 'r', encoding='utf-8') as f:
        lineas = f.readlines()

    resultado = {}
    sociedad_actual = None
    anio_actual = None

    for i, linea in enumerate(lineas):
        # Limpiar línea de números de línea y flechas
        linea_limpia = re.sub(r'^\s*\d+→', '', linea)

        # Saltar líneas vacías, separadores y headers
        if not linea_limpia.strip() or '===' in linea or 'ESTRUCTURA' in linea or 'ESTADÍSTICAS' in linea or 'FIN DEL' in linea:
            continue

        # Detectar sociedad (carpeta principal bajo [datos_originales])
        # Patrón: ├── [Nombre] o └── [Nombre]
        match_sociedad = re.search(r'^[├└]──\s+\[([^\]]+)\]', linea_limpia)
        if match_sociedad:
            sociedad_actual = match_sociedad.group(1)
            anio_actual = None
            if sociedad_actual not in resultado:
                resultado[sociedad_actual] = {
                    'nombre': sociedad_actual,
                    'libros_diarios': [],
                    'sumas_saldos': [],
                    'por_anios': {}
                }
            continue

        # Detectar año (subcarpeta)
        # Patrón: │   ├── [2024] (con indentación)
        match_anio = re.search(r'^\s*[│├└].*\[(\d{4})\]', linea_limpia)
        if match_anio and sociedad_actual and '   ' in linea_limpia[:10]:  # Tiene indentación de subcarpeta
            anio_actual = match_anio.group(1)
            if anio_actual not in resultado[sociedad_actual]['por_anios']:
                resultado[sociedad_actual]['por_anios'][anio_actual] = {
                    'anio': anio_actual,
                    'libros_diarios': [],
                    'sumas_saldos': []
                }
            continue

        # Detectar archivos
        info_archivo = extraer_info_archivo(linea_limpia)
        if info_archivo and sociedad_actual:
            nombre = info_archivo['nombre']

            archivo_info = {
                'archivo': nombre,
                'tamano': info_archivo['tamano'],
                'fecha_modificacion': info_archivo['fecha']
            }

            # Si estamos dentro de un año, agregar ahí
            if anio_actual:
                if es_libro_diario(nombre):
                    resultado[sociedad_actual]['por_anios'][anio_actual]['libros_diarios'].append(archivo_info)
                elif es_sumas_saldos(nombre):
                    resultado[sociedad_actual]['por_anios'][anio_actual]['sumas_saldos'].append(archivo_info)
            else:
                # Agregar a nivel de sociedad
                if es_libro_diario(nombre):
                    resultado[sociedad_actual]['libros_diarios'].append(archivo_info)
                elif es_sumas_saldos(nombre):
                    resultado[sociedad_actual]['sumas_saldos'].append(archivo_info)

    # Limpiar sociedades sin datos útiles y reorganizar
    resultado_limpio = []
    for sociedad, datos in resultado.items():
        sociedad_info = {
            'sociedad': sociedad
        }

        # Si tiene años, usar esa estructura
        if datos['por_anios']:
            sociedad_info['por_anios'] = list(datos['por_anios'].values())
        else:
            # Si no tiene años, poner directamente los archivos
            sociedad_info['libros_diarios'] = datos['libros_diarios']
            sociedad_info['sumas_saldos'] = datos['sumas_saldos']

        resultado_limpio.append(sociedad_info)

    return {
        'fecha_analisis': '2025-10-31',
        'total_sociedades': len(resultado_limpio),
        'sociedades': resultado_limpio
    }


def main():
    """Función principal."""
    ruta_estructura = 'estructura_datos.txt'
    ruta_salida = 'estructura_json.json'

    print("🔍 Analizando estructura de archivos...")
    resultado = parsear_estructura(ruta_estructura)

    print(f"✅ Análisis completado:")
    print(f"   - Sociedades procesadas: {resultado['total_sociedades']}")

    # Guardar JSON
    with open(ruta_salida, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    print(f"📄 JSON generado: {ruta_salida}")

    # Mostrar resumen
    print("\n📊 Resumen por sociedad:")
    for sociedad in resultado['sociedades']:
        nombre = sociedad['sociedad']
        if 'por_anios' in sociedad:
            anios = [a['anio'] for a in sociedad['por_anios']]
            print(f"   - {nombre}: {len(anios)} años ({', '.join(anios)})")
        else:
            ld_count = len(sociedad.get('libros_diarios', []))
            sys_count = len(sociedad.get('sumas_saldos', []))
            print(f"   - {nombre}: {ld_count} libros diarios, {sys_count} sumas y saldos")


if __name__ == '__main__':
    main()
