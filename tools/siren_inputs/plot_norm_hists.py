#!/usr/bin/env python3
"""Visualise PhotonHist_AngleDistanceNorm across a grid of energies.

Walks <input-dir>/<material>/<particle>/<E>MeV/photonsim.root, reads
PhotonHist_AngleDistanceNorm (opening angle × s/s_max), and writes one PNG
per particle with a row of energy subpanels — a quick eyeball of how the
Cherenkov cone shape evolves once the distance axis is normalised by the
parametrised s_max.

Designed for inspecting scan_siren_inputs.py output. Host-native
(uproot + numpy + matplotlib).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import uproot


HIST_NAME = "PhotonHist_AngleDistanceNorm"
CELL_DIR_RE = re.compile(r"^(\d+)MeV$")


def discover_cells(root: Path, materials: list[str] | None,
                   particles: list[str] | None,
                   energies: list[int] | None) -> dict[tuple[str, str], dict[int, Path]]:
    """{(material, particle): {energy_mev: root_path, ...}}"""
    out: dict[tuple[str, str], dict[int, Path]] = {}
    if not root.exists():
        return out
    for material_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        if materials and material_dir.name not in materials:
            continue
        for particle_dir in sorted(p for p in material_dir.iterdir() if p.is_dir()):
            if particles and particle_dir.name not in particles:
                continue
            for energy_dir in sorted(particle_dir.iterdir()):
                m = CELL_DIR_RE.match(energy_dir.name)
                if not m:
                    continue
                e = int(m.group(1))
                if energies and e not in energies:
                    continue
                rf = energy_dir / "photonsim.root"
                if rf.exists() and rf.stat().st_size > 0:
                    out.setdefault((material_dir.name, particle_dir.name), {})[e] = rf
    return out


def plot_particle_grid(material: str, particle: str,
                       cells: dict[int, Path], out_path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm

    energies = sorted(cells.keys())
    n = len(energies)
    ncols = min(5, n)
    nrows = (n + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols,
                             figsize=(3.0 * ncols, 2.8 * nrows),
                             squeeze=False, sharex=True, sharey=True)

    # First pass: read everything to set a shared colour scale.
    panels = []
    vmin, vmax = np.inf, 0.0
    for e in energies:
        with uproot.open(cells[e]) as f:
            if HIST_NAME not in f:
                panels.append((e, None, None, None))
                continue
            counts, xedges, yedges = f[HIST_NAME].to_numpy()
            entries = counts.sum()
            panels.append((e, counts, xedges, yedges))
            positive = counts[counts > 0]
            if positive.size:
                vmin = min(vmin, float(positive.min()))
                vmax = max(vmax, float(positive.max()))
    if not np.isfinite(vmin) or vmax == 0:
        plt.close(fig)
        return
    norm = LogNorm(vmin=max(vmin, 1.0), vmax=vmax)

    im = None
    for i, (e, counts, xedges, yedges) in enumerate(panels):
        ax = axes[i // ncols][i % ncols]
        if counts is None:
            ax.set_title(f"{e} MeV — missing")
            continue
        im = ax.pcolormesh(xedges, yedges, counts.T, norm=norm,
                           cmap="viridis", shading="auto")
        ax.set_title(f"{e} MeV  ({counts.sum():.2g} γ)", fontsize=9)
        ax.set_xlim(0, np.pi)
        ax.set_ylim(0, 1)

    # Shared axis labels
    for c in range(ncols):
        axes[nrows - 1][c].set_xlabel("opening angle [rad]")
    for r in range(nrows):
        axes[r][0].set_ylabel("s / s_max")

    # Hide unused panels
    for j in range(n, nrows * ncols):
        axes[j // ncols][j % ncols].set_visible(False)

    if im is not None:
        fig.colorbar(im, ax=axes, fraction=0.025, pad=0.02, label="photons / bin")

    fig.suptitle(f"PhotonHist_AngleDistanceNorm — {particle} in {material}",
                 y=1.0)
    fig.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input-dir", type=Path,
                   default=Path("/Users/cjesus/Desktop/INTERM/OUTPUT/siren_inputs"),
                   help="Root of scan_siren_inputs.py output (default: %(default)s).")
    p.add_argument("--output-dir", type=Path, default=None,
                   help="Where to write the PNGs (default: --input-dir).")
    p.add_argument("--materials", nargs="+", default=None)
    p.add_argument("--particles", nargs="+", default=None)
    p.add_argument("--energies", nargs="+", type=int, default=None,
                   help="Restrict to these energies (MeV).")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.input_dir.exists():
        print(f"error: input-dir does not exist: {args.input_dir}", file=sys.stderr)
        return 2
    out_dir = args.output_dir or args.input_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    cells = discover_cells(args.input_dir, args.materials, args.particles, args.energies)
    if not cells:
        print("error: no cells found matching filters", file=sys.stderr)
        return 1

    for (material, particle), per_e in sorted(cells.items()):
        out_path = out_dir / f"angle_distance_norm_{material}_{particle}.png"
        plot_particle_grid(material, particle, per_e, out_path)
        print(f"wrote {out_path}  ({len(per_e)} energies)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
