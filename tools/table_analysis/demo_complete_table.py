#!/usr/bin/env python3
"""
Demonstration of the complete 3D photon table using all 100 events.
"""

import numpy as np
import matplotlib.pyplot as plt
from query_3d_table import PhotonTable3DQuery

def demo_complete_table():
    """Demonstrate the complete 3D photon table."""
    
    print("=== Complete 3D Photon Table Demo ===")
    print("Using ALL 100 events from 1k muon simulation\n")
    
    # Load the complete table
    print("1. Loading complete 3D table...")
    table = PhotonTable3DQuery("complete_3d_table")
    
    # Show detailed statistics
    print("\n2. Detailed table statistics:")
    table.print_statistics()
    
    # Show parameter ranges
    print(f"\n3. Parameter ranges covered:")
    print(f"   Muon Energy: {table.energy_range[0]:.1f} - {table.energy_range[1]:.1f} MeV")
    print(f"   Opening Angle: {table.angle_range[0]:.3f} - {table.angle_range[1]:.3f} rad")
    print(f"   Distance: {table.distance_range[0]:.0f} - {table.distance_range[1]:.0f} mm")
    print(f"   Bin resolution: {len(table.energy_centers)} × {len(table.angle_centers)} × {len(table.distance_centers)}")
    
    # Demonstrate realistic queries
    print(f"\n4. Realistic physics queries:")
    
    physics_queries = [
        {"name": "Low energy muon, forward photons", 
         "energy": 150, "angle": 0.05, "distance": 100,
         "description": "Photons very close to track, small angles"},
        
        {"name": "Medium energy muon, moderate angles", 
         "energy": 250, "angle": 0.3, "distance": 1000,
         "description": "Typical Cherenkov cone"},
        
        {"name": "High energy muon, large angles", 
         "energy": 450, "angle": 0.8, "distance": 5000,
         "description": "Wide angle photons, further from track"},
        
        {"name": "Very high energy, edge of cone", 
         "energy": 480, "angle": 1.0, "distance": 10000,
         "description": "Near maximum Cherenkov angle"},
        
        {"name": "Track center, very close", 
         "energy": 300, "angle": 0.02, "distance": 10,
         "description": "Right at the muon track"},
    ]
    
    for i, case in enumerate(physics_queries):
        result = table.query_interpolate(case["energy"], case["angle"], case["distance"])
        
        print(f"\n   Query {i+1}: {case['name']}")
        print(f"   E={case['energy']} MeV, θ={case['angle']:.2f} rad, d={case['distance']} mm")
        print(f"   → {result:.1f} photons expected")
        print(f"   ({case['description']})")
    
    # Create parameter sweep visualization
    print(f"\n5. Creating parameter sweep visualizations...")
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Complete 3D Table Parameter Sweeps', fontsize=16)
    
    # Sweep 1: Energy vs Angle (fixed distance)
    fixed_distance = 1000  # mm
    energies = np.linspace(table.energy_range[0], table.energy_range[1], 30)
    angles = np.linspace(table.angle_range[0], table.angle_range[1], 40)
    
    E_grid, A_grid = np.meshgrid(energies, angles)
    photon_counts_1 = np.zeros_like(E_grid)
    
    for i, energy in enumerate(energies):
        for j, angle in enumerate(angles):
            photon_counts_1[j, i] = table.query_interpolate(energy, angle, fixed_distance)
    
    im1 = axes[0,0].imshow(photon_counts_1, origin='lower', aspect='auto', cmap='plasma',
                          extent=[energies[0], energies[-1], angles[0], angles[-1]])
    axes[0,0].set_xlabel('Energy (MeV)')
    axes[0,0].set_ylabel('Opening Angle (rad)')
    axes[0,0].set_title(f'Photon Count at d={fixed_distance} mm')
    plt.colorbar(im1, ax=axes[0,0], label='Photon Count')
    
    # Sweep 2: Energy vs Distance (fixed angle)
    fixed_angle = 0.3  # rad
    distances = np.linspace(100, 20000, 30)
    
    E_grid2, D_grid = np.meshgrid(energies, distances)
    photon_counts_2 = np.zeros_like(E_grid2)
    
    for i, energy in enumerate(energies):
        for j, distance in enumerate(distances):
            photon_counts_2[j, i] = table.query_interpolate(energy, fixed_angle, distance)
    
    im2 = axes[0,1].imshow(photon_counts_2, origin='lower', aspect='auto', cmap='plasma',
                          extent=[energies[0], energies[-1], distances[0], distances[-1]])
    axes[0,1].set_xlabel('Energy (MeV)')
    axes[0,1].set_ylabel('Distance (mm)')
    axes[0,1].set_title(f'Photon Count at θ={fixed_angle:.1f} rad')
    plt.colorbar(im2, ax=axes[0,1], label='Photon Count')
    
    # 1D Energy dependence
    fixed_angle_1d = 0.2
    fixed_distance_1d = 500
    
    energy_sweep = []
    for energy in energies:
        count = table.query_interpolate(energy, fixed_angle_1d, fixed_distance_1d)
        energy_sweep.append(count)
    
    axes[1,0].plot(energies, energy_sweep, 'b-', linewidth=2, marker='o', markersize=3)
    axes[1,0].set_xlabel('Energy (MeV)')
    axes[1,0].set_ylabel('Photon Count')
    axes[1,0].set_title(f'Energy Dependence (θ={fixed_angle_1d}, d={fixed_distance_1d}mm)')
    axes[1,0].grid(True, alpha=0.3)
    
    # 1D Angular dependence
    fixed_energy_1d = 300
    
    angle_sweep = []
    for angle in angles:
        count = table.query_interpolate(fixed_energy_1d, angle, fixed_distance_1d)
        angle_sweep.append(count)
    
    axes[1,1].plot(angles, angle_sweep, 'g-', linewidth=2, marker='o', markersize=3)
    axes[1,1].set_xlabel('Opening Angle (rad)')
    axes[1,1].set_ylabel('Photon Count')
    axes[1,1].set_title(f'Angular Dependence (E={fixed_energy_1d}MeV, d={fixed_distance_1d}mm)')
    axes[1,1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('complete_3d_table/parameter_sweeps.png', dpi=200, bbox_inches='tight')
    print("Parameter sweep plots saved to: complete_3d_table/parameter_sweeps.png")
    
    # Usage instructions
    print(f"\n6. Usage instructions:")
    print(f"```python")
    print(f"# Import the query class")
    print(f"from query_3d_table import PhotonTable3DQuery")
    print(f"")
    print(f"# Load the complete table")
    print(f"table = PhotonTable3DQuery('complete_3d_table')")
    print(f"")
    print(f"# Query for specific conditions")
    print(f"muon_energy = 350  # MeV")
    print(f"opening_angle = 0.25  # radians (~14 degrees)")
    print(f"distance_from_track = 2000  # mm")
    print(f"")
    print(f"# Get expected photon count")
    print(f"photons = table.query_interpolate(muon_energy, opening_angle, distance_from_track)")
    print(f"print(f'Expected {{photons:.1f}} Cherenkov photons')")
    print(f"```")
    
    print(f"\n=== Complete Table Summary ===")
    stats = table.get_statistics()
    print(f"✓ Based on ALL 100 muon events")
    print(f"✓ {stats['total_photons']:,.0f} photons in lookup table")
    print(f"✓ {stats['non_zero_bins']} non-zero bins ({stats['non_zero_bins']/np.prod(stats['histogram_shape'])*100:.1f}% coverage)")
    print(f"✓ Energy range: {table.energy_range[0]:.1f} - {table.energy_range[1]:.1f} MeV")
    print(f"✓ Full Cherenkov angular range: {table.angle_range[0]:.3f} - {table.angle_range[1]:.3f} rad")
    print(f"✓ Distance range: 0 - {table.distance_range[1]/1000:.0f} m")
    print(f"✓ High-resolution binning: 15 × 20 × 15 = 4,500 bins")

if __name__ == "__main__":
    demo_complete_table()