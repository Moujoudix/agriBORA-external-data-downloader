# src/maize_data/downloaders/hdx_ckan.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import pandas as pd
import requests
from maize_data.io import http_settings

def run_hdx_ckan_wfp_prices(cfg: dict[str, Any], log: Callable[[str], None]) -> None:

    force = bool(cfg["global"].get("force_download", False))
    timeout, _ = http_settings(cfg)
    s = cfg["sources"]["hdx_wfp_prices"]
    base = s.get("base", "https://data.humdata.org").rstrip("/")
    package_id = s.get("package_id", "wfp-food-prices")
    country_hint = s.get("country_hint", "Kenya")

    out_dir = Path(cfg["global"]["out_dir"]) / "wfp_hdx"
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / "wfp_food_prices_raw.csv"
    if out_path.exists() and not force:
        log(f"HDX: exists, skipping {out_path}")
        return
    pkg_url = f"{base}/api/3/action/package_show"
    pkg = requests.get(pkg_url, params={"id": package_id}, timeout=timeout).json()
    if not pkg.get("success"):
        raise RuntimeError(f"HDX package_show failed: {pkg}")

    resources = pkg["result"]["resources"]
    # Choose CSV resource with Kenya in name/description if possible
    def score(r: dict[str, Any]) -> int:
        text = (r.get("name", "") + " " + r.get("description", "")).lower()
        fmt = (r.get("format", "") or "").lower()
        sc = 0
        if "csv" in fmt:
            sc += 2
        if country_hint.lower() in text:
            sc += 3
        if "food price" in text:
            sc += 1
        return sc

    resources_sorted = sorted(resources, key=score, reverse=True)
    chosen = next((r for r in resources_sorted if (r.get("format","").lower() == "csv") and r.get("url")), resources_sorted[0])
    url = chosen["url"]

    log(f"HDX: downloading package={package_id} resource='{chosen.get('name')}' url={url}")
    df = pd.read_csv(url)
    out_path = out_dir / "wfp_food_prices_raw.csv"
    df.to_csv(out_path, index=False)
    log(f"HDX: saved {out_path} rows={len(df)}")
