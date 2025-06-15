#!/bin/bash
# Script to clean up PhotonSim job outputs

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
OUTPUT_DIR=""
CLEAN_LOGS=false
CLEAN_MACROS=false
CLEAN_SCRIPTS=false
DRY_RUN=true

# Parse command line arguments
while getopts "o:lmsah" opt; do
    case $opt in
        o) OUTPUT_DIR="$OPTARG";;
        l) CLEAN_LOGS=true;;
        m) CLEAN_MACROS=true;;
        s) CLEAN_SCRIPTS=true;;
        a) CLEAN_LOGS=true; CLEAN_MACROS=true; CLEAN_SCRIPTS=true;;
        h) echo "Usage: $0 -o <output_dir> [-l] [-m] [-s] [-a]"
           echo "  -o: Output directory to clean (required)"
           echo "  -l: Clean log files (job-*.out, job-*.err)"
           echo "  -m: Clean macro files (*.mac)"
           echo "  -s: Clean script files (*.sh, *.sbatch)"
           echo "  -a: Clean all (logs, macros, and scripts)"
           echo ""
           echo "By default, this runs in dry-run mode. Files are not actually deleted."
           echo "To actually delete files, edit the script and set DRY_RUN=false"
           exit 0;;
        \?) echo "Invalid option -$OPTARG" >&2; exit 1;;
    esac
done

# Check required parameters
if [ -z "$OUTPUT_DIR" ]; then
    echo "Error: Output directory is required (-o option)"
    exit 1
fi

if [ ! -d "$OUTPUT_DIR" ]; then
    echo "Error: Output directory not found: $OUTPUT_DIR"
    exit 1
fi

# Safety check
if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}Running in DRY RUN mode - no files will be deleted${NC}"
    echo "To actually delete files, edit the script and set DRY_RUN=false"
    echo ""
fi

# Function to remove files
remove_files() {
    local pattern=$1
    local description=$2
    
    echo -e "${YELLOW}Searching for $description files...${NC}"
    FILES=$(find "$OUTPUT_DIR" -name "$pattern" -type f 2>/dev/null)
    COUNT=$(echo "$FILES" | grep -c . || echo 0)
    
    if [ $COUNT -eq 0 ]; then
        echo "  No $description files found"
        return
    fi
    
    echo "  Found $COUNT $description files"
    
    if [ "$DRY_RUN" = true ]; then
        echo "  Would delete:"
        echo "$FILES" | head -10 | sed 's/^/    /'
        if [ $COUNT -gt 10 ]; then
            echo "    ... and $((COUNT-10)) more"
        fi
    else
        echo -e "  ${RED}Deleting $COUNT files...${NC}"
        echo "$FILES" | xargs rm -f
        echo -e "  ${GREEN}Done${NC}"
    fi
    echo ""
}

# Show directory structure
echo -e "${GREEN}=== PhotonSim Job Cleanup ===${NC}"
echo "Target directory: $OUTPUT_DIR"
echo ""

# Show current status
echo -e "${YELLOW}Current directory contents:${NC}"
TOTAL_ROOT=$(find "$OUTPUT_DIR" -name "*.root" -type f 2>/dev/null | wc -l)
TOTAL_LOGS=$(find "$OUTPUT_DIR" -name "job-*.out" -o -name "job-*.err" -type f 2>/dev/null | wc -l)
TOTAL_MACS=$(find "$OUTPUT_DIR" -name "*.mac" -type f 2>/dev/null | wc -l)
TOTAL_SCRIPTS=$(find "$OUTPUT_DIR" -name "*.sh" -o -name "*.sbatch" -type f 2>/dev/null | wc -l)

echo "  ROOT files: $TOTAL_ROOT (will be preserved)"
echo "  Log files: $TOTAL_LOGS"
echo "  Macro files: $TOTAL_MACS"
echo "  Script files: $TOTAL_SCRIPTS"
echo ""

# Clean files based on options
if [ "$CLEAN_LOGS" = true ]; then
    remove_files "job-*.out" "job output log"
    remove_files "job-*.err" "job error log"
fi

if [ "$CLEAN_MACROS" = true ]; then
    remove_files "*.mac" "macro"
fi

if [ "$CLEAN_SCRIPTS" = true ]; then
    remove_files "*.sh" "shell script"
    remove_files "*.sbatch" "SLURM batch script"
fi

# Summary
if [ "$DRY_RUN" = false ]; then
    echo -e "${GREEN}Cleanup complete!${NC}"
    echo ""
    echo "Remaining files:"
    TOTAL_ROOT=$(find "$OUTPUT_DIR" -name "*.root" -type f 2>/dev/null | wc -l)
    TOTAL_LOGS=$(find "$OUTPUT_DIR" -name "job-*.out" -o -name "job-*.err" -type f 2>/dev/null | wc -l)
    TOTAL_MACS=$(find "$OUTPUT_DIR" -name "*.mac" -type f 2>/dev/null | wc -l)
    TOTAL_SCRIPTS=$(find "$OUTPUT_DIR" -name "*.sh" -o -name "*.sbatch" -type f 2>/dev/null | wc -l)
    
    echo "  ROOT files: $TOTAL_ROOT"
    echo "  Log files: $TOTAL_LOGS"
    echo "  Macro files: $TOTAL_MACS"
    echo "  Script files: $TOTAL_SCRIPTS"
fi