# PhotonSim Tools

Collection of analysis and utility tools for PhotonSim.

## Main Scripts

### Photon Table Creation
- **`create_photon_table.py`** - Create 3D Cherenkov photon lookup table
- **`query_photon_table.py`** - Query the 3D lookup table

### Usage
```bash
# Create table using all events
python3 tools/create_photon_table.py

# Query table
python3 tools/query_photon_table.py --energy 300 --angle 0.3 --distance 1000 --stats
```

## Subdirectories

- **`analysis/`** - Data analysis scripts
- **`benchmarks/`** - Performance benchmarking tools  
- **`simulation/`** - Simulation execution scripts
- **`table_analysis/`** - Development scripts for table creation
- **`validation/`** - Physics validation scripts
- **`visualization/`** - Data visualization tools

## Output

All outputs are saved to the `output/` directory:
- `output/` - Main table and analysis results
- `output/benchmarks/` - Performance data and plots
- `output/documentation/` - Documentation and README files

See `output/documentation/` for detailed documentation of each tool category.