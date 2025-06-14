#!/usr/bin/env python3
"""
Demonstration of the 3D photon table usage.
Shows how to create, save, load, and query the table.
"""

import numpy as np
import matplotlib.pyplot as plt
from query_3d_table import PhotonTable3DQuery

def demonstrate_3d_table():
    """Demonstrate the 3D photon table functionality."""
    
    print("=== 3D Photon Table Demonstration ===\n")
    
    # Load the table
    print("1. Loading 3D table...")
    table = PhotonTable3DQuery("final_3d_table")
    
    # Show statistics
    print("\n2. Table statistics:")
    table.print_statistics()
    
    # Demonstrate queries
    print("\n3. Example queries:")
    
    # Query at different energies and angles
    test_cases = [
        {"name": "Low energy, small angle", "energy": 150, "angle": 0.1, "distance": 100},
        {"name": "Medium energy, medium angle", "energy": 250, "angle": 0.3, "distance": 500},
        {"name": "High energy, large angle", "energy": 400, "angle": 0.6, "distance": 1000},
        {"name": "Edge case", "energy": 100, "angle": 0.8, "distance": 10000},
    ]
    
    for case in test_cases:
        nearest = table.query_nearest(case["energy"], case["angle"], case["distance"])
        interp = table.query_interpolate(case["energy"], case["angle"], case["distance"])
        
        print(f"\n{case['name']}:")
        print(f"  E={case['energy']} MeV, θ={case['angle']:.1f} rad, d={case['distance']} mm")
        print(f"  Nearest neighbor: {nearest:.1f} photons")
        print(f"  Interpolated: {interp:.1f} photons")
    
    # Create a visualization of queries across parameter space
    print("\n4. Creating parameter space visualization...")
    
    # Fix distance and vary energy and angle
    fixed_distance = 1000  # mm
    
    energies = np.linspace(table.energy_range[0], table.energy_range[1], 20)
    angles = np.linspace(table.angle_range[0], table.angle_range[1], 25)
    
    E_grid, A_grid = np.meshgrid(energies, angles)
    photon_counts = np.zeros_like(E_grid)
    
    for i, energy in enumerate(energies):
        for j, angle in enumerate(angles):
            photon_counts[j, i] = table.query_interpolate(energy, angle, fixed_distance)
    
    # Create visualization
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # 2D map
    im = ax1.imshow(photon_counts, origin='lower', aspect='auto', cmap='viridis',
                   extent=[energies[0], energies[-1], angles[0], angles[-1]])
    ax1.set_xlabel('Energy (MeV)')
    ax1.set_ylabel('Opening Angle (rad)')
    ax1.set_title(f'Photon Count at Distance = {fixed_distance} mm')
    plt.colorbar(im, ax=ax1, label='Photon Count')
    
    # 1D slices
    mid_angle_idx = len(angles) // 2
    mid_energy_idx = len(energies) // 2
    
    ax2.plot(energies, photon_counts[mid_angle_idx, :], 'b-', 
            label=f'θ = {angles[mid_angle_idx]:.2f} rad')
    ax2_twin = ax2.twinx()
    ax2_twin.plot(angles, photon_counts[:, mid_energy_idx], 'r-',
                 label=f'E = {energies[mid_energy_idx]:.0f} MeV')
    
    ax2.set_xlabel('Energy (MeV)')
    ax2.set_ylabel('Photon Count (θ fixed)', color='b')
    ax2_twin.set_ylabel('Photon Count (E fixed)', color='r')
    ax2.set_title('1D Slices through Table')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('final_3d_table/parameter_space_demo.png', dpi=200, bbox_inches='tight')
    print("Parameter space visualization saved to: final_3d_table/parameter_space_demo.png")
    
    # Show usage example
    print(f"\n5. Usage example in simulation code:")
    print(f"```python")
    print(f"# Load the 3D table")
    print(f"from query_3d_table import PhotonTable3DQuery")
    print(f"table = PhotonTable3DQuery('final_3d_table')")
    print(f"")
    print(f"# Query for specific muon and photon parameters")
    print(f"muon_energy = 300  # MeV") 
    print(f"opening_angle = 0.2  # radians")
    print(f"distance_from_track = 500  # mm")
    print(f"")
    print(f"expected_photons = table.query_interpolate(muon_energy, opening_angle, distance_from_track)")
    print(f"print(f'Expected photons: {{expected_photons:.1f}}')")
    print(f"```")
    
    print(f"\n=== Demo Complete ===")
    print(f"The 3D table provides a lookup for Cherenkov photon production as a function of:")
    print(f"- Muon energy: {table.energy_range[0]:.1f} - {table.energy_range[1]:.1f} MeV")
    print(f"- Opening angle: {table.angle_range[0]:.3f} - {table.angle_range[1]:.3f} rad")
    print(f"- Distance from origin: {table.distance_range[0]:.1f} - {table.distance_range[1]:.0f} mm")

if __name__ == "__main__":
    demonstrate_3d_table()