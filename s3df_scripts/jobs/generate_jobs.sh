#!/bin/bash
# Unified script to generate PhotonSim jobs from JSON configuration
# NEW VERSION: Uses single PhotonSim execution with multiple primaries
# and generate_events_with_labels.py for LUCiD processing
#
# Usage: ./generate_jobs.sh -c <config_json> [-s] [-t]

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PHOTONSIM_DIR="$( cd "${SCRIPT_DIR}/../.." && pwd )"
UTILS_DIR="${SCRIPT_DIR}/../utils"
USER_PATHS="${SCRIPT_DIR}/../user_paths.sh"

# Source user paths (contains all user-specific configuration)
if [ -f "${USER_PATHS}" ]; then
    source "${USER_PATHS}"
else
    echo "Error: user_paths.sh not found at ${USER_PATHS}"
    echo "Please copy user_paths.sh.template to user_paths.sh and configure your paths."
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

echo "=== PhotonSim Job Generation (Unified Workflow) ==="
echo ""

# Parse JSON config - basic fields
CONFIG_NUMBER=$(jq -r '.config_number' "$CONFIG_FILE")
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

# Parse new fields with defaults
DISABLE_DECAYS=$(jq -r '.disable_decays // false' "$CONFIG_FILE")
APPLY_SMEARING=$(jq -r '.lucid_options.apply_smearing // true' "$CONFIG_FILE")
APPLY_ROTATION=$(jq -r '.lucid_options.apply_rotation // true' "$CONFIG_FILE")
APPLY_TRANSLATION=$(jq -r '.lucid_options.apply_translation // true' "$CONFIG_FILE")

# Validate config_number (required for unified output structure)
if [ "$CONFIG_NUMBER" == "null" ] || [ "$CONFIG_NUMBER" == "-1" ]; then
    echo "Error: config_number is required for data production configs"
    exit 1
fi

# Build output directory - always use config_XXXXXX format
OUTPUT_BASE_DIR="${OUTPUT_BASE_PATH}/${MATERIAL}/${OUTPUT_PATH}"
CONFIG_DIR="${OUTPUT_BASE_DIR}/config_$(printf "%06d" $CONFIG_NUMBER)"

# Validate parsed values
if [ "$CONFIG_NAME" == "null" ]; then
    echo "Error: Invalid JSON configuration. Required field: name"
    exit 1
fi

if [ "$MATERIAL" == "null" ]; then
    echo "Error: Invalid JSON configuration. Required field: material"
    exit 1
fi

if [ "$OUTPUT_PATH" == "null" ]; then
    echo "Error: Invalid JSON configuration. Required field: output_path"
    exit 1
fi

if [ "$ENERGY_DIST" != "monoenergetic" ] && [ "$ENERGY_DIST" != "uniform" ]; then
    echo "Error: energy_distribution must be 'monoenergetic' or 'uniform'"
    exit 1
fi

# Get LUCiD path if needed
if [ "$RUN_LUCID" == "true" ]; then
    if [ -z "$LUCID_PATH" ]; then
        echo "Error: LUCID_PATH not set. Check user_paths.sh"
        exit 1
    fi
fi

# Print configuration summary
echo "Configuration: $CONFIG_NAME (config_$(printf "%06d" $CONFIG_NUMBER))"
echo "Description: $CONFIG_DESC"
echo "Energy distribution: $ENERGY_DIST"
echo "Store individual photons: $STORE_INDIVIDUAL"
echo "Disable decays: $DISABLE_DECAYS"
echo "Run LUCiD: $RUN_LUCID"
if [ "$RUN_LUCID" == "true" ]; then
    echo "  - Apply smearing: $APPLY_SMEARING"
    echo "  - Apply rotation: $APPLY_ROTATION"
    echo "  - Apply translation: $APPLY_TRANSLATION"
