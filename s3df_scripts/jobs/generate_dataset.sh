#!/bin/bash
# Script to generate multi-particle datasets using PhotonSim + LUCiD
# Usage: ./generate_dataset.sh -c <config_json> [-s] [-t]

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PHOTONSIM_DIR="$( cd "${SCRIPT_DIR}/../.." && pwd )"
UTILS_DIR="${SCRIPT_DIR}/../utils"
USER_PATHS="${SCRIPT_DIR}/../user_paths.sh"

# Source user paths
if [ -f "${USER_PATHS}" ]; then
    source "${USER_PATHS}"
else
    echo "Error: user_paths.sh not found at ${USER_PATHS}"
    exit 1
fi

# Default values
CONFIG_FILE=""
SUBMIT_JOBS=false
TEST_MODE=false

# Parse command line arguments
while getopts "c:sth" opt; do
    case $opt in
        c) CONFIG_FILE="$OPTARG";;
        s) SUBMIT_JOBS=true;;
        t) TEST_MODE=true;;
        h) echo "Usage: $0 -c <config_json> [-s] [-t]"
           echo "  -c: Path to JSON configuration file (required)"
           echo "  -s: Submit jobs to SLURM (default: prepare only)"
           echo "  -t: Test mode - create only one job"
           echo ""
           echo "Config file should be in JSON format with the following fields:"
           echo "  - config_number: Configuration ID number"
           echo "  - name: Configuration name"
           echo "  - description: Description of the configuration"
           echo "  - output_base_dir: Base output directory"
           echo "  - particles: Array of particle specifications"
           echo "  - n_jobs: Number of jobs to generate"
           echo "  - n_events_per_job: Number of events per job"
           echo "  - lucid_path: Path to LUCiD installation"
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

# Check for jq (JSON parser)
if ! command -v jq &> /dev/null; then
    echo "Error: jq is required but not installed. Please install jq to parse JSON files."
    exit 1
fi

echo "=== PhotonSim + LUCiD Multi-Particle Dataset Generation ==="
echo ""

# Parse JSON config
CONFIG_NUMBER=$(jq -r '.config_number' "$CONFIG_FILE")
CONFIG_NAME=$(jq -r '.name' "$CONFIG_FILE")
CONFIG_DESC=$(jq -r '.description' "$CONFIG_FILE")
OUTPUT_BASE_DIR=$(jq -r '.output_base_dir' "$CONFIG_FILE")
N_JOBS=$(jq -r '.n_jobs' "$CONFIG_FILE")
N_EVENTS=$(jq -r '.n_events_per_job' "$CONFIG_FILE")
LUCID_PATH=$(jq -r '.lucid_path' "$CONFIG_FILE")
N_PARTICLES=$(jq '.particles | length' "$CONFIG_FILE")

# Validate parsed values
if [ "$CONFIG_NUMBER" == "null" ] || [ "$CONFIG_NAME" == "null" ] || [ "$OUTPUT_BASE_DIR" == "null" ]; then
    echo "Error: Invalid JSON configuration. Required fields: config_number, name, output_base_dir"
    exit 1
fi

echo "Configuration: $CONFIG_NAME (config_$CONFIG_NUMBER)"
echo "Description: $CONFIG_DESC"
echo "Output directory: ${OUTPUT_BASE_DIR}/config_$(printf "%06d" $CONFIG_NUMBER)"
echo "Number of particles per event: $N_PARTICLES"
echo "Number of jobs: $N_JOBS"
echo "Events per job: $N_EVENTS"
echo ""

# Display particle configurations
echo "Particle configurations:"
for (( i=0; i<$N_PARTICLES; i++ )); do
    PARTICLE_TYPE=$(jq -r ".particles[$i].type" "$CONFIG_FILE")
    ENERGY_MIN=$(jq -r ".particles[$i].energy_min_MeV" "$CONFIG_FILE")
    ENERGY_MAX=$(jq -r ".particles[$i].energy_max_MeV" "$CONFIG_FILE")
    echo "  [$i] $PARTICLE_TYPE: ${ENERGY_MIN}-${ENERGY_MAX} MeV"
done
echo ""

# Create output directory structure
CONFIG_DIR="${OUTPUT_BASE_DIR}/config_$(printf "%06d" $CONFIG_NUMBER)"
echo "Creating output directory: $CONFIG_DIR"
mkdir -p "$CONFIG_DIR"

