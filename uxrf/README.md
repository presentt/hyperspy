# uxrf: Bruker M4 Tornado micro-XRF with HyperSpy

Working notes, recipes and reference scripts for analysing Bruker M4 Tornado
micro-XRF hypermaps (`.bcf`) and Esprit ASCII exports with the HyperSpy
ecosystem, without the Esprit licence dongle.

This folder is a personal workspace inside a fork of HyperSpy. Nothing here is
part of the HyperSpy library and nothing here is sent upstream. Library changes,
if they ever become necessary, go through the normal community process
(see `../CLAUDE.md`, "Ecosystem map").

## Layout

| Path | What it is |
|---|---|
| `NOTES.md` | Capability log: what works today, metadata quirks, open questions, backlog |
| `WORKFLOW.md` | Plain-language git workflow for this fork, plus commit/PR message templates |
| `recipes/` | Small runnable scripts, one task each (`python uxrf/recipes/<name>.py --help`) |
| `data/` | Local data. Git-ignored except `README.md` and `fetch_data.py` |
| `matlab_reference/` | Legacy MATLAB scripts being translated to HyperSpy |
| `plans/` | Archived planning documents from working sessions |

## Setup

### Laptop (miniconda)

```bash
conda create -n uxrf -c conda-forge python=3.12
conda activate uxrf
cd path/to/your/hyperspy/checkout
conda env update -n uxrf -f conda_environment.yml      # HyperSpy's own runtime deps
pip install -e ".[tests,learning,image,speed,ipython,gui-jupyter]" exspy
```

The editable install (`-e`) means the `hyperspy` you import is this checkout,
so switching git branches switches the library. eXSpy supplies the `EDS_SEM`
signal type that the Bruker reader produces.

### Cloud session

The container's system Python is Debian-managed and refuses some upgrades, so
use a virtual environment (it is disposable with the container):

```bash
python -m venv /home/user/venv && source /home/user/venv/bin/activate
pip install -e ".[tests,doc,learning,image,speed,ipython,gui-jupyter,coverage]" exspy pre-commit
pre-commit install
```

### Check

```bash
python -c "import hyperspy.api as hs, rsciio.bruker, exspy; hs.print_known_signal_types()"
```

`EDS_SEM` and `EDS_TEM` must appear in the list.

## Sample data

See `data/README.md`. Published maps from
[doi:10.22002/nea2t-91s77](https://doi.org/10.22002/nea2t-91s77) can be
downloaded with `python uxrf/data/fetch_data.py`.

## First things to run

```bash
python uxrf/recipes/01_load_bcf_inspect.py uxrf/data/<file>.bcf --elements Ca Fe Sr
python uxrf/recipes/02_esprit_ascii_to_signals.py --demo          # no data needed
python uxrf/recipes/02_esprit_ascii_to_signals.py "exports/Sample_*.txt" --pixel-size 20 --blur 1.5
```
