#!/usr/bin/env python3
"""
Debug script to check actual energies in PhotonSim ROOT files.
"""

import uproot
import numpy as np
from pathlib import Path

def check_energy_in_file(filename, expected_energy):
    """Check what energy was actually used in a ROOT file."""
    print(f"\n=== Checking {filename} (expected: {expected_energy} MeV) ===")
    
    if not Path(filename).exists():
        print(f"File {filename} not found!")
        return
    
    with uproot.open(filename) as f:
        print(f"Keys in file: {list(f.keys())}")
        
        # Check if there's primary particle information
        if "OpticalPhotons" in f:
            photons = f["OpticalPhotons"]
            print(f"OpticalPhotons tree branches: {photons.keys()}")
            
            # Try to read some data to see what's available
            if len(photons.keys()) > 0:
                # Just read a small sample to see the structure
                arrays = photons.arrays(library="np", entry_stop=10)
                for key, array in arrays.items():
                    print(f"  {key}: shape={array.shape}, sample={array[:3] if len(array) > 0 else 'empty'}")
        
        # Look for any branches that might contain primary particle info
        for key in f.keys():
            if "Primary" in key or "Generator" in key or "Gun" in key:
                print(f"Found relevant key: {key}")
                try:
                    tree = f[key]
                    print(f"  Branches: {tree.keys()}")
                except:
                    print(f"  Could not read as tree")

def main():
    """Check energies in our test files."""
    files_to_check = [
        ("build/test_300MeV_histonly.root", 300),
        ("build/test_2000MeV_histonly.root", 2000)
    ]
    
    for filename, expected_energy in files_to_check:
        check_energy_in_file(filename, expected_energy)

if __name__ == "__main__":
    main()