#!/usr/bin/env python3
"""
Analyze the 1k muon events dataset.
"""

import numpy as np
import matplotlib.pyplot as plt
import uproot
from pathlib import Path

def analyze_1k_events(file_path="1k_mu_optical_photons.root"):
    """Comprehensive analysis of the 1k muon dataset."""
    
    print("=== 1k Muon Events Analysis ===")
    print(f"Loading data from {file_path}...")
    
    with uproot.open(file_path) as file:
        tree = file["OpticalPhotons"]
        total_events = tree.num_entries
        print(f"Total events: {total_events}")
        
        # Load basic event info first
        print("\nLoading event-level data...")
        event_data = tree.arrays(['EventID', 'PrimaryEnergy', 'NOpticalPhotons'], library="np")
        
        # Analyze event-level statistics
        energies = event_data['PrimaryEnergy']
        photon_counts = event_data['NOpticalPhotons']
        
        print(f"\n=== Event Statistics ===")
        print(f"Energy range: {energies.min():.1f} - {energies.max():.1f} MeV")
        print(f"Mean energy: {energies.mean():.1f} ± {energies.std():.1f} MeV")
        print(f"Photons per event: {photon_counts.min()} - {photon_counts.max()}")
        print(f"Mean photons per event: {photon_counts.mean():.0f} ± {photon_counts.std():.0f}")
        print(f"Total photons: {photon_counts.sum():,}")
        
        # Load a sample of photon-level data (first 10 events for detailed analysis)
        print(f"\nLoading detailed photon data (first 10 events for analysis)...")
        sample_data = tree.arrays([
            'PhotonPosX', 'PhotonPosY', 'PhotonPosZ',
            'PhotonDirX', 'PhotonDirY', 'PhotonDirZ', 
            'PhotonParent'
        ], entry_stop=10, library="np")
        
        # Analyze photon parents
        print(f"\n=== Photon Parent Analysis (first 10 events) ===")
        all_parents = []
        for event_idx in range(10):
            parents = sample_data['PhotonParent'][event_idx]
            all_parents.extend(parents)
        
        unique_parents, counts = np.unique(all_parents, return_counts=True)
        total_sample_photons = len(all_parents)
        
        print(f"Sample size: {total_sample_photons:,} photons from first 10 events")
        for parent, count in zip(unique_parents, counts):
            percentage = count / total_sample_photons * 100
            print(f"  {parent}: {count:,} ({percentage:.1f}%)")
        
        return energies, photon_counts, unique_parents, counts

