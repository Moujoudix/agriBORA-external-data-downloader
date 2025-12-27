# src/maize_data/downloaders/opendata_ke_socrata.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import pandas as pd
import requests
from maize_data.io import http_settings

def run_opendata_ke_socrata(cfg: dict[str, Any], log: Callable[[str], None]) -> None:
    force = bool(cfg["global"].get("force_download", False))
    timeout, _ = http_settings(cfg)
    s = cfg["sources"]["kenya_opendata_socrata"]
    dataset_id = s["dataset_id"]
    page_size = int(s.get("page_size", 50000))

    base = f"https://www.opendata.go.ke/resource/{dataset_id}.csv"
    out_dir = Path(cfg["global"]["out_dir"]) / "opendata_ke"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{dataset_id}.csv"
    if out_path.exists() and not force:
        log(f"Socrata: exists, skipping {out_path}")
        return

    log(f"Socrata: downloading dataset={dataset_id} page_size={page_size}")

    dfs = []
    offset = 0
    while True:
        url = f"{base}?$limit={page_size}&$offset={offset}"
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        if not r.text.strip():
            break
        df = pd.read_csv(pd.io.common.StringIO(r.text))
        if df.empty:
            break
        dfs.append(df)
        offset += page_size
        log(f"Socrata: fetched rows={len(df)} total_pages={len(dfs)}")

        # stop if last page smaller than page_size
        if len(df) < page_size:
            break

    if dfs:
        out = pd.concat(dfs, ignore_index=True)
        out.to_csv(out_path, index=False)
        log(f"Socrata: saved {out_path} rows={len(out)}")
    else:
        log("Socrata: no rows downloaded.")
