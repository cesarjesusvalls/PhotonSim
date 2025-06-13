#!/usr/bin/env python3
"""
Physics validation script for PhotonSim data.

This script validates that the optical photon data obeys fundamental physics
constraints, particularly the speed of light limit.
"""

import numpy as np
import matplotlib.pyplot as plt
import uproot
import sys
import os

# Physical constants
SPEED_OF_LIGHT = 0.299792458  # m/ns (speed of light in vacuum)
SPEED_OF_LIGHT_WATER = 0.225  # m/ns (approximate speed of light in water, n≈1.33)

def load_photon_data(root_file_path):
    """Load all photon data from ROOT file."""
    with uproot.open(root_file_path) as f:
        tree = f['OpticalPhotons']
        
        data = {
            'event_ids': tree['EventID'].array(library='np'),
            'primary_energies': tree['PrimaryEnergy'].array(library='np'),
            'n_photons': tree['NOpticalPhotons'].array(library='np'),
            'pos_x': tree['PhotonPosX'].array(library='np'),
            'pos_y': tree['PhotonPosY'].array(library='np'), 
            'pos_z': tree['PhotonPosZ'].array(library='np'),
            'dir_x': tree['PhotonDirX'].array(library='np'),
            'dir_y': tree['PhotonDirY'].array(library='np'),
            'dir_z': tree['PhotonDirZ'].array(library='np'),
            'times': tree['PhotonTime'].array(library='np'),
        }
        
        # Flatten arrays and convert units
        all_pos_x = np.concatenate(data['pos_x']) / 1000.0  # mm to m
        all_pos_y = np.concatenate(data['pos_y']) / 1000.0  # mm to m  
        all_pos_z = np.concatenate(data['pos_z']) / 1000.0  # mm to m
        all_times = np.concatenate(data['times'])  # already in ns
        
        # Calculate distances from origin (particle gun position at 0,0,0)
        distances = np.sqrt(all_pos_x**2 + all_pos_y**2 + all_pos_z**2)
        
        return {
            'positions': np.column_stack([all_pos_x, all_pos_y, all_pos_z]),
            'distances': distances,
            'times': all_times,
            'event_data': data
        }

def validate_speed_of_light(distances, times, c=SPEED_OF_LIGHT_WATER):
    """Check that no photon violates speed of light constraint."""
    
    # Calculate maximum allowed distance for each photon
    max_allowed_distance = times * c
    
    # Find violations
    violations = distances > max_allowed_distance
    n_violations = np.sum(violations)
    
    print(f"=== Speed of Light Validation ===")
    print(f"Speed of light used: {c:.3f} m/ns (in water)")
    print(f"Total photons: {len(distances):,}")
    print(f"Violations: {n_violations:,} ({100*n_violations/len(distances):.2f}%)")
    
    if n_violations > 0:
        print(f"Maximum violation: {np.max(distances - max_allowed_distance):.3f} m")
        violation_indices = np.where(violations)[0]
        print(f"Example violations:")
        for i in violation_indices[:5]:  # Show first 5 violations
            print(f"  Photon {i}: distance={distances[i]:.3f}m, time={times[i]:.3f}ns, "
                  f"max_allowed={max_allowed_distance[i]:.3f}m, "
                  f"excess={distances[i] - max_allowed_distance[i]:.3f}m")
    else:
        print("✓ All photons respect speed of light constraint!")
    
    return violations

def analyze_time_distributions(data):
    """Analyze photon time distributions."""
    
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    fig.suptitle('Photon Time Distribution Analysis', fontsize=16)
    
    # Overall time distribution
    ax1 = axes[0, 0]
    ax1.hist(data['times'], bins=50, alpha=0.7, color='skyblue', edgecolor='black')
    ax1.set_xlabel('Creation Time [ns]')
    ax1.set_ylabel('Number of Photons')
    ax1.set_title('Overall Time Distribution')
    ax1.grid(True, alpha=0.3)
    
    # Time vs distance scatter plot
    ax2 = axes[0, 1]
    scatter = ax2.scatter(data['times'], data['distances'], alpha=0.6, s=1, c='coral')
    
    # Add speed of light lines
    t_max = np.max(data['times'])
    t_line = np.linspace(0, t_max, 100)
    ax2.plot(t_line, t_line * SPEED_OF_LIGHT, 'r--', linewidth=2, 
             label=f'c in vacuum ({SPEED_OF_LIGHT:.3f} m/ns)')
    ax2.plot(t_line, t_line * SPEED_OF_LIGHT_WATER, 'b--', linewidth=2,
             label=f'c in water ({SPEED_OF_LIGHT_WATER:.3f} m/ns)')
    
    ax2.set_xlabel('Creation Time [ns]')
    ax2.set_ylabel('Distance from Origin [m]')
    ax2.set_title('Time vs Distance')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Time distribution per event
    ax3 = axes[1, 0]
    event_data = data['event_data']
    n_events = len(event_data['event_ids'])
    
    for i in range(min(n_events, 3)):  # Show first 3 events
        event_times = event_data['times'][i]
        if len(event_times) > 0:
            ax3.hist(event_times, bins=30, alpha=0.6, 
                    label=f'Event {event_data["event_ids"][i]} ({len(event_times):,} photons)')
    
    ax3.set_xlabel('Creation Time [ns]')
    ax3.set_ylabel('Number of Photons')
    ax3.set_title('Time Distribution per Event')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Distance distribution
    ax4 = axes[1, 1]
    ax4.hist(data['distances'], bins=50, alpha=0.7, color='lightgreen', edgecolor='black')
    ax4.set_xlabel('Distance from Origin [m]')
    ax4.set_ylabel('Number of Photons')
    ax4.set_title('Distance Distribution')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig

