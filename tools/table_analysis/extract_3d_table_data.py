#!/usr/bin/env python3
"""
Extract 3D lookup table data from PhotonSim ROOT file.

This script demonstrates how to:
1. Load optical photon data from the ROOT file
2. Filter by parent particle type (muon vs electron)
3. Calculate 3D spatial distributions
4. Create energy-dependent lookup tables
5. Export data for use in other applications
"""

import numpy as np
import matplotlib.pyplot as plt
import uproot
# import pandas as pd  # Not available
# from scipy.spatial.distance import cdist  # Not needed for basic analysis
import os

def load_photon_data(root_file_path):
    """Load all photon data from ROOT file."""
    
    print(f"Loading data from: {root_file_path}")
    
    with uproot.open(root_file_path) as file:
        tree = file['OpticalPhotons']
        
        # Load all branches
        data = {
            'EventID': tree['EventID'].array(library='np'),
            'PrimaryEnergy': tree['PrimaryEnergy'].array(library='np'),
            'NOpticalPhotons': tree['NOpticalPhotons'].array(library='np'),
            'PhotonPosX': tree['PhotonPosX'].array(library='np'),
            'PhotonPosY': tree['PhotonPosY'].array(library='np'),
            'PhotonPosZ': tree['PhotonPosZ'].array(library='np'),
            'PhotonDirX': tree['PhotonDirX'].array(library='np'),
            'PhotonDirY': tree['PhotonDirY'].array(library='np'),
            'PhotonDirZ': tree['PhotonDirZ'].array(library='np'),
            'PhotonTime': tree['PhotonTime'].array(library='np'),
            'PhotonParent': tree['PhotonParent'].array(library='np'),
            'PhotonParentID': tree['PhotonParentID'].array(library='np'),
        }
        
        n_events = len(data['EventID'])
        total_photons = np.sum(data['NOpticalPhotons'])
        
        print(f"✓ Loaded {n_events} events with {total_photons:,} total photons")
        
        return data

def analyze_event_data(data, event_id):
    """Analyze data for a specific event."""
    
    print(f"\n=== Event {event_id} Analysis ===")
    
    # Extract event data
    energy = data['PrimaryEnergy'][event_id]
    n_photons = data['NOpticalPhotons'][event_id]
    
    pos_x = data['PhotonPosX'][event_id]  # meters
    pos_y = data['PhotonPosY'][event_id]  # meters
    pos_z = data['PhotonPosZ'][event_id]  # meters
    
    dir_x = data['PhotonDirX'][event_id]
    dir_y = data['PhotonDirY'][event_id]
    dir_z = data['PhotonDirZ'][event_id]
    
    times = data['PhotonTime'][event_id]  # nanoseconds
    parents = data['PhotonParent'][event_id]
    
    print(f"Muon energy: {energy:.1f} MeV")
    print(f"Total photons: {n_photons:,}")
    
    # Analyze parent types
    parent_types = list(set(parents))
    print(f"Parent types: {parent_types}")
    
    for parent_type in parent_types:
        count = sum(1 for p in parents if p == parent_type)
        percentage = 100 * count / len(parents)
        print(f"  {parent_type}: {count:,} photons ({percentage:.1f}%)")
    
    # Convert to more convenient units
    pos_x_mm = pos_x * 1000  # Convert to mm
    pos_y_mm = pos_y * 1000
    pos_z_mm = pos_z * 1000
    
    print(f"\nSpatial distribution:")
    print(f"  X: {np.min(pos_x_mm):.1f} to {np.max(pos_x_mm):.1f} mm")
    print(f"  Y: {np.min(pos_y_mm):.1f} to {np.max(pos_y_mm):.1f} mm")
    print(f"  Z: {np.min(pos_z_mm):.1f} to {np.max(pos_z_mm):.1f} mm")
    
    # Calculate distances from origin
    distances = np.sqrt(pos_x**2 + pos_y**2 + pos_z**2)
    print(f"  Distance from origin: {np.min(distances)*1000:.1f} to {np.max(distances)*1000:.1f} mm")
    
    return {
        'event_id': event_id,
        'energy': energy,
        'n_photons': n_photons,
        'positions': np.column_stack([pos_x, pos_y, pos_z]),  # meters
        'directions': np.column_stack([dir_x, dir_y, dir_z]),
        'times': times,
        'parents': parents,
        'parent_types': parent_types
    }

def filter_by_parent(event_data, parent_type='mu-'):
    """Filter photons by parent particle type."""
    
    parents = event_data['parents']
    mask = np.array([p == parent_type for p in parents])
    
    filtered_data = {
        'event_id': event_data['event_id'],
        'energy': event_data['energy'],
        'n_photons': np.sum(mask),
        'positions': event_data['positions'][mask],
        'directions': event_data['directions'][mask],
        'times': event_data['times'][mask],
        'parents': [p for p in parents if p == parent_type]
    }
    
    print(f"Filtered to {parent_type}: {filtered_data['n_photons']:,} photons")
    
    return filtered_data

