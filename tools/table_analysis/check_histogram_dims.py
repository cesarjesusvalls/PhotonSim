#!/usr/bin/env python3
import uproot
import sys

file_path = sys.argv[1] if len(sys.argv) > 1 else "data/mu-/100MeV/output.root"

with uproot.open(file_path) as f:
    if "PhotonHist_AngleDistance" in f:
        hist = f["PhotonHist_AngleDistance"]
        print(f"Histogram shape: {hist.values().shape}")
        print(f"X-axis (angle) bins: {len(hist.axis(0).edges())-1}")
        print(f"Y-axis (distance) bins: {len(hist.axis(1).edges())-1}")
        print(f"X-axis range: {hist.axis(0).edges()[0]:.3f} to {hist.axis(0).edges()[-1]:.3f}")
        print(f"Y-axis range: {hist.axis(1).edges()[0]:.3f} to {hist.axis(1).edges()[-1]:.3f}")