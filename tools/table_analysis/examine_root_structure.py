#!/usr/bin/env python3
"""
Comprehensive ROOT file structure examination for PhotonSim data.

This script examines the 1k_mu_optical_photons.root file to understand:
- File structure (trees, branches, data types)
- Data content and sample entries
- Muon energy information
- Optical photon data (positions, directions, etc.)
- Track origin information
- Parent-child relationships between muons and photons
"""

import numpy as np
import uproot
import sys
import os

def examine_root_structure(root_file_path):
    """Examine the complete structure of the ROOT file."""
    
    if not os.path.exists(root_file_path):
        print(f"ERROR: File {root_file_path} does not exist!")
        return None
    
    print(f"=== ROOT File Structure Analysis ===")
    print(f"File: {root_file_path}")
    print(f"File size: {os.path.getsize(root_file_path) / (1024*1024):.1f} MB")
    print()
    
    try:
        with uproot.open(root_file_path) as file:
            # Show all keys in the file
            print("=== File Contents ===")
            print("Keys in file:")
            for key in file.keys():
                print(f"  - {key}")
            print()
            
            # Examine each tree
            for key in file.keys():
                if key.endswith(';1'):  # ROOT key format
                    tree_name = key.replace(';1', '')
                    print(f"=== Tree: {tree_name} ===")
                    
                    try:
                        tree = file[key]
                        print(f"Number of entries: {len(tree)}")
                        print(f"Branches:")
                        
                        # List all branches with their types
                        for branch_name in tree.keys():
                            branch = tree[branch_name]
                            try:
                                # Get array to determine actual data type
                                sample_data = branch.array(library='np', entry_stop=1)
                                if len(sample_data) > 0:
                                    if hasattr(sample_data[0], '__len__') and not isinstance(sample_data[0], (str, bytes)):
                                        # Variable-length array
                                        sample_element = sample_data[0][0] if len(sample_data[0]) > 0 else "empty"
                                        data_type = f"vector<{type(sample_element).__name__}>"
                                    else:
                                        data_type = type(sample_data[0]).__name__
                                else:
                                    data_type = "unknown (empty)"
                            except:
                                data_type = "unknown (error)"
                            
                            print(f"  - {branch_name}: {data_type}")
                        print()
                        
                    except Exception as e:
                        print(f"  Error examining tree {tree_name}: {e}")
                        print()
            
            return file.keys()
            
    except Exception as e:
        print(f"Error opening ROOT file: {e}")
        return None

