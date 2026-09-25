# MATLAB reference scripts

Legacy scripts for Esprit ASCII map exports. They define the behaviour the
HyperSpy recipes in `../recipes/` reproduce. Kept unchanged for comparison.

| File | Role |
|---|---|
| `import_uxrf.m` | Globs `<prefix>_<Element>.txt` exports into a struct keyed by element |
| `uxrf_montage.m` | Grid of all element maps with per-element gamma and labels |
| `Ileret_RtP4_figs.m` | Example driver: montage, RGB composites, TIFF export |
| `plot_maps.m` | Code cells extracted from `plot_maps.mlx`: single maps, histograms, RGB, ratio map, cross-plots; embeds `img_proc_uxrf` and `uxrf_labeled_montage` |
| `tricolor_plots.m` | Code cells extracted from `tricolor_plots.mlx`: RGB tiles for several samples, Ca/P ratio tiles |

The `.mlx` Live Scripts were converted to plain `.m` text because they embed
figure output (one was 8 MB). Only the code cells were kept.

`img_proc_uxrf` (inside `plot_maps.m` and `tricolor_plots.m`) is the per-map
processing step: raw counts, min-max normalised, Gaussian blurred, blurred and
normalised, plus an `imref2d` spatial reference from the typed-in pixel size.
