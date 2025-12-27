# src/maize_data/manifest.py
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def sha256_text(text: str) -> str:
    h = hashlib.sha256()
    h.update(text.encode("utf-8"))
    return h.hexdigest()

def sha256_file(path: Path, chunk_size: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def try_git_rev() -> str | None:
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL).decode().strip()
        return out or None
    except Exception:
        return None

def load_manifest(path: Path) -> dict[str, Any]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {
        "schema_version": SCHEMA_VERSION,
        "project": "maize-external-data",
        "runs": [],
    }

def save_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

def list_files_recursive(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return [p for p in root.rglob("*") if p.is_file()]

def file_meta(path: Path, base_dir: Path, do_hash: bool) -> dict[str, Any]:
    st = path.stat()
    rel = str(path.relative_to(base_dir))
    meta: dict[str, Any] = {
        "path": rel,
        "bytes": st.st_size,
        "modified_utc": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).replace(microsecond=0).isoformat(),
    }
    if do_hash:
        meta["sha256"] = sha256_file(path)
    return meta

@dataclass
class RunContext:
    run_id: str
    started_at: str
    config_path: str
    config_sha256: str
    git_rev: str | None
    skip_auth: bool
    force: bool
    hash_files: bool

def start_run(
    manifest_path: Path,
    config_path: Path,
    config_text: str,
    skip_auth: bool,
    force: bool,
    hash_files: bool,
) -> RunContext:
    rid = f"run_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    ctx = RunContext(
        run_id=rid,
        started_at=utc_now_iso(),
        config_path=str(config_path),
        config_sha256=sha256_text(config_text),
        git_rev=try_git_rev(),
        skip_auth=skip_auth,
        force=force,
        hash_files=hash_files,
    )

    manifest = load_manifest(manifest_path)
    manifest["runs"].append(
        {
            "run_id": ctx.run_id,
            "started_at": ctx.started_at,
            "ended_at": None,
            "config_path": ctx.config_path,
            "config_sha256": ctx.config_sha256,
            "git_rev": ctx.git_rev,
            "skip_auth": ctx.skip_auth,
            "force": ctx.force,
            "hash_files": ctx.hash_files,
            "sources": {},
            "notes": [],
        }
    )
    save_manifest(manifest_path, manifest)
    return ctx

def append_note(manifest_path: Path, run_id: str, note: str) -> None:
    manifest = load_manifest(manifest_path)
    run = next(r for r in manifest["runs"] if r["run_id"] == run_id)
    run.setdefault("notes", []).append({"at": utc_now_iso(), "note": note})
    save_manifest(manifest_path, manifest)

def record_source(
    manifest_path: Path,
    run_id: str,
    source_name: str,
    source_params: dict[str, Any],
    base_out_dir: Path,
    source_out_dir: Path,
    hash_files: bool,
) -> None:
    files = list_files_recursive(source_out_dir)
    payload = {
        "params": source_params,
        "out_dir": str(source_out_dir.relative_to(base_out_dir)) if source_out_dir.exists() else str(source_out_dir),
        "file_count": len(files),
        "files": [file_meta(p, base_out_dir, hash_files) for p in sorted(files)],
        "recorded_at": utc_now_iso(),
    }

    manifest = load_manifest(manifest_path)
    run = next(r for r in manifest["runs"] if r["run_id"] == run_id)
    run["sources"][source_name] = payload
    save_manifest(manifest_path, manifest)

def end_run(manifest_path: Path, run_id: str) -> None:
    manifest = load_manifest(manifest_path)
    run = next(r for r in manifest["runs"] if r["run_id"] == run_id)
    run["ended_at"] = utc_now_iso()
    save_manifest(manifest_path, manifest)
