#!/usr/bin/env python3
"""
Verify the new energy control functionality.
"""

import uproot
import numpy as np
import matplotlib.pyplot as plt

def analyze_file(filename, label, expected_behavior):
    """Analyze energies in a ROOT file."""
    print(f"\n=== {label} ===")
    
    with uproot.open(filename) as f:
        photons = f["OpticalPhotons"]
        primary_energies = photons["PrimaryEnergy"].array(library="np")
        
        print(f"Number of events: {len(primary_energies)}")
        print(f"Energy range: {primary_energies.min():.1f} - {primary_energies.max():.1f} MeV")
        print(f"Mean energy: {primary_energies.mean():.1f} MeV")
        print(f"Standard deviation: {primary_energies.std():.3f} MeV")
        print(f"Expected: {expected_behavior}")
        
        return primary_energies

def main():
    """Verify both energy control modes."""
    plt.figure(figsize=(12, 5))
    
    # Test fixed energy
    plt.subplot(1, 2, 1)
    energies_fixed = analyze_file("build/test_fixed_energy.root", 
                                 "Fixed Energy (300 MeV)", 
                                 "All exactly 300 MeV")
    
    plt.hist(energies_fixed, bins=10, alpha=0.7, color='blue', edgecolor='black')
    plt.axvline(300, color='red', linestyle='--', linewidth=2, label='Target: 300 MeV')
    plt.xlabel('Primary Energy (MeV)')
    plt.ylabel('Count')
    plt.title('Fixed Energy Test')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Test random energy
    plt.subplot(1, 2, 2)
    energies_random = analyze_file("build/test_random_energy.root", 
                                  "Random Energy (200-800 MeV)", 
                                  "Uniformly distributed 200-800 MeV")
    
    plt.hist(energies_random, bins=10, alpha=0.7, color='green', edgecolor='black')
    plt.axvline(200, color='red', linestyle='--', linewidth=2, label='Min: 200 MeV')
    plt.axvline(800, color='red', linestyle='--', linewidth=2, label='Max: 800 MeV')
    plt.axvline(energies_random.mean(), color='orange', linestyle='-', linewidth=2, 
                label=f'Mean: {energies_random.mean():.1f} MeV')
    plt.xlabel('Primary Energy (MeV)')
    plt.ylabel('Count')
    plt.title('Random Energy Test')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    
    # Validation
    print(f"\n🔍 VALIDATION:")
    
    # Fixed energy validation
    fixed_correct = np.allclose(energies_fixed, 300.0, rtol=1e-10, atol=1e-6)
    print(f"✅ Fixed energy working: {fixed_correct}")
    
    # Random energy validation
    in_range = np.all((energies_random >= 200) & (energies_random <= 800))
    reasonable_spread = energies_random.std() > 50  # Should have significant variation
    print(f"✅ Random energy in range [200, 800]: {in_range}")
    print(f"✅ Random energy has good spread: {reasonable_spread} (std = {energies_random.std():.1f})")
    
    if fixed_correct and in_range and reasonable_spread:
        print(f"\n🎉 SUCCESS: Energy control system working perfectly!")
        print(f"PhotonSim now supports both fixed and random energy generation via macro commands.")
    else:
        print(f"\n❌ ISSUE: Some validation failed")

if __name__ == "__main__":
    main()