#!/bin/bash

# TEST VERSION - Process only ONE file for testing
# Minimal logging version

# Configuration
SOURCE_DIR="/localdata/drive1/dpsaltis3/SgrAData/Data"
WORK_DIR="${HOME}/SgrA"
OUTPUT_DIR="${HOME}/SgrA/simulation_movies"
PYTHON_SCRIPT="${WORK_DIR}/simMovie.py"
LOG_FILE="${HOME}/SgrA/test_processing_log.txt"

# Create necessary directories
mkdir -p "$WORK_DIR"
mkdir -p "$OUTPUT_DIR"

# Initialize log file
echo "======================================" > "$LOG_FILE"
echo "TEST RUN - Processing ONE file only" >> "$LOG_FILE"
echo "Started at $(date)" >> "$LOG_FILE"
echo "======================================" >> "$LOG_FILE"

# Check if Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "ERROR: Python script not found at $PYTHON_SCRIPT" | tee -a "$LOG_FILE"
    exit 1
fi

# Get the first .tar.gz file
cd "$SOURCE_DIR" || { echo "Error: Cannot access $SOURCE_DIR" | tee -a "$LOG_FILE"; exit 1; }

tarfile=$(ls -1 *.tar.gz 2>/dev/null | head -1)

if [ -z "$tarfile" ]; then
    echo "No .tar.gz files found in $SOURCE_DIR" | tee -a "$LOG_FILE"
    exit 0
fi

echo "" | tee -a "$LOG_FILE"
echo "TEST: Processing $tarfile" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

BASENAME=$(basename "$tarfile" .tar.gz)

# Copy file
if ! cp "${SOURCE_DIR}/${tarfile}" "${WORK_DIR}/" 2>> "$LOG_FILE"; then
    echo "ERROR: Failed to copy file" | tee -a "$LOG_FILE"
    exit 1
fi

cd "$WORK_DIR" || { echo "Error: Cannot access $WORK_DIR" | tee -a "$LOG_FILE"; exit 1; }

# Extract
if ! tar -xzf "$tarfile" -C "${WORK_DIR}" 2>> "$LOG_FILE"; then
    echo "ERROR: Extraction failed" | tee -a "$LOG_FILE"
    rm -f "$tarfile"
    exit 1
fi

# Find extracted directory
EXTRACTED_DIR=$(find "${WORK_DIR}" -maxdepth 1 -type d ! -path "${WORK_DIR}" ! -path "${WORK_DIR}/simulation_movies" | head -1)

if [ -z "$EXTRACTED_DIR" ]; then
    if ls "${WORK_DIR}"/*.h5 1> /dev/null 2>&1; then
        EXTRACTED_DIR="${WORK_DIR}"
    else
        echo "ERROR: No extracted directory or .h5 files found" | tee -a "$LOG_FILE"
        rm -f "$tarfile"
        exit 1
    fi
fi

# Run Python script
OUTPUT_MOVIE="${OUTPUT_DIR}/${BASENAME}.mp4"

if python3 "$PYTHON_SCRIPT" "$EXTRACTED_DIR" --outfile "$OUTPUT_MOVIE" --fps 10 --filename "$BASENAME" >> "$LOG_FILE" 2>&1; then
    echo "✓ Movie created successfully: ${BASENAME}.mp4" | tee -a "$LOG_FILE"
else
    echo "ERROR: Python script failed" | tee -a "$LOG_FILE"
fi

# Cleanup
rm -f "$tarfile"
if [ "$EXTRACTED_DIR" != "$WORK_DIR" ] && [ -d "$EXTRACTED_DIR" ]; then
    rm -rf "$EXTRACTED_DIR" 2>> "$LOG_FILE"
fi

echo "" | tee -a "$LOG_FILE"
echo "======================================" >> "$LOG_FILE"
echo "TEST completed at $(date)" >> "$LOG_FILE"
echo "======================================" >> "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "Test complete!" | tee -a "$LOG_FILE"
echo "Movie saved in: $OUTPUT_DIR" | tee -a "$LOG_FILE"
echo "Check $LOG_FILE for details." | tee -a "$LOG_FILE"