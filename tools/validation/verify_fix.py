#!/usr/bin/env python3
"""
Verify that the energy fix worked.
"""

import uproot
import numpy as np

def verify_fixed_energies():
    """Check energies in the fixed file."""
    filename = "build/test_fixed_300MeV.root"
    
    with uproot.open(filename) as f:
        photons = f["OpticalPhotons"]
        primary_energies = photons["PrimaryEnergy"].array(library="np")
        
        print(f"=== VERIFICATION RESULTS ===")
        print(f"Number of events: {len(primary_energies)}")
        print(f"Energy range: {primary_energies.min():.3f} - {primary_energies.max():.3f} MeV")
        print(f"Mean energy: {primary_energies.mean():.3f} MeV")
        print(f"Standard deviation: {primary_energies.std():.6f} MeV")
        print(f"Expected: 300.000 MeV")
        
        # Check if all energies are exactly 300 MeV (within floating point precision)
        all_300 = np.allclose(primary_energies, 300.0, rtol=1e-10, atol=1e-6)
        print(f"All energies exactly 300 MeV: {all_300}")
        
        if all_300:
            print("✅ SUCCESS: PhotonSim is now using the correct fixed energy!")
        else:
            print("❌ ISSUE: Still seeing energy variations")
            print(f"Sample energies: {primary_energies[:5]}")

if __name__ == "__main__":
    verify_fixed_energies()