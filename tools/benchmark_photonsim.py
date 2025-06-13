#!/usr/bin/env python3
"""
PhotonSim Benchmark Tool
Measures runtime performance as a function of event count.
"""

import os
import sys
import time
import subprocess
import json
import argparse
from pathlib import Path
import tempfile

class PhotonSimBenchmark:
    def __init__(self, photonsim_path, base_mac_path):
        self.photonsim_path = Path(photonsim_path)
        self.base_mac_path = Path(base_mac_path)
        self.results = []
        
        if not self.photonsim_path.exists():
            raise FileNotFoundError(f"PhotonSim executable not found: {photonsim_path}")
        if not self.base_mac_path.exists():
            raise FileNotFoundError(f"Base macro file not found: {base_mac_path}")
    
    def create_test_macro(self, event_count, output_path):
        """Create a test macro with specified number of events."""
        with open(self.base_mac_path, 'r') as f:
            content = f.read()
        
        # Replace the beamOn command with new event count
        lines = content.split('\n')
        new_lines = []
        
        for line in lines:
            if line.strip().startswith('/run/beamOn'):
                new_lines.append(f'/run/beamOn {event_count}')
            else:
                new_lines.append(line)
        
        with open(output_path, 'w') as f:
            f.write('\n'.join(new_lines))
    
    def run_single_benchmark(self, event_count, runs=3):
        """Run PhotonSim with specified event count and measure runtime."""
        print(f"Benchmarking {event_count} events (averaging over {runs} runs)...")
        
        times = []
        
        for run in range(runs):
            # Create temporary macro file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.mac', delete=False) as f:
                temp_mac = f.name
            
            try:
                self.create_test_macro(event_count, temp_mac)
                
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
                'events': event_count,
                'avg_runtime': avg_time,
                'min_runtime': min_time,
                'max_runtime': max_time,
                'runs': len(times),
                'all_times': times
            }
            
            self.results.append(result_data)
            print(f"  Average: {avg_time:.3f}s (min: {min_time:.3f}s, max: {max_time:.3f}s)")
            return result_data
        else:
            print("  All runs failed!")
            return None
    
    def run_benchmark_suite(self, event_counts, runs_per_test=3):
        """Run benchmark suite with multiple event counts."""
        print("=== PhotonSim Performance Benchmark ===")
        print(f"PhotonSim executable: {self.photonsim_path}")
        print(f"Base macro: {self.base_mac_path}")
        print(f"Event counts to test: {event_counts}")
        print(f"Runs per test: {runs_per_test}")
        print()
        
        for event_count in event_counts:
            self.run_single_benchmark(event_count, runs_per_test)
            print()
    
    def save_results(self, output_file):
        """Save benchmark results to JSON file."""
        with open(output_file, 'w') as f:
            json.dump({
                'benchmark_info': {
                    'photonsim_path': str(self.photonsim_path),
                    'base_mac_path': str(self.base_mac_path),
                    'timestamp': time.time()
                },
                'results': self.results
            }, f, indent=2)
        print(f"Results saved to: {output_file}")
    
    def print_summary(self):
        """Print summary of benchmark results."""
        if not self.results:
            print("No results to summarize.")
            return
        
        print("=== Benchmark Summary ===")
        print(f"{'Events':>8} {'Avg Time (s)':>12} {'Events/s':>10} {'Scaling':>10}")
        print("-" * 45)
        
        baseline_rate = None
        
        for result in self.results:
            events = result['events']
            avg_time = result['avg_runtime']
            events_per_sec = events / avg_time
            
            if baseline_rate is None:
                baseline_rate = events_per_sec
                scaling = 1.0
            else:
                scaling = events_per_sec / baseline_rate
            
            print(f"{events:>8} {avg_time:>12.3f} {events_per_sec:>10.1f} {scaling:>10.3f}")


def main():
    parser = argparse.ArgumentParser(description='Benchmark PhotonSim performance')
    parser.add_argument('--photonsim', '-p', 
                       default='../build/PhotonSim',
                       help='Path to PhotonSim executable')
    parser.add_argument('--macro', '-m',
                       default='../macros/test_muon.mac',
                       help='Base macro file to use for benchmarking')
    parser.add_argument('--events', '-e', nargs='+', type=int,
                       default=[1, 5, 10, 25, 50, 100, 250, 500],
                       help='Event counts to benchmark')
    parser.add_argument('--runs', '-r', type=int, default=3,
                       help='Number of runs per event count')
    parser.add_argument('--output', '-o', default='benchmark_results.json',
                       help='Output file for results')
    
    args = parser.parse_args()
    
    try:
        benchmark = PhotonSimBenchmark(args.photonsim, args.macro)
        benchmark.run_benchmark_suite(args.events, args.runs)
        benchmark.print_summary()
        benchmark.save_results(args.output)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()