fi
echo "Number of particles per event: $N_PARTICLES"
echo "Number of jobs: $N_JOBS"
echo "Events per job: $N_EVENTS"
echo "Output directory: $CONFIG_DIR"
echo ""

# Create output directory
mkdir -p "$CONFIG_DIR"

# Function to create PhotonSim macro with unified multi-primary approach
create_unified_macro() {
    local macro_file="$1"
    local output_file="$2"
    local nevents="$3"
    local store_individual="$4"
    local disable_decays="$5"
    local energy_dist="$6"

    cat > "$macro_file" << EOFMACRO
# PhotonSim macro (Unified Multi-Primary Workflow)
# Configuration: $CONFIG_NAME
# Config Number: $(printf "%06d" $CONFIG_NUMBER)
# Material: $MATERIAL
# Particles: $N_PARTICLES

# Set output filename before initialization
/output/filename ${output_file}

/run/initialize

EOFMACRO

    if [ "$store_individual" == "true" ]; then
        cat >> "$macro_file" << EOFMACRO
# ENABLE individual photon/edep storage for event-by-event analysis
/photon/storeIndividual true
/edep/storeIndividual false
EOFMACRO
    else
        cat >> "$macro_file" << EOFMACRO
# DISABLE individual photon/edep storage to save space
/photon/storeIndividual false
/edep/storeIndividual false
EOFMACRO
    fi

    # Add decay inactivation if requested
    if [ "$disable_decays" == "true" ]; then
        cat >> "$macro_file" << EOFMACRO

# Disable decay processes (for lookup table generation)
/particle/select mu-
/particle/process/inactivate 1
/particle/process/inactivate 7
/particle/select mu+
/particle/process/inactivate 1
/particle/select pi+
/particle/process/inactivate 1
/particle/select pi-
/particle/process/inactivate 1
EOFMACRO
    else
        cat >> "$macro_file" << EOFMACRO

# Decay processes ENABLED (for data production)
EOFMACRO
    fi

    # Add primary particles
    cat >> "$macro_file" << EOFMACRO

# Clear any existing primaries and set up new ones
/gun/clearPrimaries
EOFMACRO

    # Add each particle as a primary
    for (( p=0; p<$N_PARTICLES; p++ )); do
        PARTICLE_TYPE=$(jq -r ".particles[$p].type" "$CONFIG_FILE")

        if [ "$energy_dist" == "uniform" ]; then
            # Get per-particle or global energy range
            ENERGY_MIN=$(jq -r ".particles[$p].energy_min_MeV" "$CONFIG_FILE")
            ENERGY_MAX=$(jq -r ".particles[$p].energy_max_MeV" "$CONFIG_FILE")

            if [ "$ENERGY_MIN" == "null" ]; then
                ENERGY_MIN=$(jq -r '.energy_min_MeV' "$CONFIG_FILE")
            fi
            if [ "$ENERGY_MAX" == "null" ]; then
                ENERGY_MAX=$(jq -r '.energy_max_MeV' "$CONFIG_FILE")
            fi

            echo "/gun/addPrimaryWithEnergyRange $PARTICLE_TYPE $ENERGY_MIN $ENERGY_MAX MeV" >> "$macro_file"
        else
            # Monoenergetic - check for single energy or per-particle energy
            ENERGY=$(jq -r ".particles[$p].energy_MeV" "$CONFIG_FILE")
            if [ "$ENERGY" == "null" ]; then
                ENERGY=$(jq -r '.energy_MeV' "$CONFIG_FILE")
            fi
            echo "/gun/addPrimary $PARTICLE_TYPE $ENERGY MeV" >> "$macro_file"
        fi
    done

    cat >> "$macro_file" << EOFMACRO

# Use random directions for all primaries
/gun/randomDirection true

# Run ${nevents} events
/run/beamOn ${nevents}
EOFMACRO
}

