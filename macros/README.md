# PhotonSim Macro Templates

This directory contains clean template macros for PhotonSim simulations.

## Available Macros

### Muon Templates
- **muons_fixed_energy_template.mac**: Fixed energy muon simulation template
- **muons_random_energy_template.mac**: Random energy muon simulation template
- **test_fixed_energy.mac**: Quick test with fixed 300 MeV (5 events)
- **test_random_energy.mac**: Quick test with random 200-800 MeV (10 events)

### Electron Templates
- **electrons_template.mac**: Fixed energy electron simulation template

## PhotonSim Energy Control System

PhotonSim supports flexible energy control via macro commands, allowing both fixed and random energy generation.

### Energy Control Commands

#### Fixed Energy (Default Mode)
```bash
/gun/randomEnergy false
/gun/energy 300 MeV
```

#### Random Energy
```bash
/gun/randomEnergy true
/gun/energyMin 100 MeV
/gun/energyMax 1000 MeV
```

#### Mixed Scenarios
```bash
# Start with random energy
/gun/randomEnergy true
/gun/energyMin 100 MeV
/gun/energyMax 500 MeV
/run/beamOn 50

# Switch to fixed energy
/gun/randomEnergy false
/gun/energy 750 MeV
/run/beamOn 50
```

### Energy Units
Supported units: `eV`, `keV`, `MeV`, `GeV`, `TeV`

Examples:
- `/gun/energy 1.5 GeV`
- `/gun/energyMin 500 keV`
- `/gun/energyMax 2 TeV`

### Default Behavior
- `fRandomEnergy = false` (fixed energy mode by default)
- Default energy: 5.0 MeV (from original GEANT4 particle gun)
- Default random range: 100-500 MeV (only used when random mode is enabled)

## Muon Decay Inactivation

All muon macros include these commands to disable muon decay:
```bash
/particle/select mu-
/particle/process/inactivate 1
/particle/process/inactivate 7
/particle/select mu+
/particle/process/inactivate 1
```

## Storage Options

Per-photon scalars are written to the `OpticalPhotonsRaw` chunk tree
only when `/photon/storeIndividual true`. With it disabled, the run
still writes per-event scalars (`PrimaryEnergy`, `NOpticalPhotons`),
the per-track and per-segment trees (`TrackInfo_*`, `Segment_*`), and
the 2D histograms — the only thing dropped is the per-photon list.

```bash
/photon/storeIndividual false   # histograms + segments only, smaller files
/photon/storeIndividual true    # also dump every optical photon
```

## Usage

```bash
cd build
./PhotonSim ../macros/[template_name].mac
```

## Output Files

All macros generate ROOT files containing:
- `PrimaryEnergy` branch: Actual primary particle energies used for validation
- 2D histograms: `PhotonHist_AngleDistance`, `dEdxHist_Distance`,
  `PhotonHist_TimeDistance`, `PhotonHist_Wavelength`
- Per-track + per-segment trees (`TrackInfo_*`, `Segment_*`)
- Optional: per-photon `OpticalPhotonsRaw` tree when
  `/photon/storeIndividual true`

## Bug Fix Notes

**Previous Issue**: PhotonSim was ignoring `/gun/energy` commands and using random energies (100-500 MeV) by default.

**Solution**: Changed default `fRandomEnergy = false` and added explicit macro commands for energy control.

**Impact**: All previous PhotonSim data generated before this fix used random energies instead of the specified values in macro files.