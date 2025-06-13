#!/usr/bin/env python3
"""
PhotonSim Particle Comparison Benchmark
Compares runtime performance for different particle types.
"""

import os
import sys
import time
import subprocess
import json
import argparse
from pathlib import Path
import tempfile

class ParticleComparisonBenchmark:
    def __init__(self, photonsim_path):
        self.photonsim_path = Path(photonsim_path)
        self.results = {}
        
        if not self.photonsim_path.exists():
            raise FileNotFoundError(f"PhotonSim executable not found: {photonsim_path}")
    
    def create_particle_macro(self, particle, energy_mev, event_count, output_path):
        """Create a test macro for specified particle type."""
        macro_content = f"""# Benchmark macro for {particle}
/run/initialize

# Disable decay processes for muons if applicable
{'/process/inactivate Decay mu+' if 'mu' in particle else ''}
{'/process/inactivate Decay mu-' if 'mu' in particle else ''}

/gun/particle {particle}
/gun/energy {energy_mev} MeV
/gun/position 0 0 0 m
/gun/direction 0 0 1
/run/beamOn {event_count}
"""
        
        with open(output_path, 'w') as f:
            f.write(macro_content)
    
    def run_particle_benchmark(self, particle, energy_mev, event_count, runs=3):
        """Run benchmark for a specific particle type."""
        print(f"Benchmarking {particle} at {energy_mev} MeV with {event_count} events...")
        
        times = []
        
        for run in range(runs):
            # Create temporary macro file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.mac', delete=False) as f:
                temp_mac = f.name
            
            try:
                self.create_particle_macro(particle, energy_mev, event_count, temp_mac)
                
                # Run PhotonSim and measure time
                start_time = time.time()
                
                result = subprocess.run(
                    [str(self.photonsim_path), temp_mac],
                    cwd=self.photonsim_path.parent,
                    capture_output=True,
                    text=True
                )
                
                end_time = time.time()
                runtime = end_time - start_time
                
                if result.returncode == 0:
                    times.append(runtime)
                    print(f"  Run {run+1}: {runtime:.3f}s")
                else:
                    print(f"  Run {run+1}: FAILED")
                    print(f"  Error: {result.stderr}")
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_mac):
                    os.unlink(temp_mac)
        
        if times:
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            
            result_data = {
                'particle': particle,
                'energy_mev': energy_mev,
                'events': event_count,
                'avg_runtime': avg_time,
                'min_runtime': min_time,
                'max_runtime': max_time,
                'runs': len(times),
                'all_times': times,
                'events_per_second': event_count / avg_time
            }
            
            print(f"  Average: {avg_time:.3f}s ({event_count/avg_time:.1f} events/s)")
            return result_data
        else:
            print("  All runs failed!")
            return None
    
    def run_comparison_suite(self, particles_config, event_count=25, runs_per_test=3):
        """Run comparison suite for multiple particle types."""
        print("=== PhotonSim Particle Comparison Benchmark ===")
        print(f"Event count: {event_count}")
        print(f"Runs per test: {runs_per_test}")
        print()
        
        for particle_name, config in particles_config.items():
            result = self.run_particle_benchmark(
                config['particle'], 
                config['energy'], 
                event_count, 
                runs_per_test
            )
            
            if result:
                self.results[particle_name] = result
            print()
    
    def save_results(self, output_file):
        """Save comparison results to JSON file."""
        with open(output_file, 'w') as f:
            json.dump({
                'benchmark_info': {
                    'photonsim_path': str(self.photonsim_path),
                    'timestamp': time.time(),
                    'benchmark_type': 'particle_comparison'
                },
                'results': self.results
            }, f, indent=2)
        print(f"Results saved to: {output_file}")
    
    def print_comparison_summary(self):
        """Print comparison summary."""
        if not self.results:
            print("No results to compare.")
            return
        
        print("=== Particle Performance Comparison ===")
        print(f"{'Particle':>12} {'Energy (MeV)':>12} {'Runtime (s)':>12} {'Events/s':>10} {'Relative':>10}")
        print("-" * 70)
        
        # Sort by events per second (descending)
        sorted_results = sorted(
            self.results.items(), 
            key=lambda x: x[1]['events_per_second'], 
            reverse=True
        )
        
        # Get baseline (fastest) for relative comparison
        baseline_rate = sorted_results[0][1]['events_per_second'] if sorted_results else 1
        
        for name, result in sorted_results:
            particle = result['particle']
            energy = result['energy_mev']
            runtime = result['avg_runtime']
            events_per_sec = result['events_per_second']
            relative = events_per_sec / baseline_rate
            
            print(f"{particle:>12} {energy:>12} {runtime:>12.3f} {events_per_sec:>10.1f} {relative:>10.3f}")


def main():
    parser = argparse.ArgumentParser(description='Compare PhotonSim performance across particle types')
    parser.add_argument('--photonsim', '-p', 
                       default='../build/PhotonSim',
                       help='Path to PhotonSim executable')
    parser.add_argument('--events', '-e', type=int, default=25,
                       help='Number of events per test')
    parser.add_argument('--runs', '-r', type=int, default=3,
                       help='Number of runs per particle type')
    parser.add_argument('--output', '-o', default='particle_comparison_results.json',
                       help='Output file for results')
    
    args = parser.parse_args()
    
    # Define particle configurations
    particles_config = {
        'muon_650': {'particle': 'mu-', 'energy': 650},
        'electron_650': {'particle': 'e-', 'energy': 650},
        'proton_650': {'particle': 'proton', 'energy': 650},
        'gamma_10': {'particle': 'gamma', 'energy': 10},
        'muon_300': {'particle': 'mu-', 'energy': 300},
        'muon_1000': {'particle': 'mu-', 'energy': 1000},
    }
    
    try:
        benchmark = ParticleComparisonBenchmark(args.photonsim)
        benchmark.run_comparison_suite(particles_config, args.events, args.runs)
        benchmark.print_comparison_summary()
        benchmark.save_results(args.output)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()