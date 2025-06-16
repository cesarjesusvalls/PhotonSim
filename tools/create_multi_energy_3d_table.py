#!/usr/bin/env python3
"""
Create a 3D lookup table from multiple energy ROOT files (100-1000 MeV).

This script processes all ROOT files in the data/mu-/ directory to create
a comprehensive 3D lookup table with axes:
1. Muon energy (MeV) - from file energies
2. Photon opening angle w.r.t. muon direction (radians)
3. Distance between photon origin and track origin (mm)
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import uproot
from pathlib import Path
import argparse
import re
from tqdm import tqdm

class MultiEnergyPhotonTable3D:
    """3D table for Cherenkov photon analysis across multiple energies."""
    
    def __init__(self, angle_bins=50, distance_bins=50, use_histogram_bins=True):
        """
        Initialize the 3D table.
        
        Parameters:
        -----------
        angle_bins : int  
            Number of bins for opening angle axis (ignored if use_histogram_bins=True)
        distance_bins : int
            Number of bins for distance axis (ignored if use_histogram_bins=True)
        use_histogram_bins : bool
            If True, use the bin structure from the ROOT histograms (500x500)
        """
        self.use_histogram_bins = use_histogram_bins
        
        if use_histogram_bins:
            # Use the histogram bins directly
            self.angle_bins = 500
            self.distance_bins = 500
        else:
            self.angle_bins = angle_bins
            self.distance_bins = distance_bins
        
        # Energy values will be determined from available files
        self.energy_values = []
        
        # Define bin ranges from histogram
        self.angle_range = (0, np.pi)  # 0 to pi radians
        self.distance_range = (0, 10000)  # 0 to 10000 mm
        
        # 3D histogram data
        self.photon_table = None
        self.bin_edges = None
        self.bin_centers = None
        
    def find_root_files(self, data_dir):
        """Find all ROOT files in the data directory."""
        data_path = Path(data_dir)
        root_files = []
        energy_pattern = re.compile(r'(\d+)MeV')
        
        # Look for all output.root files in energy subdirectories
        for energy_dir in sorted(data_path.glob('*/output.root')):
            # Extract energy from directory name
            match = energy_pattern.search(str(energy_dir.parent))
            if match:
                energy = int(match.group(1))
                root_files.append((energy, energy_dir))
        
        root_files.sort(key=lambda x: x[0])  # Sort by energy
        self.energy_values = [e for e, _ in root_files]
        
        print(f"Found {len(root_files)} ROOT files")
        print(f"Energy range: {self.energy_values[0]} - {self.energy_values[-1]} MeV")
        
        return root_files
    
    def process_single_file(self, root_file_path, energy, max_events=None):
        """Process a single ROOT file and extract 2D histogram data."""
        # Try to read the pre-computed histogram first
        try:
            with uproot.open(root_file_path) as file:
                if "PhotonHist_AngleDistance" in file:
                    hist = file["PhotonHist_AngleDistance"]
                    # Get histogram data
                    counts = hist.values()
                    edges_x = hist.axis(0).edges()  # Angle edges
                    edges_y = hist.axis(1).edges()  # Distance edges
                    
                    print(f"  Loaded pre-computed histogram for {energy} MeV")
                    print(f"  Shape: {counts.shape}, Total photons: {counts.sum():.0f}")
                    
                    return counts, (edges_x, edges_y)
        except Exception as e:
            print(f"  Could not load histogram: {e}")
        
        # If histogram not available, process raw data
        print(f"  Processing raw data for {energy} MeV...")
        
        with uproot.open(root_file_path) as file:
            tree = file["OpticalPhotons"]
            
            # Determine how many events to process
            total_events = tree.num_entries
            if max_events is None:
                max_events = min(100, total_events)  # Default to 100 events
            
            # Load necessary branches
            branches = ["PhotonPosX", "PhotonPosY", "PhotonPosZ",
                       "PhotonDirX", "PhotonDirY", "PhotonDirZ", 
                       "PhotonProcess"]
            
            data = tree.arrays(branches, entry_stop=max_events, library="np")
            
            # Collect angle and distance data
            angles = []
            distances = []
            
            for event_idx in range(len(data['PhotonPosX'])):
                # Filter for Cherenkov photons only
                process_mask = data['PhotonProcess'][event_idx] == 0  # 0 = Cherenkov
                
                if np.any(process_mask):
                    # Calculate angles
                    photon_dirs = np.column_stack([
                        data["PhotonDirX"][event_idx][process_mask],
                        data["PhotonDirY"][event_idx][process_mask],
                        data["PhotonDirZ"][event_idx][process_mask]
                    ])
                    
                    # Muon direction is along +z
                    cos_angles = photon_dirs[:, 2]  # z-component
                    cos_angles = np.clip(cos_angles, -1.0, 1.0)
                    event_angles = np.arccos(cos_angles)
                    
                    # Calculate distances (convert m to mm)
                    photon_pos = np.column_stack([
                        data["PhotonPosX"][event_idx][process_mask] * 1000,
                        data["PhotonPosY"][event_idx][process_mask] * 1000,
                        data["PhotonPosZ"][event_idx][process_mask] * 1000
                    ])
                    event_distances = np.sqrt(np.sum(photon_pos**2, axis=1))
                    
                    angles.extend(event_angles)
                    distances.extend(event_distances)
            
            angles = np.array(angles)
            distances = np.array(distances)
            
            # Create 2D histogram
            counts, x_edges, y_edges = np.histogram2d(
                angles, distances,
                bins=[self.angle_bins, self.distance_bins],
                range=[self.angle_range, self.distance_range]
            )
            
            print(f"  Processed {len(angles)} Cherenkov photons")
            
            return counts, (x_edges, y_edges)
    
    def create_3d_table(self, data_dir, max_events_per_file=None):
        """Create the full 3D table from all ROOT files."""
        print("Creating 3D lookup table...")
        
        # Find all ROOT files
        root_files = self.find_root_files(data_dir)
        
        if not root_files:
            raise ValueError(f"No ROOT files found in {data_dir}")
        
        # Initialize 3D array
        self.photon_table = np.zeros((len(self.energy_values), 
                                     self.angle_bins, 
                                     self.distance_bins))
        
        # Process each file
        print("\nProcessing files:")
        for idx, (energy, file_path) in enumerate(tqdm(root_files)):
            counts, edges = self.process_single_file(file_path, energy, max_events_per_file)
            
            # If we got a different shape than expected, handle it
            if counts.shape != (self.angle_bins, self.distance_bins):
                if self.use_histogram_bins and idx == 0:
                    # Update dimensions based on first histogram
                    self.angle_bins, self.distance_bins = counts.shape
                    self.photon_table = np.zeros((len(self.energy_values), 
                                                 self.angle_bins, 
                                                 self.distance_bins))
                else:
                    print(f"Warning: Histogram shape {counts.shape} doesn't match expected {(self.angle_bins, self.distance_bins)}")
                    continue
            
            # Store in 3D array
            self.photon_table[idx] = counts
            
            # Store bin edges from first file
            if idx == 0:
                self.bin_edges = (
                    np.array(self.energy_values),
                    edges[0],  # angle edges
                    edges[1]   # distance edges
                )
                # Update actual dimensions
                self.angle_bins = len(edges[0]) - 1
                self.distance_bins = len(edges[1]) - 1
        
        # Calculate bin centers
        self.bin_centers = (
            np.array(self.energy_values),
            (self.bin_edges[1][:-1] + self.bin_edges[1][1:]) / 2,
            (self.bin_edges[2][:-1] + self.bin_edges[2][1:]) / 2
        )
        
        # Update actual ranges based on data
        self.angle_range = (self.bin_edges[1][0], self.bin_edges[1][-1])
        self.distance_range = (self.bin_edges[2][0], self.bin_edges[2][-1])
        
        print(f"\n3D table created successfully!")
        print(f"Shape: {self.photon_table.shape}")
        print(f"Total photons: {self.photon_table.sum():.0f}")
        print(f"Non-zero bins: {np.count_nonzero(self.photon_table)}")
        
    def save_table(self, output_path):
        """Save the 3D table to files."""
        output_path = Path(output_path)
        output_path.mkdir(exist_ok=True, parents=True)
        
        # Save the photon counts array
        np.save(output_path / "photon_table_3d.npy", self.photon_table)
        
        # Save metadata
        metadata = {
            'energy_values': self.energy_values,
            'angle_bins': self.angle_bins,
            'distance_bins': self.distance_bins,
            'angle_range': self.angle_range,
            'distance_range': self.distance_range,
            'energy_edges': self.bin_edges[0],
            'angle_edges': self.bin_edges[1],
            'distance_edges': self.bin_edges[2],
            'energy_centers': self.bin_centers[0],
            'angle_centers': self.bin_centers[1],
            'distance_centers': self.bin_centers[2],
            'table_shape': self.photon_table.shape,
            'total_photons': self.photon_table.sum(),
            'non_zero_bins': np.count_nonzero(self.photon_table)
        }
        
        np.savez(output_path / "table_metadata.npz", **metadata)
        
        print(f"\n3D table saved to {output_path}")
        print(f"  - photon_table_3d.npy: Main 3D array")
        print(f"  - table_metadata.npz: Metadata and bin information")
    
    def create_visualizations(self, output_path=None):
        """Create comprehensive visualizations of the 3D table."""
        if self.photon_table is None:
            print("No data to visualize. Run create_3d_table first.")
            return
        
        print("\nCreating visualizations...")
        
        # Create figure with subplots
        fig = plt.figure(figsize=(20, 16))
        
        # 1. Energy slices showing angle vs distance
        for i in range(4):
            plt.subplot(4, 4, i+1)
            energy_idx = i * len(self.energy_values) // 4
            energy = self.energy_values[energy_idx]
            
            im = plt.imshow(self.photon_table[energy_idx].T, 
                           origin='lower', aspect='auto', cmap='viridis',
                           extent=[self.angle_range[0], self.angle_range[1],
                                  self.distance_range[0], self.distance_range[1]])
            plt.colorbar(im, label='Photon Count')
            plt.xlabel('Opening Angle (rad)')
            plt.ylabel('Distance (mm)')
            plt.title(f'Energy = {energy} MeV')
        
        # 2. Projections along each axis
        # Energy projection
        plt.subplot(4, 4, 5)
        energy_projection = np.sum(self.photon_table, axis=(1, 2))
        plt.plot(self.energy_values, energy_projection, 'b-', linewidth=2)
        plt.xlabel('Energy (MeV)')
        plt.ylabel('Total Photon Count')
        plt.title('Energy Distribution')
        plt.grid(True, alpha=0.3)
        
        # Angle projection
        plt.subplot(4, 4, 6)
        angle_projection = np.sum(self.photon_table, axis=(0, 2))
        plt.plot(self.bin_centers[1], angle_projection, 'g-', linewidth=2)
        plt.xlabel('Opening Angle (rad)')
        plt.ylabel('Total Photon Count')
        plt.title('Opening Angle Distribution')
        plt.grid(True, alpha=0.3)
        
        # Distance projection
        plt.subplot(4, 4, 7)
        distance_projection = np.sum(self.photon_table, axis=(0, 1))
        plt.plot(self.bin_centers[2], distance_projection, 'r-', linewidth=2)
        plt.xlabel('Distance (mm)')
        plt.ylabel('Total Photon Count')
        plt.title('Distance Distribution')
        plt.grid(True, alpha=0.3)
        
        # 3. 2D projections
        # Energy vs Angle
        plt.subplot(4, 4, 9)
        proj_ea = np.sum(self.photon_table, axis=2)
        im = plt.imshow(proj_ea.T, origin='lower', aspect='auto', cmap='viridis',
                       extent=[self.energy_values[0], self.energy_values[-1],
                              self.angle_range[0], self.angle_range[1]])
        plt.colorbar(im, label='Photon Count')
        plt.xlabel('Energy (MeV)')
        plt.ylabel('Opening Angle (rad)')
        plt.title('Energy vs Angle (summed over distance)')
        
        # Energy vs Distance
        plt.subplot(4, 4, 10)
        proj_ed = np.sum(self.photon_table, axis=1)
        im = plt.imshow(proj_ed.T, origin='lower', aspect='auto', cmap='viridis',
                       extent=[self.energy_values[0], self.energy_values[-1],
                              self.distance_range[0], self.distance_range[1]])
        plt.colorbar(im, label='Photon Count')
        plt.xlabel('Energy (MeV)')
        plt.ylabel('Distance (mm)')
        plt.title('Energy vs Distance (summed over angle)')
        
        # Angle vs Distance
        plt.subplot(4, 4, 11)
        proj_ad = np.sum(self.photon_table, axis=0)
        im = plt.imshow(proj_ad.T, origin='lower', aspect='auto', cmap='viridis',
                       extent=[self.angle_range[0], self.angle_range[1],
                              self.distance_range[0], self.distance_range[1]])
        plt.colorbar(im, label='Photon Count')
        plt.xlabel('Opening Angle (rad)')
        plt.ylabel('Distance (mm)')
        plt.title('Angle vs Distance (summed over energy)')
        
        # 4. 3D visualization of high-density regions
        ax3d = fig.add_subplot(4, 4, 13, projection='3d')
        
        # Find bins with significant counts
        threshold = np.percentile(self.photon_table[self.photon_table > 0], 95)
        high_indices = np.where(self.photon_table >= threshold)
        
        if len(high_indices[0]) > 0:
            # Sample points for visualization (limit to 1000 points)
            n_points = min(1000, len(high_indices[0]))
            sample_idx = np.random.choice(len(high_indices[0]), n_points, replace=False)
            
            energies = self.energy_values[high_indices[0][sample_idx]]
            angles = self.bin_centers[1][high_indices[1][sample_idx]]
            distances = self.bin_centers[2][high_indices[2][sample_idx]]
            counts = self.photon_table[high_indices[0][sample_idx], 
                                      high_indices[1][sample_idx], 
                                      high_indices[2][sample_idx]]
            
            scatter = ax3d.scatter(energies, angles, distances, 
                                 c=counts, cmap='viridis', s=30, alpha=0.6)
            ax3d.set_xlabel('Energy (MeV)')
            ax3d.set_ylabel('Angle (rad)')
            ax3d.set_zlabel('Distance (mm)')
            ax3d.set_title('High-Density Regions')
            plt.colorbar(scatter, label='Photon Count', shrink=0.5)
        
        # 5. Statistics summary
        plt.subplot(4, 4, 16)
        plt.text(0.1, 0.9, "3D Table Statistics:", fontsize=14, fontweight='bold',
                transform=plt.gca().transAxes)
        stats_text = f"""
