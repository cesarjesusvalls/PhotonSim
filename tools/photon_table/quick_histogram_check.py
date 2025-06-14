#!/usr/bin/env python3
"""
Quick check of 2D histograms in ROOT file.
"""

import uproot
import numpy as np
import sys

def check_histograms(root_file):
    """Quick check of 2D histograms."""
    with uproot.open(root_file) as file:
        print(f"ROOT file: {root_file}")
        print(f"Objects: {list(file.keys())}")
        print()
        
        # Check photon histogram
        if "PhotonHist_AngleDistance" in file:
            hist = file["PhotonHist_AngleDistance"]
            values = hist.values()
            print(f"Photon Histogram (Angle vs Distance):")
            print(f"  Shape: {values.shape}")
            print(f"  Total entries: {values.sum():,.0f}")
            print(f"  Non-zero bins: {np.count_nonzero(values):,} ({100*np.count_nonzero(values)/values.size:.1f}%)")
            print(f"  Max bin count: {values.max():,.0f}")
            print()
        
        # Check energy deposit histogram  
        if "EdepHist_DistanceEnergy" in file:
            hist = file["EdepHist_DistanceEnergy"]
            values = hist.values()
            print(f"Energy Deposit Histogram (Distance vs Energy):")
            print(f"  Shape: {values.shape}")
            print(f"  Total entries: {values.sum():,.0f}")
            print(f"  Non-zero bins: {np.count_nonzero(values):,} ({100*np.count_nonzero(values)/values.size:.1f}%)")
            print(f"  Max bin count: {values.max():,.0f}")
            print()
        
        # Check TTree (should have empty vectors if storage disabled)
        if "OpticalPhotons" in file:
            tree = file["OpticalPhotons"]
            print(f"TTree 'OpticalPhotons':")
            print(f"  Entries: {tree.num_entries}")
            
            # Check a few events
            data = tree.arrays(['NOpticalPhotons', 'NEnergyDeposits', 'PhotonPosX'], library='np')
            print(f"  Event 0 - NOpticalPhotons: {data['NOpticalPhotons'][0]}, PhotonPosX length: {len(data['PhotonPosX'][0])}")
            print(f"  Event 1 - NOpticalPhotons: {data['NOpticalPhotons'][1]}, PhotonPosX length: {len(data['PhotonPosX'][1])}")
            print("  (If PhotonPosX length is 0, individual storage is working correctly)")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        check_histograms(sys.argv[1])
    else:
        check_histograms("optical_photons.root")