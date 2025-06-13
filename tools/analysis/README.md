# PhotonSim Analysis Tools

This directory contains Python scripts for analyzing PhotonSim ROOT output data.

## Scripts

### analyze_primary_muon_photons.py
Specialized analysis for photons created directly by the primary muon (parentID=1).

**Features:**
- Filters for primary muon photons only
- Calculates perpendicular distances from photon creation points to muon track
- Generates comprehensive plots including track distance histograms
- Physics validation for Cherenkov radiation patterns

**Usage:**
```bash
python analyze_primary_muon_photons.py build/optical_photons.root
```

**Key Metrics:**
- Track distance distribution (should be millimeters for physical Cherenkov)
- Spatial distribution of photon creation points
- Time correlation analysis

### investigate_parents.py
Comprehensive investigation of parent-child particle relationships.

**Features:**
- Analyzes all photon parent IDs and particle types
- Identifies primary vs secondary photon sources
- Detailed breakdown of photon creation by parent particle
- Physics debugging for unphysical photon patterns

**Usage:**
```bash
python investigate_parents.py build/optical_photons.root
```

**Key Outputs:**
- Parent ID distribution
- Process analysis (Cerenkov vs Scintillation)
- Track ID range validation
- Sample photon positions for debugging

### analyze_photon_data.py
General-purpose photon data analysis script.

**Features:**
- Overall photon statistics
- Process and parent particle breakdown
- Spatial distribution analysis
- Distance calculations and boundary detection

**Usage:**
```bash
python analyze_photon_data.py build/optical_photons.root
```

## Dependencies

```bash
pip install uproot matplotlib numpy
```

## Expected Results

**Healthy Physics (after fix):**
- Primary muon photons: ~50-60% of total
- Track distances: mean ~10mm, max ~50mm
- All photons within centimeters of track
- No photons at detector boundaries

**Problematic Physics (before fix):**
- Photons appearing meters from track
- High concentration at detector boundaries (±50m)
- Unphysical Cherenkov patterns

## Troubleshooting

If you see photons at extreme distances (>1m from track):
1. Check if recording creation positions vs interaction positions
2. Verify GetVertexPosition() is used instead of GetPosition()
3. Examine parent particle tracking for secondary shower issues