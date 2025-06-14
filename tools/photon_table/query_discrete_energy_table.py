#!/usr/bin/env python3
"""
Query utility for discrete energy 3D photon lookup tables.
Handles interpolation between discrete energy layers.
"""

import numpy as np
from pathlib import Path

class DiscreteEnergyTableQuery:
    def __init__(self, table_dir="output"):
        """Initialize query interface for discrete energy table."""
        self.table_dir = Path(table_dir)
        
        # Load 3D table and metadata
        self.table_path = self.table_dir / "photon_histogram_3d_discrete.npy"
        self.metadata_path = self.table_dir / "table_metadata_discrete.npz"
        
        if not self.table_path.exists():
            raise FileNotFoundError(f"3D table not found: {self.table_path}")
        if not self.metadata_path.exists():
            raise FileNotFoundError(f"Metadata not found: {self.metadata_path}")
        
        # Load data
        self.histogram_3d = np.load(self.table_path)
        self.metadata = np.load(self.metadata_path)
        
        # Extract key arrays
        self.energy_centers = self.metadata['energy_centers']
        self.angle_centers = self.metadata['angle_centers'] 
        self.distance_centers = self.metadata['distance_centers']
        
        self.energy_edges = self.metadata['energy_edges']
        self.angle_edges = self.metadata['angle_edges']
        self.distance_edges = self.metadata['distance_edges']
        
        print(f"Loaded discrete energy table:")
        print(f"  Shape: {self.histogram_3d.shape}")
        print(f"  Energy layers: {len(self.energy_centers)} ({self.energy_centers.min():.0f}-{self.energy_centers.max():.0f} MeV)")
        print(f"  Angle bins: {len(self.angle_centers)} ({self.angle_centers.min():.3f}-{self.angle_centers.max():.3f} rad)")
        print(f"  Distance bins: {len(self.distance_centers)} ({self.distance_centers.min():.0f}-{self.distance_centers.max():.0f} mm)")
        print(f"  Non-zero bins: {np.count_nonzero(self.histogram_3d):,} ({100*np.count_nonzero(self.histogram_3d)/self.histogram_3d.size:.1f}%)")
    
    def query(self, energy_mev, angle_rad, distance_mm):
        """
        Query table with interpolation between discrete energy layers.
        
        Parameters:
        -----------
        energy_mev : float
            Muon energy in MeV
        angle_rad : float  
            Opening angle in radians
        distance_mm : float
            Distance from track origin in mm
            
        Returns:
        --------
        float : Expected photon count (interpolated)
        """
        # Handle energy interpolation/extrapolation
        if energy_mev <= self.energy_centers[0]:
            # Below lowest energy - use first layer
            energy_idx_low = 0
            energy_idx_high = 0
            energy_weight = 0.0
        elif energy_mev >= self.energy_centers[-1]:
            # Above highest energy - use last layer
            energy_idx_low = len(self.energy_centers) - 1
            energy_idx_high = len(self.energy_centers) - 1
            energy_weight = 0.0
        else:
            # Interpolate between layers
            energy_idx_high = np.searchsorted(self.energy_centers, energy_mev)
            energy_idx_low = energy_idx_high - 1
            
            energy_low = self.energy_centers[energy_idx_low]
            energy_high = self.energy_centers[energy_idx_high]
            energy_weight = (energy_mev - energy_low) / (energy_high - energy_low)
        
        # Query both energy layers with 2D interpolation
        result_low = self._query_2d_layer(energy_idx_low, angle_rad, distance_mm)
        result_high = self._query_2d_layer(energy_idx_high, angle_rad, distance_mm)
        
        # Linear interpolation between energy layers
        if energy_weight == 0.0:
            return result_low
        else:
            return result_low * (1 - energy_weight) + result_high * energy_weight
    
    def _query_2d_layer(self, energy_idx, angle_rad, distance_mm):
        """Query single 2D layer with bilinear interpolation."""
        # Get 2D slice for this energy
        table_2d = self.histogram_3d[energy_idx]
        
        # Find angle bin
        if angle_rad <= self.angle_edges[0]:
            angle_idx_low = 0
            angle_idx_high = 0
            angle_weight = 0.0
        elif angle_rad >= self.angle_edges[-1]:
            angle_idx_low = len(self.angle_centers) - 1
            angle_idx_high = len(self.angle_centers) - 1
            angle_weight = 0.0
        else:
            angle_idx_high = np.searchsorted(self.angle_edges[1:], angle_rad)
            angle_idx_low = angle_idx_high - 1
            if angle_idx_low < 0:
                angle_idx_low = 0
            if angle_idx_high >= len(self.angle_centers):
                angle_idx_high = len(self.angle_centers) - 1
                
            angle_low = self.angle_centers[angle_idx_low]
            angle_high = self.angle_centers[angle_idx_high]
            if angle_high > angle_low:
                angle_weight = (angle_rad - angle_low) / (angle_high - angle_low)
            else:
                angle_weight = 0.0
        
        # Find distance bin
        if distance_mm <= self.distance_edges[0]:
            distance_idx_low = 0
            distance_idx_high = 0
            distance_weight = 0.0
        elif distance_mm >= self.distance_edges[-1]:
            distance_idx_low = len(self.distance_centers) - 1
            distance_idx_high = len(self.distance_centers) - 1
            distance_weight = 0.0
        else:
            distance_idx_high = np.searchsorted(self.distance_edges[1:], distance_mm)
            distance_idx_low = distance_idx_high - 1
            if distance_idx_low < 0:
                distance_idx_low = 0
            if distance_idx_high >= len(self.distance_centers):
                distance_idx_high = len(self.distance_centers) - 1
                
            distance_low = self.distance_centers[distance_idx_low]
            distance_high = self.distance_centers[distance_idx_high]
            if distance_high > distance_low:
                distance_weight = (distance_mm - distance_low) / (distance_high - distance_low)
            else:
                distance_weight = 0.0
        
        # Bilinear interpolation
        v00 = table_2d[angle_idx_low, distance_idx_low]
        v10 = table_2d[angle_idx_high, distance_idx_low]
        v01 = table_2d[angle_idx_low, distance_idx_high]
        v11 = table_2d[angle_idx_high, distance_idx_high]
        
        # Interpolate in angle direction
        v0 = v00 * (1 - angle_weight) + v10 * angle_weight
        v1 = v01 * (1 - angle_weight) + v11 * angle_weight
        
        # Interpolate in distance direction
        result = v0 * (1 - distance_weight) + v1 * distance_weight
        
        return result
    
    def get_available_energies(self):
        """Get list of discrete energy values in the table."""
        return self.energy_centers.copy()
    
    def get_parameter_ranges(self):
        """Get parameter ranges for the table."""
        return {
            'energy_range': (self.energy_centers.min(), self.energy_centers.max()),
            'angle_range': (self.angle_edges[0], self.angle_edges[-1]),
            'distance_range': (self.distance_edges[0], self.distance_edges[-1])
        }
    
    def query_batch(self, energies, angles, distances):
        """Query multiple points efficiently."""
        energies = np.asarray(energies)
        angles = np.asarray(angles)
        distances = np.asarray(distances)
        
        # Ensure same shape
        shape = np.broadcast(energies, angles, distances).shape
        energies = np.broadcast_to(energies, shape)
        angles = np.broadcast_to(angles, shape)
        distances = np.broadcast_to(distances, shape)
        
        results = np.zeros(shape)
        flat_results = results.flatten()
        flat_energies = energies.flatten()
        flat_angles = angles.flatten()
        flat_distances = distances.flatten()
        
        for i in range(len(flat_results)):
            flat_results[i] = self.query(flat_energies[i], flat_angles[i], flat_distances[i])
        
        return results


