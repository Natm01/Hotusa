# Inventario de Datos Contables - Hotusa

## Descripción

Script de Python para realizar un inventario completo de los datos contables almacenados en la carpeta `datos_originales`. El script analiza cada sociedad y genera un reporte detallado con información sobre los archivos de Libro Diario (LD) y Sumas y Saldos (SYS).

## Estructura de Datos

```
datos_originales/
├── Sociedad 1/
│   ├── LD FECHA.XLS  (Libro Diario)
│   └── SYS FECHA.XLS (Sumas y Saldos)
├── Sociedad 2/
│   ├── LD FECHA.XLS
│   └── SYS FECHA.XLS
└── ...
```

## Uso

### Ejecución básica

```bash
python3 inventario_datos.py
```

### Especificar una ruta personalizada

```bash
python3 inventario_datos.py /ruta/a/datos_originales
```

## Información que Proporciona

El script genera un reporte que incluye:

### Por cada sociedad:
- Nombre de la sociedad
- Lista de archivos encontrados
- Tipo de cada archivo (Libro Diario, Sumas y Saldos, u Otro)
- Tamaño de cada archivo
- Fecha de modificación
- Estado de completitud (si tiene ambos archivos requeridos)
- Tamaño total de la sociedad

### Resumen estadístico:
- Número total de sociedades
- Sociedades completas e incompletas
- Total de archivos analizados
- Desglose por tipo de archivo
- Tamaño total de todos los datos
- Listado de sociedades incompletas (si las hay)

## Requisitos

- Python 3.6 o superior
- Bibliotecas estándar (no requiere instalación adicional)

## Características

- Formateo automático de tamaños de archivo (B, KB, MB, GB)
- Identificación automática de tipos de archivo
- Detección de sociedades incompletas
- Manejo de errores robusto
- Salida clara y profesional
- Código completamente comentado

## Ejemplo de Salida

```
================================================================================
                     INVENTARIO DE DATOS CONTABLES - HOTUSA
================================================================================

Fecha y hora del análisis: 31/10/2025 07:23:11
Carpeta analizada: /home/user/Hotusa/datos_originales

--------------------------------------------------------------------------------

1. SOCIEDAD: Argon Hotel
   ──────────────────────────────────────────────────────────────────────
   Archivos encontrados: 2
      📈 SYS 30.09.2025.XLS
         Tipo: Sumas y Saldos
         Tamaño: 87.39 KB
         Fecha: 31/10/2025 07:21

      📊 LD 30.09.2025.XLS
         Tipo: Libro Diario
         Tamaño: 7.87 MB
         Fecha: 31/10/2025 07:21

   Estado: ✓ COMPLETA
   Tamaño total: 7.96 MB

--------------------------------------------------------------------------------

================================================================================
                              RESUMEN ESTADÍSTICO
================================================================================

Total de sociedades:          1
  - Completas (LD + SYS):     1
  - Incompletas:              0

Total de archivos:            2
  - Libros Diario (LD):       1
  - Sumas y Saldos (SYS):     1

Tamaño total de datos:        7.96 MB

================================================================================
                                FIN DEL REPORTE
================================================================================
```

## Autor

Script desarrollado para análisis de datos contables de Hotusa
