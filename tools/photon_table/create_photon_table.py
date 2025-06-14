#!/usr/bin/env python3
"""
Main script to create 3D Cherenkov photon lookup table.

This script creates a 3D table with regular binning for:
1. Muon energy (MeV)
2. Photon opening angle with respect to muon direction (radians)  
3. Distance between photon origin and track origin (mm)

All outputs are saved to the 'output/' directory.
"""

import numpy as np
import matplotlib.pyplot as plt
import uproot
from pathlib import Path
import argparse

class PhotonTable3D:
    """3D table for Cherenkov photon analysis."""
    
    def __init__(self, energy_bins=100, angle_bins=100, distance_bins=100):
        self.energy_bins = energy_bins
        self.angle_bins = angle_bins
        self.distance_bins = distance_bins
        
        self.histogram = None
        self.bin_edges = None
        self.bin_centers = None
        self.energy_range = None
        self.angle_range = None
        self.distance_range = None
        
    def load_and_process_data(self, root_file_path, max_events=None):
        """Load and process all photon data from ROOT file."""
        print(f"Loading data from {root_file_path}...")
        
        with uproot.open(root_file_path) as file:
            tree = file["OpticalPhotons"]
            total_events = tree.num_entries
            
            if max_events is None:
                max_events = total_events
            else:
                max_events = min(max_events, total_events)
                
            print(f"Processing {max_events} events (of {total_events} total)")
            
            # Load data
            data = tree.arrays([
                'PrimaryEnergy', 'PhotonPosX', 'PhotonPosY', 'PhotonPosZ',
                'PhotonDirX', 'PhotonDirY', 'PhotonDirZ', 'PhotonParent'
            ], entry_stop=max_events, library="np")
        
        # Process all events
        energies = []
        angles = []
        distances = []
        
        muon_dir = np.array([0, 0, 1])  # Muon direction along +z
        total_photons = 0
        total_muon_photons = 0
        
        print("Processing events...")
        for event_idx in range(max_events):
            if event_idx % 20 == 0:
                print(f"  Event {event_idx+1}/{max_events}")
                
            event_energy = data['PrimaryEnergy'][event_idx]
            n_photons = len(data['PhotonPosX'][event_idx])
            total_photons += n_photons
            
            # Filter for muon photons only
            parents = data['PhotonParent'][event_idx]
            muon_indices = [i for i, p in enumerate(parents) if p == 'mu-']
            total_muon_photons += len(muon_indices)
            
            if len(muon_indices) == 0:
                continue
                
            # Sample photons if too many (to keep memory manageable)
            if len(muon_indices) > 1000:
                sample_indices = np.random.choice(muon_indices, 1000, replace=False)
            else:
                sample_indices = muon_indices
            
            for idx in sample_indices:
                # Energy
                energies.append(event_energy)
                
                # Position in mm
                pos = np.array([
                    data['PhotonPosX'][event_idx][idx] * 1000,
                    data['PhotonPosY'][event_idx][idx] * 1000,
                    data['PhotonPosZ'][event_idx][idx] * 1000
                ])
                
                # Distance from origin
                distance = np.sqrt(np.sum(pos**2))
                distances.append(distance)
                
                # Direction and opening angle
                photon_dir = np.array([
                    data['PhotonDirX'][event_idx][idx],
                    data['PhotonDirY'][event_idx][idx],
                    data['PhotonDirZ'][event_idx][idx]
                ])
                
                cos_angle = np.dot(photon_dir, muon_dir)
                cos_angle = np.clip(cos_angle, -1.0, 1.0)
                angle = np.arccos(cos_angle)
                angles.append(angle)
        
        print(f"\nData processing complete:")
        print(f"  Total photons: {total_photons:,}")
        print(f"  Muon photons: {total_muon_photons:,}")
        print(f"  Sampled for analysis: {len(energies):,}")
        
        return np.array(energies), np.array(angles), np.array(distances)
    
    def create_histogram(self, energies, angles, distances):
        """Create the 3D histogram."""
        print(f"\nCreating 3D histogram with {(self.energy_bins, self.angle_bins, self.distance_bins)} bins...")
        
        # Define ranges
        self.energy_range = (energies.min(), energies.max())
        self.angle_range = (angles.min(), angles.max())
        
        # Limit distance to 95th percentile to avoid outliers
        distance_95th = np.percentile(distances, 95)
        distance_mask = distances <= distance_95th
        
        filtered_energies = energies[distance_mask]
        filtered_angles = angles[distance_mask]
        filtered_distances = distances[distance_mask]
        self.distance_range = (0, distance_95th)
        
        print(f"Energy range: {self.energy_range[0]:.1f} - {self.energy_range[1]:.1f} MeV")
        print(f"Angle range: {self.angle_range[0]:.3f} - {self.angle_range[1]:.3f} rad")
        print(f"Distance range: {self.distance_range[0]:.1f} - {self.distance_range[1]:.1f} mm")
        print(f"Using {len(filtered_energies):,} photons after filtering")
        
        # Create bin edges
        energy_edges = np.linspace(self.energy_range[0], self.energy_range[1], self.energy_bins + 1)
        angle_edges = np.linspace(self.angle_range[0], self.angle_range[1], self.angle_bins + 1)
        distance_edges = np.linspace(self.distance_range[0], self.distance_range[1], self.distance_bins + 1)
        
        self.bin_edges = (energy_edges, angle_edges, distance_edges)
        
        # Calculate bin centers
        self.bin_centers = (
            (energy_edges[:-1] + energy_edges[1:]) / 2,
            (angle_edges[:-1] + angle_edges[1:]) / 2,
            (distance_edges[:-1] + distance_edges[1:]) / 2
        )
        
        # Create 3D histogram
        self.histogram, _ = np.histogramdd(
            np.column_stack([filtered_energies, filtered_angles, filtered_distances]),
            bins=self.bin_edges
        )
        
        print(f"3D histogram shape: {self.histogram.shape}")
        print(f"Total photons in histogram: {self.histogram.sum():,.0f}")
        print(f"Non-zero bins: {np.count_nonzero(self.histogram)}")
        print(f"Max bin count: {self.histogram.max():.0f}")
        
        return filtered_energies, filtered_angles, filtered_distances
    
    def save_table(self, output_dir):
        """Save the 3D table and metadata."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Save histogram
        np.save(output_path / "photon_histogram_3d.npy", self.histogram)
        
        # Save metadata
        metadata = {
            'histogram_shape': self.histogram.shape,
            'energy_edges': self.bin_edges[0],
            'angle_edges': self.bin_edges[1],
            'distance_edges': self.bin_edges[2],
            'energy_centers': self.bin_centers[0],
            'angle_centers': self.bin_centers[1],
            'distance_centers': self.bin_centers[2],
            'energy_range': self.energy_range,
            'angle_range': self.angle_range,
            'distance_range': self.distance_range,
            'total_photons': self.histogram.sum(),
            'max_bin_count': self.histogram.max(),
            'energy_bins': self.energy_bins,
            'angle_bins': self.angle_bins,
            'distance_bins': self.distance_bins
        }
        
        np.savez(output_path / "table_metadata.npz", **metadata)
        print(f"3D table saved to: {output_path}")
    
    def create_visualizations(self, output_dir):
        """Create comprehensive visualizations."""
        print("\nCreating visualizations...")
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Main visualization with projections - smaller figure
        fig, axes = plt.subplots(2, 3, figsize=(12, 6))
        fig.suptitle('3D Cherenkov Photon Lookup Table Analysis', fontsize=16)
        
        # 2D projections
        projection_ea = np.sum(self.histogram, axis=2)
        im1 = axes[0,0].imshow(projection_ea.T, origin='lower', aspect='auto', cmap='viridis')
        axes[0,0].set_title('Energy vs Opening Angle')
        axes[0,0].set_xlabel('Energy Bin')
        axes[0,0].set_ylabel('Angle Bin')
        plt.colorbar(im1, ax=axes[0,0], label='Photon Count')
        
        projection_ed = np.sum(self.histogram, axis=1)
        im2 = axes[0,1].imshow(projection_ed.T, origin='lower', aspect='auto', cmap='viridis')
        axes[0,1].set_title('Energy vs Distance')
        axes[0,1].set_xlabel('Energy Bin')
        axes[0,1].set_ylabel('Distance Bin')
        plt.colorbar(im2, ax=axes[0,1], label='Photon Count')
        
        projection_ad = np.sum(self.histogram, axis=0)
        im3 = axes[0,2].imshow(projection_ad.T, origin='lower', aspect='auto', cmap='viridis')
        axes[0,2].set_title('Angle vs Distance')
        axes[0,2].set_xlabel('Angle Bin')
        axes[0,2].set_ylabel('Distance Bin')
        plt.colorbar(im3, ax=axes[0,2], label='Photon Count')
        
        # 1D distributions
        energy_dist = np.sum(self.histogram, axis=(1, 2))
        axes[1,0].plot(self.bin_centers[0], energy_dist, 'b-', linewidth=2)
        axes[1,0].set_xlabel('Energy (MeV)')
        axes[1,0].set_ylabel('Photon Count')
        axes[1,0].set_title('Energy Distribution')
        axes[1,0].grid(True, alpha=0.3)
        
        angle_dist = np.sum(self.histogram, axis=(0, 2))
        axes[1,1].plot(self.bin_centers[1], angle_dist, 'g-', linewidth=2)
        axes[1,1].set_xlabel('Opening Angle (rad)')
        axes[1,1].set_ylabel('Photon Count')
        axes[1,1].set_title('Opening Angle Distribution')
        axes[1,1].grid(True, alpha=0.3)
        
        distance_dist = np.sum(self.histogram, axis=(0, 1))
        axes[1,2].plot(self.bin_centers[2], distance_dist, 'r-', linewidth=2)
        axes[1,2].set_xlabel('Distance (mm)')
        axes[1,2].set_ylabel('Photon Count')
        axes[1,2].set_title('Distance Distribution')
        axes[1,2].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_path / "photon_table_analysis.png", dpi=200, bbox_inches='tight')
        print(f"Main analysis plot saved to: {output_path / 'photon_table_analysis.png'}")
        
    def query_interpolate(self, energy, angle, distance):
        """Query the table using trilinear interpolation."""
        if self.histogram is None:
            return 0.0
            
        # Check bounds
        if (energy < self.energy_range[0] or energy > self.energy_range[1] or
            angle < self.angle_range[0] or angle > self.angle_range[1] or
            distance < self.distance_range[0] or distance > self.distance_range[1]):
            return 0.0
        
        # Find bin indices
        energy_idx = np.searchsorted(self.bin_edges[0], energy) - 1
        angle_idx = np.searchsorted(self.bin_edges[1], angle) - 1
        distance_idx = np.searchsorted(self.bin_edges[2], distance) - 1
        
        # Ensure valid indices
        energy_idx = max(0, min(energy_idx, self.energy_bins - 2))
        angle_idx = max(0, min(angle_idx, self.angle_bins - 2))
        distance_idx = max(0, min(distance_idx, self.distance_bins - 2))
        
        # Get fractional positions
        energy_frac = ((energy - self.bin_edges[0][energy_idx]) / 
                      (self.bin_edges[0][energy_idx + 1] - self.bin_edges[0][energy_idx]))
        angle_frac = ((angle - self.bin_edges[1][angle_idx]) / 
                     (self.bin_edges[1][angle_idx + 1] - self.bin_edges[1][angle_idx]))
        distance_frac = ((distance - self.bin_edges[2][distance_idx]) / 
                        (self.bin_edges[2][distance_idx + 1] - self.bin_edges[2][distance_idx]))
        
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

def create_energy_histogram(root_file_path, output_dir):
    """Create energy histogram of all events."""
    print(f"Creating energy histogram...")
    
    with uproot.open(root_file_path) as file:
        tree = file["OpticalPhotons"]
        data = tree.arrays(['PrimaryEnergy'], library="np")
        energies = data['PrimaryEnergy']
    
    plt.figure(figsize=(8, 4))
    counts, bins, _ = plt.hist(energies, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
    plt.xlabel('Muon Energy (MeV)', fontsize=12)
    plt.ylabel('Number of Events', fontsize=12)
    plt.title(f'Energy Distribution of {len(energies)} Muon Events', fontsize=14)
    plt.grid(True, alpha=0.3)
    
    # Add statistics
    stats_text = f'Mean: {energies.mean():.1f} MeV\nStd: {energies.std():.1f} MeV\nRange: {energies.min():.1f} - {energies.max():.1f} MeV'
    plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes, 
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    plt.savefig(output_path / "energy_histogram.png", dpi=200, bbox_inches='tight')
    print(f"Energy histogram saved to: {output_path / 'energy_histogram.png'}")

def main():
    parser = argparse.ArgumentParser(description='Create 3D Cherenkov photon lookup table')
    parser.add_argument('--input', '-i', default='1k_mu_optical_photons.root',
                       help='Input ROOT file path')
    parser.add_argument('--output', '-o', default='output',
                       help='Output directory')
    parser.add_argument('--events', '-e', type=int, default=None,
                       help='Max number of events to process (default: all)')
    parser.add_argument('--energy-bins', type=int, default=100,
                       help='Number of energy bins')
    parser.add_argument('--angle-bins', type=int, default=100,
                       help='Number of opening angle bins')
    parser.add_argument('--distance-bins', type=int, default=100,
                       help='Number of distance bins')
    
    args = parser.parse_args()
    
    # Find input file
    input_path = Path(args.input)
    if not input_path.exists():
        for possible in [Path(args.input), Path("build/optical_photons.root")]:
            if possible.exists():
                input_path = possible
                break
        else:
            print(f"Error: Input file not found: {args.input}")
            return
    
    print(f"=== 3D Cherenkov Photon Table Creation ===")
    print(f"Input file: {input_path}")
    print(f"Output directory: {args.output}")
    
    # Create energy histogram
    create_energy_histogram(input_path, args.output)
    
    # Create 3D table
    table = PhotonTable3D(args.energy_bins, args.angle_bins, args.distance_bins)
    
    # Process data
    energies, angles, distances = table.load_and_process_data(input_path, args.events)
    
    # Create histogram
    table.create_histogram(energies, angles, distances)
    
    # Save table
    table.save_table(args.output)
    
    # Create visualizations
    table.create_visualizations(args.output)
    
    # Test the table
    print(f"\nTesting table queries:")
    test_cases = [
        (250, 0.3, 1000),
        (400, 0.6, 5000),
        (150, 0.1, 500),
    ]
    
    for energy, angle, distance in test_cases:
        result = table.query_interpolate(energy, angle, distance)
        print(f"  E={energy} MeV, θ={angle:.1f} rad, d={distance} mm → {result:.1f} photons")
    
    print(f"\n=== Table Creation Complete! ===")
    print(f"All outputs saved to: {args.output}/")
    print(f"- photon_histogram_3d.npy: The 3D lookup table")
    print(f"- table_metadata.npz: Bin edges and metadata")
    print(f"- photon_table_analysis.png: Visualization plots")
    print(f"- energy_histogram.png: Energy distribution")

if __name__ == "__main__":
    main()