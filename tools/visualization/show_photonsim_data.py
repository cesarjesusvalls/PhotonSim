#!/usr/bin/env python3
"""
Quick visualization of PhotonSim data with smaller figures for display.
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def load_and_show_data(table_dir="output/3d_lookup_table"):
    """Load and show PhotonSim data visualizations."""
    table_path = Path(table_dir)
    
    # Load the 3D table and metadata
    print("Loading PhotonSim 3D lookup table...")
    photon_table = np.load(table_path / "photon_table_3d.npy")
    metadata = np.load(table_path / "table_metadata.npz")
    
    energy_values = metadata['energy_values']
    angle_centers = metadata['angle_centers']
    distance_centers = metadata['distance_centers']
    
    print(f"Table shape: {photon_table.shape}")
    print(f"Energy range: {energy_values[0]}-{energy_values[-1]} MeV")
    print(f"Angle range: {angle_centers[0]:.3f}-{angle_centers[-1]:.3f} rad")
    print(f"Distance range: {distance_centers[0]:.1f}-{distance_centers[-1]:.1f} mm")
    print(f"Total photons: {photon_table.sum():.2e}")
    
    # Create visualizations with smaller figure sizes
    plt.style.use('default')
    
    # 1. Energy slices showing different energies
    print("\n1. Energy Slices (Angle vs Distance at different energies):")
    fig, axes = plt.subplots(2, 3, figsize=(12, 8))  # Smaller than original
    axes = axes.flatten()
    
    energy_indices = [0, 18, 36, 54, 72, 90]  # 100, 280, 460, 640, 820, 1000 MeV
    
    for i, idx in enumerate(energy_indices):
        ax = axes[i]
        energy = energy_values[idx]
        
        # Get 2D histogram for this energy and apply log scale
        hist_2d = photon_table[idx]
        hist_2d_log = np.log10(hist_2d + 1)
        
        # Downsample for visualization
        downsample = 20  # More aggressive downsampling
        hist_2d_down = hist_2d_log[::downsample, ::downsample]
        angle_down = angle_centers[::downsample]
        distance_down = distance_centers[::downsample]
        
        im = ax.imshow(hist_2d_down.T, origin='lower', aspect='auto', 
                      cmap='viridis',
                      extent=[angle_down[0], angle_down[-1], 
                             distance_down[0], distance_down[-1]])
        
        ax.set_xlabel('Opening Angle (rad)')
        ax.set_ylabel('Distance (mm)')
        ax.set_title(f'{energy} MeV')
        
        # Focus on small angles for Cherenkov
        ax.set_xlim(0, 0.1)
        ax.set_ylim(0, 3000)
        
        plt.colorbar(im, ax=ax, label='log₁₀(Count+1)')
    
    plt.suptitle('Cherenkov Photon Distribution vs Energy', fontsize=14)
    plt.tight_layout()
    plt.show()
    
    # 2. 1D projections
    print("\n2. 1D Projections:")
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))  # Smaller figure
    
    # Energy projection
    energy_projection = np.sum(photon_table, axis=(1, 2))
    axes[0].plot(energy_values, energy_projection, 'b-', linewidth=2)
    axes[0].set_xlabel('Energy (MeV)')
    axes[0].set_ylabel('Total Photon Count')
    axes[0].set_title('Total Photons vs Energy')
    axes[0].grid(True, alpha=0.3)
    
    # Angle projection (focus on small angles)
    angle_projection = np.sum(photon_table, axis=(0, 2))
    # Focus on first 50 bins (small angles)
    angle_focused = angle_centers[:50]
    angle_proj_focused = angle_projection[:50]
    axes[1].plot(angle_focused, angle_proj_focused, 'g-', linewidth=2)
    axes[1].set_xlabel('Opening Angle (rad)')
    axes[1].set_ylabel('Total Photon Count')
    axes[1].set_title('Photons vs Angle (Cherenkov Peak)')
    axes[1].grid(True, alpha=0.3)
    
    # Distance projection (focus on main region)
    distance_projection = np.sum(photon_table, axis=(0, 1))
    # Focus on first 100 bins (main region)
    distance_focused = distance_centers[:100] 
    distance_proj_focused = distance_projection[:100]
    axes[2].plot(distance_focused, distance_proj_focused, 'r-', linewidth=2)
    axes[2].set_xlabel('Distance (mm)')
    axes[2].set_ylabel('Total Photon Count')
    axes[2].set_title('Photons vs Distance')
    axes[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    
    # 3. Cherenkov physics analysis
    print("\n3. Cherenkov Physics Analysis:")
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))  # Smaller figure
    
    # Peak angle vs energy
    peak_angles = []
    for i in range(len(energy_values)):
        angle_dist = np.sum(photon_table[i], axis=1)
        # Find peak in first 50 bins (small angles only)
        peak_idx = np.argmax(angle_dist[:50])
        peak_angles.append(angle_centers[peak_idx])
    
    axes[0,0].plot(energy_values, peak_angles, 'k-', linewidth=2, marker='o', markersize=3)
    axes[0,0].set_xlabel('Energy (MeV)')
    axes[0,0].set_ylabel('Peak Angle (rad)')
    axes[0,0].set_title('Cherenkov Angle vs Energy')
    axes[0,0].grid(True, alpha=0.3)
    
    # Energy vs angle heatmap
    proj_ea = np.sum(photon_table, axis=2)
    # Focus on small angles
    proj_ea_focused = proj_ea[:, :50]
    im = axes[0,1].imshow(np.log10(proj_ea_focused.T + 1), origin='lower', 
                         aspect='auto', cmap='viridis',
                         extent=[energy_values[0], energy_values[-1], 
                                angle_centers[0], angle_centers[49]])
    axes[0,1].set_xlabel('Energy (MeV)')
    axes[0,1].set_ylabel('Opening Angle (rad)')
    axes[0,1].set_title('Energy vs Angle (Cherenkov Cone)')
    plt.colorbar(im, ax=axes[0,1], label='log₁₀(Count+1)')
    
    # Angle distributions for selected energies
    selected_energies = [100, 300, 500, 700, 900]
    colors = plt.cm.viridis(np.linspace(0, 1, len(selected_energies)))
    
    for energy, color in zip(selected_energies, colors):
        idx = np.argmin(np.abs(energy_values - energy))
        angle_dist = np.sum(photon_table[idx], axis=1)
        # Focus on small angles and downsample
        angle_dist_focused = angle_dist[:50:2]  # Every other point
        angle_focused = angle_centers[:50:2]
        axes[1,0].plot(angle_focused, angle_dist_focused, color=color, 
                      label=f'{energy_values[idx]:.0f} MeV', linewidth=2)
    
    axes[1,0].set_xlabel('Opening Angle (rad)')
    axes[1,0].set_ylabel('Photon Count')
    axes[1,0].set_title('Cherenkov Angular Distribution')
    axes[1,0].legend()
    axes[1,0].grid(True, alpha=0.3)
    
    # Distance vs angle at peak energy
    peak_energy_idx = np.argmax(energy_projection)
    peak_energy = energy_values[peak_energy_idx]
    
    dist_angle_slice = photon_table[peak_energy_idx, :50, :100]  # Focus on relevant region
    im = axes[1,1].imshow(np.log10(dist_angle_slice + 1), origin='lower', 
                         aspect='auto', cmap='viridis',
                         extent=[distance_centers[0], distance_centers[99],
                                angle_centers[0], angle_centers[49]])
    axes[1,1].set_xlabel('Distance (mm)')
    axes[1,1].set_ylabel('Opening Angle (rad)')
    axes[1,1].set_title(f'Angle vs Distance at {peak_energy:.0f} MeV')
    plt.colorbar(im, ax=axes[1,1], label='log₁₀(Count+1)')
    
    plt.tight_layout()
    plt.show()
    
    # Print some interesting statistics
    print(f"\n📊 Key Statistics:")
    print(f"   Total photons in table: {photon_table.sum():.2e}")
    print(f"   Peak energy: {energy_values[peak_energy_idx]} MeV")
    print(f"   Peak Cherenkov angle: {np.mean(peak_angles):.4f} ± {np.std(peak_angles):.4f} rad")
    print(f"   Cherenkov angle at 500 MeV: {peak_angles[40]:.4f} rad")
    print(f"   Non-zero bins: {np.count_nonzero(photon_table):,} / {photon_table.size:,}")
    print(f"   Data sparsity: {100*np.count_nonzero(photon_table)/photon_table.size:.2f}%")

if __name__ == "__main__":
    load_and_show_data()