# src/maize_data/downloaders/geoboundaries.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import requests
from maize_data.io import http_settings

def run_geoboundaries_adm1(cfg: dict[str, Any], log: Callable[[str], None]) -> None:
    force = bool(cfg["global"].get("force_download", False))
    timeout, _ = http_settings(cfg)

    s = cfg["sources"]["geoboundaries_adm1"]
    iso3 = s.get("iso3", "KEN")
    adm = s.get("adm", "ADM1")

    out_dir = Path(cfg["global"]["out_dir"]) / "boundaries"
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"geoboundaries_{iso3}_{adm}.zip"
    if out_path.exists() and not force:
        log(f"geoBoundaries: exists, skipping {out_path}")
        return

    api = f"https://www.geoboundaries.org/api/current/gbOpen/{iso3}/{adm}/"
    meta = requests.get(api, timeout=timeout).json()

    # Prefer ZIP if available
    url = meta.get("staticDownloadLink") or meta.get("downloadURL") or meta.get("gjDownloadURL")
    if not url:
        raise KeyError(f"No download URL found in geoBoundaries metadata. Keys: {list(meta.keys())}")

    log(f"geoBoundaries: downloading {iso3}/{adm} from {url}")
    z = requests.get(url, timeout=timeout).content
    out_path.write_bytes(z)
    log(f"geoBoundaries: saved {out_path}")
