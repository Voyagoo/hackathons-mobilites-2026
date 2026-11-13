"""Step 2: prepare the routing inputs for r5py.

- Download the Île-de-France OpenStreetMap extract (Geofabrik, ODbL), about 330 MB.
- Zip the unzipped IDFM GTFS folder, because r5py expects a GTFS .zip file.
- Check that every scenario departure date is covered by the GTFS calendar.

Run: uv run python -m pipeline.network_inputs
"""

import datetime as dt
import zipfile

import pandas as pd
import requests

from pipeline.config import GTFS_DIR, GTFS_ZIP, OSM_PBF, OSM_URL, SCENARIOS


def download_osm() -> None:
    if OSM_PBF.exists():
        print(f"OSM extract already present: {OSM_PBF} ({OSM_PBF.stat().st_size / 1e6:,.0f} MB)")
        return

    OSM_PBF.parent.mkdir(parents=True, exist_ok=True)
    partial = OSM_PBF.with_suffix(".part")
    print(f"downloading {OSM_URL}")
    with requests.get(OSM_URL, stream=True, timeout=60) as response:
        response.raise_for_status()
        with partial.open("wb") as f:
            for chunk in response.iter_content(chunk_size=8 * 1024 * 1024):
                f.write(chunk)
    partial.rename(OSM_PBF)  # only a complete download gets the final name
    print(f"wrote {OSM_PBF} ({OSM_PBF.stat().st_size / 1e6:,.0f} MB)")


def zip_gtfs() -> None:
    if GTFS_ZIP.exists():
        print(f"GTFS zip already present: {GTFS_ZIP}")
        return

    files = sorted(GTFS_DIR.glob("*.txt"))
    if not files:
        raise FileNotFoundError(f"no GTFS .txt files in {GTFS_DIR}")

    GTFS_ZIP.parent.mkdir(parents=True, exist_ok=True)
    partial = GTFS_ZIP.with_suffix(".part")
    with zipfile.ZipFile(partial, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for path in files:
            z.write(path, arcname=path.name)  # GTFS files must sit at the zip root
    partial.rename(GTFS_ZIP)
    print(f"wrote {GTFS_ZIP} ({GTFS_ZIP.stat().st_size / 1e6:,.0f} MB, {len(files)} files)")


def check_calendar() -> None:
    cal = pd.read_csv(GTFS_DIR / "calendar.txt", dtype=str)
    dates = pd.read_csv(GTFS_DIR / "calendar_dates.txt", dtype=str)

    start = min(cal["start_date"].min(), dates["date"].min())
    end = max(cal["end_date"].max(), dates["date"].max())
    first, last = dt.datetime.strptime(start, "%Y%m%d").date(), dt.datetime.strptime(end, "%Y%m%d").date()
    print(f"GTFS calendar: {first} to {last}")

    for s in SCENARIOS:
        if s.mode == "transit" and not first <= s.departure.date() <= last:
            raise ValueError(f"scenario {s.name} departs {s.departure:%Y-%m-%d}, outside the GTFS calendar")
    print("all transit scenarios are inside the GTFS calendar")


def main() -> None:
    check_calendar()
    zip_gtfs()
    download_osm()


if __name__ == "__main__":
    main()
