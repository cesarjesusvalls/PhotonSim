#!/usr/bin/env python3
"""
Build 3D lookup tables from multiple discrete energy ROOT files.
Each ROOT file contains 2D histograms (angle vs distance) for a specific energy.
The 3D table stacks these 2D histograms with energy as the third dimension.
"""

import numpy as np
import matplotlib.pyplot as plt
import uproot
import sys
import os
import re
from pathlib import Path
import glob


class DiscreteEnergy3DTableBuilder:
    """Builds 3D lookup tables from multiple discrete energy ROOT files."""
    
    def __init__(self, root_files_pattern=None, histogram_name="PhotonHist_AngleDistance"):
        """
        Initialize the builder.
        
        Args:
            root_files_pattern: Glob pattern to find ROOT files (e.g., "*.root")
            histogram_name: Name of the 2D histogram to extract from each file
        """
        self.histogram_name = histogram_name
        self.energy_files = {}  # energy -> filename mapping
        self.energy_histograms = {}  # energy -> 2D histogram data
        self.angle_bins = None
        self.distance_bins = None
        
        if root_files_pattern:
            self.find_root_files(root_files_pattern)
    
    def find_root_files(self, pattern):
        """Find ROOT files matching the pattern and extract energy values."""
        files = glob.glob(pattern)
        print(f"Found {len(files)} ROOT files matching pattern: {pattern}")
        
        for filename in files:
            energy = self.extract_energy_from_filename(filename)
            if energy is not None:
                self.energy_files[energy] = filename
                print(f"  {filename} -> {energy} MeV")
            else:
                print(f"  Warning: Could not extract energy from {filename}")
        
        if not self.energy_files:
            print("No files with recognizable energy values found!")
            return
            
        print(f"\nTotal files with valid energies: {len(self.energy_files)}")
        energies = sorted(self.energy_files.keys())
        print(f"Energy range: {energies[0]} - {energies[-1]} MeV")
    
    def extract_energy_from_filename(self, filename):
        """
        Extract energy value from filename.
        
        Supports patterns like:
        - muons_500MeV_histonly.root -> 500
        - data_510MeV.root -> 510
        - simulation_1000MeV_output.root -> 1000
        """
        basename = os.path.basename(filename)
        
        # Look for patterns like "500MeV", "510MeV", etc.
        patterns = [
            r'(\d+)MeV',
            r'(\d+)_MeV',
            r'energy_(\d+)',
            r'(\d+)meV',  # case insensitive
        ]
        
        for pattern in patterns:
            match = re.search(pattern, basename, re.IGNORECASE)
            if match:
                return float(match.group(1))
        
        return None
    
    def load_histogram_from_file(self, filename):
        """Load the 2D histogram from a ROOT file."""
        try:
            with uproot.open(filename) as file:
                if self.histogram_name not in file:
                    available = list(file.keys())
                    print(f"Warning: {self.histogram_name} not found in {filename}")
                    print(f"Available histograms: {available}")
                    return None
                
                hist = file[self.histogram_name]
                values = hist.values()
                
                print(f"Loaded {self.histogram_name} from {filename}")
                print(f"  Shape: {values.shape}")
                print(f"  Total entries: {values.sum():,.0f}")
                
                return values
                
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return None
    
    def load_all_histograms(self):
        """Load 2D histograms from all energy files."""
        if not self.energy_files:
            print("No energy files found. Use find_root_files() first.")
            return False
        
        print(f"\nLoading histograms from {len(self.energy_files)} files...")
        
        for energy, filename in self.energy_files.items():
            histogram = self.load_histogram_from_file(filename)
            if histogram is not None:
                self.energy_histograms[energy] = histogram
                
                # Set bin dimensions from first successful load
                if self.angle_bins is None:
                    self.angle_bins = histogram.shape[0]
                    self.distance_bins = histogram.shape[1]
                    print(f"Using bin dimensions: {self.angle_bins} x {self.distance_bins}")
        
        success_count = len(self.energy_histograms)
        print(f"Successfully loaded {success_count}/{len(self.energy_files)} histograms")
        
        if success_count == 0:
            print("Failed to load any histograms!")
            return False
        
        return True
    
    def create_3d_table(self):
        """Create 3D lookup table by stacking 2D histograms."""
        if not self.energy_histograms:
            print("No histograms loaded. Use load_all_histograms() first.")
            return None, None
        
        # Sort energies to create ordered 3D table
        energies = sorted(self.energy_histograms.keys())
        energy_count = len(energies)
        
        print(f"\nCreating 3D table with {energy_count} energy layers...")
        print(f"Energy values: {energies}")
        
        # Initialize 3D array: [energy, angle, distance]
        table_3d = np.zeros((energy_count, self.angle_bins, self.distance_bins))
        
        # Stack 2D histograms
        for i, energy in enumerate(energies):
            histogram_2d = self.energy_histograms[energy]
            table_3d[i, :, :] = histogram_2d
            
            total_photons = histogram_2d.sum()
            print(f"  Layer {i}: {energy} MeV -> {total_photons:,.0f} photons")
        
        # Convert to probability distributions (normalize each energy layer)
        for i in range(energy_count):
            layer_sum = table_3d[i, :, :].sum()
            if layer_sum > 0:
                table_3d[i, :, :] /= layer_sum
        
        print(f"\n3D table created successfully!")
        print(f"Shape: {table_3d.shape} (energy, angle, distance)")
        print(f"Total probability per layer should be ~1.0")
        
        # Verify normalization
        for i in range(min(3, energy_count)):  # Check first 3 layers
            layer_sum = table_3d[i, :, :].sum()
            print(f"  Layer {i} sum: {layer_sum:.6f}")
        
        return table_3d, np.array(energies)
    
    def save_3d_table(self, table_3d, energies, filename="discrete_energy_3d_table.npz"):
        """Save 3D table and energy array to file."""
        # Ensure output directory exists
        output_dir = "output/tables"
        os.makedirs(output_dir, exist_ok=True)
        
        # Save to output directory
        full_path = os.path.join(output_dir, filename)
        np.savez_compressed(full_path, 
                           table_3d=table_3d, 
                           energies=energies,
                           angle_bins=self.angle_bins,
                           distance_bins=self.distance_bins)
        
        print(f"\n3D table saved to: {full_path}")
        print(f"File size: {os.path.getsize(full_path)/1024/1024:.2f} MB")
    
    def load_3d_table(self, filename="discrete_energy_3d_table.npz"):
        """Load 3D table from file."""
        try:
            # Try loading from output directory first
            output_path = os.path.join("output/tables", filename)
            if os.path.exists(output_path):
                load_path = output_path
            else:
                load_path = filename
                
            data = np.load(load_path)
            table_3d = data['table_3d']
            energies = data['energies']
            self.angle_bins = int(data['angle_bins'])
            self.distance_bins = int(data['distance_bins'])
            
            print(f"Loaded 3D table from: {load_path}")
            print(f"Shape: {table_3d.shape}")
            print(f"Energy range: {energies.min():.0f} - {energies.max():.0f} MeV")
            
            return table_3d, energies
            
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return None, None
    
    def query_3d_table(self, table_3d, energies, energy, angle_rad, distance_mm):
        """
        Query the 3D table for a specific energy, angle, and distance.
        Uses trilinear interpolation for smooth results.
        """
        # Convert physical values to bin indices
        energy_idx = np.interp(energy, energies, np.arange(len(energies)))
        angle_idx = angle_rad * self.angle_bins / np.pi  # 0 to π maps to 0 to angle_bins
        distance_idx = distance_mm * self.distance_bins / 10000.0  # 0 to 10000mm maps to 0 to distance_bins
        
        # Clip to valid ranges
        energy_idx = np.clip(energy_idx, 0, len(energies) - 1.001)
        angle_idx = np.clip(angle_idx, 0, self.angle_bins - 1.001)
        distance_idx = np.clip(distance_idx, 0, self.distance_bins - 1.001)
        
        # Trilinear interpolation
        e0, e1 = int(energy_idx), min(int(energy_idx) + 1, len(energies) - 1)
        a0, a1 = int(angle_idx), min(int(angle_idx) + 1, self.angle_bins - 1)
        d0, d1 = int(distance_idx), min(int(distance_idx) + 1, self.distance_bins - 1)
        
        # Interpolation weights
        we = energy_idx - e0
        wa = angle_idx - a0
        wd = distance_idx - d0
        
        # 8-point interpolation
        c000 = table_3d[e0, a0, d0]
        c001 = table_3d[e0, a0, d1]
        c010 = table_3d[e0, a1, d0]
        c011 = table_3d[e0, a1, d1]
        c100 = table_3d[e1, a0, d0]
        c101 = table_3d[e1, a0, d1]
        c110 = table_3d[e1, a1, d0]
        c111 = table_3d[e1, a1, d1]
        
        # Interpolate
        c00 = c000 * (1 - wd) + c001 * wd
        c01 = c010 * (1 - wd) + c011 * wd
        c10 = c100 * (1 - wd) + c101 * wd
        c11 = c110 * (1 - wd) + c111 * wd
        
        c0 = c00 * (1 - wa) + c01 * wa
        c1 = c10 * (1 - wa) + c11 * wa
        
        result = c0 * (1 - we) + c1 * we
        
        return result
    
    def visualize_3d_table(self, table_3d, energies, save_plots=True):
        """Create visualization plots for the 3D table."""
        print("\nCreating visualization plots...")
        
        fig, axes = plt.subplots(2, 3, figsize=(12, 8))
        
        # Plot 1: Energy slices (first few energies)
        n_slices = min(3, len(energies))
        for i in range(n_slices):
            ax = axes[0, i]
            im = ax.imshow(table_3d[i, :, :].T, origin='lower', aspect='auto', cmap='plasma')
            ax.set_title(f'Energy: {energies[i]:.0f} MeV\nTotal prob: {table_3d[i,:,:].sum():.4f}')
            ax.set_xlabel('Angle Bin (0=0°, 500=180°)')
            ax.set_ylabel('Distance Bin (0=0mm, 500=10000mm)')
            plt.colorbar(im, ax=ax, label='Probability Density')
        
        # Plot 2: Projections
        # Angle projection (sum over distance and energy)
        ax = axes[1, 0]
        angle_proj = table_3d.sum(axis=(0, 2))
        angle_bins_deg = np.linspace(0, 180, len(angle_proj))
        ax.plot(angle_bins_deg, angle_proj)
        ax.set_xlabel('Opening Angle (degrees)')
        ax.set_ylabel('Total Probability')
        ax.set_title('Angle Projection (all energies)')
        ax.grid(True, alpha=0.3)
        
        # Distance projection (sum over angle and energy)
        ax = axes[1, 1]
        distance_proj = table_3d.sum(axis=(0, 1))
        distance_bins_mm = np.linspace(0, 10000, len(distance_proj))
        ax.plot(distance_bins_mm, distance_proj)
        ax.set_xlabel('Distance (mm)')
        ax.set_ylabel('Total Probability')
        ax.set_title('Distance Projection (all energies)')
        ax.grid(True, alpha=0.3)
        
        # Energy projection (sum over angle and distance)
        ax = axes[1, 2]
        energy_proj = table_3d.sum(axis=(1, 2))
        ax.plot(energies, energy_proj, 'o-')
        ax.set_xlabel('Energy (MeV)')
        ax.set_ylabel('Total Probability')
        ax.set_title('Energy Projection')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_plots:
            # Save to output directory
            output_dir = "output/visualizations"
            os.makedirs(output_dir, exist_ok=True)
            filename = os.path.join(output_dir, '3d_table_visualization.png')
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            print(f"Visualization saved: {filename}")
        
        plt.show()


