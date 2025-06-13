#!/usr/bin/env python3
"""
Analyze physics processes generating optical photons in PhotonSim.

This script examines which physics processes (Cerenkov, Scintillation, etc.) 
are creating photons and their relative contributions.
"""

import numpy as np
import matplotlib.pyplot as plt
import uproot
import sys

def analyze_physics_processes(root_file_path):
    """Analyze physics processes for photon generation."""
    
    try:
        with uproot.open(root_file_path) as file:
            tree = file["OpticalPhotons"]
            
            # Load all data including parent tracking
            data = {
                'EventID': tree['EventID'].array(library='np'),
                'PrimaryEnergy': tree['PrimaryEnergy'].array(library='np'),
                'NOpticalPhotons': tree['NOpticalPhotons'].array(library='np'),
                'PhotonProcess': tree['PhotonProcess'].array(library='np'),
                'PhotonParent': tree['PhotonParent'].array(library='np'),
                'PhotonParentID': tree['PhotonParentID'].array(library='np'),
            }
            
            n_events = len(data['EventID'])
            total_photons = np.sum(data['NOpticalPhotons'])
            
            print(f"=== Physics Process Analysis ===")
            print(f"Total events: {n_events}")
            print(f"Total photons: {total_photons:,}")
            
            # Collect all processes and parent IDs
            all_processes = []
            all_parent_ids = []
            all_parent_names = []
            
            for event_id in range(n_events):
                processes = data['PhotonProcess'][event_id]
                parent_ids = data['PhotonParentID'][event_id]
                parent_names = data['PhotonParent'][event_id]
                
                all_processes.extend(processes)
                all_parent_ids.extend(parent_ids)
                all_parent_names.extend(parent_names)
            
            all_parent_ids = np.array(all_parent_ids)
            
            print(f"\\n=== ALL PHOTONS - Process Breakdown ===")
            unique_processes, process_counts = np.unique(all_processes, return_counts=True)
            
            for process, count in zip(unique_processes, process_counts):
                percentage = 100 * count / len(all_processes)
                print(f"{process}: {count:,} photons ({percentage:.2f}%)")
            
            # Filter for primary muon photons (parentID = 1)
            primary_muon_mask = all_parent_ids == 1
            primary_muon_processes = [all_processes[i] for i in range(len(all_processes)) if primary_muon_mask[i]]
            
            print(f"\\n=== PRIMARY MUON PHOTONS (parentID=1) - Process Breakdown ===")
            print(f"Primary muon photons: {len(primary_muon_processes):,} ({100*len(primary_muon_processes)/len(all_processes):.1f}% of total)")
            
            if len(primary_muon_processes) > 0:
                unique_primary_processes, primary_process_counts = np.unique(primary_muon_processes, return_counts=True)
                
                for process, count in zip(unique_primary_processes, primary_process_counts):
                    percentage = 100 * count / len(primary_muon_processes)
                    print(f"{process}: {count:,} photons ({percentage:.2f}%)")
            else:
                print("No photons from primary muon found!")
            
            # Analyze other parent particles
            print(f"\\n=== SECONDARY PARTICLES - Process Breakdown ===")
            secondary_mask = all_parent_ids != 1
            secondary_processes = [all_processes[i] for i in range(len(all_processes)) if secondary_mask[i]]
            secondary_parent_names = [all_parent_names[i] for i in range(len(all_parent_names)) if secondary_mask[i]]
            
            print(f"Secondary particle photons: {len(secondary_processes):,} ({100*len(secondary_processes)/len(all_processes):.1f}% of total)")
            
            if len(secondary_processes) > 0:
                unique_secondary_processes, secondary_process_counts = np.unique(secondary_processes, return_counts=True)
                
                for process, count in zip(unique_secondary_processes, secondary_process_counts):
                    percentage = 100 * count / len(secondary_processes)
                    print(f"{process}: {count:,} photons ({percentage:.2f}%)")
                
                # Break down by parent particle type for secondaries
                print(f"\\nSecondary particle types creating photons:")
                unique_secondary_parents, secondary_parent_counts = np.unique(secondary_parent_names, return_counts=True)
                
                for parent, count in zip(unique_secondary_parents, secondary_parent_counts):
                    percentage = 100 * count / len(secondary_parent_names)
                    print(f"  {parent}: {count:,} photons ({percentage:.2f}%)")
            
            # Create summary for easy reading
            print(f"\\n=== SUMMARY ===")
            print(f"Total photons: {len(all_processes):,}")
            print(f"├─ Primary muon (parentID=1): {len(primary_muon_processes):,} ({100*len(primary_muon_processes)/len(all_processes):.1f}%)")
            if len(primary_muon_processes) > 0:
                for process, count in zip(unique_primary_processes, primary_process_counts):
                    print(f"│  └─ {process}: {count:,} ({100*count/len(primary_muon_processes):.1f}%)")
            
            print(f"└─ Secondary particles: {len(secondary_processes):,} ({100*len(secondary_processes)/len(all_processes):.1f}%)")
            if len(secondary_processes) > 0:
                for process, count in zip(unique_secondary_processes, secondary_process_counts):
                    print(f"   └─ {process}: {count:,} ({100*count/len(secondary_processes):.1f}%)")
            
            return {
                'all_processes': all_processes,
                'all_parent_ids': all_parent_ids,
                'primary_muon_processes': primary_muon_processes,
                'secondary_processes': secondary_processes,
                'secondary_parent_names': secondary_parent_names
            }
            
    except Exception as e:
        print(f"Error analyzing ROOT file: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_process_plots(analysis_data):
    """Create plots showing process breakdowns."""
    
    if analysis_data is None:
        return
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle('PhotonSim Physics Process Analysis', fontsize=16)
    
    # Plot 1: All processes
    all_processes = analysis_data['all_processes']
    unique_all, counts_all = np.unique(all_processes, return_counts=True)
    
    axes[0].pie(counts_all, labels=unique_all, autopct='%1.1f%%', startangle=90)
    axes[0].set_title(f'All Photons\\n({len(all_processes):,} total)')
    
    # Plot 2: Primary muon processes
    primary_processes = analysis_data['primary_muon_processes']
    if len(primary_processes) > 0:
        unique_primary, counts_primary = np.unique(primary_processes, return_counts=True)
        axes[1].pie(counts_primary, labels=unique_primary, autopct='%1.1f%%', startangle=90)
        axes[1].set_title(f'Primary Muon Photons (parentID=1)\\n({len(primary_processes):,} total)')
    else:
        axes[1].text(0.5, 0.5, 'No primary\\nmuon photons', 
                    ha='center', va='center', transform=axes[1].transAxes)
        axes[1].set_title('Primary Muon Photons\\n(0 total)')
    
    # Plot 3: Secondary particle processes
    secondary_processes = analysis_data['secondary_processes']
    if len(secondary_processes) > 0:
        unique_secondary, counts_secondary = np.unique(secondary_processes, return_counts=True)
        axes[2].pie(counts_secondary, labels=unique_secondary, autopct='%1.1f%%', startangle=90)
        axes[2].set_title(f'Secondary Particle Photons\\n({len(secondary_processes):,} total)')
    else:
        axes[2].text(0.5, 0.5, 'No secondary\\nparticle photons', 
                    ha='center', va='center', transform=axes[2].transAxes)
        axes[2].set_title('Secondary Particle Photons\\n(0 total)')
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    root_file = "build/optical_photons.root"
    if len(sys.argv) > 1:
        root_file = sys.argv[1]
    
    print(f"Analyzing physics processes in: {root_file}")
    analysis_data = analyze_physics_processes(root_file)
    
    if analysis_data is not None:
        create_process_plots(analysis_data)