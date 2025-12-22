#!/bin/bash

# Black Hole Simulation Data Processing Script - Minimal Logging Version
# Only logs essential information: start, each movie completion, and final summary

# Configuration
SOURCE_DIR="/localdata/drive1/dpsaltis3/SgrAData/Data"
WORK_DIR="${HOME}/SgrA"
OUTPUT_DIR="${HOME}/SgrA/simulation_movies"
PYTHON_SCRIPT="${WORK_DIR}/simMovie.py"
LOG_FILE="${HOME}/SgrA/processing_log.txt"
ERROR_LOG="${HOME}/SgrA/error_log.txt"

# Create necessary directories
mkdir -p "$WORK_DIR"
mkdir -p "$OUTPUT_DIR"

# Initialize log files
echo "======================================" > "$LOG_FILE"
echo "Processing started at $(date)" >> "$LOG_FILE"
echo "======================================" >> "$LOG_FILE"
echo "" > "$ERROR_LOG"

# Check if Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "[ERROR] Python script not found at $PYTHON_SCRIPT" | tee -a "$LOG_FILE" | tee -a "$ERROR_LOG"
    exit 1
fi

# Get list of all tar.gz files in source directory
cd "$SOURCE_DIR" || { echo "[ERROR] Cannot access $SOURCE_DIR" | tee -a "$LOG_FILE"; exit 1; }
TOTAL_FILES=$(ls -1 *.tar.gz 2>/dev/null | wc -l)
CURRENT=0
SUCCESS_COUNT=0
FAILED_COUNT=0

if [ "$TOTAL_FILES" -eq 0 ]; then
    echo "No .tar.gz files found in $SOURCE_DIR" | tee -a "$LOG_FILE"
    exit 0
fi

echo "Found $TOTAL_FILES .tar.gz files to process" | tee -a "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Process each .tar.gz file one at a time
for tarfile in *.tar.gz; do
    [ -e "$tarfile" ] || continue
    
    CURRENT=$((CURRENT + 1))
    BASENAME=$(basename "$tarfile" .tar.gz)
    
    echo "[$CURRENT/$TOTAL_FILES] Processing: $tarfile" | tee -a "$LOG_FILE"
    
    # Step 1: Copy file
    if ! cp "${SOURCE_DIR}/${tarfile}" "${WORK_DIR}/" 2>> "$LOG_FILE"; then
        echo "  ERROR: Failed to copy - SKIPPING" | tee -a "$LOG_FILE" | tee -a "$ERROR_LOG"
        FAILED_COUNT=$((FAILED_COUNT + 1))
        continue
    fi
    
    cd "$WORK_DIR" || { echo "ERROR: Cannot access $WORK_DIR" | tee -a "$LOG_FILE"; exit 1; }
    
    # Step 2: Extract
    if ! tar -xzf "$tarfile" -C "${WORK_DIR}" 2>> "$LOG_FILE"; then
        echo "  ERROR: Extraction failed - SKIPPING" | tee -a "$LOG_FILE" | tee -a "$ERROR_LOG"
        rm -f "$tarfile"
        FAILED_COUNT=$((FAILED_COUNT + 1))
        cd "$SOURCE_DIR" || exit 1
        continue
    fi
    
    # Step 3: Find extracted directory
    EXTRACTED_DIR=$(find "${WORK_DIR}" -maxdepth 1 -type d ! -path "${WORK_DIR}" ! -path "${WORK_DIR}/simulation_movies" | head -1)
    
    if [ -z "$EXTRACTED_DIR" ]; then
        if ls "${WORK_DIR}"/*.h5 1> /dev/null 2>&1; then
            EXTRACTED_DIR="${WORK_DIR}"
        else
            echo "  ERROR: No .h5 files found - SKIPPING" | tee -a "$LOG_FILE" | tee -a "$ERROR_LOG"
            rm -f "$tarfile"
            FAILED_COUNT=$((FAILED_COUNT + 1))
            cd "$SOURCE_DIR" || exit 1
            continue
        fi
    fi
    
    # Step 4: Run Python script
    OUTPUT_MOVIE="${OUTPUT_DIR}/${BASENAME}.mp4"
    
    if python3 "$PYTHON_SCRIPT" "$EXTRACTED_DIR" --outfile "$OUTPUT_MOVIE" --fps 10 --filename "$BASENAME" >> "$LOG_FILE" 2>&1; then
        echo "  ✓ Movie created successfully: ${BASENAME}.mp4" | tee -a "$LOG_FILE"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        echo "  ERROR: Movie generation failed - CONTINUING" | tee -a "$LOG_FILE" | tee -a "$ERROR_LOG"
        FAILED_COUNT=$((FAILED_COUNT + 1))
    fi
    
    # Step 5: Cleanup
    rm -f "$tarfile"
    if [ "$EXTRACTED_DIR" != "$WORK_DIR" ] && [ -d "$EXTRACTED_DIR" ]; then
        rm -rf "$EXTRACTED_DIR" 2>> "$LOG_FILE"
    fi
    
    cd "$SOURCE_DIR" || { echo "ERROR: Cannot access $SOURCE_DIR" | tee -a "$LOG_FILE"; exit 1; }
done

# Final summary
echo "" | tee -a "$LOG_FILE"
echo "======================================" | tee -a "$LOG_FILE"
echo "Processing completed at $(date)" | tee -a "$LOG_FILE"
echo "Total files: $TOTAL_FILES" | tee -a "$LOG_FILE"
echo "Successful: $SUCCESS_COUNT" | tee -a "$LOG_FILE"
if [ $FAILED_COUNT -gt 0 ]; then
    echo "Failed: $FAILED_COUNT" | tee -a "$LOG_FILE" | tee -a "$ERROR_LOG"
fi
echo "======================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "Movies saved in: $OUTPUT_DIR" | tee -a "$LOG_FILE"

if [ $FAILED_COUNT -gt 0 ]; then
    exit 1
else
    exit 0
fi