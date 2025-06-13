#!/usr/bin/env python3
"""
Analyze PhotonSim optical photon data for physics validation.

This script examines the stored photon data to understand:
- What processes are creating photons
- Spatial distribution of photon creation points
- Time distribution
- Potential issues with data collection
"""

import numpy as np
import matplotlib.pyplot as plt
import uproot
import sys

def analyze_photon_data(root_file_path):
    """Analyze the photon data from ROOT file."""
    
    try:
        with uproot.open(root_file_path) as file:
            tree = file["OpticalPhotons"]
            
            # Load all data
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
            }
            
            n_events = len(data['EventID'])
            print(f"=== PhotonSim Data Analysis ===")
            print(f"Number of events: {n_events}")
            print(f"Total photons: {np.sum(data['NOpticalPhotons']):,}")
            print()
            
            # Analyze processes creating photons
            print("=== Process Analysis ===")
            all_processes = []
            all_parents = []
            for event_processes in data['PhotonProcess']:
                all_processes.extend(event_processes)
            for event_parents in data['PhotonParent']:
                all_parents.extend(event_parents)
            
            unique_processes, counts = np.unique(all_processes, return_counts=True)
            for process, count in zip(unique_processes, counts):
                percentage = 100 * count / len(all_processes)
                print(f"{process}: {count:,} photons ({percentage:.1f}%)")
            
            print("\n=== Parent Particle Analysis ===")
            unique_parents, parent_counts = np.unique(all_parents, return_counts=True)
            for parent, count in zip(unique_parents, parent_counts):
                percentage = 100 * count / len(all_parents)
                print(f"{parent}: {count:,} photons ({percentage:.1f}%)")
            print()
            
            # Analyze spatial distribution for first event
            if n_events > 0:
                event_id = 0
                print(f"=== Spatial Analysis (Event {event_id}) ===")
                pos_x = data['PhotonPosX'][event_id]  # in mm
                pos_y = data['PhotonPosY'][event_id]  # in mm
                pos_z = data['PhotonPosZ'][event_id]  # in mm
                times = data['PhotonTime'][event_id]  # in ns
                processes = data['PhotonProcess'][event_id]
                parents = data['PhotonParent'][event_id]
                
                print(f"Photons in event: {len(pos_x):,}")
                print(f"Primary energy: {data['PrimaryEnergy'][event_id]:.1f} MeV")
                print()
                
                # Position statistics
                print("Position ranges (mm):")
                print(f"  X: {np.min(pos_x):.1f} to {np.max(pos_x):.1f}")
                print(f"  Y: {np.min(pos_y):.1f} to {np.max(pos_y):.1f}")
                print(f"  Z: {np.min(pos_z):.1f} to {np.max(pos_z):.1f}")
                print()
                
                # Distance from origin
                distances = np.sqrt(pos_x**2 + pos_y**2 + pos_z**2)
                print(f"Distance from origin (mm):")
                print(f"  Min: {np.min(distances):.1f}")
                print(f"  Max: {np.max(distances):.1f}")
                print(f"  Mean: {np.mean(distances):.1f}")
                print(f"  Median: {np.median(distances):.1f}")
                print()
                
                # Time analysis
                print(f"Time distribution (ns):")
                print(f"  Min: {np.min(times):.3f}")
                print(f"  Max: {np.max(times):.3f}")
                print(f"  Mean: {np.mean(times):.3f}")
                print()
                
                # Look at photons very close to origin vs far away
                close_mask = distances < 1000  # Within 1 meter
                far_mask = distances > 10000   # Beyond 10 meters
                
                print(f"Photons within 1m of origin: {np.sum(close_mask):,}")
                print(f"Photons beyond 10m from origin: {np.sum(far_mask):,}")
                
                if np.sum(close_mask) > 0:
                    close_processes = [processes[i] for i in range(len(processes)) if close_mask[i]]
                    unique_close, counts_close = np.unique(close_processes, return_counts=True)
                    print("Processes for photons near origin:")
                    for proc, count in zip(unique_close, counts_close):
                        print(f"  {proc}: {count}")
                
                if np.sum(far_mask) > 0:
                    far_processes = [processes[i] for i in range(len(processes)) if far_mask[i]]
                    unique_far, counts_far = np.unique(far_processes, return_counts=True)
                    print("Processes for photons far from origin:")
                    for proc, count in zip(unique_far, counts_far):
                        print(f"  {proc}: {count}")
                print()
                
                # Check if photons are at detector boundaries
                detector_half_size = 50000  # 50m in mm (from code inspection)
                boundary_tolerance = 1000   # 1m tolerance
                
                at_boundary_x = (np.abs(np.abs(pos_x) - detector_half_size) < boundary_tolerance)
                at_boundary_y = (np.abs(np.abs(pos_y) - detector_half_size) < boundary_tolerance)
                at_boundary_z = (np.abs(np.abs(pos_z) - detector_half_size) < boundary_tolerance)
                at_boundary = at_boundary_x | at_boundary_y | at_boundary_z
                
                print(f"Photons at detector boundaries (±{detector_half_size/1000}m): {np.sum(at_boundary):,}")
                
                # Analyze photons by parent particle type
                print("\n=== Photons by Parent Type ===")
                unique_event_parents, event_parent_counts = np.unique(parents, return_counts=True)
                for parent, count in zip(unique_event_parents, event_parent_counts):
                    percentage = 100 * count / len(parents)
                    print(f"  {parent}: {count:,} photons ({percentage:.1f}%)")
                
                # Sample a few photon positions for detailed inspection
                print("\n=== Sample Photon Positions (first 10) ===")
                for i in range(min(10, len(pos_x))):
                    print(f"Photon {i}: ({pos_x[i]/1000:.2f}, {pos_y[i]/1000:.2f}, {pos_z[i]/1000:.2f}) m, "
                          f"t={times[i]:.3f} ns, process={processes[i]}, parent={parents[i]}")
                
                # Focus on photons created by different parent types
                primary_mask = np.array([p == "Primary" for p in parents])
                secondary_mask = ~primary_mask
                
                if np.sum(primary_mask) > 0:
                    primary_distances = np.sqrt(pos_x[primary_mask]**2 + pos_y[primary_mask]**2 + pos_z[primary_mask]**2)
                    print(f"\nPhotons from PRIMARY particle: {np.sum(primary_mask):,}")
                    print(f"  Distance range: {np.min(primary_distances)/1000:.2f} to {np.max(primary_distances)/1000:.2f} m")
                    print(f"  Mean distance: {np.mean(primary_distances)/1000:.2f} m")
                
                if np.sum(secondary_mask) > 0:
                    secondary_distances = np.sqrt(pos_x[secondary_mask]**2 + pos_y[secondary_mask]**2 + pos_z[secondary_mask]**2)
                    print(f"\nPhotons from SECONDARY particles: {np.sum(secondary_mask):,}")
                    print(f"  Distance range: {np.min(secondary_distances)/1000:.2f} to {np.max(secondary_distances)/1000:.2f} m")
                    print(f"  Mean distance: {np.mean(secondary_distances)/1000:.2f} m")
                    
                    # Show what types of secondary particles
                    secondary_parents = [parents[i] for i in range(len(parents)) if secondary_mask[i]]
                    unique_secondary, secondary_counts = np.unique(secondary_parents, return_counts=True)
                    print("  Secondary particle types:")
                    for parent, count in zip(unique_secondary, secondary_counts):
                        print(f"    {parent}: {count:,} photons")
                
                return data, event_id
                
    except Exception as e:
        print(f"Error analyzing ROOT file: {e}")
        return None, None

