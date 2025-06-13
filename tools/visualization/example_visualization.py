#!/usr/bin/env python3
"""
Example usage of PhotonSim visualization tools.

This script demonstrates how to use the PhotonSimVisualizer class
for analyzing optical photon data.
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from visualize_photons import PhotonSimVisualizer

def analyze_event_statistics(root_file_path):
    """Analyze statistics across all events."""
    
    print("=== PhotonSim Event Analysis ===")
    
    # Load the data
    viz = PhotonSimVisualizer(root_file_path)
    
    print(f"\nDataset Overview:")
    print(f"Number of events: {viz.n_events}")
    print(f"Detector size: ±{viz.detector_size:.1f} m")
    
    # Analyze each event
    energies = []
    photon_counts = []
    
    for i in range(viz.n_events):
        event_data = viz.get_event_data(i)
        energies.append(event_data['primary_energy'])
        photon_counts.append(event_data['n_photons'])
        
        print(f"\nEvent {event_data['event_id']}:")
        print(f"  Primary energy: {event_data['primary_energy']:.1f} MeV")
        print(f"  Optical photons: {event_data['n_photons']:,}")
        
        if event_data['n_photons'] > 0:
            # Calculate spatial distribution
            positions = np.column_stack([
                event_data['pos_x'],
                event_data['pos_y'],
                event_data['pos_z']
            ])
            
            # Statistics
            mean_pos = np.mean(positions, axis=0)
            std_pos = np.std(positions, axis=0)
            max_distance = np.max(np.linalg.norm(positions, axis=1))
            
            print(f"  Mean position: ({mean_pos[0]:.2f}, {mean_pos[1]:.2f}, {mean_pos[2]:.2f}) m")
            print(f"  Position spread: ({std_pos[0]:.2f}, {std_pos[1]:.2f}, {std_pos[2]:.2f}) m")
            print(f"  Max distance from origin: {max_distance:.2f} m")
            
            # Time analysis
            if np.max(event_data['time']) > 0:
                print(f"  Time range: {np.min(event_data['time']):.2f} - {np.max(event_data['time']):.2f} ns")
    
    # Summary statistics
    print(f"\n=== Summary Statistics ===")
    print(f"Energy range: {np.min(energies):.1f} - {np.max(energies):.1f} MeV")
    print(f"Average energy: {np.mean(energies):.1f} ± {np.std(energies):.1f} MeV")
    print(f"Total photons: {np.sum(photon_counts):,}")
    print(f"Average photons per event: {np.mean(photon_counts):.0f} ± {np.std(photon_counts):.0f}")
    
    # Photons per MeV
    photons_per_mev = [pc/e for pc, e in zip(photon_counts, energies)]
    print(f"Photons per MeV: {np.mean(photons_per_mev):.0f} ± {np.std(photons_per_mev):.0f}")

def create_summary_plots(root_file_path):
    """Create summary plots of the simulation data."""
    
    viz = PhotonSimVisualizer(root_file_path)
    
    # Collect data for all events
    energies = []
    photon_counts = []
    
    for i in range(viz.n_events):
        event_data = viz.get_event_data(i)
        energies.append(event_data['primary_energy'])
        photon_counts.append(event_data['n_photons'])
    
    # Create plots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(10, 8))
    fig.suptitle('PhotonSim Simulation Summary', fontsize=16)
    
    # Energy distribution
    ax1.hist(energies, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
    ax1.set_xlabel('Primary Energy [MeV]')
    ax1.set_ylabel('Events')
    ax1.set_title('Primary Particle Energy Distribution')
    ax1.grid(True, alpha=0.3)
    
    # Photon count distribution  
    ax2.hist(photon_counts, bins=20, alpha=0.7, color='lightgreen', edgecolor='black')
    ax2.set_xlabel('Optical Photons')
    ax2.set_ylabel('Events')
    ax2.set_title('Optical Photon Count Distribution')
    ax2.grid(True, alpha=0.3)
    
    # Energy vs Photon count
    ax3.scatter(energies, photon_counts, alpha=0.7, color='coral')
    ax3.set_xlabel('Primary Energy [MeV]')
    ax3.set_ylabel('Optical Photons')
    ax3.set_title('Energy vs Photon Yield')
    ax3.grid(True, alpha=0.3)
    
    # Photons per MeV
    photons_per_mev = [pc/e for pc, e in zip(photon_counts, energies)]
    ax4.bar(range(len(photons_per_mev)), photons_per_mev, alpha=0.7, color='gold')
    ax4.set_xlabel('Event Number')
    ax4.set_ylabel('Photons per MeV')
    ax4.set_title('Cherenkov Yield Efficiency')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    
    return fig

def demo_interactive_visualization(root_file_path):
    """Demonstrate interactive visualization capabilities."""
    
    print("=== Interactive Visualization Demo ===")
    
    # Create visualizer
    viz = PhotonSimVisualizer(root_file_path)
    
    # Show specific event
    print(f"\nDisplaying Event 0:")
    viz.plot_event(0)
    plt.show()
    
    print("\nUse arrow keys or 'n'/'p' to navigate between events")
    print("Press 'r' to refresh the current view")
    
    # Start interactive mode
    viz.create_interactive_plot()

def main():
    """Main demonstration function."""
    
    import sys
    import os
    
    # Default ROOT file (relative to PhotonSim root)
    root_file = "../../build/optical_photons.root"
    
    # If running from PhotonSim root, try that path too
    if not os.path.exists(root_file):
        root_file = "build/optical_photons.root"
    
    # Check if file exists
    if not os.path.exists(root_file):
        print(f"Error: ROOT file '{root_file}' not found")
        print("Please run PhotonSim first to generate data:")
        print("  ./PhotonSim")
        sys.exit(1)
    
    print("PhotonSim Visualization Example")
    print("=" * 40)
    
    try:
        # Run analysis
        analyze_event_statistics(root_file)
        
        # Create summary plots
        print(f"\n=== Creating Summary Plots ===")
        create_summary_plots(root_file)
        
        # Interactive visualization
        response = input("\nStart interactive 3D visualization? (y/n): ")
        if response.lower() in ['y', 'yes']:
            demo_interactive_visualization(root_file)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()