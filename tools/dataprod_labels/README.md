# Label-Based Data Production and Validation Tools

This directory contains tools for validating PhotonSim's label-based photon classification system.

## Overview

PhotonSim uses a label-based genealogy system to track photons by their origin. Each label represents a distinct physics category:
- **Primary (0)**: Primary beam particles
- **DecayElectron (1)**: Electrons from muon/pion decay
- **SecondaryPion (2)**: Secondary pions from hadronic interactions (above Cherenkov threshold)
- **GammaShower (3)**: Gamma showers from pi0 decay

## Files

### Test Macros
Standard test configurations for different particle types (1 GeV, 20 events each) in `test_macros/`:
- `test_macros/test_mu_minus.mac` - Negative muons
- `test_macros/test_mu_plus.mac` - Positive muons
- `test_macros/test_pi_minus.mac` - Negative pions
- `test_macros/test_pi_plus.mac` - Positive pions
- `test_macros/test_e_minus.mac` - Electrons
- `test_macros/test_e_plus.mac` - Positrons

### Validation Scripts

- `validate_photonsim_classification.py` - Validates label classification for any particle type
- `validate_photonsim_rotation.py` - Validates rotation invariance for any particle type
- `run_all_validation_tests.sh` - Master script to run all validation tests

### Analysis Tools
- `analyze_categories.py` - Statistical analysis of category distribution

## Usage

### Quick Start: Run All Validation Tests

From the PhotonSim root directory:
```bash
cd tools/dataprod_labels
./run_all_validation_tests.sh
```

This will:
1. Run PhotonSim for each particle type (mu-, mu+, pi-, pi+, e-, e+)
2. Generate 20 events per particle at 1 GeV
3. Create HTML visualizations for all events
4. Output files in `../../build/`

### Manual Validation

#### 1. Generate simulation data
```bash
cd build
./PhotonSim ../tools/dataprod_labels/test_macros/test_pi_minus.mac
```

#### 2. Run validation
```bash
# From build directory
python3 ../tools/dataprod_labels/validate_photonsim_classification.py test_pi_minus.root --events 20
```

#### 3. View results
Open the generated HTML files in a browser:
```bash
open photonsim_classification_event*.html
```

### Command-line Options

**validate_photonsim_classification.py**:
```bash
python3 validate_photonsim_classification.py <root_file> [options]

Required:
  root_file              Input ROOT file from PhotonSim

Optional:
  --events N             Number of events to validate (default: 50)
  --photons N            Photons to sample per label (default: 500)
  --seed N               Random seed for sampling (default: 42)
```

**validate_photonsim_rotation.py**:
```bash
python3 validate_photonsim_rotation.py <root_file> [options]

Required:
  root_file              Input ROOT file from PhotonSim

Optional:
  --events N1 N2 N3      Event indices to validate (default: 0 1 2)
  --photons N            Photons to sample per label (default: 500)
  --seed N               Random seed for sampling (default: 42)
```

## Output

### HTML Visualizations
Interactive 3D plots showing:
- Photon clouds color-coded by label
- Track positions and directions (toggle-able)
- Category and particle information in legend

### Console Statistics
Summary statistics including:
- Total events processed
- Primary particle types detected
- Category breakdown (counts, percentages, averages)

## Examples

### Validate specific events
```bash
python3 validate_photonsim_classification.py test_mu_minus.root --events 10
```

### Validate with custom photon sampling
```bash
python3 validate_photonsim_classification.py test_pi_plus.root --events 20 --photons 1000
```

### Test rotation for specific events
```bash
python3 validate_photonsim_rotation.py test_pi_minus.root --events 5 10 15
```

## Validation Checklist

When validating the classification system, check:

1. **Primary particles** - Correctly labeled as category 0
2. **Decay electrons** - Electrons from muon/pion decay labeled as category 1
3. **Secondary pions** - Pions above threshold from interactions labeled as category 2
4. **Gamma showers** - Gammas from pi0 decay labeled as category 3
5. **Deflection detection** - Kinks >5° properly split into separate labels
6. **Photon-track alignment** - Photon clouds aligned with track directions
7. **Rotation invariance** - Labels maintain structure after rotation

## Troubleshooting

### "Build directory not found"
Ensure PhotonSim is built:
```bash
cd build
cmake ..
make -j8
```

### "Module not found" errors
Ensure LUCiD is in your Python path:
```bash
export PYTHONPATH=/path/to/LUCiD:$PYTHONPATH
```

Or the scripts automatically add it via:
```python
sys.path.append('/Users/cjesus/Software/LUCiD')
```

### No HTML files generated
Check that:
- ROOT file contains photon data
- Plotly is installed: `pip install plotly`
- Events exist in the ROOT file

## Notes

- All test macros use random directions for statistical sampling
- Kinetic energy is displayed for all particles (not momentum)
- HTML files are saved in the current working directory
- The master script runs from the build directory