def calculate_distance_to_track(pos_x, pos_y, pos_z, track_start, track_direction):
    """
    Calculate perpendicular distance from photon positions to the straight-line track.
    
    Args:
        pos_x, pos_y, pos_z: Arrays of photon positions (in meters)
        track_start: Track starting point [x, y, z] (in meters)
        track_direction: Track direction vector [dx, dy, dz] (normalized)
    
    Returns:
        Array of perpendicular distances from each photon to the track line
    """
    # Convert to numpy arrays
    photon_positions = np.column_stack([pos_x, pos_y, pos_z])
    track_start = np.array(track_start)
    track_direction = np.array(track_direction)
    
    # Normalize track direction
    track_direction = track_direction / np.linalg.norm(track_direction)
    
    distances = []
    for pos in photon_positions:
        # Vector from track start to photon position
        to_photon = pos - track_start
        
        # Project onto track direction to find closest point on track
        projection_length = np.dot(to_photon, track_direction)
        closest_point_on_track = track_start + projection_length * track_direction
        
        # Distance from photon to closest point on track
        distance = np.linalg.norm(pos - closest_point_on_track)
        distances.append(distance)
    
    return np.array(distances)

def plot_spatial_distribution(data, event_id=0):
    """Create plots to visualize the spatial distribution."""
    
    pos_x = data['PhotonPosX'][event_id] / 1000.0  # Convert to meters
    pos_y = data['PhotonPosY'][event_id] / 1000.0
    pos_z = data['PhotonPosZ'][event_id] / 1000.0
    times = data['PhotonTime'][event_id]
    parents = data['PhotonParent'][event_id]
    
    fig, axes = plt.subplots(2, 3, figsize=(12, 8))
    fig.suptitle(f'PRIMARY Photon Distribution - Event {event_id}', fontsize=12)
    
    # Assume muon track starts at origin and goes in +Z direction (simplified)
    # In reality, we'd need to extract the actual track from the primary particle
    track_start = [0.0, 0.0, 0.0]  # Origin
    track_direction = [0.0, 0.0, 1.0]  # +Z direction
    
    # Calculate distance to track for all photons
    track_distances = calculate_distance_to_track(pos_x, pos_y, pos_z, track_start, track_direction)
    
    # Separate by parent type (should be mostly/all primary now)
    primary_mask = np.array([p == "Primary" for p in parents])
    muon_mask = np.array([p == "mu-" for p in parents])
    electron_mask = np.array([p == "e-" for p in parents])
    
    # XY projection colored by time
    scatter1 = axes[0,0].scatter(pos_x, pos_y, c=times, s=1, alpha=0.6, cmap='plasma')
    axes[0,0].set_xlabel('X [m]')
    axes[0,0].set_ylabel('Y [m]')
    axes[0,0].set_title('XY Projection (Time Colored)')
    axes[0,0].set_aspect('equal')
    axes[0,0].axhline(0, color='black', alpha=0.3, linewidth=0.5)
    axes[0,0].axvline(0, color='black', alpha=0.3, linewidth=0.5)
    
    # XZ projection with track line
    scatter2 = axes[0,1].scatter(pos_x, pos_z, c=times, s=1, alpha=0.6, cmap='plasma')
    # Draw the assumed track line
    z_track = np.linspace(0, 50, 100)
    x_track = np.zeros_like(z_track)
    axes[0,1].plot(x_track, z_track, 'k-', linewidth=2, label='Assumed track')
    axes[0,1].set_xlabel('X [m]')
    axes[0,1].set_ylabel('Z [m]')
    axes[0,1].set_title('XZ Projection with Track')
    axes[0,1].legend()
    
    # Distance to track histogram - THIS IS THE KEY PLOT
    axes[0,2].hist(track_distances, bins=50, alpha=0.7, color='red', 
                   label=f'PRIMARY photons (n={len(track_distances)})')
    axes[0,2].set_xlabel('Distance to Track [m]')
    axes[0,2].set_ylabel('Count')
    axes[0,2].set_title('Distance to Muon Track')
    axes[0,2].legend()
    axes[0,2].set_yscale('log')
    
    # Statistics
    print(f"\n=== Track Distance Analysis (PRIMARY ONLY) ===")
    print(f"Primary photons - Distance to track:")
    print(f"  Mean: {np.mean(track_distances):.6f} m")
    print(f"  Median: {np.median(track_distances):.6f} m")
    print(f"  95th percentile: {np.percentile(track_distances, 95):.6f} m")
    print(f"  Max: {np.max(track_distances):.6f} m")
    print(f"  Count: {len(track_distances):,} photons")
    
    # Distance histogram
    distances = np.sqrt(pos_x**2 + pos_y**2 + pos_z**2)
    axes[1,0].hist(distances, bins=50, alpha=0.7, edgecolor='black')
    axes[1,0].set_xlabel('Distance from Origin [m]')
    axes[1,0].set_ylabel('Number of Photons')
    axes[1,0].set_title('Radial Distribution')
    axes[1,0].axvline(np.mean(distances), color='red', linestyle='--', label=f'Mean: {np.mean(distances):.1f}m')
    axes[1,0].legend()
    
    # Time histogram
    axes[1,1].hist(times, bins=50, alpha=0.7, color='red', label='PRIMARY photons')
    axes[1,1].set_xlabel('Creation Time [ns]')
    axes[1,1].set_ylabel('Count')
    axes[1,1].set_title('Time Distribution')
    axes[1,1].legend()
    
    # Track distance vs time scatter plot
    scatter = axes[1,2].scatter(times, track_distances, c=times, s=1, alpha=0.6, cmap='plasma')
    axes[1,2].set_xlabel('Creation Time [ns]')
    axes[1,2].set_ylabel('Distance to Track [m]')
    axes[1,2].set_title('Track Distance vs Time')
    axes[1,2].set_yscale('log')
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    root_file = "build/optical_photons.root"
    if len(sys.argv) > 1:
        root_file = sys.argv[1]
    
    print(f"Analyzing: {root_file}")
    data, event_id = analyze_photon_data(root_file)
    
    if data is not None:
        plot_spatial_distribution(data, event_id)