# Capability notes: M4 Tornado micro-XRF in HyperSpy

A running log. Add dated entries at the bottom of each section; do not rewrite
history.

## Who does what

| Task | Where it lives | Status |
|---|---|---|
| Read `.bcf` (hypermap + SEM-style images + metadata) | RosettaSciIO `rsciio.bruker` | works for Esprit 1.x/2.x SEM files; M4/M6 files "poorly documented and tested" per rsciio docs |
| `EDS_SEM` signal class, X-ray line database, element maps | eXSpy | present; designed for SEM-EDS, applicability to tube-excited XRF to be checked |
| Spatial maps, arithmetic, filtering, multi-image figures | HyperSpy core | present |
| Quantification (fundamental parameters, matrix corrections) | none in the ecosystem for XRF | Esprit only, for now |

## Known reader behaviour (RosettaSciIO Bruker plugin, verified in source)

- Signal type is guessed from accelerating voltage: above 30 kV becomes `EDS_TEM`,
  otherwise `EDS_SEM`. M4 Tornado tubes typically run at 50 kV, so pass
  `instrument="SEM"` to `hs.load`, or call `s.set_signal_type("EDS_SEM")`.
- `beam_energy` is filled from the tube high voltage. Live and real time come from
  the hardware metadata and are stored in seconds.
- Useful load options: `downsample=<int>` (sums pixel blocks), `cutoff_at_kV=<float>`
  (truncates the energy axis), `select_type="spectrum_image"` (skip the images),
  `lazy=True` (dask-backed, for large maps).
- Metadata that Esprit shows but the reader may not map: to be filled from real files
  (compare `s.original_metadata` against the instrument configuration and the Esprit
  project settings).

## Open design question

Reuse eXSpy's SEM-EDS machinery for micro-XRF, or eventually define an XRF signal
type?

Arguments for reuse now: element and line identification, line-intensity windows,
sum spectra, and plotting already work on `EDS_SEM` signals. Arguments for a
dedicated type later: excitation by a polychromatic tube (with filters) rather than
an electron beam; detector geometry and quantification models differ; metadata
fields such as tube current, anode material and filter have no home in the EDS
metadata schema. Decision deferred until the first real files have been inspected.
Any move toward a new signal type would be an eXSpy proposal, not a change here.

## MATLAB workflow to reproduce (from `matlab_reference/`)

Input: Esprit exports one ASCII matrix of counts per element, named
`<prefix>_<Element>.txt`. Pixel size is entered by hand.

| MATLAB step | HyperSpy equivalent | Recipe |
|---|---|---|
| `importdata` + `imref2d(px)` | `np.loadtxt` into `Signal2D`, calibrated signal axes | 02 |
| `imgaussfilt(counts, sd)` | `s.map(scipy.ndimage.gaussian_filter, sigma=sd)` | 02 |
| min-max normalisation | signal arithmetic | 02 |
| `uxrf_montage` (grid, labels, gamma, histeq) | `hs.plot.plot_images(..., label=, per_row=, scalebar=, vmin='1th', vmax='99th')`; gamma via matplotlib `PowerNorm` | 02 |
| `histogram(cps)` | `s.get_histogram().plot()` | backlog |
| `cat(3, r, g, b)` + `stretchlim` + `imwrite` TIFF | 3-channel `Signal1D` → `change_dtype("rgb8")`; save via RosettaSciIO TIFF writer | 03 (backlog) |
| `log10(A ./ B)` ratio maps | `(a / b).map(np.log10)` | 04 (backlog) |
| `histogram2` pixel cross-plots | matplotlib `hist2d` on `.data.ravel()` (not in HyperSpy) | 04 (backlog) |
| Maps straight from raw spectra instead of Esprit exports | eXSpy `get_lines_intensity` on the `.bcf` spectrum image | 01, 05 (backlog) |

## Backlog

- [ ] `03_rgb_composite.py`: tricolour composite with percentile stretch, gamma,
      scale bar, TIFF export.
- [ ] `04_ratio_and_crossplots.py`: log ratio maps and 2D histograms against a
      reference element.
- [ ] `05_bcf_vs_esprit_maps.py`: compare line-intensity maps computed from the raw
      spectrum image with Esprit's exported maps for the same region; quantify
      differences (background handling, overlaps, dead-time correction).
- [ ] Inspect `original_metadata` of real files and list fields that differ from the
      instrument configuration.
- [ ] Try HyperSpyUI and the Jupyter widgets on a real map; note what is usable.

## Log

### 2026-09-24
- Workspace created. Recipes 01 and 02 written. No real `.bcf` inspected yet: the
  cloud environment could not reach `data.caltech.edu` (network policy). Recipe 01's
  eXSpy calls (`set_elements`, `set_lines([])`, `get_lines_intensity`, sum-spectrum
  plot with line markers, `plot_images`) were exercised on a synthetic `EDS_SEM` signal
  with a 50 keV beam energy; recipe 02 was run on synthetic exports (`--demo`) with
  blur, gamma, normalisation and `.hspy` stack export.
- Versions in the cloud environment: hyperspy 2.4.2.dev (this checkout), rosettasciio
  0.14.0, exspy 0.3.2. Installed `EDS_SEM`, `EDS_TEM`, `EELS` come from exspy;
  `hologram` from holospy (pulled in by the docs extras).
- The Bruker reader also takes `index=` (a `.bcf` can hold several datasets; default is
  the first, `"all"` loads every one). Worth checking on multi-ROI project files.
- `get_lines_intensity` returns navigation-only `BaseSignal`s (shape `(nx, ny|)`), not
  `Signal2D`; `plot_images` handles them, but for arithmetic with recipe 02 maps
  transpose them first (`m.T`) so both are `Signal2D` with the same axes.
