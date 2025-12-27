# src/maize_data/downloaders/url_list_downloader.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import requests
from maize_data.io import http_settings

def run_url_list(cfg: dict[str, Any], log: Callable[[str], None], key: str) -> None:
    timeout, sleep_s = http_settings(cfg)
    s = cfg["sources"][key]
    urls_file = Path(s["urls_file"])

    out_dir = Path(cfg["global"]["out_dir"]) / key
    out_dir.mkdir(parents=True, exist_ok=True)

    urls = [u.strip() for u in urls_file.read_text(encoding="utf-8").splitlines() if u.strip() and not u.strip().startswith("#")]
    if not urls:
        log(f"{key}: no URLs found in {urls_file}")
        return

    for i, url in enumerate(urls, 1):
        name = url.split("/")[-1] or f"file_{i}"
        out_path = out_dir / name
        if out_path.exists():
            log(f"{key}: exists, skipping {out_path.name}")
            continue
        log(f"{key}: downloading {i}/{len(urls)} {name}")
        r = requests.get(url, stream=True, timeout=timeout)
        r.raise_for_status()
        with out_path.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                if chunk:
                    f.write(chunk)
        if sleep_s:
            import time
            time.sleep(sleep_s)
        log(f"{key}: saved {out_path}")
