#!/usr/bin/env python3
"""
Simple 3D table creator for Cherenkov photon data.
Creates regular binning for: energy, opening angle, distance from origin.
"""

import numpy as np
import matplotlib.pyplot as plt
import uproot
from pathlib import Path
import argparse

def load_photon_data(file_path, max_events=10):
    """Load and process photon data efficiently."""
    print(f"Loading data from {file_path}...")
    
    with uproot.open(file_path) as file:
        tree = file["OpticalPhotons"]
        
        # Load only essential branches for first few events
        data = tree.arrays([
            'PrimaryEnergy', 'PhotonPosX', 'PhotonPosY', 'PhotonPosZ',
            'PhotonDirX', 'PhotonDirY', 'PhotonDirZ', 'PhotonParent'
        ], entry_stop=max_events, library="np")
        
        print(f"Processing {max_events} events...")
    
    # Process each event
    energies = []
    angles = []
    distances = []
    
    muon_dir = np.array([0, 0, 1])  # Muon direction along +z
    
    for event_idx in range(len(data['PrimaryEnergy'])):
        event_energy = data['PrimaryEnergy'][event_idx]
        n_photons = len(data['PhotonPosX'][event_idx])
        
        # Filter for muon photons only
        parents = data['PhotonParent'][event_idx]
        muon_indices = [i for i, p in enumerate(parents) if p == 'mu-']
        
        if len(muon_indices) == 0:
            continue
            
        # Sample photons if too many
        if len(muon_indices) > 500:
            sample_indices = np.random.choice(muon_indices, 500, replace=False)
        else:
            sample_indices = muon_indices
        
        for idx in sample_indices:
            # Energy (repeat for each photon)
            energies.append(event_energy)
            
            # Position in mm
            pos = np.array([
                data['PhotonPosX'][event_idx][idx] * 1000,
                data['PhotonPosY'][event_idx][idx] * 1000,
                data['PhotonPosZ'][event_idx][idx] * 1000
            ])
            
            # Distance from origin
            distance = np.sqrt(np.sum(pos**2))
            distances.append(distance)
            
            # Direction
            photon_dir = np.array([
                data['PhotonDirX'][event_idx][idx],
                data['PhotonDirY'][event_idx][idx],
                data['PhotonDirZ'][event_idx][idx]
            ])
            
            # Opening angle
            cos_angle = np.dot(photon_dir, muon_dir)
            cos_angle = np.clip(cos_angle, -1.0, 1.0)
            angle = np.arccos(cos_angle)
            angles.append(angle)
    
    return np.array(energies), np.array(angles), np.array(distances)

def create_3d_histogram(energies, angles, distances, bins=(10, 15, 12)):
    """Create 3D histogram with regular binning."""
    print(f"Creating 3D histogram with {bins} bins...")
    
    # Define ranges
    energy_range = (energies.min(), energies.max())
    angle_range = (angles.min(), angles.max())
    
    # Limit distance to 95th percentile to avoid outliers
    distance_95th = np.percentile(distances, 95)
    distance_mask = distances <= distance_95th
    
    filtered_energies = energies[distance_mask]
    filtered_angles = angles[distance_mask]
    filtered_distances = distances[distance_mask]
    distance_range = (0, distance_95th)
    
    print(f"Energy range: {energy_range[0]:.1f} - {energy_range[1]:.1f} MeV")
    print(f"Angle range: {angle_range[0]:.3f} - {angle_range[1]:.3f} rad")
    print(f"Distance range: {distance_range[0]:.1f} - {distance_range[1]:.1f} mm")
    print(f"Using {len(filtered_energies)} photons after filtering")
    
    # Create bin edges
    energy_edges = np.linspace(energy_range[0], energy_range[1], bins[0] + 1)
    angle_edges = np.linspace(angle_range[0], angle_range[1], bins[1] + 1)
    distance_edges = np.linspace(distance_range[0], distance_range[1], bins[2] + 1)
    
    # Create 3D histogram
    hist, edges = np.histogramdd(
        np.column_stack([filtered_energies, filtered_angles, filtered_distances]),
        bins=[energy_edges, angle_edges, distance_edges]
    )
    
    print(f"3D histogram shape: {hist.shape}")
    print(f"Total photons in histogram: {hist.sum()}")
    print(f"Non-zero bins: {np.count_nonzero(hist)}")
    print(f"Max bin count: {hist.max()}")
    
    return hist, edges, (energy_range, angle_range, distance_range)

