#!/usr/bin/env python3
"""
Visualize the 3D photon lookup table created by create_multi_energy_3d_table.py
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
from pathlib import Path
import argparse

def load_3d_table(table_dir):
    """Load the 3D table and metadata."""
    table_path = Path(table_dir)
    
    # Load the table
    print("Loading 3D table...")
    photon_table = np.load(table_path / "photon_table_3d.npy")
    
    # Load metadata
    metadata = np.load(table_path / "table_metadata.npz")
    
    print(f"Table shape: {photon_table.shape}")
    print(f"Total photons: {photon_table.sum():.0f}")
    print(f"Non-zero bins: {np.count_nonzero(photon_table)}")
    
    return photon_table, metadata

def create_energy_slices(photon_table, metadata, output_dir=None):
    """Create plots showing angle vs distance for different energies."""
    energy_values = metadata['energy_values']
    angle_centers = metadata['angle_centers']
    distance_centers = metadata['distance_centers']
    
    # Select 6 representative energies
    energy_indices = [0, 18, 36, 54, 72, 90]  # 100, 280, 460, 640, 820, 1000 MeV
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    axes = axes.flatten()
    
    for i, idx in enumerate(energy_indices):
        ax = axes[i]
        energy = energy_values[idx]
        
        # Get the 2D histogram for this energy
        hist_2d = photon_table[idx]
        
        # Apply log scale for better visualization
        hist_2d_log = np.log10(hist_2d + 1)  # +1 to avoid log(0)
        
        # Downsample for visualization (average over 10x10 bins)
        downsample = 10
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
        
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('log10(Photon Count + 1)', rotation=270, labelpad=20)
    
    plt.suptitle('Photon Distribution at Different Energies', fontsize=16)
    plt.tight_layout()
    
    if output_dir:
        plt.savefig(Path(output_dir) / "energy_slices.png", dpi=150, bbox_inches='tight')
        print(f"Saved energy slices to {output_dir}/energy_slices.png")
    
    plt.show()

def create_projections(photon_table, metadata, output_dir=None):
    """Create 1D and 2D projections of the 3D table."""
    energy_values = metadata['energy_values']
    angle_centers = metadata['angle_centers']
    distance_centers = metadata['distance_centers']
    
    fig = plt.figure(figsize=(18, 12))
    
    # 1D projections
    # Energy projection
    plt.subplot(3, 3, 1)
    energy_projection = np.sum(photon_table, axis=(1, 2))
    plt.plot(energy_values, energy_projection, 'b-', linewidth=2)
    plt.xlabel('Energy (MeV)')
    plt.ylabel('Total Photon Count')
    plt.title('Total Photons vs Energy')
    plt.grid(True, alpha=0.3)
    
    # Angle projection
    plt.subplot(3, 3, 2)
    angle_projection = np.sum(photon_table, axis=(0, 2))
    # Downsample for plotting
    angle_down = angle_centers[::10]
    angle_proj_down = np.sum(angle_projection.reshape(-1, 10), axis=1)
    plt.plot(angle_down, angle_proj_down, 'g-', linewidth=2)
    plt.xlabel('Opening Angle (rad)')
    plt.ylabel('Total Photon Count')
    plt.title('Photon Count vs Opening Angle')
    plt.grid(True, alpha=0.3)
    
    # Distance projection
    plt.subplot(3, 3, 3)
    distance_projection = np.sum(photon_table, axis=(0, 1))
    # Downsample for plotting
    distance_down = distance_centers[::10]
    distance_proj_down = np.sum(distance_projection.reshape(-1, 10), axis=1)
    plt.plot(distance_down, distance_proj_down, 'r-', linewidth=2)
    plt.xlabel('Distance (mm)')
    plt.ylabel('Total Photon Count')
    plt.title('Photon Count vs Distance')
    plt.grid(True, alpha=0.3)
    plt.xlim(0, 5000)  # Focus on main region
    
    # 2D projections
    # Energy vs Angle (summed over distance)
    plt.subplot(3, 3, 4)
    proj_ea = np.sum(photon_table, axis=2)
    # Downsample angle axis
    proj_ea_down = proj_ea[:, ::10]
    im = plt.imshow(np.log10(proj_ea_down.T + 1), origin='lower', aspect='auto',
                   cmap='viridis',
                   extent=[energy_values[0], energy_values[-1], 
                          angle_centers[0], angle_centers[-1]])
    plt.colorbar(im, label='log10(Count + 1)')
    plt.xlabel('Energy (MeV)')
    plt.ylabel('Opening Angle (rad)')
    plt.title('Energy vs Angle')
    
    # Energy vs Distance (summed over angle)
    plt.subplot(3, 3, 5)
    proj_ed = np.sum(photon_table, axis=1)
    # Downsample distance axis
    proj_ed_down = proj_ed[:, ::10]
    im = plt.imshow(np.log10(proj_ed_down.T + 1), origin='lower', aspect='auto',
                   cmap='viridis',
                   extent=[energy_values[0], energy_values[-1],
                          0, 5000])  # Focus on main region
    plt.colorbar(im, label='log10(Count + 1)')
    plt.xlabel('Energy (MeV)')
    plt.ylabel('Distance (mm)')
    plt.title('Energy vs Distance')
    
    # Angle vs Distance (summed over energy)
    plt.subplot(3, 3, 6)
    proj_ad = np.sum(photon_table, axis=0)
    # Downsample both axes
    proj_ad_down = proj_ad[::10, ::10]
    im = plt.imshow(np.log10(proj_ad_down.T + 1), origin='lower', aspect='auto',
                   cmap='viridis',
                   extent=[angle_centers[0], angle_centers[-1],
                          0, 5000])  # Focus on main region
    plt.colorbar(im, label='log10(Count + 1)')
    plt.xlabel('Opening Angle (rad)')
    plt.ylabel('Distance (mm)')
    plt.title('Angle vs Distance')
    
    # Cherenkov angle analysis
    plt.subplot(3, 3, 7)
    # Find peak angle for each energy
    peak_angles = []
    for i in range(len(energy_values)):
        angle_dist = np.sum(photon_table[i], axis=1)
        peak_idx = np.argmax(angle_dist)
        peak_angles.append(angle_centers[peak_idx])
    
    plt.plot(energy_values, peak_angles, 'k-', linewidth=2)
    plt.xlabel('Energy (MeV)')
    plt.ylabel('Peak Opening Angle (rad)')
    plt.title('Cherenkov Angle vs Energy')
    plt.grid(True, alpha=0.3)
    
    # Statistics
    plt.subplot(3, 3, 9)
    stats_text = f"""3D Table Statistics:
    
