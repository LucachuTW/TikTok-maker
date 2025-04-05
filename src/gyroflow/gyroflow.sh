#!/bin/bash

# ==============================================================================
# Script para procesar un video con Gyroflow usando un archivo GCSV asociado.
# Uso: ./process_gyroflow.sh <archivo_video> <archivo_gcsv>
# ==============================================================================

# --- Configuración (Intenta encontrar el ejecutable de Gyroflow) ---
# Prioridad 1: Comando 'gyroflow' en el PATH del sistema
# Prioridad 2: Ejecutable './gyroflow' en el directorio actual
if command -v gyroflow &> /dev/null; then
    GYROFLOW_EXECUTABLE="gyroflow"
    echo "INFO: Usando el comando 'gyroflow' encontrado en el PATH."
elif [ -x "./gyroflow" ]; then
    GYROFLOW_EXECUTABLE="./gyroflow"
    echo "INFO: Usando el ejecutable './gyroflow' encontrado en el directorio actual."
else
    echo "ERROR: No se encontró el ejecutable de Gyroflow." >&2
    echo "Asegúrate de que 'gyroflow' esté en tu PATH o coloca este script en el mismo directorio que el ejecutable 'gyroflow'." >&2
    exit 1
fi

# --- Validación de Entradas ---
# Verificar que se proporcionaron exactamente 2 argumentos
if [ "$#" -ne 2 ]; then
    echo "ERROR: Número incorrecto de argumentos." >&2
    echo "Uso: $0 <archivo_video> <archivo_gcsv>" >&2
    exit 1
fi

VIDEO_FILE="$1"
GCSV_FILE="$2"

# Verificar que los archivos de entrada existen
if [ ! -f "$VIDEO_FILE" ]; then
    echo "ERROR: Archivo de video no encontrado: '$VIDEO_FILE'" >&2
    exit 1
fi

if [ ! -f "$GCSV_FILE" ]; then
    echo "ERROR: Archivo GCSV no encontrado: '$GCSV_FILE'" >&2
    exit 1
fi

# --- Ejecución del Procesamiento ---
echo "------------------------------------"
echo "Iniciando procesamiento con Gyroflow"
echo "  Video: '$VIDEO_FILE'"
echo "  GCSV:  '$GCSV_FILE'"
echo "  Comando: $GYROFLOW_EXECUTABLE"
echo "------------------------------------"
echo "Ejecutando: $GYROFLOW_EXECUTABLE \"$VIDEO_FILE\" -g \"$GCSV_FILE\""
echo # Línea en blanco para separar la salida de Gyroflow

# Ejecutar Gyroflow:
# Pasa el archivo de video como argumento posicional.
# Usa '-g' para especificar el archivo GCSV.
# Añadimos '-f' opcionalmente para sobreescribir el archivo de salida si ya existe.
if "$GYROFLOW_EXECUTABLE" "$VIDEO_FILE" -g "$GCSV_FILE" -f; then
    # --- Éxito ---
    INPUT_BASENAME=$(basename "$VIDEO_FILE")
    INPUT_NAME="${INPUT_BASENAME%.*}"
    INPUT_EXT="${INPUT_BASENAME##*.}"
    # Gyroflow por defecto añade el sufijo "_stabilized"
    EXPECTED_OUTPUT="${INPUT_NAME}_stabilized.${INPUT_EXT}"

    echo # Línea en blanco
    echo "------------------------------------"
    echo "Procesamiento de Gyroflow finalizado con ÉXITO."
    echo "El archivo de salida debería llamarse aproximadamente: '$EXPECTED_OUTPUT'"
    echo "(Guardado probablemente en el mismo directorio que el video de entrada)."
    echo "------------------------------------"
    exit 0 # Salir con código 0 (éxito)
else
    # --- Fallo ---
    echo # Línea en blanco
    echo "------------------------------------" >&2
    echo "ERROR: El procesamiento de Gyroflow falló." >&2
    echo "Revisa la salida anterior para ver los detalles del error." >&2
    echo "------------------------------------" >&2
    exit 1 # Salir con código 1 (error)
fi
