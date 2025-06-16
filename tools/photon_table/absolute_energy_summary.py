#!/usr/bin/env python3
"""
Create summary distribution plots showing absolute photon counts across different energies.
Shows both normalized and absolute comparisons.
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

def create_absolute_summary():
    """Create summary plots with absolute photon counts."""
    # Select representative energies
    energies = [200, 300, 500, 700, 1000]  # MeV
    data_dir = Path("/Users/cjesus/Software/PhotonSim/data/mu-")
    
    # Load data
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
    
    # Create figure
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))
    
    colors = ['blue', 'green', 'red', 'orange', 'purple']
    
    # Plot 1: Normalized Distance Distribution
    ax1.set_title('Photon Distribution vs Distance (Normalized)', fontsize=11)
    ax1.set_xlabel('Distance (mm)')
    ax1.set_ylabel('Normalized Count')
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Absolute Distance Distribution
    ax2.set_title('Photon Count vs Distance (Absolute)', fontsize=11)
    ax2.set_xlabel('Distance (mm)')
    ax2.set_ylabel('Photon Count (millions)')
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Normalized Angle Distribution
    ax3.set_title('Photon Distribution vs Angle (Normalized)', fontsize=11)
    ax3.set_xlabel('Opening Angle (degrees)')
    ax3.set_ylabel('Normalized Count')
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Absolute Angle Distribution
    ax4.set_title('Photon Count vs Angle (Absolute)', fontsize=11)
    ax4.set_xlabel('Opening Angle (degrees)')
    ax4.set_ylabel('Photon Count (millions)')
    ax4.grid(True, alpha=0.3)
    
    for i, (energy, data) in enumerate(energy_data.items()):
        color = colors[i % len(colors)]
        
        # Distance projections
        distance_centers = (data['distance_edges'][:-1] + data['distance_edges'][1:]) / 2
        distance_projection = data['values'].sum(axis=0)
        
        # Normalized distance
        norm_distance = distance_projection / distance_projection.max()
        ax1.plot(distance_centers, norm_distance, color=color, linewidth=2, label=f'{energy} MeV')
        
        # Absolute distance (in millions)
        abs_distance = distance_projection / 1e6
        ax2.plot(distance_centers, abs_distance, color=color, linewidth=2, label=f'{energy} MeV')
        
        # Angle projections
        angle_centers = (data['angle_edges'][:-1] + data['angle_edges'][1:]) / 2
        angle_projection = data['values'].sum(axis=1)
        angle_degrees = np.degrees(angle_centers)
        
        # Normalized angle
        norm_angle = angle_projection / angle_projection.max()
        ax3.plot(angle_degrees, norm_angle, color=color, linewidth=2, label=f'{energy} MeV')
        
        # Absolute angle (in millions)
        abs_angle = angle_projection / 1e6
        ax4.plot(angle_degrees, abs_angle, color=color, linewidth=2, label=f'{energy} MeV')
    
    # Set limits and add legends
    ax1.set_xlim(0, 3000)
    ax1.legend(fontsize=9)
    
    ax2.set_xlim(0, 3000)
    ax2.legend(fontsize=9)
    
    ax3.set_xlim(0, 90)
    ax3.axvline(43, color='black', linestyle='--', alpha=0.5, label='Expected Čerenkov')
    ax3.legend(fontsize=9)
    
    ax4.set_xlim(0, 90)
    ax4.axvline(43, color='black', linestyle='--', alpha=0.5, label='Expected Čerenkov')
    ax4.legend(fontsize=9)
    
    plt.tight_layout()
    
    # Save plot
    output_file = 'absolute_energy_summary.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\nAbsolute summary plot saved: {output_file}")
    
    # Print scaling information
    print(f"\n=== ENERGY SCALING ANALYSIS ===")
    base_energy = min(energy_data.keys())
    base_photons = energy_data[base_energy]['total_photons']
    
    for energy in sorted(energy_data.keys()):
        total = energy_data[energy]['total_photons']
        scaling = total / base_photons
        expected_scaling = (energy / base_energy) ** 2  # Approximate expectation
        print(f"{energy:4d} MeV: {total:12,.0f} photons | {scaling:5.2f}x scaling | Expected ~{expected_scaling:.2f}x")
    
    plt.show()

if __name__ == '__main__':
    create_absolute_summary()