def create_visualizations(hist, edges, ranges, output_dir):
    """Create simple visualizations of the 3D table."""
    print("Creating visualizations...")
    
    # Calculate bin centers
    energy_centers = (edges[0][:-1] + edges[0][1:]) / 2
    angle_centers = (edges[1][:-1] + edges[1][1:]) / 2
    distance_centers = (edges[2][:-1] + edges[2][1:]) / 2
    
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle('3D Photon Table Analysis', fontsize=16)
    
    # 2D projections
    # Energy vs Angle
    projection_ea = np.sum(hist, axis=2)
    im1 = axes[0,0].imshow(projection_ea.T, origin='lower', aspect='auto', cmap='viridis')
    axes[0,0].set_title('Energy vs Opening Angle')
    axes[0,0].set_xlabel('Energy Bin')
    axes[0,0].set_ylabel('Angle Bin')
    plt.colorbar(im1, ax=axes[0,0])
    
    # Energy vs Distance
    projection_ed = np.sum(hist, axis=1)
    im2 = axes[0,1].imshow(projection_ed.T, origin='lower', aspect='auto', cmap='viridis')
    axes[0,1].set_title('Energy vs Distance')
    axes[0,1].set_xlabel('Energy Bin')
    axes[0,1].set_ylabel('Distance Bin')
    plt.colorbar(im2, ax=axes[0,1])
    
    # Angle vs Distance
    projection_ad = np.sum(hist, axis=0)
    im3 = axes[0,2].imshow(projection_ad.T, origin='lower', aspect='auto', cmap='viridis')
    axes[0,2].set_title('Angle vs Distance')
    axes[0,2].set_xlabel('Angle Bin')
    axes[0,2].set_ylabel('Distance Bin')
    plt.colorbar(im3, ax=axes[0,2])
    
    # 1D projections
    energy_dist = np.sum(hist, axis=(1, 2))
    axes[1,0].plot(energy_centers, energy_dist, 'b-', linewidth=2)
    axes[1,0].set_xlabel('Energy (MeV)')
    axes[1,0].set_ylabel('Photon Count')
    axes[1,0].set_title('Energy Distribution')
    axes[1,0].grid(True, alpha=0.3)
    
    angle_dist = np.sum(hist, axis=(0, 2))
    axes[1,1].plot(angle_centers, angle_dist, 'g-', linewidth=2)
    axes[1,1].set_xlabel('Opening Angle (rad)')
    axes[1,1].set_ylabel('Photon Count')
    axes[1,1].set_title('Opening Angle Distribution')
    axes[1,1].grid(True, alpha=0.3)
    
    distance_dist = np.sum(hist, axis=(0, 1))
    axes[1,2].plot(distance_centers, distance_dist, 'r-', linewidth=2)
    axes[1,2].set_xlabel('Distance (mm)')
    axes[1,2].set_ylabel('Photon Count')
    axes[1,2].set_title('Distance Distribution')
    axes[1,2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save visualization
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    plt.savefig(output_path / "3d_table_simple.png", dpi=200, bbox_inches='tight')
    print(f"Visualization saved to {output_path / '3d_table_simple.png'}")
    
    # Don't show plot to avoid hanging in non-interactive environment
    print("Visualization created and saved.")

def save_table_data(hist, edges, ranges, output_dir):
    """Save the 3D table data."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Save histogram
    np.save(output_path / "photon_histogram_3d.npy", hist)
    
    # Save metadata
    metadata = {
        'histogram_shape': hist.shape,
        'energy_edges': edges[0],
        'angle_edges': edges[1],
        'distance_edges': edges[2],
        'energy_range': ranges[0],
        'angle_range': ranges[1],
        'distance_range': ranges[2],
        'total_photons': hist.sum(),
        'max_bin_count': hist.max()
    }
    
    np.savez(output_path / "table_metadata.npz", **metadata)
    
    print(f"Table data saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Create simple 3D photon table')
    parser.add_argument('--input', '-i', default='1k_mu_optical_photons.root',
                       help='Input ROOT file')
    parser.add_argument('--output', '-o', default='simple_3d_table',
                       help='Output directory')
    parser.add_argument('--events', '-e', type=int, default=10,
                       help='Number of events to process')
    parser.add_argument('--energy-bins', type=int, default=8,
                       help='Energy bins')
    parser.add_argument('--angle-bins', type=int, default=12,
                       help='Angle bins')
    parser.add_argument('--distance-bins', type=int, default=10,
                       help='Distance bins')
    
    args = parser.parse_args()
    
    # Check input file
    input_path = Path(args.input)
    if not input_path.exists():
        for possible in [Path(args.input), Path("build/optical_photons.root")]:
            if possible.exists():
                input_path = possible
                break
        else:
            print(f"Error: Input file not found: {args.input}")
            return
    
    print(f"Using input file: {input_path}")
    
    # Load data
    energies, angles, distances = load_photon_data(input_path, args.events)
    
    if len(energies) == 0:
        print("No photon data found!")
        return
    
    # Create 3D histogram
    bins = (args.energy_bins, args.angle_bins, args.distance_bins)
    hist, edges, ranges = create_3d_histogram(energies, angles, distances, bins)
    
    # Save data
    save_table_data(hist, edges, ranges, args.output)
    
    # Create visualizations
    create_visualizations(hist, edges, ranges, args.output)
    
    print(f"\n3D photon table creation complete!")
    print(f"Processed {len(energies)} photons from {args.events} events")
    print(f"Output saved to: {args.output}")

if __name__ == "__main__":
    main()