def create_visualizations(energies, photon_counts, output_dir="output"):
    """Create visualizations for the 1k dataset."""
    
    print(f"\n=== Creating Visualizations ===")
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    fig, axes = plt.subplots(2, 2, figsize=(10, 6))
    fig.suptitle('1k Muon Events Analysis', fontsize=16)
    
    # Energy histogram
    axes[0,0].hist(energies, bins=50, alpha=0.7, color='skyblue', edgecolor='black')
    axes[0,0].set_xlabel('Muon Energy (MeV)')
    axes[0,0].set_ylabel('Number of Events')
    axes[0,0].set_title(f'Energy Distribution ({len(energies)} events)')
    axes[0,0].grid(True, alpha=0.3)
    
    # Add energy statistics
    stats_text = f'Mean: {energies.mean():.1f} MeV\nStd: {energies.std():.1f} MeV'
    axes[0,0].text(0.02, 0.98, stats_text, transform=axes[0,0].transAxes, 
                   verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Photon count histogram
    axes[0,1].hist(photon_counts, bins=50, alpha=0.7, color='lightgreen', edgecolor='black')
    axes[0,1].set_xlabel('Photons per Event')
    axes[0,1].set_ylabel('Number of Events')
    axes[0,1].set_title('Photon Count Distribution')
    axes[0,1].grid(True, alpha=0.3)
    
    # Energy vs Photon count scatter
    axes[1,0].scatter(energies, photon_counts, alpha=0.5, s=10)
    axes[1,0].set_xlabel('Muon Energy (MeV)')
    axes[1,0].set_ylabel('Photons per Event')
    axes[1,0].set_title('Energy vs Photon Production')
    axes[1,0].grid(True, alpha=0.3)
    
    # Photons per MeV
    photons_per_mev = photon_counts / energies
    axes[1,1].hist(photons_per_mev, bins=50, alpha=0.7, color='orange', edgecolor='black')
    axes[1,1].set_xlabel('Photons per MeV')
    axes[1,1].set_ylabel('Number of Events')
    axes[1,1].set_title('Photon Production Efficiency')
    axes[1,1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path / "1k_events_analysis.png", dpi=200, bbox_inches='tight')
    print(f"Analysis plots saved to: {output_path / '1k_events_analysis.png'}")
    
    # Create detailed energy distribution
    fig, ax = plt.subplots(1, 1, figsize=(8, 4))
    
    n, bins, patches = ax.hist(energies, bins=100, alpha=0.7, color='skyblue', edgecolor='black')
    ax.set_xlabel('Muon Energy (MeV)', fontsize=12)
    ax.set_ylabel('Number of Events', fontsize=12)
    ax.set_title(f'Detailed Energy Distribution - 1000 Muon Events', fontsize=14)
    ax.grid(True, alpha=0.3)
    
    # Add statistics box
    stats_text = (f'Events: {len(energies)}\n'
                 f'Range: {energies.min():.1f} - {energies.max():.1f} MeV\n'
                 f'Mean: {energies.mean():.1f} MeV\n'
                 f'Std: {energies.std():.1f} MeV\n'
                 f'Median: {np.median(energies):.1f} MeV')
    
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
    
    plt.tight_layout()
    plt.savefig(output_path / "1k_energy_distribution.png", dpi=200, bbox_inches='tight')
    print(f"Detailed energy plot saved to: {output_path / '1k_energy_distribution.png'}")

def estimate_full_dataset_size(file_path="1k_mu_optical_photons.root"):
    """Estimate the size of the full dataset."""
    
    print(f"\n=== Dataset Size Estimation ===")
    
    with uproot.open(file_path) as file:
        tree = file["OpticalPhotons"]
        
        # Sample first 10 events to estimate total photons
        sample_data = tree.arrays(['NOpticalPhotons'], entry_stop=10, library="np")
        sample_photons = sample_data['NOpticalPhotons']
        
        mean_photons_per_event = sample_photons.mean()
        total_events = tree.num_entries
        estimated_total_photons = mean_photons_per_event * total_events
        
        print(f"Sample (first 10 events): {sample_photons.mean():.0f} ± {sample_photons.std():.0f} photons/event")
        print(f"Estimated total photons: {estimated_total_photons:,.0f}")
        print(f"Estimated muon photons (~70%): {estimated_total_photons * 0.7:,.0f}")
        
        # Memory estimation
        estimated_memory_gb = estimated_total_photons * 8 * 10 / (1024**3)  # ~10 floats per photon
        print(f"Estimated memory needed: {estimated_memory_gb:.1f} GB")
        
        if estimated_memory_gb > 2:
            print("⚠️  Large dataset! Consider sampling for table creation.")
        else:
            print("✅ Dataset size manageable for full processing.")

def main():
    """Main analysis function."""
    
    # Check if file exists
    file_path = "1k_mu_optical_photons.root"
    if not Path(file_path).exists():
        print(f"Error: File {file_path} not found!")
        return
    
    # Analyze the dataset
    energies, photon_counts, parents, parent_counts = analyze_1k_events(file_path)
    
    # Create visualizations
    create_visualizations(energies, photon_counts)
    
    # Estimate full dataset processing requirements
    estimate_full_dataset_size(file_path)
    
    # Summary
    print(f"\n=== Summary ===")
    print(f"✅ Successfully analyzed 1k muon events")
    print(f"✅ Energy range: {energies.min():.1f} - {energies.max():.1f} MeV")
    print(f"✅ Total photons: {photon_counts.sum():,}")
    print(f"✅ Photon types: {', '.join(parents)}")
    print(f"✅ Visualizations saved to output/")
    
    print(f"\nNext steps:")
    print(f"1. Create 3D table: python3 tools/create_photon_table.py")
    print(f"2. View results: Check output/ directory")

if __name__ == "__main__":
    main()