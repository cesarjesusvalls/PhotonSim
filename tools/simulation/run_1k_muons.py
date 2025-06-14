#!/usr/bin/env python3
"""
Run 1000 muons with PhotonSim and provide runtime monitoring.
"""

import os
import sys
import time
import subprocess
import argparse
from pathlib import Path

def run_1k_muons(photonsim_path="build/PhotonSim", macro_path="macros/muons_1k.mac", verbose=True):
    """Run PhotonSim with 1000 muons and monitor progress."""
    
    photonsim_path = Path(photonsim_path)
    macro_path = Path(macro_path)
    
    if not photonsim_path.exists():
        raise FileNotFoundError(f"PhotonSim executable not found: {photonsim_path}")
    if not macro_path.exists():
        raise FileNotFoundError(f"Macro file not found: {macro_path}")
    
    print("=== Running 1000 Muons with PhotonSim ===")
    print(f"Executable: {photonsim_path}")
    print(f"Macro: {macro_path}")
    print()
    
    if verbose:
        print("Starting simulation...")
        print("This will take approximately 4-5 minutes based on benchmarks.")
        print()
    
    start_time = time.time()
    
    try:
        # Run PhotonSim
        result = subprocess.run(
            [str(photonsim_path), str(macro_path)],
            cwd=os.getcwd(),  # Use current working directory instead of executable parent
            text=True,
            capture_output=not verbose
        )
        
        end_time = time.time()
        runtime = end_time - start_time
        
        if result.returncode == 0:
            print(f"\n=== Simulation Complete ===")
            print(f"Runtime: {runtime:.2f} seconds ({runtime/60:.1f} minutes)")
            print(f"Rate: {1000/runtime:.1f} events/second")
            print(f"Output saved to: optical_photons.root")
            
            # Show file size
            root_file = photonsim_path.parent / "optical_photons.root"
            if root_file.exists():
                size_mb = root_file.stat().st_size / (1024 * 1024)
                print(f"ROOT file size: {size_mb:.1f} MB")
            
            return True
            
        else:
            print(f"Simulation failed with return code: {result.returncode}")
            if hasattr(result, 'stderr') and result.stderr:
                print(f"Error: {result.stderr}")
            return False
            
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user.")
        return False
    except Exception as e:
        print(f"Error running simulation: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Run 1000 muons with PhotonSim')
    parser.add_argument('--photonsim', '-p', default='build/PhotonSim',
                       help='Path to PhotonSim executable')
    parser.add_argument('--macro', '-m', default='macros/muons_1k.mac',
                       help='Path to macro file')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Run quietly (no real-time output)')
    
    args = parser.parse_args()
    
    success = run_1k_muons(args.photonsim, args.macro, not args.quiet)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()