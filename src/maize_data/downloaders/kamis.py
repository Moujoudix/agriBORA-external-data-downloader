# src/maize_data/downloaders/kamis.py
from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any, Callable

import pandas as pd
import requests
from bs4 import BeautifulSoup

from maize_data.io import http_settings
from io import StringIO

BASE = "https://kamis.kilimo.go.ke/site/market"

def _norm(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s

def _fetch_product_catalog(session: requests.Session, timeout: int) -> pd.DataFrame:
    """
    Returns a DataFrame with columns: product_id (int), product_name (str)
    Parsed from the <select> dropdown on the market page.
    """
    r = session.get(BASE, timeout=timeout)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")

    # Find the product select. Most pages use name="product".
    sel = soup.find("select", attrs={"name": "product"})
    if sel is None:
        # fallback: first select that contains an option with "Dry Maize"
        selects = soup.find_all("select")
        for s in selects:
            if s.find(string=re.compile(r"Dry\s+Maize", re.I)):
                sel = s
                break
    if sel is None:
        raise RuntimeError("Could not locate product dropdown (<select name='product'>) on KAMIS market page.")

    rows = []
    for opt in sel.find_all("option"):
        val = (opt.get("value") or "").strip()
        name = re.sub(r"\s+", " ", (opt.text or "").strip())
        if not val or not val.isdigit():
            continue
        rows.append({"product_id": int(val), "product_name": name})

    if not rows:
        raise RuntimeError("Parsed product dropdown but found no numeric option values.")
    df = pd.DataFrame(rows).sort_values("product_id").reset_index(drop=True)
    return df

def _resolve_product_id(products_df: pd.DataFrame, requested_name: str) -> int:
    """
    Resolves a config product string (e.g. 'Dry Maize') to a product_id using normalized matching.
    Raises with helpful candidates if ambiguous/missing.
    """
    target = _norm(requested_name)
    products_df = products_df.copy()
    products_df["key"] = products_df["product_name"].map(_norm)

    exact = products_df[products_df["key"] == target]
    if len(exact) == 1:
        return int(exact.iloc[0]["product_id"])
    if len(exact) > 1:
        ids = exact["product_id"].tolist()
        raise ValueError(f"Ambiguous product name '{requested_name}'. Matches multiple ids: {ids}")

    # fallback: contains match
    contains = products_df[products_df["key"].str.contains(re.escape(target), na=False)]
    if len(contains) == 1:
        return int(contains.iloc[0]["product_id"])
    if len(contains) > 1:
        sample = contains[["product_id", "product_name"]].head(10).to_dict(orient="records")
        raise ValueError(
            f"Ambiguous product '{requested_name}'. Did you mean one of: {sample} (showing up to 10)"
        )

    # no match
    sample = products_df[["product_id", "product_name"]].head(30).to_dict(orient="records")
    raise ValueError(
        f"Unknown product '{requested_name}'. Check KAMIS dropdown. First options: {sample} (showing 30)"
    )

def _read_market_table(html: str) -> pd.DataFrame:
    """
    KAMIS page has a single main table; pandas.read_html usually returns it.
    """
    tables = pd.read_html(StringIO(html), flavor="lxml")
    if not tables:
        return pd.DataFrame()

    # Prefer the table that contains the expected header
    for t in tables:
        cols = [str(c).strip().lower() for c in t.columns]
        if "commodity" in cols and "county" in cols and "date" in cols:
            return t

    return tables[-1]

def run_kamis(cfg: dict[str, Any], log: Callable[[str], None]) -> None:
    force = bool(cfg["global"].get("force_download", False))
    timeout, sleep_s = http_settings(cfg)

    s = cfg["sources"]["kamis"]
    out_dir = Path(cfg["global"]["out_dir"]) / "kamis"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Config knobs (new)
    products = s.get("products", ["Dry Maize"])
    per_page = int(s.get("per_page", 3000))
    max_offsets = int(s.get("max_offsets", 1000))  # safety cap

    # Cache product catalog locally (so you can inspect ids & names)
    products_csv = out_dir / "_products.csv"

    session = requests.Session()

    if products_csv.exists() and not force:
        prod_df = pd.read_csv(products_csv)
    else:
        log("KAMIS: fetching product dropdown catalog")
        prod_df = _fetch_product_catalog(session, timeout=timeout)
        prod_df.to_csv(products_csv, index=False)
        log(f"KAMIS: saved product catalog -> {products_csv} (n={len(prod_df)})")

    for prod_name in products:
        pid = _resolve_product_id(prod_df, prod_name)
        slug = re.sub(r"[^a-z0-9]+", "_", _norm(prod_name)).strip("_")

        out_path = out_dir / f"kamis_product{pid}_{slug}_perpage{per_page}.csv"
        if out_path.exists() and not force:
            log(f"KAMIS: exists, skipping {out_path.name}")
            continue

        log(f"KAMIS: downloading product='{prod_name}' id={pid} per_page={per_page}")

        chunks: list[pd.DataFrame] = []
        for i in range(max_offsets):
            offset = i * per_page
            url = f"{BASE}/{offset}" if offset > 0 else BASE
            params = {"product": pid, "per_page": per_page}

            try:
                r = session.get(url, params=params, timeout=timeout)
                r.raise_for_status()
                df = _read_market_table(r.text)

                # Stop if no rows
                if df.empty:
                    log(f"KAMIS: offset={offset} -> empty, stopping.")
                    break

                df["product_id"] = pid
                df["product_name"] = prod_name
                df["offset"] = offset
                chunks.append(df)

                log(f"KAMIS: offset={offset} rows={len(df)}")
                time.sleep(sleep_s)

                # If the page returned fewer rows than per_page, it's likely the last chunk.
                if len(df) < per_page:
                    break

            except Exception as e:
                log(f"KAMIS: offset={offset} error: {e}")
                break

        if chunks:
            out = pd.concat(chunks, ignore_index=True)

            # light de-dup, just in case pagination overlaps
            key_cols = [c for c in ["Commodity", "Classification", "Market", "County", "Date"] if c in out.columns]
            if key_cols:
                out = out.drop_duplicates(subset=key_cols + ["Wholesale", "Retail"], keep="last")

            out.to_csv(out_path, index=False)
            log(f"KAMIS: saved {out_path} rows={len(out)}")
        else:
            log(f"KAMIS: no data for product='{prod_name}' (id={pid})")
