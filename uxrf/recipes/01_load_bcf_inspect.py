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


def save_camera_image(images, spectrum_image, path):
    """Recombine the optical camera image and save it as a PNG.

    M4 Tornado files store the colour camera picture of the mapped field as
    three 8-bit planes; RosettaSciIO returns each plane as its own untitled
    ``Signal2D``. A same-field, map-resolution copy is stored as ``Video``.
    The reader gives the planes the map's pixel size, which is too large;
    the true pixel size is recovered from the map extent, assuming the camera
    picture covers exactly the mapped area (true for the files seen so far).
    """
    import matplotlib.pyplot as plt
    import numpy as np

    planes = [
        im
        for im in images
        if im.data.dtype == np.uint8 and not im.metadata.General.title
    ]
    if len(planes) != 3 or len({im.data.shape for im in planes}) != 1:
        return
    rgb = np.dstack([im.data for im in planes])
    nav = spectrum_image.axes_manager.navigation_axes
    width_um = nav[0].size * nav[0].scale
    height_um = nav[1].size * nav[1].scale
    print(
        f"Camera image {rgb.shape[1]}x{rgb.shape[0]} px covers the mapped field: "
        f"{width_um:.0f} x {height_um:.0f} {nav[0].units}, "
        f"about {width_um / rgb.shape[1]:.2f} {nav[0].units}/px "
        "(plane order assumed R, G, B; unverified)"
    )
    fig, ax = plt.subplots()
    ax.imshow(rgb, extent=(0, width_um, height_um, 0))
    ax.set_xlabel(f"x ({nav[0].units})")
    ax.set_ylabel(f"y ({nav[1].units})")
    ax.set_title("camera image")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Camera image written to {path}")


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
    images = []
    for s in signals:
        print(repr(s), s.data.dtype)
        print(s.axes_manager)
        print()
        if s.metadata.Signal.signal_type.startswith("EDS"):
            spectrum_image = s
        else:
            images.append(s)

    if spectrum_image is None:
        print("No spectrum image found in this file.")
        return 1

    s = spectrum_image
    save_camera_image(images, s, outdir / f"{stem}_camera_rgb.png")
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
        print(f"Line-intensity maps written to {maps_path}")
        for m in maps:
            print(f"  {m.metadata.General.title}: max {float(m.data.max()):.0f} counts")

    if args.show:
        plt.show()
    return 0


if __name__ == "__main__":
    sys.exit(main())
