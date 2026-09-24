"""Load a Bruker M4 Tornado ``.bcf`` hypermap and report what HyperSpy sees.

What it does
------------
1. Loads the file with ``instrument="SEM"`` so the spectrum image becomes an
   eXSpy ``EDS_SEM`` signal (RosettaSciIO would otherwise pick ``EDS_TEM``
   because the tube runs above 30 kV).
2. Prints every signal in the file (images and the spectrum image), the axes
   calibration, and the acquisition metadata the reader mapped.
3. Writes the full ``original_metadata`` tree to a text file next to the
   ``.bcf`` so it can be compared against the instrument configuration.
4. Plots the sum spectrum with X-ray line markers and, if elements are given,
   a montage of line-intensity maps computed from the raw spectra.

Usage::

    python uxrf/recipes/01_load_bcf_inspect.py path/to/map.bcf
    python uxrf/recipes/01_load_bcf_inspect.py map.bcf --elements Ca Fe Sr --show
    python uxrf/recipes/01_load_bcf_inspect.py map.bcf --downsample 2 --lazy
"""

import argparse
import sys
from pathlib import Path


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("bcf", type=Path, help="Bruker .bcf hypermap")
    parser.add_argument(
        "--elements",
        nargs="*",
        default=None,
        metavar="EL",
        help="elements for line-intensity maps (default: those stored in the file)",
    )
    parser.add_argument(
        "--downsample",
        type=int,
        default=1,
        help="sum blocks of N x N pixels while reading (default 1 = none)",
    )
    parser.add_argument(
        "--cutoff-kev",
        type=float,
        default=None,
        help="truncate the energy axis at this energy in keV (default: keep all)",
    )
    parser.add_argument("--lazy", action="store_true", help="dask-backed loading")
    parser.add_argument(
        "--outdir",
        type=Path,
        default=None,
        help="where to write the metadata dump and figures (default: next to the file)",
    )
    parser.add_argument("--show", action="store_true", help="open figure windows")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    if not args.show:
        # Headless by default so the script works in a cloud session or a batch job.
        import matplotlib

        matplotlib.use("Agg")

    import matplotlib.pyplot as plt

    import hyperspy.api as hs

    outdir = args.outdir or args.bcf.parent
    outdir.mkdir(parents=True, exist_ok=True)
    stem = args.bcf.stem

    load_kwargs = dict(instrument="SEM", lazy=args.lazy, downsample=args.downsample)
    if args.cutoff_kev is not None:
        load_kwargs["cutoff_at_kV"] = args.cutoff_kev
    signals = hs.load(str(args.bcf), **load_kwargs)
    if not isinstance(signals, list):
        signals = [signals]

    print(f"\n{args.bcf.name}: {len(signals)} signal(s)\n")
    spectrum_image = None
    for s in signals:
        print(repr(s))
        print(s.axes_manager)
        print()
        if s.metadata.Signal.signal_type.startswith("EDS"):
            spectrum_image = s

    if spectrum_image is None:
        print("No spectrum image found in this file.")
        return 1

    s = spectrum_image
    print("Signal type:", s.metadata.Signal.signal_type)
    print("\nMapped metadata:")
    print(s.metadata)

    meta_path = outdir / f"{stem}_original_metadata.txt"
    s.original_metadata.export(str(meta_path))
    print(f"\nFull original_metadata written to {meta_path}")

    stored_elements = list(s.metadata.get_item("Sample.elements", []))
    print("\nElements stored in the file:", stored_elements or "none")

    # Sum spectrum with X-ray line markers.
    total = s.sum()
    total.plot(xray_lines=True)
    fig_path = outdir / f"{stem}_sum_spectrum.png"
    plt.gcf().savefig(fig_path, dpi=150, bbox_inches="tight")
    print(f"Sum spectrum figure written to {fig_path}")

    # Line-intensity maps straight from the raw spectra (no Esprit export needed).
    elements = args.elements if args.elements is not None else stored_elements
    if elements:
        s.set_elements(elements)
        s.set_lines([])  # let eXSpy choose the strongest line per element
        maps = s.get_lines_intensity()
        hs.plot.plot_images(
            maps,
            per_row=min(4, len(maps)),
            axes_decor="off",
            scalebar=[0],
            colorbar=None,
            cmap="viridis",
            vmin="1th",
            vmax="99th",
            tight_layout=True,
        )
        maps_path = outdir / f"{stem}_line_maps.png"
        plt.gcf().savefig(maps_path, dpi=150, bbox_inches="tight")
        print(f"Line-intensity maps written to {maps_path}")
        for m in maps:
            print(f"  {m.metadata.General.title}: max {float(m.data.max()):.0f} counts")

    if args.show:
        plt.show()
    return 0


if __name__ == "__main__":
    sys.exit(main())