Energy range: {self.energy_values[0]}-{self.energy_values[-1]} MeV
Number of energies: {len(self.energy_values)}
Angle bins: {self.angle_bins}
Distance bins: {self.distance_bins}
Total table size: {self.photon_table.shape}
Total photons: {self.photon_table.sum():.2e}
Non-zero bins: {np.count_nonzero(self.photon_table):,} ({100*np.count_nonzero(self.photon_table)/self.photon_table.size:.1f}%)
Max bin count: {self.photon_table.max():.0f}
Mean (non-zero): {self.photon_table[self.photon_table>0].mean():.1f}
"""
        plt.text(0.1, 0.05, stats_text, transform=plt.gca().transAxes,
                fontsize=10, family='monospace')
        plt.axis('off')
        
        plt.tight_layout()
        
        if output_path:
            output_path = Path(output_path)
            output_path.mkdir(exist_ok=True, parents=True)
            plt.savefig(output_path / "3d_table_visualizations.png", 
                       dpi=150, bbox_inches='tight')
            print(f"Visualizations saved to {output_path}")
        
        plt.show()
        
        # Additional specific energy plots
        self.create_energy_comparison_plot(output_path)
    
    def create_energy_comparison_plot(self, output_path=None):
        """Create a plot comparing angle-distance distributions at different energies."""
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        axes = axes.flatten()
        
        # Select 6 representative energies
        energy_indices = np.linspace(0, len(self.energy_values)-1, 6, dtype=int)
        
        for i, idx in enumerate(energy_indices):
            ax = axes[i]
            energy = self.energy_values[idx]
            
            # Plot the 2D histogram for this energy
            im = ax.imshow(self.photon_table[idx].T, 
                          origin='lower', aspect='auto', cmap='viridis',
                          extent=[self.angle_range[0], self.angle_range[1],
                                 self.distance_range[0], self.distance_range[1]])
            
            ax.set_xlabel('Opening Angle (rad)')
            ax.set_ylabel('Distance (mm)')
            ax.set_title(f'{energy} MeV')
            
            # Add colorbar
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label('Photon Count', rotation=270, labelpad=15)
        
        plt.suptitle('Photon Distribution at Different Energies', fontsize=16)
        plt.tight_layout()
        
        if output_path:
            plt.savefig(Path(output_path) / "energy_comparison.png", 
                       dpi=150, bbox_inches='tight')
        
        plt.show()


def main():
    parser = argparse.ArgumentParser(
        description='Create 3D photon lookup table from multiple energy ROOT files')
    parser.add_argument('--data-dir', '-d', 
                       default='data/mu-',
                       help='Directory containing energy subdirectories with ROOT files')
    parser.add_argument('--output', '-o', 
                       default='output/3d_lookup_table',
                       help='Output directory for table and visualizations')
    parser.add_argument('--angle-bins', type=int, default=50,
                       help='Number of opening angle bins (ignored if using histogram bins)')
    parser.add_argument('--distance-bins', type=int, default=50,
                       help='Number of distance bins (ignored if using histogram bins)')
    parser.add_argument('--use-histogram-bins', action='store_true', default=True,
                       help='Use the bin structure from ROOT histograms (500x500)')
    parser.add_argument('--rebin', action='store_true',
                       help='Rebin histograms to specified angle/distance bins')
    parser.add_argument('--max-events', type=int, default=None,
                       help='Maximum events to process per file (default: use histogram if available)')
    parser.add_argument('--visualize', action='store_true',
                       help='Create visualizations after building table')
    
    args = parser.parse_args()
    
    # Create table builder
    table_builder = MultiEnergyPhotonTable3D(
        angle_bins=args.angle_bins,
        distance_bins=args.distance_bins,
        use_histogram_bins=not args.rebin
    )
    
    # Build the 3D table
    table_builder.create_3d_table(args.data_dir, args.max_events)
    
    # Save the table
    table_builder.save_table(args.output)
    
    # Create visualizations if requested
    if args.visualize:
        table_builder.create_visualizations(args.output)
    
    print("\nDone! 3D lookup table created successfully.")


if __name__ == "__main__":
    main()