# Data

Everything in this folder except this file and `fetch_data.py` is git-ignored.
Put `.bcf` files and Esprit ASCII exports here for local work.

## Published sample maps

Two M4 Tornado hypermaps from a published dataset are available on CaltechDATA,
record [doi:10.22002/nea2t-91s77](https://doi.org/10.22002/nea2t-91s77):

| File | Size | Notes |
|---|---|---|
| `BDNE-7H1_3620-47_ROI1a 20um 10x30ms 50kV 600uA Al100.bcf` | ~30 MB | Small; good for quick tests |
| `SBSB-1H1_2401-64 ROI4 50kV 600uA 40keV 90kcps Al100 20um 3x40ms.bcf` | ~100 MB | Larger, more to see |

Acquisition settings encoded in the names: 20 µm pixel, 50 kV tube voltage,
600 µA tube current, Al 100 µm filter, frame count × dwell time per pixel.

Download both with:

```bash
python uxrf/data/fetch_data.py            # both files
python uxrf/data/fetch_data.py --small    # only the 30 MB file
```

Please cite the dataset when using these files.
