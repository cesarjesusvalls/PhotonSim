# PhotonSim Analysis Tools

This directory contains Python tools for analyzing PhotonSim simulation data.

## Structure

- **`visualization/`**: Interactive 3D visualization tools
- **`validation/`**: Physics validation and analysis scripts

## Dependencies

Install required Python packages:

```bash
pip install uproot matplotlib numpy ipywidgets
```

## Quick Start

### Visualization
```bash
# Interactive 3D visualization
python visualization/visualize_photons.py ../build/optical_photons.root

# Example analysis with plots
python visualization/example_visualization.py
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