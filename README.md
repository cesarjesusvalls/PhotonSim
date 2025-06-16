# PhotonSim - GEANT4 Optical Photon Simulation

A GEANT4-based application for simulating optical photon generation in monolithic detector volumes.

## Overview

PhotonSim is designed to study optical photon production from particle interactions in large detector volumes. It records detailed information about optical photons generated through Cerenkov and scintillation processes.

**Scope**: PhotonSim focuses on data generation and 3D lookup table creation. For machine learning applications and neural network training on PhotonSim data, see the [diffCherenkov](../diffCherenkov) repository.

## Features

- **Monolithic Detector Geometry**: Configurable detector dimensions (default 100×100×100 meters)
- **Multiple Materials**: Water, Liquid Argon, Ice, or Liquid Scintillator with proper optical properties
- **Configurable Particle Gun**: Shoots particles from detector center (0,0,0) along z-axis (0,0,1)
- **Optical Physics**: Complete Cerenkov and scintillation processes
- **Data Recording**: ROOT output with optical photon data including:
  - Initial position (x,y,z)
  - Direction vector (dx,dy,dz)
  - Creation time
  - Physics process (Cerenkov/Scintillation)
  - Primary particle energy

## Requirements

- GEANT4 (version 11.3+)
- ROOT (version 6.0+)
- CMake (version 3.16+)
- C++17 compiler

## Installation

### Prerequisites

First install GEANT4 and ROOT:

```bash
# Install GEANT4 following official instructions
# Install ROOT via package manager or from source
```

### Building PhotonSim

```bash
git clone https://github.com/cesarjesusvalls/PhotonSim.git
cd PhotonSim
mkdir build && cd build

# Configure with CMake
cmake -DGeant4_DIR=/path/to/geant4/install/lib/cmake/Geant4 ..

# Build
make -j$(nproc)
```

## Usage

### Basic Execution

```bash
cd build
./PhotonSim ../macros/test_muon.mac
```

This runs the simulation with default parameters. Multiple macro files are available in the `macros/` directory.

### Configuration

The detector and physics parameters can be configured by modifying the source code:

- **Detector size**: Modify `fDetectorSizeX/Y/Z` in `DetectorConstruction.hh`
- **Material**: Change `fDetectorMaterialName` in `DetectorConstruction.hh`
- **Particle type**: Modify particle in `PrimaryGeneratorAction.cc`
- **Energy range**: Adjust `fMinEnergy/fMaxEnergy` in `PrimaryGeneratorAction.hh`

## Project Structure

```
PhotonSim/
├── src/              # C++ source files
├── include/          # Header files  
├── macros/           # GEANT4 macro files
│   ├── test_muon.mac
│   ├── muons_300_1000MeV.mac
│   └── electrons_100_500MeV.mac
├── tools/            # Analysis and visualization tools
│   ├── analysis/     # Python analysis scripts
│   ├── validation/   # Physics validation tools
│   └── visualization/ # 3D visualization tools
├── build/            # Build directory (created by cmake)
└── README.md
```

### Output

The simulation produces a ROOT file `optical_photons.root` containing:

- `EventID`: Event number
- `PrimaryEnergy`: Primary particle energy (MeV)
- `NOpticalPhotons`: Number of optical photons in event
- `PhotonPosX/Y/Z`: Photon creation positions (mm)
- `PhotonDirX/Y/Z`: Photon direction vectors
- `PhotonTime`: Photon creation times (ns)
- `PhotonProcess`: Creation process name

## 3D Lookup Tables (HDF5 Format)

PhotonSim can generate comprehensive 3D lookup tables for machine learning applications:

```bash
# Generate density-normalized 3D lookup table from simulation data
python tools/table_generation/create_density_3d_table.py \
    --data-dir data/mu-/ \
    --output output/3d_lookup_table_density
```

### HDF5 Output Structure

The lookup table is saved as `photon_lookup_table.h5` with the following structure:

```
/data/
  ├── photon_table_raw         # Raw photon counts
  ├── photon_table_normalized  # Photons per event
  ├── photon_table_density     # Photon density (photons/event/sr/mm)
  └── bin_areas               # Bin areas in sr·mm
/coordinates/
  ├── energy_values           # Energy grid points (MeV)
  ├── energy_centers          # Energy bin centers
  ├── angle_centers           # Angle bin centers (radians)
  ├── distance_centers        # Distance bin centers (mm)
  └── *_edges                 # Bin edge arrays
/metadata/
  ├── energy_min/max          # Energy range
  ├── angle/distance_range    # Spatial ranges
  ├── table_shape             # Array dimensions
  ├── density_units           # "photons/(event·sr·mm)"
  └── events_per_file         # Event counts per energy
```

This HDF5 format is compatible with [diffCherenkov](../diffCherenkov) for neural network training.

## Visualization

PhotonSim includes a Python-based interactive 3D visualization tool:

### Quick Start

```bash
# Install Python dependencies
pip install uproot matplotlib numpy ipywidgets

# Run visualization
python tools/visualization/visualize_photons.py build/optical_photons.root
```

### Features

- **Interactive 3D Plots**: Navigate through events with keyboard controls
- **Color-coded Photons**: Photons colored by creation time
- **Detector Geometry**: Wireframe detector outline
- **Direction Vectors**: Sample of photon directions as arrows
- **Event Statistics**: Energy and photon count information

### Controls

- **Arrow keys** or **n/p**: Navigate between events
- **Mouse**: Rotate, zoom, pan 3D view
- **r**: Refresh current view

See [VISUALIZATION.md](VISUALIZATION.md) for detailed documentation.

### Example Analysis

```python
import sys
sys.path.append('tools/visualization')
from visualize_photons import PhotonSimVisualizer

# Load and analyze data
viz = PhotonSimVisualizer('build/optical_photons.root')

# Get event statistics
event_data = viz.get_event_data(0)
print(f"Event 0: {event_data['primary_energy']:.1f} MeV")
print(f"Photons: {event_data['n_photons']:,}")

# Interactive visualization
viz.create_interactive_plot()
```

## Analysis

### Python Analysis (Recommended)

```python
# Run example analysis
python tools/visualization/example_visualization.py

# Run physics validation
python tools/validation/physics_summary.py
```

### ROOT Analysis

```cpp
// Open the output file
TFile* f = new TFile("optical_photons.root");
TTree* tree = (TTree*)f->Get("OpticalPhotons");

// Draw photon positions
tree->Draw("PhotonPosY:PhotonPosX", "PhotonProcess==\"Cerenkov\"");
```

## Architecture

- **DetectorConstruction**: Defines geometry and materials with optical properties
- **PhysicsList**: Configures physics processes including optical physics
- **PrimaryGeneratorAction**: Configurable particle gun
- **SteppingAction**: Tracks optical photon creation
- **DataManager**: Manages ROOT output
- **EventAction/RunAction**: Event-level data handling

## Contributing

Feel free to submit issues and pull requests to improve the simulation.

## License

This project is based on GEANT4 examples and follows the GEANT4 license terms.