def main():
    """Demo usage of discrete energy table query."""
    import sys
    
    if len(sys.argv) > 1:
        table_dir = sys.argv[1]
    else:
        table_dir = "output"
    
    try:
        # Load table
        query_table = DiscreteEnergyTableQuery(table_dir)
        
        # Show available energies
        energies = query_table.get_available_energies()
        print(f"\nAvailable energy layers: {energies} MeV")
        
        # Show parameter ranges
        ranges = query_table.get_parameter_ranges()
        print(f"\nParameter ranges:")
        print(f"  Energy: {ranges['energy_range'][0]:.0f} - {ranges['energy_range'][1]:.0f} MeV")
        print(f"  Angle: {ranges['angle_range'][0]:.3f} - {ranges['angle_range'][1]:.3f} rad")
        print(f"  Distance: {ranges['distance_range'][0]:.0f} - {ranges['distance_range'][1]:.0f} mm")
        
        # Example queries
        print(f"\nExample queries:")
        
        # Query at exact energy layers
        for energy in energies:
            result = query_table.query(energy, 0.7, 5000)
            print(f"  {energy:.0f} MeV, 0.7 rad, 5000 mm: {result:.3f} photons")
        
        # Query with interpolation
        if len(energies) >= 2:
            mid_energy = (energies[0] + energies[1]) / 2
            result = query_table.query(mid_energy, 0.7, 5000)
            print(f"  {mid_energy:.0f} MeV (interpolated), 0.7 rad, 5000 mm: {result:.3f} photons")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())