# Create README file
README_FILE="${CONFIG_DIR}/README.md"
echo "Creating README: $README_FILE"
cat > "$README_FILE" << EOF
# Multi-Particle Dataset Configuration

**Configuration Number**: $(printf "%06d" $CONFIG_NUMBER)
**Configuration Name**: $CONFIG_NAME
**Description**: $CONFIG_DESC
**Generated**: $(date)

## Configuration Details

- **Number of jobs**: $N_JOBS
- **Events per job**: $N_EVENTS
- **Total events**: $((N_JOBS * N_EVENTS))
- **Particles per event**: $N_PARTICLES

## Particle Specifications

EOF

for (( i=0; i<$N_PARTICLES; i++ )); do
    PARTICLE_TYPE=$(jq -r ".particles[$i].type" "$CONFIG_FILE")
    ENERGY_MIN=$(jq -r ".particles[$i].energy_min_MeV" "$CONFIG_FILE")
    ENERGY_MAX=$(jq -r ".particles[$i].energy_max_MeV" "$CONFIG_FILE")
    echo "- **Particle $i**: $PARTICLE_TYPE (${ENERGY_MIN}-${ENERGY_MAX} MeV, uniform distribution)" >> "$README_FILE"
done

cat >> "$README_FILE" << EOF

## Output Files

