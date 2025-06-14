#!/usr/bin/env python3
"""
Create 3D photon lookup table from multiple discrete energy ROOT files.
Strategy: Generate 2D tables (angle vs distance) for each energy, then stack into 3D.
"""

import numpy as np
import uproot
import matplotlib.pyplot as plt
from pathlib import Path
import os
import sys

class DiscreteEnergyTableBuilder:
    def __init__(self, output_dir="output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Default binning for 2D tables (angle vs distance)
        self.angle_bins = 100
        self.distance_bins = 100
        
        # Storage for 2D tables and metadata
        self.energy_tables = {}  # energy -> 2D histogram
        self.energy_metadata = {}  # energy -> metadata dict
        
    def create_2d_table_from_file(self, root_file_path, energy_mev):
        """Create 2D lookup table (angle vs distance) from single energy ROOT file."""
        print(f"Processing {root_file_path} for {energy_mev} MeV...")
        
        try:
            with uproot.open(root_file_path) as file:
                tree = file['OpticalPhotons']
                
                # Read all data
                data = tree.arrays([
                    'EventID', 'PrimaryEnergy', 'NOpticalPhotons',
                    'PhotonPosX', 'PhotonPosY', 'PhotonPosZ',
                    'PhotonDirX', 'PhotonDirY', 'PhotonDirZ',
                    'PhotonTime'
                ], library='np')
                
        except Exception as e:
            print(f"Error reading {root_file_path}: {e}")
            return None
            
        # Process photon data
        all_angles = []
        all_distances = []
        total_photons = 0
        
        for event_idx in range(len(data['EventID'])):
            # Get photon data for this event
            pos_x = data['PhotonPosX'][event_idx]
            pos_y = data['PhotonPosY'][event_idx] 
            pos_z = data['PhotonPosZ'][event_idx]
            dir_x = data['PhotonDirX'][event_idx]
            dir_y = data['PhotonDirY'][event_idx]
            dir_z = data['PhotonDirZ'][event_idx]
            
            if len(pos_x) == 0:
                continue
                
            total_photons += len(pos_x)
            
            # Convert to numpy arrays
            positions = np.column_stack([pos_x, pos_y, pos_z])
            directions = np.column_stack([dir_x, dir_y, dir_z])
            
            # Sample photons if too many (for memory efficiency)
            max_photons_per_event = 1000
            if len(positions) > max_photons_per_event:
                indices = np.random.choice(len(positions), max_photons_per_event, replace=False)
                positions = positions[indices]
                directions = directions[indices]
            
            # Calculate opening angles with respect to muon direction (0,0,1)
            muon_direction = np.array([0, 0, 1])
            dot_products = np.dot(directions, muon_direction)
            # Clamp to valid range for arccos
            dot_products = np.clip(dot_products, -1.0, 1.0)
            opening_angles = np.arccos(dot_products)
            
            # Calculate distances from photon origins to track origin (0,0,0)
            distances = np.sqrt(np.sum(positions**2, axis=1))
            
            all_angles.extend(opening_angles)
            all_distances.extend(distances)
        
        if not all_angles:
            print(f"No photons found in {root_file_path}")
            return None
            
        all_angles = np.array(all_angles)
        all_distances = np.array(all_distances)
        
        print(f"  Total photons: {total_photons}")
        print(f"  Processed photons: {len(all_angles)}")
        print(f"  Angle range: {all_angles.min():.3f} - {all_angles.max():.3f} rad")
        print(f"  Distance range: {all_distances.min():.1f} - {all_distances.max():.1f} mm")
        
        # Filter outliers (95th percentile)
        distance_95th = np.percentile(all_distances, 95)
        mask = all_distances <= distance_95th
        filtered_angles = all_angles[mask]
        filtered_distances = all_distances[mask]
        
        print(f"  After 95th percentile filtering: {len(filtered_angles)} photons")
        print(f"  Distance cutoff: {distance_95th:.1f} mm")
        
        # Create 2D histogram
        angle_range = (filtered_angles.min(), filtered_angles.max())
        distance_range = (0, distance_95th)  # Start distance from 0
        
        histogram_2d, angle_edges, distance_edges = np.histogram2d(
            filtered_angles, filtered_distances,
            bins=[self.angle_bins, self.distance_bins],
            range=[angle_range, distance_range]
        )
        
        # Store table and metadata
        metadata = {
            'energy_mev': energy_mev,
            'angle_range': angle_range,
            'distance_range': distance_range,
            'angle_edges': angle_edges,
            'distance_edges': distance_edges,
            'angle_centers': (angle_edges[:-1] + angle_edges[1:]) / 2,
            'distance_centers': (distance_edges[:-1] + distance_edges[1:]) / 2,
            'total_photons': total_photons,
            'processed_photons': len(all_angles),
            'filtered_photons': len(filtered_angles),
            'max_bin_count': histogram_2d.max(),
            'non_zero_bins': np.count_nonzero(histogram_2d)
        }
        
        self.energy_tables[energy_mev] = histogram_2d
        self.energy_metadata[energy_mev] = metadata
        
        print(f"  2D table created: {self.angle_bins}x{self.distance_bins} bins")
        print(f"  Non-zero bins: {metadata['non_zero_bins']} ({100*metadata['non_zero_bins']/(self.angle_bins*self.distance_bins):.1f}%)")
        print(f"  Max bin count: {metadata['max_bin_count']}")
        
        return histogram_2d, metadata
    
    def create_3d_table_from_2d_stack(self):
        """Stack 2D tables to create 3D lookup table."""
        if not self.energy_tables:
            print("No 2D tables to stack!")
            return None
            
        energies = sorted(self.energy_tables.keys())
        print(f"\nStacking {len(energies)} 2D tables into 3D table...")
        print(f"Energy layers: {energies} MeV")
        
        # Use the angle/distance ranges from the first table as reference
        ref_metadata = self.energy_metadata[energies[0]]
        angle_edges = ref_metadata['angle_edges']
        distance_edges = ref_metadata['distance_edges']
        
        # Verify all tables have compatible dimensions
        for energy in energies:
            table = self.energy_tables[energy]
            if table.shape != (self.angle_bins, self.distance_bins):
                print(f"Warning: Table for {energy} MeV has incompatible shape: {table.shape}")
        
        # Create energy binning
        energy_bins = len(energies)
        energy_edges = np.array(energies + [energies[-1] + (energies[-1] - energies[-2])])
        energy_centers = np.array(energies)
        
        # Stack 2D tables into 3D array
        # Shape: (energy_bins, angle_bins, distance_bins)
        histogram_3d = np.zeros((energy_bins, self.angle_bins, self.distance_bins))
        
        for i, energy in enumerate(energies):
            histogram_3d[i] = self.energy_tables[energy]
        
        # Create 3D metadata
        metadata_3d = {
            'energy_bins': energy_bins,
            'angle_bins': self.angle_bins,
            'distance_bins': self.distance_bins,
            'histogram_shape': histogram_3d.shape,
            'energy_edges': energy_edges,
            'angle_edges': angle_edges,
            'distance_edges': distance_edges,
            'energy_centers': energy_centers,
            'angle_centers': ref_metadata['angle_centers'],
            'distance_centers': ref_metadata['distance_centers'],
            'energy_range': (energies[0], energies[-1]),
            'angle_range': ref_metadata['angle_range'],
            'distance_range': ref_metadata['distance_range'],
            'total_photons': sum(meta['total_photons'] for meta in self.energy_metadata.values()),
            'max_bin_count': histogram_3d.max(),
            'non_zero_bins': np.count_nonzero(histogram_3d),
            'coverage_percent': 100 * np.count_nonzero(histogram_3d) / histogram_3d.size
        }
        
        print(f"3D table created: {energy_bins}x{self.angle_bins}x{self.distance_bins} = {histogram_3d.size:,} bins")
        print(f"Total photons: {metadata_3d['total_photons']:,}")
        print(f"Non-zero bins: {metadata_3d['non_zero_bins']:,} ({metadata_3d['coverage_percent']:.1f}%)")
        print(f"Max bin count: {metadata_3d['max_bin_count']}")
        
        return histogram_3d, metadata_3d
    
    def save_3d_table(self, histogram_3d, metadata_3d):
        """Save 3D table and metadata to files."""
        # Save main 3D histogram
        table_path = self.output_dir / "photon_histogram_3d_discrete.npy"
        np.save(table_path, histogram_3d)
        
        # Save metadata
        metadata_path = self.output_dir / "table_metadata_discrete.npz"
        np.savez(metadata_path, **metadata_3d)
        
        # Save individual 2D tables for reference
        for energy, table_2d in self.energy_tables.items():
            table_2d_path = self.output_dir / f"photon_table_2d_{energy}MeV.npy"
            np.save(table_2d_path, table_2d)
        
        print(f"\nFiles saved:")
        print(f"  3D table: {table_path} ({histogram_3d.nbytes / 1024**2:.1f} MB)")
        print(f"  Metadata: {metadata_path}")
        print(f"  Individual 2D tables: {len(self.energy_tables)} files")
        
        return table_path, metadata_path
    
    def visualize_2d_tables(self):
        """Create visualization of individual 2D tables."""
        if not self.energy_tables:
            return
            
        n_energies = len(self.energy_tables)
        energies = sorted(self.energy_tables.keys())
        
        # Create subplots
        cols = min(3, n_energies)
        rows = (n_energies + cols - 1) // cols
        
        fig, axes = plt.subplots(rows, cols, figsize=(5*cols, 4*rows))
        if n_energies == 1:
            axes = [axes]
        elif rows == 1:
            axes = [axes]
        else:
            axes = axes.flatten()
        
        for i, energy in enumerate(energies):
            ax = axes[i] if i < len(axes) else None
            if ax is None:
                break
                
            table_2d = self.energy_tables[energy]
            metadata = self.energy_metadata[energy]
            
            # Plot 2D histogram
            im = ax.imshow(table_2d.T, origin='lower', aspect='auto', cmap='plasma')
            ax.set_title(f'{energy} MeV Muons\n{metadata["filtered_photons"]:,} photons')
            ax.set_xlabel('Angle Bin')
            ax.set_ylabel('Distance Bin')
            
            # Add colorbar
            plt.colorbar(im, ax=ax, label='Photon Count')
        
        # Hide extra subplots
        for i in range(n_energies, len(axes)):
            axes[i].set_visible(False)
        
        plt.tight_layout()
        
        # Save plot
        plot_path = self.output_dir / "discrete_2d_tables_analysis.png"
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        print(f"2D tables visualization saved: {plot_path}")
        plt.show()


def main():
    """Main function for creating discrete energy lookup table."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Create 3D photon table from discrete energy files')
    parser.add_argument('root_files', nargs='+', help='ROOT files with discrete energies')
    parser.add_argument('--energies', nargs='+', type=float, required=True,
                       help='Energy values (MeV) corresponding to ROOT files')
    parser.add_argument('--angle-bins', type=int, default=100,
                       help='Number of angle bins for 2D tables')
    parser.add_argument('--distance-bins', type=int, default=100,
                       help='Number of distance bins for 2D tables')
    parser.add_argument('--output', '-o', default='output',
                       help='Output directory')
    
    args = parser.parse_args()
    
    if len(args.root_files) != len(args.energies):
        print("Error: Number of ROOT files must match number of energies")
        return 1
    
    # Create table builder
    builder = DiscreteEnergyTableBuilder(args.output)
    builder.angle_bins = args.angle_bins
    builder.distance_bins = args.distance_bins
    
    # Process each ROOT file
    for root_file, energy in zip(args.root_files, args.energies):
        if not os.path.exists(root_file):
            print(f"Warning: ROOT file not found: {root_file}")
            continue
            
        result = builder.create_2d_table_from_file(root_file, energy)
        if result is None:
            print(f"Failed to process {root_file}")
    
    if not builder.energy_tables:
        print("No tables created successfully!")
        return 1
    
    # Create 3D table from 2D stack
    histogram_3d, metadata_3d = builder.create_3d_table_from_2d_stack()
    
    if histogram_3d is not None:
        # Save results
        builder.save_3d_table(histogram_3d, metadata_3d)
        
        # Create visualizations
        builder.visualize_2d_tables()
        
        print(f"\nDiscrete energy 3D lookup table created successfully!")
        print(f"Energies: {sorted(builder.energy_tables.keys())} MeV")
        print(f"Table shape: {histogram_3d.shape}")
        
    return 0


if __name__ == '__main__':
    sys.exit(main())