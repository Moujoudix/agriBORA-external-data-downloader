from __future__ import annotations

import re
import zipfile
from pathlib import Path

import pandas as pd

try:
    import geopandas as gpd
except ImportError as e:
    raise SystemExit(
        "Missing dependency: geopandas. Add `geopandas` to requirements.extra.in and run `make install`."
    ) from e


def norm_name(s: str) -> str:
    s = s.strip().lower()
    s = s.replace("’", "'")
    s = re.sub(r"[’']", "", s)           # Murang'a -> muranga
    s = re.sub(r"[\s\-]+", " ", s)       # Trans-Nzoia -> trans nzoia
    return re.sub(r"\s+", " ", s).strip()


def slugify(s: str) -> str:
    s = norm_name(s)
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


def pick_name_column(gdf: "gpd.GeoDataFrame") -> str:
    candidates = ["shapeName", "NAME_1", "name", "admin1Name", "ADM1_EN", "ADM1NAME"]
    for c in candidates:
        if c in gdf.columns:
            return c
    raise RuntimeError(f"Could not find an ADM1 name column. Columns: {list(gdf.columns)}")


def extract_preferred_geojson_from_zip(zip_path: Path) -> Path:
    """
    Extracts the canonical geoBoundaries GeoJSON (not metadata, not simplified) from the zip.
    Prefers: geoBoundaries-*-ADM1.geojson
    """
    if not zip_path.exists():
        raise FileNotFoundError(f"Boundary zip not found: {zip_path}")

    extract_dir = zip_path.parent / (zip_path.stem + "_extracted")
    extract_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as z:
        names = z.namelist()
        lower = [n.lower().replace("\\", "/") for n in names]

        # 1) Prefer the main ADM1 geojson
        preferred = None
        for orig, low in zip(names, lower):
            if low.endswith(".geojson") and "metadata" not in low and "simplified" not in low:
                # strongest match: ends with -adm1.geojson (your case)
                if low.endswith("-adm1.geojson"):
                    preferred = orig
                    break
                # otherwise keep as a fallback candidate
                preferred = preferred or orig

        # 2) If not found, allow simplified geojson (still fine for centroids)
        if preferred is None:
            for orig, low in zip(names, lower):
                if low.endswith(".geojson") and "metadata" not in low:
                    preferred = orig
                    break

        if preferred is None:
            raise RuntimeError(f"No usable .geojson found inside {zip_path}. Sample: {names[:30]}")

        out_path = extract_dir / Path(preferred).name
        if not out_path.exists():
            z.extract(preferred, extract_dir)
            nested = extract_dir / preferred
            if nested.exists() and nested != out_path:
                out_path.parent.mkdir(parents=True, exist_ok=True)
                nested.rename(out_path)

    return out_path


def build_points(zip_path: Path, out_csv: Path) -> None:
    geojson_path = extract_preferred_geojson_from_zip(zip_path)

    # Read the extracted geojson
    gdf = gpd.read_file(geojson_path)

    name_col = pick_name_column(gdf)
    gdf = gdf.copy()
    gdf["county_name"] = gdf[name_col].astype(str)

    # Compute centroids safely: project -> centroid -> back to WGS84
    gdf_3857 = gdf.to_crs(epsg=3857)
    cent = gdf_3857.geometry.centroid
    cent_wgs84 = gpd.GeoSeries(cent, crs="EPSG:3857").to_crs(epsg=4326)

    out = pd.DataFrame({
        "id": gdf["county_name"].map(slugify),
        "name": gdf["county_name"],
        "lat": cent_wgs84.y.astype(float),
        "lon": cent_wgs84.x.astype(float),
    }).sort_values("name").reset_index(drop=True)

    # Sanity check: ids should be unique
    dup = out["id"][out["id"].duplicated()].unique().tolist()
    if dup:
        raise RuntimeError(
            f"Non-unique ids after slugify. Duplicates: {dup}. "
            f"Consider appending a suffix for colliding names."
        )

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_csv, index=False)
    print(f"✅ Wrote {out_csv} rows={len(out)} (from {geojson_path.name})")


def main() -> None:
    zip_path = Path("data_raw/boundaries/geoboundaries_KEN_ADM1.zip")
    out_csv = Path("configs/points.csv")
    build_points(zip_path=zip_path, out_csv=out_csv)


if __name__ == "__main__":
    main()
