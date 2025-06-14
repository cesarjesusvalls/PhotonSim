#!/usr/bin/env python3
"""Quick test to check ROOT file structure and data size."""

import uproot
import numpy as np

def test_root_file():
    with uproot.open('1k_mu_optical_photons.root') as file:
        tree = file["OpticalPhotons"]
        
        print("Tree keys:", tree.keys())
        print("Number of events:", tree.num_entries)
        
        # Load just the first few events to test
        data = tree.arrays(['EventID', 'PrimaryEnergy', 'PhotonPosX', 'PhotonParent'], 
                          entry_stop=5, library="np")
        
        print("\nFirst 5 events:")
        for i in range(len(data['EventID'])):
            print(f"Event {data['EventID'][i]}, Energy: {data['PrimaryEnergy'][i]} MeV, "
                  f"Photons: {len(data['PhotonPosX'][i])}")
            print(f"  First few parents: {data['PhotonParent'][i][:10] if len(data['PhotonParent'][i]) > 0 else 'None'}")

if __name__ == "__main__":
    test_root_file()