#!/bin/bash
# Script to generate configuration files for uniform energy simulations
# Usage: ./generate_uniform_energy_config.sh -p <particle> -n <njobs> [-e <nevents>] [-o <output_dir>]

# Cherenkov threshold calculation for water (n=1.33):
# E_threshold = m * n / sqrt(n^2 - 1) = m * 1.517
#
# Electron (m=0.511 MeV): E_threshold = 0.775 MeV → Start at 51 MeV (threshold + 50)
# Muon (m=105.66 MeV): E_threshold = 160.3 MeV → Start at 210 MeV (threshold + 50)
# Pion (m=139.57 MeV): E_threshold = 211.8 MeV → Start at 262 MeV (threshold + 50)

# Default values
PARTICLE=""
NJOBS=100
NEVENTS=100
OUTPUT_DIR="/sdf/data/neutrino/cjesus/photonsim_output/water/uniform_energy"
MAX_ENERGY=1500

# Parse command line arguments
while getopts "p:n:e:o:h" opt; do
    case $opt in
        p) PARTICLE="$OPTARG";;
        n) NJOBS="$OPTARG";;
        e) NEVENTS="$OPTARG";;
        o) OUTPUT_DIR="$OPTARG";;
        h) echo "Usage: $0 -p <particle> -n <njobs> [-e <nevents>] [-o <output_dir>]"
           echo "  -p: Particle type (e-, mu-, or pi+) (required)"
           echo "  -n: Number of jobs to generate (required)"
           echo "  -e: Number of events per job (default: 100)"
           echo "  -o: Output directory (default: /sdf/data/neutrino/cjesus/photonsim_output/water/uniform_energy)"
           echo ""
           echo "Energy range: (Cherenkov_threshold + 50 MeV) to 1500 MeV"
           echo "  e-:  51-1500 MeV"
           echo "  mu-: 210-1500 MeV"
           echo "  pi+: 262-1500 MeV"
           exit 0;;
        \?) echo "Invalid option -$OPTARG" >&2; exit 1;;
    esac
done

# Check required parameters
if [ -z "$PARTICLE" ]; then
    echo "Error: Particle type is required (-p option)"
    echo "Use -h for help"
    exit 1
fi

if [ -z "$NJOBS" ]; then
    echo "Error: Number of jobs is required (-n option)"
    echo "Use -h for help"
    exit 1
fi

# Set minimum energy based on particle type
case $PARTICLE in
    e-)
        MIN_ENERGY=51
        PARTICLE_NAME="electron"
        ;;
    mu-)
        MIN_ENERGY=210
        PARTICLE_NAME="muon"
        ;;
    pi+)
        MIN_ENERGY=262
        PARTICLE_NAME="pion_plus"
        ;;
    *)
        echo "Error: Unsupported particle type: $PARTICLE"
        echo "Supported types: e-, mu-, pi+"
        exit 1
        ;;
esac

# Create config filename
CONFIG_FILE="${PARTICLE_NAME}_uniform_${MIN_ENERGY}_${MAX_ENERGY}_MeV_${NJOBS}jobs_${NEVENTS}events.txt"

echo "Generating configuration file: ${CONFIG_FILE}"
echo "Particle: ${PARTICLE}"
echo "Number of jobs: ${NJOBS}"
echo "Events per job: ${NEVENTS}"
echo "Energy range: ${MIN_ENERGY}-${MAX_ENERGY} MeV (uniform distribution)"
echo "Output directory: ${OUTPUT_DIR}"

# Create header
cat > "${CONFIG_FILE}" << EOF
# Uniform energy ${PARTICLE_NAME} simulations
# Particle: ${PARTICLE}
# Energy range: ${MIN_ENERGY}-${MAX_ENERGY} MeV (uniform random per event)
# Jobs: ${NJOBS} with ${NEVENTS} events each
# Individual photon storage ENABLED
# Format: particle nevents min_energy max_energy output_dir filename

EOF

# Generate job lines
for i in $(seq -f "%03g" 1 ${NJOBS}); do
    echo "${PARTICLE} ${NEVENTS} ${MIN_ENERGY} ${MAX_ENERGY} ${OUTPUT_DIR} output_job${i}.root" >> "${CONFIG_FILE}"
done

echo ""
echo "Configuration file created: ${CONFIG_FILE}"
echo "Total entries: ${NJOBS}"
echo ""
echo "To prepare jobs, run:"
echo "  ./submit_photonsim_batch_uniform.sh -c ${CONFIG_FILE}"
echo ""
echo "To prepare and submit jobs, run:"
echo "  ./submit_photonsim_batch_uniform.sh -c ${CONFIG_FILE} -s"
