#!/bin/bash
# Unified script to generate PhotonSim jobs from JSON configuration
# Usage: ./generate_jobs.sh -c <config_json> [-s] [-t]

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PHOTONSIM_DIR="$( cd "${SCRIPT_DIR}/../.." && pwd )"
UTILS_DIR="${SCRIPT_DIR}/../utils"
USER_PATHS="${SCRIPT_DIR}/../user_paths.sh"
BASE_CONFIG="${SCRIPT_DIR}/../base_config.sh"

# Source user paths
if [ -f "${USER_PATHS}" ]; then
    source "${USER_PATHS}"
else
    echo "Error: user_paths.sh not found at ${USER_PATHS}"
    exit 1
fi

# Source base config
if [ -f "${BASE_CONFIG}" ]; then
    source "${BASE_CONFIG}"
else
    echo "Error: base_config.sh not found at ${BASE_CONFIG}"
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
           echo "See macros/data_production_config/ for example configurations"
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

echo "=== PhotonSim Job Generation ==="
echo ""

# Parse JSON config
CONFIG_NUMBER=$(jq -r '.config_number' "$CONFIG_FILE")
USE_CONFIG_NUMBER=$(jq -r '.use_config_number' "$CONFIG_FILE")
CONFIG_NAME=$(jq -r '.name' "$CONFIG_FILE")
CONFIG_DESC=$(jq -r '.description' "$CONFIG_FILE")
MATERIAL=$(jq -r '.material' "$CONFIG_FILE")
OUTPUT_PATH=$(jq -r '.output_path' "$CONFIG_FILE")
ENERGY_DIST=$(jq -r '.energy_distribution' "$CONFIG_FILE")
STORE_INDIVIDUAL=$(jq -r '.store_individual_photons' "$CONFIG_FILE")
RUN_LUCID=$(jq -r '.run_lucid' "$CONFIG_FILE")
N_JOBS=$(jq -r '.n_jobs' "$CONFIG_FILE")
N_EVENTS=$(jq -r '.n_events_per_job' "$CONFIG_FILE")
N_PARTICLES=$(jq '.particles | length' "$CONFIG_FILE")

# Handle backward compatibility - check for old output_base_dir field
OLD_OUTPUT_BASE_DIR=$(jq -r '.output_base_dir' "$CONFIG_FILE")
if [ "$OLD_OUTPUT_BASE_DIR" != "null" ]; then
    echo "Warning: 'output_base_dir' field is deprecated. Please use 'material' and 'output_path' instead."
    echo "Using old format for now..."
    OUTPUT_BASE_DIR="$OLD_OUTPUT_BASE_DIR"
else
    # Build output directory from new fields
    OUTPUT_BASE_DIR="${OUTPUT_BASE_PATH}/${MATERIAL}/${OUTPUT_PATH}"
fi

# Validate parsed values
if [ "$CONFIG_NAME" == "null" ]; then
    echo "Error: Invalid JSON configuration. Required field: name"
    exit 1
fi

if [ "$MATERIAL" == "null" ] && [ "$OLD_OUTPUT_BASE_DIR" == "null" ]; then
    echo "Error: Invalid JSON configuration. Required field: material (or use deprecated output_base_dir)"
    exit 1
fi

if [ "$OUTPUT_PATH" == "null" ] && [ "$OLD_OUTPUT_BASE_DIR" == "null" ]; then
    echo "Error: Invalid JSON configuration. Required field: output_path (or use deprecated output_base_dir)"
    exit 1
fi

# Default use_config_number to false if not specified
if [ "$USE_CONFIG_NUMBER" == "null" ]; then
    USE_CONFIG_NUMBER="false"
fi

if [ "$ENERGY_DIST" != "monoenergetic" ] && [ "$ENERGY_DIST" != "uniform" ]; then
    echo "Error: energy_distribution must be 'monoenergetic' or 'uniform'"
    exit 1
