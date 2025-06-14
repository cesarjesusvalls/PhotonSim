#!/usr/bin/env python3
"""
Simple visualization that works with different uproot versions.
"""

import numpy as np
import matplotlib.pyplot as plt
import uproot
import sys

def simple_plot(filename=None):
    """Create simple plots that work with any uproot version."""
    
    if filename:
        possible_files = [filename]
    else:
        # Find ROOT file
        possible_files = [
            "optical_photons.root",
            "../optical_photons.root", 
            "../../optical_photons.root",
            "../build/optical_photons.root"
        ]
    
    root_file = None
    for f in possible_files:
        try:
            with uproot.open(f) as test:
                root_file = f
                break
        except:
            continue
    
    if root_file is None:
        print("Could not find optical_photons.root file")
        return
    
    print(f"Plotting: {root_file}")
    
    with uproot.open(root_file) as file:
        objects = list(file.keys())
        print(f"Available: {objects}")
        
        fig, axes = plt.subplots(1, 2, figsize=(15, 6))
        
        # Plot photon histogram
        if "PhotonHist_AngleDistance" in file:
            hist = file["PhotonHist_AngleDistance"]
            values = hist.values()
            
            # Get histogram info manually
            print(f"Photon histogram shape: {values.shape}")
            print(f"Photon histogram entries: {values.sum():,.0f}")
            
            ax = axes[0]
            im = ax.imshow(values.T, origin='lower', aspect='auto', cmap='plasma')
            plt.colorbar(im, ax=ax, label='Photon Count')
            
            ax.set_xlabel('Angle Bin (0=0 rad, 500=π rad)')
            ax.set_ylabel('Distance Bin (0=0 mm, 500=10000 mm)')
            ax.set_title(f'Photon Distribution\n{values.sum():,.0f} total photons')
            
            # Find peak in angle projection
            angle_proj = values.sum(axis=1)
            peak_bin = np.argmax(angle_proj)
            peak_angle_rad = peak_bin * np.pi / 500  # Convert bin to radians
            
            ax.axvline(peak_bin, color='white', linestyle='--', alpha=0.8, 
                      label=f'Peak: bin {peak_bin} (~{np.degrees(peak_angle_rad):.1f}°)')
            ax.legend()
            
            print(f"Peak angle: bin {peak_bin} = {peak_angle_rad:.3f} rad = {np.degrees(peak_angle_rad):.1f}°")
        
        # Plot energy deposit histogram
        if "EdepHist_DistanceEnergy" in file:
            hist = file["EdepHist_DistanceEnergy"]
            values = hist.values()
            
            print(f"Energy histogram shape: {values.shape}")
            print(f"Energy histogram entries: {values.sum():,.0f}")
            
            ax = axes[1]
            im = ax.imshow(values.T, origin='lower', aspect='auto', cmap='viridis')
            plt.colorbar(im, ax=ax, label='Deposit Count')
            
            ax.set_xlabel('Distance Bin (0=0 mm, 500=10000 mm)')
            ax.set_ylabel('Energy Bin (0=0 keV, 500=1000 keV)')
            ax.set_title(f'Energy Deposits\n{values.sum():,.0f} total deposits')
            
            # Calculate average energy in bins
            energy_proj = values.sum(axis=0)
            total_energy_weighted = np.sum(energy_proj * np.arange(len(energy_proj)))
            avg_energy_bin = total_energy_weighted / energy_proj.sum() if energy_proj.sum() > 0 else 0
            avg_energy_kev = avg_energy_bin * 1000 / 500  # Convert bin to keV
            
            ax.axhline(avg_energy_bin, color='white', linestyle='--', alpha=0.8,
                      label=f'Avg: bin {avg_energy_bin:.0f} (~{avg_energy_kev:.1f} keV)')
            ax.legend()
            
            print(f"Average energy: bin {avg_energy_bin:.1f} = {avg_energy_kev:.1f} keV")
        
        # Check tree data
        if "OpticalPhotons" in file:
            tree = file["OpticalPhotons"]
            data = tree.arrays(['EventID', 'PrimaryEnergy', 'NOpticalPhotons'], library='np')
            
            print(f"\nTree information:")
            print(f"Events: {len(data['EventID'])}")
            print(f"Primary energy: {data['PrimaryEnergy'][0]:.0f} MeV")
            print(f"Individual photon storage: {'OFF' if data['NOpticalPhotons'][0] == 0 else 'ON'}")
            
            # Add text to plot
            fig.suptitle(f'PhotonSim Analysis - {len(data["EventID"])} events at {data["PrimaryEnergy"][0]:.0f} MeV', 
                        fontsize=14)
        
        plt.tight_layout()
        
        # Save
        output_name = 'simple_analysis.png'
        plt.savefig(output_name, dpi=150, bbox_inches='tight')
        print(f"\nPlot saved: {output_name}")
        
        plt.show()

if __name__ == '__main__':
    filename = sys.argv[1] if len(sys.argv) > 1 else None
    simple_plot(filename)