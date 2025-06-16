#!/usr/bin/env python3
"""
Visualize the 3D lookup table structure.
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def visualize_3d_table():
    """Load and visualize the 3D lookup table."""
    table_dir = Path("output/3d_lookup_table_corrected")
    
    # Load table and metadata
    table = np.load(table_dir / "photon_table_3d.npy")
    metadata = np.load(table_dir / "table_metadata.npz")
    
    print(f"3D Table loaded:")
    print(f"Shape: {table.shape}")
    print(f"Total photons: {table.sum():,.0f}")
    print(f"Non-zero bins: {np.count_nonzero(table):,}")
    print(f"Energy values: {len(metadata['energy_values'])} energies from {metadata['energy_values'][0]} to {metadata['energy_values'][-1]} MeV")
    
    # Create visualizations
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # 1. Energy scaling plot
    ax = axes[0, 0]
    energies = metadata['energy_values']
    total_photons_per_energy = table.sum(axis=(1, 2))
    
    # Only plot non-zero values
    mask = total_photons_per_energy > 0
    ax.plot(energies[mask], total_photons_per_energy[mask] / 1e6, 'b-', linewidth=2, marker='o')
    ax.set_xlabel('Energy (MeV)')
    ax.set_ylabel('Total Photons (millions)')
    ax.set_title('Photon Production vs Energy')
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 700)  # Focus on available data
    
    # 2. Sample 2D slices at different energies
    sample_energies = [200, 300, 500]
    for i, energy in enumerate(sample_energies):
        ax = axes[0, 1] if i == 0 else (axes[1, 0] if i == 1 else axes[1, 1])
        
        # Find closest energy index
        idx = np.argmin(np.abs(energies - energy))
        actual_energy = energies[idx]
        
        # Get 2D slice
        slice_2d = table[idx]
        
        # Plot with proper extent
        angle_edges = metadata['angle_edges']
        distance_edges = metadata['distance_edges']
        
        im = ax.imshow(slice_2d.T, origin='lower', aspect='auto', cmap='viridis',
                      extent=[0, np.degrees(angle_edges[-1]), 0, distance_edges[-1]],
                      interpolation='nearest')
        
        ax.set_xlabel('Opening Angle (degrees)')
        ax.set_ylabel('Distance (mm)')
        ax.set_title(f'{actual_energy:.0f} MeV: {slice_2d.sum():.1e} photons')
        ax.set_xlim(0, 90)
        ax.set_ylim(0, 3000)
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Photon Count', rotation=270, labelpad=15)
        
        # Mark Cherenkov angle
        ax.axvline(43, color='red', linestyle='--', alpha=0.7, linewidth=1)
    
    plt.suptitle('3D Lookup Table Visualization', fontsize=14)
    plt.tight_layout()
    
    plt.savefig('3d_table_visualization.png', dpi=150, bbox_inches='tight')
    print("\nVisualization saved: 3d_table_visualization.png")
    plt.show()
    
    # Additional analysis
    print("\n=== Table Analysis ===")
    
    # Find energy range with data
    valid_energies = energies[total_photons_per_energy > 0]
    print(f"Valid energy range: {valid_energies[0]}-{valid_energies[-1]} MeV ({len(valid_energies)} energies)")
    
    # Memory usage
    memory_mb = table.nbytes / 1024 / 1024
    print(f"Memory usage: {memory_mb:.1f} MB")
    
    # Sparsity
    sparsity = 1 - np.count_nonzero(table) / table.size
    print(f"Sparsity: {sparsity*100:.1f}%")
    
    # Peak location analysis
    for energy in [200, 300, 500]:
        idx = np.argmin(np.abs(energies - energy))
        slice_2d = table[idx]
        
        # Find peak in angle projection
        angle_projection = slice_2d.sum(axis=1)
        peak_angle_idx = np.argmax(angle_projection)
        peak_angle = np.degrees(metadata['angle_centers'][peak_angle_idx])
        
        print(f"\n{energies[idx]:.0f} MeV:")
        print(f"  Peak angle: {peak_angle:.1f}°")
        print(f"  Total photons: {slice_2d.sum():.2e}")

if __name__ == '__main__':
    visualize_3d_table()