fi

# Get LUCiD path if needed
if [ "$RUN_LUCID" == "true" ]; then
    # Check if lucid_path is specified in JSON (backward compatibility)
    JSON_LUCID_PATH=$(jq -r '.lucid_path' "$CONFIG_FILE")
    if [ "$JSON_LUCID_PATH" != "null" ]; then
        echo "Warning: 'lucid_path' in JSON is deprecated. Using value from base_config.sh instead."
        echo "Please remove 'lucid_path' from your JSON config."
        # Still use the base_config.sh value for consistency
    fi

    # Use LUCID_PATH from base_config.sh (sourced earlier)
    if [ -z "$LUCID_PATH" ]; then
        echo "Error: LUCID_PATH not set. Check base_config.sh"
        exit 1
    fi
fi

echo "Configuration: $CONFIG_NAME (config_$CONFIG_NUMBER)"
echo "Description: $CONFIG_DESC"
echo "Energy distribution: $ENERGY_DIST"
echo "Store individual photons: $STORE_INDIVIDUAL"
echo "Run LUCiD: $RUN_LUCID"
echo "Number of particles per event: $N_PARTICLES"
echo "Number of jobs: $N_JOBS"
echo "Events per job: $N_EVENTS"
echo ""

# Function to create PhotonSim macro
create_macro() {
    local macro_file="$1"
    local particle_type="$2"
    local output_file="$3"
    local energy_mode="$4"  # "fixed" or "uniform"
    local energy_value="$5"  # Single value for fixed, or "min" for uniform
    local energy_max="$6"    # Only used for uniform
    local nevents="$7"
    local store_individual="$8"

    cat > "$macro_file" << EOFMACRO
# PhotonSim macro
# Configuration: $CONFIG_NAME
# Material: $MATERIAL
# Particle: $particle_type
EOFMACRO

    if [ "$energy_mode" == "fixed" ]; then
        echo "# Energy: ${energy_value} MeV (fixed)" >> "$macro_file"
    else
        echo "# Energy: ${energy_value}-${energy_max} MeV (uniform distribution)" >> "$macro_file"
    fi

    cat >> "$macro_file" << EOFMACRO

# Set output filename before initialization
/output/filename ${output_file}

# TODO: Add PhotonSim macro command to set detector material when available
# For now, material is: $MATERIAL

/run/initialize

EOFMACRO

    if [ "$store_individual" == "true" ]; then
        cat >> "$macro_file" << EOFMACRO
# ENABLE individual photon/edep storage for event-by-event analysis
/photon/storeIndividual true
/edep/storeIndividual true
EOFMACRO
    else
        cat >> "$macro_file" << EOFMACRO
# DISABLE individual photon/edep storage to save space
/photon/storeIndividual false
/edep/storeIndividual false
EOFMACRO
    fi

    cat >> "$macro_file" << EOFMACRO

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

# Set up primary particle
/gun/particle ${particle_type}
EOFMACRO

    if [ "$energy_mode" == "fixed" ]; then
        cat >> "$macro_file" << EOFMACRO
/gun/randomEnergy false
/gun/energy ${energy_value} MeV
EOFMACRO
    else
        cat >> "$macro_file" << EOFMACRO
/gun/randomEnergy true
/gun/energyMin ${energy_value} MeV
/gun/energyMax ${energy_max} MeV
EOFMACRO
    fi

    cat >> "$macro_file" << EOFMACRO
/gun/position 0 0 0 m
/gun/direction 0 0 1

# Run ${nevents} events
/run/beamOn ${nevents}
EOFMACRO
}

