#!/usr/bin/env python3
"""
Analyze primary muon photons (parentID=1) from PhotonSim data.

This script focuses specifically on photons created directly by the primary muon
to understand the distance distribution from the muon trajectory.
"""

import numpy as np
import matplotlib.pyplot as plt
import uproot
import sys

def analyze_primary_muon_photons(root_file_path):
    """Analyze photons created directly by the primary muon (parentID=1)."""
    
    try:
        with uproot.open(root_file_path) as file:
            tree = file["OpticalPhotons"]
            
            # Load all data including parent tracking
            data = {
                'EventID': tree['EventID'].array(library='np'),
                'PrimaryEnergy': tree['PrimaryEnergy'].array(library='np'),
                'NOpticalPhotons': tree['NOpticalPhotons'].array(library='np'),
                'PhotonPosX': tree['PhotonPosX'].array(library='np'),
                'PhotonPosY': tree['PhotonPosY'].array(library='np'),
                'PhotonPosZ': tree['PhotonPosZ'].array(library='np'),
                'PhotonTime': tree['PhotonTime'].array(library='np'),
                'PhotonProcess': tree['PhotonProcess'].array(library='np'),
                'PhotonParent': tree['PhotonParent'].array(library='np'),
                'PhotonParentID': tree['PhotonParentID'].array(library='np'),
                'PhotonTrackID': tree['PhotonTrackID'].array(library='np'),
            }
            
            n_events = len(data['EventID'])
            total_photons = np.sum(data['NOpticalPhotons'])
            
            print(f"=== Primary Muon Photon Analysis ===")
            print(f"Total events: {n_events}")
            print(f"Total photons: {total_photons:,}")
            
            # Focus on first event for detailed analysis
            event_id = 0
            if n_events == 0:
                print("No events found!")
                return None
            
            # Extract event data
            pos_x = data['PhotonPosX'][event_id] / 1000.0  # Convert mm to meters
            pos_y = data['PhotonPosY'][event_id] / 1000.0
            pos_z = data['PhotonPosZ'][event_id] / 1000.0
            times = data['PhotonTime'][event_id]
            processes = data['PhotonProcess'][event_id]
            parents = data['PhotonParent'][event_id]
            parent_ids = data['PhotonParentID'][event_id]
            track_ids = data['PhotonTrackID'][event_id]
            
            print(f"\\nEvent {event_id} - Primary energy: {data['PrimaryEnergy'][event_id]:.1f} MeV")
            print(f"Total photons in event: {len(pos_x):,}")
            
            # Filter for PRIMARY MUON photons (parentID = 1)
            primary_muon_mask = np.array(parent_ids) == 1
            
            print(f"\\n=== Primary Muon Photons (parentID=1) ===")
            print(f"Photons from primary muon: {np.sum(primary_muon_mask):,}")
            print(f"Percentage of total: {100 * np.sum(primary_muon_mask) / len(parent_ids):.1f}%")
            
            if np.sum(primary_muon_mask) == 0:
                print("ERROR: No photons from primary muon found!")
                return None
            
            # Extract primary muon photon data
            primary_x = pos_x[primary_muon_mask]
            primary_y = pos_y[primary_muon_mask]
            primary_z = pos_z[primary_muon_mask]
            primary_times = times[primary_muon_mask]
            primary_processes = processes[primary_muon_mask]
            
            print(f"\\nPrimary muon photon positions:")
            print(f"  X range: {np.min(primary_x):.2f} to {np.max(primary_x):.2f} m")
            print(f"  Y range: {np.min(primary_y):.2f} to {np.max(primary_y):.2f} m")
            print(f"  Z range: {np.min(primary_z):.2f} to {np.max(primary_z):.2f} m")
            
            # Calculate distances from origin
            origin_distances = np.sqrt(primary_x**2 + primary_y**2 + primary_z**2)
            print(f"\\nDistance from origin:")
            print(f"  Min: {np.min(origin_distances):.2f} m")
            print(f"  Max: {np.max(origin_distances):.2f} m")
            print(f"  Mean: {np.mean(origin_distances):.2f} m")
            print(f"  Median: {np.median(origin_distances):.2f} m")
            
            return {
                'primary_x': primary_x,
                'primary_y': primary_y,
                'primary_z': primary_z,
                'primary_times': primary_times,
                'primary_processes': primary_processes,
                'primary_energy': data['PrimaryEnergy'][event_id],
                'all_x': pos_x,
                'all_y': pos_y,
                'all_z': pos_z,
                'all_parent_ids': parent_ids,
            }
            
    except Exception as e:
        print(f"Error analyzing ROOT file: {e}")
        import traceback
        traceback.print_exc()
        return None

