#!/bin/bash
# Master script to run PhotonSim validation tests for all particle types
# Generates data and creates HTML visualizations for each particle type
#
# Usage: ./run_all_validation_tests.sh [num_events]
#   num_events: Number of events per particle type (default: 20)

# Trap Ctrl+C and exit gracefully
trap 'echo ""; echo "Script interrupted by user. Exiting..."; exit 130' INT

# Parse command-line arguments
NUM_EVENTS=${1:-20}  # Default to 20 if not provided

# Validate input
if ! [[ "$NUM_EVENTS" =~ ^[0-9]+$ ]] || [ "$NUM_EVENTS" -lt 1 ]; then
    echo "Error: Number of events must be a positive integer"
    echo "Usage: $0 [num_events]"
    return 1 2>/dev/null || exit 1
fi

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Navigate to build directory (assumes PhotonSim is built)
BUILD_DIR="../../build"
if [ ! -d "$BUILD_DIR" ]; then
    echo "Error: Build directory not found at $BUILD_DIR"
    echo "Please build PhotonSim first by running 'cmake .. && make' in the build directory"
    return 1 2>/dev/null || exit 1
fi

cd "$BUILD_DIR" || { echo "Error: Could not change to build directory"; return 1 2>/dev/null || exit 1; }

# Check if PhotonSim executable exists
if [ ! -f "./PhotonSim" ]; then
    echo "Error: PhotonSim executable not found"
    echo "Please build PhotonSim first by running 'cmake .. && make' in the build directory"
    return 1 2>/dev/null || exit 1
fi

echo "========================================="
echo "PHOTONSIM VALIDATION TEST SUITE"
echo "========================================="
echo ""
echo "This script will:"
echo "  1. Run PhotonSim for each particle type (mu-, mu+, pi-, pi+, e-, e+)"
echo "  2. Generate $NUM_EVENTS events per particle at 1 GeV"
echo "  3. Create HTML visualizations for validation"
echo ""
echo "Output files will be in the build directory"
echo ""

# Define particle types to test
particles="mu_minus mu_plus pi_minus pi_plus e_minus e_plus"

# Run simulations and validation for each particle type
for particle in $particles; do
    # Convert particle name to label (mu_minus -> mu-)
    label=$(echo "$particle" | sed 's/_minus/-/' | sed 's/_plus/+/')

    echo ""
    echo "========================================="
    echo "Processing: $label (1 GeV, $NUM_EVENTS events)"
    echo "========================================="
    echo ""

    # Create temporary macro with correct number of events
    temp_macro="test_${particle}_temp.mac"
    sed "s|/run/beamOn 20|/run/beamOn $NUM_EVENTS|" "$SCRIPT_DIR/test_macros/test_${particle}.mac" > "$temp_macro"

    # Run PhotonSim
    echo "Running PhotonSim simulation..."
    ./PhotonSim "$temp_macro"

    # Clean up temporary macro
    rm -f "$temp_macro"

    if [ $? -ne 0 ]; then
        echo "ERROR: PhotonSim failed for $label"
        continue
    fi

    # Check if ROOT file was created
    root_file="test_${particle}.root"
    if [ ! -f "$root_file" ]; then
        echo "ERROR: Output file $root_file not found"
        continue
    fi

    echo ""
    echo "Running validation script..."
    python3 "$SCRIPT_DIR/validate_photonsim_classification.py" "$root_file" --events "$NUM_EVENTS"

    if [ $? -ne 0 ]; then
        echo "ERROR: Validation failed for $label"
        continue
    fi

    echo ""
    echo "✓ Completed: $label"
done

echo ""
echo "========================================="
echo "VALIDATION COMPLETE"
echo "========================================="
echo ""
echo "Generated files in $BUILD_DIR:"
echo "  ROOT files: test_*.root"
echo "  HTML plots: test_*_event*.html"
echo ""
echo "Open the HTML files in a browser to inspect the results"
echo ""
# Exit successfully (use return if sourced, exit if executed)
return 0 2>/dev/null || exit 0
