#!/usr/bin/env python3
"""
Plot the current ROOT file data with detailed analysis.
"""

import numpy as np
import matplotlib.pyplot as plt
import uproot
import sys

def analyze_and_plot():
    """Analyze and plot the current optical_photons.root file."""
    
    # Try different possible locations
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
        print("Please run from the PhotonSim directory or provide the file path")
        return
    
    print(f"Found and analyzing: {root_file}")
    
    with uproot.open(root_file) as file:
        print(f"Available objects: {list(file.keys())}")
        
        # Create comprehensive plot
        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        
        # Check if we have the 2D histograms
        has_photon_hist = "PhotonHist_AngleDistance" in file
        has_edep_hist = "EdepHist_DistanceEnergy" in file
        has_tree = "OpticalPhotons" in file
        
        if has_photon_hist:
            # Main photon histogram
            hist = file["PhotonHist_AngleDistance"]
            values = hist.values()
            
            # Handle different uproot versions
            try:
                angle_edges = hist.axes[0].edges
                distance_edges = hist.axes[1].edges
            except:
                # Fallback for older uproot versions
                angle_edges = hist.axis(0).edges()
                distance_edges = hist.axis(1).edges()
            
            ax = axes[0, 0]
            extent = [angle_edges[0], angle_edges[-1], distance_edges[0], distance_edges[-1]]
            im = ax.imshow(values.T, origin='lower', aspect='auto', extent=extent, cmap='plasma')
            plt.colorbar(im, ax=ax, label='Count', shrink=0.8)
            
            ax.set_xlabel('Opening Angle (rad)')
            ax.set_ylabel('Distance (mm)')
            ax.set_title(f'Photon Distribution\n{values.sum():,.0f} total photons')
            
            # Mark Cherenkov angle
            ax.axvline(0.76, color='white', linestyle='--', alpha=0.8, label='Čerenkov ~43°')
            ax.legend()
            
            # Angular projection
            ax = axes[0, 1]
            angle_centers = (angle_edges[:-1] + angle_edges[1:]) / 2
            angle_proj = values.sum(axis=1)
            ax.plot(angle_centers, angle_proj, 'b-', linewidth=2)
            ax.fill_between(angle_centers, angle_proj, alpha=0.3)
            ax.set_xlabel('Opening Angle (rad)')
            ax.set_ylabel('Photon Count')
            ax.set_title('Angular Distribution')
            ax.grid(True, alpha=0.3)
            
            # Find and mark peak
            peak_idx = np.argmax(angle_proj)
            peak_angle = angle_centers[peak_idx]
            ax.axvline(peak_angle, color='red', linestyle='--', 
                      label=f'Peak: {peak_angle:.3f} rad\n({np.degrees(peak_angle):.1f}°)')
            ax.legend()
            
            # Distance projection
            ax = axes[1, 0]
            distance_centers = (distance_edges[:-1] + distance_edges[1:]) / 2
            distance_proj = values.sum(axis=0)
            ax.plot(distance_centers, distance_proj, 'g-', linewidth=2)
            ax.fill_between(distance_centers, distance_proj, alpha=0.3)
            ax.set_xlabel('Distance (mm)')
            ax.set_ylabel('Photon Count')
            ax.set_title('Radial Distribution')
            ax.grid(True, alpha=0.3)
            
            print(f"✓ Photon Analysis:")
            print(f"  Total photons: {values.sum():,.0f}")
            print(f"  Peak angle: {peak_angle:.3f} rad ({np.degrees(peak_angle):.1f}°)")
            print(f"  Non-zero bins: {np.count_nonzero(values):,}/{values.size:,} ({100*np.count_nonzero(values)/values.size:.1f}%)")
        
        if has_edep_hist:
            # Energy deposit histogram
            hist = file["EdepHist_DistanceEnergy"]
            values = hist.values()
            
            # Handle different uproot versions
            try:
                distance_edges = hist.axes[0].edges
                energy_edges = hist.axes[1].edges
            except:
                # Fallback for older uproot versions
                distance_edges = hist.axis(0).edges()
                energy_edges = hist.axis(1).edges()
            
            ax = axes[0, 2]
            extent = [distance_edges[0], distance_edges[-1], energy_edges[0], energy_edges[-1]]
            im = ax.imshow(values.T, origin='lower', aspect='auto', extent=extent, cmap='viridis')
            plt.colorbar(im, ax=ax, label='Count', shrink=0.8)
            
            ax.set_xlabel('Distance (mm)')
            ax.set_ylabel('Energy Deposit (keV)')
            ax.set_title(f'Energy Deposits\n{values.sum():,.0f} total deposits')
            
            # Energy projection
            ax = axes[1, 1]
            energy_centers = (energy_edges[:-1] + energy_edges[1:]) / 2
            energy_proj = values.sum(axis=0)
            ax.plot(energy_centers, energy_proj, 'r-', linewidth=2)
            ax.fill_between(energy_centers, energy_proj, alpha=0.3)
            ax.set_xlabel('Energy Deposit (keV)')
            ax.set_ylabel('Deposit Count')
            ax.set_title('Energy Distribution')
            ax.grid(True, alpha=0.3)
            
            # Calculate average energy
            total_energy = np.sum(values * energy_centers[:, np.newaxis].T)
            avg_energy = total_energy / values.sum() if values.sum() > 0 else 0
            ax.axvline(avg_energy, color='red', linestyle='--', 
                      label=f'Avg: {avg_energy:.1f} keV')
            ax.legend()
            
            print(f"✓ Energy Deposit Analysis:")
            print(f"  Total deposits: {values.sum():,.0f}")
            print(f"  Average energy: {avg_energy:.1f} keV")
            print(f"  Energy range: {energy_edges[0]:.1f} - {energy_edges[-1]:.1f} keV")
        
        # Tree information
        ax = axes[1, 2]
        ax.axis('off')
        
        if has_tree:
            tree = file["OpticalPhotons"]
            tree_data = tree.arrays(['EventID', 'PrimaryEnergy', 'NOpticalPhotons', 'NEnergyDeposits'], library='np')
            
            info_text = f"""
SIMULATION INFORMATION

Events: {len(tree_data['EventID'])}
Primary Energy: {tree_data['PrimaryEnergy'][0]:.0f} MeV

Per Event (Tree Data):
• Optical Photons: {tree_data['NOpticalPhotons'][0]:,}
• Energy Deposits: {tree_data['NEnergyDeposits'][0]:,}

Histogram Totals:
• Photon entries: {file['PhotonHist_AngleDistance'].values().sum():,.0f}
• Energy entries: {file['EdepHist_DistanceEnergy'].values().sum():,.0f}

Histogram Details:
• Size: 500 × 500 bins
• Physics: Čerenkov + Ionization
• Storage: {'Individual data OFF' if tree_data['NOpticalPhotons'][0] == 0 else 'Individual data ON'}

Quality Check:
• Čerenkov peak angle: {np.degrees(peak_angle):.1f}°
• Expected for water: ~43°
• Status: {'✓ Good' if 40 <= np.degrees(peak_angle) <= 50 else '⚠ Check medium'}
            """
            
            ax.text(0.05, 0.95, info_text, transform=ax.transAxes, 
                   fontsize=10, verticalalignment='top', fontfamily='monospace')
            
            print(f"✓ Run Information:")
            print(f"  Events: {len(tree_data['EventID'])}")
            print(f"  Primary energy: {tree_data['PrimaryEnergy'][0]:.0f} MeV")
            print(f"  Individual storage: {'OFF' if tree_data['NOpticalPhotons'][0] == 0 else 'ON'}")
        
        plt.suptitle('PhotonSim 2D Histogram Analysis', fontsize=16, y=0.98)
        plt.tight_layout()
        plt.subplots_adjust(top=0.93)
        
        # Save plot
        output_name = 'photonsim_analysis.png'
        plt.savefig(output_name, dpi=200, bbox_inches='tight')
        print(f"\n📊 Analysis plot saved as: {output_name}")
        
        plt.show()

if __name__ == '__main__':
    analyze_and_plot()