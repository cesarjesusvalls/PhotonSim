#!/usr/bin/env python3
"""
Proper visualization of PhotonSim data showing the full angular range.
"""

import numpy as np
import matplotlib.pyplot as plt

def show_full_angular_data():
    """Show PhotonSim data across the full angular range."""
    
    # Load data
    print("Loading PhotonSim data...")
    photon_table = np.load('output/3d_lookup_table/photon_table_3d.npy')
    metadata = np.load('output/3d_lookup_table/table_metadata.npz')
    
    energy_values = metadata['energy_values']
    angle_centers = metadata['angle_centers']
    distance_centers = metadata['distance_centers']
    
    print(f"Full angle range: {np.degrees(angle_centers[0]):.2f}° to {np.degrees(angle_centers[-1]):.2f}°")
    
    # 1. Full angular distribution for several energies
    plt.figure(figsize=(12, 8))
    
    plt.subplot(2, 2, 1)
    selected_energies = [100, 300, 500, 700, 900]
    colors = plt.cm.viridis(np.linspace(0, 1, len(selected_energies)))
    
    for energy, color in zip(selected_energies, colors):
        idx = np.argmin(np.abs(energy_values - energy))
        angle_dist = np.sum(photon_table[idx], axis=1)
        
        # Convert to degrees for better readability
        angles_deg = np.degrees(angle_centers)
        
        plt.plot(angles_deg, angle_dist, color=color, 
                label=f'{energy_values[idx]:.0f} MeV', linewidth=2)
    
    plt.xlabel('Opening Angle (degrees)')
    plt.ylabel('Photon Count')
    plt.title('Angular Distribution (Full Range)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xlim(0, 180)
    
    # 2. Peak region zoom (30-50 degrees)
    plt.subplot(2, 2, 2)
    peak_mask = (np.degrees(angle_centers) >= 30) & (np.degrees(angle_centers) <= 50)
    
    for energy, color in zip(selected_energies, colors):
        idx = np.argmin(np.abs(energy_values - energy))
        angle_dist = np.sum(photon_table[idx], axis=1)
        
        angles_deg = np.degrees(angle_centers)
        plt.plot(angles_deg[peak_mask], angle_dist[peak_mask], color=color, 
                label=f'{energy_values[idx]:.0f} MeV', linewidth=2, marker='o', markersize=2)
    
    plt.xlabel('Opening Angle (degrees)')
    plt.ylabel('Photon Count')
    plt.title('Peak Region (30-50°)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 3. Find peak angles vs energy
    plt.subplot(2, 2, 3)
    peak_angles = []
    peak_counts = []
    
    for i, energy in enumerate(energy_values):
        angle_dist = np.sum(photon_table[i], axis=1)
        peak_idx = np.argmax(angle_dist)
        peak_angles.append(np.degrees(angle_centers[peak_idx]))
        peak_counts.append(angle_dist[peak_idx])
    
    plt.plot(energy_values, peak_angles, 'ko-', linewidth=2, markersize=4)
    plt.xlabel('Energy (MeV)')
    plt.ylabel('Peak Angle (degrees)')
    plt.title('Cherenkov Angle vs Energy')
    plt.grid(True, alpha=0.3)
    
    # Add theoretical Cherenkov angle for comparison
    # θ_c = arccos(1/(n*β)) where n≈1.33 for water, β≈1 for relativistic muons
    n_water = 1.33
    theoretical_angle = np.degrees(np.arccos(1/n_water))
    plt.axhline(y=theoretical_angle, color='red', linestyle='--', 
               label=f'Theory (water): {theoretical_angle:.1f}°')
    plt.legend()
    
    # 4. 2D view: Energy vs Angle
    plt.subplot(2, 2, 4)
    proj_ea = np.sum(photon_table, axis=2)  # Sum over distance
    
    angles_deg = np.degrees(angle_centers)
    
    # Apply log scale and show
    im = plt.imshow(np.log10(proj_ea.T + 1), origin='lower', aspect='auto', 
                   cmap='viridis',
                   extent=[energy_values[0], energy_values[-1], 
                          angles_deg[0], angles_deg[-1]])
    
    plt.xlabel('Energy (MeV)')
    plt.ylabel('Opening Angle (degrees)')
    plt.title('Energy vs Angle Heatmap')
    plt.colorbar(im, label='log₁₀(Count + 1)')
    
    # Mark the theoretical Cherenkov angle
    plt.axhline(y=theoretical_angle, color='red', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.show()
    
    # Print physics analysis
    print(f"\n🔬 Physics Analysis:")
    print(f"   Average peak angle: {np.mean(peak_angles):.2f}° ± {np.std(peak_angles):.2f}°")
    print(f"   Theoretical Cherenkov (water): {theoretical_angle:.2f}°")
    print(f"   Peak angle range: {np.min(peak_angles):.2f}° to {np.max(peak_angles):.2f}°")
    print(f"   Peak photon count range: {np.min(peak_counts):,.0f} to {np.max(peak_counts):,.0f}")
    
    # Check if peak is consistent with Cherenkov physics
    angle_diff = abs(np.mean(peak_angles) - theoretical_angle)
    print(f"   Difference from theory: {angle_diff:.2f}°")
    
    if angle_diff < 5:
        print("   ✅ Peak angle consistent with Cherenkov radiation!")
    else:
        print("   ⚠️  Peak angle differs significantly from Cherenkov theory")

if __name__ == "__main__":
    show_full_angular_data()