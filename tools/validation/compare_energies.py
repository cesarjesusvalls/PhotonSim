#!/usr/bin/env python3
"""
Compare PhotonSim outputs for 300 MeV vs 600 MeV muons.
Focus on photons vs distance plots to check for energy-dependent differences.
"""

import numpy as np
import matplotlib.pyplot as plt
import uproot
from pathlib import Path

def compare_energy_outputs():
    """Compare 300 MeV and 2000 MeV PhotonSim outputs."""
    
    # File paths
    file_300 = Path("build/test_300MeV_histonly.root")
    file_600 = Path("build/test_2000MeV_histonly.root")
    
    print("Loading PhotonSim test outputs...")
    
    # Check files exist
    if not file_300.exists():
        print(f"Error: {file_300} not found!")
        return
    if not file_600.exists():
        print(f"Error: {file_600} not found!")
        return
    
    # Load both files
    with uproot.open(file_300) as f300, uproot.open(file_600) as f600:
        print(f"\n300 MeV file contents:")
        for key in f300.keys():
            print(f"  - {key}")
            
        print(f"\n2000 MeV file contents:")
        for key in f600.keys():
            print(f"  - {key}")
        
        # Get the photon angle-distance histograms
        if "PhotonHist_AngleDistance" in f300 and "PhotonHist_AngleDistance" in f600:
            hist_300 = f300["PhotonHist_AngleDistance"]
            hist_600 = f600["PhotonHist_AngleDistance"]
            
            # Get histogram data
            counts_300 = hist_300.values()
            counts_600 = hist_600.values()
            
            # Get bin edges
            angle_edges = hist_300.axis(0).edges()  # Angle axis
            distance_edges = hist_300.axis(1).edges()  # Distance axis
            
            # Calculate bin centers
            angle_centers = (angle_edges[:-1] + angle_edges[1:]) / 2
            distance_centers = (distance_edges[:-1] + distance_edges[1:]) / 2
            
            print(f"\nHistogram shapes:")
            print(f"  300 MeV: {counts_300.shape}, total = {counts_300.sum():.0f}")
            print(f"  2000 MeV: {counts_600.shape}, total = {counts_600.sum():.0f}")
            print(f"  Angle range: {np.degrees(angle_centers[0]):.2f}° to {np.degrees(angle_centers[-1]):.2f}°")
            print(f"  Distance range: {distance_centers[0]:.1f} to {distance_centers[-1]:.1f} mm")
            
            # Create comparison plots
            create_comparison_plots(counts_300, counts_600, angle_centers, distance_centers, "300 MeV", "2000 MeV")
            
        else:
            print("PhotonHist_AngleDistance not found in one or both files!")

