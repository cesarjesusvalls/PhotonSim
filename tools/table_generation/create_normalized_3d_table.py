#!/usr/bin/env python3
"""
Create a normalized 3D lookup table from 200-450 MeV ROOT files.
Normalizes 2D histograms by the number of events used to create them.
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import uproot
from pathlib import Path
import argparse
from tqdm import tqdm

class NormalizedPhotonTable3D:
    """3D table for normalized Cherenkov photon distributions."""
    
    def __init__(self, energy_min=200, energy_max=450, energy_step=10):
        """
        Initialize the normalized 3D table.
        
        Parameters:
        -----------
        energy_min : int
            Minimum energy in MeV
        energy_max : int  
            Maximum energy in MeV
        energy_step : int
            Energy step size in MeV
        """
        self.energy_min = energy_min
        self.energy_max = energy_max
        self.energy_step = energy_step
        
        # Use histogram bins (500x500)
        self.angle_bins = 500
        self.distance_bins = 500
        
        # Energy values
        self.energy_values = list(range(energy_min, energy_max + 1, energy_step))
        
        # Skip known bad files
        self.skip_energies = [460, 480]
        self.energy_values = [e for e in self.energy_values if e not in self.skip_energies]
        
        # Define bin ranges from histogram
        self.angle_range = (0, np.pi)  # 0 to pi radians
        self.distance_range = (0, 10000)  # 0 to 10000 mm
        
        # 3D histogram data
        self.photon_table = None
        self.normalized_table = None
        self.events_per_file = {}
        self.bin_edges = None
        self.bin_centers = None
        
    def process_single_file(self, root_file_path, energy):
        """Process a single ROOT file and extract normalized 2D histogram data."""
        try:
            with uproot.open(root_file_path) as file:
                # Get number of events from the tree
                n_events = 10000  # Default
                if "OpticalPhotons" in file:
                    tree = file["OpticalPhotons"]
                    n_events = tree.num_entries
                    print(f"  {energy} MeV: {n_events} events in file")
                
                self.events_per_file[energy] = n_events
                
                # Get the 2D histogram
                if "PhotonHist_AngleDistance" in file:
                    hist = file["PhotonHist_AngleDistance"]
                    counts = hist.values()
                    edges_x = hist.axes[0].edges()  # Angle edges
                    edges_y = hist.axes[1].edges()  # Distance edges
                    
                    # Normalize by number of events
                    normalized_counts = counts / n_events
                    
                    total_photons = counts.sum()
                    print(f"  Total photons: {total_photons:,.0f} ({total_photons/n_events:.1f} per event)")
                    
                    return normalized_counts, (edges_x, edges_y), counts
                else:
                    print(f"  WARNING: No PhotonHist_AngleDistance in {energy} MeV file")
                    return None, None, None
                    
        except Exception as e:
            print(f"  ERROR processing {energy} MeV: {e}")
            return None, None, None
    
    def create_3d_table(self, data_dir):
        """Create the normalized 3D table from ROOT files."""
        print(f"Creating normalized 3D lookup table for {self.energy_min}-{self.energy_max} MeV...")
        
        data_path = Path(data_dir)
        
        # Initialize 3D arrays
        n_energies = len(self.energy_values)
        self.photon_table = np.zeros((n_energies, self.angle_bins, self.distance_bins))
        self.normalized_table = np.zeros((n_energies, self.angle_bins, self.distance_bins))
        
        # Process each file
        print("\nProcessing files:")
        for idx, energy in enumerate(tqdm(self.energy_values)):
            file_path = data_path / f"{energy}MeV" / "output.root"
            
            if not file_path.exists():
                print(f"\n  WARNING: File not found for {energy} MeV")
                continue
            
            normalized_counts, edges, raw_counts = self.process_single_file(file_path, energy)
            
            if normalized_counts is None:
                continue
            
            # Store in 3D arrays
            self.normalized_table[idx] = normalized_counts
            self.photon_table[idx] = raw_counts
            
            # Store bin edges from first file
            if idx == 0:
                self.bin_edges = (
                    np.array(self.energy_values),
                    edges[0],  # angle edges
                    edges[1]   # distance edges
                )
        
        # Calculate bin centers
        self.bin_centers = (
            np.array(self.energy_values),
            (self.bin_edges[1][:-1] + self.bin_edges[1][1:]) / 2,
            (self.bin_edges[2][:-1] + self.bin_edges[2][1:]) / 2
        )
        
        print(f"\n3D table created successfully!")
        print(f"Energy range: {self.energy_values[0]}-{self.energy_values[-1]} MeV ({len(self.energy_values)} energies)")
        print(f"Shape: {self.normalized_table.shape}")
        print(f"Total photons: {self.photon_table.sum():,.0f}")
        print(f"Average photons per event: {self.photon_table.sum() / sum(self.events_per_file.values()):.1f}")
        
    def save_table(self, output_path):
        """Save the normalized 3D table to files."""
        output_path = Path(output_path)
        output_path.mkdir(exist_ok=True, parents=True)
        
        # Save both normalized and raw tables
        np.save(output_path / "photon_table_3d_normalized.npy", self.normalized_table)
        np.save(output_path / "photon_table_3d_raw.npy", self.photon_table)
        
        # Save metadata
        metadata = {
            'energy_values': self.energy_values,
            'energy_min': self.energy_min,
            'energy_max': self.energy_max,
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
            'table_shape': self.normalized_table.shape,
            'total_photons': self.photon_table.sum(),
            'events_per_file': dict(self.events_per_file),
            'normalization': 'per_event'
        }
        
        np.savez(output_path / "table_metadata_normalized.npz", **metadata)
        
        print(f"\n3D table saved to {output_path}")
        print(f"  - photon_table_3d_normalized.npy: Normalized table (photons per event)")
        print(f"  - photon_table_3d_raw.npy: Raw photon counts")
        print(f"  - table_metadata_normalized.npz: Metadata and bin information")
    
    def visualize_table(self, output_path=None):
        """Create visualizations of the normalized 3D table."""
        if self.normalized_table is None:
            print("No data to visualize. Run create_3d_table first.")
            return
        
        print("\nCreating visualizations...")
        
        # Figure 1: Overview
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        
        # 1. Energy scaling (photons per event)
        ax = axes[0, 0]
        photons_per_event = []
        for i, energy in enumerate(self.energy_values):
            if energy in self.events_per_file:
                total = self.photon_table[i].sum()
                n_events = self.events_per_file[energy]
                photons_per_event.append(total / n_events)
            else:
                photons_per_event.append(0)
        
        ax.plot(self.energy_values, photons_per_event, 'b-', linewidth=2, marker='o')
        ax.set_xlabel('Energy (MeV)')
        ax.set_ylabel('Photons per Event')
        ax.set_title('Photon Production per Event vs Energy')
        ax.grid(True, alpha=0.3)
        
        # 2-4. Sample normalized 2D slices
        sample_energies = [200, 300, 400]
        for i, energy in enumerate(sample_energies):
            ax = axes[0, i+1] if i < 2 else axes[1, 0]
            
            idx = self.energy_values.index(energy)
            slice_2d = self.normalized_table[idx]
            
            # Convert to photons per event per bin
            im = ax.imshow(slice_2d.T, origin='lower', aspect='auto', cmap='viridis',
                          extent=[0, np.degrees(self.bin_edges[1][-1]), 
                                 0, self.bin_edges[2][-1]],
                          interpolation='nearest')
            
            ax.set_xlabel('Opening Angle (degrees)')
            ax.set_ylabel('Distance (mm)')
            ax.set_title(f'{energy} MeV (normalized)')
            ax.set_xlim(0, 90)
            ax.set_ylim(0, 3000)
            
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label('Photons/event/bin', rotation=270, labelpad=15)
            
            # Mark Cherenkov angle
            ax.axvline(43, color='red', linestyle='--', alpha=0.7, linewidth=1)
        
        # 5. Angle distribution comparison (normalized)
        ax = axes[1, 1]
        for energy in [200, 300, 400]:
            idx = self.energy_values.index(energy)
            angle_projection = self.normalized_table[idx].sum(axis=1)
            angle_degrees = np.degrees(self.bin_centers[1])
            ax.plot(angle_degrees, angle_projection, linewidth=2, label=f'{energy} MeV')
        
        ax.set_xlabel('Opening Angle (degrees)')
        ax.set_ylabel('Photons per Event (summed over distance)')
        ax.set_title('Normalized Angular Distribution')
        ax.set_xlim(0, 90)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 6. Statistics
        ax = axes[1, 2]
        ax.axis('off')
        stats_text = f"""Normalized 3D Table Statistics:
        