def main():
    """Main function to demonstrate usage."""
    print("=== Discrete Energy 3D Table Builder ===\n")
    
    # Initialize builder
    builder = DiscreteEnergy3DTableBuilder()
    
    # Find ROOT files in current directory and build directory
    patterns_to_try = [
        "*.root",
        "build/*.root",
        "../build/*.root",
        "muons_*MeV*.root",
        "build/muons_*MeV*.root"
    ]
    
    found_files = False
    for pattern in patterns_to_try:
        builder.find_root_files(pattern)
        if builder.energy_files:
            found_files = True
            break
    
    if not found_files:
        print("No ROOT files found! Please check the file patterns.")
        print("Expected files like: muons_500MeV_histonly.root, muons_510MeV_histonly.root")
        return
    
    # Load histograms
    if not builder.load_all_histograms():
        print("Failed to load histograms!")
        return
    
    # Create 3D table
    table_3d, energies = builder.create_3d_table()
    if table_3d is None:
        print("Failed to create 3D table!")
        return
    
    # Save the table
    builder.save_3d_table(table_3d, energies)
    
    # Visualize
    builder.visualize_3d_table(table_3d, energies)
    
    # Demonstrate query functionality
    print("\n=== Query Examples ===")
    
    # Query at Cherenkov angle for water (~40 degrees)
    cherenkov_angle = np.radians(40)
    test_distance = 1000  # mm
    
    for energy in energies[:3]:  # Test first 3 energies
        probability = builder.query_3d_table(table_3d, energies, energy, cherenkov_angle, test_distance)
        print(f"Energy: {energy:.0f} MeV, Angle: 40°, Distance: 1000mm -> Probability: {probability:.6f}")


if __name__ == "__main__":
    main()