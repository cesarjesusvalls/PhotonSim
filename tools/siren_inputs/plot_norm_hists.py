#!/usr/bin/env python3
"""Visualise the SIREN-input *Norm histograms across a grid of energies.

Walks <input-dir>/<material>/<particle>/<E>MeV/photonsim.root, reads the
selected 2D histogram (defaults to PhotonHist_AngleDistanceNorm: opening
angle × s/s_max), and writes one PNG per particle with a row of energy
subpanels — a quick eyeball of how the Cherenkov cone shape (or dE/dx
profile) evolves once the distance axis is normalised by the
parametrised s_max.

Two histogram variants share the same s/s_max y-axis:

  --hist angle   PhotonHist_AngleDistanceNorm  (opening angle, default)
  --hist dedx    dEdxHist_DistanceNorm         (dE/dx in keV/mm)

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


# Hist-variant config. Each entry: (TKey in ROOT, x-axis label, output filename stem).
HIST_VARIANTS = {
    "angle": ("PhotonHist_AngleDistanceNorm", "opening angle [rad]",
              "angle_distance_norm"),
    "dedx":  ("dEdxHist_DistanceNorm",        "dE/dx [keV/mm]",
              "dedx_distance_norm"),
}
CELL_DIR_RE = re.compile(r"^(\d+)MeV$")


def discover_cells(root: Path, materials: list[str] | None,
                   particles: list[str] | None,
                   energies: list[int] | None,
                   hist_name: str = HIST_VARIANTS["angle"][0],
                   ) -> dict[tuple[str, str], dict[int, Path]]:
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


def _read_panels(cells: dict[int, Path], energies: list[int], hist_name: str):
    """Read histograms once; return (panels, vmin, vmax, xlim_max).

    Reading is the same cost whether we render in 1 figure or N, but we want
    a *shared* colour scale across all chunks of the same (material, particle)
    so panels are comparable. So we read everything up front.
    """
    panels = []
    vmin, vmax = np.inf, 0.0
    xlim_max = 0.0
    for e in energies:
        with uproot.open(cells[e]) as f:
            if hist_name not in f:
                panels.append((e, None, None, None))
                continue
            counts, xedges, yedges = f[hist_name].to_numpy()
            panels.append((e, counts, xedges, yedges))
            xlim_max = max(xlim_max, float(xedges[-1]))
            positive = counts[counts > 0]
            if positive.size:
                vmin = min(vmin, float(positive.min()))
                vmax = max(vmax, float(positive.max()))
    return panels, vmin, vmax, xlim_max


def _render_chunk(material: str, particle: str, hist_name: str, xlabel: str,
                  chunk: list, norm, xlim_max: float, out_path: Path,
                  page_idx: int, n_pages: int) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    n = len(chunk)
    ncols = min(5, n)
    nrows = (n + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols,
                             figsize=(3.0 * ncols, 2.8 * nrows),
                             squeeze=False, sharex=True, sharey=True)

    im = None
    for i, (e, counts, xedges, yedges) in enumerate(chunk):
        ax = axes[i // ncols][i % ncols]
        if counts is None:
            ax.set_title(f"{e} MeV — missing")
            continue
        im = ax.pcolormesh(xedges, yedges, counts.T, norm=norm,
                           cmap="viridis", shading="auto")
        ax.set_title(f"{e} MeV  ({counts.sum():.2g} entries)", fontsize=9)
        ax.set_xlim(0, xlim_max)
        ax.set_ylim(0, 1)

    for c in range(ncols):
        axes[nrows - 1][c].set_xlabel(xlabel)
    for r in range(nrows):
        axes[r][0].set_ylabel("s / s_max")

    for j in range(n, nrows * ncols):
        axes[j // ncols][j % ncols].set_visible(False)

    if im is not None:
        fig.colorbar(im, ax=axes, fraction=0.025, pad=0.02, label="entries / bin")

    suffix = f"  (page {page_idx + 1}/{n_pages})" if n_pages > 1 else ""
    fig.suptitle(f"{hist_name} — {particle} in {material}{suffix}", y=1.0)
    fig.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)


def plot_particle_grid(material: str, particle: str,
                       cells: dict[int, Path], out_stem_path: Path,
                       hist_name: str, xlabel: str,
                       max_panels_per_fig: int = 50) -> list[Path]:
    """Write one PNG per chunk of `max_panels_per_fig` cells.

    `out_stem_path` is the bare path without extension; for an N-page split
    we write `<stem>_p01.png ... <stem>_pNN.png`. With a single page we keep
    the simple `<stem>.png` name for backward compatibility.

    Returns the list of files written.
    """
    from matplotlib.colors import LogNorm

    energies = sorted(cells.keys())
    panels, vmin, vmax, xlim_max = _read_panels(cells, energies, hist_name)
    if not np.isfinite(vmin) or vmax == 0:
        return []
    norm = LogNorm(vmin=max(vmin, 1.0), vmax=vmax)

    chunks = [panels[i:i + max_panels_per_fig]
              for i in range(0, len(panels), max_panels_per_fig)]
    n_pages = len(chunks)
    written: list[Path] = []
    for idx, chunk in enumerate(chunks):
        if n_pages == 1:
            out_path = out_stem_path.with_suffix(".png")
        else:
            out_path = out_stem_path.with_name(
                f"{out_stem_path.name}_p{idx + 1:02d}.png")
        _render_chunk(material, particle, hist_name, xlabel,
                      chunk, norm, xlim_max, out_path, idx, n_pages)
        written.append(out_path)
    return written


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
    p.add_argument("--hist", choices=sorted(HIST_VARIANTS), default="angle",
                   help="Which Norm histogram to render. 'angle' = "
                        "PhotonHist_AngleDistanceNorm (default), 'dedx' = "
                        "dEdxHist_DistanceNorm.")
    p.add_argument("--max-panels-per-fig", type=int, default=50,
                   help="Split into multiple PNGs when the energy grid is "
                        "larger than this many cells (default: 50). "
                        "Each chunk uses the same colour scale so panels "
                        "remain visually comparable across pages.")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.input_dir.exists():
        print(f"error: input-dir does not exist: {args.input_dir}", file=sys.stderr)
        return 2
    out_dir = args.output_dir or args.input_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    hist_name, xlabel, out_stem = HIST_VARIANTS[args.hist]

    cells = discover_cells(args.input_dir, args.materials, args.particles,
                           args.energies, hist_name=hist_name)
    if not cells:
        print(f"error: no cells found matching filters (looking for {hist_name})",
              file=sys.stderr)
        return 1

    for (material, particle), per_e in sorted(cells.items()):
        out_stem_path = out_dir / f"{out_stem}_{material}_{particle}"
        written = plot_particle_grid(material, particle, per_e, out_stem_path,
                                      hist_name=hist_name, xlabel=xlabel,
                                      max_panels_per_fig=args.max_panels_per_fig)
        if not written:
            print(f"skip {material}/{particle}: empty histograms",
                  file=sys.stderr)
            continue
        for p in written:
            print(f"wrote {p}", file=sys.stderr)
        print(f"  ({len(per_e)} energies across {len(written)} page(s))",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
