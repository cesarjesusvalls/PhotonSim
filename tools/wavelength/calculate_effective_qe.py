#!/usr/bin/env python3
"""
Calculate effective quantum efficiency for SK and HK detectors
based on photon wavelength distribution from PhotonSim.

The effective QE is calculated as:
    QE_eff = Sum(N(λ) * QE(λ)) / Sum(N(λ))

where N(λ) is the number of photons at wavelength λ from the simulation,
and QE(λ) is the quantum efficiency at that wavelength.
"""

import numpy as np
import argparse
from pathlib import Path

try:
    import ROOT
except ImportError:
    print("Error: ROOT module not found. Make sure PyROOT is installed.")
    exit(1)


def load_qe_data(csv_file):
    """Load quantum efficiency data from CSV file."""
    data = np.loadtxt(csv_file, delimiter=',')
    wavelength = data[:, 0]  # nm
    qe = data[:, 1]  # percentage
    return wavelength, qe


def get_wavelength_histogram(root_file):
    """Extract wavelength histogram from ROOT file."""
    f = ROOT.TFile.Open(root_file, "READ")
    if not f or f.IsZombie():
        raise RuntimeError(f"Cannot open ROOT file: {root_file}")

    hist = f.Get("PhotonHist_Wavelength")
    if not hist:
        raise RuntimeError("PhotonHist_Wavelength not found in ROOT file")

    # Extract histogram data
    nbins = hist.GetNbinsX()
    wavelengths = []
    counts = []

    for i in range(1, nbins + 1):
        wavelengths.append(hist.GetBinCenter(i))
        counts.append(hist.GetBinContent(i))

    f.Close()

    return np.array(wavelengths), np.array(counts)


def interpolate_qe(wavelength_bins, qe_wavelength, qe_values):
    """Interpolate QE values to match histogram wavelength bins."""
    # Use linear interpolation, set QE=0 outside the measured range
    qe_interp = np.interp(wavelength_bins, qe_wavelength, qe_values,
                          left=0.0, right=0.0)
    return qe_interp


def calculate_effective_qe(wavelengths, counts, qe_wavelength, qe_values):
    """Calculate effective quantum efficiency."""
    # Interpolate QE to histogram bins
    qe_interp = interpolate_qe(wavelengths, qe_wavelength, qe_values)

    # Calculate weighted average: QE_eff = Sum(N * QE) / Sum(N)
    weighted_sum = np.sum(counts * qe_interp)
    total_counts = np.sum(counts)

    if total_counts == 0:
        return 0.0, 0.0

    effective_qe = weighted_sum / total_counts

    return effective_qe, total_counts


def main():
    parser = argparse.ArgumentParser(
        description="Calculate effective quantum efficiency from wavelength histogram"
    )
    parser.add_argument(
        "--root-file",
        type=str,
        default="test_wavelength_5_events.root",
        help="ROOT file containing wavelength histogram (default: test_wavelength_5_events.root)"
    )
    parser.add_argument(
        "--hk-qe",
        type=str,
        default="HK_QE.csv",
        help="CSV file with HK quantum efficiency data (default: HK_QE.csv)"
    )
    parser.add_argument(
        "--sk-qe",
        type=str,
        default="SK_QE.csv",
        help="CSV file with SK quantum efficiency data (default: SK_QE.csv)"
    )

    args = parser.parse_args()

    # Get wavelength histogram from ROOT file
    print(f"Reading wavelength histogram from: {args.root_file}")
    wavelengths, counts = get_wavelength_histogram(args.root_file)
    total_photons = int(np.sum(counts))
    print(f"Total photons in histogram: {total_photons:,}")
    print(f"Wavelength range: {wavelengths.min():.1f} - {wavelengths.max():.1f} nm")
    print()

    # Load QE data
    print(f"Loading HK QE data from: {args.hk_qe}")
    hk_wavelength, hk_qe = load_qe_data(args.hk_qe)
    print(f"HK QE wavelength range: {hk_wavelength.min():.1f} - {hk_wavelength.max():.1f} nm")

    print(f"Loading SK QE data from: {args.sk_qe}")
    sk_wavelength, sk_qe = load_qe_data(args.sk_qe)
    print(f"SK QE wavelength range: {sk_wavelength.min():.1f} - {sk_wavelength.max():.1f} nm")
    print()

    # Calculate effective QE for HK
    hk_eff_qe, _ = calculate_effective_qe(wavelengths, counts, hk_wavelength, hk_qe)

    # Calculate effective QE for SK
    sk_eff_qe, _ = calculate_effective_qe(wavelengths, counts, sk_wavelength, sk_qe)

    # Display results
    print("=" * 60)
    print("EFFECTIVE QUANTUM EFFICIENCY RESULTS")
    print("=" * 60)
    print(f"HK Effective QE: {hk_eff_qe:.3f}%")
    print(f"SK Effective QE: {sk_eff_qe:.3f}%")
    print(f"HK/SK Ratio:     {hk_eff_qe/sk_eff_qe:.3f}" if sk_eff_qe > 0 else "HK/SK Ratio:     N/A")
    print("=" * 60)


if __name__ == "__main__":
    main()
