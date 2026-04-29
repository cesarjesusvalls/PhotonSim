# t0 correction

Calibration of PhotonSim's per-photon emission time as a function of
distance from the source and primary energy. The fit is over a sweep
of muon energies (10–2000 MeV, decays disabled, only the
`PhotonHist_TimeDistance` 2D histogram populated) and produces an
`(E, d) → t` parameterization that downstream consumers — notably
LUCiD's SIREN surrogate — can apply as a timing correction.

Self-contained PhotonSim tooling. No LUCiD dependency: the scripts
drive PhotonSim directly and the output is plain JSON.

## Workflow

```bash
# 1. Generate per-energy macros (10–2000 MeV mu-, 100 events each)
python3 generate_energy_scan_macros.py

# 2. Run PhotonSim against each generated macro
python3 run_energy_scan.py

# 3. Fit (E, d) → t from the histograms produced above
python3 calculate_t0.py
```

Each script accepts `--help` for input/output paths.

## Output

A JSON file containing baseline + delta-timing parameters keyed by
energy and distance. Plain text — any consumer can load it; LUCiD's
SIREN training pipeline is the current primary user.
