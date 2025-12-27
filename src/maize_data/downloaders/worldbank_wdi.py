# src/maize_data/downloaders/worldbank_wdi.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import pandas as pd
import requests
from maize_data.io import http_settings

def _fetch_indicator(country: str, indicator: str, timeout: int) -> pd.DataFrame:
    url = f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}"
    r = requests.get(url, params={"format": "json", "per_page": 20000}, timeout=timeout)
    r.raise_for_status()
    meta, data = r.json()
    rows = []
    for d in data:
        if not d:
            continue
        rows.append({
            "date": d.get("date"),
            "value": d.get("value"),
            "indicator": indicator,
            "country": country,
        })
    return pd.DataFrame(rows)

def run_worldbank_wdi(cfg: dict[str, Any], log: Callable[[str], None]) -> None:
    timeout, _ = http_settings(cfg)
    s = cfg["sources"]["worldbank_wdi"]
    country = s.get("country", "KEN")
    indicators = s.get("indicators", [])

    out_dir = Path(cfg["global"]["out_dir"]) / "worldbank_wdi"
    out_dir.mkdir(parents=True, exist_ok=True)

    all_df = []
    for ind in indicators:
        log(f"WDI: fetching {country} {ind}")
        df = _fetch_indicator(country, ind, timeout)
        out_path = out_dir / f"{country}_{ind}.csv"
        df.to_csv(out_path, index=False)
        all_df.append(df)
        log(f"WDI: saved {out_path} rows={len(df)}")

    if all_df:
        merged = pd.concat(all_df, ignore_index=True)
        merged.to_csv(out_dir / f"{country}_all_indicators.csv", index=False)
