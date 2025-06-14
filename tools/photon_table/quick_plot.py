#!/usr/bin/env python3
"""
Quick and simple visualization of 2D histograms from PhotonSim ROOT files.
"""

import numpy as np
import matplotlib.pyplot as plt
import uproot
import sys

def quick_plot(root_file):
    """Create quick plots of both histograms."""
    with uproot.open(root_file) as file:
        print(f"Plotting histograms from: {root_file}")
        
        # Check available objects
        objects = list(file.keys())
        print(f"Available: {objects}")
        
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        
        # Plot photon histogram
        if "PhotonHist_AngleDistance" in file:
            hist = file["PhotonHist_AngleDistance"]
            values = hist.values()
            angle_edges = hist.axes[0].edges
            distance_edges = hist.axes[1].edges
            
            ax = axes[0]
            extent = [angle_edges[0], angle_edges[-1], distance_edges[0], distance_edges[-1]]
            im = ax.imshow(values.T, origin='lower', aspect='auto', extent=extent, cmap='plasma')
            plt.colorbar(im, ax=ax, label='Photon Count')
            
            ax.set_xlabel('Opening Angle (rad)')
            ax.set_ylabel('Distance (mm)')
            ax.set_title(f'Photon Distribution\n{values.sum():,.0f} photons, {values.shape} bins')
            
            # Mark typical Cherenkov angle
            ax.axvline(0.76, color='white', linestyle='--', alpha=0.8, label='Čerenkov ~43°')
            ax.legend()
            
            print(f"Photon histogram: {values.sum():,.0f} entries, max={values.max():,.0f}")
        
        # Plot energy deposit histogram
        if "EdepHist_DistanceEnergy" in file:
            hist = file["EdepHist_DistanceEnergy"]
            values = hist.values()
            distance_edges = hist.axes[0].edges
            energy_edges = hist.axes[1].edges
            
            ax = axes[1]
            extent = [distance_edges[0], distance_edges[-1], energy_edges[0], energy_edges[-1]]
            im = ax.imshow(values.T, origin='lower', aspect='auto', extent=extent, cmap='viridis')
            plt.colorbar(im, ax=ax, label='Deposit Count')
            
            ax.set_xlabel('Distance (mm)')
            ax.set_ylabel('Energy Deposit (keV)')
            ax.set_title(f'Energy Deposits\n{values.sum():,.0f} deposits, {values.shape} bins')
            
            print(f"Energy histogram: {values.sum():,.0f} entries, max={values.max():,.0f}")
        
        plt.tight_layout()
        plt.savefig('quick_plot.png', dpi=150, bbox_inches='tight')
        print("Plot saved as: quick_plot.png")
        plt.show()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        quick_plot(sys.argv[1])
    else:
        quick_plot("optical_photons.root")