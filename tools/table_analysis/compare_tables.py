#!/usr/bin/env python3
"""
Compare the partial table (20 events) vs full table (100 events).
"""

import numpy as np
import matplotlib.pyplot as plt
from query_3d_table import PhotonTable3DQuery

def compare_tables():
    """Compare the two 3D tables."""
    
    print("=== 3D Table Comparison ===\n")
    
    # Load both tables
    print("Loading tables...")
    partial_table = PhotonTable3DQuery("final_3d_table")
    full_table = PhotonTable3DQuery("full_3d_table")
    
    print("\n1. Table Statistics Comparison:")
    print("Partial Table (20 events):")
    partial_stats = partial_table.get_statistics()
    for key, value in partial_stats.items():
        print(f"  {key}: {value}")
    
    print("\nFull Table (100 events):")
    full_stats = full_table.get_statistics()
    for key, value in full_stats.items():
        print(f"  {key}: {value}")
    
    print(f"\nImprovement factors:")
    print(f"  Photons: {full_stats['total_photons'] / partial_stats['total_photons']:.1f}x")
    print(f"  Non-zero bins: {full_stats['non_zero_bins'] / partial_stats['non_zero_bins']:.1f}x")
    print(f"  Coverage: {full_stats['non_zero_bins'] / np.prod(full_stats['histogram_shape']) * 100:.1f}% vs {partial_stats['non_zero_bins'] / np.prod(partial_stats['histogram_shape']) * 100:.1f}%")
    
    # Test same queries on both tables
    print(f"\n2. Query Comparison:")
    test_queries = [
        (200, 0.2, 1000),
        (300, 0.4, 5000),
        (400, 0.6, 10000),
        (150, 0.1, 500),
    ]
    
    for i, (energy, angle, distance) in enumerate(test_queries):
        partial_result = partial_table.query_interpolate(energy, angle, distance)
        full_result = full_table.query_interpolate(energy, angle, distance)
        
        print(f"Query {i+1}: E={energy} MeV, θ={angle:.1f} rad, d={distance} mm")
        print(f"  Partial table: {partial_result:.1f} photons")
        print(f"  Full table: {full_result:.1f} photons")
        print(f"  Ratio: {full_result/max(partial_result, 0.1):.1f}x")
    
    # Create visualization comparison
    print(f"\n3. Creating visualization comparison...")
    
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle('3D Table Comparison: Partial (20 events) vs Full (100 events)', fontsize=16)
    
    tables = [partial_table, full_table]
    labels = ['Partial (20 events)', 'Full (100 events)']
    
    for row, (table, label) in enumerate(zip(tables, labels)):
        # Energy projection
        energy_proj = np.sum(table.histogram, axis=(1, 2))
        axes[row, 0].plot(table.energy_centers, energy_proj, 'b-', linewidth=2)
        axes[row, 0].set_xlabel('Energy (MeV)')
        axes[row, 0].set_ylabel('Photon Count')
        axes[row, 0].set_title(f'{label}: Energy Distribution')
        axes[row, 0].grid(True, alpha=0.3)
        
        # Angle projection  
        angle_proj = np.sum(table.histogram, axis=(0, 2))
        axes[row, 1].plot(table.angle_centers, angle_proj, 'g-', linewidth=2)
        axes[row, 1].set_xlabel('Opening Angle (rad)')
        axes[row, 1].set_ylabel('Photon Count')
        axes[row, 1].set_title(f'{label}: Angle Distribution')
        axes[row, 1].grid(True, alpha=0.3)
        
        # Distance projection
        distance_proj = np.sum(table.histogram, axis=(0, 1))
        axes[row, 2].plot(table.distance_centers, distance_proj, 'r-', linewidth=2)
        axes[row, 2].set_xlabel('Distance (mm)')
        axes[row, 2].set_ylabel('Photon Count')
        axes[row, 2].set_title(f'{label}: Distance Distribution')
        axes[row, 2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('table_comparison.png', dpi=200, bbox_inches='tight')
    print("Comparison plot saved to: table_comparison.png")
    
    print(f"\n=== Summary ===")
    print(f"Using ALL 100 events provides:")
    print(f"✓ {full_stats['total_photons'] / partial_stats['total_photons']:.0f}x more photons in the lookup table")
    print(f"✓ {full_stats['non_zero_bins'] / partial_stats['non_zero_bins']:.1f}x better coverage of parameter space")
    print(f"✓ More accurate interpolation across the full energy range (101.7 - 498.1 MeV)")
    print(f"✓ Better statistics for rare parameter combinations")
    
    print(f"\nRecommendation: Use the FULL table (full_3d_table/) for production simulations!")

if __name__ == "__main__":
    compare_tables()