# PhotonSim — GEANT4 optical-photon simulation

A GEANT4-based C++ application that simulates optical photon generation
(Cherenkov + scintillation) from particle interactions in monolithic
detector volumes. Inputs a `.mac` macro, outputs a ROOT file of
per-photon records.

PhotonSim is a **helper binary** for the LUCiD production pipeline. For
the full ROOT → v3 HDF5 dataset chain — including JSON dataset
configs, the batch runner, and SLURM wrappers — use
[LUCiD](https://github.com/CIDeR-ML/LUCiD); see its
`docs/QUICKSTART_LOCAL.md` / `docs/QUICKSTART_S3DF.md`.

## Features

- **Monolithic detector geometry**, configurable dimensions (default
  100 × 100 × 100 m).
- **Materials**: water, liquid argon, ice, liquid scintillator (with
  optical properties).
- **Configurable particle gun** via `/gun/addPrimary*` macro commands
  (multiple primaries per event, random isotropic or fixed direction,
  uniform or monoenergetic ranges).
- **Full optical physics** (Cherenkov, scintillation).
- **ROOT output** with per-photon position, direction, creation time,
  process, primary energy, optional wavelength.
- **Track segment storage** for downstream truth reconstruction (merged
  G4 steps with length / angle / edep thresholds).

## Requirements

- GEANT4 ≥ 11.3
- ROOT ≥ 6.0
- CMake ≥ 3.16
- C++17 compiler

## Build

```bash
git clone https://github.com/cesarjesusvalls/PhotonSim.git
cd PhotonSim
mkdir build && cd build
cmake -DGeant4_DIR=$(geant4-config --prefix)/lib/cmake/Geant4 ..
make -j$(nproc)
# → ./PhotonSim
```

The `setup.sh` script in the repo root is a convenience for setting
GEANT4 env vars on macOS; Linux users normally just source
`$(geant4-config --prefix)/bin/geant4.sh`.

## Run

```bash
cd build
./PhotonSim ../macros/test_muon.mac
```

Example macros live in `macros/` (e.g. `test_muon.mac`,
`muon_gun_uniform_energy_all_photons.mac`, `electrons_template.mac`).

### ROOT output branches

| Branch | Description |
|---|---|
| `EventID` | Event index |
| `PrimaryEnergy` | Primary kinetic energy (MeV) |
| `NOpticalPhotons` | Photon count in event |
| `PhotonPosX/Y/Z` | Photon creation positions (mm) |
| `PhotonDirX/Y/Z` | Photon direction unit vectors |
| `PhotonTime` | Creation time (ns) |
| `PhotonWavelength` | Photon wavelength (nm), when enabled via `/photon/storeIndividual` |
| `PhotonProcess` | `Cerenkov` or `Scintillation` |

Track-segment and per-particle branches are also written when segments
are enabled; see `src/DataManager.cc` for the full schema.

## Visualization

Interactive 3D photon-event viewer (Python, matplotlib-based):

```bash
pip install -r requirements.txt  # uproot, numpy, matplotlib, ipywidgets
python tools/visualization/visualize_photons.py build/optical_photons.root
```

`tools/` contains additional analysis and validation utilities (physics
validation, wavelength spectra, lookup-table generation). They are
consumers of PhotonSim ROOT output and are independent of this binary.

## Project layout

```
PhotonSim/
├── CMakeLists.txt
├── PhotonSim.cc          # main() — parses CLI macro arg, runs G4 run manager
├── include/              # C++ headers
├── src/                  # C++ sources
├── macros/               # example .mac macros
├── tools/                # Python analysis / validation / visualization
└── README.md
```

## License

Based on GEANT4 examples; follows the GEANT4 license terms.
