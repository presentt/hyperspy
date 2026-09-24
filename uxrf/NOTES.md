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

## Findings from the first real file (2026-09-24)

File: `BDNE-7H1_3620-47_ROI1a 20um 10x30ms 50kV 600uA Al100.bcf` (published, 30 MB).
Loaded with `hs.load(path, instrument="SEM")`; five signals come back:

| Signal | Shape | What it is |
|---|---|---|
| `EDX` (`EDSSEMSpectrum`) | 55 x 42 pixels x 4096 channels | the hypermap |
| `Video` (`Signal2D`, uint16) | 55 x 42 | camera picture of the field at map resolution |
| three untitled `Signal2D` (uint8) | 1024 x 768 each | the three colour planes of the full-resolution camera picture (Bruker stores one image with `PlaneCount = 3`; the reader emits one signal per plane) |

- **Energy axis**: 4096 channels, 9.982 eV/channel, offset -0.954 keV, so 0 to ~40 keV.
  Comes from `Spectrum.CalibAbs` / `CalibLin`. The enormous peak at 0 keV in the sum
  spectrum is the zero-strobe (electronic) peak (`Hardware.ZeroPeakPosition = 96`,
  `ZeroPeakFrequency = 20000` Hz), not X-rays. Crop it (`s.isig[0.3:]`) before fitting
  or normalising. The broad hump near 19 keV plus the line at 20.2 keV are Rh Kα
  Compton and Rayleigh scatter from the tube anode; Esprit's stored element list
  includes `Rh` for that reason.
- **Pixel size**: `Microscope.DX = 26.95`, `DY = 26.90` µm; the reader reports exactly
  these. The "20um" in the file name therefore does not describe the pixel step of this
  map (open question for the operator: spot size? intended step?). Map extent is
  55 x 26.9 = 1.48 mm by 42 x 26.9 = 1.13 mm.
- **Reader detail**: both map axes use `DY` (`rsciio/bruker/_api.py`, the `"width"` axis
  is given `y_res`), a 0.17 % difference here. The camera planes and `Video` are given
  the map pixel size too, which is wrong for the 1024 x 768 planes (true pixel about
  1.45 µm, from the map extent). Candidate RosettaSciIO issue, low priority.
- **Timing**: `DSP Configuration.PixelAverage = 30000` (µs, the 30 ms dwell),
  `Line counter` = 10 for every line (the 10 frames). `real_time = 693 s`
  = 55 x 42 x 10 x 0.030 s exactly. No live time or dead time anywhere in the file.
- **Not in the file**: tube current (600 µA), filter (Al 100 µm), anode material,
  chamber atmosphere, spot size. If they are needed they must come from the file name
  or a lab notebook. `beam_energy = 50` comes from `Analysis.PrimaryEnergy`.
- **Detector**: `XFlash 430`, 0.45 mm SDD, 12.5 µm Be window, `DetectorCount = 2`,
  `SelectedDetectors = 1.2` (both detectors, presumably summed); `elevation_angle = 50`,
  `azimuth_angle = 0`, `energy_resolution_MnKa = 130` eV. The detector response
  tables (`ResponseFunction`, `PPRTData`, `ShiftData`) are carried along; useful later
  for a fundamental-parameters model.
- **Stage**: `X = 172.7`, `Y = 110.9`, `Z = 125.6` (mm, presumably) mapped to
  `Acquisition_instrument.SEM.Stage`.
- **Line maps** (`get_lines_intensity` with default 2-FWHM windows) look right: the Ca
  map shows the dark vein seen in the camera picture. The Ca map has a bright first
  column and faint vertical stripes; check whether this is a scan artefact of the
  instrument or of the reader's row/column handling.

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
- [x] Inspect `original_metadata` of a real file (done for one file; see Findings).
- [ ] Confirm what "20um" in the file names refers to, given `DX = 26.9` µm.
- [ ] Verify the camera plane order (R, G, B or B, G, R) against Esprit's display.
- [ ] Decide whether to report the image pixel-size and `y_res` details to RosettaSciIO.
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
- Later the same day: recipe 01 run on the published 30 MB file (uploaded into the
  session). Findings recorded above. Recipe 01 gained `--plot-from-kev` (skips the
  zero-strobe peak) and a camera-image reconstruction.