def analyze_optical_photons_data(root_file_path):
    """Detailed analysis of the OpticalPhotons tree data."""
    
    try:
        with uproot.open(root_file_path) as file:
            tree = file["OpticalPhotons"]
            
            print("=== OpticalPhotons Tree Detailed Analysis ===")
            print(f"Total events in tree: {len(tree)}")
            
            # Load sample data from first few events
            sample_size = min(5, len(tree))
            print(f"Loading sample data from first {sample_size} events...")
            
            # Load all branch data for sample
            branches = {}
            for branch_name in tree.keys():
                try:
                    branches[branch_name] = tree[branch_name].array(library='np', entry_stop=sample_size)
                    print(f"✓ Loaded {branch_name}")
                except Exception as e:
                    print(f"✗ Failed to load {branch_name}: {e}")
            
            print(f"\n=== Branch Data Analysis ===")
            
            # Analyze each branch
            for branch_name, data in branches.items():
                print(f"\n--- Branch: {branch_name} ---")
                print(f"Type: {type(data)}")
                print(f"Length: {len(data)}")
                
                if len(data) > 0:
                    first_entry = data[0]
                    print(f"First entry type: {type(first_entry)}")
                    
                    if hasattr(first_entry, '__len__') and not isinstance(first_entry, (str, bytes)):
                        # Variable-length array
                        print(f"First entry length: {len(first_entry)}")
                        if len(first_entry) > 0:
                            print(f"First element type: {type(first_entry[0])}")
                            print(f"Sample values (first 5): {first_entry[:5]}")
                        else:
                            print("First entry is empty array")
                    else:
                        # Scalar value
                        print(f"Sample values: {data[:3]}")
            
            print(f"\n=== Event-by-Event Sample Data ===")
            
            # Show detailed data for first few events
            for event_id in range(min(3, len(tree))):
                print(f"\n--- Event {event_id} ---")
                
                for branch_name, data in branches.items():
                    if event_id < len(data):
                        entry = data[event_id]
                        if hasattr(entry, '__len__') and not isinstance(entry, (str, bytes)):
                            print(f"{branch_name}: {len(entry)} elements")
                            if len(entry) > 0:
                                if len(entry) <= 5:
                                    print(f"  Values: {list(entry)}")
                                else:
                                    print(f"  First 5: {list(entry[:5])}")
                                    print(f"  Last 5: {list(entry[-5:])}")
                        else:
                            print(f"{branch_name}: {entry}")
            
            # Analyze relationships and patterns
            print(f"\n=== Data Relationships Analysis ===")
            
            if 'EventID' in branches and 'PrimaryEnergy' in branches and 'NOpticalPhotons' in branches:
                print("\nMuon Energy Information:")
                for i in range(min(5, len(branches['PrimaryEnergy']))):
                    event_id = branches['EventID'][i] if 'EventID' in branches else i
                    energy = branches['PrimaryEnergy'][i]
                    n_photons = branches['NOpticalPhotons'][i]
                    print(f"  Event {event_id}: Muon Energy = {energy:.1f} MeV, Optical Photons = {n_photons}")
            
            if 'PhotonParent' in branches and 'PhotonParentID' in branches:
                print("\nParent-Child Relationships (Event 0):")
                if len(branches['PhotonParent']) > 0:
                    parents = branches['PhotonParent'][0]
                    parent_ids = branches['PhotonParentID'][0]
                    
                    if len(parents) > 0:
                        unique_parents = list(set(parents))
                        print(f"  Unique parent types: {unique_parents}")
                        
                        for parent_type in unique_parents:
                            count = sum(1 for p in parents if p == parent_type)
                            print(f"    {parent_type}: {count} photons")
                        
                        print(f"  Sample parent data (first 10):")
                        for i in range(min(10, len(parents))):
                            print(f"    Photon {i}: Parent={parents[i]}, ParentID={parent_ids[i]}")
            
            if all(key in branches for key in ['PhotonPosX', 'PhotonPosY', 'PhotonPosZ']):
                print("\nOptical Photon Position Data (Event 0):")
                if len(branches['PhotonPosX']) > 0:
                    pos_x = branches['PhotonPosX'][0]  # mm
                    pos_y = branches['PhotonPosY'][0]  # mm
                    pos_z = branches['PhotonPosZ'][0]  # mm
                    
                    if len(pos_x) > 0:
                        print(f"  Number of photons: {len(pos_x)}")
                        print(f"  X range: {np.min(pos_x):.1f} to {np.max(pos_x):.1f} mm")
                        print(f"  Y range: {np.min(pos_y):.1f} to {np.max(pos_y):.1f} mm")
                        print(f"  Z range: {np.min(pos_z):.1f} to {np.max(pos_z):.1f} mm")
                        
                        # Distance from origin
                        distances = np.sqrt(pos_x**2 + pos_y**2 + pos_z**2)
                        print(f"  Distance from origin: {np.min(distances):.1f} to {np.max(distances):.1f} mm")
                        
                        print(f"  Sample positions (first 5, in meters):")
                        for i in range(min(5, len(pos_x))):
                            print(f"    Photon {i}: ({pos_x[i]/1000:.3f}, {pos_y[i]/1000:.3f}, {pos_z[i]/1000:.3f}) m")
            
            if 'PhotonTime' in branches:
                print("\nOptical Photon Timing Data (Event 0):")
                if len(branches['PhotonTime']) > 0:
                    times = branches['PhotonTime'][0]  # ns
                    if len(times) > 0:
                        print(f"  Time range: {np.min(times):.3f} to {np.max(times):.3f} ns")
                        print(f"  Mean time: {np.mean(times):.3f} ns")
                        print(f"  Sample times (first 5): {times[:5]} ns")
            
            if 'PhotonProcess' in branches:
                print("\nPhoton Creation Processes (Event 0):")
                if len(branches['PhotonProcess']) > 0:
                    processes = branches['PhotonProcess'][0]
                    if len(processes) > 0:
                        unique_processes = list(set(processes))
                        print(f"  Unique processes: {unique_processes}")
                        for process in unique_processes:
                            count = sum(1 for p in processes if p == process)
                            print(f"    {process}: {count} photons")
            
            return branches
            
    except Exception as e:
        print(f"Error analyzing OpticalPhotons data: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_summary_report(root_file_path):
    """Create a comprehensive summary report of the ROOT file."""
    
    print("=" * 80)
    print("COMPREHENSIVE ROOT FILE STRUCTURE REPORT")
    print("=" * 80)
    
    # Examine file structure
    keys = examine_root_structure(root_file_path)
    
    if keys is None:
        return
    
    print("\n" + "=" * 80)
    
    # Analyze OpticalPhotons data if it exists
    if any('OpticalPhotons' in key for key in keys):
        branches = analyze_optical_photons_data(root_file_path)
        
        if branches:
            print(f"\n=== SUMMARY FOR 3D TABLE EXTRACTION ===")
            print(f"✓ File contains OpticalPhotons tree")
            print(f"✓ Available data fields:")
            
            # Check for required fields
            required_fields = {
                'EventID': 'Event identifier',
                'PrimaryEnergy': 'Muon energy (MeV)',
                'PhotonPosX': 'Photon X position (mm)',
                'PhotonPosY': 'Photon Y position (mm)', 
                'PhotonPosZ': 'Photon Z position (mm)',
                'PhotonTime': 'Photon creation time (ns)',
                'PhotonParent': 'Parent particle type',
                'PhotonParentID': 'Parent particle ID',
                'PhotonProcess': 'Physics process creating photon'
            }
            
            for field, description in required_fields.items():
                status = "✓" if field in branches else "✗"
                print(f"    {status} {field}: {description}")
            
            print(f"\n=== RECOMMENDED EXTRACTION APPROACH ===")
            print(f"1. Load data event by event")
            print(f"2. For each event:")
            print(f"   - Get muon energy from PrimaryEnergy")
            print(f"   - Filter photons by parent type (e.g., 'Primary' or 'mu-')")
            print(f"   - Extract photon positions (PhotonPosX, PhotonPosY, PhotonPosZ)")
            print(f"   - Calculate distance from photon to muon track")
            print(f"   - Bin data into 3D grid for lookup table")
            print(f"3. Create energy-dependent lookup tables")
            
    else:
        print("WARNING: No OpticalPhotons tree found in file!")

if __name__ == "__main__":
    root_file = "/Users/cjesus/Software/PhotonSim/1k_mu_optical_photons.root"
    if len(sys.argv) > 1:
        root_file = sys.argv[1]
    
    if not os.path.exists(root_file):
        print(f"Error: File {root_file} does not exist!")
        sys.exit(1)
    
    create_summary_report(root_file)