#!/usr/bin/env python3
"""
Analyze energy deposits from PhotonSim for scintillation modeling.

This script examines the energy deposits stored in the ROOT file
to understand the spatial and temporal distribution for subsequent
scintillation light generation modeling.
"""

import numpy as np
import matplotlib.pyplot as plt
import uproot
import sys

def analyze_energy_deposits(root_file_path):
    """Analyze energy deposit data from PhotonSim."""
    
    try:
        with uproot.open(root_file_path) as file:
            tree = file["OpticalPhotons"]
            
            # Load energy deposit data
            data = {
                'EventID': tree['EventID'].array(library='np'),
                'PrimaryEnergy': tree['PrimaryEnergy'].array(library='np'),
                'NEnergyDeposits': tree['NEnergyDeposits'].array(library='np'),
                'EdepPosX': tree['EdepPosX'].array(library='np'),
                'EdepPosY': tree['EdepPosY'].array(library='np'),
                'EdepPosZ': tree['EdepPosZ'].array(library='np'),
                'EdepEnergy': tree['EdepEnergy'].array(library='np'),
                'EdepTime': tree['EdepTime'].array(library='np'),
                'EdepParticle': tree['EdepParticle'].array(library='np'),
                'EdepTrackID': tree['EdepTrackID'].array(library='np'),
                'EdepParentID': tree['EdepParentID'].array(library='np'),
            }
            
            n_events = len(data['EventID'])
            total_deposits = np.sum(data['NEnergyDeposits'])
            
            print(f"=== Energy Deposit Analysis ===")
            print(f"Total events: {n_events}")
            print(f"Total energy deposits: {total_deposits:,}")
            
            if total_deposits == 0:
                print("No energy deposits found!")
                return None
            
            # Focus on first event for detailed analysis
            event_id = 0
            print(f"\\nEvent {event_id} - Primary energy: {data['PrimaryEnergy'][event_id]:.1f} MeV")
            print(f"Energy deposits in event: {data['NEnergyDeposits'][event_id]:,}")
            
            # Extract energy deposit data for first event
            edep_x = data['EdepPosX'][event_id] / 1000.0  # Convert mm to m
            edep_y = data['EdepPosY'][event_id] / 1000.0
            edep_z = data['EdepPosZ'][event_id] / 1000.0
            edep_energy = data['EdepEnergy'][event_id] * 1000.0  # Convert MeV to keV
            edep_time = data['EdepTime'][event_id]  # ns
            edep_particles = data['EdepParticle'][event_id]
            edep_track_ids = data['EdepTrackID'][event_id]
            edep_parent_ids = data['EdepParentID'][event_id]
            
            if len(edep_energy) == 0:
                print("No energy deposits in event 0!")
                return None
            
            print(f"\\n=== Energy Deposit Statistics ===")
            print(f"Total deposited energy: {np.sum(edep_energy):.2f} keV")
            print(f"Mean deposit energy: {np.mean(edep_energy):.3f} keV")
            print(f"Median deposit energy: {np.median(edep_energy):.3f} keV")
            print(f"Max deposit energy: {np.max(edep_energy):.3f} keV")
            print(f"Min deposit energy: {np.min(edep_energy):.6f} keV")
            
            print(f"\\n=== Spatial Distribution ===")
            print(f"X range: {np.min(edep_x):.3f} to {np.max(edep_x):.3f} m")
            print(f"Y range: {np.min(edep_y):.3f} to {np.max(edep_y):.3f} m")
            print(f"Z range: {np.min(edep_z):.3f} to {np.max(edep_z):.3f} m")
            
            print(f"\\n=== Temporal Distribution ===")
            print(f"Time range: {np.min(edep_time):.3f} to {np.max(edep_time):.3f} ns")
            print(f"Time span: {np.max(edep_time) - np.min(edep_time):.3f} ns")
            
            print(f"\\n=== Particle Types Creating Deposits ===")
            unique_particles, particle_counts = np.unique(edep_particles, return_counts=True)
            for particle, count in zip(unique_particles, particle_counts):
                total_energy = np.sum(edep_energy[np.array(edep_particles) == particle])
                percentage = 100 * count / len(edep_particles)
                energy_percentage = 100 * total_energy / np.sum(edep_energy)
                print(f"{particle}: {count:,} deposits ({percentage:.1f}%), {total_energy:.2f} keV ({energy_percentage:.1f}%)")
            
            print(f"\\n=== Primary vs Secondary Contributions ===")
            primary_mask = np.array(edep_parent_ids) == 0
            secondary_mask = ~primary_mask
            
            primary_energy = np.sum(edep_energy[primary_mask])
            secondary_energy = np.sum(edep_energy[secondary_mask])
            total_energy = np.sum(edep_energy)
            
            print(f"Primary particle deposits: {np.sum(primary_mask):,} ({100*np.sum(primary_mask)/len(edep_energy):.1f}%)")
            print(f"  Energy: {primary_energy:.2f} keV ({100*primary_energy/total_energy:.1f}%)")
            
            print(f"Secondary particle deposits: {np.sum(secondary_mask):,} ({100*np.sum(secondary_mask)/len(edep_energy):.1f}%)")
            print(f"  Energy: {secondary_energy:.2f} keV ({100*secondary_energy/total_energy:.1f}%)")
            
            # Sample first few deposits for inspection
            print(f"\\n=== Sample Energy Deposits (first 10) ===")
            for i in range(min(10, len(edep_energy))):
                print(f"Deposit {i}: {edep_energy[i]:.3f} keV by {edep_particles[i]} at "
                      f"({edep_x[i]:.4f}, {edep_y[i]:.4f}, {edep_z[i]:.4f}) m, "
                      f"t={edep_time[i]:.3f} ns, parentID={edep_parent_ids[i]}")
            
            return {
                'edep_x': edep_x,
                'edep_y': edep_y,
                'edep_z': edep_z,
                'edep_energy': edep_energy,
                'edep_time': edep_time,
                'edep_particles': edep_particles,
                'edep_parent_ids': edep_parent_ids,
                'primary_energy': data['PrimaryEnergy'][event_id]
            }
            
    except Exception as e:
        print(f"Error analyzing ROOT file: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_energy_deposit_plots(analysis_data):
    """Create plots showing energy deposit patterns."""
    
    if analysis_data is None:
        return
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle(f'Energy Deposit Analysis - Primary: {analysis_data["primary_energy"]:.1f} MeV', fontsize=16)
    
    edep_x = analysis_data['edep_x']
    edep_y = analysis_data['edep_y']
    edep_z = analysis_data['edep_z']
    edep_energy = analysis_data['edep_energy']
    edep_time = analysis_data['edep_time']
    edep_particles = analysis_data['edep_particles']
    
    # 1. Energy deposit spectrum
    axes[0,0].hist(edep_energy, bins=50, alpha=0.7, edgecolor='black')
    axes[0,0].set_xlabel('Deposit Energy [keV]')
    axes[0,0].set_ylabel('Count')
    axes[0,0].set_title('Energy Deposit Spectrum')
    axes[0,0].set_yscale('log')
    
    # 2. Spatial distribution (XY projection)
    scatter = axes[0,1].scatter(edep_x, edep_y, c=edep_energy, s=10, alpha=0.7, cmap='viridis')
    axes[0,1].set_xlabel('X [m]')
    axes[0,1].set_ylabel('Y [m]')
    axes[0,1].set_title('XY Projection (colored by energy)')
    axes[0,1].set_aspect('equal')
    plt.colorbar(scatter, ax=axes[0,1], label='Energy [keV]')
    
    # 3. Z distribution
    axes[0,2].hist(edep_z, bins=50, alpha=0.7, edgecolor='black')
    axes[0,2].set_xlabel('Z Position [m]')
    axes[0,2].set_ylabel('Count')
    axes[0,2].set_title('Z Distribution')
    
    # 4. Time distribution
    axes[1,0].hist(edep_time, bins=50, alpha=0.7, edgecolor='black')
    axes[1,0].set_xlabel('Time [ns]')
    axes[1,0].set_ylabel('Count')
    axes[1,0].set_title('Time Distribution')
    
    # 5. Energy vs Time
    axes[1,1].scatter(edep_time, edep_energy, alpha=0.6, s=5)
    axes[1,1].set_xlabel('Time [ns]')
    axes[1,1].set_ylabel('Energy [keV]')
    axes[1,1].set_title('Energy vs Time')
    axes[1,1].set_yscale('log')
    
    # 6. Particle type breakdown
    unique_particles, counts = np.unique(edep_particles, return_counts=True)
    axes[1,2].pie(counts, labels=unique_particles, autopct='%1.1f%%')
    axes[1,2].set_title('Deposits by Particle Type')
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    root_file = "build/optical_photons.root"
    if len(sys.argv) > 1:
        root_file = sys.argv[1]
    
    print(f"Analyzing energy deposits in: {root_file}")
    analysis_data = analyze_energy_deposits(root_file)
    
    if analysis_data is not None:
        create_energy_deposit_plots(analysis_data)