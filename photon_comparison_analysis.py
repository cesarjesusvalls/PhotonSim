#!/usr/bin/env python3

import ROOT
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import pandas as pd

def extract_data(filename, particle_type):
    """Extract energy and photon count data from ROOT file"""
    file_root = ROOT.TFile(filename, 'READ')
    tree = file_root.Get('OpticalPhotons')
    
    energies = []
    photon_counts = []
    
    print(f"Processing {particle_type} file: {filename}")
    print(f"Total events: {tree.GetEntries()}")
    
    for i in range(tree.GetEntries()):
        tree.GetEntry(i)
        energy = tree.PrimaryEnergy  # Primary particle energy in MeV
        n_photons = tree.NOpticalPhotons  # Number of optical photons
        
        energies.append(energy)
        photon_counts.append(n_photons)
    
    file_root.Close()
    
    return np.array(energies), np.array(photon_counts)

def create_binned_analysis(energies, photon_counts, particle_type, n_bins=20, energy_range=(500, 1500)):
    """Create binned analysis for energy vs photon count"""
    
    # Create energy bins
    bin_edges = np.linspace(energy_range[0], energy_range[1], n_bins + 1)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    
    # Initialize arrays for binned data
    avg_photons = []
    std_photons = []
    bin_counts = []
    
    for i in range(n_bins):
        # Find events in this energy bin
        mask = (energies >= bin_edges[i]) & (energies < bin_edges[i+1])
        bin_photons = photon_counts[mask]
        
        if len(bin_photons) > 0:
            avg_photons.append(np.mean(bin_photons))
            std_photons.append(np.std(bin_photons))
            bin_counts.append(len(bin_photons))
        else:
            avg_photons.append(0)
            std_photons.append(0)
            bin_counts.append(0)
    
    return bin_centers, np.array(avg_photons), np.array(std_photons), np.array(bin_counts)

def linear_fit(x, a, b):
    """Linear fitting function"""
    return a * x + b

def polynomial_fit(x, a, b, c):
    """Quadratic fitting function"""  
    return a * x**2 + b * x + c

def fit_trend(energies, photon_counts, fit_type='linear'):
    """Fit trend to the data"""
    
    # Only use bins with data
    valid_mask = photon_counts > 0
    x_data = energies[valid_mask]
    y_data = photon_counts[valid_mask]
    
    if fit_type == 'linear':
        popt, pcov = curve_fit(linear_fit, x_data, y_data)
        fit_func = linear_fit
        fit_label = f'Linear: y = {popt[0]:.3f}x + {popt[1]:.1f}'
    elif fit_type == 'polynomial':
        popt, pcov = curve_fit(polynomial_fit, x_data, y_data)
        fit_func = polynomial_fit
        fit_label = f'Quadratic: y = {popt[0]:.6f}x² + {popt[1]:.3f}x + {popt[2]:.1f}'
    
    return popt, pcov, fit_func, fit_label

def find_equivalent_energy(electron_fit_params, electron_fit_func, muon_fit_params, muon_fit_func, target_energy=1000):
    """Find muon energy that gives same photon yield as target electron energy"""
    
    # Calculate photon yield for target electron energy
    target_photons = electron_fit_func(target_energy, *electron_fit_params)
    
    print(f"\nFor {target_energy} MeV electron:")
    print(f"Expected photon yield: {target_photons:.1f}")
    
    # Find muon energy that gives same photon yield
    # For linear fits: solve muon_a * E_mu + muon_b = target_photons
    if len(muon_fit_params) == 2:  # linear fit
        a_mu, b_mu = muon_fit_params
        equivalent_muon_energy = (target_photons - b_mu) / a_mu
    else:  # quadratic fit  
        a_mu, b_mu, c_mu = muon_fit_params
        # Solve quadratic: a*E^2 + b*E + c - target_photons = 0
        discriminant = b_mu**2 - 4*a_mu*(c_mu - target_photons)
        if discriminant >= 0:
            equivalent_muon_energy = (-b_mu + np.sqrt(discriminant)) / (2*a_mu)
        else:
            equivalent_muon_energy = float('nan')
    
    return equivalent_muon_energy, target_photons

