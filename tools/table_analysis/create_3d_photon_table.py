#!/usr/bin/env python3
"""
Create a 3D table from the 1k muon optical photon data.

Axes:
1. Muon energy (MeV)
2. Photon opening angle with respect to muon direction (radians)
3. Distance between photon origin and track origin (mm)

This script creates regular binning for all three axes and provides visualization.
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import uproot
from pathlib import Path
import argparse

class PhotonTable3D:
    """3D table for Cherenkov photon analysis."""
    
    def __init__(self, energy_bins=20, angle_bins=30, distance_bins=25):
        """
        Initialize the 3D table.
        
        Parameters:
        -----------
        energy_bins : int
            Number of bins for muon energy axis
        angle_bins : int  
            Number of bins for opening angle axis
        distance_bins : int
            Number of bins for distance axis
        """
        self.energy_bins = energy_bins
        self.angle_bins = angle_bins
        self.distance_bins = distance_bins
        
        # Define bin ranges (will be set based on data)
        self.energy_range = None
        self.angle_range = None 
        self.distance_range = None
        
        # 3D histogram data
        self.photon_counts = None
        self.bin_edges = None
        self.bin_centers = None
        
    def load_data(self, root_file_path, max_events=20, sample_fraction=0.1):
        """Load and process data from ROOT file."""
        print(f"Loading data from {root_file_path}...")
        
        # Open ROOT file
        with uproot.open(root_file_path) as file:
            tree = file["OpticalPhotons"]
            
            # Load all branches we need
            branches = [
                "EventID", "PrimaryEnergy", "PhotonPosX", "PhotonPosY", "PhotonPosZ",
                "PhotonDirX", "PhotonDirY", "PhotonDirZ", "PhotonParent"
            ]
            
            # Load only first few events to keep memory manageable
            data = tree.arrays(branches, entry_stop=max_events, library="np")
            print(f"Processing {max_events} events (of {tree.num_entries} total)")
            
        # Flatten the data since it's stored per event
        flattened_data = {}
        total_photons = 0
        
        for event_idx in range(len(data['EventID'])):
            n_photons = len(data['PhotonPosX'][event_idx])
            
            # Sample photons to reduce memory usage
            if n_photons > 1000:  # Sample if too many photons
                sample_size = max(100, int(n_photons * sample_fraction))
                indices = np.random.choice(n_photons, sample_size, replace=False)
                indices = np.sort(indices)
            else:
                indices = np.arange(n_photons)
            
            n_sampled = len(indices)
            total_photons += n_sampled
            
            for key in data.keys():
                if key not in flattened_data:
                    flattened_data[key] = []
                
                if key in ['EventID', 'PrimaryEnergy']:
                    # These are per-event values, repeat for each photon
                    flattened_data[key].extend([data[key][event_idx]] * n_sampled)
                else:
                    # These are per-photon values, sample them
                    sampled_values = [data[key][event_idx][i] for i in indices]
                    flattened_data[key].extend(sampled_values)
        
        # Convert to numpy arrays
        for key in flattened_data.keys():
            flattened_data[key] = np.array(flattened_data[key])
            
        print(f"Loaded {total_photons} photon records from {len(data['EventID'])} events")
        
        # Filter for muon-generated photons only
        muon_mask = flattened_data["PhotonParent"] == "mu-"
        
        muon_photons = {}
        for key in flattened_data.keys():
            muon_photons[key] = flattened_data[key][muon_mask]
        
        print(f"Found {len(muon_photons['EventID'])} muon-generated photons")
        
        return self._process_photon_data(muon_photons)
    
    def _process_photon_data(self, data):
        """Process photon data to extract the three axis variables."""
        print("Processing photon data...")
        
        # 1. Muon energy (already in MeV)
        muon_energy = data["PrimaryEnergy"]
        
        # 2. Calculate opening angle with muon direction
        # Muon direction is along +z axis (0, 0, 1)
        muon_dir = np.array([0, 0, 1])
        
        photon_dirs = np.column_stack([
            data["PhotonDirX"],
            data["PhotonDirY"], 
            data["PhotonDirZ"]
        ])
        
        # Calculate opening angle using dot product
        # cos(θ) = photon_dir · muon_dir
        cos_angles = np.dot(photon_dirs, muon_dir)
        # Ensure values are in valid range for arccos
        cos_angles = np.clip(cos_angles, -1.0, 1.0)
        opening_angles = np.arccos(cos_angles)
        
        # 3. Calculate distance from track origin
        # Track origin is at (0, 0, 0), photon positions in meters -> convert to mm
        photon_positions = np.column_stack([
            data["PhotonPosX"] * 1000,  # m to mm
            data["PhotonPosY"] * 1000,
            data["PhotonPosZ"] * 1000
        ])
        
        # Distance from origin to photon creation point
        distances = np.sqrt(np.sum(photon_positions**2, axis=1))
        
        # Create processed data dictionary
        processed_data = {
            'muon_energy': muon_energy,
            'opening_angle': opening_angles,
            'distance_from_origin': distances,
            'photon_x': photon_positions[:, 0],
            'photon_y': photon_positions[:, 1], 
            'photon_z': photon_positions[:, 2]
        }
        
        print(f"Energy range: {muon_energy.min():.1f} - {muon_energy.max():.1f} MeV")
        print(f"Opening angle range: {opening_angles.min():.3f} - {opening_angles.max():.3f} rad")
        print(f"Distance range: {distances.min():.1f} - {distances.max():.1f} mm")
        
        return processed_data
    
    def create_3d_histogram(self, data):
        """Create the 3D histogram table."""
        print("Creating 3D histogram...")
        
        # Define bin ranges based on data
        self.energy_range = (data['muon_energy'].min(), data['muon_energy'].max())
        self.angle_range = (data['opening_angle'].min(), data['opening_angle'].max())
        
        # Limit distance range to remove extreme outliers
        distance_95th = np.percentile(data['distance_from_origin'], 95)
        self.distance_range = (0, distance_95th)
        
        # Filter data to distance range
        distance_mask = data['distance_from_origin'] <= distance_95th
        filtered_data = {}
        for key in data.keys():
            filtered_data[key] = data[key][distance_mask]
        print(f"Using {len(filtered_data['muon_energy'])} photons after distance filtering (95th percentile: {distance_95th:.1f} mm)")
        
        # Create bin edges
        energy_edges = np.linspace(self.energy_range[0], self.energy_range[1], self.energy_bins + 1)
        angle_edges = np.linspace(self.angle_range[0], self.angle_range[1], self.angle_bins + 1)
        distance_edges = np.linspace(self.distance_range[0], self.distance_range[1], self.distance_bins + 1)
        
        self.bin_edges = (energy_edges, angle_edges, distance_edges)
        
        # Create bin centers for visualization
        self.bin_centers = (
            (energy_edges[:-1] + energy_edges[1:]) / 2,
            (angle_edges[:-1] + angle_edges[1:]) / 2,
            (distance_edges[:-1] + distance_edges[1:]) / 2
        )
        
        # Create 3D histogram
        self.photon_counts, _ = np.histogramdd(
            np.column_stack([
                filtered_data['muon_energy'],
                filtered_data['opening_angle'],
                filtered_data['distance_from_origin']
            ]),
            bins=self.bin_edges
        )
        
        print(f"3D histogram shape: {self.photon_counts.shape}")
        print(f"Total photons in histogram: {self.photon_counts.sum()}")
        print(f"Max photons in single bin: {self.photon_counts.max()}")
        
        return filtered_data
    
    def save_table(self, output_path):
        """Save the 3D table to files."""
        output_path = Path(output_path)
        output_path.mkdir(exist_ok=True)
        
        # Save the photon counts array
        np.save(output_path / "photon_counts_3d.npy", self.photon_counts)
        
        # Save bin information
        bin_info = {
            'energy_bins': self.energy_bins,
            'angle_bins': self.angle_bins,
            'distance_bins': self.distance_bins,
            'energy_range': self.energy_range,
            'angle_range': self.angle_range,
            'distance_range': self.distance_range,
            'energy_edges': self.bin_edges[0],
            'angle_edges': self.bin_edges[1],
            'distance_edges': self.bin_edges[2],
            'energy_centers': self.bin_centers[0],
            'angle_centers': self.bin_centers[1],
            'distance_centers': self.bin_centers[2]
        }
        
        np.savez(output_path / "bin_info.npz", **bin_info)
        
        print(f"3D table saved to {output_path}")
    
    def visualize_table(self, output_path=None):
        """Create visualizations of the 3D table."""
        if self.photon_counts is None:
            print("No data to visualize. Run create_3d_histogram first.")
            return
        
        print("Creating visualizations...")
        
        # Set up the plotting style
        plt.style.use('default')
        
        fig = plt.figure(figsize=(20, 15))
        
        # 1. 2D projections of the 3D histogram
        
        # Energy vs Angle (summed over distance)
        plt.subplot(3, 3, 1)
        projection_ea = np.sum(self.photon_counts, axis=2)
        plt.imshow(projection_ea.T, origin='lower', aspect='auto', cmap='viridis')
        plt.colorbar(label='Photon Count')
        plt.xlabel('Energy Bin')
        plt.ylabel('Opening Angle Bin')
        plt.title('Energy vs Opening Angle\n(summed over distance)')
        
        # Energy vs Distance (summed over angle)
        plt.subplot(3, 3, 2)
        projection_ed = np.sum(self.photon_counts, axis=1)
        plt.imshow(projection_ed.T, origin='lower', aspect='auto', cmap='viridis')
        plt.colorbar(label='Photon Count')
        plt.xlabel('Energy Bin')
        plt.ylabel('Distance Bin')
        plt.title('Energy vs Distance\n(summed over angle)')
        
        # Angle vs Distance (summed over energy)
        plt.subplot(3, 3, 3)
        projection_ad = np.sum(self.photon_counts, axis=0)
        plt.imshow(projection_ad.T, origin='lower', aspect='auto', cmap='viridis')
        plt.colorbar(label='Photon Count')
        plt.xlabel('Opening Angle Bin')
        plt.ylabel('Distance Bin')
        plt.title('Opening Angle vs Distance\n(summed over energy)')
        
        # 2. 1D projections
        
        # Energy distribution
        plt.subplot(3, 3, 4)
        energy_dist = np.sum(self.photon_counts, axis=(1, 2))
        plt.plot(self.bin_centers[0], energy_dist, 'b-', linewidth=2)
        plt.xlabel('Muon Energy (MeV)')
        plt.ylabel('Photon Count')
        plt.title('Energy Distribution')
        plt.grid(True, alpha=0.3)
        
        # Opening angle distribution
        plt.subplot(3, 3, 5)
        angle_dist = np.sum(self.photon_counts, axis=(0, 2))
        plt.plot(self.bin_centers[1], angle_dist, 'g-', linewidth=2)
        plt.xlabel('Opening Angle (rad)')
        plt.ylabel('Photon Count')
        plt.title('Opening Angle Distribution')
        plt.grid(True, alpha=0.3)
        
        # Distance distribution
        plt.subplot(3, 3, 6)
        distance_dist = np.sum(self.photon_counts, axis=(0, 1))
        plt.plot(self.bin_centers[2], distance_dist, 'r-', linewidth=2)
        plt.xlabel('Distance from Origin (mm)')
        plt.ylabel('Photon Count')
        plt.title('Distance Distribution')
        plt.grid(True, alpha=0.3)
        
        # 3. 3D scatter plot of bin centers with highest counts
        ax3d = fig.add_subplot(3, 3, 7, projection='3d')
        
        # Find bins with significant photon counts (top 1%)
        threshold = np.percentile(self.photon_counts[self.photon_counts > 0], 99)
        high_count_indices = np.where(self.photon_counts >= threshold)
        
        if len(high_count_indices[0]) > 0:
            # Get bin centers for high-count bins
            high_energy = self.bin_centers[0][high_count_indices[0]]
            high_angle = self.bin_centers[1][high_count_indices[1]]
            high_distance = self.bin_centers[2][high_count_indices[2]]
            high_counts = self.photon_counts[high_count_indices]
            
            # Create 3D scatter plot
            scatter = ax3d.scatter(high_energy, high_angle, high_distance, 
                                c=high_counts, cmap='viridis', s=50, alpha=0.7)
            
            ax3d.set_xlabel('Energy (MeV)')
            ax3d.set_ylabel('Opening Angle (rad)')
            ax3d.set_zlabel('Distance (mm)')
            ax3d.set_title('High-Count Bins in 3D Space')
            plt.colorbar(scatter, label='Photon Count', shrink=0.5)
        
        # 4. Cross-sections at specific values
        
        # Cross-section at middle energy
        plt.subplot(3, 3, 8)
        mid_energy_idx = self.energy_bins // 2
        cross_section = self.photon_counts[mid_energy_idx, :, :]
        plt.imshow(cross_section.T, origin='lower', aspect='auto', cmap='viridis')
        plt.colorbar(label='Photon Count')
        plt.xlabel('Opening Angle Bin')
        plt.ylabel('Distance Bin')
        plt.title(f'Cross-section at E = {self.bin_centers[0][mid_energy_idx]:.1f} MeV')
        
        # Summary statistics
        plt.subplot(3, 3, 9)
        plt.text(0.1, 0.9, f"3D Table Statistics:", transform=plt.gca().transAxes, 
                fontsize=12, fontweight='bold')
        plt.text(0.1, 0.8, f"Energy bins: {self.energy_bins}", transform=plt.gca().transAxes)
        plt.text(0.1, 0.7, f"Angle bins: {self.angle_bins}", transform=plt.gca().transAxes)
        plt.text(0.1, 0.6, f"Distance bins: {self.distance_bins}", transform=plt.gca().transAxes)
        plt.text(0.1, 0.5, f"Total photons: {int(self.photon_counts.sum()):,}", transform=plt.gca().transAxes)
        plt.text(0.1, 0.4, f"Non-zero bins: {np.count_nonzero(self.photon_counts)}", transform=plt.gca().transAxes)
        plt.text(0.1, 0.3, f"Max bin count: {int(self.photon_counts.max())}", transform=plt.gca().transAxes)
        plt.text(0.1, 0.2, f"Energy range: {self.energy_range[0]:.1f}-{self.energy_range[1]:.1f} MeV", 
                transform=plt.gca().transAxes)
        plt.text(0.1, 0.1, f"Distance range: 0-{self.distance_range[1]:.1f} mm", 
                transform=plt.gca().transAxes)
        plt.axis('off')
        
        plt.tight_layout()
        
        if output_path:
            output_path = Path(output_path)
            output_path.mkdir(exist_ok=True)
            plt.savefig(output_path / "3d_table_visualization.png", dpi=300, bbox_inches='tight')
            print(f"Visualization saved to {output_path / '3d_table_visualization.png'}")
        
        plt.show()
    
    def query_table(self, energy, angle, distance):
        """
        Query the 3D table for given parameters using nearest neighbor.
        
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
        if self.photon_counts is None:
            print("No data available. Run create_3d_histogram first.")
            return 0
        
        # Find nearest bin indices
        energy_idx = np.argmin(np.abs(self.bin_centers[0] - energy))
        angle_idx = np.argmin(np.abs(self.bin_centers[1] - angle))
        distance_idx = np.argmin(np.abs(self.bin_centers[2] - distance))
        
        # Check bounds
        if (energy_idx >= self.energy_bins or angle_idx >= self.angle_bins or 
            distance_idx >= self.distance_bins):
            return 0
        
        return self.photon_counts[energy_idx, angle_idx, distance_idx]


