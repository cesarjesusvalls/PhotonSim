# PhotonSim Analysis Tools

This directory contains Python tools for analyzing PhotonSim simulation data.

## Structure

- **`visualization/`**: Interactive 3D visualization tools
- **`analysis/`**: Python analysis scripts for photons and energy deposits  
- **`validation/`**: Physics validation and analysis scripts

## Dependencies

Install required Python packages:

```bash
pip install uproot matplotlib numpy ipywidgets
```

## Quick Start

### Visualization
```bash
# Interactive 3D optical photon visualization
python visualization/visualize_photons.py ../build/optical_photons.root

# Interactive 3D energy deposit visualization  
python visualization/visualize_energy_deposits.py ../build/optical_photons.root

# Example analysis with plots
python visualization/example_visualization.py
```

### Analysis
```bash
# Analyze physics processes generating photons
python analysis/analyze_physics_processes.py ../build/optical_photons.root

# Focus on primary muon photons and track distances
python analysis/analyze_primary_muon_photons.py ../build/optical_photons.root

# Analyze energy deposits for scintillation modeling
python analysis/analyze_energy_deposits.py ../build/optical_photons.root

# Comprehensive parent-child particle investigation  
python analysis/investigate_parents.py ../build/optical_photons.root
```

### Physics Validation
```bash
# Quick physics summary
python validation/physics_summary.py

# Comprehensive validation
python validation/final_physics_check.py

# Detailed analysis
python validation/physics_validation.py
python validation/detailed_validation.py
```

## File Descriptions

### Visualization Tools
- **`visualize_photons.py`**: Main interactive 3D visualization class
- **`example_visualization.py`**: Example analysis with statistics and plots

### Validation Tools
- **`physics_summary.py`**: Quick physics validation summary
- **`final_physics_check.py`**: Comprehensive Cerenkov physics validation
- **`physics_validation.py`**: Detailed time/distance analysis
- **`detailed_validation.py`**: Deep dive into apparent speed-of-light violations

## Usage from Root Directory

All tools can be run from the PhotonSim root directory:

```bash
# From PhotonSim root
python tools/visualization/visualize_photons.py build/optical_photons.root
python tools/validation/physics_summary.py
```