def create_comparison_plots(counts_300, counts_600, angle_centers, distance_centers, label_300, label_600):
    """Create comparison plots between two energy datasets."""
    
    # Convert to degrees for better readability
    angles_deg = np.degrees(angle_centers)
    
    plt.figure(figsize=(12, 8))
    
    # 1. Distance projections (sum over all angles)
    plt.subplot(2, 3, 1)
    dist_proj_300 = np.sum(counts_300, axis=0)
    dist_proj_600 = np.sum(counts_600, axis=0)
    
    # Focus on main region (0-5000 mm)
    distance_mask = distance_centers <= 5000
    distances_focused = distance_centers[distance_mask]
    dist_proj_300_focused = dist_proj_300[distance_mask]
    dist_proj_600_focused = dist_proj_600[distance_mask]
    
    plt.plot(distances_focused, dist_proj_300_focused, 'b-', linewidth=2, label=label_300)
    plt.plot(distances_focused, dist_proj_600_focused, 'r-', linewidth=2, label=label_600)
    plt.xlabel('Distance (mm)')
    plt.ylabel('Photon Count')
    plt.title('Photons vs Distance (All Angles)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 2. Distance projections - normalized
    plt.subplot(2, 3, 2)
    # Normalize by total counts
    dist_proj_300_norm = dist_proj_300_focused / np.sum(dist_proj_300_focused)
    dist_proj_600_norm = dist_proj_600_focused / np.sum(dist_proj_600_focused)
    
    plt.plot(distances_focused, dist_proj_300_norm, 'b-', linewidth=2, label=f'{label_300} (normalized)')
    plt.plot(distances_focused, dist_proj_600_norm, 'r-', linewidth=2, label=f'{label_600} (normalized)')
    plt.xlabel('Distance (mm)')
    plt.ylabel('Normalized Photon Count')
    plt.title('Normalized Photons vs Distance')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 3. Angular projections (sum over all distances)
    plt.subplot(2, 3, 3)
    angle_proj_300 = np.sum(counts_300, axis=1)
    angle_proj_600 = np.sum(counts_600, axis=1)
    
    # Focus on Cherenkov region (30-50 degrees)
    angle_mask = (angles_deg >= 30) & (angles_deg <= 60)
    angles_focused = angles_deg[angle_mask]
    angle_proj_300_focused = angle_proj_300[angle_mask]
    angle_proj_600_focused = angle_proj_600[angle_mask]
    
    plt.plot(angles_focused, angle_proj_300_focused, 'b-', linewidth=2, label=label_300)
    plt.plot(angles_focused, angle_proj_600_focused, 'r-', linewidth=2, label=label_600)
    plt.xlabel('Opening Angle (degrees)')
    plt.ylabel('Photon Count')
    plt.title('Cherenkov Peak Region')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 4. Ratio plot: 600 MeV / 300 MeV
    plt.subplot(2, 3, 4)
    ratio = np.divide(dist_proj_600_focused, dist_proj_300_focused, 
                     out=np.zeros_like(dist_proj_600_focused), 
                     where=dist_proj_300_focused!=0)
    
    plt.plot(distances_focused, ratio, 'g-', linewidth=2)
    plt.axhline(y=1, color='k', linestyle='--', alpha=0.5)
    plt.xlabel('Distance (mm)')
    plt.ylabel('Ratio (2000 MeV / 300 MeV)')
    plt.title('Energy Ratio vs Distance')
    plt.grid(True, alpha=0.3)
    plt.ylim(0, 3)
    
    # 5. 2D comparison: 300 MeV
    plt.subplot(2, 3, 5)
    # Focus on relevant region
    angle_idx_max = np.where(angles_deg <= 60)[0][-1]
    distance_idx_max = np.where(distance_centers <= 3000)[0][-1]
    
    counts_300_focused = counts_300[:angle_idx_max, :distance_idx_max]
    
    im1 = plt.imshow(np.log10(counts_300_focused + 1), origin='lower', aspect='auto',
                    cmap='viridis',
                    extent=[0, 3000, 0, 60])
    plt.xlabel('Distance (mm)')
    plt.ylabel('Opening Angle (degrees)')
    plt.title(f'{label_300} (log scale)')
    plt.colorbar(im1, label='log₁₀(Count + 1)')
    
    # 6. 2D comparison: 600 MeV
    plt.subplot(2, 3, 6)
    counts_600_focused = counts_600[:angle_idx_max, :distance_idx_max]
    
    im2 = plt.imshow(np.log10(counts_600_focused + 1), origin='lower', aspect='auto',
                    cmap='viridis',
                    extent=[0, 3000, 0, 60])
    plt.xlabel('Distance (mm)')
    plt.ylabel('Opening Angle (degrees)')
    plt.title(f'{label_600} (log scale)')
    plt.colorbar(im2, label='log₁₀(Count + 1)')
    
    plt.tight_layout()
    plt.show()
    
    # Print numerical comparison
    print(f"\n📊 Numerical Comparison:")
    print(f"   Total photons - {label_300}: {np.sum(counts_300):,.0f}")
    print(f"   Total photons - {label_600}: {np.sum(counts_600):,.0f}")
    print(f"   Ratio (2000/300): {np.sum(counts_600)/np.sum(counts_300):.3f}")
    
    # Find peak angles
    peak_idx_300 = np.argmax(angle_proj_300)
    peak_idx_600 = np.argmax(angle_proj_600)
    
    print(f"   Peak angle - {label_300}: {angles_deg[peak_idx_300]:.2f}°")
    print(f"   Peak angle - {label_600}: {angles_deg[peak_idx_600]:.2f}°")
    
    # Check distance distributions
    mean_dist_300 = np.average(distances_focused, weights=dist_proj_300_focused)
    mean_dist_600 = np.average(distances_focused, weights=dist_proj_600_focused)
    
    print(f"   Mean distance - {label_300}: {mean_dist_300:.1f} mm")
    print(f"   Mean distance - {label_600}: {mean_dist_600:.1f} mm")
    
    # Statistical test
    max_ratio = np.max(ratio[ratio < np.inf])
    min_ratio = np.min(ratio[ratio > 0])
    
    print(f"   Distance ratio range: {min_ratio:.3f} to {max_ratio:.3f}")
    
    if max_ratio < 1.1 and min_ratio > 0.9:
        print("   ⚠️  Very similar distributions - potential issue!")
    else:
        print("   ✅ Clear energy-dependent differences detected")

if __name__ == "__main__":
    compare_energy_outputs()