def analyze_time_distance_correlation(data):
    """Detailed analysis of time-distance correlation."""
    
    times = data['times']
    distances = data['distances']
    
    print(f"\n=== Time-Distance Correlation Analysis ===")
    print(f"Time range: {np.min(times):.3f} - {np.max(times):.3f} ns")
    print(f"Distance range: {np.min(distances):.3f} - {np.max(distances):.3f} m")
    
    # Calculate correlation coefficient
    correlation = np.corrcoef(times, distances)[0, 1]
    print(f"Correlation coefficient: {correlation:.3f}")
    
    # Binned analysis
    time_bins = np.linspace(0, np.max(times), 20)
    bin_centers = (time_bins[:-1] + time_bins[1:]) / 2
    mean_distances = []
    max_distances = []
    
    for i in range(len(time_bins) - 1):
        mask = (times >= time_bins[i]) & (times < time_bins[i+1])
        if np.sum(mask) > 0:
            mean_distances.append(np.mean(distances[mask]))
            max_distances.append(np.max(distances[mask]))
        else:
            mean_distances.append(0)
            max_distances.append(0)
    
    # Plot binned analysis
    fig, ax = plt.subplots(1, 1, figsize=(8, 5))
    
    ax.plot(bin_centers, mean_distances, 'bo-', label='Mean distance per time bin')
    ax.plot(bin_centers, max_distances, 'ro-', label='Max distance per time bin')
    
    # Speed of light constraints
    ax.plot(bin_centers, bin_centers * SPEED_OF_LIGHT, 'r--', 
            label=f'c in vacuum ({SPEED_OF_LIGHT:.3f} m/ns)')
    ax.plot(bin_centers, bin_centers * SPEED_OF_LIGHT_WATER, 'b--',
            label=f'c in water ({SPEED_OF_LIGHT_WATER:.3f} m/ns)')
    
    ax.set_xlabel('Time [ns]')
    ax.set_ylabel('Distance [m]')
    ax.set_title('Time vs Distance - Binned Analysis')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig

def print_summary_statistics(data):
    """Print comprehensive summary statistics."""
    
    times = data['times']
    distances = data['distances']
    positions = data['positions']
    
    print(f"\n=== Summary Statistics ===")
    print(f"Total photons: {len(times):,}")
    print(f"Time statistics:")
    print(f"  Mean: {np.mean(times):.3f} ns")
    print(f"  Std:  {np.std(times):.3f} ns")
    print(f"  Min:  {np.min(times):.3f} ns")
    print(f"  Max:  {np.max(times):.3f} ns")
    
    print(f"Distance statistics:")
    print(f"  Mean: {np.mean(distances):.3f} m")
    print(f"  Std:  {np.std(distances):.3f} m")
    print(f"  Min:  {np.min(distances):.3f} m")
    print(f"  Max:  {np.max(distances):.3f} m")
    
    print(f"Position statistics:")
    print(f"  X: {np.min(positions[:, 0]):.1f} to {np.max(positions[:, 0]):.1f} m")
    print(f"  Y: {np.min(positions[:, 1]):.1f} to {np.max(positions[:, 1]):.1f} m")
    print(f"  Z: {np.min(positions[:, 2]):.1f} to {np.max(positions[:, 2]):.1f} m")
    
    # Calculate effective speeds
    non_zero_times = times[times > 0]
    non_zero_distances = distances[times > 0]
    if len(non_zero_times) > 0:
        effective_speeds = non_zero_distances / non_zero_times
        print(f"Effective speeds (distance/time):")
        print(f"  Mean: {np.mean(effective_speeds):.3f} m/ns")
        print(f"  Max:  {np.max(effective_speeds):.3f} m/ns")
        print(f"  Comparison to c in water: {np.max(effective_speeds)/SPEED_OF_LIGHT_WATER:.2f}x")

def main():
    """Main analysis function."""
    
    # Default ROOT file (try different paths)
    root_file = "../../build/optical_photons.root"
    if not os.path.exists(root_file):
        root_file = "build/optical_photons.root"
    
    if len(sys.argv) > 1:
        root_file = sys.argv[1]
    
    # Check if file exists
    if not os.path.exists(root_file):
        print(f"Error: ROOT file '{root_file}' not found")
        print("Please run PhotonSim first to generate data:")
        print("  ./PhotonSim")
        sys.exit(1)
    
    print("PhotonSim Physics Validation")
    print("=" * 50)
    
    try:
        # Load data
        print("Loading photon data...")
        data = load_photon_data(root_file)
        
        # Print summary statistics
        print_summary_statistics(data)
        
        # Validate speed of light constraint
        violations = validate_speed_of_light(data['distances'], data['times'])
        
        # Create analysis plots
        print(f"\nCreating time distribution plots...")
        time_fig = analyze_time_distributions(data)
        
        print(f"Creating correlation analysis...")
        corr_fig = analyze_time_distance_correlation(data)
        
        # Show plots
        plt.show()
        
        # Final verdict
        print(f"\n=== PHYSICS VALIDATION RESULT ===")
        n_violations = np.sum(violations)
        if n_violations == 0:
            print("✅ PASS: All photons respect causality constraints")
        else:
            print(f"❌ FAIL: {n_violations:,} photons violate speed of light")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()