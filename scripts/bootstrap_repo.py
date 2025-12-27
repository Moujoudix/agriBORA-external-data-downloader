from __future__ import annotations
from pathlib import Path

# EXACT layout you agreed on
DIRS = [
    "configs/urls",
    "src/maize_data/downloaders",
    "data_raw",
    "logs",
    "scripts",
]

FILES = [
    "Makefile",  # will not overwrite
    "requirements.txt",
    ".env.example",
    "configs/download.yaml",
    "configs/points.csv",
    "configs/urls/spei_urls.txt",
    "configs/urls/esa_cci_sm_urls.txt",
    "src/maize_data/__init__.py",
    "src/maize_data/cli.py",
    "src/maize_data/io.py",
    "src/maize_data/downloaders/__init__.py",
    "src/maize_data/downloaders/kamis.py",
    "src/maize_data/downloaders/opendata_ke_socrata.py",
    "src/maize_data/downloaders/hdx_ckan.py",
    "src/maize_data/downloaders/worldbank_wdi.py",
    "src/maize_data/downloaders/nasa_power.py",
    "src/maize_data/downloaders/era5_cds.py",
    "src/maize_data/downloaders/geoboundaries.py",
    "src/maize_data/downloaders/url_list_downloader.py",
    "src/maize_data/downloaders/uncomtrade.py",
    "data_raw/.gitkeep",
    "logs/.gitkeep",
]

# Safe starter content (won’t overwrite existing files)
DEFAULTS = {
    "requirements.txt": "# Optional placeholder. Project uses ds-core + requirements.extra.in/requirements.extra.txt.\n",
    ".env.example": (
        "UNCOMTRADE_API_KEY=\n"
        "HTTP_TIMEOUT=120\n"
        "HTTP_SLEEP_SECONDS=1.0\n"
    ),
    "configs/download.yaml": (
        "global:\n"
        "  out_dir: data_raw\n"
        "  start_date: \"2015-01-01\"\n"
        "  end_date: \"2025-12-31\"\n"
        "  http_timeout: 120\n"
        "  http_sleep_seconds: 1.0\n"
        "  log_dir: logs\n"
        "\n"
        "sources:\n"
        "  kamis:\n"
        "    enabled: true\n"
        "    products: [\"Dry Maize\"]\n"
        "    max_pages: 20\n"
        "\n"
        "  kenya_opendata_socrata:\n"
        "    enabled: true\n"
        "    dataset_id: \"p7k9-6zuz\"\n"
        "    page_size: 50000\n"
        "\n"
        "  hdx_wfp_prices:\n"
        "    enabled: true\n"
        "    base: \"https://data.humdata.org\"\n"
        "    package_id: \"wfp-food-prices\"\n"
        "    country_hint: \"Kenya\"\n"
        "\n"
        "  worldbank_wdi:\n"
        "    enabled: true\n"
        "    country: \"KEN\"\n"
        "    indicators: [\"FP.CPI.TOTL\", \"FP.CPI.TOTL.ZG\", \"PA.NUS.FCRF\"]\n"
        "\n"
        "  nasa_power:\n"
        "    enabled: true\n"
        "    points_csv: \"configs/points.csv\"\n"
        "    parameters: [\"T2M\",\"PRECTOT\",\"WS2M\",\"RH2M\",\"ALLSKY_SFC_SW_DWN\"]\n"
        "    community: \"AG\"\n"
        "\n"
        "  era5_cds:\n"
        "    enabled: false\n"
        "    dataset: \"reanalysis-era5-single-levels\"\n"
        "    area: [5.5, 33.8, -4.9, 42.3]\n"
        "    variables: [\"2m_temperature\",\"total_precipitation\"]\n"
        "\n"
        "  geoboundaries_adm1:\n"
        "    enabled: true\n"
        "    iso3: \"KEN\"\n"
        "    adm: \"ADM1\"\n"
        "\n"
        "  spei_urls:\n"
        "    enabled: false\n"
        "    urls_file: \"configs/urls/spei_urls.txt\"\n"
        "\n"
        "  esa_cci_sm_urls:\n"
        "    enabled: false\n"
        "    urls_file: \"configs/urls/esa_cci_sm_urls.txt\"\n"
        "\n"
        "  uncomtrade:\n"
        "    enabled: false\n"
        "    hs_code: \"1005\"\n"
        "    reporter: \"KEN\"\n"
        "    year_from: 2015\n"
        "    year_to: 2025\n"
    ),
    "configs/points.csv": "id,name,lat,lon\nnairobi,Nairobi,-1.286389,36.817223\n",
    "configs/urls/spei_urls.txt": "# Paste one direct SPEI file URL per line\n",
    "configs/urls/esa_cci_sm_urls.txt": "# Paste one direct ESA CCI SM file URL per line\n",
    "data_raw/.gitkeep": "",
    "logs/.gitkeep": "",
}

def write_if_missing(path: Path, content: str) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

def touch_if_missing(path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")

def main() -> None:
    for d in DIRS:
        Path(d).mkdir(parents=True, exist_ok=True)

    for f in FILES:
        p = Path(f)
        if f in DEFAULTS:
            write_if_missing(p, DEFAULTS[f])
        else:
            touch_if_missing(p)

    print("✅ Scaffold created/verified (non-destructive).")

if __name__ == "__main__":
    main()