# Function to handle monoenergetic jobs (energy scan)
handle_monoenergetic() {
    # Check if it's a single energy or energy scan
    local single_energy=$(jq -r '.energy_MeV' "$CONFIG_FILE")
    local has_scan=$(jq -r '.energy_scan' "$CONFIG_FILE")

    if [ "$single_energy" != "null" ]; then
        ENERGIES=("$single_energy")
    elif [ "$has_scan" != "null" ]; then
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

    echo "Energies to process: ${ENERGIES[@]}"
    echo ""

    local submitted_count=0
    local jobs_to_process=$N_JOBS
    if [ "$TEST_MODE" = true ]; then
        jobs_to_process=1
        echo "Test mode: Processing only 1 job per energy"
    fi

    # For monoenergetic with energy scan, create subdirectories per energy
    for energy in "${ENERGIES[@]}"; do
        energy_int=$(printf "%.0f" $energy)
        ENERGY_DIR="${CONFIG_DIR}/${energy_int}MeV"
        mkdir -p "$ENERGY_DIR"

        echo "=== Energy: ${energy_int} MeV ==="

        for (( job_num=1; job_num<=$jobs_to_process; job_num++ )); do
            JOB_ID=$(printf "%06d" $job_num)
            OUTPUT_FILE="output_job_${JOB_ID}.root"

            # Create macro - temporarily override energy_MeV for this iteration
            MACRO_FILE="${ENERGY_DIR}/job_${JOB_ID}.mac"

            # For monoenergetic, we need to handle the energy differently
            # Create a custom macro for this specific energy
            cat > "$MACRO_FILE" << EOFMACRO
# PhotonSim macro (Monoenergetic)
# Configuration: $CONFIG_NAME
# Config Number: $(printf "%06d" $CONFIG_NUMBER)
# Material: $MATERIAL
# Energy: ${energy_int} MeV

/output/filename ${OUTPUT_FILE}
/run/initialize

EOFMACRO

            if [ "$STORE_INDIVIDUAL" == "true" ]; then
                echo "/photon/storeIndividual true" >> "$MACRO_FILE"
                echo "/edep/storeIndividual false" >> "$MACRO_FILE"
            else
                echo "/photon/storeIndividual false" >> "$MACRO_FILE"
                echo "/edep/storeIndividual false" >> "$MACRO_FILE"
            fi

            if [ "$DISABLE_DECAYS" == "true" ]; then
                cat >> "$MACRO_FILE" << EOFMACRO

/particle/select mu-
/particle/process/inactivate 1
/particle/process/inactivate 7
/particle/select mu+
/particle/process/inactivate 1
/particle/select pi+
/particle/process/inactivate 1
/particle/select pi-
/particle/process/inactivate 1
EOFMACRO
            fi

            cat >> "$MACRO_FILE" << EOFMACRO

/gun/clearPrimaries
EOFMACRO

            # Add each particle at this energy
            for (( p=0; p<$N_PARTICLES; p++ )); do
                PARTICLE_TYPE=$(jq -r ".particles[$p].type" "$CONFIG_FILE")
                echo "/gun/addPrimary $PARTICLE_TYPE $energy MeV" >> "$MACRO_FILE"
            done

            cat >> "$MACRO_FILE" << EOFMACRO

/gun/randomDirection true
/run/beamOn ${N_EVENTS}
EOFMACRO

            # Create job script
            JOB_SCRIPT="${ENERGY_DIR}/run_job_${JOB_ID}.sh"
            create_job_script "$JOB_SCRIPT" "$MACRO_FILE" "$OUTPUT_FILE" "$ENERGY_DIR" "$JOB_ID"

            # Create SLURM script
            SLURM_SCRIPT="${ENERGY_DIR}/submit_job_${JOB_ID}.sbatch"
            JOB_NAME="photonsim_config$(printf "%06d" $CONFIG_NUMBER)_${energy_int}MeV_${JOB_ID}"
            create_slurm_script "$SLURM_SCRIPT" "$JOB_SCRIPT" "$ENERGY_DIR" "$JOB_ID" "$JOB_NAME"

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
    echo "Total energies: ${#ENERGIES[@]}"
    echo "Jobs per energy: $jobs_to_process"
    if [ "$SUBMIT_JOBS" = true ]; then
        echo "Total jobs submitted: $submitted_count"
    fi
}