def main():
    """Main function to create and visualize the 3D photon table."""
    parser = argparse.ArgumentParser(description='Create 3D photon table from ROOT file')
    parser.add_argument('--input', '-i', default='1k_mu_optical_photons.root',
                       help='Input ROOT file path')
    parser.add_argument('--output', '-o', default='3d_photon_table',
                       help='Output directory for table and visualizations')
    parser.add_argument('--energy-bins', type=int, default=20,
                       help='Number of energy bins')
    parser.add_argument('--angle-bins', type=int, default=30,
                       help='Number of opening angle bins')
    parser.add_argument('--distance-bins', type=int, default=25,
                       help='Number of distance bins')
    
    args = parser.parse_args()
    
    # Check if input file exists
    input_path = Path(args.input)
    if not input_path.exists():
        # Try in current directory or build directory
        for possible_path in [Path.cwd() / args.input, Path.cwd() / "build" / "optical_photons.root"]:
            if possible_path.exists():
                input_path = possible_path
                break
        else:
            print(f"Error: Could not find input file {args.input}")
            return
    
    print(f"Using input file: {input_path}")
    
    # Create 3D table
    table = PhotonTable3D(
        energy_bins=args.energy_bins,
        angle_bins=args.angle_bins, 
        distance_bins=args.distance_bins
    )
    
    # Load and process data
    data = table.load_data(input_path)
    
    # Create 3D histogram
    filtered_data = table.create_3d_histogram(data)
    
    # Save table
    table.save_table(args.output)
    
    # Create visualizations
    table.visualize_table(args.output)
    
    # Test table query
    print("\nTesting table query:")
    mid_energy = (table.energy_range[0] + table.energy_range[1]) / 2
    mid_angle = (table.angle_range[0] + table.angle_range[1]) / 2
    mid_distance = table.distance_range[1] / 2
    
    result = table.query_table(mid_energy, mid_angle, mid_distance)
    print(f"Photon count at E={mid_energy:.1f} MeV, θ={mid_angle:.3f} rad, d={mid_distance:.1f} mm: {result:.0f}")
    
    print(f"\n3D photon table analysis complete!")
    print(f"Output saved to: {args.output}")


if __name__ == "__main__":
    main()