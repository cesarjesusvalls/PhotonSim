#!/usr/bin/env python3
"""
Compare histograms from different energy ROOT files.
"""

import numpy as np
import matplotlib.pyplot as plt
import uproot
import sys
from pathlib import Path

def compare_root_files(file_list, energy_list=None):
    """Compare multiple ROOT files side by side."""
    
    n_files = len(file_list)
    if n_files == 0:
        print("No files provided")
        return
    
    # Create subplot grid
    fig, axes = plt.subplots(2, n_files, figsize=(6*n_files, 10))
    if n_files == 1:
        axes = axes.reshape(2, 1)
    
    print(f"Comparing {n_files} ROOT files:")
    
    for i, root_file in enumerate(file_list):
        file_path = Path(root_file)
        if not file_path.exists():
            print(f"File not found: {root_file}")
            continue
            
        print(f"\n{i+1}. {root_file}")
        
        try:
            with uproot.open(root_file) as file:
                # Photon histogram
                if "PhotonHist_AngleDistance" in file:
                    hist = file["PhotonHist_AngleDistance"]
                    values = hist.values()
                    
                    ax = axes[0, i]
                    im = ax.imshow(values.T, origin='lower', aspect='auto', cmap='plasma')
                    plt.colorbar(im, ax=ax, label='Count', shrink=0.8)
                    
                    ax.set_xlabel('Angle Bin')
                    ax.set_ylabel('Distance Bin')
                    
                    # Calculate Cherenkov angle
                    angle_proj = values.sum(axis=1)
                    peak_bin = np.argmax(angle_proj)
                    peak_angle = peak_bin * np.pi / 500
                    
                    energy_label = f" ({energy_list[i]:.0f} MeV)" if energy_list and i < len(energy_list) else ""
                    ax.set_title(f'Photons{energy_label}\n{values.sum():,.0f} total\nPeak: {np.degrees(peak_angle):.1f}°')
                    
                    ax.axvline(peak_bin, color='white', linestyle='--', alpha=0.7)
                    
                    print(f"   Photons: {values.sum():,.0f}, Peak angle: {np.degrees(peak_angle):.1f}°")
                
                # Energy deposit histogram
                if "EdepHist_DistanceEnergy" in file:
                    hist = file["EdepHist_DistanceEnergy"]
                    values = hist.values()
                    
                    ax = axes[1, i]
                    im = ax.imshow(values.T, origin='lower', aspect='auto', cmap='viridis')
                    plt.colorbar(im, ax=ax, label='Count', shrink=0.8)
                    
                    ax.set_xlabel('Distance Bin')
                    ax.set_ylabel('Energy Bin')
                    
                    energy_label = f" ({energy_list[i]:.0f} MeV)" if energy_list and i < len(energy_list) else ""
                    ax.set_title(f'Energy Deposits{energy_label}\n{values.sum():,.0f} total')
                    
                    print(f"   Energy deposits: {values.sum():,.0f}")
        
        except Exception as e:
            print(f"   Error reading file: {e}")
    
    plt.tight_layout()
    
    # Save comparison
    output_name = f'energy_comparison_{n_files}files.png'
    plt.savefig(output_name, dpi=150, bbox_inches='tight')
    print(f"\nComparison saved: {output_name}")
    
    plt.show()

def main():
    """Main comparison function."""
    if len(sys.argv) < 2:
        print("Usage: python compare_energies.py <file1.root> [file2.root] [file3.root] ...")
        print("Example: python compare_energies.py 500MeV.root 510MeV.root")
        return
    
    root_files = sys.argv[1:]
    
    # Try to extract energies from filenames
    energy_list = []
    for f in root_files:
        try:
            # Look for patterns like "500MeV" or "500_"
            import re
            match = re.search(r'(\d+)(?:MeV|_)', f)
            if match:
                energy_list.append(float(match.group(1)))
            else:
                energy_list.append(None)
        except:
            energy_list.append(None)
    
    # Filter out None values if we couldn't extract all energies
    if None in energy_list:
        energy_list = None
    
    compare_root_files(root_files, energy_list)

if __name__ == '__main__':
    main()