# Function to handle single-particle monoenergetic jobs
handle_monoenergetic_single_particle() {
    local particle_type=$(jq -r '.particles[0].type' "$CONFIG_FILE")

    # Check if it's a single energy or energy scan
    local single_energy=$(jq -r '.energy_MeV' "$CONFIG_FILE")
    local has_scan=$(jq -r '.energy_scan' "$CONFIG_FILE")

    if [ "$single_energy" != "null" ]; then
        # Single energy
        ENERGIES=("$single_energy")
    elif [ "$has_scan" != "null" ]; then
        # Energy scan
        local start=$(jq -r '.energy_scan.start_MeV' "$CONFIG_FILE")
        local stop=$(jq -r '.energy_scan.stop_MeV' "$CONFIG_FILE")
        local step=$(jq -r '.energy_scan.step_MeV' "$CONFIG_FILE")

        ENERGIES=()
        for (( e=$start; e<=$stop; e+=$step )); do
            ENERGIES+=("$e")
        done
    else
        echo "Error: For monoenergetic mode, either energy_MeV or energy_scan must be specified"
        exit 1
    fi

    echo "Particle: $particle_type"
    echo "Energies: ${ENERGIES[@]}"
    echo ""

    local submitted_count=0
    local jobs_to_process=$N_JOBS
    if [ "$TEST_MODE" = true ]; then
        jobs_to_process=1
        echo "Test mode: Processing only 1 job per energy"
    fi

    # For each energy
    for energy in "${ENERGIES[@]}"; do
        energy_int=$(printf "%.0f" $energy)
        OUTPUT_DIR="${OUTPUT_BASE_DIR}/${particle_type}/${energy_int}MeV"

        echo "=== Energy: ${energy_int} MeV ==="
        echo "Output directory: $OUTPUT_DIR"
        mkdir -p "$OUTPUT_DIR"

        # Generate jobs for this energy
        for (( job_num=1; job_num<=$jobs_to_process; job_num++ )); do
            if [ $jobs_to_process -eq 1 ]; then
                OUTPUT_FILE="output.root"
                JOB_SUFFIX=""
            else
                JOB_ID=$(printf "%03d" $job_num)
                OUTPUT_FILE="output_job${JOB_ID}.root"
                JOB_SUFFIX="_job${JOB_ID}"
            fi

            # Create macro
            MACRO_FILE="${OUTPUT_DIR}/run_${particle_type}_${energy_int}MeV${JOB_SUFFIX}.mac"
            create_macro "$MACRO_FILE" "$particle_type" "$OUTPUT_FILE" "fixed" "$energy" "" "$N_EVENTS" "$STORE_INDIVIDUAL"

            # Create job script
            JOB_SCRIPT="${OUTPUT_DIR}/run_photonsim${JOB_SUFFIX}.sh"
            cat > "$JOB_SCRIPT" << EOFJOBSCRIPT
#!/bin/bash
# PhotonSim job execution script
# Generated by generate_jobs.sh

echo "Starting PhotonSim job"
echo "Configuration: ${CONFIG_NAME}"
echo "Particle: ${particle_type}"
echo "Energy: ${energy_int} MeV"
echo "Events: ${N_EVENTS}"
echo "Output: ${OUTPUT_FILE}"
echo ""

# Source environment
source ${UTILS_DIR}/setup_environment.sh

# Change to output directory
cd ${OUTPUT_DIR}

# Run PhotonSim
${PHOTONSIM_DIR}/build/PhotonSim "${MACRO_FILE}"

if [ -f "${OUTPUT_FILE}" ]; then
    echo "Success! Created: ${OUTPUT_FILE}"
    ls -lh "${OUTPUT_FILE}"
else
    echo "Error: PhotonSim failed to create ${OUTPUT_FILE}"
    exit 1
fi

echo ""
echo "=== Job completed successfully ==="
EOFJOBSCRIPT
            chmod +x "$JOB_SCRIPT"

            # Create SLURM script
            SLURM_SCRIPT="${OUTPUT_DIR}/submit_job${JOB_SUFFIX}.sbatch"
            JOB_NAME="photonsim_${particle_type}_${energy_int}MeV${JOB_SUFFIX}"

            cat > "$SLURM_SCRIPT" << EOFSLURM
#!/bin/bash
#SBATCH --partition=${SLURM_PARTITION}
#SBATCH --account=${SLURM_ACCOUNT}
#
#SBATCH --job-name=${JOB_NAME}
#SBATCH --output=${OUTPUT_DIR}/job${JOB_SUFFIX}-%j.out
#SBATCH --error=${OUTPUT_DIR}/job${JOB_SUFFIX}-%j.err
#
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=${DEFAULT_CPUS}
#SBATCH --mem-per-cpu=${DEFAULT_MEMORY}
#
#SBATCH --time=${DEFAULT_TIME}

echo "SLURM Job ID: \${SLURM_JOB_ID}"
echo "Job started at: \$(date)"
echo "Running on node: \$(hostname)"

# Execute the job script
${JOB_SCRIPT}

echo "Job ended at: \$(date)"
EOFSLURM
            chmod +x "$SLURM_SCRIPT"

            # Submit if requested
            if [ "$SUBMIT_JOBS" = true ]; then
                sbatch "$SLURM_SCRIPT"
                submitted_count=$((submitted_count + 1))
            fi
        done

        if [ "$TEST_MODE" = true ]; then
            echo "Test mode: Stopping after first energy"
            break
        fi
    done

    echo ""
    echo "=== Job Generation Complete ==="
    echo "Total energies processed: ${#ENERGIES[@]}"
    echo "Jobs per energy: $jobs_to_process"
    if [ "$SUBMIT_JOBS" = true ]; then
        echo "Total jobs submitted: $submitted_count"
    fi
}

