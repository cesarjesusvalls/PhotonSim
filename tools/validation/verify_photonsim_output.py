#!/usr/bin/env python3
"""
Simple verification script to check PhotonSim ROOT output structure.
This demonstrates the expected format for the LUCiD integration.
"""

import ROOT
import sys

def verify_photonsim_output(filename):
    """Verify and display the structure of a PhotonSim ROOT file."""
    print(f"\nVerifying PhotonSim output file: {filename}")
    print("=" * 80)
    
    # Open the ROOT file
    f = ROOT.TFile(filename)
    if not f or f.IsZombie():
        print("ERROR: Could not open ROOT file")
        return False
    
    # Get the tree
    tree = f.Get("OpticalPhotons")
    if not tree:
        print("ERROR: Could not find 'OpticalPhotons' tree")
        f.Close()
        return False
    
    print(f"\nTree 'OpticalPhotons' found with {tree.GetEntries()} entries")
    
    # List all branches
    print("\nBranches in the tree:")
    branches = tree.GetListOfBranches()
    for branch in branches:
        name = branch.GetName()
        title = branch.GetTitle()
        print(f"  - {name}: {title}")
    
    # Show data from first few events
    print("\n" + "-" * 80)
    print("Sample data from first 3 events:")
    print("-" * 80)
    print(f"{'Event':<8} {'Energy (MeV)':<15} {'# Photons':<12} {'# Edeps':<10}")
    print("-" * 80)
    
    for i in range(min(3, tree.GetEntries())):
        tree.GetEntry(i)
        print(f"{tree.EventID:<8} {tree.PrimaryEnergy:<15.2f} {tree.NOpticalPhotons:<12} {tree.NEnergyDeposits:<10}")
    
    # Show detailed info for first event
    print("\n" + "-" * 80)
    print("Detailed info for Event 0:")
    print("-" * 80)
    tree.GetEntry(0)
    
    print(f"Primary Energy: {tree.PrimaryEnergy:.2f} MeV")
    print(f"Number of Optical Photons: {tree.NOpticalPhotons}")
    
    # Check if individual photon data is available
    if hasattr(tree, 'PhotonPosX') and tree.PhotonPosX.size() > 0:
        print(f"\nFirst 5 photons:")
        print(f"{'Index':<8} {'Position (mm)':<30} {'Direction':<30}")
        print("-" * 70)
        
        for j in range(min(5, tree.PhotonPosX.size())):
            pos = f"({tree.PhotonPosX[j]:.1f}, {tree.PhotonPosY[j]:.1f}, {tree.PhotonPosZ[j]:.1f})"
            dir = f"({tree.PhotonDirX[j]:.3f}, {tree.PhotonDirY[j]:.3f}, {tree.PhotonDirZ[j]:.3f})"
            print(f"{j:<8} {pos:<30} {dir:<30}")
    
    print("\n" + "=" * 80)
    print("✓ PhotonSim output file verified successfully!")
    print("\nThis file is compatible with the LUCiD integration.")
    print("Use generate_events_from_photonsim() function in generate.py to process it.")
    
    f.Close()
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = "muons_50_with_photons.root"
    
    verify_photonsim_output(filename)