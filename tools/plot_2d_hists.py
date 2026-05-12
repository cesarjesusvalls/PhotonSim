#!/usr/bin/env python3
"""Plot every TH2D in a PhotonSim ROOT file with a log-intensity colormap.

Auto-discovers all TH2D keys, reads bin contents + axis titles via uproot,
renders one subpanel per histogram into a single PNG. Useful as a quick
"what's in this file?" inspection — works on any PhotonSim output (smax
parametrisation scan, SIREN-input scan, or one-off macros).

Single-file mode:
    plot_2d_hists.py /path/to/photonsim.root [-o out.png]

Tree mode: pass a directory and it walks <dir>/<material>/<particle>/<E>MeV/
producing one PNG per cell.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import uproot


CELL_DIR_RE = re.compile(r"^(\d+)MeV$")


def _axis_titles(hist) -> tuple[str, str]:
    """Pull axis titles out of the TAxis members (uproot exposes them)."""
    try:
        xt = hist.member("fXaxis").member("fTitle") or ""
        yt = hist.member("fYaxis").member("fTitle") or ""
    except Exception:
        xt, yt = "", ""
    return xt, yt


def _find_th2d(file) -> list[tuple[str, object]]:
    """List (name, hist) for every TH2D at the top level of `file`."""
    out: list[tuple[str, object]] = []
    for key in file.keys():
        obj = file[key]
        if getattr(obj, "classname", "") == "TH2D":
            out.append((key.split(";")[0], obj))
    return out


def plot_file(root_path: Path, out_path: Path) -> bool:
    """Render every TH2D in `root_path` into `out_path`. Returns True on success."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm

    with uproot.open(root_path) as f:
        hists = _find_th2d(f)
        if not hists:
            print(f"warn: no TH2D in {root_path}", file=sys.stderr)
            return False

        ncols = min(2, len(hists))
        nrows = (len(hists) + ncols - 1) // ncols
        fig, axes = plt.subplots(nrows, ncols,
                                 figsize=(6.5 * ncols, 5.0 * nrows),
                                 squeeze=False)

        for i, (name, hist) in enumerate(hists):
            ax = axes[i // ncols][i % ncols]
            counts, xedges, yedges = hist.to_numpy()
            positive = counts[counts > 0]
            if not positive.size:
                ax.set_title(f"{name} (empty)", fontsize=10)
                ax.set_xticks([]); ax.set_yticks([])
                continue
            vmin = max(1.0, float(positive.min()))
            vmax = float(positive.max())
            im = ax.pcolormesh(xedges, yedges, counts.T,
                               norm=LogNorm(vmin=vmin, vmax=vmax),
                               cmap="viridis", shading="auto")
            xt, yt = _axis_titles(hist)
            ax.set_xlabel(xt or "X")
            ax.set_ylabel(yt or "Y")
            ax.set_title(f"{name}  ({counts.sum():.3g} entries)", fontsize=10)
            fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03,
                         label="counts / bin")

        for j in range(len(hists), nrows * ncols):
            axes[j // ncols][j % ncols].set_visible(False)

        fig.suptitle(str(root_path), fontsize=10, y=1.0)
        fig.tight_layout()
        fig.savefig(out_path, dpi=130, bbox_inches="tight")
        plt.close(fig)
        return True


def discover_cells(root: Path) -> list[Path]:
    """Walk <root>/<material>/<particle>/<E>MeV/photonsim.root."""
    out: list[Path] = []
    if not root.is_dir():
        return out
    for material_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        for particle_dir in sorted(p for p in material_dir.iterdir() if p.is_dir()):
            for energy_dir in sorted(particle_dir.iterdir()):
                if not CELL_DIR_RE.match(energy_dir.name):
                    continue
                rf = energy_dir / "photonsim.root"
                if rf.exists() and rf.stat().st_size > 0:
                    out.append(rf)
    return out


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input", type=Path,
                   help="A .root file (single-file mode) or a directory tree "
                        "rooted at <material>/<particle>/<E>MeV/ (tree mode).")
    p.add_argument("-o", "--output", type=Path, default=None,
                   help="Single-file mode: output PNG path "
                        "(default: <input>.png next to the ROOT file). "
                        "Tree mode: output directory (default: --input).")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    # If input doesn't exist, treat as tree mode: create the directory so the
    # next scan can drop files into it, and exit cleanly with "0 cells".
    if not args.input.exists():
        if args.input.suffix == ".root":
            print(f"error: input file does not exist: {args.input}", file=sys.stderr)
            return 2
        args.input.mkdir(parents=True, exist_ok=True)
        print(f"created empty input dir: {args.input}", file=sys.stderr)

    if args.input.is_file():
        out_path = args.output or args.input.with_suffix(".png")
        ok = plot_file(args.input, out_path)
        if ok:
            print(f"wrote {out_path}", file=sys.stderr)
        return 0 if ok else 1

    out_dir = args.output or args.input
    out_dir.mkdir(parents=True, exist_ok=True)
    cells = discover_cells(args.input)
    if not cells:
        print(f"no PhotonSim cells under {args.input} (nothing to plot)",
              file=sys.stderr)
        return 0
    n_ok = 0
    for rf in cells:
        # Mirror the <material>/<particle>/<E>MeV/ layout in the output dir.
        rel = rf.relative_to(args.input).parent
        out_path = out_dir / f"{rel.as_posix().replace('/', '_')}.png"
        if plot_file(rf, out_path):
            n_ok += 1
            print(f"wrote {out_path}", file=sys.stderr)
    print(f"\n{n_ok} / {len(cells)} cells plotted", file=sys.stderr)
    return 0 if n_ok else 1


if __name__ == "__main__":
    sys.exit(main())