# Function to handle single-particle uniform energy jobs
handle_uniform_single_particle() {
    local particle_type=$(jq -r '.particles[0].type' "$CONFIG_FILE")
    local energy_min=$(jq -r '.energy_min_MeV' "$CONFIG_FILE")
    local energy_max=$(jq -r '.energy_max_MeV' "$CONFIG_FILE")

    if [ "$energy_min" == "null" ] || [ "$energy_max" == "null" ]; then
        echo "Error: For uniform energy mode with single particle, energy_min_MeV and energy_max_MeV are required"
        exit 1
    fi

    local energy_min_int=$(printf "%.0f" $energy_min)
    local energy_max_int=$(printf "%.0f" $energy_max)

    OUTPUT_DIR="${OUTPUT_BASE_DIR}/${particle_type}/${energy_min_int}_${energy_max_int}MeV_uniform"

    echo "Particle: $particle_type"
    echo "Energy range: ${energy_min_int}-${energy_max_int} MeV"
    echo "Output directory: $OUTPUT_DIR"
    echo ""

    mkdir -p "$OUTPUT_DIR"

    local jobs_to_process=$N_JOBS
    if [ "$TEST_MODE" = true ]; then
        jobs_to_process=1
        echo "Test mode: Processing only 1 job"
    fi

    local submitted_count=0

    for (( job_num=1; job_num<=$jobs_to_process; job_num++ )); do
        JOB_ID=$(printf "%06d" $job_num)
        OUTPUT_FILE="output_job${JOB_ID}.root"

        # Create macro
        MACRO_FILE="${OUTPUT_DIR}/run_${particle_type}_${energy_min_int}_${energy_max_int}MeV_uniform_job${JOB_ID}.mac"
        create_macro "$MACRO_FILE" "$particle_type" "$OUTPUT_FILE" "uniform" "$energy_min" "$energy_max" "$N_EVENTS" "$STORE_INDIVIDUAL"

        # Create job script
        JOB_SCRIPT="${OUTPUT_DIR}/run_photonsim_job${JOB_ID}.sh"

        if [ "$RUN_LUCID" == "true" ]; then
            # Job script with LUCiD
            cat > "$JOB_SCRIPT" << EOFJOBSCRIPT
#!/bin/bash
# PhotonSim + LUCiD job execution script
# Generated by generate_jobs.sh

echo "Starting PhotonSim + LUCiD job"
echo "Configuration: ${CONFIG_NAME}"
echo "Particle: ${particle_type}"
echo "Energy range: ${energy_min_int}-${energy_max_int} MeV"
echo "Events: ${N_EVENTS}"
echo "Output: ${OUTPUT_FILE}"
echo ""

# Source environment
source ${UTILS_DIR}/setup_environment.sh

# Change to output directory
cd ${OUTPUT_DIR}

# Step 1: Run PhotonSim
echo "=== Step 1: Running PhotonSim ==="
${PHOTONSIM_DIR}/build/PhotonSim "${MACRO_FILE}"

if [ -f "${OUTPUT_FILE}" ]; then
    echo "Success! Created: ${OUTPUT_FILE}"
    ls -lh "${OUTPUT_FILE}"
else
    echo "Error: PhotonSim failed to create ${OUTPUT_FILE}"
    exit 1
fi

# Step 2: Set up LUCiD environment
echo ""
echo "=== Step 2: Setting up LUCiD environment ==="
export SINGULARITY_IMAGE_PATH=/sdf/group/neutrino/images/develop.sif
export JAX_PLATFORMS=cpu
function spython() {
    singularity exec -B /sdf,/fs,/sdf/scratch,/lscratch \${SINGULARITY_IMAGE_PATH} python "\$@"
}

# Create output folder for LUCiD
LUCID_OUTPUT_FOLDER="${OUTPUT_DIR}/folder_job_${JOB_ID}"
mkdir -p "\${LUCID_OUTPUT_FOLDER}"
echo "Created LUCiD output folder: \${LUCID_OUTPUT_FOLDER}"

# Step 3: Run LUCiD
echo ""
echo "=== Step 3: Running LUCiD ==="
echo "Input: ${OUTPUT_DIR}/${OUTPUT_FILE}"
echo "Output folder: \${LUCID_OUTPUT_FOLDER}"

spython ${LUCID_PATH}/tools/production/generate_events.py --particle ${particle_type}:${OUTPUT_DIR}/${OUTPUT_FILE} --output "\${LUCID_OUTPUT_FOLDER}"

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
FINAL_H5_PATH="${OUTPUT_DIR}/\${FINAL_H5_NAME}"

mv "\${LUCID_OUTPUT_FILE}" "\${FINAL_H5_PATH}"
echo "Moved and renamed: \${LUCID_OUTPUT_FILE} -> \${FINAL_H5_PATH}"
ls -lh "\${FINAL_H5_PATH}"

# Remove the temporary folder
rmdir "\${LUCID_OUTPUT_FOLDER}" 2>/dev/null && echo "Removed temporary folder: \${LUCID_OUTPUT_FOLDER}" || echo "Folder not empty, keeping: \${LUCID_OUTPUT_FOLDER}"

echo ""
echo "=== Job completed successfully ==="
echo "PhotonSim output: ${OUTPUT_DIR}/${OUTPUT_FILE}"
echo "LUCiD output: \${FINAL_H5_PATH}"
EOFJOBSCRIPT
        else
            # Job script without LUCiD
            cat > "$JOB_SCRIPT" << EOFJOBSCRIPT
#!/bin/bash
# PhotonSim job execution script
# Generated by generate_jobs.sh

echo "Starting PhotonSim job"
echo "Configuration: ${CONFIG_NAME}"
echo "Particle: ${particle_type}"
echo "Energy range: ${energy_min_int}-${energy_max_int} MeV"
echo "Events: ${N_EVENTS}"
echo "Output: ${OUTPUT_FILE}"
echo ""

# Source environment
source ${UTILS_DIR}/setup_environment.sh

# Change to output directory
cd ${OUTPUT_DIR}

# Run PhotonSim
${PHOTONSIM_DIR}/build/PhotonSim "${MACRO_FILE}"

if [ -f "${OUTPUT_FILE}" ]; then
    echo "Success! Created: ${OUTPUT_FILE}"
    ls -lh "${OUTPUT_FILE}"
else
    echo "Error: PhotonSim failed to create ${OUTPUT_FILE}"
    exit 1
fi

echo ""
echo "=== Job completed successfully ==="
EOFJOBSCRIPT
        fi

        chmod +x "$JOB_SCRIPT"

        # Create SLURM script
        SLURM_SCRIPT="${OUTPUT_DIR}/submit_job_${JOB_ID}.sbatch"
        if [ "$RUN_LUCID" == "true" ]; then
            JOB_NAME="photonsim_lucid_${particle_type}_${energy_min_int}-${energy_max_int}MeV_${JOB_ID}"
        else
            JOB_NAME="photonsim_${particle_type}_${energy_min_int}-${energy_max_int}MeV_${JOB_ID}"
        fi

        cat > "$SLURM_SCRIPT" << EOFSLURM
#!/bin/bash
#SBATCH --partition=${SLURM_PARTITION}
#SBATCH --account=${SLURM_ACCOUNT}
#
#SBATCH --job-name=${JOB_NAME}
#SBATCH --output=${OUTPUT_DIR}/job_${JOB_ID}-%j.out
#SBATCH --error=${OUTPUT_DIR}/job_${JOB_ID}-%j.err
#
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=${DEFAULT_CPUS}
#SBATCH --mem-per-cpu=${DEFAULT_MEMORY}
#
#SBATCH --time=${DEFAULT_TIME}

echo "SLURM Job ID: \${SLURM_JOB_ID}"
echo "Job started at: \$(date)"
echo "Running on node: \$(hostname)"

# Execute the job script
${JOB_SCRIPT}

echo "Job ended at: \$(date)"
EOFSLURM
        chmod +x "$SLURM_SCRIPT"

        # Submit if requested
        if [ "$SUBMIT_JOBS" = true ]; then
            sbatch "$SLURM_SCRIPT"
            submitted_count=$((submitted_count + 1))
        fi
    done

    echo ""
    echo "=== Job Generation Complete ==="
    echo "Jobs prepared: $jobs_to_process"
    if [ "$SUBMIT_JOBS" = true ]; then
        echo "Jobs submitted: $submitted_count"
    fi
}

