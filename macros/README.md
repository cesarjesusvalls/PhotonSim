# PhotonSim Macro Files

This directory contains GEANT4 macro files for different simulation configurations.

## Available Macros

### test_muon.mac
Basic muon simulation for testing and validation.
- **Particle**: Muon (mu-)
- **Energy**: ~152 MeV (single energy)
- **Events**: 1 event for quick testing
- **Purpose**: Physics validation and debugging

**Usage:**
```bash
cd build
./PhotonSim ../macros/test_muon.mac
```

### muons_300_1000MeV.mac
Extended muon energy range simulation.
- **Particle**: Muon (mu-)
- **Energy**: 300-1000 MeV range
- **Events**: Multiple events for statistics
- **Purpose**: Energy-dependent Cherenkov studies

**Usage:**
```bash
cd build
./PhotonSim ../macros/muons_300_1000MeV.mac
```

### electrons_100_500MeV.mac
Electron beam simulation for comparison studies.
- **Particle**: Electron (e-)
- **Energy**: 100-500 MeV range
- **Events**: Multiple events
- **Purpose**: Electromagnetic shower studies, secondary particle analysis

**Usage:**
```bash
cd build
./PhotonSim ../macros/electrons_100_500MeV.mac
```

## Macro Structure

All macros follow this general structure:
```
# Physics setup
/run/initialize

# Particle gun configuration
/gun/particle [particle_type]
/gun/energy [energy] [unit]
/gun/position 0 0 0 m
/gun/direction 0 0 1

# Run simulation
/run/beamOn [number_of_events]
```

## Creating Custom Macros

To create a new macro file:

1. Copy an existing macro as a template
2. Modify particle type: `/gun/particle mu-` or `/gun/particle e-`
3. Set energy: `/gun/energy 500 MeV`
4. Adjust number of events: `/run/beamOn 10`
5. Save with descriptive filename (e.g., `high_energy_muons.mac`)

## Expected Outputs

Each macro produces:
- ROOT file: `optical_photons.root` in the build directory
- Console output with photon creation debugging
- Physics validation information