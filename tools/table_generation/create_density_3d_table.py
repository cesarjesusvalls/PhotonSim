#!/usr/bin/env python3
"""
Create a normalized density 3D lookup table from 200-450 MeV ROOT files.
Normalizes 2D histograms by:
1. Number of events
2. Bin area (solid angle × distance bin width)
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import uproot
from pathlib import Path
import argparse
from tqdm import tqdm

class DensityPhotonTable3D:
    """3D table for normalized Cherenkov photon density distributions."""
    
    def __init__(self, energy_min=200, energy_max=450, energy_step=10):
        """
        Initialize the density 3D table.
        
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
        self.density_table = None
        self.events_per_file = {}
        self.bin_edges = None
        self.bin_centers = None
        self.bin_areas = None
        
    def calculate_bin_areas(self):
        """Calculate the area of each bin in angle-distance space."""
        # Get bin edges
        angle_edges = self.bin_edges[1]  # radians
        distance_edges = self.bin_edges[2]  # mm
        
        # Calculate bin widths
        d_angle = angle_edges[1:] - angle_edges[:-1]  # radians
        d_distance = distance_edges[1:] - distance_edges[:-1]  # mm
        
        # Create 2D arrays for bin areas
        # For each angle bin, we need the solid angle element
        # In spherical coordinates: dΩ = sin(θ) dθ dφ
        # For azimuthal symmetry: dΩ = 2π sin(θ) dθ
        
        # Use bin centers for sin(theta)
        angle_centers = self.bin_centers[1]
        
        # Solid angle element for each angle bin (steradians)
        solid_angle_elements = 2 * np.pi * np.sin(angle_centers) * d_angle
        
        # Create 2D array of bin areas
        # Each bin area = solid angle × distance bin width
        self.bin_areas = np.outer(solid_angle_elements, d_distance)
        
        print(f"\nBin area calculation:")
        print(f"  Angle bins: {len(d_angle)}")
        print(f"  Distance bins: {len(d_distance)}")
        print(f"  Min solid angle element: {solid_angle_elements.min():.6f} sr")
        print(f"  Max solid angle element: {solid_angle_elements.max():.6f} sr")
        print(f"  Min bin area: {self.bin_areas.min():.2f} sr·mm")
        print(f"  Max bin area: {self.bin_areas.max():.2f} sr·mm")
        
    def process_single_file(self, root_file_path, energy):
        """Process a single ROOT file and extract density-normalized 2D histogram data."""
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
                    
                    # Store raw counts
                    total_photons = counts.sum()
                    print(f"  Total photons: {total_photons:,.0f} ({total_photons/n_events:.1f} per event)")
                    
                    return counts, (edges_x, edges_y)
                else:
                    print(f"  WARNING: No PhotonHist_AngleDistance in {energy} MeV file")
                    return None, None
                    
        except Exception as e:
            print(f"  ERROR processing {energy} MeV: {e}")
            return None, None
    
    def create_3d_table(self, data_dir):
        """Create the density-normalized 3D table from ROOT files."""
        print(f"Creating density-normalized 3D lookup table for {self.energy_min}-{self.energy_max} MeV...")
        
        data_path = Path(data_dir)
        
        # Initialize 3D arrays
        n_energies = len(self.energy_values)
        self.photon_table = np.zeros((n_energies, self.angle_bins, self.distance_bins))
        self.normalized_table = np.zeros((n_energies, self.angle_bins, self.distance_bins))
        self.density_table = np.zeros((n_energies, self.angle_bins, self.distance_bins))
        
        # Process each file
        print("\nProcessing files:")
        for idx, energy in enumerate(tqdm(self.energy_values)):
            file_path = data_path / f"{energy}MeV" / "output.root"
            
            if not file_path.exists():
                print(f"\n  WARNING: File not found for {energy} MeV")
                continue
            
            raw_counts, edges = self.process_single_file(file_path, energy)
            
            if raw_counts is None:
                continue
            
            # Store raw counts
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
                
                # Calculate bin areas
                self.calculate_bin_areas()
            
            # Normalize by events
            n_events = self.events_per_file[energy]
            self.normalized_table[idx] = raw_counts / n_events
            
            # Calculate density (photons per event per unit solid angle per unit distance)
            # Avoid division by zero for small bin areas
            with np.errstate(divide='ignore', invalid='ignore'):
                self.density_table[idx] = self.normalized_table[idx] / self.bin_areas
                self.density_table[idx][self.bin_areas < 1e-10] = 0
        
        print(f"\n3D density table created successfully!")
        print(f"Energy range: {self.energy_values[0]}-{self.energy_values[-1]} MeV ({len(self.energy_values)} energies)")
        print(f"Shape: {self.density_table.shape}")
        print(f"Total photons: {self.photon_table.sum():,.0f}")
        print(f"Average photons per event: {self.photon_table.sum() / sum(self.events_per_file.values()):.1f}")
        
    def save_table(self, output_path):
        """Save the density 3D table to files."""
        output_path = Path(output_path)
        output_path.mkdir(exist_ok=True, parents=True)
        
        # Save all three versions
        np.save(output_path / "photon_table_3d_raw.npy", self.photon_table)
        np.save(output_path / "photon_table_3d_normalized.npy", self.normalized_table)
        np.save(output_path / "photon_table_3d_density.npy", self.density_table)
        
        # Save bin areas
        np.save(output_path / "bin_areas.npy", self.bin_areas)
        
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
            'table_shape': self.density_table.shape,
            'total_photons': self.photon_table.sum(),
            'events_per_file': dict(self.events_per_file),
            'normalization': 'density',
            'density_units': 'photons/(event·sr·mm)'
        }
        
        np.savez(output_path / "table_metadata_density.npz", **metadata)
        
        print(f"\n3D table saved to {output_path}")
        print(f"  - photon_table_3d_raw.npy: Raw photon counts")
        print(f"  - photon_table_3d_normalized.npy: Photons per event")
        print(f"  - photon_table_3d_density.npy: Photon density (photons/event/sr/mm)")
        print(f"  - bin_areas.npy: Bin areas in sr·mm")
        print(f"  - table_metadata_density.npz: Metadata and bin information")
    
    def visualize_table(self, output_path=None):
        """Create visualizations of the density 3D table."""
        if self.density_table is None:
            print("No data to visualize. Run create_3d_table first.")
            return
        
        print("\nCreating visualizations...")
        
        # Figure 1: Density visualizations
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
        
        # 2-4. Sample density 2D slices
        sample_energies = [200, 300, 400]
        for i, energy in enumerate(sample_energies):
            ax = axes[0, i+1] if i < 2 else axes[1, 0]
            
            idx = self.energy_values.index(energy)
            slice_2d = self.density_table[idx]
            
            # Use log scale for better visualization
            with np.errstate(divide='ignore'):
                log_slice = np.log10(slice_2d + 1e-10)  # Add small value to avoid log(0)
            
            im = ax.imshow(log_slice.T, origin='lower', aspect='auto', cmap='viridis',
                          extent=[0, np.degrees(self.bin_edges[1][-1]), 
                                 0, self.bin_edges[2][-1]],
                          interpolation='nearest')
            
            ax.set_xlabel('Opening Angle (degrees)')
            ax.set_ylabel('Distance (mm)')
            ax.set_title(f'{energy} MeV (log₁₀ density)')
            ax.set_xlim(0, 90)
            ax.set_ylim(0, 3000)
            
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label('log₁₀(photons/event/sr/mm)', rotation=270, labelpad=20)
            
            # Mark Cherenkov angle
            ax.axvline(43, color='red', linestyle='--', alpha=0.7, linewidth=1)
        
        # 5. Integrated angular density (accounting for solid angle)
        ax = axes[1, 1]
        for energy in [200, 300, 400]:
            idx = self.energy_values.index(energy)
            # Integrate over distance, density already includes solid angle normalization
            angular_density = self.density_table[idx].sum(axis=1) * np.diff(self.bin_edges[2]).mean()
            angle_degrees = np.degrees(self.bin_centers[1])
            ax.plot(angle_degrees, angular_density, linewidth=2, label=f'{energy} MeV')
        
        ax.set_xlabel('Opening Angle (degrees)')
        ax.set_ylabel('Photons per Event per Steradian')
        ax.set_title('Angular Photon Density (integrated over distance)')
        ax.set_xlim(0, 90)
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_yscale('log')
        
        # 6. Statistics
        ax = axes[1, 2]
        ax.axis('off')
        stats_text = f"""Density 3D Table Statistics:
        
Energy range: {self.energy_min}-{self.energy_max} MeV
Valid energies: {len(self.energy_values)}
Skipped: {self.skip_energies}

Table dimensions: {self.density_table.shape}
Angle bins: {self.angle_bins} (0-180°)
Distance bins: {self.distance_bins} (0-10m)

Total events: {sum(self.events_per_file.values()):,}
Total photons: {self.photon_table.sum():,.0f}
Avg photons/event: {self.photon_table.sum()/sum(self.events_per_file.values()):.1f}

Normalization: density basis
Units: photons/(event·sr·mm)
Bin areas: {self.bin_areas.min():.2f} - {self.bin_areas.max():.2f} sr·mm"""
        
        ax.text(0.1, 0.9, stats_text, transform=ax.transAxes,
                fontsize=10, family='monospace', verticalalignment='top')
        
        plt.suptitle('Density-Normalized 3D Photon Lookup Table', fontsize=16)
        plt.tight_layout()
        
        if output_path:
            output_path = Path(output_path)
            plt.savefig(output_path / "density_3d_table_visualization.png", 
                       dpi=150, bbox_inches='tight')
            print(f"Visualizations saved to {output_path}")
        
        plt.show()


def main():
    parser = argparse.ArgumentParser(
        description='Create density-normalized 3D photon lookup table from ROOT files')
    parser.add_argument('--data-dir', '-d', 
                       default='data/mu-',
                       help='Directory containing energy subdirectories with ROOT files')
    parser.add_argument('--output', '-o', 
                       default='output/3d_lookup_table_density',
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
    table_builder = DensityPhotonTable3D(
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
    
    print("\nDone! Density-normalized 3D lookup table created successfully.")


if __name__ == "__main__":
    main()