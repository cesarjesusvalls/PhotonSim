#!/usr/bin/env python3
"""
Analyze 2D ROOT histograms from PhotonSim for efficient lookup table creation.
Reads the PhotonHist_AngleDistance and EdepHist_DistanceEnergy histograms.
"""

import numpy as np
import matplotlib.pyplot as plt
import uproot
import sys
from pathlib import Path

def analyze_photon_histogram(hist_data, title_prefix=""):
    """Analyze the photon angle vs distance histogram."""
    # Get histogram content and edges
    values = hist_data.values()
    x_edges = hist_data.axes[0].edges  # Angle edges (rad)
    y_edges = hist_data.axes[1].edges  # Distance edges (mm)
    
    print(f"\n{title_prefix}Photon Histogram Analysis:")
    print(f"  Shape: {values.shape}")
    print(f"  Total entries: {values.sum():,.0f}")
    print(f"  Non-zero bins: {np.count_nonzero(values):,} ({100*np.count_nonzero(values)/values.size:.1f}%)")
    print(f"  Max bin count: {values.max():,.0f}")
    print(f"  Angle range: {x_edges[0]:.3f} - {x_edges[-1]:.3f} rad")
    print(f"  Distance range: {y_edges[0]:.0f} - {y_edges[-1]:.0f} mm")
    
    # Calculate angle centers for analysis
    angle_centers = (x_edges[:-1] + x_edges[1:]) / 2
    distance_centers = (y_edges[:-1] + y_edges[1:]) / 2
    
    # Find typical Cherenkov angle peak
    angle_sums = values.sum(axis=1)  # Sum over distance for each angle
    peak_angle_idx = np.argmax(angle_sums)
    peak_angle = angle_centers[peak_angle_idx]
    
    print(f"  Peak Cherenkov angle: {peak_angle:.3f} rad ({np.degrees(peak_angle):.1f}°)")
    
    # Statistics by distance
    distance_sums = values.sum(axis=0)  # Sum over angle for each distance
    avg_distance = np.average(distance_centers, weights=distance_sums)
    print(f"  Average photon distance: {avg_distance:.0f} mm")
    
    return {
        'values': values,
        'angle_edges': x_edges,
        'distance_edges': y_edges,
        'angle_centers': angle_centers,
        'distance_centers': distance_centers,
        'total_entries': values.sum(),
        'peak_angle': peak_angle,
        'avg_distance': avg_distance
    }

def analyze_edep_histogram(hist_data, title_prefix=""):
    """Analyze the energy deposit vs distance histogram."""
    # Get histogram content and edges
    values = hist_data.values()
    x_edges = hist_data.axes[0].edges  # Distance edges (mm)
    y_edges = hist_data.axes[1].edges  # Energy edges (keV)
    
    print(f"\n{title_prefix}Energy Deposit Histogram Analysis:")
    print(f"  Shape: {values.shape}")
    print(f"  Total entries: {values.sum():,.0f}")
    print(f"  Non-zero bins: {np.count_nonzero(values):,} ({100*np.count_nonzero(values)/values.size:.1f}%)")
    print(f"  Max bin count: {values.max():,.0f}")
    print(f"  Distance range: {x_edges[0]:.0f} - {x_edges[-1]:.0f} mm")
    print(f"  Energy range: {y_edges[0]:.1f} - {y_edges[-1]:.1f} keV")
    
    # Calculate centers
    distance_centers = (x_edges[:-1] + x_edges[1:]) / 2
    energy_centers = (y_edges[:-1] + y_edges[1:]) / 2
    
    # Calculate average energy deposit
    total_energy = np.sum(values * energy_centers[:, np.newaxis].T)
    total_count = values.sum()
    avg_energy = total_energy / total_count if total_count > 0 else 0
    
    print(f"  Average energy deposit: {avg_energy:.1f} keV")
    
    # Find energy range that contains most deposits
    energy_sums = values.sum(axis=1)  # Sum over distance for each energy
    cumsum = np.cumsum(energy_sums)
    total_deposits = cumsum[-1]
    
    # Find 95% energy range
    energy_95_idx = np.searchsorted(cumsum, 0.95 * total_deposits)
    energy_95 = energy_centers[min(energy_95_idx, len(energy_centers)-1)]
    
    print(f"  95% of deposits below: {energy_95:.1f} keV")
    
    return {
        'values': values,
        'distance_edges': x_edges,
        'energy_edges': y_edges,
        'distance_centers': distance_centers,
        'energy_centers': energy_centers,
        'total_entries': values.sum(),
        'avg_energy': avg_energy,
        'energy_95': energy_95
    }

