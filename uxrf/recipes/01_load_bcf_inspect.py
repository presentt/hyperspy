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
   a montage of line-intensity maps computed from the raw spectra, both as
   raw counts and as counts per second using the per-pixel measurement times.
5. Reads the parts of the header RosettaSciIO skips (``bcf_extras.py``): the
   XRF tube/filter/optic block, the map configuration record, the per-pixel
   times, and all stored camera images (high-res, low-res, chamber overview,
   section mosaic), saved as PNGs.

Usage::

    python uxrf/recipes/01_load_bcf_inspect.py path/to/map.bcf
    python uxrf/recipes/01_load_bcf_inspect.py map.bcf --elements Ca Fe Sr --show
    python uxrf/recipes/01_load_bcf_inspect.py map.bcf --downsample 2 --lazy
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bcf_extras  # noqa: E402  (sibling module; recipe file names start with digits)


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
        "--plot-from-kev",
        type=float,
        default=0.3,
        help="start of the plotted sum spectrum; skips the zero-strobe peak at 0 keV (default 0.3)",
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=None,
        help="where to write the metadata dump and figures (default: next to the file)",
    )
    parser.add_argument("--show", action="store_true", help="open figure windows")
    return parser.parse_args(argv)


def report_header_extras(bcf_path, spectrum_image, outdir, stem):
    """Print and save what RosettaSciIO leaves out of the header.

    Returns the per-pixel measurement times in microseconds (or None).
    """
    import matplotlib.pyplot as plt
    import numpy as np

    xml = bcf_extras.read_header_xml(bcf_path)

    print("\nXRF header (tube, filter, optic, chamber, geometry):")
    for key, val in bcf_extras.xrf_header(xml).items():
        if key not in ("Type", "Version", "Size", "NofLayer", "RelativeArea"):
            print(f"  {key} = {val}")
    print("Pulse processor:")
    for key, val in bcf_extras.hardware_header(xml).items():
        if key not in ("Type", "Version", "Size"):
            print(f"  {key} = {val}")
    print("Map configuration record:")
    for key, val in bcf_extras.map_description(xml).items():
        print(f"  {key} = {val}")

    times = bcf_extras.pixel_times(xml)
    if times is not None:
        print(
            f"PixelTimes: {times.shape[1]} x {times.shape[0]} px, "
            f"{times.min() / 1e3:.0f} to {times.max() / 1e3:.0f} ms per pixel, "
            f"sum {times.sum() / 1e6:.0f} s; first column has "
            f"{times[:, 0].mean() / np.median(times):.0%} of the median time"
        )
        fig, ax = plt.subplots()
        im = ax.imshow(times / 1e3, cmap="viridis")
        plt.colorbar(im, ax=ax, label="ms per pixel")
        ax.set_title("PixelTimes")
        fig.savefig(outdir / f"{stem}_pixel_times.png", dpi=150, bbox_inches="tight")
        plt.close(fig)

    nav = spectrum_image.axes_manager.navigation_axes
    width_um = nav[0].size * nav[0].scale
    height_um = nav[1].size * nav[1].scale
    for role, rgb in bcf_extras.images(xml).items():
        path = outdir / f"{stem}_camera_{role}.png"
        fig, ax = plt.subplots()
        if role == "HiRes":
            # Covers exactly the mapped field in the files seen so far, so it
            # can be given the map's extent; the others have unknown scale.
            ax.imshow(rgb, extent=(0, width_um, height_um, 0))
            ax.set_xlabel(f"x ({nav[0].units})")
            ax.set_ylabel(f"y ({nav[1].units})")
        else:
            ax.imshow(rgb)
            ax.axis("off")
        ax.set_title(f"camera: {role} ({rgb.shape[1]} x {rgb.shape[0]} px)")
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"Camera image '{role}' written to {path}")
    return times


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
        print(repr(s), s.data.dtype)
        print(s.axes_manager)
        print()
        if s.metadata.Signal.signal_type.startswith("EDS"):
            spectrum_image = s

    if spectrum_image is None:
        print("No spectrum image found in this file.")
        return 1

    s = spectrum_image
    times = report_header_extras(args.bcf, s, outdir, stem)
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
    # The huge peak at 0 keV is the detector's zero-strobe (electronic) peak,
    # not X-rays; start the plot above it so the real lines are visible.
    total.isig[args.plot_from_kev :].plot(xray_lines=True)
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
        print(f"Line-intensity maps (raw counts) written to {maps_path}")
        for m in maps:
            print(f"  {m.metadata.General.title}: max {float(m.data.max()):.0f} counts")
        if times is not None:
            # Same maps per second of measurement: this is what Esprit shows,
            # and it removes the dim first column and the stage-speed stripes.
            cps_maps = [bcf_extras.counts_per_second(m, times) for m in maps]
            hs.plot.plot_images(
                cps_maps,
                per_row=min(4, len(cps_maps)),
                axes_decor="off",
                scalebar=[0],
                colorbar=None,
                cmap="viridis",
                vmin="1th",
                vmax="99th",
                tight_layout=True,
            )
            cps_path = outdir / f"{stem}_line_maps_cps.png"
            plt.gcf().savefig(cps_path, dpi=150, bbox_inches="tight")
            print(f"Line-intensity maps (counts per second) written to {cps_path}")

    if args.show:
        plt.show()
    return 0


if __name__ == "__main__":
    sys.exit(main())
