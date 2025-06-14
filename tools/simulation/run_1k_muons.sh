#!/bin/bash
# Simple shell script to run 1000 muons

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PHOTONSIM_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Running 1000 Muons ==="
echo "Working directory: $PHOTONSIM_DIR"
echo "Expected runtime: ~4-5 minutes"
echo

cd "$PHOTONSIM_DIR"

# Check if executable exists
if [ ! -f "build/PhotonSim" ]; then
    echo "Error: PhotonSim executable not found at build/PhotonSim"
    echo "Please build PhotonSim first."
    exit 1
fi

# Check if macro exists
if [ ! -f "macros/muons_1k.mac" ]; then
    echo "Error: Macro file not found at macros/muons_1k.mac"
    exit 1
fi

# Record start time
start_time=$(date +%s)

# Run the simulation
echo "Starting simulation..."
./build/PhotonSim macros/muons_1k.mac

# Calculate runtime
end_time=$(date +%s)
runtime=$((end_time - start_time))

echo
echo "=== Simulation Complete ==="
echo "Runtime: ${runtime} seconds ($((runtime/60)) minutes)"
echo "Rate: $((1000/runtime)) events/second"

# Show ROOT file info if it exists
if [ -f "build/optical_photons.root" ]; then
    size=$(ls -lh build/optical_photons.root | awk '{print $5}')
    echo "ROOT file size: $size"
fi