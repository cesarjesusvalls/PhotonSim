#!/usr/bin/env python3
"""
Analyze all events in the ROOT file and create energy histogram.
"""

import numpy as np
import matplotlib.pyplot as plt
import uproot
from pathlib import Path
import argparse

def analyze_all_events(file_path, output_dir="all_events_analysis"):
    """Analyze all events and create energy histogram."""
    print(f"Loading all events from {file_path}...")
    
    with uproot.open(file_path) as file:
        tree = file["OpticalPhotons"]
        total_events = tree.num_entries
        print(f"Total events in file: {total_events}")
        
        # Load energy data for all events
        data = tree.arrays(['PrimaryEnergy'], library="np")
        
        # Extract all energies
        all_energies = data['PrimaryEnergy']
        
        print(f"Energy statistics:")
        print(f"  Min energy: {all_energies.min():.1f} MeV")
        print(f"  Max energy: {all_energies.max():.1f} MeV")
        print(f"  Mean energy: {all_energies.mean():.1f} MeV")
        print(f"  Std energy: {all_energies.std():.1f} MeV")
        
        # Create energy histogram
        plt.figure(figsize=(10, 6))
        
        n_bins = 20
        counts, bins, patches = plt.hist(all_energies, bins=n_bins, alpha=0.7, 
                                        color='skyblue', edgecolor='black')
        
        plt.xlabel('Muon Energy (MeV)', fontsize=12)
        plt.ylabel('Number of Events', fontsize=12)
        plt.title(f'Energy Distribution of {total_events} Muon Events', fontsize=14)
        plt.grid(True, alpha=0.3)
        
        # Add statistics text
        stats_text = f'Mean: {all_energies.mean():.1f} MeV\nStd: {all_energies.std():.1f} MeV\nRange: {all_energies.min():.1f} - {all_energies.max():.1f} MeV'
        plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes, 
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Save histogram
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        plt.savefig(output_path / "energy_histogram.png", dpi=200, bbox_inches='tight')
        print(f"Energy histogram saved to: {output_path / 'energy_histogram.png'}")
        
        # Print bin details
        print(f"\nEnergy histogram details:")
        for i in range(len(counts)):
            print(f"  Bin {i+1}: {bins[i]:.1f} - {bins[i+1]:.1f} MeV: {int(counts[i])} events")
        
        plt.show()
        
        return all_energies

def create_full_3d_table(file_path, output_dir="full_3d_table"):
    """Create 3D table using ALL events."""
    print(f"\nCreating 3D table using ALL events...")
    
    with uproot.open(file_path) as file:
        tree = file["OpticalPhotons"]
        total_events = tree.num_entries
        print(f"Processing all {total_events} events...")
        
        # Load all data (this might take a while)
        data = tree.arrays([
            'PrimaryEnergy', 'PhotonPosX', 'PhotonPosY', 'PhotonPosZ',
            'PhotonDirX', 'PhotonDirY', 'PhotonDirZ', 'PhotonParent'
        ], library="np")
    
    # Process all events
    energies = []
    angles = []
    distances = []
    
    muon_dir = np.array([0, 0, 1])  # Muon direction along +z
    total_photons = 0
    total_muon_photons = 0
    
    print("Processing events...")
    for event_idx in range(total_events):
        if event_idx % 10 == 0:
            print(f"  Processing event {event_idx+1}/{total_events}")
            
        event_energy = data['PrimaryEnergy'][event_idx]
        n_photons = len(data['PhotonPosX'][event_idx])
        total_photons += n_photons
        
        # Filter for muon photons only
        parents = data['PhotonParent'][event_idx]
        muon_indices = [i for i, p in enumerate(parents) if p == 'mu-']
        total_muon_photons += len(muon_indices)
        
        if len(muon_indices) == 0:
            continue
            
        # Sample photons if too many (to keep memory manageable)
        if len(muon_indices) > 2000:  # Increased sampling
            sample_indices = np.random.choice(muon_indices, 2000, replace=False)
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
    
    print(f"\nData processing complete:")
    print(f"  Total photons: {total_photons:,}")
    print(f"  Muon photons: {total_muon_photons:,}")
    print(f"  Sampled for analysis: {len(energies):,}")
    
    # Convert to numpy arrays
    energies = np.array(energies)
    angles = np.array(angles)
    distances = np.array(distances)
    
    # Create 3D histogram with more bins since we have more data
    bins = (15, 20, 15)  # energy, angle, distance
    
    # Define ranges
    energy_range = (energies.min(), energies.max())
    angle_range = (angles.min(), angles.max())
    
    # Limit distance to 95th percentile
    distance_95th = np.percentile(distances, 95)
    distance_mask = distances <= distance_95th
    
    filtered_energies = energies[distance_mask]
    filtered_angles = angles[distance_mask]
    filtered_distances = distances[distance_mask]
    distance_range = (0, distance_95th)
    
    print(f"\nCreating 3D histogram with {bins} bins...")
    print(f"Energy range: {energy_range[0]:.1f} - {energy_range[1]:.1f} MeV")
    print(f"Angle range: {angle_range[0]:.3f} - {angle_range[1]:.3f} rad")
    print(f"Distance range: {distance_range[0]:.1f} - {distance_range[1]:.1f} mm")
    print(f"Using {len(filtered_energies):,} photons after filtering")
    
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
    print(f"Total photons in histogram: {hist.sum():,.0f}")
    print(f"Non-zero bins: {np.count_nonzero(hist)}")
    print(f"Max bin count: {hist.max():.0f}")
    
    # Save the full table
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Save histogram
    np.save(output_path / "photon_histogram_3d.npy", hist)
    
    # Save metadata
    metadata = {
        'histogram_shape': hist.shape,
        'energy_edges': energy_edges,
        'angle_edges': angle_edges,
        'distance_edges': distance_edges,
        'energy_range': energy_range,
        'angle_range': angle_range,
        'distance_range': distance_range,
        'total_photons': hist.sum(),
        'max_bin_count': hist.max(),
        'total_events_processed': total_events,
        'total_muon_photons': total_muon_photons
    }
    
    np.savez(output_path / "table_metadata.npz", **metadata)
    
    print(f"Full 3D table saved to: {output_path}")
    
    return hist, edges, (energy_range, angle_range, distance_range)

def main():
    parser = argparse.ArgumentParser(description='Analyze all events and create full 3D table')
    parser.add_argument('--input', '-i', default='1k_mu_optical_photons.root',
                       help='Input ROOT file')
    parser.add_argument('--energy-only', action='store_true',
                       help='Only create energy histogram')
    
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
    
    # Always create energy histogram
    energies = analyze_all_events(input_path)
    
    # Create full 3D table if requested
    if not args.energy_only:
        create_full_3d_table(input_path)
    
    print(f"\nAnalysis complete!")

if __name__ == "__main__":
    main()