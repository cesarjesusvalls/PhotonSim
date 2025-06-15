#!/bin/bash
# Script to submit multiple PhotonSim jobs in batch
# Usage: ./submit_photonsim_batch.sh -c <config_file>

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Default config file
CONFIG_FILE=""
SUBMIT_JOBS=false
TEST_MODE=false

# Parse command line arguments
while getopts "c:sth" opt; do
    case $opt in
        c) CONFIG_FILE="$OPTARG";;
        s) SUBMIT_JOBS=true;;
        t) TEST_MODE=true;;
        h) echo "Usage: $0 -c <config_file> [-s] [-t]"
           echo "  -c: Configuration file (required)"
           echo "  -s: Submit jobs to SLURM (default: prepare only)"
           echo "  -t: Test mode - create only one job"
           echo ""
           echo "Config file format (one job per line):"
           echo "  particle nevents energy output_dir [filename]"
           echo ""
           echo "Example config file:"
           echo "  mu- 1000 500 /path/to/your/output"
           echo "  mu- 1000 1000 /path/to/your/output"
           echo "  mu- 1000 2000 /path/to/your/output output_2GeV.root"
           exit 0;;
        \?) echo "Invalid option -$OPTARG" >&2; exit 1;;
    esac
done

# Check required parameters
if [ -z "$CONFIG_FILE" ]; then
    echo "Error: Configuration file is required (-c option)"
    exit 1
fi

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Configuration file not found: $CONFIG_FILE"
    exit 1
fi

# Count total jobs
TOTAL_JOBS=$(grep -v '^#' "$CONFIG_FILE" | grep -v '^[[:space:]]*$' | wc -l)
echo "Found $TOTAL_JOBS job configurations in $CONFIG_FILE"

# Process each line in the config file
JOB_COUNT=0
SUBMITTED_COUNT=0

while IFS=' ' read -r particle nevents energy output_dir filename || [ -n "$particle" ]; do
    # Skip comments and empty lines
    [[ "$particle" =~ ^#.*$ ]] && continue
    [[ -z "$particle" ]] && continue
    
    JOB_COUNT=$((JOB_COUNT + 1))
    
    # Set default filename if not provided
    if [ -z "$filename" ]; then
        filename="output.root"
    fi
    
    echo ""
    echo "=== Processing job $JOB_COUNT/$TOTAL_JOBS ==="
    echo "Particle: $particle"
    echo "Events: $nevents"
    echo "Energy: $energy MeV"
    echo "Output dir: $output_dir"
    echo "Filename: $filename"
    
    # Prepare the job
    CMD="${SCRIPT_DIR}/submit_photonsim_job.sh -p $particle -n $nevents -e $energy -o $output_dir -f $filename"
    echo "Executing: $CMD"
    $CMD
    
    if [ $? -eq 0 ]; then
        # Get the SLURM script path
        ENERGY_INT=$(printf "%.0f" $energy)
        SLURM_SCRIPT="${output_dir}/${particle}/${ENERGY_INT}MeV/submit_job.sbatch"
        
        if [ "$SUBMIT_JOBS" = true ]; then
            echo "Submitting job to SLURM..."
            sbatch "$SLURM_SCRIPT"
            SUBMITTED_COUNT=$((SUBMITTED_COUNT + 1))
        else
            echo "Job prepared but not submitted (use -s flag to submit)"
        fi
    else
        echo "Error: Failed to prepare job"
    fi
    
    # In test mode, only process first job
    if [ "$TEST_MODE" = true ]; then
        echo ""
        echo "Test mode: Only processed first job"
        break
    fi
    
done < "$CONFIG_FILE"

# Summary
echo ""
echo "=== Batch processing complete ==="
echo "Total jobs processed: $JOB_COUNT"
if [ "$SUBMIT_JOBS" = true ]; then
    echo "Jobs submitted to SLURM: $SUBMITTED_COUNT"
else
    echo "Jobs prepared but not submitted (use -s flag to submit)"
fi