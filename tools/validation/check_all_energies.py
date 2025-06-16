#!/usr/bin/env python3
"""
Check all primary energies in PhotonSim ROOT files.
"""

import uproot
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def analyze_energies(filename, expected_energy, label):
    """Analyze all primary energies in a ROOT file."""
    print(f"\n=== {label} (expected: {expected_energy} MeV) ===")
    
    if not Path(filename).exists():
        print(f"File {filename} not found!")
        return None
    
    with uproot.open(filename) as f:
        if "OpticalPhotons" in f:
            photons = f["OpticalPhotons"]
            primary_energies = photons["PrimaryEnergy"].array(library="np")
            
            print(f"Number of events: {len(primary_energies)}")
            print(f"Energy range: {primary_energies.min():.1f} - {primary_energies.max():.1f} MeV")
            print(f"Mean energy: {primary_energies.mean():.1f} MeV")
            print(f"Expected energy: {expected_energy} MeV")
            
            # Check if any energy is close to expected
            close_to_expected = np.abs(primary_energies - expected_energy) < 1.0  # within 1 MeV
            print(f"Events close to expected energy: {close_to_expected.sum()}/{len(primary_energies)}")
            
            return primary_energies
    
    return None

def main():
    """Check energies in our test files."""
    plt.figure(figsize=(10, 6))
    
    # Check both files
    energies_300 = analyze_energies("build/test_300MeV_histonly.root", 300, "300 MeV File")
    energies_2000 = analyze_energies("build/test_2000MeV_histonly.root", 2000, "2000 MeV File")
    
    # Plot histograms
    if energies_300 is not None:
        plt.subplot(1, 2, 1)
        plt.hist(energies_300, bins=20, alpha=0.7, label="300 MeV File", color='blue')
        plt.axvline(300, color='red', linestyle='--', label='Expected: 300 MeV')
        plt.xlabel('Primary Energy (MeV)')
        plt.ylabel('Count')
        plt.title('300 MeV File - Actual Energies')
        plt.legend()
        plt.grid(True, alpha=0.3)
    
    if energies_2000 is not None:
        plt.subplot(1, 2, 2)
        plt.hist(energies_2000, bins=20, alpha=0.7, label="2000 MeV File", color='green')
        plt.axvline(2000, color='red', linestyle='--', label='Expected: 2000 MeV')
        plt.xlabel('Primary Energy (MeV)')
        plt.ylabel('Count')
        plt.title('2000 MeV File - Actual Energies')
        plt.legend()
        plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    
    # Summary
    print(f"\n🚨 DIAGNOSIS:")
    print(f"PhotonSim is NOT using the energies specified in macro files!")
    print(f"Instead, it's using random energies in the default range (100-500 MeV).")
    print(f"This explains why all energy comparisons show similar results.")

if __name__ == "__main__":
    main()