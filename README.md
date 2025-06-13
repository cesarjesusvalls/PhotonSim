# PhotonSim - GEANT4 Optical Photon Detector

A GEANT4-based application for simulating optical photon generation in monolithic detector volumes.

## Overview

PhotonSim is designed to study optical photon production from particle interactions in large detector volumes. It records detailed information about optical photons generated through Cerenkov and scintillation processes.

## Features

- **Monolithic Detector Geometry**: Configurable detector dimensions (default 10×10×10 meters)
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
./OpticalPhotonDetector
```

This runs the simulation with default parameters (10 events, electron beam, water detector).

### Configuration

The detector and physics parameters can be configured by modifying the source code:

- **Detector size**: Modify `fDetectorSizeX/Y/Z` in `DetectorConstruction.hh`
- **Material**: Change `fDetectorMaterialName` in `DetectorConstruction.hh`
- **Particle type**: Modify particle in `PrimaryGeneratorAction.cc`
- **Energy range**: Adjust `fMinEnergy/fMaxEnergy` in `PrimaryGeneratorAction.hh`

### Output

The simulation produces a ROOT file `optical_photons.root` containing:

- `EventID`: Event number
- `PrimaryEnergy`: Primary particle energy (MeV)
- `NOpticalPhotons`: Number of optical photons in event
- `PhotonPosX/Y/Z`: Photon creation positions (mm)
- `PhotonDirX/Y/Z`: Photon direction vectors
- `PhotonTime`: Photon creation times (ns)
- `PhotonProcess`: Creation process name

## Analysis

Example ROOT analysis:

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