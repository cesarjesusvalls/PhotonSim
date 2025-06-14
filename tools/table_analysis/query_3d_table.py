#!/usr/bin/env python3
"""
Utility to load and query the 3D photon table.
"""

import numpy as np
from pathlib import Path
import argparse

class PhotonTable3DQuery:
    """Query interface for the 3D photon table."""
    
    def __init__(self, table_dir):
        """Load the 3D table from directory."""
        self.table_dir = Path(table_dir)
        
        # Load histogram
        self.histogram = np.load(self.table_dir / "photon_histogram_3d.npy")
        
        # Load metadata
        metadata = np.load(self.table_dir / "table_metadata.npz")
        self.energy_edges = metadata['energy_edges']
        self.angle_edges = metadata['angle_edges']
        self.distance_edges = metadata['distance_edges']
        self.energy_range = metadata['energy_range']
        self.angle_range = metadata['angle_range']
        self.distance_range = metadata['distance_range']
        
        # Calculate bin centers
        self.energy_centers = (self.energy_edges[:-1] + self.energy_edges[1:]) / 2
        self.angle_centers = (self.angle_edges[:-1] + self.angle_edges[1:]) / 2
        self.distance_centers = (self.distance_edges[:-1] + self.distance_edges[1:]) / 2
        
        print(f"Loaded 3D table with shape: {self.histogram.shape}")
        print(f"Energy range: {self.energy_range[0]:.1f} - {self.energy_range[1]:.1f} MeV")
        print(f"Angle range: {self.angle_range[0]:.3f} - {self.angle_range[1]:.3f} rad")
        print(f"Distance range: {self.distance_range[0]:.1f} - {self.distance_range[1]:.1f} mm")
    
    def query_nearest(self, energy, angle, distance):
        """
        Query table using nearest neighbor lookup.
        
        Parameters:
        -----------
        energy : float
            Muon energy in MeV
        angle : float
            Opening angle in radians
        distance : float
            Distance from origin in mm
            
        Returns:
        --------
        float : Photon count from nearest bin
        """
        # Find nearest bin indices
        energy_idx = np.argmin(np.abs(self.energy_centers - energy))
        angle_idx = np.argmin(np.abs(self.angle_centers - angle))
        distance_idx = np.argmin(np.abs(self.distance_centers - distance))
        
        # Check bounds
        if (energy_idx >= len(self.energy_centers) or 
            angle_idx >= len(self.angle_centers) or 
            distance_idx >= len(self.distance_centers)):
            return 0.0
        
        return self.histogram[energy_idx, angle_idx, distance_idx]
    
    def query_interpolate(self, energy, angle, distance):
        """
        Query table using trilinear interpolation.
        
        Parameters:
        -----------
        energy : float
            Muon energy in MeV
        angle : float
            Opening angle in radians
        distance : float
            Distance from origin in mm
            
        Returns:
        --------
        float : Interpolated photon count
        """
        # Check bounds
        if (energy < self.energy_range[0] or energy > self.energy_range[1] or
            angle < self.angle_range[0] or angle > self.angle_range[1] or
            distance < self.distance_range[0] or distance > self.distance_range[1]):
            return 0.0
        
        # Find bin indices for interpolation
        energy_idx = np.searchsorted(self.energy_edges, energy) - 1
        angle_idx = np.searchsorted(self.angle_edges, angle) - 1
        distance_idx = np.searchsorted(self.distance_edges, distance) - 1
        
        # Ensure valid indices
        energy_idx = max(0, min(energy_idx, len(self.energy_centers) - 2))
        angle_idx = max(0, min(angle_idx, len(self.angle_centers) - 2))
        distance_idx = max(0, min(distance_idx, len(self.distance_centers) - 2))
        
        # Get fractional positions within bins
        energy_frac = ((energy - self.energy_edges[energy_idx]) / 
                      (self.energy_edges[energy_idx + 1] - self.energy_edges[energy_idx]))
        angle_frac = ((angle - self.angle_edges[angle_idx]) / 
                     (self.angle_edges[angle_idx + 1] - self.angle_edges[angle_idx]))
        distance_frac = ((distance - self.distance_edges[distance_idx]) / 
                        (self.distance_edges[distance_idx + 1] - self.distance_edges[distance_idx]))
        
        # Trilinear interpolation
        c000 = self.histogram[energy_idx, angle_idx, distance_idx]
        c001 = self.histogram[energy_idx, angle_idx, distance_idx + 1]
        c010 = self.histogram[energy_idx, angle_idx + 1, distance_idx]
        c011 = self.histogram[energy_idx, angle_idx + 1, distance_idx + 1]
        c100 = self.histogram[energy_idx + 1, angle_idx, distance_idx]
        c101 = self.histogram[energy_idx + 1, angle_idx, distance_idx + 1]
        c110 = self.histogram[energy_idx + 1, angle_idx + 1, distance_idx]
        c111 = self.histogram[energy_idx + 1, angle_idx + 1, distance_idx + 1]
        
        # Interpolate along distance
        c00 = c000 * (1 - distance_frac) + c001 * distance_frac
        c01 = c010 * (1 - distance_frac) + c011 * distance_frac
        c10 = c100 * (1 - distance_frac) + c101 * distance_frac
        c11 = c110 * (1 - distance_frac) + c111 * distance_frac
        
        # Interpolate along angle
        c0 = c00 * (1 - angle_frac) + c01 * angle_frac
        c1 = c10 * (1 - angle_frac) + c11 * angle_frac
        
        # Interpolate along energy
        result = c0 * (1 - energy_frac) + c1 * energy_frac
        
        return result
    
    def get_statistics(self):
        """Get table statistics."""
        stats = {
            'total_photons': self.histogram.sum(),
            'non_zero_bins': np.count_nonzero(self.histogram),
            'max_bin_count': self.histogram.max(),
            'mean_bin_count': self.histogram[self.histogram > 0].mean(),
            'histogram_shape': self.histogram.shape
        }
        return stats
    
    def print_statistics(self):
        """Print table statistics."""
        stats = self.get_statistics()
        print("\n=== 3D Table Statistics ===")
        print(f"Total photons: {stats['total_photons']:.0f}")
        print(f"Non-zero bins: {stats['non_zero_bins']}")
        print(f"Max bin count: {stats['max_bin_count']:.0f}")
        print(f"Mean bin count: {stats['mean_bin_count']:.1f}")
        print(f"Histogram shape: {stats['histogram_shape']}")

