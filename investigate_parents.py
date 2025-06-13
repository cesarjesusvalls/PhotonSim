#!/usr/bin/env python3
"""
Investigate parent particle patterns in PhotonSim data.

This script performs detailed analysis of which particles are creating 
Cherenkov photons and their parent-child relationships.
"""

import numpy as np
import matplotlib.pyplot as plt
import uproot
import sys

def investigate_parent_patterns(root_file_path):
    """Investigate parent-child patterns in photon creation."""
    
    try:
        with uproot.open(root_file_path) as file:
            tree = file["OpticalPhotons"]
            
            # Load all data including new fields
            data = {
                'EventID': tree['EventID'].array(library='np'),
                'PrimaryEnergy': tree['PrimaryEnergy'].array(library='np'),
                'NOpticalPhotons': tree['NOpticalPhotons'].array(library='np'),
                'PhotonPosX': tree['PhotonPosX'].array(library='np'),
                'PhotonPosY': tree['PhotonPosY'].array(library='np'),
                'PhotonPosZ': tree['PhotonPosZ'].array(library='np'),
                'PhotonTime': tree['PhotonTime'].array(library='np'),
                'PhotonProcess': tree['PhotonProcess'].array(library='np'),
                'PhotonParent': tree['PhotonParent'].array(library='np'),
                'PhotonParentID': tree['PhotonParentID'].array(library='np'),
                'PhotonTrackID': tree['PhotonTrackID'].array(library='np'),
            }
            
            n_events = len(data['EventID'])
            total_photons = np.sum(data['NOpticalPhotons'])
            
            print(f"=== Parent Pattern Investigation ===")
            print(f"Number of events: {n_events}")
            print(f"Total photons: {total_photons:,}")
            
            if total_photons == 0:
                print("ERROR: No photons found! Check simulation setup.")
                return None
            
            # Analyze all photons across events
            all_parent_names = []
            all_parent_ids = []
            all_track_ids = []
            all_processes = []
            all_positions = []
            
            for event_id in range(n_events):
                parents = data['PhotonParent'][event_id]
                parent_ids = data['PhotonParentID'][event_id]
                track_ids = data['PhotonTrackID'][event_id]
                processes = data['PhotonProcess'][event_id]
                
                pos_x = data['PhotonPosX'][event_id] / 1000.0  # Convert to meters
                pos_y = data['PhotonPosY'][event_id] / 1000.0
                pos_z = data['PhotonPosZ'][event_id] / 1000.0
                
                all_parent_names.extend(parents)
                all_parent_ids.extend(parent_ids)
                all_track_ids.extend(track_ids)
                all_processes.extend(processes)
                
                for i in range(len(pos_x)):
                    all_positions.append((pos_x[i], pos_y[i], pos_z[i]))
            
            # Convert to numpy arrays
            all_parent_ids = np.array(all_parent_ids)
            all_track_ids = np.array(all_track_ids)
            all_positions = np.array(all_positions)
            
            print(f"\n=== Parent ID Analysis ===")
            unique_parent_ids, counts = np.unique(all_parent_ids, return_counts=True)
            for pid, count in zip(unique_parent_ids, counts):
                percentage = 100 * count / len(all_parent_ids)
                print(f"Parent ID {pid}: {count:,} photons ({percentage:.1f}%)")
                
                # Show what particle names correspond to these IDs
                mask = np.array(all_parent_ids) == pid
                parent_names_for_id = [all_parent_names[i] for i in range(len(all_parent_names)) if mask[i]]
                unique_names = list(set(parent_names_for_id))
                print(f"  Particle names: {unique_names}")
                
                if len(parent_names_for_id) > 0:
                    # Sample positions for this parent ID
                    sample_positions = all_positions[mask][:5]  # First 5 positions
                    print(f"  Sample positions:")
                    for i, pos in enumerate(sample_positions):
                        print(f"    {i+1}: ({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f}) m")
                print()
            
            print(f"=== Process Analysis ===")
            unique_processes, process_counts = np.unique(all_processes, return_counts=True)
            for process, count in zip(unique_processes, process_counts):
                percentage = 100 * count / len(all_processes)
                print(f"{process}: {count:,} photons ({percentage:.1f}%)")
            
            print(f"\n=== Track ID Range ===")
            print(f"Track IDs range from {np.min(all_track_ids)} to {np.max(all_track_ids)}")
            print(f"Parent IDs range from {np.min(all_parent_ids)} to {np.max(all_parent_ids)}")
            
            # Check specific patterns
            primary_photons = all_parent_ids == 0
            secondary_photons = all_parent_ids > 0
            
            print(f"\n=== Primary vs Secondary Analysis ===")
            print(f"PRIMARY photons (parentID=0): {np.sum(primary_photons):,} ({100*np.sum(primary_photons)/len(all_parent_ids):.1f}%)")
            print(f"SECONDARY photons (parentID>0): {np.sum(secondary_photons):,} ({100*np.sum(secondary_photons)/len(all_parent_ids):.1f}%)")
            
            if np.sum(primary_photons) == 0:
                print("\n*** CRITICAL: NO PRIMARY PHOTONS FOUND! ***")
                print("This means the primary muon is NOT creating any Cherenkov photons directly.")
                print("Possible causes:")
                print("1. Muon energy below Cherenkov threshold")
                print("2. Muon stops before creating photons") 
                print("3. Physics process issue")
                print("4. Track ID assignment problem")
            
            # Analyze first event in detail
            if n_events > 0:
                print(f"\n=== Detailed Event 0 Analysis ===")
                event_parent_ids = data['PhotonParentID'][0]
                event_parent_names = data['PhotonParent'][0]
                event_track_ids = data['PhotonTrackID'][0]
                
                print(f"Event 0 photons: {len(event_parent_ids):,}")
                
                if len(event_parent_ids) > 0:
                    print(f"Parent ID breakdown:")
                    unique_ids, id_counts = np.unique(event_parent_ids, return_counts=True)
                    for uid, count in zip(unique_ids, id_counts):
                        print(f"  ID {uid}: {count} photons")
                    
                    print(f"\nFirst 10 photon details:")
                    for i in range(min(10, len(event_parent_ids))):
                        print(f"  Photon {i}: ParentID={event_parent_ids[i]}, "
                              f"ParentName={event_parent_names[i]}, TrackID={event_track_ids[i]}")
            
            return data
            
    except Exception as e:
        print(f"Error analyzing ROOT file: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_parent_plots(data):
    """Create plots showing parent patterns."""
    
    if data is None:
        return
        
    # Collect data for first event
    event_id = 0
    if len(data['PhotonParentID']) == 0:
        print("No data to plot")
        return
        
    parent_ids = data['PhotonParentID'][event_id]
    parent_names = data['PhotonParent'][event_id]
    
    if len(parent_ids) == 0:
        print("No photons in event 0 to plot")
        return
    
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle('Parent ID Analysis - Event 0', fontsize=14)
    
    # Parent ID histogram
    unique_ids, counts = np.unique(parent_ids, return_counts=True)
    axes[0].bar(unique_ids, counts, alpha=0.7)
    axes[0].set_xlabel('Parent ID')
    axes[0].set_ylabel('Number of Photons')
    axes[0].set_title('Photons by Parent ID')
    axes[0].set_yscale('log')
    
    # Parent name breakdown
    unique_names, name_counts = np.unique(parent_names, return_counts=True)
    axes[1].pie(name_counts, labels=unique_names, autopct='%1.1f%%')
    axes[1].set_title('Photons by Parent Particle')
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    root_file = "optical_photons.root"
    if len(sys.argv) > 1:
        root_file = sys.argv[1]
    
    print(f"Investigating: {root_file}")
    data = investigate_parent_patterns(root_file)
    
    if data is not None:
        create_parent_plots(data)