Energy range: {self.energy_min}-{self.energy_max} MeV
Valid energies: {len(self.energy_values)}
Skipped: {self.skip_energies}

Table dimensions: {self.normalized_table.shape}
Angle bins: {self.angle_bins} (0-180°)
Distance bins: {self.distance_bins} (0-10m)

Total events processed: {sum(self.events_per_file.values()):,}
Total photons: {self.photon_table.sum():,.0f}
Avg photons/event: {self.photon_table.sum()/sum(self.events_per_file.values()):.1f}

Normalization: per event basis
Each bin value = photons/event"""
        
        ax.text(0.1, 0.9, stats_text, transform=ax.transAxes,
                fontsize=10, family='monospace', verticalalignment='top')
        
        plt.suptitle('Normalized 3D Photon Lookup Table', fontsize=16)
        plt.tight_layout()
        
        if output_path:
            output_path = Path(output_path)
            plt.savefig(output_path / "normalized_3d_table_visualization.png", 
                       dpi=150, bbox_inches='tight')
            print(f"Visualizations saved to {output_path}")
        
        plt.show()


def main():
    parser = argparse.ArgumentParser(
        description='Create normalized 3D photon lookup table from ROOT files')
    parser.add_argument('--data-dir', '-d', 
                       default='data/mu-',
                       help='Directory containing energy subdirectories with ROOT files')
    parser.add_argument('--output', '-o', 
                       default='output/3d_lookup_table_normalized',
                       help='Output directory for table and visualizations')
    parser.add_argument('--energy-min', type=int, default=200,
                       help='Minimum energy in MeV')
    parser.add_argument('--energy-max', type=int, default=450,
                       help='Maximum energy in MeV')
    parser.add_argument('--energy-step', type=int, default=10,
                       help='Energy step size in MeV')
    parser.add_argument('--visualize', action='store_true',
                       help='Create visualizations after building table')
    
    args = parser.parse_args()
    
    # Create table builder
    table_builder = NormalizedPhotonTable3D(
        energy_min=args.energy_min,
        energy_max=args.energy_max,
        energy_step=args.energy_step
    )
    
    # Build the 3D table
    table_builder.create_3d_table(args.data_dir)
    
    # Save the table
    table_builder.save_table(args.output)
    
    # Create visualizations if requested
    if args.visualize:
        table_builder.visualize_table(args.output)
    
    print("\nDone! Normalized 3D lookup table created successfully.")


if __name__ == "__main__":
    main()