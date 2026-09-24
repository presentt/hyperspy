"""Turn Esprit ASCII map exports into calibrated HyperSpy images and a montage.

This reproduces the MATLAB ``import_uxrf`` / ``img_proc_uxrf`` / ``uxrf_montage``
workflow in ``uxrf/matlab_reference/``:

* one ``<prefix>_<Element>.txt`` matrix of counts per element,
* pixel size typed in by hand (Esprit does not write it to the export),
* optional Gaussian blur (sigma in pixels) and min-max normalisation,
* a labelled grid of all maps with a scale bar.

Usage::

    python uxrf/recipes/02_esprit_ascii_to_signals.py "exports/Sample_*.txt" --pixel-size 20
    python uxrf/recipes/02_esprit_ascii_to_signals.py "exports/Sample_*.txt" --pixel-size 25 --blur 1.5 --normalise
    python uxrf/recipes/02_esprit_ascii_to_signals.py --demo      # synthetic data, no files needed

The functions can also be imported from a notebook::

    from importlib import import_module
    esprit = import_module("02_esprit_ascii_to_signals")   # with uxrf/recipes on sys.path
    maps = esprit.load_element_maps("exports/Sample_*.txt", pixel_size=20)
"""

import argparse
import glob
import re
import sys
import tempfile
from pathlib import Path

import numpy as np

# Esprit exports are plain text matrices; the delimiter varies with the locale
# and export dialog, so several are tried in order.
_DELIMITERS = (None, ",", ";", "\t")


def element_from_filename(path) -> str:
    """``'Sample 1_Ca.txt'`` -> ``'Ca'`` (text after the last underscore, spaces removed).

    Mirrors the MATLAB ``import_uxrf`` convention.
    """
    stem = Path(path).stem
    return stem.rsplit("_", 1)[-1].replace(" ", "")


def read_counts_matrix(path) -> np.ndarray:
    """Read one Esprit ASCII export as a 2-D float array (rows = y, columns = x)."""
    last_error = None
    for delimiter in _DELIMITERS:
        try:
            data = np.loadtxt(path, delimiter=delimiter, dtype=float, ndmin=2)
        except ValueError as err:  # wrong delimiter: try the next one
            last_error = err
            continue
        if data.ndim == 2 and data.shape[1] > 1:
            return data
    raise ValueError(f"Could not parse {path} as a 2-D matrix: {last_error}")


def counts_to_signal(counts, element, pixel_size, units="µm"):
    """Wrap a counts matrix in a calibrated ``Signal2D``.

    NumPy shape ``(ny, nx)`` displays in HyperSpy as ``(nx, ny)``; the
    ``signal_axes`` are set in display order (x first).
    """
    import hyperspy.api as hs

    s = hs.signals.Signal2D(counts)
    s.axes_manager.signal_axes.set(name=("x", "y"), scale=pixel_size, units=units)
    s.metadata.General.title = element
    s.metadata.set_item("Sample.elements", [element])
    s.metadata.set_item("Signal.quantity", "X-rays (Counts)")
    return s


def gaussian_blur(s, sigma):
    """Gaussian-blurred copy of a map (``sigma`` in pixels), like ``imgaussfilt``."""
    from scipy.ndimage import gaussian_filter

    blurred = s.map(gaussian_filter, sigma=sigma, inplace=False, show_progressbar=False)
    blurred.metadata.General.title = f"{s.metadata.General.title} blur {sigma:g}"
    return blurred


def normalise(s):
    """Stretch a map to the 0-1 range (min-max), like the MATLAB ``.norm`` field."""
    # Scalars come from .data because min()/max() with no navigation axes would
    # return the map unchanged rather than a single number.
    lo, hi = float(s.data.min()), float(s.data.max())
    out = (s - lo) / (hi - lo) if hi > lo else s - lo
    out.metadata.General.title = f"{s.metadata.General.title} norm"
    return out


def load_element_maps(pattern, pixel_size, units="µm", blur=None, normalised=False):
    """Load every export matching ``pattern`` into ``{element: Signal2D}``."""
    files = sorted(glob.glob(str(pattern)))
    if not files:
        raise FileNotFoundError(f"No files match {pattern!r}")
    maps = {}
    for path in files:
        element = element_from_filename(path)
        s = counts_to_signal(read_counts_matrix(path), element, pixel_size, units)
        if blur:
            s = gaussian_blur(s, blur)
        if normalised:
            s = normalise(s)
        maps[element] = s
    return maps


