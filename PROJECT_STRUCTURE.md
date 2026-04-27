# PhotonSim Project Structure

Modern GEANT4-based simulation for optical photon generation with comprehensive analysis tools and energy control system.

## Directory Structure

```
PhotonSim/
├── README.md                    # Main project documentation
├── CMakeLists.txt              # Build configuration
├── PhotonSim.cc                # Main Geant4 application
├── requirements.txt            # Python dependencies
├── setup.sh                    # Environment setup
│
├── include/                    # C++ header files
│   ├── ActionInitialization.hh
│   ├── DataManager.hh
│   ├── DetectorConstruction.hh
│   ├── PrimaryGeneratorAction.hh    # ✨ Enhanced with energy controls
│   ├── PrimaryGeneratorMessenger.hh # ✨ New energy commands
│   └── ...
│
├── src/                        # C++ source files
│   ├── PrimaryGeneratorAction.cc   # ✨ Fixed/random energy system
│   ├── PrimaryGeneratorMessenger.cc# ✨ Macro command handlers
│   └── ...
│
├── macros/                     # ✨ Clean macro templates
│   ├── README.md               # Complete energy control guide
│   ├── muons_fixed_energy_template.mac
│   ├── muons_random_energy_template.mac
│   ├── electrons_template.mac
│   ├── test_fixed_energy.mac   # Quick test (5 events)
│   └── test_random_energy.mac  # Quick test (10 events)
│
├── build/                      # Build directory (generated)
│   ├── PhotonSim              # Compiled executable
│   └── *.root                 # Output ROOT files
│
├── tools/                     # ✨ Organized analysis tools
│   ├── create_multi_energy_3d_table.py  # Main: Build 3D table
│   ├── visualize_3d_table.py           # Main: Visualize table
│   │
│   ├── analysis/              # Physics analysis
│   │   ├── analyze_photon_data.py
│   │   ├── analyze_physics_processes.py
│   │   └── ...
│   │
│   ├── benchmarks/            # Performance testing
│   │   ├── benchmark_photonsim.py
│   │   └── visualize_benchmark.py
│   │
│   ├── photon_table/          # Table utilities
│   │   ├── create_photon_table.py
│   │   ├── query_photon_table.py
│   │   └── ...
│   │
│   ├── simulation/            # Simulation runners
│   │   ├── run_1k_muons.py
│   │   └── analyze_all_events.py
│   │
│   ├── table_analysis/        # Table development
│   │   ├── check_histogram_dims.py  # ✨ Moved from root
│   │   ├── create_3d_photon_table.py
│   │   └── ...
│   │
│   ├── validation/            # ✨ Energy & physics validation
│   │   ├── compare_energies.py     # ✨ Moved from root
│   │   ├── verify_energy_controls.py # ✨ New validation
│   │   ├── check_all_energies.py   # ✨ Energy debugging
│   │   └── physics_validation.py
│   │
│   └── visualization/         # ✨ Plotting & visualization
│       ├── show_photonsim_data.py   # ✨ Moved from root
│       ├── show_full_angular_range.py # ✨ Moved from root
│       └── visualize_photons.py
│
├── output/                    # All analysis outputs (gitignored)
│   ├── benchmarks/           # Performance results
│   ├── documentation/        # Analysis reports
│   └── visualizations/      # Generated plots
│
└── s3df_scripts/            # HPC cluster utilities
    ├── jobs/                # Batch job scripts
    └── utils/               # Setup and build scripts
```

## ✨ New Features & Fixes

### Energy Control System
PhotonSim now supports flexible energy control via macro commands:

**Fixed Energy (Default)**:
```bash
/gun/randomEnergy false
/gun/energy 300 MeV
```

**Random Energy**:
```bash
/gun/randomEnergy true
/gun/energyMin 100 MeV
/gun/energyMax 1000 MeV
```

### Muon Decay Inactivation
All muon macros automatically disable decay processes:
```bash
/particle/select mu-
/particle/process/inactivate 1
/particle/process/inactivate 7
/particle/select mu+
/particle/process/inactivate 1
```

### Bug Fix
**Fixed Critical Issue**: PhotonSim was ignoring `/gun/energy` commands and using random energies (100-500 MeV) by default. Now respects fixed energy settings.

## Key Data Products

### 🔬 **3D Lookup Table** (built in LUCiD)
ML-training input tables (`photon_lookup_table.h5`, `dedx_lookup_table.h5`)
are no longer produced inside this repo. PhotonSim writes the per-energy
ROOT files; the ROOT → HDF5 build lives in LUCiD. See
`LUCiD/docs/SIREN_TRAINING_INPUTS.md`.

## Quick Usage

### Run Simulations
```bash
cd build
./PhotonSim ../macros/test_fixed_energy.mac     # 5 events, 300 MeV
./PhotonSim ../macros/test_random_energy.mac    # 10 events, 200-800 MeV
```

### Analyze Data
```bash
# Create comprehensive 3D table
python tools/create_multi_energy_3d_table.py

# Visualize table
python tools/visualize_3d_table.py

# Validate energy controls
python tools/validation/verify_energy_controls.py
```

### Validate Energy System
```bash
# Check actual energies used
python tools/validation/check_all_energies.py

# Compare different energies
python tools/validation/compare_energies.py
```

## Development Workflow

1. **Simulation**: Use clean macro templates in `macros/`
2. **Analysis**: Tools organized by purpose in `tools/`
3. **Validation**: Energy and physics validation in `tools/validation/`
4. **Visualization**: All plotting tools in `tools/visualization/`
5. **Documentation**: Comprehensive guides in `macros/README.md`

## Data Generation

PhotonSim can generate comprehensive simulation data locally:
- **Energy Range**: 100-1000 MeV in configurable steps
- **Output**: ROOT files with optical photon and energy deposit data
- **HPC Support**: Batch job scripts for large-scale generation (`s3df_scripts/`)
- **ML Training Inputs**: ROOT outputs feed into LUCiD's table builders;
  see `LUCiD/docs/SIREN_TRAINING_INPUTS.md`.

## Integration Ready

- **diffCherenkov Integration**: JAX-native pipeline in place
- **Energy Control**: Flexible fixed/random energy generation
- **Clean Structure**: No scattered files, proper organization
- **Local Data Generation**: Tools for comprehensive energy coverage