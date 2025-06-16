#!/usr/bin/env python3
"""
Create summary distribution plots comparing photon distributions across different energies.
Shows photons vs distance and photons vs angle for multiple energy levels.
"""

import numpy as np
import matplotlib.pyplot as plt
import uproot
from pathlib import Path

def load_histogram_data(root_file):
    """Load photon histogram data from ROOT file."""
    try:
        with uproot.open(root_file) as file:
            if "PhotonHist_AngleDistance" not in file:
                return None
            
            hist = file["PhotonHist_AngleDistance"]
            values = hist.values()
            
            # Get histogram edges
            angle_edges = hist.axes[0].edges()
            distance_edges = hist.axes[1].edges()
            
            return {
                'values': values,
                'angle_edges': angle_edges,
                'distance_edges': distance_edges,
                'total_photons': values.sum()
            }
    except Exception as e:
        print(f"Error loading {root_file}: {e}")
        return None

def create_summary_plots():
    """Create summary distribution plots for multiple energies."""
    # Select representative energies for comparison
    energies = [200, 300, 500, 700, 1000]  # MeV
    data_dir = Path("/Users/cjesus/Software/PhotonSim/data/mu-")
    
    # Load data for each energy
    energy_data = {}
    for energy in energies:
        root_file = data_dir / f"{energy}MeV" / "output.root"
        if root_file.exists():
            data = load_histogram_data(root_file)
            if data is not None:
                energy_data[energy] = data
                print(f"Loaded {energy} MeV: {data['total_photons']:,.0f} photons")
    
    if not energy_data:
        print("No valid data files found")
        return
    
    # Create figure with smaller size as preferred
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    
    colors = ['blue', 'green', 'red', 'orange', 'purple']
    
    # Plot 1: Photons vs Distance
    ax1.set_title('Photon Count vs Distance', fontsize=12)
    ax1.set_xlabel('Distance (mm)')
    ax1.set_ylabel('Photon Count')
    ax1.grid(True, alpha=0.3)
    
    for i, (energy, data) in enumerate(energy_data.items()):
        # Project onto distance axis (sum over angles)
        distance_centers = (data['distance_edges'][:-1] + data['distance_edges'][1:]) / 2
        distance_projection = data['values'].sum(axis=0)
        
        # Normalize for comparison
        distance_projection = distance_projection / distance_projection.max()
        
        ax1.plot(distance_centers, distance_projection, 
                color=colors[i % len(colors)], linewidth=2,
                label=f'{energy} MeV')
    
    ax1.legend()
    ax1.set_xlim(0, 3000)  # Focus on relevant distance range
    
    # Plot 2: Photons vs Angle
    ax2.set_title('Photon Count vs Opening Angle', fontsize=12)
    ax2.set_xlabel('Opening Angle (degrees)')
    ax2.set_ylabel('Photon Count')
    ax2.grid(True, alpha=0.3)
    
    for i, (energy, data) in enumerate(energy_data.items()):
        # Project onto angle axis (sum over distances)
        angle_centers = (data['angle_edges'][:-1] + data['angle_edges'][1:]) / 2
        angle_projection = data['values'].sum(axis=1)
        
        # Convert to degrees
        angle_degrees = np.degrees(angle_centers)
        
        # Normalize for comparison
        angle_projection = angle_projection / angle_projection.max()
        
        ax2.plot(angle_degrees, angle_projection,
                color=colors[i % len(colors)], linewidth=2,
                label=f'{energy} MeV')
    
    # Mark expected Cherenkov angle (~43°)
    ax2.axvline(43, color='black', linestyle='--', alpha=0.5, label='Expected Čerenkov')
    ax2.legend()
    ax2.set_xlim(0, 90)  # Focus on relevant angle range
    
    plt.tight_layout()
    
    # Save plot
    output_file = 'energy_comparison_summary.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\nSummary plot saved: {output_file}")
    
    plt.show()

if __name__ == '__main__':
    create_summary_plots()