For each job (e.g., job 000001):
- PhotonSim ROOT files: \`particle_0_<type>_job_000001.root\`, \`particle_1_<type>_job_000001.root\`, etc.
- LUCiD events file: \`events_job_000001.h5\`

## Job Structure

Each job performs the following steps:
1. Run PhotonSim for each particle type (sequential)
2. Run LUCiD to process all ROOT files and generate combined events
3. Clean up intermediate files

All particles in each event share a common vertex position.
EOF

echo "README created successfully"
echo ""

# Determine number of jobs to process
if [ "$TEST_MODE" = true ]; then
    JOBS_TO_PROCESS=1
    echo "Test mode: Processing only 1 job"
else
    JOBS_TO_PROCESS=$N_JOBS
    echo "Processing $JOBS_TO_PROCESS jobs"
fi
echo ""

# Generate jobs
SUBMITTED_COUNT=0
for (( job_num=1; job_num<=$JOBS_TO_PROCESS; job_num++ )); do
    JOB_ID=$(printf "%06d" $job_num)

    echo "=== Preparing Job $job_num/$JOBS_TO_PROCESS (ID: $JOB_ID) ==="

    # Create macro files for each particle
    MACRO_FILES=()
    ROOT_FILES=()

    for (( p=0; p<$N_PARTICLES; p++ )); do
        PARTICLE_TYPE=$(jq -r ".particles[$p].type" "$CONFIG_FILE")
        ENERGY_MIN=$(jq -r ".particles[$p].energy_min_MeV" "$CONFIG_FILE")
        ENERGY_MAX=$(jq -r ".particles[$p].energy_max_MeV" "$CONFIG_FILE")

        # Create output filename
        ROOT_FILE="particle_${p}_${PARTICLE_TYPE}_job_${JOB_ID}.root"
        ROOT_FILES+=("$ROOT_FILE")

        # Create macro file
        MACRO_FILE="${CONFIG_DIR}/particle_${p}_${PARTICLE_TYPE}_job_${JOB_ID}.mac"
        MACRO_FILES+=("$MACRO_FILE")

        cat > "$MACRO_FILE" << EOFMACRO
# PhotonSim macro for ${PARTICLE_TYPE} (particle index ${p}, job ${JOB_ID})
# Configuration: $CONFIG_NAME
# Energy range: ${ENERGY_MIN}-${ENERGY_MAX} MeV (uniform distribution)

# Set output filename before initialization
/output/filename ${ROOT_FILE}

/run/initialize

# ENABLE individual photon/edep storage for event-by-event analysis
/photon/storeIndividual true
/edep/storeIndividual true

# Disable muon decay processes
/particle/select mu-
/particle/process/inactivate 1
/particle/process/inactivate 7
/particle/select mu+
/particle/process/inactivate 1

# Disable pion decay processes
/particle/select pi+
/particle/process/inactivate 1
/particle/select pi-
/particle/process/inactivate 1

# Set up primary particle with UNIFORM RANDOM energy
/gun/particle ${PARTICLE_TYPE}
/gun/randomEnergy true
/gun/energyMin ${ENERGY_MIN} MeV
/gun/energyMax ${ENERGY_MAX} MeV
/gun/position 0 0 0 m
/gun/direction 0 0 1

# Run ${N_EVENTS} events
/run/beamOn ${N_EVENTS}
EOFMACRO
    done

    # Create job execution script (generate all commands explicitly, no runtime loops)
    JOB_SCRIPT="${CONFIG_DIR}/run_job_${JOB_ID}.sh"

    cat > "$JOB_SCRIPT" << EOFJOBSCRIPT
#!/bin/bash
# Multi-particle PhotonSim + LUCiD job execution script
# Generated by generate_dataset.sh

echo "Starting Multi-Particle PhotonSim + LUCiD job"
echo "Configuration: ${CONFIG_NAME}"
echo "Job ID: ${JOB_ID}"
echo "Events per particle: ${N_EVENTS}"
echo "Number of particles: ${N_PARTICLES}"
echo ""

# Source environment
source ${UTILS_DIR}/setup_environment.sh

# Change to output directory
cd ${CONFIG_DIR}

# Step 1: Run PhotonSim for each particle
echo "=== Step 1: Running PhotonSim for each particle ==="
EOFJOBSCRIPT

    # Generate PhotonSim commands for each particle
    for (( p=0; p<$N_PARTICLES; p++ )); do
        PARTICLE_TYPE=$(jq -r ".particles[$p].type" "$CONFIG_FILE")
        cat >> "$JOB_SCRIPT" << EOFJOBSCRIPT

echo ""
echo "Running PhotonSim for particle $p (${PARTICLE_TYPE})..."
echo "Macro: ${MACRO_FILES[$p]}"
echo "Output: ${ROOT_FILES[$p]}"

${PHOTONSIM_DIR}/build/PhotonSim "${MACRO_FILES[$p]}"

if [ -f "${ROOT_FILES[$p]}" ]; then
    echo "Success! Created: ${ROOT_FILES[$p]}"
    ls -lh "${ROOT_FILES[$p]}"
else
    echo "Error: PhotonSim failed to create ${ROOT_FILES[$p]}"
    exit 1
fi
EOFJOBSCRIPT
    done

    # Generate LUCiD section
    # Build particle arguments
    LUCID_PARTICLE_ARGS=""
    for (( p=0; p<$N_PARTICLES; p++ )); do
        PARTICLE_TYPE=$(jq -r ".particles[$p].type" "$CONFIG_FILE")
        LUCID_PARTICLE_ARGS="${LUCID_PARTICLE_ARGS} --particle ${PARTICLE_TYPE}:${CONFIG_DIR}/${ROOT_FILES[$p]}"
    done

    cat >> "$JOB_SCRIPT" << EOFJOBSCRIPT

# Step 2: Set up LUCiD environment
echo ""
echo "=== Step 2: Setting up LUCiD environment ==="
export SINGULARITY_IMAGE_PATH=/sdf/group/neutrino/images/develop.sif
export JAX_PLATFORMS=cpu
function spython() {
    singularity exec -B /sdf,/fs,/sdf/scratch,/lscratch \${SINGULARITY_IMAGE_PATH} python "\$@"
}

# Create output folder for LUCiD
LUCID_OUTPUT_FOLDER="${CONFIG_DIR}/folder_job_${JOB_ID}"
mkdir -p "\${LUCID_OUTPUT_FOLDER}"
echo "Created LUCiD output folder: \${LUCID_OUTPUT_FOLDER}"

# Step 3: Run LUCiD with all particle files
echo ""
echo "=== Step 3: Running LUCiD with multi-particle input ==="
echo "LUCiD command arguments:${LUCID_PARTICLE_ARGS}"
echo "Output folder: \${LUCID_OUTPUT_FOLDER}"

spython ${LUCID_PATH}/tools/production/generate_events.py ${LUCID_PARTICLE_ARGS} --output "\${LUCID_OUTPUT_FOLDER}"

# Check if LUCiD output was created
LUCID_OUTPUT_FILE="\${LUCID_OUTPUT_FOLDER}/merged_events.h5"
if [ -f "\${LUCID_OUTPUT_FILE}" ]; then
    echo "Success! LUCiD output file created: \${LUCID_OUTPUT_FILE}"
    ls -lh "\${LUCID_OUTPUT_FILE}"
else
    echo "Error: LUCiD output file not created"
    exit 1
fi

# Step 4: Rename and move the .h5 file
echo ""
echo "=== Step 4: Organizing output files ==="
FINAL_H5_NAME="events_job_${JOB_ID}.h5"
FINAL_H5_PATH="${CONFIG_DIR}/\${FINAL_H5_NAME}"

mv "\${LUCID_OUTPUT_FILE}" "\${FINAL_H5_PATH}"
echo "Moved and renamed: \${LUCID_OUTPUT_FILE} -> \${FINAL_H5_PATH}"
ls -lh "\${FINAL_H5_PATH}"

# Remove the temporary folder
rmdir "\${LUCID_OUTPUT_FOLDER}" 2>/dev/null && echo "Removed temporary folder: \${LUCID_OUTPUT_FOLDER}" || echo "Folder not empty, keeping: \${LUCID_OUTPUT_FOLDER}"

echo ""
echo "=== Job completed successfully ==="
echo "PhotonSim outputs:"
EOFJOBSCRIPT

    # Generate output file list
    for (( p=0; p<$N_PARTICLES; p++ )); do
        echo "echo \"  - ${CONFIG_DIR}/${ROOT_FILES[$p]}\"" >> "$JOB_SCRIPT"
    done

    cat >> "$JOB_SCRIPT" << EOFJOBSCRIPT
echo "LUCiD output: ${CONFIG_DIR}/events_job_${JOB_ID}.h5"
EOFJOBSCRIPT

    chmod +x "$JOB_SCRIPT"

    # Create SLURM submission script
    SLURM_SCRIPT="${CONFIG_DIR}/submit_job_${JOB_ID}.sbatch"
    JOB_NAME="multiparticle_${CONFIG_NAME}_$(date +%Y%m%d_%H%M%S)_${JOB_ID}"

    cat > "$SLURM_SCRIPT" << EOFSLURM
#!/bin/bash
#SBATCH --partition=${SLURM_PARTITION}
#SBATCH --account=${SLURM_ACCOUNT}
#
#SBATCH --job-name=${JOB_NAME}
#SBATCH --output=${CONFIG_DIR}/job_${JOB_ID}-%j.out
#SBATCH --error=${CONFIG_DIR}/job_${JOB_ID}-%j.err
#
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=${DEFAULT_CPUS}
#SBATCH --mem-per-cpu=${DEFAULT_MEMORY}
#
#SBATCH --time=${DEFAULT_TIME}

echo "SLURM Job ID: \${SLURM_JOB_ID}"
echo "Job started at: \$(date)"
echo "Running on node: \$(hostname)"
echo "Working directory: \$(pwd)"

# Execute the job script
${JOB_SCRIPT}

echo "Job ended at: \$(date)"
EOFSLURM

    chmod +x "$SLURM_SCRIPT"

    echo "Job $JOB_ID prepared:"
    echo "  - Macro files: ${#MACRO_FILES[@]} created"
    echo "  - Job script: $JOB_SCRIPT"
    echo "  - SLURM script: $SLURM_SCRIPT"

    # Submit job if requested
    if [ "$SUBMIT_JOBS" = true ]; then
        echo "  - Submitting to SLURM..."
        sbatch "$SLURM_SCRIPT"
        SUBMITTED_COUNT=$((SUBMITTED_COUNT + 1))
    fi
    echo ""
done

# Final summary
echo "=== Dataset Generation Complete ==="
echo "Configuration: $CONFIG_NAME (config_$(printf "%06d" $CONFIG_NUMBER))"
echo "Output directory: $CONFIG_DIR"
echo "Jobs prepared: $JOBS_TO_PROCESS"
if [ "$SUBMIT_JOBS" = true ]; then
    echo "Jobs submitted to SLURM: $SUBMITTED_COUNT"
else
    echo "Jobs not submitted (use -s flag to submit)"
fi
echo ""
echo "To submit all jobs manually:"
echo "  cd $CONFIG_DIR && for f in submit_job_*.sbatch; do sbatch \$f; done"
echo ""
echo "To test a single job locally:"
echo "  $CONFIG_DIR/run_job_$(printf "%06d" 1).sh"
echo ""