Energy range: {energy_values[0]}-{energy_values[-1]} MeV
Number of energies: {len(energy_values)}
Angle bins: {len(angle_centers)}
Distance bins: {len(distance_centers)}
Total table size: {photon_table.shape}

Total photons: {photon_table.sum():.2e}
Non-zero bins: {np.count_nonzero(photon_table):,}
Sparsity: {100*np.count_nonzero(photon_table)/photon_table.size:.2f}%

Max bin count: {photon_table.max():.0f}
Mean (non-zero): {photon_table[photon_table>0].mean():.1f}
Median (non-zero): {np.median(photon_table[photon_table>0]):.1f}"""
    
    plt.text(0.1, 0.5, stats_text, transform=plt.gca().transAxes,
            fontsize=10, family='monospace', verticalalignment='center')
    plt.axis('off')
    
    plt.suptitle('3D Photon Table Analysis', fontsize=16)
    plt.tight_layout()
    
    if output_dir:
        plt.savefig(Path(output_dir) / "table_projections.png", dpi=150, bbox_inches='tight')
        print(f"Saved projections to {output_dir}/table_projections.png")
    
    plt.show()

def create_3d_visualization(photon_table, metadata, output_dir=None):
    """Create 3D visualization of high-density regions."""
    energy_values = metadata['energy_values']
    angle_centers = metadata['angle_centers']
    distance_centers = metadata['distance_centers']
    
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # Find high-density regions (top 0.1% of non-zero bins)
    threshold = np.percentile(photon_table[photon_table > 0], 99.9)
    high_indices = np.where(photon_table >= threshold)
    
    # Limit number of points for visualization
    n_points = min(5000, len(high_indices[0]))
    if len(high_indices[0]) > n_points:
        # Random sampling
        sample_idx = np.random.choice(len(high_indices[0]), n_points, replace=False)
        high_indices = tuple(idx[sample_idx] for idx in high_indices)
    
    # Get coordinates and values
    energies = energy_values[high_indices[0]]
    angles = angle_centers[high_indices[1]]
    distances = distance_centers[high_indices[2]]
    counts = photon_table[high_indices]
    
    # Create scatter plot
    scatter = ax.scatter(energies, angles, distances,
                        c=np.log10(counts + 1), cmap='viridis',
                        s=20, alpha=0.6)
    
    ax.set_xlabel('Energy (MeV)')
    ax.set_ylabel('Opening Angle (rad)')
    ax.set_zlabel('Distance (mm)')
    ax.set_title('High-Density Regions in 3D Photon Table')
    
    # Set z-limits to focus on main region
    ax.set_zlim(0, 5000)
    
    cbar = plt.colorbar(scatter, label='log10(Photon Count + 1)', shrink=0.6)
    
    if output_dir:
        plt.savefig(Path(output_dir) / "3d_visualization.png", dpi=150, bbox_inches='tight')
        print(f"Saved 3D visualization to {output_dir}/3d_visualization.png")
    
    plt.show()

def create_cherenkov_analysis(photon_table, metadata, output_dir=None):
    """Analyze Cherenkov photon characteristics."""
    energy_values = metadata['energy_values']
    angle_centers = metadata['angle_centers']
    distance_centers = metadata['distance_centers']
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    
    # 1. Cherenkov angle distribution for selected energies
    ax = axes[0, 0]
    energies_to_plot = [100, 300, 500, 700, 900]
    colors = plt.cm.viridis(np.linspace(0, 1, len(energies_to_plot)))
    
    for energy, color in zip(energies_to_plot, colors):
        idx = np.argmin(np.abs(energy_values - energy))
        angle_dist = np.sum(photon_table[idx], axis=1)
        # Downsample for plotting
        angle_dist_down = np.sum(angle_dist.reshape(-1, 10), axis=1)
        angle_down = angle_centers[::10]
        ax.plot(angle_down, angle_dist_down, color=color, 
                label=f'{energy_values[idx]:.0f} MeV', linewidth=2)
    
    ax.set_xlabel('Opening Angle (rad)')
    ax.set_ylabel('Photon Count')
    ax.set_title('Angle Distribution vs Energy')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 0.1)  # Focus on small angles
    
    # 2. Distance distribution for selected energies
    ax = axes[0, 1]
    for energy, color in zip(energies_to_plot, colors):
        idx = np.argmin(np.abs(energy_values - energy))
        dist_dist = np.sum(photon_table[idx], axis=0)
        # Downsample for plotting
        dist_dist_down = np.sum(dist_dist.reshape(-1, 10), axis=1)
        dist_down = distance_centers[::10]
        ax.plot(dist_down, dist_dist_down, color=color,
                label=f'{energy_values[idx]:.0f} MeV', linewidth=2)
    
    ax.set_xlabel('Distance (mm)')
    ax.set_ylabel('Photon Count')
    ax.set_title('Distance Distribution vs Energy')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 3000)  # Focus on main region
    
    # 3. Average photons per energy
    ax = axes[1, 0]
    total_photons = np.sum(photon_table, axis=(1, 2))
    ax.plot(energy_values, total_photons, 'b-', linewidth=2)
    ax.set_xlabel('Energy (MeV)')
    ax.set_ylabel('Total Photon Count')
    ax.set_title('Total Cherenkov Photons vs Muon Energy')
    ax.grid(True, alpha=0.3)
    
    # 4. Photon density heatmap at peak angle
    ax = axes[1, 1]
    # Find peak angle across all energies
    angle_projection = np.sum(photon_table, axis=(0, 2))
    peak_angle_idx = np.argmax(angle_projection)
    
    # Extract 2D slice at peak angle
    energy_distance_slice = photon_table[:, peak_angle_idx, :]
    # Downsample distance axis
    slice_down = energy_distance_slice[:, ::10]
    
    im = ax.imshow(np.log10(slice_down.T + 1), origin='lower', aspect='auto',
                   cmap='viridis',
                   extent=[energy_values[0], energy_values[-1], 0, 3000])
    ax.set_xlabel('Energy (MeV)')
    ax.set_ylabel('Distance (mm)')
    ax.set_title(f'Photon Density at Peak Angle ({angle_centers[peak_angle_idx]:.3f} rad)')
    plt.colorbar(im, ax=ax, label='log10(Count + 1)')
    
    plt.suptitle('Cherenkov Photon Analysis', fontsize=16)
    plt.tight_layout()
    
    if output_dir:
        plt.savefig(Path(output_dir) / "cherenkov_analysis.png", dpi=150, bbox_inches='tight')
        print(f"Saved Cherenkov analysis to {output_dir}/cherenkov_analysis.png")
    
    plt.show()

def main():
    parser = argparse.ArgumentParser(description='Visualize 3D photon lookup table')
    parser.add_argument('--input', '-i', default='output/3d_lookup_table',
                       help='Directory containing the 3D table files')
    parser.add_argument('--output', '-o', default='output/3d_lookup_table/visualizations',
                       help='Output directory for visualizations')
    parser.add_argument('--all', action='store_true',
                       help='Create all visualizations')
    parser.add_argument('--slices', action='store_true',
                       help='Create energy slice visualizations')
    parser.add_argument('--projections', action='store_true',
                       help='Create projection visualizations')
    parser.add_argument('--3d', action='store_true',
                       help='Create 3D visualization')
    parser.add_argument('--cherenkov', action='store_true',
                       help='Create Cherenkov analysis plots')
    
    args = parser.parse_args()
    
    # Load the 3D table
    photon_table, metadata = load_3d_table(args.input)
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Create visualizations
    if args.all or args.slices:
        create_energy_slices(photon_table, metadata, output_dir)
    
    if args.all or args.projections:
        create_projections(photon_table, metadata, output_dir)
    
    if args.all or args.__dict__.get('3d', False):
        create_3d_visualization(photon_table, metadata, output_dir)
    
    if args.all or args.cherenkov:
        create_cherenkov_analysis(photon_table, metadata, output_dir)
    
    if not any([args.all, args.slices, args.projections, 
                args.__dict__.get('3d', False), args.cherenkov]):
        print("No visualization type specified. Use --all or specific flags.")
        print("Available options: --slices, --projections, --3d, --cherenkov")

if __name__ == "__main__":
    main()