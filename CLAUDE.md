# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Read first

- `AGENTS.md` (root) and the `AGENTS.md` in each subdirectory are the canonical, auto-generated
  conventions for this codebase: axis convention, test rules, changelog rules, completion
  checklist, agent setup steps. Follow them. Edit an `AGENTS.md` only below its
  `<!-- MANUAL -->` line.
- `.github/copilot-instructions.md` and `.github/instructions/*.md` are the reviewer rules
  applied to every PR upstream. When AGENTS.md and these disagree on a detail (e.g. float
  assertions), follow the reviewer rules.
- `doc/dev_guide/coding_with_ai.rst` is the project's AI-assisted contribution policy.

## Commands

```bash
# Environment (ask before installing into an unknown environment; see AGENTS.md "AI Agent Setup")
python -m venv .venv && source .venv/bin/activate   # or a conda env; the system Python is Debian-managed
pip install -e ".[dev]"            # full dev extras; if dask-image or traitsui wheels fail to build,
pip install -e ".[tests,doc,learning,image,speed,ipython,gui-jupyter,coverage]"   # use this subset
pip install exspy                  # EDS_SEM / EDS_TEM / EELS signal types (needed for XRF work)
pre-commit install                 # installs pre-commit AND commit-msg hooks
pre-commit run --all-files

# Lint / format
ruff check                         # config in pyproject.toml; `uxrf/` is linted too
ruff format

# Tests (pyproject addopts always enable pytest-xdist: -n auto --dist loadfile)
pytest hyperspy/tests/                                  # full suite
pytest hyperspy/tests/signals/test_signal2d.py          # one file
pytest -p no:xdist hyperspy/tests/signals/test_signal2d.py::TestClass::test_name   # one test, no xdist
pytest -m "not slow" hyperspy/tests/                    # skip slow tests
pytest --mpl hyperspy/tests/drawing/                    # image-comparison plot tests
pytest --doctest-modules --ignore=hyperspy/tests hyperspy   # docstring examples (CI runs this too)

# Docs / changelog validation (what CI runs)
python scripts/check-docs.py --quick   # changelog fragment names + towncrier parse
python scripts/check-docs.py           # + Sphinx build, warnings as errors
python scripts/check-docs.py --full    # + gallery examples
cd doc && make html
```

Changelog: every change under `hyperspy/` needs `upcoming_changes/<issue>.<type>.rst`
(`new|enhancements|bugfix|api|deprecation|doc|maintenance`), one sentence, no PR number.

Commit trailer: the `commit-msg` hook rejects `Co-authored-by:` lines that name an AI tool.
Use `Assisted-by: Claude Code:<model-id>` instead, and do not add any other AI attribution
trailer.

## Architecture in one screen

- Everything is a `BaseSignal` (`hyperspy/signal.py`) holding `.data` (NumPy or dask, always
  NumPy axis order), `.axes_manager` (`hyperspy/axes.py`), and `.metadata` /
  `.original_metadata` trees. Display order is the reverse of NumPy order; see AGENTS.md.
- Concrete signal classes live in `hyperspy/_signals/` and are re-exported by
  `hyperspy/signals.py`; components in `hyperspy/_components/` re-exported by
  `components1d.py` / `components2d.py`. `hyperspy/api.py` is the public contract.
- Loading: `hs.load()` in `hyperspy/io.py` calls RosettaSciIO (`rsciio`) readers, then
  `assign_signal_subclass()` picks the class from `hyperspy_extension.yaml` merged with every
  installed extension's yaml (`hyperspy/extensions.py`, entry point `hyperspy.extensions`).
  That is how eXSpy adds `EDS_SEM` etc. without touching this repo.
- Models: `hyperspy/model.py` + `hyperspy/models/`; components subclass `Expression` where
  possible. Lazy signals branch on `signal._lazy`. In-place data edits must trigger
  `events.data_changed`.
- Plotting lives in `hyperspy/drawing/`; multi-image figures come from
  `hs.plot.plot_images` (`hyperspy/drawing/utils.py`).

## Ecosystem map (HyperSpy 2.x)

| Need | Package / repo |
|---|---|
| Signal framework, axes, models, plotting, MVA | this repo (`hyperspy/hyperspy`) |
| File readers and writers, incl. Bruker `.bcf` (`rsciio.bruker`) | `hyperspy/rosettasciio` |
| EDS/EELS signal types, X-ray line database, `add_elements`, `get_lines_intensity`, quantification | `hyperspy/exspy` |
| Jupyter / traitsui widgets | `hyperspy_gui_ipywidgets`, `hyperspy_gui_traitsui` |
| Desktop Qt application | `hyperspy/hyperspyUI` |
| Design proposals | `hyperspy/hyperspy-proposals` |

Rules of the road: reader bugs go to RosettaSciIO, EDS/XRF features go to eXSpy, only
core signal-framework changes belong here. Non-trivial or AI-assisted changes to any of
these start with a proposal PR in `hyperspy-proposals` before implementation. Keep PRs small
and explain *why* in the description.

## This fork (presentt/hyperspy): micro-XRF work

- `uxrf/` holds notes, recipes and reference scripts for Bruker M4 Tornado micro-XRF data.
  It is **not** library code and is never sent upstream. Nothing under `hyperspy/` is
  changed for it, so no changelog fragment is needed for `uxrf/` commits.
- Branches: `uxrf` is the stable integration branch (created from upstream
  `RELEASE_next_minor`); topic branches are named `uxrf-<topic>` (never `uxrf/<topic>`,
  git forbids that next to a branch called `uxrf`) and are merged into `uxrf` by PRs inside
  the fork. See `uxrf/WORKFLOW.md`.
- Bruker reader gotcha: RosettaSciIO picks `EDS_TEM` whenever the accelerating voltage is
  above 30 kV, so a 50 kV micro-XRF map needs `hs.load(path, instrument="SEM")` or
  `s.set_signal_type("EDS_SEM")`.
- Privacy in this public fork: no personal e-mail addresses, credentials, or local machine
  paths in committed files; no data files (`uxrf/data/` is git-ignored); no commentary about
  people. Instrument metadata from `.bcf` files may be quoted.
- Plans from planning sessions are archived in `uxrf/plans/`.
- Upstream's `.gitignore` deliberately ignores `CLAUDE.md` (their conventions live in
  `AGENTS.md`). This fork un-ignores it at the end of `.gitignore` for its `uxrf` branches.
  Never include `CLAUDE.md` or the fork-specific `.gitignore` lines in an upstream PR.