def create_3d_histogram(positions, bins=50):
    """Create 3D histogram of photon positions."""
    
    x, y, z = positions[:, 0], positions[:, 1], positions[:, 2]
    
    # Define bin edges
    x_edges = np.linspace(np.min(x), np.max(x), bins + 1)
    y_edges = np.linspace(np.min(y), np.max(y), bins + 1)
    z_edges = np.linspace(np.min(z), np.max(z), bins + 1)
    
    # Create 3D histogram
    hist, edges = np.histogramdd(positions, bins=[x_edges, y_edges, z_edges])
    
    return hist, edges

def calculate_track_distance(positions, track_start=None, track_direction=None):
    """Calculate perpendicular distance from each photon to the muon track."""
    
    if track_start is None:
        track_start = np.array([0.0, 0.0, 0.0])  # Origin
    if track_direction is None:
        track_direction = np.array([0.0, 0.0, 1.0])  # +Z direction
    
    # Normalize direction vector
    track_direction = track_direction / np.linalg.norm(track_direction)
    
    distances = []
    for pos in positions:
        # Vector from track start to photon position
        to_photon = pos - track_start
        
        # Project onto track direction
        projection_length = np.dot(to_photon, track_direction)
        closest_point = track_start + projection_length * track_direction
        
        # Perpendicular distance
        distance = np.linalg.norm(pos - closest_point)
        distances.append(distance)
    
    return np.array(distances)

def create_visualization(event_data, filtered_data, save_path=None):
    """Create visualization of photon distribution."""
    
    fig = plt.figure(figsize=(15, 10))
    
    # All photons
    positions_all = event_data['positions']
    x_all, y_all, z_all = positions_all[:, 0] * 1000, positions_all[:, 1] * 1000, positions_all[:, 2] * 1000
    
    # Filtered photons (muon only)
    positions_filtered = filtered_data['positions']
    x_filt, y_filt, z_filt = positions_filtered[:, 0] * 1000, positions_filtered[:, 1] * 1000, positions_filtered[:, 2] * 1000
    
    # 3D scatter plot
    ax1 = fig.add_subplot(221, projection='3d')
    ax1.scatter(x_all, y_all, z_all, c='blue', s=0.1, alpha=0.3, label='All photons')
    ax1.scatter(x_filt, y_filt, z_filt, c='red', s=0.1, alpha=0.8, label='Muon photons')
    ax1.set_xlabel('X (mm)')
    ax1.set_ylabel('Y (mm)')
    ax1.set_zlabel('Z (mm)')
    ax1.set_title(f'Event {event_data["event_id"]}: 3D Photon Distribution')
    ax1.legend()
    
    # XY projection
    ax2 = fig.add_subplot(222)
    ax2.scatter(x_all, y_all, c='blue', s=0.1, alpha=0.3, label='All photons')
    ax2.scatter(x_filt, y_filt, c='red', s=0.1, alpha=0.8, label='Muon photons')
    ax2.set_xlabel('X (mm)')
    ax2.set_ylabel('Y (mm)')
    ax2.set_title('XY Projection')
    ax2.legend()
    ax2.axis('equal')
    
    # XZ projection
    ax3 = fig.add_subplot(223)
    ax3.scatter(x_all, z_all, c='blue', s=0.1, alpha=0.3, label='All photons')
    ax3.scatter(x_filt, z_filt, c='red', s=0.1, alpha=0.8, label='Muon photons')
    ax3.set_xlabel('X (mm)')
    ax3.set_ylabel('Z (mm)')
    ax3.set_title('XZ Projection')
    ax3.legend()
    
    # Distance from track
    ax4 = fig.add_subplot(224)
    track_distances = calculate_track_distance(positions_filtered)
    ax4.hist(track_distances * 1000, bins=50, alpha=0.7, color='red', edgecolor='black')
    ax4.set_xlabel('Distance from Track (mm)')
    ax4.set_ylabel('Number of Photons')
    ax4.set_title('Distance from Muon Track')
    ax4.set_yscale('log')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Visualization saved to: {save_path}")
    
    plt.show()

