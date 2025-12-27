from __future__ import annotations
import argparse
from pathlib import Path
import yaml

SOURCE_TO_DIR = {
    "kamis": "kamis",
    "kenya_opendata_socrata": "opendata_ke",
    "hdx_wfp_prices": "wfp_hdx",
    "worldbank_wdi": "worldbank_wdi",
    "nasa_power": "nasa_power",
    "era5_cds": "era5",
    "geoboundaries_adm1": "boundaries",
    "spei_urls": "spei_urls",
    "esa_cci_sm_urls": "esa_cci_sm_urls",
    "uncomtrade": "uncomtrade",
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out-dir", default="data_raw")
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    sources = cfg.get("sources", {})
    out = Path(args.out_dir)

    failed = []
    for name, scfg in sources.items():
        if not scfg.get("enabled", False):
            continue
        subdir = SOURCE_TO_DIR.get(name)
        if not subdir:
            continue
        p = out / subdir
        has_files = p.exists() and any(x.is_file() for x in p.rglob("*"))
        if not has_files:
            failed.append(name)

    if failed:
        raise SystemExit(f"Enabled sources with no files: {failed}")
    print("OK: all enabled sources produced at least one file.")

if __name__ == "__main__":
    main()