def main():
    parser = argparse.ArgumentParser(description='Query 3D photon table')
    parser.add_argument('table_dir', help='Directory containing the 3D table')
    parser.add_argument('--energy', '-e', type=float, help='Muon energy (MeV)')
    parser.add_argument('--angle', '-a', type=float, help='Opening angle (rad)')
    parser.add_argument('--distance', '-d', type=float, help='Distance (mm)')
    parser.add_argument('--method', '-m', choices=['nearest', 'interpolate'], 
                       default='interpolate', help='Query method')
    parser.add_argument('--test', action='store_true', help='Run test queries')
    
    args = parser.parse_args()
    
    # Load table
    try:
        table = PhotonTable3DQuery(args.table_dir)
    except Exception as e:
        print(f"Error loading table: {e}")
        return
    
    # Print statistics
    table.print_statistics()
    
    # Single query
    if args.energy is not None and args.angle is not None and args.distance is not None:
        if args.method == 'nearest':
            result = table.query_nearest(args.energy, args.angle, args.distance)
        else:
            result = table.query_interpolate(args.energy, args.angle, args.distance)
        
        print(f"\nQuery result:")
        print(f"Energy: {args.energy} MeV, Angle: {args.angle:.3f} rad, Distance: {args.distance} mm")
        print(f"Photon count ({args.method}): {result:.2f}")
    
    # Test queries
    if args.test:
        print(f"\n=== Test Queries ===")
        
        # Test at bin centers
        mid_energy = (table.energy_range[0] + table.energy_range[1]) / 2
        mid_angle = (table.angle_range[0] + table.angle_range[1]) / 2
        mid_distance = table.distance_range[1] / 2
        
        test_points = [
            (mid_energy, mid_angle, mid_distance),
            (table.energy_range[0] + 50, table.angle_range[0] + 0.1, 1000),
            (table.energy_range[1] - 50, table.angle_range[1] - 0.1, 5000),
        ]
        
        for i, (e, a, d) in enumerate(test_points):
            nearest = table.query_nearest(e, a, d)
            interp = table.query_interpolate(e, a, d)
            print(f"Test {i+1}: E={e:.1f} MeV, θ={a:.3f} rad, d={d:.0f} mm")
            print(f"  Nearest: {nearest:.2f}, Interpolated: {interp:.2f}")

if __name__ == "__main__":
    main()