def visualize_histograms(photon_analysis, edep_analysis, energy_mev=None, output_path=None):
    """Create visualization of both 2D histograms."""
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    
    # Photon histogram
    ax1 = axes[0]
    im1 = ax1.imshow(photon_analysis['values'].T, 
                     origin='lower', 
                     aspect='auto', 
                     extent=[photon_analysis['angle_edges'][0], photon_analysis['angle_edges'][-1],
                            photon_analysis['distance_edges'][0], photon_analysis['distance_edges'][-1]],
                     cmap='plasma')
    
    title = f"Photon Opening Angle vs Distance"
    if energy_mev:
        title += f"\n{energy_mev} MeV Muons"
    title += f"\n{photon_analysis['total_entries']:,.0f} photons"
    
    ax1.set_title(title)
    ax1.set_xlabel('Opening Angle (rad)')
    ax1.set_ylabel('Distance (mm)')
    plt.colorbar(im1, ax=ax1, label='Photon Count')
    
    # Mark peak Cherenkov angle
    ax1.axvline(photon_analysis['peak_angle'], color='white', linestyle='--', alpha=0.7, 
                label=f'Peak: {photon_analysis["peak_angle"]:.3f} rad')
    ax1.legend()
    
    # Energy deposit histogram
    ax2 = axes[1]
    im2 = ax2.imshow(edep_analysis['values'].T,
                     origin='lower',
                     aspect='auto',
                     extent=[edep_analysis['distance_edges'][0], edep_analysis['distance_edges'][-1],
                            edep_analysis['energy_edges'][0], edep_analysis['energy_edges'][-1]],
                     cmap='viridis')
    
    title = f"Energy Deposits vs Distance"
    if energy_mev:
        title += f"\n{energy_mev} MeV Muons"
    title += f"\n{edep_analysis['total_entries']:,.0f} deposits"
    
    ax2.set_title(title)
    ax2.set_xlabel('Distance (mm)')
    ax2.set_ylabel('Energy Deposit (keV)')
    plt.colorbar(im2, ax=ax2, label='Deposit Count')
    
    # Mark 95% energy cutoff
    ax2.axhline(edep_analysis['energy_95'], color='white', linestyle='--', alpha=0.7,
                label=f'95%: {edep_analysis["energy_95"]:.1f} keV')
    ax2.legend()
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Visualization saved: {output_path}")
    
    plt.show()

def main():
    """Main analysis function."""
    if len(sys.argv) < 2:
        print("Usage: python analyze_2d_histograms.py <root_file> [energy_mev]")
        return 1
    
    root_file = sys.argv[1]
    energy_mev = float(sys.argv[2]) if len(sys.argv) > 2 else None
    
    if not Path(root_file).exists():
        print(f"Error: ROOT file not found: {root_file}")
        return 1
    
    try:
        with uproot.open(root_file) as file:
            print(f"Analyzing ROOT file: {root_file}")
            print(f"Available objects: {list(file.keys())}")
            
            # Check for 2D histograms
            if "PhotonHist_AngleDistance" not in file:
                print("Error: PhotonHist_AngleDistance histogram not found")
                return 1
            
            if "EdepHist_DistanceEnergy" not in file:
                print("Error: EdepHist_DistanceEnergy histogram not found")
                return 1
            
            # Load histograms
            photon_hist = file["PhotonHist_AngleDistance"]
            edep_hist = file["EdepHist_DistanceEnergy"]
            
            # Analyze histograms
            prefix = f"{energy_mev} MeV " if energy_mev else ""
            photon_analysis = analyze_photon_histogram(photon_hist, prefix)
            edep_analysis = analyze_edep_histogram(edep_hist, prefix)
            
            # Check if we should suggest different energy ranges
            if edep_analysis['energy_95'] > 800:  # Close to 1000 keV limit
                print(f"\nWarning: 95% energy cutoff ({edep_analysis['energy_95']:.1f} keV) is close to histogram limit")
                print("Consider increasing energy range in DataManager.cc")
            
            # Create visualization
            output_name = f"histogram_analysis_{energy_mev}MeV.png" if energy_mev else "histogram_analysis.png"
            visualize_histograms(photon_analysis, edep_analysis, energy_mev, output_name)
            
            # Summary
            print(f"\n=== SUMMARY ===")
            print(f"Total photons: {photon_analysis['total_entries']:,.0f}")
            print(f"Total energy deposits: {edep_analysis['total_entries']:,.0f}")
            print(f"Peak Cherenkov angle: {photon_analysis['peak_angle']:.3f} rad ({np.degrees(photon_analysis['peak_angle']):.1f}°)")
            print(f"Average energy deposit: {edep_analysis['avg_energy']:.1f} keV")
            
    except Exception as e:
        print(f"Error reading ROOT file: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())