#!/usr/bin/env python3
"""Fit the t0 (vertex-time) parametrisation from a PhotonSim energy scan
and write LUCiD's ``data/<material>/<particle>/t0.json``.

Schema: ``stretched_exp_delay_v1``

    t(d, E) = d / c + A(E) · (exp((d / λ(E))^β(E)) − 1)

with

    log10 A(E) = cA + mA · log10 E
    log10 λ(E) = cL + mL · log10 E
    β(E)       = bB0 + bB1 · log10 E + bB2 · (log10 E)²

Inputs: per-energy ROOT files containing ``PhotonHist_TimeDistanceNorm``
(2D hist of s/s_max vs delay = t − d/c, populated only when
``/output/smax`` is set in the macro). The per-energy ``s_max(E)`` used
to convert the histogram x-axis back to physical distance is read from
``PhotonSim/data/<material>/<particle>/smax_fit.csv`` — same source the
macros bake in.

Outputs (written to the scan directory):
    timing_parameters.json   — the seven trend params
    pred_vs_data.png         — all-energies overlay, data + per-E fit
    trends.png               — A(E), λ(E), β(E) with their fit lines

If ``--lucid-data`` is given, also installs the JSON at
``<lucid-data>/<material>/<particle>/t0.json`` so LUCiD picks it up
directly.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import uproot
from scipy.optimize import curve_fit

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from generate_energy_scan_macros import _load_smax_row, _eval_smax  # noqa: E402


C_MM_PER_NS = 299.792
PHOTON_CUM_FRAC = 0.99            # u-axis trim — drop the sparse range-out tail
MIN_D_MM = 50.0                   # ignore the few-mm region (degenerate)
ENERGY_FROM_NAME = re.compile(r"muons_(\d+)MeV")


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

def stretched_exp(d, A, lam, beta):
    """delay(d) = A · (exp((d/λ)^β) − 1).  Passes through (0, 0)."""
    arg = np.power(np.clip(d / lam, 1e-12, None), beta)
    return A * (np.exp(arg) - 1.0)


def trend_predict(E, params):
    """Evaluate (A, λ, β) at energy E from the trend params dict."""
    le = np.log10(E)
    A = 10.0 ** (params["A"]["log10_intercept"] +
                 params["A"]["log10_slope_logE"] * le)
    lam = 10.0 ** (params["lambda"]["log10_intercept"] +
                   params["lambda"]["log10_slope_logE"] * le)
    beta = (params["beta"]["const"]
            + params["beta"]["slope_logE"] * le
            + params["beta"]["slope_logE_sq"] * le * le)
    return A, lam, beta


# ---------------------------------------------------------------------------
# Input loading
# ---------------------------------------------------------------------------

def discover_scan_files(scan_dir: Path):
    """Return [(E_MeV, path), ...] sorted by energy."""
    out = []
    for fp in scan_dir.glob("muons_*MeV_*.root"):
        m = ENERGY_FROM_NAME.search(fp.name)
        if m is None:
            continue
        out.append((int(m.group(1)), fp))
    out.sort()
    return out


def load_profile(root_path: Path, smax_mm: float):
    """Return (d_mm, delay_mean_ns) per u-bin, with the 99% cumulative cut."""
    with uproot.open(root_path) as f:
        if "PhotonHist_TimeDistanceNorm" not in f:
            raise KeyError(f"{root_path.name}: PhotonHist_TimeDistanceNorm "
                           "missing — did /output/smax get set?")
        h = f["PhotonHist_TimeDistanceNorm"]
        vals = h.values()
        u = h.axis(0).centers()
        delay_axis = h.axis(1).centers()
    counts = vals.sum(axis=1)
    total = counts.sum()
    if total == 0:
        raise ValueError(f"{root_path.name}: hist is empty.")
    with np.errstate(invalid="ignore", divide="ignore"):
        delay_mean = (vals * delay_axis[None, :]).sum(axis=1) / counts
    cum = np.cumsum(counts) / total
    keep = (cum <= PHOTON_CUM_FRAC) & (counts > 0)
    d_mm = u[keep] * smax_mm
    return d_mm, delay_mean[keep]


# ---------------------------------------------------------------------------
# Fits
# ---------------------------------------------------------------------------

def fit_per_energy(profiles):
    """Stage 1: independent (A, λ, β) per energy."""
    out = []
    for entry in profiles:
        d, y = entry["d"], entry["delay"]
        keep = d > MIN_D_MM
        lam0 = max(d[keep].max() / 4.0, 100.0)
        popt, _ = curve_fit(
            stretched_exp, d[keep], y[keep],
            p0=[0.01, lam0, 1.0],
            bounds=([1e-9, 1.0, 0.2], [1.0, 1e6, 5.0]),
            maxfev=50000,
        )
        rms = float(np.sqrt(np.mean(
            (y[keep] - stretched_exp(d[keep], *popt)) ** 2)))
        out.append({"E": entry["E"], "popt": popt, "rms_ns": rms})
    return out


def fit_trends(per_energy):
    """Stage 2: power-law for A, λ; quadratic-in-logE for β."""
    Es = np.array([r["E"] for r in per_energy])
    A  = np.array([r["popt"][0] for r in per_energy])
    L  = np.array([r["popt"][1] for r in per_energy])
    B  = np.array([r["popt"][2] for r in per_energy])
    logE = np.log10(Es)
    mA, cA = np.polyfit(logE, np.log10(A), 1)
    mL, cL = np.polyfit(logE, np.log10(L), 1)
    bB2, bB1, bB0 = np.polyfit(logE, B, 2)
    return {
        "A":      {"log10_intercept": float(cA), "log10_slope_logE": float(mA)},
        "lambda": {"log10_intercept": float(cL), "log10_slope_logE": float(mL)},
        "beta":   {"const": float(bB0),
                   "slope_logE": float(bB1),
                   "slope_logE_sq": float(bB2)},
    }


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def plot_pred_vs_data(profiles, per_energy, out_path: Path):
    """All energies overlay: data (points) + per-energy fit (lines)."""
    colors = plt.cm.viridis(np.linspace(0.05, 0.95, len(profiles)))
    fig, ax = plt.subplots(figsize=(10, 6))
    for c, p, r in zip(colors, profiles, per_energy):
        d = p["d"]
        ax.plot(d / 1000.0, p["delay"], "o", color=c, ms=2.0, alpha=0.4,
                label=f"{p['E']} MeV")
        d_grid = np.linspace(d.min(), d.max(), 300)
        ax.plot(d_grid / 1000.0, stretched_exp(d_grid, *r["popt"]),
                "-", color=c, lw=2.8)
    ax.axhline(0, color="grey", lw=0.4)
    ax.set_xlabel("physical distance d (m)")
    ax.set_ylabel(r"delay  $t - d/c$  (ns)")
    ax.set_title("Per-energy stretched-exp fit:  "
                 r"delay$(d) = A \cdot (e^{(d/\lambda)^\beta} - 1)$"
                 "\npoints = data, lines = fit")
    ax.legend(fontsize=9, loc="upper left")
    ax.set_xlim(0, None)
    fig.tight_layout()
    fig.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)


def plot_trends(per_energy, trends, out_path: Path):
    """A(E), λ(E), β(E) with trend lines overlaid."""
    Es = np.array([r["E"] for r in per_energy])
    A  = np.array([r["popt"][0] for r in per_energy])
    L  = np.array([r["popt"][1] for r in per_energy])
    B  = np.array([r["popt"][2] for r in per_energy])
    Egrid = np.logspace(np.log10(Es.min()), np.log10(Es.max()), 200)
    A_t, L_t, B_t = trend_predict(Egrid, trends)
    cA, mA = trends["A"]["log10_intercept"], trends["A"]["log10_slope_logE"]
    cL, mL = trends["lambda"]["log10_intercept"], trends["lambda"]["log10_slope_logE"]
    bB0, bB1, bB2 = (trends["beta"]["const"],
                     trends["beta"]["slope_logE"],
                     trends["beta"]["slope_logE_sq"])

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))
    axes[0].loglog(Es, A, "o", color="k", label="per-E fit")
    axes[0].loglog(Egrid, A_t, "-", color="tab:red",
                   label=f"log A = {cA:.3f} + {mA:.3f}·logE")
    axes[0].set_ylabel("A (ns)")
    axes[1].loglog(Es, L, "o", color="k", label="per-E fit")
    axes[1].loglog(Egrid, L_t, "-", color="tab:red",
                   label=f"log λ = {cL:.3f} + {mL:.3f}·logE")
    axes[1].set_ylabel("λ (mm)")
    axes[2].semilogx(Es, B, "o", color="k", label="per-E fit")
    axes[2].semilogx(Egrid, B_t, "-", color="tab:red",
                     label=f"β = {bB0:.2f}{bB1:+.2f}·logE{bB2:+.3f}·logE²")
    axes[2].set_ylabel("β")
    for ax in axes:
        ax.set_xlabel("E (MeV)")
        ax.legend(fontsize=9)
        ax.grid(True, which="both", alpha=0.3)
    fig.suptitle("Stage-2 trends of stretched-exp params", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# JSON output
# ---------------------------------------------------------------------------

def build_t0_json(trends, particle, material, per_energy, scan_dir):
    return {
        "form": "stretched_exp_delay_v1",
        "description": ("t(d, E) = d/c + A(E)*(exp((d/lambda(E))^beta(E)) - 1)"
                        "  -- d in mm, E in MeV, t in ns."),
        "particle": particle,
        "material": material,
        "c_mm_per_ns": C_MM_PER_NS,
        "A": trends["A"],
        "lambda": trends["lambda"],
        "beta": trends["beta"],
        "provenance": {
            "source": "PhotonSim/tools/t0_correction/calculate_t0.py",
            "scan_dir": str(scan_dir),
            "n_energies": len(per_energy),
            "energy_range_mev": [int(min(r["E"] for r in per_energy)),
                                 int(max(r["E"] for r in per_energy))],
        },
        "per_energy_fits": [
            {"energy_mev": int(r["E"]),
             "A_ns": float(r["popt"][0]),
             "lambda_mm": float(r["popt"][1]),
             "beta": float(r["popt"][2]),
             "rms_ps": float(r["rms_ns"] * 1000)}
            for r in per_energy
        ],
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scan_dir", type=Path,
                    help="Directory of PhotonSim ROOT files (muons_*MeV_*.root)")
    ap.add_argument("--material", default="water")
    ap.add_argument("--particle", default="mu-",
                    help="PhotonSim particle name (used to look up smax_fit.csv)")
    ap.add_argument("--smax-data-dir", type=Path,
                    default=HERE.parent.parent / "data",
                    help="PhotonSim/data root (contains <material>/<particle>/smax_fit.csv)")
    ap.add_argument("--lucid-data", type=Path,
                    help="LUCiD/data root; if set, installs t0.json at "
                         "<lucid-data>/<material>/<lucid-particle>/t0.json")
    ap.add_argument("--lucid-particle", default="muon",
                    help="LUCiD particle directory (mu- -> muon)")
    args = ap.parse_args()

    files = discover_scan_files(args.scan_dir)
    if not files:
        print(f"No ROOT files found in {args.scan_dir}", file=sys.stderr)
        sys.exit(1)
    print(f"Discovered {len(files)} energies: "
          f"{files[0][0]} - {files[-1][0]} MeV")

    smax_row, _ = _load_smax_row(args.smax_data_dir, args.material, args.particle)
    profiles = []
    for E, fp in files:
        smax = _eval_smax(smax_row, E)
        try:
            d_mm, delay = load_profile(fp, smax)
        except (KeyError, ValueError) as exc:
            print(f"  skip {E} MeV: {exc}")
            continue
        profiles.append({"E": E, "d": d_mm, "delay": delay, "smax_mm": smax})

    per_energy = fit_per_energy(profiles)
    print("\nStage 1 — per-energy fits:")
    for r in per_energy:
        A, lam, beta = r["popt"]
        print(f"  {r['E']:5d} MeV: A={A:.4g} ns, λ={lam:7.1f} mm, "
              f"β={beta:.3f},  RMS={r['rms_ns']*1000:5.2f} ps")

    trends = fit_trends(per_energy)
    print(f"\nStage 2 — trends:")
    print(f"  log A      = {trends['A']['log10_intercept']:+.4f} "
          f"+ {trends['A']['log10_slope_logE']:+.4f} · logE")
    print(f"  log lambda = {trends['lambda']['log10_intercept']:+.4f} "
          f"+ {trends['lambda']['log10_slope_logE']:+.4f} · logE")
    print(f"  beta       = {trends['beta']['const']:+.4f} "
          f"+ {trends['beta']['slope_logE']:+.4f}·logE "
          f"+ {trends['beta']['slope_logE_sq']:+.4f}·logE²")

    # Stitched RMS (trend-evaluated, not per-energy)
    print("\nStitched-trend residuals per energy:")
    for entry, r in zip(profiles, per_energy):
        A, lam, beta = trend_predict(entry["E"], trends)
        pred = stretched_exp(entry["d"], A, lam, beta)
        rms = float(np.sqrt(np.mean((entry["delay"] - pred) ** 2)))
        print(f"  {r['E']:5d} MeV: trend-RMS = {rms*1000:5.1f} ps  "
              f"(direct = {r['rms_ns']*1000:5.1f} ps)")

    blob = build_t0_json(trends, args.particle, args.material,
                         per_energy, args.scan_dir)
    out_json = args.scan_dir / "timing_parameters.json"
    out_json.write_text(json.dumps(blob, indent=4))
    print(f"\nWrote {out_json}")

    if args.lucid_data is not None:
        lucid_path = args.lucid_data / args.material / args.lucid_particle / "t0.json"
        lucid_path.parent.mkdir(parents=True, exist_ok=True)
        lucid_path.write_text(json.dumps(blob, indent=4))
        print(f"Installed at {lucid_path}")

    plot_pred_vs_data(profiles, per_energy, args.scan_dir / "pred_vs_data.png")
    plot_trends(per_energy, trends, args.scan_dir / "trends.png")
    print(f"Saved {args.scan_dir / 'pred_vs_data.png'}")
    print(f"Saved {args.scan_dir / 'trends.png'}")


if __name__ == "__main__":
    main()
