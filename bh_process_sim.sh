#!/bin/bash

# Black Hole Simulation Data Processing Script
# Processes .tar.gz files containing GRMHD .h5 snapshots
# Extracts, creates movies, and cleans up automatically
# Enhanced with detailed logging and error recovery

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

# Function for detailed logging
log_info() {
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE" | tee -a "$ERROR_LOG"
}

log_success() {
    echo "[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Check if Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    log_error "Python script not found at $PYTHON_SCRIPT"
    exit 1
fi

log_info "Python script found: $PYTHON_SCRIPT"

# Get list of all tar.gz files in source directory
cd "$SOURCE_DIR" || { log_error "Cannot access $SOURCE_DIR"; exit 1; }
TOTAL_FILES=$(ls -1 *.tar.gz 2>/dev/null | wc -l)
CURRENT=0
SUCCESS_COUNT=0
FAILED_COUNT=0

if [ "$TOTAL_FILES" -eq 0 ]; then
    log_info "No .tar.gz files found in $SOURCE_DIR"
    exit 0
fi

log_info "Found $TOTAL_FILES .tar.gz files to process"
echo "" >> "$LOG_FILE"

# Process each .tar.gz file one at a time
for tarfile in *.tar.gz; do
    # Skip if no files found
    [ -e "$tarfile" ] || continue
    
    CURRENT=$((CURRENT + 1))
    
    echo "" >> "$LOG_FILE"
    echo "==========================================" | tee -a "$LOG_FILE"
    log_info "[$CURRENT/$TOTAL_FILES] Processing: $tarfile"
    echo "==========================================" >> "$LOG_FILE"
    
    # Extract base name (without .tar.gz extension)
    BASENAME=$(basename "$tarfile" .tar.gz)
    
    # Use a flag to track if this file succeeds
    FILE_SUCCESS=true
    
    # Step 1: Copy file to working directory
    log_info "  [1/6] Copying file to working directory..."
    if cp "${SOURCE_DIR}/${tarfile}" "${WORK_DIR}/" 2>> "$LOG_FILE"; then
        log_success "  Copy complete"
    else
        log_error "  Failed to copy $tarfile - SKIPPING"
        FAILED_COUNT=$((FAILED_COUNT + 1))
        continue
    fi
    
    # Change to working directory
    cd "$WORK_DIR" || { log_error "Cannot access $WORK_DIR"; exit 1; }
    
    # Step 2: Extract the tar.gz file
    log_info "  [2/6] Extracting tar.gz file..."
    if tar -xzf "$tarfile" -C "${WORK_DIR}" 2>> "$LOG_FILE"; then
        log_success "  Extraction complete"
    else
        log_error "  Extraction failed for $tarfile - CLEANING UP AND SKIPPING"
        rm -f "$tarfile"
        FAILED_COUNT=$((FAILED_COUNT + 1))
        FILE_SUCCESS=false
        cd "$SOURCE_DIR" || exit 1
        continue
    fi
    
    # Step 3: Find the extracted directory
    log_info "  [3/6] Locating extracted data..."
    EXTRACTED_DIR=$(find "${WORK_DIR}" -maxdepth 1 -type d ! -path "${WORK_DIR}" ! -path "${WORK_DIR}/simulation_movies" | head -1)
    
    if [ -z "$EXTRACTED_DIR" ]; then
        if ls "${WORK_DIR}"/*.h5 1> /dev/null 2>&1; then
            EXTRACTED_DIR="${WORK_DIR}"
            log_info "  Found .h5 files in work directory"
        else
            log_error "  No extracted directory or .h5 files found for $tarfile - CLEANING UP AND SKIPPING"
            rm -f "$tarfile"
            FAILED_COUNT=$((FAILED_COUNT + 1))
            FILE_SUCCESS=false
            cd "$SOURCE_DIR" || exit 1
            continue
        fi
    else
        log_success "  Found data directory: $EXTRACTED_DIR"
    fi
    
    # Step 4: Run Python script to generate movie
    log_info "  [4/6] Running Python script to generate movie..."
    OUTPUT_MOVIE="${OUTPUT_DIR}/${BASENAME}.mp4"
    
    if python3 "$PYTHON_SCRIPT" "$EXTRACTED_DIR" --outfile "$OUTPUT_MOVIE" --fps 10 --filename "$BASENAME" >> "$LOG_FILE" 2>&1; then
        log_success "  Video generation successful: ${BASENAME}.mp4"
    else
        log_error "  Python script failed for $tarfile - WILL CLEAN UP AND CONTINUE"
        FAILED_COUNT=$((FAILED_COUNT + 1))
        FILE_SUCCESS=false
    fi
    
    # Step 5: Remove the copied tar.gz file
    log_info "  [5/6] Removing tar.gz file..."
    rm -f "$tarfile"
    log_success "  Removed tar.gz file"
    
    # Step 6: Clean up extracted directory
    log_info "  [6/6] Cleaning up extracted directory..."
    if [ "$EXTRACTED_DIR" != "$WORK_DIR" ] && [ -d "$EXTRACTED_DIR" ]; then
        if rm -rf "$EXTRACTED_DIR" 2>> "$LOG_FILE"; then
            log_success "  Removed directory: $(basename $EXTRACTED_DIR)"
        else
            log_error "  Failed to remove directory: $(basename $EXTRACTED_DIR)"
        fi
    fi
    log_success "  Cleanup complete"
    
    # Update success counter
    if [ "$FILE_SUCCESS" = true ]; then
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    fi
    
    log_info "  [$CURRENT/$TOTAL_FILES] Finished processing $tarfile"
    echo "==========================================" >> "$LOG_FILE"
    
    # Go back to source directory for next iteration
    cd "$SOURCE_DIR" || { log_error "Cannot access $SOURCE_DIR"; exit 1; }
done

echo "" | tee -a "$LOG_FILE"
echo "======================================" | tee -a "$LOG_FILE"
log_info "Processing completed at $(date)"
log_info "Total files processed: $TOTAL_FILES"
log_success "Successful: $SUCCESS_COUNT"
if [ $FAILED_COUNT -gt 0 ]; then
    log_error "Failed: $FAILED_COUNT"
fi
echo "======================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "🎉 All processing complete!" | tee -a "$LOG_FILE"
echo "📁 Movies saved in: $OUTPUT_DIR" | tee -a "$LOG_FILE"
echo "📋 Main log: $LOG_FILE" | tee -a "$LOG_FILE"
echo "📋 Error log: $ERROR_LOG" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Exit with error code if any files failed
if [ $FAILED_COUNT -gt 0 ]; then
    exit 1
else
    exit 0
fi