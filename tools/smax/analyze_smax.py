#!/usr/bin/env python3
"""Summarise PhotonHist_Distance across a scan_smax.py output tree.

Walks <output-dir>/<material>/<particle>/<E>MeV/photonsim.root, reads the
1D s = |emission - vertex| histogram, and emits:

  * a text table (mean, configurable quantile, s_max proxy) to stdout
  * an optional CSV with the same columns
  * an optional log-log plot of s_max(E) and the quantile per particle

"s_max" here is the upper edge of the last non-empty bin — i.e. the
farthest Cherenkov emission point from the primary vertex actually
observed in the scan, at 1 cm bin resolution. The quantile is the natural
robust replacement when tails are sparse.

Host-native (uproot + numpy + matplotlib). No Docker. Works against either
the new scan_smax.py layout or any sibling tree that has
`<material>/<particle>/<E>MeV/*.root` cells with a `PhotonHist_Distance`
TH1D inside.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import uproot


HIST_NAME = "PhotonHist_Distance"
CELL_DIR_RE = re.compile(r"^(\d+)MeV$")

# Where per-(material, particle) parametrization CSVs are written by default.
# Resolves to <repo>/PhotonSim/data when run from PhotonSim/tools/smax/.
DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "data"

# Energy below which a particle is excluded from the linear s_max(E) fit —
# basically a per-particle Cherenkov-threshold floor. Particles missing from
# this dict default to no threshold (all points eligible).
DEFAULT_FIT_MIN_MEV = {
    "mu-":   500, "mu+":   500,
    "pi-":   500, "pi+":   500,
    "proton": 5000,
    # 10 MeV e± is too close to threshold + range-limited to give a clean
    # point on the shower-extent curve; start the fit at 100 MeV.
    "e-": 100, "e+": 100,
    "gamma": 0,
}

# Detector is a 1 km cube (default in DetectorConstruction.hh). A particle
# fired from origin along +Z can travel at most 500 m before exiting, so
# s_max values within `sat_frac` of that ceiling are geometry-limited and
# excluded from the fit.
WORLD_HALF_MM = 500_000.0
GEOMETRY_SAT_FRAC = 0.95


@dataclass
class CellStat:
    material: str
    particle: str
    energy_mev: int
    entries: float
    mean_mm: float
    quantile_mm: float
    smax_mm: float
    n_events: int | None  # optional; from Events tree if present
    counts: np.ndarray | None = None  # full PhotonHist_Distance bin counts
    edges: np.ndarray | None = None   # bin edges (len == nbins + 1)


def discover_cells(root: Path) -> list[Path]:
    """Return every .../<material>/<particle>/<E>MeV/photonsim.root."""
    cells: list[Path] = []
    for material_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        for particle_dir in sorted(p for p in material_dir.iterdir() if p.is_dir()):
            for energy_dir in sorted(particle_dir.iterdir()):
                if not energy_dir.is_dir():
                    continue
                if not CELL_DIR_RE.match(energy_dir.name):
                    continue
                rf = energy_dir / "photonsim.root"
                if rf.exists() and rf.stat().st_size > 0:
                    cells.append(rf)
    return cells


def analyse_cell(root_path: Path, quantile: float) -> CellStat:
    energy_mev = int(CELL_DIR_RE.match(root_path.parent.name).group(1))
    particle = root_path.parent.parent.name
    material = root_path.parent.parent.parent.name

    with uproot.open(root_path) as f:
        if HIST_NAME not in f:
            raise KeyError(f"{HIST_NAME} missing in {root_path}")
        h = f[HIST_NAME]
        counts, edges = h.to_numpy()       # counts: nbins, edges: nbins+1
        centers = 0.5 * (edges[:-1] + edges[1:])
        total = counts.sum()

        if total == 0:
            return CellStat(material, particle, energy_mev,
                            entries=0.0, mean_mm=float("nan"),
                            quantile_mm=float("nan"), smax_mm=float("nan"),
                            n_events=_event_count(f),
                            counts=counts, edges=edges)

        mean_mm = float(np.average(centers, weights=counts))

        # Quantile via cumulative distribution on bin upper edges — robust
        # against the wide range / sparse-tail regime of the s distribution.
        cdf = np.cumsum(counts) / total
        q_idx = int(np.searchsorted(cdf, quantile))
        q_idx = min(q_idx, len(edges) - 2)
        quantile_mm = float(edges[q_idx + 1])

        last_nonzero = int(np.nonzero(counts)[0][-1])
        smax_mm = float(edges[last_nonzero + 1])

        return CellStat(material, particle, energy_mev,
                        entries=float(total), mean_mm=mean_mm,
                        quantile_mm=quantile_mm, smax_mm=smax_mm,
                        n_events=_event_count(f),
                        counts=counts, edges=edges)


def _event_count(f) -> int | None:
    """Best-effort: pull event count from the Events TTree if present."""
    for key in ("Events", "OpticalPhotons"):
        if key in f:
            try:
                return int(f[key].num_entries)
            except Exception:
                pass
    return None


def print_table(stats: list[CellStat], quantile: float, out=sys.stdout) -> None:
    q_pct = f"{quantile*100:.1f}".rstrip("0").rstrip(".")
    header = (f"{'material':<10s} {'particle':<8s} {'E [MeV]':>8s} "
              f"{'events':>7s} {'entries':>12s} "
              f"{'mean s [mm]':>14s} {f'{q_pct}% s [mm]':>14s} "
              f"{'s_max [mm]':>12s}")
    print(header, file=out)
    print("-" * len(header), file=out)
    for s in stats:
        ev = f"{s.n_events:>7d}" if s.n_events is not None else f"{'?':>7s}"
        print(f"{s.material:<10s} {s.particle:<8s} {s.energy_mev:>8d} "
              f"{ev} {s.entries:>12.0f} "
              f"{s.mean_mm:>14.0f} {s.quantile_mm:>14.0f} "
              f"{s.smax_mm:>12.0f}", file=out)


def write_parametrization(stats: list[CellStat],
                          fits: dict[tuple[str, str], PowerLawFit],
                          data_dir: Path,
                          quantile: float, quantile_multiplier: float,
                          world_half_mm: float, sat_frac: float) -> list[Path]:
    """Write per-(material, particle) parametrization CSVs to data_dir.

    Layout:
        <data_dir>/<material>/<particle>/smax_data.csv   per-energy table
        <data_dir>/<material>/<particle>/smax_fit.csv    1-row fit metadata

    Two files instead of one keeps the table easy to consume row-by-row
    and the fit metadata easy to parse without sniffing for header rows.
    """
    from datetime import datetime, timezone
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    written: list[Path] = []
    by_pm = _group_by_pm(stats)
    for (material, particle), rows in sorted(by_pm.items()):
        cell_dir = data_dir / material / particle
        cell_dir.mkdir(parents=True, exist_ok=True)

        data_path = cell_dir / "smax_data.csv"
        with data_path.open("w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["energy_mev", "n_events", "entries",
                        "mean_mm", "quantile_mm", "quantile_eff_mm",
                        "smax_mm", "below_fit_threshold",
                        "geometry_saturated"])
            fit = fits.get((material, particle))
            threshold = (DEFAULT_FIT_MIN_MEV.get(particle, 0)
                         if fit is None else fit.e_min_mev)
            for r in sorted(rows, key=lambda r: r.energy_mev):
                q_eff = (r.quantile_mm * quantile_multiplier
                         if np.isfinite(r.quantile_mm) else float("nan"))
                sat = (np.isfinite(r.smax_mm)
                       and r.smax_mm >= sat_frac * world_half_mm)
                w.writerow([
                    r.energy_mev,
                    r.n_events if r.n_events is not None else "",
                    f"{r.entries:.0f}",
                    "" if not np.isfinite(r.mean_mm) else f"{r.mean_mm:.3f}",
                    "" if not np.isfinite(r.quantile_mm) else f"{r.quantile_mm:.3f}",
                    "" if not np.isfinite(q_eff) else f"{q_eff:.3f}",
                    "" if not np.isfinite(r.smax_mm) else f"{r.smax_mm:.3f}",
                    int(r.energy_mev < threshold),
                    int(bool(sat)),
                ])
        written.append(data_path)

        fit_path = cell_dir / "smax_fit.csv"
        with fit_path.open("w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["material", "particle", "form",
                        "A", "B",
                        "fit_min_mev", "fit_max_mev",
                        "n_used", "n_excluded_low", "n_excluded_saturated",
                        "quantile", "quantile_multiplier",
                        "min_fit_to_quantile_ratio", "min_ratio_e_mev",
                        "generated_at_utc"])
            if fit is None:
                w.writerow([material, particle, "", "", "", "", "", "", "",
                            "", quantile, quantile_multiplier, "", "",
                            generated_at])
            else:
                chk = check_fit_above_quantile(rows, fit)
                w.writerow([
                    material, particle, "A*E^B",
                    f"{fit.A:.6f}", f"{fit.B:.6f}",
                    fit.e_min_mev, fit.e_max_mev,
                    fit.n_used, fit.n_excluded_low, fit.n_excluded_saturated,
                    quantile, quantile_multiplier,
                    "" if chk.n_compared == 0 else f"{chk.min_ratio:.4f}",
                    "" if chk.n_compared == 0 else chk.min_ratio_energy_mev,
                    generated_at,
                ])
        written.append(fit_path)
    return written


def write_csv(stats: list[CellStat], path: Path, quantile: float) -> None:
    with path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["material", "particle", "energy_mev", "n_events",
                    "entries", "mean_mm",
                    f"q{quantile:.4f}_mm", "smax_mm"])
        for s in stats:
            w.writerow([s.material, s.particle, s.energy_mev,
                        s.n_events if s.n_events is not None else "",
                        f"{s.entries:.0f}", f"{s.mean_mm:.3f}",
                        f"{s.quantile_mm:.3f}", f"{s.smax_mm:.3f}"])


def _group_by_pm(stats: list[CellStat]) -> dict[tuple[str, str], list[CellStat]]:
    by_pm: dict[tuple[str, str], list[CellStat]] = {}
    for s in stats:
        by_pm.setdefault((s.material, s.particle), []).append(s)
    for rows in by_pm.values():
        rows.sort(key=lambda r: r.energy_mev)
    return by_pm


@dataclass
class PowerLawFit:
    """Power-law fit s_max ≈ A · E^B (least squares in log-log space).

    A is the prefactor with units of mm · MeV^(-B); B is the exponent.
    Linear in log-log means a straight line on the existing plot axes.
    """
    A: float
    B: float
    n_used: int
    e_min_mev: int
    e_max_mev: int
    n_excluded_low: int
    n_excluded_saturated: int

    def eval(self, energy_mev: np.ndarray | float) -> np.ndarray | float:
        return self.A * np.asarray(energy_mev) ** self.B


def _eligible_for_fit(rows: list[CellStat], min_mev: int,
                      world_half_mm: float, sat_frac: float) -> list[CellStat]:
    keep: list[CellStat] = []
    for r in rows:
        if r.energy_mev < min_mev:
            continue
        if not np.isfinite(r.smax_mm):
            continue
        if r.smax_mm >= sat_frac * world_half_mm:
            continue
        keep.append(r)
    return keep


@dataclass
class FitQuantileCheck:
    """Diagnostic: where does the fit sit relative to the 99% quantile?

    The fit is meant to bound the bulk of the Cherenkov emission. If
    `min_ratio < 1` the fit underestimates the quantile somewhere → the
    parametrization would clip real photons.
    """
    n_compared: int
    min_ratio: float
    min_ratio_energy_mev: int
    max_ratio: float
    violations: list[tuple[int, float, float]]  # (E, fit, q) where fit < q


def check_fit_above_quantile(rows: list[CellStat], fit: PowerLawFit) -> FitQuantileCheck:
    """Compare fit to quantile only for points the fit was actually trained on
    (E ≥ fit.e_min_mev). Sub-threshold rows are pure extrapolation, where it
    is OK and expected for the fit to drop below the local quantile."""
    ratios: list[tuple[int, float, float]] = []
    violations: list[tuple[int, float, float]] = []
    for r in rows:
        if r.energy_mev < fit.e_min_mev:
            continue
        if not np.isfinite(r.quantile_mm) or r.quantile_mm <= 0:
            continue
        f = float(fit.eval(r.energy_mev))
        ratios.append((r.energy_mev, f, r.quantile_mm))
        if f < r.quantile_mm:
            violations.append((r.energy_mev, f, r.quantile_mm))
    if not ratios:
        return FitQuantileCheck(0, float("nan"), 0, float("nan"), [])
    rmin_idx = min(range(len(ratios)), key=lambda i: ratios[i][1] / ratios[i][2])
    rmax_idx = max(range(len(ratios)), key=lambda i: ratios[i][1] / ratios[i][2])
    e_min, f_min, q_min = ratios[rmin_idx]
    e_max, f_max, q_max = ratios[rmax_idx]
    return FitQuantileCheck(
        n_compared=len(ratios),
        min_ratio=f_min / q_min,
        min_ratio_energy_mev=e_min,
        max_ratio=f_max / q_max,
        violations=violations,
    )


def fit_smax(rows: list[CellStat], particle: str,
             quantile_multiplier: float,
             fit_min_overrides: dict[str, int] | None = None,
             world_half_mm: float = WORLD_HALF_MM,
             sat_frac: float = GEOMETRY_SAT_FRAC) -> PowerLawFit | None:
    """Power-law fit (linear in log-log) of the *effective* s_max target,
    quantile · quantile_multiplier (the bound that defines `s/s_max ≤ 1`
    downstream). Uses points with E ≥ per-particle threshold and not
    geometry-saturated. Returns None if fewer than 2 points survive."""
    threshold = (fit_min_overrides or {}).get(particle,
                  DEFAULT_FIT_MIN_MEV.get(particle, 0))
    n_low = sum(1 for r in rows if r.energy_mev < threshold)
    keep = _eligible_for_fit(rows, threshold, world_half_mm, sat_frac)
    n_sat = sum(1 for r in rows
                if r.energy_mev >= threshold and np.isfinite(r.smax_mm)
                and r.smax_mm >= sat_frac * world_half_mm)
    # Need a finite, positive quantile to take logs.
    keep = [r for r in keep
            if np.isfinite(r.quantile_mm) and r.quantile_mm > 0]
    if len(keep) < 2:
        return None
    E = np.array([r.energy_mev for r in keep], dtype=float)
    y = np.array([r.quantile_mm * quantile_multiplier for r in keep], dtype=float)
    B, logA = np.polyfit(np.log(E), np.log(y), 1)
    return PowerLawFit(A=float(np.exp(logA)), B=float(B),
                       n_used=len(keep), e_min_mev=int(E.min()), e_max_mev=int(E.max()),
                       n_excluded_low=n_low, n_excluded_saturated=n_sat)


def _group_by_material(stats: list[CellStat]) -> dict[str, dict[str, list[CellStat]]]:
    """{material: {particle: [rows sorted by E, ...]}}"""
    out: dict[str, dict[str, list[CellStat]]] = {}
    for s in stats:
        out.setdefault(s.material, {}).setdefault(s.particle, []).append(s)
    for parts in out.values():
        for rows in parts.values():
            rows.sort(key=lambda r: r.energy_mev)
    return out


def _grid_layout(n: int) -> tuple[int, int]:
    """Pick (nrows, ncols) for n subpanels — favour ≤3 columns for legibility."""
    if n <= 1:
        return 1, 1
    if n <= 4:
        return (n + 1) // 2, 2
    ncols = 3
    nrows = (n + ncols - 1) // ncols
    return nrows, ncols


def _draw_smax_panel(ax, rows: list[CellStat], particle: str, material: str,
                     quantile: float, quantile_multiplier: float,
                     fit: PowerLawFit | None) -> None:
    E = np.array([r.energy_mev for r in rows])
    smax = np.array([r.smax_mm for r in rows])
    q = np.array([r.quantile_mm for r in rows])
    q_eff = q * quantile_multiplier
    ax.plot(E, smax, "o-", color="C0", lw=1.8, ms=5, label="s_max", zorder=5)
    ax.plot(E, q, "x--", color="C0", lw=1.0, ms=5,
            label=f"{quantile*100:g}% quantile", zorder=4)
    ax.plot(E, q_eff, "s:", color="C0", lw=1.4, ms=4,
            label=f"{quantile*100:g}% × {quantile_multiplier:g}", zorder=4)
    if fit is not None:
        xs = np.geomspace(fit.e_min_mev, fit.e_max_mev, 64)
        ax.plot(xs, fit.eval(xs), "-", color="crimson", lw=2.2, zorder=10,
                label=f"fit: {fit.A:.3g}·E^{fit.B:.3f}")
        valid_E = E[np.isfinite(smax)]
        if len(valid_E) and float(valid_E.min()) < fit.e_min_mev:
            xs_ex = np.geomspace(float(valid_E.min()), fit.e_min_mev, 32)
            ax.plot(xs_ex, fit.eval(xs_ex), "--", color="crimson",
                    lw=1.8, alpha=0.85, zorder=9, label="fit (extrap.)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("E [MeV]")
    ax.set_ylabel("s [mm]")
    ax.set_title(f"{particle} in {material}")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(fontsize=8, loc="lower right")


def plot_smax_vs_energy(stats: list[CellStat], output_dir: Path,
                        quantile: float, quantile_multiplier: float,
                        fits: dict[tuple[str, str], PowerLawFit] | None = None
                        ) -> list[Path]:
    """One figure per material, one subpanel per particle.

    Returns the list of files written.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    written: list[Path] = []
    by_mat = _group_by_material(stats)
    for material, particles in sorted(by_mat.items()):
        names = sorted(particles.keys())
        nrows, ncols = _grid_layout(len(names))
        fig, axes = plt.subplots(nrows, ncols,
                                 figsize=(4.8 * ncols, 3.8 * nrows),
                                 squeeze=False)
        for i, particle in enumerate(names):
            ax = axes[i // ncols][i % ncols]
            fit = (fits or {}).get((material, particle))
            _draw_smax_panel(ax, particles[particle], particle, material,
                             quantile, quantile_multiplier, fit)
        for j in range(len(names), nrows * ncols):
            axes[j // ncols][j % ncols].set_visible(False)
        fig.suptitle(f"Cherenkov emission s_max(E) — {material}", y=1.0)
        fig.tight_layout()
        path = output_dir / f"smax_vs_energy_{material}.png"
        fig.savefig(path, dpi=130)
        plt.close(fig)
        written.append(path)
    return written


def plot_distributions(stats: list[CellStat], output_dir: Path) -> list[Path]:
    """One figure per material, one subpanel per particle. Each subpanel
    overlays the per-energy PhotonHist_Distance, viridis-coloured by E."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.cm import viridis
    from matplotlib.colors import LogNorm

    written: list[Path] = []
    by_mat = _group_by_material(stats)
    for material, particles in sorted(by_mat.items()):
        names = sorted(particles.keys())
        nrows, ncols = _grid_layout(len(names))
        fig, axes = plt.subplots(nrows, ncols,
                                 figsize=(5.5 * ncols, 3.8 * nrows),
                                 squeeze=False)
        # Shared colormap across panels so the legend reads consistently.
        all_rows = [r for rows in particles.values() for r in rows]
        e_min = min(r.energy_mev for r in all_rows)
        e_max = max(r.energy_mev for r in all_rows)
        norm = LogNorm(vmin=max(e_min, 1), vmax=e_max)

        for i, particle in enumerate(names):
            ax = axes[i // ncols][i % ncols]
            x_max = 0.0
            for r in particles[particle]:
                if r.counts is None or r.edges is None or not r.counts.sum():
                    continue
                centers = 0.5 * (r.edges[:-1] + r.edges[1:])
                mask = r.counts > 0
                ax.step(centers[mask], r.counts[mask], where="mid",
                        color=viridis(norm(r.energy_mev)), lw=1.0,
                        label=f"{r.energy_mev} MeV")
                if np.isfinite(r.smax_mm):
                    x_max = max(x_max, r.smax_mm)
            ax.set_xlim(0, x_max * 1.05 if x_max else None)
            ax.set_yscale("log")
            ax.set_xlabel("s = |emission - vertex|  [mm]")
            ax.set_ylabel("photons / bin")
            ax.set_title(f"{particle} in {material}")
            ax.grid(True, which="both", alpha=0.25)
            ax.legend(fontsize=7, loc="upper right", ncol=2)

        for j in range(len(names), nrows * ncols):
            axes[j // ncols][j % ncols].set_visible(False)
        fig.suptitle(f"PhotonHist_Distance — {material}", y=1.0)
        fig.tight_layout()
        path = output_dir / f"s_distributions_{material}.png"
        fig.savefig(path, dpi=130)
        plt.close(fig)
        written.append(path)
    return written


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument(
        "--output-dir", type=Path,
        default=Path("/Users/cjesus/Desktop/INTERM/OUTPUT/smax"),
        help="Root of the scan_smax.py output tree.",
    )
    p.add_argument("--materials", nargs="+", default=None,
                   help="Restrict to these materials (default: all found).")
    p.add_argument("--particles", nargs="+", default=None,
                   help="Restrict to these particles (default: all found).")
    p.add_argument("--quantile", type=float, default=0.999,
                   help="Quantile used as the fit target (default: 0.999). "
                        "5× stats per cell give 10–10⁵ photons in the 0.1 %% "
                        "tail, plenty for a stable per-bin quantile.")
    p.add_argument("--quantile-multiplier", type=float, default=1.1,
                   help="Multiplier applied to the quantile to produce the "
                        "'effective s_max' that the fit targets (default: 1.1).")
    p.add_argument("--csv", type=Path, default=None,
                   help="Optional CSV output path (default: <output-dir>/smax_summary.csv).")
    p.add_argument("--plots-dir", type=Path, default=None,
                   help="Directory for per-material PNGs (default: --output-dir). "
                        "Files written: smax_vs_energy_<material>.png and "
                        "s_distributions_<material>.png per material.")
    p.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR,
                   help="Root for per-particle parametrization CSVs "
                        "(default: PhotonSim/data, alongside this script).")
    p.add_argument("--no-csv", action="store_true", help="Skip summary CSV.")
    p.add_argument("--no-data-export", action="store_true",
                   help="Skip writing per-particle parametrization CSVs to --data-dir.")
    p.add_argument("--no-plot", action="store_true", help="Skip all plots.")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if not args.output_dir.exists():
        print(f"error: output-dir does not exist: {args.output_dir}", file=sys.stderr)
        return 2

    cells = discover_cells(args.output_dir)
    if args.materials:
        cells = [c for c in cells if c.parent.parent.parent.name in args.materials]
    if args.particles:
        cells = [c for c in cells if c.parent.parent.name in args.particles]
    if not cells:
        print(f"error: no cells found under {args.output_dir}", file=sys.stderr)
        return 1

    stats: list[CellStat] = []
    for rf in cells:
        try:
            stats.append(analyse_cell(rf, args.quantile))
        except Exception as exc:
            print(f"warn: skipping {rf}: {exc}", file=sys.stderr)
    if not stats:
        return 1

    stats.sort(key=lambda s: (s.material, s.particle, s.energy_mev))
    print_table(stats, args.quantile)

    # Per-(material, particle) linear fits, excluding sub-threshold and
    # geometry-saturated points.
    by_pm = _group_by_pm(stats)
    fits: dict[tuple[str, str], PowerLawFit] = {}
    print(f"\npower-law fits to effective s_max ({args.quantile*100:g}% × "
          f"{args.quantile_multiplier:g}) ≈ A · E^B  "
          f"(linear in log-log; E in MeV, s_max in mm):",
          file=sys.stderr)
    for (material, particle), rows in sorted(by_pm.items()):
        fit = fit_smax(rows, particle, args.quantile_multiplier)
        if fit is None:
            print(f"  {particle:<6s} / {material:<10s}  insufficient points",
                  file=sys.stderr)
            continue
        fits[(material, particle)] = fit
        notes = []
        if fit.n_excluded_low:
            notes.append(f"-{fit.n_excluded_low} sub-threshold")
        if fit.n_excluded_saturated:
            notes.append(f"-{fit.n_excluded_saturated} geom-saturated")
        note = (" [" + ", ".join(notes) + "]") if notes else ""
        print(f"  {particle:<6s} / {material:<10s}  "
              f"A = {fit.A:9.4f}   B = {fit.B:6.4f} "
              f"  n_fit={fit.n_used}  (E={fit.e_min_mev}–{fit.e_max_mev} MeV){note}",
              file=sys.stderr)

        # Validation: the fit should sit above the 99% quantile at every
        # measured E (including extrapolated ones) so it's a safe upper
        # bound for downstream parametrisation.
        chk = check_fit_above_quantile(rows, fit)
        if chk.n_compared == 0:
            continue
        if chk.violations:
            print(f"    ⚠ fit BELOW {args.quantile*100:g}% quantile at "
                  f"{len(chk.violations)} energ{'y' if len(chk.violations)==1 else 'ies'}:",
                  file=sys.stderr)
            for e, f_val, q_val in chk.violations:
                print(f"        E={e} MeV: fit={f_val:.0f} mm < q={q_val:.0f} mm "
                      f"(ratio {f_val/q_val:.3f})", file=sys.stderr)
        else:
            print(f"    fit ≥ {args.quantile*100:g}% quantile at all "
                  f"{chk.n_compared} measured points "
                  f"(min margin {chk.min_ratio:.2f}× at E={chk.min_ratio_energy_mev} MeV, "
                  f"max {chk.max_ratio:.2f}×)",
                  file=sys.stderr)

    if not args.no_csv:
        csv_path = args.csv or (args.output_dir / "smax_summary.csv")
        write_csv(stats, csv_path, args.quantile)
        print(f"\nwrote {csv_path}", file=sys.stderr)

    if not args.no_data_export:
        written = write_parametrization(
            stats, fits, args.data_dir,
            args.quantile, args.quantile_multiplier,
            WORLD_HALF_MM, GEOMETRY_SAT_FRAC)
        print(f"wrote {len(written)} parametrization file(s) under {args.data_dir}",
              file=sys.stderr)

    if not args.no_plot:
        plots_dir = args.plots_dir or args.output_dir
        plots_dir.mkdir(parents=True, exist_ok=True)
        for p in plot_smax_vs_energy(stats, plots_dir, args.quantile,
                                     args.quantile_multiplier, fits=fits):
            print(f"wrote {p}", file=sys.stderr)
        for p in plot_distributions(stats, plots_dir):
            print(f"wrote {p}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