def main():
    # Extract data from both files
    print("Extracting data from ROOT files...")
    electron_energies, electron_photons = extract_data('elec_gun_100_events_uniform_energy.root', 'Electron')
    muon_energies, muon_photons = extract_data('muon_gun_100_events_uniform_energy.root', 'Muon')
    
    print(f"\nElectron data: {len(electron_energies)} events")
    print(f"Energy range: {electron_energies.min():.1f} - {electron_energies.max():.1f} MeV")
    print(f"Photon range: {electron_photons.min()} - {electron_photons.max()}")
    
    print(f"\nMuon data: {len(muon_energies)} events") 
    print(f"Energy range: {muon_energies.min():.1f} - {muon_energies.max():.1f} MeV")
    print(f"Photon range: {muon_photons.min()} - {muon_photons.max()}")
    
    # Create binned analysis
    print("\nCreating binned analysis...")
    e_bins, e_avg, e_std, e_counts = create_binned_analysis(electron_energies, electron_photons, 'Electron')
    m_bins, m_avg, m_std, m_counts = create_binned_analysis(muon_energies, muon_photons, 'Muon')
    
    # Print some statistics
    print(f"\nElectron bins with data: {np.sum(e_counts > 0)}/20")
    print(f"Muon bins with data: {np.sum(m_counts > 0)}/20")
    
    # Fit trends (try both linear and polynomial)
    print("\nFitting trends...")
    
    # Try linear fits first
    e_fit_linear, e_cov_linear, e_func_linear, e_label_linear = fit_trend(e_bins, e_avg, 'linear')
    m_fit_linear, m_cov_linear, m_func_linear, m_label_linear = fit_trend(m_bins, m_avg, 'linear')
    
    # Try polynomial fits
    e_fit_poly, e_cov_poly, e_func_poly, e_label_poly = fit_trend(e_bins, e_avg, 'polynomial')
    m_fit_poly, m_cov_poly, m_func_poly, m_label_poly = fit_trend(m_bins, m_avg, 'polynomial')
    
    print(f"Electron linear fit: {e_label_linear}")
    print(f"Muon linear fit: {m_label_linear}")
    print(f"Electron polynomial fit: {e_label_poly}")
    print(f"Muon polynomial fit: {m_label_poly}")
    
    # Create the comparison plot
    plt.figure(figsize=(12, 8))
    
    # Plot raw data points
    plt.scatter(electron_energies, electron_photons, alpha=0.5, color='blue', s=20, label='Electron events')
    plt.scatter(muon_energies, muon_photons, alpha=0.5, color='red', s=20, label='Muon events')
    
    # Plot binned averages with error bars
    valid_e = e_avg > 0
    valid_m = m_avg > 0
    
    plt.errorbar(e_bins[valid_e], e_avg[valid_e], yerr=e_std[valid_e], 
                fmt='o', color='blue', markersize=8, capsize=5, label='Electron (binned avg)')
    plt.errorbar(m_bins[valid_m], m_avg[valid_m], yerr=m_std[valid_m], 
                fmt='s', color='red', markersize=8, capsize=5, label='Muon (binned avg)')
    
    # Plot fitted curves
    x_fit = np.linspace(500, 1500, 200)
    plt.plot(x_fit, e_func_linear(x_fit, *e_fit_linear), 'b--', linewidth=2, label=f'Electron: {e_label_linear}')
    plt.plot(x_fit, m_func_linear(x_fit, *m_fit_linear), 'r--', linewidth=2, label=f'Muon: {m_label_linear}')
    
    # Find equivalent energies
    equiv_energy, target_photons = find_equivalent_energy(e_fit_linear, e_func_linear, 
                                                         m_fit_linear, m_func_linear, 1000)
    
    # Mark the equivalent point
    plt.axvline(x=1000, color='blue', linestyle=':', alpha=0.7, label=f'1 GeV electron')
    plt.axvline(x=equiv_energy, color='red', linestyle=':', alpha=0.7, 
               label=f'Equivalent muon: {equiv_energy:.0f} MeV')
    plt.axhline(y=target_photons, color='gray', linestyle=':', alpha=0.5)
    
    plt.xlabel('Primary Particle Energy (MeV)', fontsize=12)
    plt.ylabel('Number of Optical Photons', fontsize=12)
    plt.title('Optical Photon Yield vs Primary Particle Energy', fontsize=14)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, alpha=0.3)
    plt.xlim(450, 1550)
    
    plt.tight_layout()
    plt.savefig('photon_comparison_plot.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Print final results
    print(f"\n{'='*60}")
    print("FINAL RESULTS")
    print(f"{'='*60}")
    print(f"1 GeV electron produces: {target_photons:.1f} optical photons")
    print(f"Equivalent muon energy: {equiv_energy:.1f} MeV")
    print(f"Equivalent muon produces: {m_func_linear(equiv_energy, *m_fit_linear):.1f} optical photons")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()