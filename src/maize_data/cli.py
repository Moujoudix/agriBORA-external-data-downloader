# src/maize_data/cli.py
from __future__ import annotations

import argparse
from pathlib import Path

from maize_data.io import load_yaml, setup_env, make_logger
from maize_data.manifest import start_run, record_source, end_run, append_note
from maize_data.downloaders import (
    run_kamis,
    run_opendata_ke_socrata,
    run_hdx_ckan_wfp_prices,
    run_worldbank_wdi,
    run_nasa_power,
    run_era5_cds,
    run_geoboundaries_adm1,
    run_url_list,
    run_uncomtrade_template,
)

def main() -> None:
    p = argparse.ArgumentParser(prog="maize_data")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("download", help="Download enabled sources in config")
    d.add_argument("--config", required=True, type=str)
    d.add_argument("--skip-auth", action="store_true", help="Skip sources that usually need accounts/keys (e.g., ERA5)")
    d.add_argument("--force", action="store_true", help="Re-download even if output files already exist")
    d.add_argument("--hash", action="store_true", help="Compute sha256 for files in manifest (slower)")

    args = p.parse_args()
    setup_env()

    config_path = Path(args.config)
    config_text = config_path.read_text(encoding="utf-8")
    cfg = load_yaml(config_path)

    # global knobs
    cfg.setdefault("global", {})
    cfg["global"]["force_download"] = bool(args.force)

    log = make_logger(cfg["global"].get("log_dir", "logs"))

    out_dir = Path(cfg["global"].get("out_dir", "data_raw"))
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = out_dir / "_MANIFEST.json"
    ctx = start_run(
        manifest_path=manifest_path,
        config_path=config_path,
        config_text=config_text,
        skip_auth=bool(args.skip_auth),
        force=bool(args.force),
        hash_files=bool(args.hash),
    )
    log(f"Manifest run_id={ctx.run_id} -> {manifest_path}")

    sources = cfg.get("sources", {})

    def enabled(name: str) -> bool:
        return bool(sources.get(name, {}).get("enabled", False))

    def snap(source_name: str, source_out_subdir: str) -> None:
        """Record the current state of files for this source into the manifest."""
        record_source(
            manifest_path=manifest_path,
            run_id=ctx.run_id,
            source_name=source_name,
            source_params=sources.get(source_name, {}),
            base_out_dir=out_dir,
            source_out_dir=out_dir / source_out_subdir,
            hash_files=bool(args.hash),
        )

    try:
        # PRICES
        if enabled("kamis"):
            run_kamis(cfg, log); snap("kamis", "kamis")
        if enabled("kenya_opendata_socrata"):
            run_opendata_ke_socrata(cfg, log); snap("kenya_opendata_socrata", "opendata_ke")
        if enabled("hdx_wfp_prices"):
            run_hdx_ckan_wfp_prices(cfg, log); snap("hdx_wfp_prices", "wfp_hdx")

        # MACRO
        if enabled("worldbank_wdi"):
            run_worldbank_wdi(cfg, log); snap("worldbank_wdi", "worldbank_wdi")

        # WEATHER
        if enabled("nasa_power"):
            run_nasa_power(cfg, log); snap("nasa_power", "nasa_power")

        if enabled("era5_cds"):
            if args.skip_auth:
                log("Skipping ERA5 (skip-auth enabled).")
                append_note(manifest_path, ctx.run_id, "Skipped era5_cds because --skip-auth was set.")
            else:
                run_era5_cds(cfg, log); snap("era5_cds", "era5")

        # SPATIAL
        if enabled("geoboundaries_adm1"):
            run_geoboundaries_adm1(cfg, log); snap("geoboundaries_adm1", "boundaries")

        # URL-list sources
        if enabled("spei_urls"):
            run_url_list(cfg, log, key="spei_urls"); snap("spei_urls", "spei_urls")
        if enabled("esa_cci_sm_urls"):
            run_url_list(cfg, log, key="esa_cci_sm_urls"); snap("esa_cci_sm_urls", "esa_cci_sm_urls")

        # TRADE template
        if enabled("uncomtrade"):
            if args.skip_auth:
                log("Skipping UN Comtrade (skip-auth enabled).")
                append_note(manifest_path, ctx.run_id, "Skipped uncomtrade because --skip-auth was set.")
            else:
                run_uncomtrade_template(cfg, log); snap("uncomtrade", "uncomtrade")

        log("Done.")
    finally:
        end_run(manifest_path, ctx.run_id)
        log(f"Manifest finalized for run_id={ctx.run_id}")

if __name__ == "__main__":
    main()