def calculate_track_distances(x, y, z, track_start=[0, 0, 0], track_direction=[0, 0, 1]):
    """
    Calculate perpendicular distances from photon positions to the muon track.
    
    Assumes muon travels in a straight line from track_start in track_direction.
    """
    track_start = np.array(track_start)
    track_direction = np.array(track_direction) / np.linalg.norm(track_direction)
    
    distances = []
    projections = []
    
    for i in range(len(x)):
        photon_pos = np.array([x[i], y[i], z[i]])
        
        # Vector from track start to photon
        to_photon = photon_pos - track_start
        
        # Project onto track direction
        projection_length = np.dot(to_photon, track_direction)
        projections.append(projection_length)
        
        # Find closest point on track
        closest_on_track = track_start + projection_length * track_direction
        
        # Perpendicular distance
        distance = np.linalg.norm(photon_pos - closest_on_track)
        distances.append(distance)
    
    return np.array(distances), np.array(projections)

def plot_primary_muon_analysis(analysis_data):
    """Create comprehensive plots for primary muon photons."""
    
    primary_x = analysis_data['primary_x']
    primary_y = analysis_data['primary_y'] 
    primary_z = analysis_data['primary_z']
    primary_times = analysis_data['primary_times']
    
    # Calculate track distances (assume muon goes from origin in +Z direction)
    track_distances, track_projections = calculate_track_distances(
        primary_x, primary_y, primary_z, 
        track_start=[0, 0, 0], 
        track_direction=[0, 0, 1]
    )
    
    print(f"\\n=== Track Distance Analysis ===")
    print(f"Distance to muon track (assuming straight +Z trajectory):")
    print(f"  Min: {np.min(track_distances):.6f} m")
    print(f"  Max: {np.max(track_distances):.6f} m")
    print(f"  Mean: {np.mean(track_distances):.6f} m")
    print(f"  Median: {np.median(track_distances):.6f} m")
    print(f"  95th percentile: {np.percentile(track_distances, 95):.6f} m")
    print(f"  99th percentile: {np.percentile(track_distances, 99):.6f} m")
    
    # Check for unphysically large distances
    large_distances = track_distances > 1.0  # > 1 meter from track
    print(f"\\nPhotons > 1m from track: {np.sum(large_distances):,} ({100*np.sum(large_distances)/len(track_distances):.1f}%)")
    
    very_large = track_distances > 10.0  # > 10 meters
    print(f"Photons > 10m from track: {np.sum(very_large):,} ({100*np.sum(very_large)/len(track_distances):.1f}%)")
    
    # Create plots
    fig, axes = plt.subplots(2, 3, figsize=(12, 8))
    fig.suptitle(f'Primary Muon Photons (parentID=1) - {len(primary_x):,} photons', fontsize=16)
    
    # 1. Track distance histogram - KEY PLOT
    axes[0,0].hist(track_distances, bins=50, alpha=0.7, color='red', edgecolor='black')
    axes[0,0].set_xlabel('Distance to Muon Track [m]')
    axes[0,0].set_ylabel('Number of Photons')
    axes[0,0].set_title('Distance to Track Distribution')
    axes[0,0].axvline(np.mean(track_distances), color='blue', linestyle='--', 
                     label=f'Mean: {np.mean(track_distances):.3f}m')
    axes[0,0].axvline(np.median(track_distances), color='green', linestyle='--', 
                     label=f'Median: {np.median(track_distances):.3f}m')
    axes[0,0].legend()
    axes[0,0].set_yscale('log')
    
    # 2. XY projection showing track
    scatter = axes[0,1].scatter(primary_x, primary_y, c=track_distances, s=10, 
                               cmap='viridis', alpha=0.7)
    axes[0,1].plot(0, 0, 'r*', markersize=15, label='Track (origin)')
    axes[0,1].set_xlabel('X [m]')
    axes[0,1].set_ylabel('Y [m]')
    axes[0,1].set_title('XY Projection (colored by track distance)')
    axes[0,1].set_aspect('equal')
    axes[0,1].legend()
    plt.colorbar(scatter, ax=axes[0,1], label='Track Distance [m]')
    
    # 3. XZ projection with muon track
    axes[0,2].scatter(primary_x, primary_z, c=track_distances, s=10, 
                     cmap='viridis', alpha=0.7)
    # Draw assumed muon track
    z_track = np.linspace(np.min(primary_z)-5, np.max(primary_z)+5, 100)
    x_track = np.zeros_like(z_track)
    axes[0,2].plot(x_track, z_track, 'r-', linewidth=3, label='Assumed muon track')
    axes[0,2].set_xlabel('X [m]')
    axes[0,2].set_ylabel('Z [m]')
    axes[0,2].set_title('XZ Projection with Track')
    axes[0,2].legend()
    
    # 4. Track distance vs Z position
    axes[1,0].scatter(primary_z, track_distances, c=primary_times, s=10, 
                     cmap='plasma', alpha=0.7)
    axes[1,0].set_xlabel('Z Position [m]')
    axes[1,0].set_ylabel('Distance to Track [m]')
    axes[1,0].set_title('Track Distance vs Z Position')
    axes[1,0].set_yscale('log')
    
    # 5. Time distribution
    axes[1,1].hist(primary_times, bins=50, alpha=0.7, color='orange', edgecolor='black')
    axes[1,1].set_xlabel('Creation Time [ns]')
    axes[1,1].set_ylabel('Number of Photons')
    axes[1,1].set_title('Time Distribution')
    
    # 6. Track distance vs time
    scatter_time = axes[1,2].scatter(primary_times, track_distances, c=primary_z, 
                                    s=10, cmap='viridis', alpha=0.7)
    axes[1,2].set_xlabel('Creation Time [ns]')
    axes[1,2].set_ylabel('Distance to Track [m]')
    axes[1,2].set_title('Track Distance vs Time (colored by Z)')
    axes[1,2].set_yscale('log')
    plt.colorbar(scatter_time, ax=axes[1,2], label='Z Position [m]')
    
    plt.tight_layout()
    plt.show()
    
    # Additional detailed statistics
    print(f"\\n=== Detailed Statistics ===")
    
    # Binned analysis
    distance_bins = [0, 0.001, 0.01, 0.1, 1.0, 10.0, 100.0]
    bin_labels = ['0-1mm', '1-10mm', '10-100mm', '0.1-1m', '1-10m', '10-100m']
    
    for i in range(len(distance_bins)-1):
        mask = (track_distances >= distance_bins[i]) & (track_distances < distance_bins[i+1])
        count = np.sum(mask)
        percentage = 100 * count / len(track_distances)
        print(f"  {bin_labels[i]}: {count:,} photons ({percentage:.1f}%)")
    
    # Sample positions for very far photons
    if np.sum(very_large) > 0:
        print(f"\\nSample positions of photons > 10m from track:")
        far_indices = np.where(very_large)[0][:10]  # First 10
        for i, idx in enumerate(far_indices):
            print(f"  {i+1}: ({primary_x[idx]:.2f}, {primary_y[idx]:.2f}, {primary_z[idx]:.2f}) m, "
                  f"distance={track_distances[idx]:.2f}m, time={primary_times[idx]:.2f}ns")

if __name__ == "__main__":
    root_file = "build/optical_photons.root"
    if len(sys.argv) > 1:
        root_file = sys.argv[1]
    
    print(f"Analyzing primary muon photons from: {root_file}")
    analysis_data = analyze_primary_muon_photons(root_file)
    
    if analysis_data is not None:
        plot_primary_muon_analysis(analysis_data)