# Capability notes: M4 Tornado micro-XRF in HyperSpy

A running log. Add dated entries at the bottom of each section; do not rewrite
history.

## Start here (handoff for the next session)

1. Work from the `uxrf` branch (`git checkout uxrf`), then make a topic branch
   `uxrf-<topic>`. Set up the environment as in `uxrf/README.md` (cloud: venv +
   `pip install -e ".[tests,doc,learning,image,speed,ipython,gui-jupyter,coverage]" exspy`).
2. Data is not in git. Either upload a `.bcf` into the session or, if the
   environment allows `data.caltech.edu`, run `python uxrf/data/fetch_data.py`.
3. Smoke test: `python uxrf/recipes/01_load_bcf_inspect.py uxrf/data/<file>.bcf --elements Ca Fe Sr`
   and `python uxrf/recipes/02_esprit_ascii_to_signals.py --demo`.
4. Read "Findings from the first real file" and "What the raw header holds" below
   before touching `bcf_extras.py`; field meanings marked unverified need a second file.
5. Most useful new inputs: the 100 MB CaltechDATA map (90 kcps, 40 keV in its name),
   any map acquired at 130 kcps or a different energy range or pixel size, and the
   map pixel size Esprit displays for the 30 MB file (to settle `MapGeometry = 55,42,20,0`).
6. Backlog order suggested: recipe 03 (RGB composites, now also from counts-per-second
   maps), recipe 05 (compare `.bcf`-derived maps with Esprit exports), then map-to-mosaic
   registration.

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

## What the raw header holds that the reader skips (2026-09-24, same file)

The `.bcf` is a container (`EDSDatabase/HeaderData`, `SpectrumData0`,
`SpectrumPositions0`). The header is 22 MB of XML, mostly base64 images.
`uxrf/recipes/bcf_extras.py` reads the pieces below straight from it.

**`TRTXrfHeader` (not mapped by RosettaSciIO at all):**

| Field | Value in this file | Meaning |
|---|---|---|
| `Voltage`, `Current` | 50, 599 | kV, µA |
| `TubeType`, `Anode` | MCBM 50-0.6B Rh, 45 | tube model; anode Z |
| `Filters` | Tube window (Be, 100 µm) \| Al 100 µm | tube window and excitation filter |
| `Optic`, `OpticParam` | Lens, 6 coefficients | polycapillary optic and its transmission model |
| `SpotSize`, `DetSpotSize` | 50, 20 | µm; which one is the selected spot setting is unverified, the file name says 20 |
| `ExcitationAngle`, `DetectionAngle` | 50, 50 | degrees |
| `TubeIncidentAngle`, `TubeTakeOffAngle` | 78, 12 | degrees |
| `ExcitationPathLength`, `DetectionPathLength` | 10, 20 | mm, presumably |
| `SolidAngleDetection` | 0.013 | sr, presumably |
| `Atmosphere`, `ChamberPressure` | Air, 2 | mbar (operator confirmed the unit) |
| `ChassisType`, `ChassisNumber`, `ChassisProdDate` | XS-52, 0126, 1.6.2018 | instrument identity |

**`TRTSpectrumHardwareHeader`:** `ZeroPeakPosition = 96`, `ZeroPeakFrequency = 20000`,
`Amplification = 40000`, `ShapingTime = 90000`, `DetectorCount = 2`,
`SelectedDetectors = 1,2`. Whether `ShapingTime` encodes the 90/130 kcps throughput
setting and `Amplification` the 40 keV range is unverified; a file acquired at the
other setting would tell. **No detector temperature is stored anywhere.**

**Two detectors, one stream.** `SelectedDetectors = 1,2`, DSP `ChannelCount = 1`, one
`SpectrumData0`. The two SDDs are summed before storage; per-detector spectra (for
separating diffraction peaks) are not in the file.

**Data type.** The hypermap is unsigned 16-bit integer counts per channel per pixel,
not normalised. This file: 86.4 M counts, mean 37 400 per pixel.

**`OverviewImageDescription`** is a base64 text record:

```
Default=HiRes            Image_0=LowRes         Image_1=Overview      Image_2=Mosaic
MapStartPosMM=172.014,110.374,125.564      (stage x, y, z at the map corner; Stage X/Y
                                            in the SEM block is the map centre)
MapRectMM=0.1840,0.1370,1.1099,0.8310      (interpretation open; not the map size in mm)
MapGeometry=55,42,20,0                     (width px, height px, 20 = ?, 0)
MapTime=30;693;1585;10;10;40               (dwell ms; real time s; ?; frames; ?; keV range?)
```

The third `MapGeometry` value and the `MapTime` fields need a second file with
different settings to pin down. The 20 is either the pixel-size setting the operator
typed (with Esprit then choosing 55 x 42 pixels at 26.9 µm, which would be odd) or the
spot setting. **Action for the operator: open this file in Esprit and read off the
map pixel size it shows.**

**Images.** Four colour images (three 8-bit planes each), plus two map-grid images:

| XML name | Role | Size | Notes |
|---|---|---|---|
| `Default` | HiRes | 1024 x 768 | camera view of the mapped field; the reader returns only this one, as three untitled signals |
| `Image_0` | LowRes | 1024 x 768 | the other camera (instrument has a 10x and a 100x camera) |
| `Image_1` | Overview | 752 x 480 | chamber camera; dark in this file because the lamp was off |
| `Image_2` | Mosaic | 2426 x 1502 | whole thin section, assembled from the 10x camera |
| (unnamed) | Video | 55 x 42, uint16 | camera brightness sampled on the map grid, cut from whichever image the map was drawn on |
| `PixelTimes` | | 55 x 42, uint32 | **real measurement time per pixel in µs** |

Operator notes: Esprit tends to lose stage coordinates, so the map position on the
mosaic should eventually be recovered by image registration (Video or HiRes against
Mosaic) rather than trusted from `MapStartPosMM`. The map overlay rectangles in the
XML are all zero in this file.

**`PixelTimes` explains the artefacts.** Mean 297 ms, range 167 to 322 ms, sum 687 s
(metadata `real_time` 693 s). The first column has 59 % of the median time, and 59 %
of the counts: a stage start-up effect, not a spectral one. Dividing total counts by
`PixelTimes` reduces column-to-column roughness from 2.4 % to 0.5 %, matching the
0.25 % row-to-row value. Esprit displays counts per second, which is why it never
shows the dim column or the stripes. `bcf_extras.counts_per_second` does the same.

**Zero-strobe peak = live-time clock.** The 20 kHz strobe would give 6000 counts per
0.3 s pixel; the observed mean is 4200, and the per-pixel zero-peak count correlates
0.89 with `PixelTimes` and drops where Ca (dense carbonate) is high. So the strobe
pulses are subject to the same dead time as X-rays, the zero peak measures live time,
and this map ran at roughly 30 % dead time. Per-pixel live time is recoverable as
`zero_peak_counts / 20000` s. Worth cross-checking against Esprit's dead-time readout.

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
- [ ] Confirm what "20um" in the file names refers to (`DetSpotSize = 20`,
      `MapGeometry = 55,42,20,0`, `DX = 26.9` µm): read the map pixel size off Esprit.
- [ ] Pin down `MapTime` fields, `ShapingTime` vs throughput setting, `Amplification`
      vs energy range, using the 100 MB file (90 kcps, 40 keV in its name) and a
      130 kcps file.
- [ ] Register Video/HiRes onto the Mosaic to recover the map position (stage
      coordinates are unreliable).
- [ ] Compare zero-peak live time with Esprit's dead-time readout.
- [x] Camera plane order is R, G, B (blue-stained epoxy pore renders blue).
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
- Later still: the raw header was read directly from the container. Tube, filter,
  optic, chamber and geometry are all stored (`TRTXrfHeader`), as are per-pixel
  measurement times and four camera images including a whole-section mosaic. Recorded
  above; `bcf_extras.py` added; recipe 01 now prints the extras, saves all camera
  images and `PixelTimes`, and produces counts-per-second line maps.
