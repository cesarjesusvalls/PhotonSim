#!/usr/bin/env python3
"""
Run energy scan simulations for t0 calculation.

This script runs PhotonSim with all the macro files in energy_scan_macros/
to generate the ROOT files needed for t0 timing analysis.
"""

import os
import sys
import subprocess
from pathlib import Path
import time

def run_photonsim_macro(macro_path, photonsim_executable):
    """Run PhotonSim with a single macro file."""
    
    print(f"Running simulation: {macro_path.name}")
    start_time = time.time()
    
    try:
        # Run PhotonSim with the macro
        result = subprocess.run(
            [str(photonsim_executable), str(macro_path)],
            capture_output=True,
            text=True,
        )
        
        elapsed_time = time.time() - start_time
        
        if result.returncode == 0:
            print(f"  ✅ Completed in {elapsed_time:.1f}s")
            return True
        else:
            print(f"  ❌ Failed (exit code {result.returncode})")
            print(f"  Error output: {result.stderr[:200]}...")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"  ⏰ Timeout after {elapsed_time:.1f}s")
        return False
    except Exception as e:
        print(f"  💥 Error: {e}")
        return False

def move_output_file(expected_output, target_dir):
    """Move the generated ROOT file to the target directory."""
    
    if expected_output.exists():
        target_path = target_dir / expected_output.name
        expected_output.rename(target_path)
        print(f"  📁 Moved to: {target_path}")
        return True
    else:
        print(f"  ❌ Output file not found: {expected_output}")
        return False

def main():
    """Main function to run all energy scan simulations."""
    
    # Set up paths
    project_root = Path(__file__).parent.parent.parent
    photonsim_executable = project_root / "build" / "PhotonSim"
    macros_dir = Path(__file__).parent / "energy_scan_macros"
    
    print("=== Energy Scan Simulation Runner ===")
    print(f"Project root: {project_root}")
    print(f"PhotonSim executable: {photonsim_executable}")
    print(f"Macros directory: {macros_dir}")
    
    # Check if PhotonSim executable exists
    if not photonsim_executable.exists():
        print(f"❌ PhotonSim executable not found: {photonsim_executable}")
        print("Please build PhotonSim first:")
        print("  cd build && cmake .. && make -j4")
        return 1
    
    # Check if macros directory exists
    if not macros_dir.exists():
        print(f"❌ Macros directory not found: {macros_dir}")
        return 1
    
    # Find all macro files
    macro_files = list(macros_dir.glob("muons_*MeV_scan.mac"))
    if not macro_files:
        print(f"❌ No macro files found in {macros_dir}")
        return 1
    
    # Sort by energy for logical processing order
    def extract_energy(macro_path):
        try:
            energy_str = macro_path.stem.split('_')[1].replace('MeV', '')
            return int(energy_str)
        except:
            return 0
    
    macro_files.sort(key=extract_energy)
    
    print(f"Found {len(macro_files)} macro files")
    
    # Check which simulations need to be run (skip if ROOT file already exists)
    needed_macros = []
    for macro_path in macro_files:
        expected_root = macros_dir / macro_path.name.replace('.mac', '.root')
        if not expected_root.exists():
            needed_macros.append(macro_path)
        else:
            energy = extract_energy(macro_path)
            print(f"⏭️  Skipping {energy} MeV (ROOT file exists)")
    
    if not needed_macros:
        print("✅ All ROOT files already exist. Nothing to do!")
        return 0
    
    print(f"Need to run {len(needed_macros)} simulations...")
    
    # Change to project root directory for running PhotonSim
    original_cwd = os.getcwd()
    os.chdir(project_root)
    
    try:
        # Run simulations
        successful = 0
        failed = 0
        
        for i, macro_path in enumerate(needed_macros, 1):
            energy = extract_energy(macro_path)
            print(f"\n[{i}/{len(needed_macros)}] Energy: {energy} MeV")
            
            # Run the simulation
            if run_photonsim_macro(macro_path, photonsim_executable):
                # Move the output file
                expected_output = project_root / macro_path.name.replace('.mac', '.root')
                if move_output_file(expected_output, macros_dir):
                    successful += 1
                else:
                    failed += 1
            else:
                failed += 1
        
        # Summary
        print(f"\n=== Simulation Summary ===")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"📊 Total: {successful + failed}")
        
        if failed > 0:
            print(f"\n⚠️  {failed} simulations failed. Check the error messages above.")
            return 1
        else:
            print(f"\n🎉 All simulations completed successfully!")
            print(f"\nTo run the t0 analysis:")
            print(f"python3 tools/t0_calculation/calculate_t0.py tools/t0_calculation/energy_scan_macros")
            return 0
            
    finally:
        # Restore original working directory
        os.chdir(original_cwd)

if __name__ == "__main__":
    sys.exit(main())