# Function to handle multi-particle jobs
handle_multiparticle() {
    if [ "$ENERGY_DIST" != "uniform" ]; then
        echo "Error: Multi-particle mode currently only supports uniform energy distribution"
        exit 1
    fi

    if [ "$RUN_LUCID" != "true" ]; then
        echo "Error: Multi-particle mode requires run_lucid to be true"
        exit 1
    fi

    # Determine output directory based on use_config_number
    if [ "$USE_CONFIG_NUMBER" == "true" ]; then
        CONFIG_DIR="${OUTPUT_BASE_DIR}/config_$(printf "%06d" $CONFIG_NUMBER)"
        echo "Using config number: $(printf "%06d" $CONFIG_NUMBER)"
    else
        CONFIG_DIR="${OUTPUT_BASE_DIR}"
        echo "Not using config number subdirectory"
    fi

    echo "Output directory: $CONFIG_DIR"
    echo ""

    mkdir -p "$CONFIG_DIR"

    # Create README file
    README_FILE="${CONFIG_DIR}/README.md"
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

        # Check for per-particle energy range
        ENERGY_MIN=$(jq -r ".particles[$i].energy_min_MeV" "$CONFIG_FILE")
        ENERGY_MAX=$(jq -r ".particles[$i].energy_max_MeV" "$CONFIG_FILE")

        # Fall back to global energy range if not specified
        if [ "$ENERGY_MIN" == "null" ]; then
            ENERGY_MIN=$(jq -r '.energy_min_MeV' "$CONFIG_FILE")
        fi
        if [ "$ENERGY_MAX" == "null" ]; then
            ENERGY_MAX=$(jq -r '.energy_max_MeV' "$CONFIG_FILE")
        fi

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

    local jobs_to_process=$N_JOBS
    if [ "$TEST_MODE" = true ]; then
        jobs_to_process=1
        echo "Test mode: Processing only 1 job"
    fi

    local submitted_count=0

    for (( job_num=1; job_num<=$jobs_to_process; job_num++ )); do
        JOB_ID=$(printf "%06d" $job_num)

        echo "=== Preparing Job $job_num/$jobs_to_process (ID: $JOB_ID) ==="

        # Create macro files for each particle
        MACRO_FILES=()
        ROOT_FILES=()

        for (( p=0; p<$N_PARTICLES; p++ )); do
            PARTICLE_TYPE=$(jq -r ".particles[$p].type" "$CONFIG_FILE")

            # Get per-particle or global energy range
            ENERGY_MIN=$(jq -r ".particles[$p].energy_min_MeV" "$CONFIG_FILE")
            ENERGY_MAX=$(jq -r ".particles[$p].energy_max_MeV" "$CONFIG_FILE")

            if [ "$ENERGY_MIN" == "null" ]; then
                ENERGY_MIN=$(jq -r '.energy_min_MeV' "$CONFIG_FILE")
            fi
            if [ "$ENERGY_MAX" == "null" ]; then
                ENERGY_MAX=$(jq -r '.energy_max_MeV' "$CONFIG_FILE")
            fi

            # Create output filename
            ROOT_FILE="particle_${p}_${PARTICLE_TYPE}_job_${JOB_ID}.root"
            ROOT_FILES+=("$ROOT_FILE")

            # Create macro file
            MACRO_FILE="${CONFIG_DIR}/particle_${p}_${PARTICLE_TYPE}_job_${JOB_ID}.mac"
            MACRO_FILES+=("$MACRO_FILE")

            create_macro "$MACRO_FILE" "$PARTICLE_TYPE" "$ROOT_FILE" "uniform" "$ENERGY_MIN" "$ENERGY_MAX" "$N_EVENTS" "true"
        done

        # Create job execution script
        JOB_SCRIPT="${CONFIG_DIR}/run_job_${JOB_ID}.sh"

        cat > "$JOB_SCRIPT" << EOFJOBSCRIPT
#!/bin/bash
# Multi-particle PhotonSim + LUCiD job execution script
# Generated by generate_jobs.sh

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
        JOB_NAME="multiparticle_${CONFIG_NAME}_${JOB_ID}"

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

# Execute the job script
${JOB_SCRIPT}

echo "Job ended at: \$(date)"
EOFSLURM

        chmod +x "$SLURM_SCRIPT"

        # Submit job if requested
        if [ "$SUBMIT_JOBS" = true ]; then
            sbatch "$SLURM_SCRIPT"
            submitted_count=$((submitted_count + 1))
        fi
    done

    echo ""
    echo "=== Dataset Generation Complete ==="
    echo "Configuration: $CONFIG_NAME (config_$(printf "%06d" $CONFIG_NUMBER))"
    echo "Output directory: $CONFIG_DIR"
    echo "Jobs prepared: $jobs_to_process"
    if [ "$SUBMIT_JOBS" = true ]; then
        echo "Jobs submitted to SLURM: $submitted_count"
    fi
}

# Main logic - route to appropriate handler
if [ "$N_PARTICLES" -eq 1 ]; then
    if [ "$ENERGY_DIST" == "monoenergetic" ]; then
        handle_monoenergetic_single_particle
    else
        handle_uniform_single_particle
    fi
else
    handle_multiparticle
fi

echo ""
echo "To monitor jobs, run:"
echo "  ${SCRIPT_DIR}/monitor_jobs.sh -w"
echo ""
