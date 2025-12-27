# src/maize_data/downloaders/nasa_power.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import pandas as pd
import requests
from maize_data.io import http_settings

BASE = "https://power.larc.nasa.gov/api/temporal/daily/point"

def run_nasa_power(cfg: dict[str, Any], log: Callable[[str], None]) -> None:
    timeout, sleep_s = http_settings(cfg)
    s = cfg["sources"]["nasa_power"]

    points_csv = Path(s["points_csv"])
    params = s.get("parameters", ["T2M", "PRECTOT"])
    community = s.get("community", "AG")

    out_dir = Path(cfg["global"]["out_dir"]) / "nasa_power"
    out_dir.mkdir(parents=True, exist_ok=True)

    pts = pd.read_csv(points_csv)
    start = cfg["global"]["start_date"].replace("-", "")
    end = cfg["global"]["end_date"].replace("-", "")

    for row in pts.to_dict(orient="records"):
        force = bool(cfg["global"].get("force_download", False))
        pid = str(row["id"])
        lat = float(row["lat"])
        lon = float(row["lon"])
        out_path = out_dir / f"power_daily_{pid}.json"
        if out_path.exists() and not force:
            log(f"NASA POWER: exists, skipping {out_path.name}")
            continue

        q = {
            "latitude": lat,
            "longitude": lon,
            "start": start,
            "end": end,
            "community": community,
            "parameters": ",".join(params),
            "format": "JSON",
        }
        log(f"NASA POWER: {pid} lat={lat} lon={lon}")
        r = requests.get(BASE, params=q, timeout=timeout)
        r.raise_for_status()
        out_path = out_dir / f"power_daily_{pid}.json"
        out_path.write_text(r.text, encoding="utf-8")
        log(f"NASA POWER: saved {out_path}")
        if sleep_s:
            import time
            time.sleep(sleep_s)