# Function to handle uniform energy jobs
handle_uniform() {
    local jobs_to_process=$N_JOBS
    if [ "$TEST_MODE" = true ]; then
        jobs_to_process=1
        echo "Test mode: Processing only 1 job"
    fi

    local submitted_count=0

    # Print particle info
    echo "Particles:"
    for (( p=0; p<$N_PARTICLES; p++ )); do
        PARTICLE_TYPE=$(jq -r ".particles[$p].type" "$CONFIG_FILE")
        ENERGY_MIN=$(jq -r ".particles[$p].energy_min_MeV // .energy_min_MeV" "$CONFIG_FILE")
        ENERGY_MAX=$(jq -r ".particles[$p].energy_max_MeV // .energy_max_MeV" "$CONFIG_FILE")
        echo "  - $PARTICLE_TYPE: ${ENERGY_MIN}-${ENERGY_MAX} MeV"
    done
    echo ""

    for (( job_num=1; job_num<=$jobs_to_process; job_num++ )); do
        JOB_ID=$(printf "%06d" $job_num)
        OUTPUT_FILE="output_job_${JOB_ID}.root"

        echo "=== Preparing Job $job_num/$jobs_to_process (ID: $JOB_ID) ==="

        # Create macro
        MACRO_FILE="${CONFIG_DIR}/job_${JOB_ID}.mac"
        create_unified_macro "$MACRO_FILE" "$OUTPUT_FILE" "$N_EVENTS" "$STORE_INDIVIDUAL" "$DISABLE_DECAYS" "uniform"

        # Create job script
        JOB_SCRIPT="${CONFIG_DIR}/run_job_${JOB_ID}.sh"
        create_job_script "$JOB_SCRIPT" "$MACRO_FILE" "$OUTPUT_FILE" "$CONFIG_DIR" "$JOB_ID"

        # Create SLURM script
        SLURM_SCRIPT="${CONFIG_DIR}/submit_job_${JOB_ID}.sbatch"
        JOB_NAME="photonsim_config$(printf "%06d" $CONFIG_NUMBER)_${JOB_ID}"
        create_slurm_script "$SLURM_SCRIPT" "$JOB_SCRIPT" "$CONFIG_DIR" "$JOB_ID" "$JOB_NAME"

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

# Function to create job execution script
create_job_script() {
    local job_script="$1"
    local macro_file="$2"
    local output_file="$3"
    local output_dir="$4"
    local job_id="$5"

    if [ "$RUN_LUCID" == "true" ]; then
        # Build LUCiD flags
        LUCID_FLAGS=""
        [ "$APPLY_SMEARING" == "true" ] && LUCID_FLAGS="$LUCID_FLAGS --apply-smearing"
        [ "$APPLY_ROTATION" == "true" ] && LUCID_FLAGS="$LUCID_FLAGS --apply-rotation"
        [ "$APPLY_TRANSLATION" == "true" ] && LUCID_FLAGS="$LUCID_FLAGS --apply-translation"

        cat > "$job_script" << EOFJOBSCRIPT
#!/bin/bash
# PhotonSim + LUCiD job execution script (Unified Workflow)
# Generated by generate_jobs.sh

echo "Starting PhotonSim + LUCiD job (Unified Workflow)"
echo "Configuration: ${CONFIG_NAME}"
echo "Config Number: $(printf "%06d" $CONFIG_NUMBER)"
echo "Job ID: ${job_id}"
echo "Events: ${N_EVENTS}"
echo "Particles per event: ${N_PARTICLES}"
echo ""

# Source environment
source ${UTILS_DIR}/setup_environment.sh

# Change to output directory
cd ${output_dir}

# Step 1: Run PhotonSim (single execution with all primaries)
echo "=== Step 1: Running PhotonSim ==="
echo "Macro: ${macro_file}"
echo "Output: ${output_file}"

${PHOTONSIM_DIR}/build/PhotonSim "${macro_file}"

if [ -f "${output_file}" ]; then
    echo "Success! Created: ${output_file}"
    ls -lh "${output_file}"
else
    echo "Error: PhotonSim failed to create ${output_file}"
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
LUCID_OUTPUT_FOLDER="${output_dir}/folder_job_${job_id}"
mkdir -p "\${LUCID_OUTPUT_FOLDER}"
echo "Created LUCiD output folder: \${LUCID_OUTPUT_FOLDER}"

# Step 3: Run LUCiD with label-based workflow
echo ""
echo "=== Step 3: Running LUCiD (generate_events_with_labels.py) ==="
echo "Input: ${output_dir}/${output_file}"
echo "Output folder: \${LUCID_OUTPUT_FOLDER}"
echo "LUCiD flags:${LUCID_FLAGS}"

spython ${LUCID_PATH}/tools/production/generate_events_with_labels.py \\
    --root-file ${output_dir}/${output_file} \\
    --output "\${LUCID_OUTPUT_FOLDER}" \\
    ${LUCID_FLAGS}

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
FINAL_H5_NAME="events_job_${job_id}.h5"
FINAL_H5_PATH="${output_dir}/\${FINAL_H5_NAME}"

mv "\${LUCID_OUTPUT_FILE}" "\${FINAL_H5_PATH}"
echo "Moved and renamed: \${LUCID_OUTPUT_FILE} -> \${FINAL_H5_PATH}"
ls -lh "\${FINAL_H5_PATH}"

# Remove the temporary folder
rmdir "\${LUCID_OUTPUT_FOLDER}" 2>/dev/null && echo "Removed temporary folder: \${LUCID_OUTPUT_FOLDER}" || echo "Folder not empty, keeping: \${LUCID_OUTPUT_FOLDER}"

echo ""
echo "=== Job completed successfully ==="
echo "PhotonSim output: ${output_dir}/${output_file}"
echo "LUCiD output: \${FINAL_H5_PATH}"
EOFJOBSCRIPT
    else
        # Job script without LUCiD
        cat > "$job_script" << EOFJOBSCRIPT
#!/bin/bash
# PhotonSim job execution script (Unified Workflow)
# Generated by generate_jobs.sh

echo "Starting PhotonSim job (Unified Workflow)"
echo "Configuration: ${CONFIG_NAME}"
echo "Config Number: $(printf "%06d" $CONFIG_NUMBER)"
echo "Job ID: ${job_id}"
echo "Events: ${N_EVENTS}"
echo "Particles per event: ${N_PARTICLES}"
echo ""

# Source environment
source ${UTILS_DIR}/setup_environment.sh

# Change to output directory
cd ${output_dir}

# Run PhotonSim
echo "=== Running PhotonSim ==="
echo "Macro: ${macro_file}"
echo "Output: ${output_file}"

${PHOTONSIM_DIR}/build/PhotonSim "${macro_file}"

if [ -f "${output_file}" ]; then
    echo "Success! Created: ${output_file}"
    ls -lh "${output_file}"
else
    echo "Error: PhotonSim failed to create ${output_file}"
    exit 1
fi

echo ""
echo "=== Job completed successfully ==="
EOFJOBSCRIPT
    fi

    chmod +x "$job_script"
}

# Function to create SLURM submission script
create_slurm_script() {
    local slurm_script="$1"
    local job_script="$2"
    local output_dir="$3"
    local job_id="$4"
    local job_name="$5"

    cat > "$slurm_script" << EOFSLURM
#!/bin/bash
#SBATCH --partition=${SLURM_PARTITION}
#SBATCH --account=${SLURM_ACCOUNT}
#
#SBATCH --job-name=${job_name}
#SBATCH --output=${output_dir}/job_${job_id}-%j.out
#SBATCH --error=${output_dir}/job_${job_id}-%j.err
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
${job_script}

echo "Job ended at: \$(date)"
EOFSLURM

    chmod +x "$slurm_script"
}

# Create README file for this configuration
create_readme() {
    local readme_file="${CONFIG_DIR}/README.md"

    cat > "$readme_file" << EOF
# Dataset Configuration

**Configuration Number**: $(printf "%06d" $CONFIG_NUMBER)
**Configuration Name**: $CONFIG_NAME
**Description**: $CONFIG_DESC
**Generated**: $(date)

## Configuration Details

- **Material**: $MATERIAL
- **Energy distribution**: $ENERGY_DIST
- **Number of jobs**: $N_JOBS
- **Events per job**: $N_EVENTS
- **Total events**: $((N_JOBS * N_EVENTS))
- **Particles per event**: $N_PARTICLES
- **Disable decays**: $DISABLE_DECAYS
- **Run LUCiD**: $RUN_LUCID
EOF

    if [ "$RUN_LUCID" == "true" ]; then
        cat >> "$readme_file" << EOF
  - Apply smearing: $APPLY_SMEARING
  - Apply rotation: $APPLY_ROTATION
  - Apply translation: $APPLY_TRANSLATION
EOF
    fi

    cat >> "$readme_file" << EOF

## Particle Specifications

EOF

    for (( i=0; i<$N_PARTICLES; i++ )); do
        PARTICLE_TYPE=$(jq -r ".particles[$i].type" "$CONFIG_FILE")

        if [ "$ENERGY_DIST" == "uniform" ]; then
            ENERGY_MIN=$(jq -r ".particles[$i].energy_min_MeV // .energy_min_MeV" "$CONFIG_FILE")
            ENERGY_MAX=$(jq -r ".particles[$i].energy_max_MeV // .energy_max_MeV" "$CONFIG_FILE")
            echo "- **Particle $i**: $PARTICLE_TYPE (${ENERGY_MIN}-${ENERGY_MAX} MeV, uniform distribution)" >> "$readme_file"
        else
            ENERGY=$(jq -r ".particles[$i].energy_MeV // .energy_MeV" "$CONFIG_FILE")
            echo "- **Particle $i**: $PARTICLE_TYPE (${ENERGY} MeV, monoenergetic)" >> "$readme_file"
        fi
    done

    cat >> "$readme_file" << EOF

## Output Files

For each job (e.g., job 000001):
- PhotonSim ROOT file: \`output_job_000001.root\`
EOF

    if [ "$RUN_LUCID" == "true" ]; then
        echo "- LUCiD events file: \`events_job_000001.h5\`" >> "$readme_file"
    fi

    cat >> "$readme_file" << EOF

## Workflow

This configuration uses the **unified multi-primary workflow**:
1. Single PhotonSim execution per job with all particles as primaries
2. Each primary can have independent random energy (for uniform distribution)
3. All primaries share the same vertex position (0,0,0)
4. Random directions are enabled for all primaries
EOF

    if [ "$RUN_LUCID" == "true" ]; then
        cat >> "$readme_file" << EOF
5. LUCiD processes the single ROOT file using \`generate_events_with_labels.py\`
6. Label-based output preserves genealogy information for each primary
EOF
    fi
}

# Create README
create_readme

# Main logic - route to appropriate handler
if [ "$ENERGY_DIST" == "monoenergetic" ]; then
    handle_monoenergetic
else
    handle_uniform
fi

echo ""
echo "Output directory: $CONFIG_DIR"
echo "To monitor jobs, run:"
echo "  ${SCRIPT_DIR}/monitor_jobs.sh -w"
echo ""
