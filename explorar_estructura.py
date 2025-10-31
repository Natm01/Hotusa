#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Exploración de Estructura - Datos Originales
======================================================

Este script explora recursivamente la carpeta 'datos_originales' y genera
un archivo de texto con toda la estructura de carpetas y archivos encontrados.

El resultado incluye:
- Árbol de directorios completo
- Nombres de todos los archivos
- Tamaños de archivos
- Extensiones
- Fechas de modificación

Autor: Script de exploración de estructura
Fecha: 2025-10-31
"""

import os
from pathlib import Path
from datetime import datetime
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


def explorar_directorio(ruta_base: str, archivo_salida: str = 'estructura_datos.txt'):
    """
    Explora recursivamente un directorio y genera un archivo con su estructura.

    Args:
        ruta_base: Ruta del directorio a explorar
        archivo_salida: Nombre del archivo de salida donde guardar la estructura
    """

    # Abrir archivo de salida para escritura
    with open(archivo_salida, 'w', encoding='utf-8') as f:
        # Escribir encabezado
        f.write("=" * 100 + "\n")
        f.write("ESTRUCTURA DE DATOS ORIGINALES - HOTUSA\n")
        f.write("=" * 100 + "\n\n")
        f.write(f"Fecha y hora del análisis: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write(f"Carpeta analizada: {os.path.abspath(ruta_base)}\n")
        f.write("\n" + "=" * 100 + "\n\n")

        # Verificar que existe la carpeta
        ruta_datos = Path(ruta_base)
        if not ruta_datos.exists():
            f.write(f"ERROR: No se encuentra la carpeta '{ruta_base}'\n")
            print(f"ERROR: No se encuentra la carpeta '{ruta_base}'")
            return

        if not ruta_datos.is_dir():
            f.write(f"ERROR: '{ruta_base}' no es una carpeta\n")
            print(f"ERROR: '{ruta_base}' no es una carpeta")
            return

        # Contadores para estadísticas
        total_carpetas = 0
        total_archivos = 0
        total_bytes = 0
        extensiones = {}

        # Función recursiva para explorar directorios
        def explorar_recursivo(ruta_actual: Path, nivel: int = 0, prefijo: str = ""):
            nonlocal total_carpetas, total_archivos, total_bytes, extensiones

            try:
                # Obtener todos los elementos en el directorio actual
                elementos = sorted(ruta_actual.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))

                for idx, elemento in enumerate(elementos):
                    # Determinar si es el último elemento
                    es_ultimo = (idx == len(elementos) - 1)

                    # Símbolos para el árbol
                    if es_ultimo:
                        simbolo = "└── "
                        extension_prefijo = "    "
                    else:
                        simbolo = "├── "
                        extension_prefijo = "│   "

                    if elemento.is_dir():
                        # Es un directorio
                        total_carpetas += 1
                        nombre_carpeta = f"[{elemento.name}]"
                        f.write(f"{prefijo}{simbolo}{nombre_carpeta}\n")

                        # Explorar recursivamente
                        explorar_recursivo(elemento, nivel + 1, prefijo + extension_prefijo)

                    else:
                        # Es un archivo
                        total_archivos += 1
                        stats = elemento.stat()
                        tamano = stats.st_size
                        total_bytes += tamano
                        fecha_mod = datetime.fromtimestamp(stats.st_mtime)
                        extension = elemento.suffix.lower() if elemento.suffix else '(sin extensión)'

                        # Contar extensiones
                        if extension in extensiones:
                            extensiones[extension] += 1
                        else:
                            extensiones[extension] = 1

                        # Formatear información del archivo
                        info_archivo = (
                            f"{elemento.name} "
                            f"[{formatear_tamano(tamano)}] "
                            f"[{fecha_mod.strftime('%d/%m/%Y %H:%M')}]"
                        )

                        f.write(f"{prefijo}{simbolo}{info_archivo}\n")

            except PermissionError:
                f.write(f"{prefijo}[ERROR: Sin permisos para acceder a esta carpeta]\n")
            except Exception as e:
                f.write(f"{prefijo}[ERROR: {str(e)}]\n")

        # Escribir nombre de la carpeta raíz
        f.write(f"[{ruta_datos.name}]\n")

        # Explorar recursivamente desde la raíz
        explorar_recursivo(ruta_datos, 0, "")

        # Escribir estadísticas al final
        f.write("\n" + "=" * 100 + "\n")
        f.write("ESTADÍSTICAS\n")
        f.write("=" * 100 + "\n\n")
        f.write(f"Total de carpetas:        {total_carpetas}\n")
        f.write(f"Total de archivos:        {total_archivos}\n")
        f.write(f"Tamaño total:             {formatear_tamano(total_bytes)}\n")
        f.write(f"\n")
        f.write(f"DISTRIBUCIÓN POR TIPO DE ARCHIVO:\n")
        f.write(f"-" * 50 + "\n")

        # Ordenar extensiones por cantidad (descendente)
        for ext, cantidad in sorted(extensiones.items(), key=lambda x: x[1], reverse=True):
            f.write(f"  {ext:<20} {cantidad:>5} archivo(s)\n")

        f.write("\n" + "=" * 100 + "\n")
        f.write("FIN DEL ANÁLISIS\n")
        f.write("=" * 100 + "\n")

    # Informar al usuario
    print(f"\n{'=' * 80}")
    print(f"EXPLORACIÓN COMPLETADA")
    print(f"{'=' * 80}\n")
    print(f"Carpeta analizada:     {os.path.abspath(ruta_base)}")
    print(f"Archivo generado:      {os.path.abspath(archivo_salida)}")
    print(f"\nEstadísticas:")
    print(f"  - Total carpetas:    {total_carpetas}")
    print(f"  - Total archivos:    {total_archivos}")
    print(f"  - Tamaño total:      {formatear_tamano(total_bytes)}")
    print(f"\n{'=' * 80}\n")
    print(f"Revisa el archivo '{archivo_salida}' para ver la estructura completa.\n")


if __name__ == "__main__":
    """
    Punto de entrada principal del script.
    """
    # Permitir especificar una ruta personalizada como argumento
    if len(sys.argv) > 1:
        ruta = sys.argv[1]
    else:
        ruta = './datos_originales'

    # Archivo de salida (se puede personalizar como segundo argumento)
    if len(sys.argv) > 2:
        salida = sys.argv[2]
    else:
        salida = 'estructura_datos.txt'

    try:
        explorar_directorio(ruta, salida)
    except KeyboardInterrupt:
        print("\n\nOperación cancelada por el usuario.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nERROR INESPERADO: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
