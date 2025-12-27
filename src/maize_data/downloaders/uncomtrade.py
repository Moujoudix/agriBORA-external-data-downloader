# src/maize_data/downloaders/uncomtrade.py
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable

import pandas as pd
import requests
from maize_data.io import http_settings

def run_uncomtrade_template(cfg: dict[str, Any], log: Callable[[str], None]) -> None:
    """
    Treat as a starting point: Comtrade endpoints/keys can change.
    """
    force = bool(cfg["global"].get("force_download", False))
    timeout, _ = http_settings(cfg)
    s = cfg["sources"]["uncomtrade"]
    hs = s.get("hs_code", "1005")
    year_from = int(s.get("year_from", 2015))
    year_to = int(s.get("year_to", 2025))

    api_key = os.getenv("UNCOMTRADE_API_KEY", "").strip() or None

    out_dir = Path(cfg["global"]["out_dir"]) / "uncomtrade"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"trade_hs{hs}_{year_from}-{year_to}.csv"

    if out_path.exists() and not force:
        log(f"UN Comtrade: exists, skipping {out_path}")
        return

    # Placeholder endpoint (verify when you enable this)
    url = "https://comtradeapi.worldbank.org/v1/get"
    params = {
        "cmdCode": hs,
        "freqCode": "A",
        "flowCode": "M,X",
        "year": ",".join(map(str, range(year_from, year_to + 1))),
        "format": "json",
        "max": 50000,
    }
    headers = {"Ocp-Apim-Subscription-Key": api_key} if api_key else {}

    log("UN Comtrade: downloading (template; may require endpoint tweaks)")
    r = requests.get(url, params=params, headers=headers, timeout=timeout)
    r.raise_for_status()
    js = r.json()
    df = pd.json_normalize(js.get("data", []))
    df.to_csv(out_path, index=False)
    log(f"UN Comtrade: saved {out_path} rows={len(df)}")