def export_lookup_table_data(event_data, output_file):
    """Export processed data for lookup table creation."""
    
    # Extract data
    positions = event_data['positions']
    directions = event_data['directions']
    times = event_data['times']
    parents = event_data['parents']
    
    # Calculate derived quantities
    distances_from_origin = np.sqrt(np.sum(positions**2, axis=1))
    track_distances = calculate_track_distance(positions)
    
    # Create CSV data manually
    header = "event_id,muon_energy_MeV,pos_x_m,pos_y_m,pos_z_m,dir_x,dir_y,dir_z,time_ns,parent_type,distance_from_origin_m,distance_from_track_m\n"
    
    with open(output_file, 'w') as f:
        f.write(header)
        
        for i in range(len(positions)):
            line = f"{event_data['event_id']},{event_data['energy']:.6f},"
            line += f"{positions[i,0]:.6f},{positions[i,1]:.6f},{positions[i,2]:.6f},"
            line += f"{directions[i,0]:.6f},{directions[i,1]:.6f},{directions[i,2]:.6f},"
            line += f"{times[i]:.6f},{parents[i]},"
            line += f"{distances_from_origin[i]:.6f},{track_distances[i]:.6f}\n"
            f.write(line)
    
    print(f"Data exported to: {output_file}")
    
    return positions, track_distances

def process_all_events(data, output_dir='output'):
    """Process all events and create summary statistics."""
    
    os.makedirs(output_dir, exist_ok=True)
    
    n_events = len(data['EventID'])
    summary_stats = []
    
    print(f"\n=== Processing {n_events} Events ===")
    
    for event_id in range(n_events):
        print(f"\nProcessing Event {event_id}...")
        
        # Analyze event
        event_data = analyze_event_data(data, event_id)
        
        # Filter for muon photons only
        muon_data = filter_by_parent(event_data, 'mu-')
        
        # Calculate statistics
        track_distances = calculate_track_distance(muon_data['positions'])
        
        stats = {
            'event_id': event_id,
            'muon_energy_MeV': event_data['energy'],
            'total_photons': event_data['n_photons'],
            'muon_photons': muon_data['n_photons'],
            'electron_photons': event_data['n_photons'] - muon_data['n_photons'],
            'muon_fraction': muon_data['n_photons'] / event_data['n_photons'] if event_data['n_photons'] > 0 else 0,
            'mean_track_distance_mm': np.mean(track_distances) * 1000 if len(track_distances) > 0 else 0,
            'max_track_distance_mm': np.max(track_distances) * 1000 if len(track_distances) > 0 else 0,
            'photons_per_MeV': event_data['n_photons'] / event_data['energy'] if event_data['energy'] > 0 else 0
        }
        
        summary_stats.append(stats)
        
        # Export individual event data
        if event_id < 3:  # Only export first 3 events to save space
            output_file = os.path.join(output_dir, f'event_{event_id}_photons.csv')
            export_lookup_table_data(muon_data, output_file)
    
    # Create summary CSV manually
    summary_file = os.path.join(output_dir, 'event_summary.csv')
    with open(summary_file, 'w') as f:
        # Write header
        f.write("event_id,muon_energy_MeV,total_photons,muon_photons,electron_photons,muon_fraction,mean_track_distance_mm,max_track_distance_mm,photons_per_MeV\n")
        
        # Write data
        for stats in summary_stats:
            line = f"{stats['event_id']},{stats['muon_energy_MeV']:.3f},{stats['total_photons']},{stats['muon_photons']},{stats['electron_photons']},{stats['muon_fraction']:.3f},{stats['mean_track_distance_mm']:.3f},{stats['max_track_distance_mm']:.3f},{stats['photons_per_MeV']:.1f}\n"
            f.write(line)
    
    print(f"\n=== Summary Statistics ===")
    print("Energy range:", min(s['muon_energy_MeV'] for s in summary_stats), "to", max(s['muon_energy_MeV'] for s in summary_stats), "MeV")
    print("Total photons range:", min(s['total_photons'] for s in summary_stats), "to", max(s['total_photons'] for s in summary_stats))
    print("Muon photon fraction:", min(s['muon_fraction'] for s in summary_stats), "to", max(s['muon_fraction'] for s in summary_stats))
    print(f"Summary saved to: {summary_file}")
    
    return summary_stats

if __name__ == "__main__":
    # Configuration
    root_file = "build/optical_photons.root"
    output_dir = "photon_analysis_output"
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Load data
    data = load_photon_data(root_file)
    
    # Process first event in detail
    event_data = analyze_event_data(data, 0)
    muon_data = filter_by_parent(event_data, 'mu-')
    
    # Skip visualization for now to avoid display issues
    print("Skipping visualization (use create_visualization() manually if needed)")
    
    # Process all events
    summary_stats = process_all_events(data, output_dir)
    
    print(f"\n=== Analysis Complete ===")
    print(f"Output directory: {output_dir}")
    print(f"Key files:")
    print(f"  - event_summary.csv: Summary statistics for all events")
    print(f"  - event_*_photons.csv: Individual event photon data")
    
    # Show a few sample lines from the first event
    first_event_file = os.path.join(output_dir, 'event_0_photons.csv')
    if os.path.exists(first_event_file):
        print(f"\nSample data from {first_event_file}:")
        with open(first_event_file, 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines[:6]):  # Show header + 5 data lines
                print(f"  {line.strip()}")
            if len(lines) > 6:
                print(f"  ... ({len(lines)-1} total data rows)")