# src/maize_data/io.py
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Callable

import yaml
from dotenv import load_dotenv

def setup_env() -> None:
    load_dotenv(override=False)

def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def make_logger(log_dir: str) -> Callable[[str], None]:
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_path = Path(log_dir) / "download.log"

    def log(msg: str) -> None:
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {msg}"
        print(line)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    return log

def http_settings(cfg: dict[str, Any]) -> tuple[int, float]:
    g = cfg.get("global", {})
    timeout = int(os.getenv("HTTP_TIMEOUT", g.get("http_timeout", 120)))
    sleep_s = float(os.getenv("HTTP_SLEEP_SECONDS", g.get("http_sleep_seconds", 1.0)))
    return timeout, sleep_s

def should_skip(path: Path, force: bool) -> bool:
    return path.exists() and (not force)
