#!/usr/bin/env python3
"""
Advanced visualization of 2D ROOT histograms from PhotonSim.
Creates comprehensive plots with physics insights and statistics.
"""

import numpy as np
import matplotlib.pyplot as plt
import uproot
import sys
from pathlib import Path

class PhotonSimVisualizer:
    def __init__(self, root_file):
        self.root_file = Path(root_file)
        if not self.root_file.exists():
            raise FileNotFoundError(f"ROOT file not found: {root_file}")
        
        self.photon_data = None
        self.edep_data = None
        self.tree_data = None
        
        self._load_data()
    
    def _load_data(self):
        """Load all data from ROOT file."""
        with uproot.open(self.root_file) as file:
            print(f"Loading data from: {self.root_file}")
            print(f"Available objects: {list(file.keys())}")
            
            # Load histograms
            if "PhotonHist_AngleDistance" in file:
                hist = file["PhotonHist_AngleDistance"]
                self.photon_data = {
                    'values': hist.values(),
                    'angle_edges': hist.axes[0].edges,
                    'distance_edges': hist.axes[1].edges,
                    'title': hist.title,
                    'x_label': hist.axes[0].label,
                    'y_label': hist.axes[1].label
                }
                print(f"✓ Loaded photon histogram: {self.photon_data['values'].sum():,.0f} entries")
            
            if "EdepHist_DistanceEnergy" in file:
                hist = file["EdepHist_DistanceEnergy"]
                self.edep_data = {
                    'values': hist.values(),
                    'distance_edges': hist.axes[0].edges,
                    'energy_edges': hist.axes[1].edges,
                    'title': hist.title,
                    'x_label': hist.axes[0].label,
                    'y_label': hist.axes[1].label
                }
                print(f"✓ Loaded energy deposit histogram: {self.edep_data['values'].sum():,.0f} entries")
            
            # Load basic tree info
            if "OpticalPhotons" in file:
                tree = file["OpticalPhotons"]
                try:
                    self.tree_data = tree.arrays(['EventID', 'PrimaryEnergy', 'NOpticalPhotons', 'NEnergyDeposits'], library='np')
                    print(f"✓ Loaded tree data: {tree.num_entries} events")
                except:
                    print("⚠ Could not load tree data")
    
    def plot_photon_histogram(self, log_scale=False, save_path=None):
        """Create comprehensive photon histogram visualization."""
        if self.photon_data is None:
            print("No photon histogram data available")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        values = self.photon_data['values']
        angle_edges = self.photon_data['angle_edges']
        distance_edges = self.photon_data['distance_edges']
        
        # Convert edges to centers for analysis
        angle_centers = (angle_edges[:-1] + angle_edges[1:]) / 2
        distance_centers = (distance_edges[:-1] + distance_edges[1:]) / 2
        
        # Main 2D histogram
        ax1 = axes[0, 0]
        extent = [angle_edges[0], angle_edges[-1], distance_edges[0], distance_edges[-1]]
        
        if log_scale and values.max() > 0:
            # Use log scale with small offset to handle zeros
            plot_values = np.log10(values + 1)
            im1 = ax1.imshow(plot_values.T, origin='lower', aspect='auto', 
                           extent=extent, cmap='plasma')
            cbar1 = plt.colorbar(im1, ax=ax1)
            cbar1.set_label('log₁₀(Photon Count + 1)')
        else:
            im1 = ax1.imshow(values.T, origin='lower', aspect='auto', 
                           extent=extent, cmap='plasma')
            cbar1 = plt.colorbar(im1, ax=ax1)
            cbar1.set_label('Photon Count')
        
        ax1.set_xlabel('Opening Angle (rad)')
        ax1.set_ylabel('Distance (mm)')
        ax1.set_title(f'Photon Distribution: Angle vs Distance\n{values.sum():,.0f} total photons')
        
        # Mark Cherenkov angle range (typical: ~0.7-0.8 rad for water)
        ax1.axvline(0.7, color='white', linestyle='--', alpha=0.7, label='Typical Čerenkov')
        ax1.axvline(0.8, color='white', linestyle='--', alpha=0.7)
        ax1.legend()
        
        # Angle projection
        ax2 = axes[0, 1]
        angle_projection = values.sum(axis=1)  # Sum over distance
        ax2.plot(angle_centers, angle_projection, 'b-', linewidth=2)
        ax2.fill_between(angle_centers, angle_projection, alpha=0.3)
        ax2.set_xlabel('Opening Angle (rad)')
        ax2.set_ylabel('Photon Count')
        ax2.set_title('Angular Distribution')
        ax2.grid(True, alpha=0.3)
        
        # Mark peak angle
        peak_idx = np.argmax(angle_projection)
        peak_angle = angle_centers[peak_idx]
        ax2.axvline(peak_angle, color='red', linestyle='--', 
                   label=f'Peak: {peak_angle:.3f} rad ({np.degrees(peak_angle):.1f}°)')
        ax2.legend()
        
        # Distance projection
        ax3 = axes[1, 0]
        distance_projection = values.sum(axis=0)  # Sum over angle
        ax3.plot(distance_centers, distance_projection, 'g-', linewidth=2)
        ax3.fill_between(distance_centers, distance_projection, alpha=0.3)
        ax3.set_xlabel('Distance (mm)')
        ax3.set_ylabel('Photon Count')
        ax3.set_title('Radial Distribution')
        ax3.grid(True, alpha=0.3)
        
        # Mark average distance
        avg_distance = np.average(distance_centers, weights=distance_projection)
        ax3.axvline(avg_distance, color='red', linestyle='--', 
                   label=f'Average: {avg_distance:.0f} mm')
        ax3.legend()
        
        # Statistics panel
        ax4 = axes[1, 1]
        ax4.axis('off')
        
        # Calculate statistics
        non_zero_bins = np.count_nonzero(values)
        total_bins = values.size
        coverage = 100 * non_zero_bins / total_bins
        max_count = values.max()
        
        stats_text = f"""
PHOTON HISTOGRAM STATISTICS

Total Photons: {values.sum():,.0f}
Histogram Size: {values.shape[0]} × {values.shape[1]} = {total_bins:,} bins

Coverage:
• Non-zero bins: {non_zero_bins:,} ({coverage:.1f}%)
• Max bin count: {max_count:,.0f}

Angular Analysis:
• Range: {angle_edges[0]:.3f} - {angle_edges[-1]:.3f} rad
• Peak angle: {peak_angle:.3f} rad ({np.degrees(peak_angle):.1f}°)
• Bin resolution: {(angle_edges[1] - angle_edges[0]):.4f} rad

Distance Analysis:
• Range: {distance_edges[0]:.0f} - {distance_edges[-1]:.0f} mm
• Average: {avg_distance:.0f} mm
• Bin resolution: {(distance_edges[1] - distance_edges[0]):.1f} mm

Physics Notes:
• Čerenkov angle in water: ~41-46° (0.7-0.8 rad)
• Peak at {np.degrees(peak_angle):.1f}° indicates {'water-like' if 40 <= np.degrees(peak_angle) <= 50 else 'non-water'} medium
        """
        
        ax4.text(0.05, 0.95, stats_text, transform=ax4.transAxes, 
                fontsize=10, verticalalignment='top', fontfamily='monospace')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Photon histogram saved: {save_path}")
        
        plt.show()
    
    def plot_energy_deposit_histogram(self, log_scale=False, save_path=None):
        """Create comprehensive energy deposit histogram visualization."""
        if self.edep_data is None:
            print("No energy deposit histogram data available")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        values = self.edep_data['values']
        distance_edges = self.edep_data['distance_edges']
        energy_edges = self.edep_data['energy_edges']
        
        # Convert edges to centers
        distance_centers = (distance_edges[:-1] + distance_edges[1:]) / 2
        energy_centers = (energy_edges[:-1] + energy_edges[1:]) / 2
        
        # Main 2D histogram
        ax1 = axes[0, 0]
        extent = [distance_edges[0], distance_edges[-1], energy_edges[0], energy_edges[-1]]
        
        if log_scale and values.max() > 0:
            plot_values = np.log10(values + 1)
            im1 = ax1.imshow(plot_values.T, origin='lower', aspect='auto', 
                           extent=extent, cmap='viridis')
            cbar1 = plt.colorbar(im1, ax=ax1)
            cbar1.set_label('log₁₀(Deposit Count + 1)')
        else:
            im1 = ax1.imshow(values.T, origin='lower', aspect='auto', 
                           extent=extent, cmap='viridis')
            cbar1 = plt.colorbar(im1, ax=ax1)
            cbar1.set_label('Deposit Count')
        
        ax1.set_xlabel('Distance (mm)')
        ax1.set_ylabel('Energy Deposit (keV)')
        ax1.set_title(f'Energy Deposits: Distance vs Energy\n{values.sum():,.0f} total deposits')
        
        # Distance projection
        ax2 = axes[0, 1]
        distance_projection = values.sum(axis=1)  # Sum over energy
        ax2.plot(distance_centers, distance_projection, 'b-', linewidth=2)
        ax2.fill_between(distance_centers, distance_projection, alpha=0.3)
        ax2.set_xlabel('Distance (mm)')
        ax2.set_ylabel('Deposit Count')
        ax2.set_title('Spatial Distribution of Deposits')
        ax2.grid(True, alpha=0.3)
        
        # Energy projection
        ax3 = axes[1, 0]
        energy_projection = values.sum(axis=0)  # Sum over distance
        ax3.plot(energy_centers, energy_projection, 'r-', linewidth=2)
        ax3.fill_between(energy_centers, energy_projection, alpha=0.3)
        ax3.set_xlabel('Energy Deposit (keV)')
        ax3.set_ylabel('Deposit Count')
        ax3.set_title('Energy Distribution')
        ax3.grid(True, alpha=0.3)
        
        # Calculate and mark average energy
        total_energy = np.sum(values * energy_centers[:, np.newaxis].T)
        total_count = values.sum()
        avg_energy = total_energy / total_count if total_count > 0 else 0
        ax3.axvline(avg_energy, color='red', linestyle='--', 
                   label=f'Average: {avg_energy:.1f} keV')
        ax3.legend()
        
        # Statistics panel
        ax4 = axes[1, 1]
        ax4.axis('off')
        
        # Calculate statistics
        non_zero_bins = np.count_nonzero(values)
        total_bins = values.size
        coverage = 100 * non_zero_bins / total_bins
        max_count = values.max()
        
        # Energy percentiles
        energy_cumsum = np.cumsum(energy_projection)
        total_deposits = energy_cumsum[-1]
        
        energy_50_idx = np.searchsorted(energy_cumsum, 0.5 * total_deposits)
        energy_90_idx = np.searchsorted(energy_cumsum, 0.9 * total_deposits)
        energy_95_idx = np.searchsorted(energy_cumsum, 0.95 * total_deposits)
        
        energy_50 = energy_centers[min(energy_50_idx, len(energy_centers)-1)]
        energy_90 = energy_centers[min(energy_90_idx, len(energy_centers)-1)]
        energy_95 = energy_centers[min(energy_95_idx, len(energy_centers)-1)]
        
        stats_text = f"""
ENERGY DEPOSIT STATISTICS

Total Deposits: {values.sum():,.0f}
Total Energy: {total_energy:,.1f} keV
Histogram Size: {values.shape[0]} × {values.shape[1]} = {total_bins:,} bins

Coverage:
• Non-zero bins: {non_zero_bins:,} ({coverage:.1f}%)
• Max bin count: {max_count:,.0f}

Energy Analysis:
• Range: {energy_edges[0]:.1f} - {energy_edges[-1]:.1f} keV
• Average: {avg_energy:.1f} keV
• Median (50%): {energy_50:.1f} keV
• 90th percentile: {energy_90:.1f} keV
• 95th percentile: {energy_95:.1f} keV
• Bin resolution: {(energy_edges[1] - energy_edges[0]):.1f} keV

Distance Analysis:
• Range: {distance_edges[0]:.0f} - {distance_edges[-1]:.0f} mm
• Bin resolution: {(distance_edges[1] - distance_edges[0]):.1f} mm

Physics Notes:
• Primary ionization from muon track
• Secondary electron energy deposits
• {'Range may need extension' if energy_95 > 900 else 'Good energy range coverage'}
        """
        
        ax4.text(0.05, 0.95, stats_text, transform=ax4.transAxes, 
                fontsize=10, verticalalignment='top', fontfamily='monospace')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Energy deposit histogram saved: {save_path}")
        
        plt.show()
    
    def plot_comparison_overview(self, save_path=None):
        """Create side-by-side comparison of both histograms."""
        if self.photon_data is None or self.edep_data is None:
            print("Need both photon and energy deposit data for comparison")
            return
        
        fig, axes = plt.subplots(1, 2, figsize=(20, 8))
        
        # Photon histogram
        ax1 = axes[0]
        values1 = self.photon_data['values']
        extent1 = [self.photon_data['angle_edges'][0], self.photon_data['angle_edges'][-1],
                  self.photon_data['distance_edges'][0], self.photon_data['distance_edges'][-1]]
        
        im1 = ax1.imshow(values1.T, origin='lower', aspect='auto', extent=extent1, cmap='plasma')
        cbar1 = plt.colorbar(im1, ax=ax1, fraction=0.046, pad=0.04)
        cbar1.set_label('Photon Count')
        
        ax1.set_xlabel('Opening Angle (rad)')
        ax1.set_ylabel('Distance (mm)')
        ax1.set_title(f'Cherenkov Photons\n{values1.sum():,.0f} photons, {np.count_nonzero(values1):,} bins')
        
        # Energy deposit histogram
        ax2 = axes[1]
        values2 = self.edep_data['values']
        extent2 = [self.edep_data['distance_edges'][0], self.edep_data['distance_edges'][-1],
                  self.edep_data['energy_edges'][0], self.edep_data['energy_edges'][-1]]
        
        im2 = ax2.imshow(values2.T, origin='lower', aspect='auto', extent=extent2, cmap='viridis')
        cbar2 = plt.colorbar(im2, ax=ax2, fraction=0.046, pad=0.04)
        cbar2.set_label('Deposit Count')
        
        ax2.set_xlabel('Distance (mm)')
        ax2.set_ylabel('Energy Deposit (keV)')
        ax2.set_title(f'Energy Deposits\n{values2.sum():,.0f} deposits, {np.count_nonzero(values2):,} bins')
        
        # Add run info if available
        if self.tree_data is not None:
            run_info = f"Run: {len(self.tree_data['EventID'])} events"
            if len(np.unique(self.tree_data['PrimaryEnergy'])) == 1:
                energy = self.tree_data['PrimaryEnergy'][0]
                run_info += f", {energy:.0f} MeV muons"
            fig.suptitle(f'PhotonSim 2D Histogram Analysis - {run_info}', fontsize=16, y=0.95)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Comparison plot saved: {save_path}")
        
        plt.show()
    
    def create_all_plots(self, output_dir="visualizations", log_scale=False):
        """Generate all visualization plots."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        print(f"Creating all plots in {output_path}/")
        
        # Individual detailed plots
        if self.photon_data is not None:
            log_suffix = "_log" if log_scale else ""
            self.plot_photon_histogram(log_scale=log_scale, 
                                     save_path=output_path / f"photon_analysis{log_suffix}.png")
        
        if self.edep_data is not None:
            log_suffix = "_log" if log_scale else ""
            self.plot_energy_deposit_histogram(log_scale=log_scale,
                                             save_path=output_path / f"energy_analysis{log_suffix}.png")
        
        # Comparison overview
        self.plot_comparison_overview(save_path=output_path / "histogram_comparison.png")
        
        print(f"All plots created in {output_path}/")


def main():
    """Main visualization function."""
    if len(sys.argv) < 2:
        print("Usage: python visualize_2d_tables.py <root_file> [--log] [--output-dir <dir>]")
        print("Example: python visualize_2d_tables.py optical_photons.root --log --output-dir plots")
        return 1
    
    root_file = sys.argv[1]
    log_scale = "--log" in sys.argv
    
    # Parse output directory
    output_dir = "visualizations"
    if "--output-dir" in sys.argv:
        idx = sys.argv.index("--output-dir")
        if idx + 1 < len(sys.argv):
            output_dir = sys.argv[idx + 1]
    
    try:
        viz = PhotonSimVisualizer(root_file)
        viz.create_all_plots(output_dir=output_dir, log_scale=log_scale)
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())