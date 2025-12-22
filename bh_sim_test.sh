#!/bin/bash

# TEST VERSION - Process only ONE file for testing
# Black Hole Simulation Data Processing Script

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

# Get list of all tar.gz files and select the FIRST one
cd "$SOURCE_DIR" || { echo "Error: Cannot access $SOURCE_DIR" | tee -a "$LOG_FILE"; exit 1; }

# Get the first .tar.gz file
tarfile=$(ls -1 *.tar.gz 2>/dev/null | head -1)

if [ -z "$tarfile" ]; then
    echo "No .tar.gz files found in $SOURCE_DIR" | tee -a "$LOG_FILE"
    exit 0
fi

echo "" | tee -a "$LOG_FILE"
echo "==========================================" | tee -a "$LOG_FILE"
echo "TEST: Processing: $tarfile" | tee -a "$LOG_FILE"
echo "==========================================" | tee -a "$LOG_FILE"

# Extract base name (without .tar.gz extension)
BASENAME=$(basename "$tarfile" .tar.gz)

# Step 1: Copy file to working directory
echo "  [1/6] Copying file to working directory..." | tee -a "$LOG_FILE"
cp "${SOURCE_DIR}/${tarfile}" "${WORK_DIR}/" 2>> "$LOG_FILE"

if [ $? -ne 0 ]; then
    echo "  ERROR: Failed to copy file" | tee -a "$LOG_FILE"
    exit 1
fi
echo "  ✓ Copy complete" | tee -a "$LOG_FILE"

# Change to working directory
cd "$WORK_DIR" || { echo "Error: Cannot access $WORK_DIR" | tee -a "$LOG_FILE"; exit 1; }

# Step 2: Extract the tar.gz file directly into working directory
echo "  [2/6] Extracting tar.gz file..." | tee -a "$LOG_FILE"
tar -xzf "$tarfile" -C "${WORK_DIR}" 2>> "$LOG_FILE"

if [ $? -ne 0 ]; then
    echo "  ERROR: Extraction failed" | tee -a "$LOG_FILE"
    rm -f "$tarfile"
    exit 1
fi
echo "  ✓ Extraction complete" | tee -a "$LOG_FILE"

# Step 3: Find the extracted directory (should contain .h5 files)
echo "  [3/6] Locating extracted data..." | tee -a "$LOG_FILE"
EXTRACTED_DIR=$(find "${WORK_DIR}" -maxdepth 1 -type d ! -path "${WORK_DIR}" ! -path "${WORK_DIR}/simulation_movies" | head -1)

if [ -z "$EXTRACTED_DIR" ]; then
    if ls "${WORK_DIR}"/*.h5 1> /dev/null 2>&1; then
        EXTRACTED_DIR="${WORK_DIR}"
    else
        echo "  ERROR: No extracted directory or .h5 files found" | tee -a "$LOG_FILE"
        rm -f "$tarfile"
        exit 1
    fi
fi

echo "  ✓ Found data directory: $EXTRACTED_DIR" | tee -a "$LOG_FILE"

# Step 4: Run Python script to generate movie
echo "  [4/6] Running Python script to generate movie..." | tee -a "$LOG_FILE"
OUTPUT_MOVIE="${OUTPUT_DIR}/${BASENAME}.mp4"

python3 "$PYTHON_SCRIPT" "$EXTRACTED_DIR" --outfile "$OUTPUT_MOVIE" --fps 10 --filename "$BASENAME" >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then
    echo "  ✓ Video generation successful: ${BASENAME}.mp4" | tee -a "$LOG_FILE"
else
    echo "  ERROR: Python script failed" | tee -a "$LOG_FILE"
fi

# Step 5: Remove the copied tar.gz file
echo "  [5/6] Removing tar.gz file..." | tee -a "$LOG_FILE"
rm -f "$tarfile"
echo "  ✓ Removed tar.gz file" | tee -a "$LOG_FILE"

# Step 6: Clean up extracted directory only
echo "  [6/6] Cleaning up extracted directory..." | tee -a "$LOG_FILE"
if [ "$EXTRACTED_DIR" != "$WORK_DIR" ] && [ -d "$EXTRACTED_DIR" ]; then
    rm -rf "$EXTRACTED_DIR" 2>> "$LOG_FILE"
    echo "  ✓ Removed directory: $(basename $EXTRACTED_DIR)" | tee -a "$LOG_FILE"
fi
echo "  ✓ Cleanup complete" | tee -a "$LOG_FILE"

echo "==========================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "======================================" >> "$LOG_FILE"
echo "TEST completed at $(date)" >> "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "🎉 Test processing complete!" | tee -a "$LOG_FILE"
echo "📁 Movie saved in: $OUTPUT_DIR" | tee -a "$LOG_FILE"
echo "📋 Check $LOG_FILE for detailed logs." | tee -a "$LOG_FILE"