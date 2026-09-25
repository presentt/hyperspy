"""Download the published M4 Tornado sample maps into this folder.

Files come from CaltechDATA record doi:10.22002/nea2t-91s77. They are
git-ignored, so re-run this script in each fresh checkout or session.

Usage::

    python uxrf/data/fetch_data.py            # both files
    python uxrf/data/fetch_data.py --small    # only the ~30 MB file
"""

import argparse
import sys
import urllib.parse
import urllib.request
from pathlib import Path

# RECORD_URL = "https://data.caltech.edu/records/nea2t-91s77/files/" # 403 Forbidden by CaltechDATA
RECORD_URL = "https://drive.google.com/drive/folders/1N3Uc_OSjoO0bjb0D9BC8mjrkoVP8xwH_/"

if RECORD_URL.find("drive.google.com") > -1:
    import gdown
    GOOGLE_DRIVE = True

FILES = {
    "small": "BDNE-7H1_3620-47_ROI1a 20um 10x30ms 50kV 600uA Al100.bcf",
    "large": "SBSB-1H1_2401-64 ROI4 50kV 600uA 40keV 90kcps Al100 20um 3x40ms.bcf",
}

HERE = Path(__file__).resolve().parent


def download(name: str, dest: Path) -> None:
    """Stream one file from CaltechDATA to ``dest`` with a simple progress line."""
    if dest.exists():
        print(f"already present: {dest.name} ({dest.stat().st_size / 1e6:.1f} MB)")
        return
    print(f"downloading {name}")
    if GOOGLE_DRIVE == True:
        gdown.download(RECORD_URL, output=name, quiet=False)
    else:
        url = RECORD_URL + urllib.parse.quote(name) + "?download=1"
        with urllib.request.urlopen(url) as response, open(dest, "wb") as fh:
            total = int(response.headers.get("Content-Length") or 0)
            done = 0
            while chunk := response.read(1 << 20):
                fh.write(chunk)
                done += len(chunk)
                if total:
                    print(f"\r  {done / 1e6:6.1f} / {total / 1e6:.1f} MB", end="")
    print(f"\n  saved to {dest}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--small", action="store_true", help="download only the ~30 MB file"
    )
    parser.add_argument(
        "--dest", type=Path, default=HERE, help="destination folder (default: here)"
    )
    args = parser.parse_args(argv)

    keys = ["small"] if args.small else ["small", "large"]
    args.dest.mkdir(parents=True, exist_ok=True)
    for key in keys:
        name = FILES[key]
        download(name, args.dest / name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
