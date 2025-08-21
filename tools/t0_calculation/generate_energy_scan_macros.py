#!/usr/bin/env python3
"""
Generate macro files for energy scan from 10 MeV to 2000 MeV.
This script creates Geant4 macro files for different muon energies.
"""

import os
from pathlib import Path

def create_macro_file(energy_mev, output_dir):
    """Create a macro file for the specified energy."""
    
    macro_content = f"""# Macro for {energy_mev} MeV muons - Energy scan
# 100 events with individual photon storage disabled for histograms only

# Set output filename before initialization
/output/filename muons_{energy_mev}MeV_scan.root

/run/initialize

# Disable individual photon storage to save space - only histograms
/photon/storeIndividual false
/edep/storeIndividual false

# Disable muon decay processes via macro commands
/particle/select mu-
/particle/process/inactivate 1
/particle/process/inactivate 7
/particle/select mu+
/particle/process/inactivate 1

# Set up primary particle with fixed energy
/gun/particle mu-
/gun/randomEnergy false
/gun/energy {energy_mev} MeV
/gun/position 0 0 0 m
/gun/direction 0 0 1

# Run 100 events
/run/beamOn 100
"""
    
    macro_file = output_dir / f"muons_{energy_mev}MeV_scan.mac"
    with open(macro_file, 'w') as f:
        f.write(macro_content)
    
    print(f"Created: {macro_file}")
    return macro_file

def main():
    """Generate all macro files for the energy scan."""
    
    # Define the output directory
    output_dir = Path("/Users/cjesus/Software/PhotonSim/tools/t0_calculation/energy_scan_macros")
    
    # Define energy ranges
    energies = range(100, 2100, 100)
    
    print(f"Generating macro files for energies: {energies}")
    print(f"Output directory: {output_dir}")
    
    # Check if output directory exists
    if not output_dir.exists():
        print(f"Error: Directory {output_dir} does not exist!")
        return
    
    # Generate macro files
    created_files = []
    for energy in energies:
        # Check if macro file already exists
        macro_file = output_dir / f"muons_{energy}MeV_scan.mac"
        if macro_file.exists():
            print(f"Skipping {energy} MeV (file already exists)")
            continue
            
        macro_file = create_macro_file(energy, output_dir)
        created_files.append(macro_file)
    
    print(f"\nGenerated {len(created_files)} new macro files.")
    
    # Create a script to run all the new simulations
    run_script_path = output_dir / "run_new_energy_scans.sh"
    with open(run_script_path, 'w') as f:
        f.write("#!/bin/bash\n")
        f.write("# Script to run all new energy scan simulations\n")
        f.write("# Make sure PhotonSim is built in the build directory\n\n")
        f.write("cd /Users/cjesus/Software/PhotonSim\n")
        f.write("source setup.sh\n\n")
        
        for energy in energies:
            macro_path = f"tools/t0_calculation/energy_scan_macros/muons_{energy}MeV_scan.mac"
            f.write(f"echo 'Running {energy} MeV simulation...'\n")
            f.write(f"./build/PhotonSim {macro_path}\n")
            f.write(f"mv muons_{energy}MeV_scan.root tools/t0_calculation/energy_scan_macros/\n\n")
    
    # Make the run script executable
    os.chmod(run_script_path, 0o755)
    
    print(f"Created run script: {run_script_path}")
    print("\nTo run all simulations:")
    print(f"cd /Users/cjesus/Software/PhotonSim")
    print(f"./tools/t0_calculation/energy_scan_macros/run_new_energy_scans.sh")

if __name__ == "__main__":
    main()