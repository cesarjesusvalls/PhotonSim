#!/bin/bash
# Script to submit multiple JSON configurations
# Usage: ./submit_all_configs.sh [-p pattern] [-s] [-t] [-d]

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CONFIG_DIR="${SCRIPT_DIR}/../../macros/data_production_config"

# Default values
PATTERN="*.json"
SUBMIT_JOBS=false
TEST_MODE=false
DRY_RUN=false

# Parse command line arguments
while getopts "p:stdh" opt; do
    case $opt in
        p) PATTERN="$OPTARG";;
        s) SUBMIT_JOBS=true;;
        t) TEST_MODE=true;;
        d) DRY_RUN=true;;
        h) echo "Usage: $0 [-p pattern] [-s] [-t] [-d]"
           echo "  -p: Pattern to match config files (default: *.json)"
           echo "  -s: Submit jobs to SLURM (default: prepare only)"
           echo "  -t: Test mode - create only one job per config"
           echo "  -d: Dry run - show what would be submitted without doing it"
           echo ""
           echo "Examples:"
           echo "  # Dry run to see all configs"
           echo "  $0 -d"
           echo ""
           echo "  # Submit all uniform energy configs"
           echo "  $0 -p 'uniform*.json' -s"
           echo ""
           echo "  # Test all monoenergetic configs"
           echo "  $0 -p 'monoenergetic*.json' -t"
           echo ""
           echo "  # Submit all configs (prepare and submit)"
           echo "  $0 -s"
           exit 0;;
        \?) echo "Invalid option -$OPTARG" >&2; exit 1;;
    esac
done

# Check if config directory exists
if [ ! -d "$CONFIG_DIR" ]; then
    echo "Error: Config directory not found: $CONFIG_DIR"
    exit 1
fi

# Find matching config files
mapfile -t CONFIG_FILES < <(find "$CONFIG_DIR" -maxdepth 1 -name "$PATTERN" -type f | sort)

if [ ${#CONFIG_FILES[@]} -eq 0 ]; then
    echo "No configuration files found matching pattern: $PATTERN"
    echo "Looking in: $CONFIG_DIR"
    exit 1
fi

echo "=== Submit All Configurations ==="
echo "Config directory: $CONFIG_DIR"
echo "Pattern: $PATTERN"
echo "Found ${#CONFIG_FILES[@]} configuration file(s)"
echo ""

# Show what will be processed
echo "Configurations to process:"
for config_file in "${CONFIG_FILES[@]}"; do
    config_name=$(basename "$config_file")
    config_desc=$(jq -r '.name' "$config_file" 2>/dev/null || echo "N/A")
    echo "  - $config_name ($config_desc)"
done
echo ""

# Build command arguments
CMD_ARGS=""
if [ "$SUBMIT_JOBS" = true ]; then
    CMD_ARGS="$CMD_ARGS -s"
    echo "Mode: Generate and SUBMIT jobs to SLURM"
else
    echo "Mode: Generate jobs only (no submission)"
fi

if [ "$TEST_MODE" = true ]; then
    CMD_ARGS="$CMD_ARGS -t"
    echo "Test mode: Only 1 job per configuration"
fi
echo ""

if [ "$DRY_RUN" = true ]; then
    echo "DRY RUN - Would execute the following:"
    for config_file in "${CONFIG_FILES[@]}"; do
        echo "  ${SCRIPT_DIR}/generate_jobs.sh -c $config_file $CMD_ARGS"
    done
    echo ""
    echo "Run without -d flag to actually execute"
    exit 0
fi

# Confirm before proceeding if submitting
if [ "$SUBMIT_JOBS" = true ]; then
    echo "WARNING: This will submit jobs to SLURM!"
    read -p "Continue? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 0
    fi
    echo ""
fi

# Process each config file
SUCCESS_COUNT=0
FAIL_COUNT=0

for config_file in "${CONFIG_FILES[@]}"; do
    config_name=$(basename "$config_file")

    echo "=========================================="
    echo "Processing: $config_name"
    echo "=========================================="

    # Execute generate_jobs.sh
    if ${SCRIPT_DIR}/generate_jobs.sh -c "$config_file" $CMD_ARGS; then
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        echo "✓ Success: $config_name"
    else
        FAIL_COUNT=$((FAIL_COUNT + 1))
        echo "✗ Failed: $config_name"
    fi
    echo ""
done

# Summary
echo "=========================================="
echo "=== Summary ==="
echo "=========================================="
echo "Total configurations: ${#CONFIG_FILES[@]}"
echo "Successful: $SUCCESS_COUNT"
echo "Failed: $FAIL_COUNT"
echo ""

if [ "$SUBMIT_JOBS" = true ]; then
    echo "Jobs have been submitted to SLURM"
    echo "Monitor with: ${SCRIPT_DIR}/monitor_jobs.sh -w"
else
    echo "Jobs have been prepared but not submitted"
    echo "To submit individual configs, run:"
    echo "  ${SCRIPT_DIR}/generate_jobs.sh -c <config_file> -s"
fi
echo ""
