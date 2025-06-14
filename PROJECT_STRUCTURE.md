# PhotonSim Project Structure

Clean and organized structure for the PhotonSim Geant4 simulation and analysis tools.

## Directory Structure

```
PhotonSim/
├── README.md                    # Main project documentation
├── CMakeLists.txt              # Build configuration
├── PhotonSim.cc                # Main Geant4 application
├── requirements.txt            # Python dependencies
├── setup.sh                    # Environment setup
├── 1k_mu_optical_photons.root  # Data file (1000 muon events)
│
├── include/                    # C++ header files
├── src/                        # C++ source files  
├── macros/                     # Geant4 macro files
├── build/                      # Build directory
│
├── tools/                      # Analysis and utility tools
│   ├── README.md               # Tools overview
│   ├── create_photon_table.py  # Main: Create 3D lookup table
│   ├── query_photon_table.py   # Main: Query lookup table
│   │
│   ├── analysis/               # Data analysis scripts
│   ├── benchmarks/             # Performance benchmarking
│   ├── simulation/             # Simulation execution scripts  
│   ├── table_analysis/         # Table development scripts
│   ├── validation/             # Physics validation
│   └── visualization/          # Data visualization
│
└── output/                     # All outputs and results
    ├── README.md               # Output overview
    ├── photon_histogram_3d.npy # 3D lookup table
    ├── table_metadata.npz      # Table metadata
    ├── photon_table_analysis.png
    ├── energy_histogram.png
    │
    ├── benchmarks/             # Performance results
    │   ├── benchmark_results.json
    │   ├── runtime_vs_events.png
    │   └── ...
    │
    └── documentation/          # All documentation
        ├── PHOTON_TABLE_README.md
        ├── FINAL_ANALYSIS_SUMMARY.md
        └── ...
```

## Key Features

### ✅ **Clean Organization**
- **All Python scripts** organized in `tools/` subdirectories
- **All outputs** consolidated in `output/` 
- **All documentation** in `output/documentation/`
- **No scattered files** in root directory

### ✅ **Main Functionality**
- **`tools/create_photon_table.py`** - Create 3D Cherenkov photon lookup table
- **`tools/query_photon_table.py`** - Query the lookup table with interpolation
- **`output/`** - Single location for all results and documentation

### ✅ **3D Lookup Table**
- **95,000 photons** from 100 muon events
- **15×20×15 bins** with trilinear interpolation
- **Full energy range**: 101.7 - 498.1 MeV
- **26.6% parameter space coverage**

## Quick Usage

```bash
# Create the 3D photon lookup table
python3 tools/create_photon_table.py

# Query the table
python3 tools/query_photon_table.py --energy 300 --angle 0.3 --distance 1000 --stats

# All outputs saved to output/
```

## Development

- **Production scripts**: `tools/create_photon_table.py`, `tools/query_photon_table.py`
- **Development scripts**: `tools/table_analysis/` subdirectory  
- **Documentation**: `output/documentation/` for all guides and reports
- **Results**: `output/` for all analysis outputs and plots