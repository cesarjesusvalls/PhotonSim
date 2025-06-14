#!/usr/bin/env python3
"""
PhotonSim Benchmark Visualization Tool
Creates plots to analyze runtime performance vs event count.
"""

import json
import argparse
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

def load_benchmark_data(file_path):
    """Load benchmark results from JSON file."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

def plot_runtime_vs_events(data, output_dir='.'):
    """Plot runtime vs number of events."""
    results = data['results']
    
    if not results:
        print("No results to plot.")
        return
    
    events = [r['events'] for r in results]
    avg_times = [r['avg_runtime'] for r in results]
    min_times = [r['min_runtime'] for r in results]
    max_times = [r['max_runtime'] for r in results]
    
    plt.figure(figsize=(12, 8))
    
    # Plot with error bars
    plt.errorbar(events, avg_times, 
                yerr=[np.array(avg_times) - np.array(min_times),
                      np.array(max_times) - np.array(avg_times)],
                fmt='o-', capsize=5, capthick=2, label='Runtime')
    
    plt.xlabel('Number of Events')
    plt.ylabel('Runtime (seconds)')
    plt.title('PhotonSim Runtime vs Number of Events')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Add data labels
    for i, (x, y) in enumerate(zip(events, avg_times)):
        plt.annotate(f'{y:.2f}s', (x, y), textcoords="offset points", 
                    xytext=(0,10), ha='center', fontsize=9)
    
    plt.tight_layout()
    output_path = Path(output_dir) / 'runtime_vs_events.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Runtime plot saved to: {output_path}")
    plt.show()

def plot_throughput_analysis(data, output_dir='.'):
    """Plot events per second and scaling efficiency."""
    results = data['results']
    
    if not results:
        print("No results to plot.")
        return
    
    events = [r['events'] for r in results]
    avg_times = [r['avg_runtime'] for r in results]
    events_per_sec = [e/t for e, t in zip(events, avg_times)]
    
    # Calculate scaling efficiency (events/sec relative to single event)
    baseline_rate = events_per_sec[0] if events_per_sec else 1
    scaling_efficiency = [eps/baseline_rate for eps in events_per_sec]
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Events per second
    ax1.plot(events, events_per_sec, 'o-', linewidth=2, markersize=8, color='blue')
    ax1.set_xlabel('Number of Events')
    ax1.set_ylabel('Events per Second')
    ax1.set_title('PhotonSim Throughput')
    ax1.grid(True, alpha=0.3)
    
    # Add data labels
    for x, y in zip(events, events_per_sec):
        ax1.annotate(f'{y:.1f}', (x, y), textcoords="offset points", 
                    xytext=(0,10), ha='center', fontsize=9)
    
    # Scaling efficiency
    ax2.plot(events, scaling_efficiency, 'o-', linewidth=2, markersize=8, color='red')
    ax2.axhline(y=1.0, color='gray', linestyle='--', alpha=0.7, label='Linear scaling')
    ax2.set_xlabel('Number of Events')
    ax2.set_ylabel('Scaling Factor')
    ax2.set_title('Scaling Efficiency (relative to 1 event)')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # Add data labels
    for x, y in zip(events, scaling_efficiency):
        ax2.annotate(f'{y:.2f}x', (x, y), textcoords="offset points", 
                    xytext=(0,10), ha='center', fontsize=9)
    
    plt.tight_layout()
    output_path = Path(output_dir) / 'throughput_analysis.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Throughput analysis plot saved to: {output_path}")
    plt.show()

def plot_overhead_analysis(data, output_dir='.'):
    """Analyze initialization overhead vs simulation time."""
    results = data['results']
    
    if len(results) < 2:
        print("Need at least 2 data points for overhead analysis.")
        return
    
    events = np.array([r['events'] for r in results])
    avg_times = np.array([r['avg_runtime'] for r in results])
    
    # Fit linear model: time = overhead + rate * events
    # Using least squares: [1, events] * [overhead, rate] = times
    A = np.column_stack([np.ones(len(events)), events])
    coeffs = np.linalg.lstsq(A, avg_times, rcond=None)[0]
    overhead, rate = coeffs
    
    # Calculate R-squared
    predicted_times = overhead + rate * events
    ss_res = np.sum((avg_times - predicted_times) ** 2)
    ss_tot = np.sum((avg_times - np.mean(avg_times)) ** 2)
    r_squared = 1 - (ss_res / ss_tot)
    
    plt.figure(figsize=(12, 8))
    
    # Plot data points
    plt.plot(events, avg_times, 'o', markersize=8, label='Measured times', color='blue')
    
    # Plot linear fit
    fit_events = np.linspace(0, max(events), 100)
    fit_times = overhead + rate * fit_events
    plt.plot(fit_events, fit_times, '--', linewidth=2, 
             label=f'Linear fit (R² = {r_squared:.3f})', color='red')
    
    plt.xlabel('Number of Events')
    plt.ylabel('Runtime (seconds)')
    plt.title('PhotonSim Runtime Analysis\n' + 
              f'Overhead: {overhead:.3f}s, Rate: {rate:.4f}s/event')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Add annotations
    textstr = f'Initialization overhead: {overhead:.3f}s\\n'
    textstr += f'Time per event: {rate:.4f}s\\n'
    textstr += f'Events per second: {1/rate:.1f}\\n'
    textstr += f'R-squared: {r_squared:.3f}'
    
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    plt.text(0.02, 0.98, textstr, transform=plt.gca().transAxes, fontsize=10,
             verticalalignment='top', bbox=props)
    
    plt.tight_layout()
    output_path = Path(output_dir) / 'overhead_analysis.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Overhead analysis plot saved to: {output_path}")
    plt.show()

def print_performance_summary(data):
    """Print detailed performance analysis."""
    results = data['results']
    
    if not results:
        print("No results to analyze.")
        return
    
    print("=== Performance Analysis Summary ===")
    print(f"Total test points: {len(results)}")
    print()
    
    events = np.array([r['events'] for r in results])
    avg_times = np.array([r['avg_runtime'] for r in results])
    events_per_sec = events / avg_times
    
    # Linear fit for overhead analysis
    if len(results) >= 2:
        A = np.column_stack([np.ones(len(events)), events])
        coeffs = np.linalg.lstsq(A, avg_times, rcond=None)[0]
        overhead, rate = coeffs
        
        print(f"Initialization overhead: {overhead:.3f} seconds")
        print(f"Time per event: {rate:.4f} seconds")
        print(f"Theoretical max throughput: {1/rate:.1f} events/second")
        print()
    
    print("Detailed Results:")
    print(f"{'Events':>8} {'Time (s)':>10} {'Events/s':>10} {'Efficiency':>12}")
    print("-" * 45)
    
    baseline_rate = events_per_sec[0] if len(events_per_sec) > 0 else 1
    
    for result in results:
        e = result['events']
        t = result['avg_runtime']
        eps = e / t
        eff = eps / baseline_rate
        print(f"{e:>8} {t:>10.3f} {eps:>10.1f} {eff:>12.3f}")

def main():
    parser = argparse.ArgumentParser(description='Visualize PhotonSim benchmark results')
    parser.add_argument('input_file', help='Benchmark results JSON file')
    parser.add_argument('--output-dir', '-o', default='.', 
                       help='Output directory for plots')
    parser.add_argument('--no-plots', action='store_true',
                       help='Only print summary, no plots')
    
    args = parser.parse_args()
    
    try:
        # Check if matplotlib is available
        if not args.no_plots:
            try:
                import matplotlib.pyplot as plt
            except ImportError:
                print("Warning: matplotlib not available, only printing summary")
                args.no_plots = True
        
        data = load_benchmark_data(args.input_file)
        
        print_performance_summary(data)
        print()
        
        if not args.no_plots:
            output_dir = Path(args.output_dir)
            output_dir.mkdir(exist_ok=True)
            
            plot_runtime_vs_events(data, output_dir)
            plot_throughput_analysis(data, output_dir)
            plot_overhead_analysis(data, output_dir)
        
    except FileNotFoundError:
        print(f"Error: Benchmark file not found: {args.input_file}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()