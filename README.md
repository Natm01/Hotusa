# Scripts de Análisis y Organización de Datos Contables - Hotusa

## Descripción

Conjunto de scripts de Python para analizar, mapear y organizar los datos contables almacenados en la carpeta `datos_originales`. Los scripts identifican sociedades, libros diario y sumas y saldos, y generan un plan de reorganización hacia `datos_tratados`.

## Scripts Disponibles

### 1. explorar_estructura.py - Exploración de Estructura

Explora recursivamente la carpeta `datos_originales` y genera un archivo de texto con toda la estructura de directorios y archivos.

#### Uso:
```bash
python3 explorar_estructura.py
```

#### Genera:
- `estructura_datos.txt` - Árbol completo con tamaños y fechas de modificación

#### Propósito:
Visualizar la estructura actual antes de comenzar la reorganización.

---

### 2. mapear_archivos_csv.py - Mapeo de Archivos

Analiza todos los archivos en `datos_originales` e identifica automáticamente:
- Sociedades
- Libros Diario vs Sumas y Saldos
- Estructura por años (ej: Bemus Hotels con carpetas 2017-2024)
- Archivos múltiples (trimestres, códigos, partes)

Genera un plan completo de reorganización hacia `datos_tratados`.

#### Uso:
```bash
python3 mapear_archivos_csv.py
```

#### Genera:
- `mapeo_archivos.csv` - Tabla con todos los archivos y destinos propuestos
- `mapeo_archivos.json` - Formato JSON para procesamiento automatizado
- `mapeo_archivos.txt` - Reporte legible con toda la información

#### Estructura de Salida Propuesta:
```
datos_tratados/
├── libro_diario/
│   ├── Acteon_Siglo_XXI_libro_diario.csv
│   ├── Argon_Hotel_libro_diario.csv
│   ├── 2017_Bemus_Hotels_libro_diario.csv
│   ├── 2018_Bemus_Hotels_libro_diario.csv
│   ├── Braide_libro_diario_parte1.csv
│   ├── Braide_libro_diario_parte2.csv
│   └── ...
└── sumas_saldos/
    ├── Acteon_Siglo_XXI_sumas_saldos.csv
    ├── Argon_Hotel_sumas_saldos.csv
    ├── 2017_Bemus_Hotels_sumas_saldos.csv
    └── ...
```

#### Características de Identificación:
- **Libro Diario**: Detecta "LD", "Diario", "LIBRO DIARIO"
- **Sumas y Saldos**: Detecta "SYS", "SyS", "Balance", "Sumas y saldos"
- **Años**: Detecta subcarpetas con formato 2017, 2018, etc.
- **Múltiples**: Identifica trimestres, códigos (LD_4200), partes (AA00, AA01)

---

### 3. inventario_datos.py - Inventario Rápido

Script original para generar un reporte rápido del estado actual de los datos.

#### Uso:
```bash
python3 inventario_datos.py
```

---

## Estructura de Datos Original

### Sociedades con archivos directos:
```
datos_originales/
└── Argon Hotel/
    ├── LD 30.09.2025.XLS
    └── SYS 30.09.2025.XLS
```

### Sociedades con estructura por años:
```
datos_originales/
└── Bemus Hotels/
    ├── 2017/
    │   ├── Diario a 31.12.2017.XLS
    │   └── Balance de sumas y saldos 31.12.2017.XLS
    ├── 2018/
    │   ├── Diario a 31.12.2018.XLS
    │   └── Balance de sumas y saldos 31.12.2018.XLS
    └── ...
```

### Sociedades con archivos múltiples:
```
datos_originales/
└── Braide/
    ├── BRAIDE - Diario 01.01.2025 a 31.03.2025.XLS
    ├── BRAIDE - Diario 01.04.2025 a 30.06.2025.XLS
    ├── BRAIDE - Diario 01.07.2025 a 30.09.2025.XLS
    └── BRAIDE - 1000.25 Sumas y saldos 30.09.2025.XLS
```

## Flujo de Trabajo Recomendado

1. **Explorar la estructura actual**:
   ```bash
   python3 explorar_estructura.py
   ```
   Revisa `estructura_datos.txt` para familiarizarte con los datos.

2. **Generar el mapeo de reorganización**:
   ```bash
   python3 mapear_archivos_csv.py
   ```
   Revisa los archivos generados:
   - `mapeo_archivos.txt` - Para lectura rápida
   - `mapeo_archivos.csv` - Para análisis en Excel
   - `mapeo_archivos.json` - Para procesamiento automatizado

3. **Verificar el mapeo**:
   - Revisa que todos los archivos estén correctamente identificados
   - Verifica que los nombres destino sean correctos
   - Confirma que las sociedades con años estén agrupadas apropiadamente

4. **Ejecutar la reorganización** (próximo script):
   - El siguiente paso será crear un script que lea el mapeo
   - Convierta los archivos XLS/XLSX a CSV
   - Los reorganice en la carpeta `datos_tratados`

## Requisitos

- Python 3.6 o superior
- Bibliotecas estándar (no requiere instalación adicional)

## Características

- Identificación automática de tipos de archivo con sistema de confianza
- Manejo de estructuras complejas (años, trimestres, códigos)
- Formateo automático de tamaños de archivo (B, KB, MB, GB)
- Normalización de nombres de archivo
- Detección de archivos múltiples
- Código completamente comentado
- Manejo robusto de errores
- Salida clara y profesional

## Casos Especiales Soportados

- **Bemus Hotels**: Subcarpetas por años (2017-2024)
- **Braide, Cygnus, Explotadora Madrid Tower**: Archivos divididos por trimestres
- **Hoteles Turísticos Unidos**: Archivos con códigos (LD_4200, LD_4201, etc.)
- **Estrela de Santiago**: Archivos divididos en partes (AA00, AA01)
- **Extensiones mixtas**: .XLS, .xlsx, .xlsm

## Notas Importantes

- Los nombres de archivo destino siguen el formato:
  - Sin año: `Sociedad_tipo.csv`
  - Con año: `Año_Sociedad_tipo.csv`
  - Múltiples: `Sociedad_tipo_parte1.csv`

- Todos los espacios se convierten en guiones bajos
- Los caracteres especiales se eliminan
- Los archivos se reorganizan en dos carpetas: `libro_diario` y `sumas_saldos`

## Autor

Scripts desarrollados para análisis y organización de datos contables de Hotusa
