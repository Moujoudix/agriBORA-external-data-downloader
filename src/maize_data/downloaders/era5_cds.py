# src/maize_data/downloaders/era5_cds.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

def run_era5_cds(cfg: dict[str, Any], log: Callable[[str], None]) -> None:
    s = cfg["sources"]["era5_cds"]
    out_dir = Path(cfg["global"]["out_dir"]) / "era5"
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        import cdsapi
    except Exception as e:
        log(f"ERA5: cdsapi not installed ({e}). Set enabled=false or install cdsapi.")
        return

    dataset = s.get("dataset", "reanalysis-era5-single-levels")
    area = s["area"]  # [N, W, S, E]
    variables = s.get("variables", ["2m_temperature", "total_precipitation"])

    year_from = int(cfg["global"]["start_date"][:4])
    year_to = int(cfg["global"]["end_date"][:4])

    c = cdsapi.Client()
    for year in range(year_from, year_to + 1):
        out_nc = out_dir / f"era5_{year}.nc"
        if out_nc.exists():
            log(f"ERA5: exists, skipping {out_nc}")
            continue
        log(f"ERA5: downloading year={year} vars={len(variables)} bbox={area}")
        c.retrieve(
            dataset,
            {
                "product_type": "reanalysis",
                "variable": variables,
                "year": str(year),
                "month": [f"{m:02d}" for m in range(1, 13)],
                "day": [f"{d:02d}" for d in range(1, 32)],
                "time": [f"{h:02d}:00" for h in range(24)],
                "area": area,
                "format": "netcdf",
            },
            str(out_nc),
        )
        log(f"ERA5: saved {out_nc}")
