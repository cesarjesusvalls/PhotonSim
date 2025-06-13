#!/usr/bin/env python3
"""
Detailed validation script to investigate speed of light violations.
"""

import numpy as np
import matplotlib.pyplot as plt
import uproot
import os

def detailed_violation_analysis():
    """Detailed analysis of apparent speed of light violations."""
    
    # Try relative path from tools/validation or from PhotonSim root
    root_file = "../../build/optical_photons.root"
    if not os.path.exists(root_file):
        root_file = "build/optical_photons.root"
    
    with uproot.open(root_file) as f:
        tree = f['OpticalPhotons']
        
        # Load data
        all_pos_x = np.concatenate(tree['PhotonPosX'].array(library='np')) / 1000.0  # mm to m
        all_pos_y = np.concatenate(tree['PhotonPosY'].array(library='np')) / 1000.0
        all_pos_z = np.concatenate(tree['PhotonPosZ'].array(library='np')) / 1000.0
        all_times = np.concatenate(tree['PhotonTime'].array(library='np'))  # ns
        
        distances = np.sqrt(all_pos_x**2 + all_pos_y**2 + all_pos_z**2)
        
        # Speed of light in water (n ≈ 1.33)
        c_water = 0.299792458 / 1.33  # ≈ 0.225 m/ns
        c_vacuum = 0.299792458  # m/ns
        
        # Calculate violations with different tolerances
        max_allowed = all_times * c_water
        violations = distances > max_allowed
        excess = distances - max_allowed
        
        print(f"=== Detailed Violation Analysis ===")
        print(f"Total photons: {len(distances):,}")
        print(f"Violations (c in water): {np.sum(violations):,} ({100*np.sum(violations)/len(violations):.2f}%)")
        
        # Check violations against vacuum speed
        max_allowed_vacuum = all_times * c_vacuum
        violations_vacuum = distances > max_allowed_vacuum
        print(f"Violations (c in vacuum): {np.sum(violations_vacuum):,} ({100*np.sum(violations_vacuum)/len(violations_vacuum):.2f}%)")
        
        # Analyze violation magnitudes
        if np.sum(violations) > 0:
            violation_excess = excess[violations]
            print(f"\nViolation magnitudes:")
            print(f"  Mean excess: {np.mean(violation_excess):.6f} m")
            print(f"  Std excess:  {np.std(violation_excess):.6f} m")
            print(f"  Max excess:  {np.max(violation_excess):.6f} m")
            print(f"  Min excess:  {np.min(violation_excess):.6f} m")
            
            # Check if violations are due to numerical precision
            precision_threshold = 1e-6  # 1 micrometer
            significant_violations = violation_excess > precision_threshold
            print(f"  Violations > {precision_threshold*1e6:.1f} μm: {np.sum(significant_violations)}")
            
        # Look at specific violation cases
        print(f"\n=== Detailed Violation Examples ===")
        violation_indices = np.where(violations)[0]
        
        for i, idx in enumerate(violation_indices[:10]):  # First 10 violations
            print(f"Violation {i+1}:")
            print(f"  Position: ({all_pos_x[idx]:.6f}, {all_pos_y[idx]:.6f}, {all_pos_z[idx]:.6f}) m")
            print(f"  Distance: {distances[idx]:.6f} m")
            print(f"  Time: {all_times[idx]:.6f} ns")
            print(f"  Max allowed (c_water): {max_allowed[idx]:.6f} m")
            print(f"  Excess: {excess[idx]:.6f} m ({excess[idx]*1e6:.3f} μm)")
            print(f"  Effective speed: {distances[idx]/all_times[idx]:.6f} m/ns")
            print(f"  Speed ratio (vs c_water): {(distances[idx]/all_times[idx])/c_water:.6f}")
            print()
        
        # Create detailed plots
        fig, axes = plt.subplots(2, 2, figsize=(10, 8))
        fig.suptitle('Detailed Speed of Light Violation Analysis', fontsize=16)
        
        # Scatter plot of all points
        ax1 = axes[0, 0]
        ax1.scatter(all_times, distances, alpha=0.6, s=1, c='blue', label='All photons')
        if np.sum(violations) > 0:
            ax1.scatter(all_times[violations], distances[violations], 
                       alpha=0.8, s=2, c='red', label=f'Violations ({np.sum(violations):,})')
        
        # Add speed of light lines
        t_max = np.max(all_times)
        t_line = np.linspace(0, t_max, 100)
        ax1.plot(t_line, t_line * c_vacuum, 'r--', linewidth=2, label=f'c vacuum')
        ax1.plot(t_line, t_line * c_water, 'b--', linewidth=2, label=f'c water')
        
        ax1.set_xlabel('Time [ns]')
        ax1.set_ylabel('Distance [m]')
        ax1.set_title('Time vs Distance')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Histogram of violation magnitudes
        ax2 = axes[0, 1]
        if np.sum(violations) > 0:
            ax2.hist(violation_excess * 1e6, bins=50, alpha=0.7, color='red', edgecolor='black')
            ax2.set_xlabel('Violation Magnitude [μm]')
            ax2.set_ylabel('Count')
            ax2.set_title('Distribution of Violation Magnitudes')
            ax2.set_yscale('log')
            ax2.grid(True, alpha=0.3)
        
        # Effective speed distribution
        ax3 = axes[1, 0]
        effective_speeds = distances / all_times
        ax3.hist(effective_speeds, bins=50, alpha=0.7, color='skyblue', edgecolor='black')
        ax3.axvline(c_water, color='blue', linestyle='--', linewidth=2, label=f'c in water')
        ax3.axvline(c_vacuum, color='red', linestyle='--', linewidth=2, label=f'c in vacuum')
        ax3.set_xlabel('Effective Speed [m/ns]')
        ax3.set_ylabel('Count')
        ax3.set_title('Distribution of Effective Speeds')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Zoomed view of violations
        ax4 = axes[1, 1]
        if np.sum(violations) > 0:
            # Focus on early times where violations might be more obvious
            early_mask = all_times < 10  # First 10 ns
            early_times = all_times[early_mask]
            early_distances = distances[early_mask]
            early_violations = violations[early_mask]
            
            ax4.scatter(early_times, early_distances, alpha=0.6, s=2, c='blue', label='All photons')
            if np.sum(early_violations) > 0:
                ax4.scatter(early_times[early_violations], early_distances[early_violations],
                           alpha=0.8, s=4, c='red', label=f'Violations ({np.sum(early_violations)})')
            
            t_max_early = np.max(early_times)
            t_line_early = np.linspace(0, t_max_early, 100)
            ax4.plot(t_line_early, t_line_early * c_vacuum, 'r--', linewidth=2, label='c vacuum')
            ax4.plot(t_line_early, t_line_early * c_water, 'b--', linewidth=2, label='c water')
            
            ax4.set_xlabel('Time [ns]')
            ax4.set_ylabel('Distance [m]')
            ax4.set_title('Early Time Violations (0-10 ns)')
            ax4.legend()
            ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
        
        return violations, excess

if __name__ == "__main__":
    violations, excess = detailed_violation_analysis()