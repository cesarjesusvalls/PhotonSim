#!/usr/bin/env python3
"""
Query tool for discrete energy 3D lookup tables.
Provides easy interface to query photon probabilities for specific energy, angle, and distance values.
"""

import numpy as np
import sys
import os
from discrete_energy_3d_builder import DiscreteEnergy3DTableBuilder


class DiscreteEnergy3DTableQuery:
    """Query interface for discrete energy 3D lookup tables."""
    
    def __init__(self, table_file="discrete_energy_3d_table.npz"):
        """Initialize with a saved 3D table file."""
        self.builder = DiscreteEnergy3DTableBuilder()
        
        # Try multiple locations for the table file
        possible_paths = [
            os.path.join("output/tables", table_file),
            os.path.join("../../output/tables", table_file),
            table_file
        ]
        
        loaded = False
        for path in possible_paths:
            if os.path.exists(path):
                self.table_3d, self.energies = self.builder.load_3d_table(path)
                if self.table_3d is not None:
                    loaded = True
                    break
        
        if not loaded:
            raise ValueError(f"Could not load 3D table from any of: {possible_paths}")
    
    def query(self, energy_mev, angle_degrees, distance_mm):
        """
        Query the 3D table for photon probability.
        
        Args:
            energy_mev: Muon energy in MeV
            angle_degrees: Opening angle in degrees (0-180)
            distance_mm: Distance in millimeters (0-10000)
            
        Returns:
            Probability density value
        """
        angle_rad = np.radians(angle_degrees)
        return self.builder.query_3d_table(self.table_3d, self.energies, 
                                         energy_mev, angle_rad, distance_mm)
    
    def get_energy_range(self):
        """Get the available energy range."""
        return self.energies.min(), self.energies.max()
    
    def get_available_energies(self):
        """Get list of available discrete energies."""
        return self.energies.tolist()
    
    def query_cherenkov_peak(self, energy_mev, distance_mm=1000):
        """
        Query at the Cherenkov peak angle (~40 degrees for water).
        
        Args:
            energy_mev: Muon energy in MeV
            distance_mm: Distance in millimeters
            
        Returns:
            Probability at Cherenkov peak
        """
        return self.query(energy_mev, 40.0, distance_mm)
    
    def scan_angles(self, energy_mev, distance_mm, angle_range=(0, 90), n_points=100):
        """
        Scan across angles for a fixed energy and distance.
        
        Args:
            energy_mev: Muon energy in MeV
            distance_mm: Distance in millimeters
            angle_range: (min_angle, max_angle) in degrees
            n_points: Number of points to sample
            
        Returns:
            angles, probabilities arrays
        """
        angles = np.linspace(angle_range[0], angle_range[1], n_points)
        probabilities = [self.query(energy_mev, angle, distance_mm) for angle in angles]
        return angles, np.array(probabilities)
    
    def scan_distances(self, energy_mev, angle_degrees, distance_range=(0, 5000), n_points=100):
        """
        Scan across distances for a fixed energy and angle.
        
        Args:
            energy_mev: Muon energy in MeV
            angle_degrees: Opening angle in degrees
            distance_range: (min_distance, max_distance) in mm
            n_points: Number of points to sample
            
        Returns:
            distances, probabilities arrays
        """
        distances = np.linspace(distance_range[0], distance_range[1], n_points)
        probabilities = [self.query(energy_mev, angle_degrees, dist) for dist in distances]
        return distances, np.array(probabilities)
    
    def scan_energies(self, angle_degrees, distance_mm, energy_range=None, n_points=50):
        """
        Scan across energies for a fixed angle and distance.
        
        Args:
            angle_degrees: Opening angle in degrees
            distance_mm: Distance in millimeters
            energy_range: (min_energy, max_energy) in MeV, or None for full range
            n_points: Number of points to sample
            
        Returns:
            energies, probabilities arrays
        """
        if energy_range is None:
            energy_range = self.get_energy_range()
        
        energies = np.linspace(energy_range[0], energy_range[1], n_points)
        probabilities = [self.query(energy, angle_degrees, distance_mm) for energy in energies]
        return energies, np.array(probabilities)
    
    def find_peak_angle(self, energy_mev, distance_mm, angle_range=(30, 60)):
        """
        Find the angle with maximum probability for given energy and distance.
        
        Args:
            energy_mev: Muon energy in MeV
            distance_mm: Distance in millimeters
            angle_range: Search range in degrees
            
        Returns:
            peak_angle, peak_probability
        """
        angles, probs = self.scan_angles(energy_mev, distance_mm, angle_range, n_points=200)
        peak_idx = np.argmax(probs)
        return angles[peak_idx], probs[peak_idx]
    
    def print_info(self):
        """Print information about the loaded table."""
        print("=== Discrete Energy 3D Table Info ===")
        print(f"Table shape: {self.table_3d.shape} (energy, angle, distance)")
        print(f"Available energies: {len(self.energies)} values")
        print(f"Energy range: {self.energies.min():.0f} - {self.energies.max():.0f} MeV")
        print(f"Energy values: {', '.join(f'{e:.0f}' for e in self.energies)} MeV")
        print(f"Angle bins: {self.builder.angle_bins} (0° to 180°)")
        print(f"Distance bins: {self.builder.distance_bins} (0 to 10000 mm)")


def main():
    """Main function demonstrating usage."""
    print("=== Discrete Energy 3D Table Query Tool ===\n")
    
    try:
        # Load the 3D table
        query_tool = DiscreteEnergy3DTableQuery()
        query_tool.print_info()
        
        print("\n=== Example Queries ===")
        
        # Available energies
        energies = query_tool.get_available_energies()
        
        # Query at Cherenkov angle for different energies
        print("\nCherenkov peak queries (40°, 1000mm distance):")
        for energy in energies:
            prob = query_tool.query_cherenkov_peak(energy)
            print(f"  Energy: {energy:.0f} MeV -> Probability: {prob:.6f}")
        
        # Find peak angles
        print(f"\nPeak angle analysis (1000mm distance):")
        for energy in energies:
            peak_angle, peak_prob = query_tool.find_peak_angle(energy, 1000)
            print(f"  Energy: {energy:.0f} MeV -> Peak at {peak_angle:.1f}° (prob: {peak_prob:.6f})")
        
        # Compare different distances at Cherenkov angle
        print(f"\nDistance comparison at Cherenkov angle (40°, {energies[0]:.0f} MeV):")
        distances = [500, 1000, 2000, 3000, 5000]
        for dist in distances:
            prob = query_tool.query(energies[0], 40.0, dist)
            print(f"  Distance: {dist:4d}mm -> Probability: {prob:.6f}")
        
        # Interactive query if command line arguments provided
        if len(sys.argv) >= 4:
            energy = float(sys.argv[1])
            angle = float(sys.argv[2])
            distance = float(sys.argv[3])
            
            prob = query_tool.query(energy, angle, distance)
            print(f"\n=== Command Line Query ===")
            print(f"Energy: {energy} MeV, Angle: {angle}°, Distance: {distance}mm")
            print(f"Probability: {prob:.8f}")
        
        else:
            print(f"\nUsage for command line query:")
            print(f"python {sys.argv[0]} <energy_MeV> <angle_degrees> <distance_mm>")
            print(f"Example: python {sys.argv[0]} 505 40 1000")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure discrete_energy_3d_table.npz exists in the current directory.")
        print("Run discrete_energy_3d_builder.py first to create the table.")


if __name__ == "__main__":
    main()