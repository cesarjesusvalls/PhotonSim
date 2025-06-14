#!/usr/bin/env python3
"""
Query utility for the 3D Cherenkov photon lookup table.
"""

import numpy as np
from pathlib import Path
import argparse

class PhotonTableQuery:
    """Query interface for the 3D photon table."""
    
    def __init__(self, table_dir="output"):
        """Load the 3D table from directory."""
        self.table_dir = Path(table_dir)
        
        # Load histogram and metadata
        self.histogram = np.load(self.table_dir / "photon_histogram_3d.npy")
        metadata = np.load(self.table_dir / "table_metadata.npz")
        
        self.energy_edges = metadata['energy_edges']
        self.angle_edges = metadata['angle_edges']
        self.distance_edges = metadata['distance_edges']
        self.energy_range = metadata['energy_range']
        self.angle_range = metadata['angle_range']
        self.distance_range = metadata['distance_range']
        
        print(f"Loaded 3D table with shape: {self.histogram.shape}")
        print(f"Energy range: {self.energy_range[0]:.1f} - {self.energy_range[1]:.1f} MeV")
        print(f"Angle range: {self.angle_range[0]:.3f} - {self.angle_range[1]:.3f} rad")
        print(f"Distance range: {self.distance_range[0]:.1f} - {self.distance_range[1]:.0f} mm")
    
    def query(self, energy, angle, distance):
        """Query table using trilinear interpolation."""
        # Check bounds
        if (energy < self.energy_range[0] or energy > self.energy_range[1] or
            angle < self.angle_range[0] or angle > self.angle_range[1] or
            distance < self.distance_range[0] or distance > self.distance_range[1]):
            return 0.0
        
        # Find bin indices
        energy_idx = np.searchsorted(self.energy_edges, energy) - 1
        angle_idx = np.searchsorted(self.angle_edges, angle) - 1
        distance_idx = np.searchsorted(self.distance_edges, distance) - 1
        
        # Ensure valid indices
        energy_bins, angle_bins, distance_bins = self.histogram.shape
        energy_idx = max(0, min(energy_idx, energy_bins - 2))
        angle_idx = max(0, min(angle_idx, angle_bins - 2))
        distance_idx = max(0, min(distance_idx, distance_bins - 2))
        
        # Get fractional positions
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
        
        # Interpolate
        c00 = c000 * (1 - distance_frac) + c001 * distance_frac
        c01 = c010 * (1 - distance_frac) + c011 * distance_frac
        c10 = c100 * (1 - distance_frac) + c101 * distance_frac
        c11 = c110 * (1 - distance_frac) + c111 * distance_frac
        
        c0 = c00 * (1 - angle_frac) + c01 * angle_frac
        c1 = c10 * (1 - angle_frac) + c11 * angle_frac
        
        result = c0 * (1 - energy_frac) + c1 * energy_frac
        return result
    
    def print_stats(self):
        """Print table statistics."""
        total_photons = self.histogram.sum()
        non_zero_bins = np.count_nonzero(self.histogram)
        max_count = self.histogram.max()
        
        print(f"\n=== Table Statistics ===")
        print(f"Total photons: {total_photons:,.0f}")
        print(f"Non-zero bins: {non_zero_bins}")
        print(f"Max bin count: {max_count:.0f}")
        print(f"Parameter space coverage: {non_zero_bins/np.prod(self.histogram.shape)*100:.1f}%")

def main():
    parser = argparse.ArgumentParser(description='Query 3D photon table')
    parser.add_argument('--table-dir', default='output', help='Table directory')
    parser.add_argument('--energy', '-e', type=float, help='Muon energy (MeV)')
    parser.add_argument('--angle', '-a', type=float, help='Opening angle (rad)')
    parser.add_argument('--distance', '-d', type=float, help='Distance (mm)')
    parser.add_argument('--stats', action='store_true', help='Show table statistics')
    
    args = parser.parse_args()
    
    try:
        table = PhotonTableQuery(args.table_dir)
    except Exception as e:
        print(f"Error loading table: {e}")
        return
    
    if args.stats:
        table.print_stats()
    
    if args.energy is not None and args.angle is not None and args.distance is not None:
        result = table.query(args.energy, args.angle, args.distance)
        print(f"\nQuery: E={args.energy} MeV, θ={args.angle:.3f} rad, d={args.distance} mm")
        print(f"Result: {result:.2f} photons")

if __name__ == "__main__":
    main()