# agriBORA external data downloader

Utilities to **download and validate external datasets** used for the agriBORA commodity price forecasting workstream (market prices, weather/climate signals, boundaries, macro indicators).

This repo is intentionally lightweight: downloaded artifacts and logs are generated locally and **not committed**.

## Repository structure

* `src/maize_data/`

  * `cli.py` — command-line interface to run one or more download jobs.
  * `downloaders/` — source-specific downloaders:

    * `kamis.py` — KAMIS commodity prices.
    * `hdx_ckan.py` — CKAN portals (e.g., HDX/WFP).
    * `nasa_power.py` — NASA POWER daily weather time series.
    * `worldbank_wdi.py` — World Bank WDI indicators.
    * `uncomtrade.py` — UN Comtrade trade data.
    * `opendata_ke_socrata.py` — Socrata portals (Kenya Open Data).
    * `geoboundaries.py` — admin boundaries from GeoBoundaries.
    * `era5_cds.py` — ERA5 via CDS API (requires CDS credentials).
    * `url_list_downloader.py` — helper downloader for sources defined as URL lists.
  * `manifest.py` — manifest of downloaded artifacts (for tracking/reproducibility).
  * `io.py` — shared I/O helpers.
* `configs/`

  * `download.yaml` — main download configuration.
  * `points.csv` — points/locations used for gridded data extraction (if applicable).
  * `urls/` — URL lists used by `url_list_downloader.py`.
* `scripts/`

  * `bootstrap_repo.py` — convenience script for initial local setup.
  * `build_points_from_boundaries.py` — generates `configs/points.csv` from boundary geometries.
  * `validate_downloads.py` — validates local downloads (completeness/integrity checks).
* `data/` — derived / cleaned outputs (**ignored by git**).
* `data_raw/` — raw downloaded artifacts (**ignored by git**).
* `logs/` — runtime logs (**ignored by git**).

> `data/`, `data_raw/`, and `logs/` are ignored by default (via `.gitignore`) to keep the repo small and reproducible.

## Environment & dependencies

I use a **base Python environment for DS** with base dependencies, then install project-specific constraints from `requirements.extra.in`.

* `requirements.txt` is the **ds-core** dependencies.
* `requirements.extra.in` is the **source** requirements/constraints list.
* `requirements.extra.txt` is a **compiled**/pinned lock-style file.

### Setup — Compile pinned requirements Then install (recommended)

This repo uses the typical `pip-tools` workflow.

```bash
pip install pip-tools
pip-compile requirements.extra.in -o requirements.extra.txt
pip install -r requirements.extra.txt
```

If you previously used a command like:

```bash
pip-compile requirements.dev.in -o requirements.dev.txt
```

…it’s the same idea; this repo uses the `requirements.extra.in → requirements.extra.txt` naming.

## Usage

The workflow is driven by the **Makefile** targets. The Makefile ensures `src/` is on `PYTHONPATH`, compiles project requirements using your fixed **ds-core** constraints, installs them, and then runs the CLI.

### Quick start

```bash
make help
make init
make install
make download-fast
make download # later when .env is configured.
```

### Targets

* `make init` — create the agreed folder structure + placeholder files (non-destructive).
* `make check` — verify `python/pip/pip-compile` and that the ds-core constraints file exists.
* `make compile` — generate `requirements.extra.txt` from `requirements.extra.in` constrained by your ds-core file.
* `make install` — `pip install -r requirements.extra.txt`.
* `make points` — build `configs/points.csv` from boundary geometries.
* `make download` — run all enabled downloaders using `configs/download.yaml`.
* `make download-fast` — like `download` but skips auth-heavy sources (ERA5/Comtrade).
* `make clean` — remove `data_raw/*` and `logs/*` (keeps folders).

### Configuration

The download configuration is controlled by `CFG` (defaults to `configs/download.yaml`). Override it like this:

```bash
make download CFG=configs/download.yaml
# or point to a different config
make download CFG=configs/my_download.yaml
```

> Note: `make compile` uses your fixed ds-core constraints at `~/env-specs/ds-core/requirements.txt` (see `CORE_CONSTRAINT` in the Makefile).

## Credentials & secrets

Some sources may require credentials (e.g., ERA5/CDS API).

* Put secrets in `.env`.
* The existing `.env.example` documents expected variables **without real values**.

## Outputs

By default the project writes:

* raw downloads under `data_raw/`
* processed outputs under `data/`
* logs under `logs/`

## Notes

* `__pycache__/` folders are Python bytecode caches and are intentionally ignored.


> 🪬 Good luck. May your API keys be valid and your rate limits be generous. 🪬