def stretch(s, low=1.0, high=99.0, gamma=1.0):
    """Percentile contrast stretch to 0-1 with optional gamma.

    Equivalent to MATLAB ``imadjust(img, stretchlim(img), [], gamma)``: values
    below the ``low`` percentile become 0, above ``high`` become 1, then the
    result is raised to ``gamma`` (``gamma`` < 1 brightens faint features).
    """
    lo, hi = np.percentile(s.data, [low, high])
    if hi <= lo:
        hi = lo + 1.0
    out = ((s - lo) / (hi - lo)).map(
        np.clip, a_min=0.0, a_max=1.0, inplace=False, show_progressbar=False
    )
    if gamma != 1.0:
        out = out**gamma
    out.metadata.General.title = s.metadata.General.title
    return out


def montage(maps, per_row=None, gamma=1.0, cmap="viridis", low=1.0, high=99.0):
    """Labelled grid of all maps with one scale bar, like ``uxrf_montage``.

    Each map is stretched between its ``low`` and ``high`` percentiles and
    gamma-adjusted before plotting, so the colour scale of every panel is 0-1.
    """
    import hyperspy.api as hs

    images = [stretch(s, low, high, gamma) for s in maps.values()]
    per_row = per_row or int(np.ceil(np.sqrt(len(images))))
    axes = hs.plot.plot_images(
        images,
        label=list(maps),
        per_row=per_row,
        axes_decor="off",
        scalebar=[0],
        colorbar=None,
        cmap=cmap,
        vmin=0.0,
        vmax=1.0,
        tight_layout=True,
    )
    return axes[0].figure


def write_demo_exports(folder, prefix="demo") -> str:
    """Write three synthetic Esprit-style exports and return the glob pattern.

    Dimensions are deliberately all different (37 rows x 52 columns) so any
    axis mix-up is visible.
    """
    rng = np.random.default_rng(0)
    ny, nx = 37, 52
    yy, xx = np.mgrid[0:ny, 0:nx]
    patterns = {
        "Ca": 800 * np.exp(-((xx - 15) ** 2 + (yy - 12) ** 2) / 60),
        "Fe": 300 * (xx > nx / 2),
        "Sr": 50 + 40 * np.sin(yy / 4),
    }
    for element, signal in patterns.items():
        counts = rng.poisson(signal + 5).astype(float)
        np.savetxt(
            Path(folder) / f"{prefix}_{element}.txt", counts, fmt="%d", delimiter="\t"
        )
    return str(Path(folder) / f"{prefix}_*.txt")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "pattern", nargs="?", help='glob for the exports, e.g. "exports/Sample_*.txt"'
    )
    parser.add_argument("--pixel-size", type=float, default=20.0, help="pixel size")
    parser.add_argument("--units", default="µm", help="pixel size units (default µm)")
    parser.add_argument(
        "--blur",
        type=float,
        default=None,
        help="Gaussian sigma in pixels (default: none)",
    )
    parser.add_argument(
        "--normalise", action="store_true", help="min-max stretch each map"
    )
    parser.add_argument(
        "--gamma", type=float, default=1.0, help="display gamma (<1 brightens)"
    )
    parser.add_argument(
        "--per-row", type=int, default=None, help="maps per row in the montage"
    )
    parser.add_argument("--save", type=Path, default=None, help="montage PNG path")
    parser.add_argument(
        "--hspy", type=Path, default=None, help="save all maps to one .hspy file"
    )
    parser.add_argument("--demo", action="store_true", help="use synthetic exports")
    parser.add_argument("--show", action="store_true", help="open the figure window")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    if not args.show:
        import matplotlib

        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if args.demo:
        tmp = tempfile.mkdtemp(prefix="uxrf_demo_")
        args.pattern = write_demo_exports(tmp)
        print(f"Synthetic exports written to {tmp}")
    if not args.pattern:
        print("Give a glob pattern for the exports, or use --demo.", file=sys.stderr)
        return 2

    maps = load_element_maps(
        args.pattern,
        args.pixel_size,
        args.units,
        blur=args.blur,
        normalised=args.normalise,
    )
    for element, s in maps.items():
        print(f"{element:>3}: {s}  total {float(s.data.sum()):.0f}")

    fig = montage(maps, per_row=args.per_row, gamma=args.gamma)
    save = args.save
    if save is None and not args.show:
        stem = re.sub(r"[_\s]*\*.*$", "", Path(args.pattern).name) or "maps"
        save = Path(args.pattern).parent / f"{stem}_montage.png"
    if save is not None:
        fig.savefig(save, dpi=150, bbox_inches="tight")
        print(f"Montage written to {save}")

    if args.hspy is not None:
        import hyperspy.api as hs

        # One file, navigation axis = element, so the stack opens with a slider.
        stack = hs.stack(list(maps.values()), new_axis_name="element")
        stack.save(str(args.hspy), overwrite=True)
        print(f"Stack saved to {args.hspy}")

    if args.show:
        plt.show()
    return 0


if __name__ == "__main__":
    sys.exit(main())
