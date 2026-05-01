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
- **Track segment storage** for downstream truth reconstruction — one
  row per raw G4 sub-step, with inline `Segment_TrackID` so consumers
  can re-aggregate by track or apply their own merging policy.

## Requirements

- GEANT4 ≥ 11.3
- ROOT ≥ 6.0
- CMake ≥ 3.16
- C++17 compiler

## Running PhotonSim

The canonical path is the LUCiD container, which has GEANT4 + ROOT and
a baked PhotonSim build already installed. Bind-mount your checkout to
pick up local edits without rebuilding the image:

- macOS / dev laptop → [`LUCiD/docs/QUICKSTART_DOCKER.md`](https://github.com/CIDeR-ML/LUCiD/blob/main/docs/QUICKSTART_DOCKER.md).
- SLAC S3DF / SLURM → [`LUCiD/docs/QUICKSTART_S3DF.md`](https://github.com/CIDeR-ML/LUCiD/blob/main/docs/QUICKSTART_S3DF.md).
- Host-native (GEANT4 ≥ 11.3 + ROOT installed yourself) →
  [`LUCiD/docs/QUICKSTART_LOCAL.md`](https://github.com/CIDeR-ML/LUCiD/blob/main/docs/QUICKSTART_LOCAL.md).

### Build (host-native)

```bash
git clone https://github.com/cesarjesusvalls/PhotonSim.git
cd PhotonSim
mkdir build && cd build
cmake -DGeant4_DIR=$(geant4-config --prefix)/lib/cmake/Geant4 ..
make -j$(nproc)
# → ./PhotonSim
```

Linux users typically `source $(geant4-config --prefix)/bin/geant4.sh`
before building; macOS users likewise need the GEANT4 env vars set.

### Run

```bash
cd build
./PhotonSim ../macros/quick_test.mac
```

`macros/quick_test.mac` is a 5-event muon smoke test; edit the `/gun/`
block to swap particle / energy. `macros/list_processes.mac` dumps the
GEANT4 process table for each particle type (handy when picking
`/particle/process/inactivate` indices). Bespoke runs are usually
written from scratch — the macro language is small and well-documented
upstream.

### ROOT output branches

| Branch | Description |
|---|---|
| `EventID` | Event index |
| `PrimaryEnergy` | Primary kinetic energy (MeV) |
| `NOpticalPhotons` | Photon count in event |
| `PhotonPosX/Y/Z` | Photon creation positions (mm) |
| `PhotonDirX/Y/Z` | Photon direction unit vectors |
| `PhotonTime` | Creation time (ns) |
| `PhotonWavelength` | Photon wavelength (nm) |
| `PhotonProcess` | `Cerenkov` or `Scintillation` |

The per-photon branches (rows below `NOpticalPhotons`) are written to
the `OpticalPhotonsRaw` chunk tree only when `/photon/storeIndividual
true`. Track-segment and per-track branches (`Segment_*`,
`TrackInfo_*`) are always written; see `src/DataManager.cc` for the
full schema.

## Visualization, analysis, and SIREN training inputs

These all live in [LUCiD](https://github.com/CIDeR-ML/LUCiD):

- Interactive web event display: `LUCiD/viewer/serve_viewer.py`
  (consumes the v3 four-file HDF5 dataset produced by `lucid-run-job`).
- ROOT → HDF5 lookup-table builders for SIREN training:
  `lucid-build-photon-table` and `lucid-build-dedx-table` (see
  `LUCiD/docs/SIREN_TRAINING_INPUTS.md`).
- ROOT-file sanity checks:
  `LUCiD/lucid/siren/training/photonsim_data/check_root_files.py`.

The only Python utility that lives in this repo is `tools/t0_correction/`
— a self-contained timing-correction calibration that runs PhotonSim
energy scans and fits an `(E, distance) → t` parameterization. See
`tools/t0_correction/README.md`.

## Project layout

```
PhotonSim/
├── CMakeLists.txt
├── PhotonSim.cc          # main() — parses CLI macro arg, runs G4 run manager
├── include/              # C++ headers
├── src/                  # C++ sources
├── macros/
│   ├── quick_test.mac        # 5-event muon smoke test
│   ├── list_processes.mac    # dumps GEANT4 process table per particle
│   └── diffsim_input/        # JSON run-configs (consumed by LUCiD's job runner)
├── tools/
│   └── t0_correction/    # PhotonSim-only timing calibration utility
└── README.md
```

## License

Based on GEANT4 examples; follows the GEANT4 license terms.
