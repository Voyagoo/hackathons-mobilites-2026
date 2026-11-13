"""Shared paths and analysis parameters for the pipeline."""

import datetime as dt
from dataclasses import dataclass

from utils.loaders import DATA_DIR, PROCESSED_DIR

# --- Inputs ------------------------------------------------------------------

IDF_REGION = "11"

COMMUNES_GEOJSON = DATA_DIR / "Communes, cantons et Epci 2025 - Admin Express COG PLUS IGN" / "a-com2025.geojson"
# Optional: Paris arrondissement boundaries (opendata.paris.fr, "arrondissements", ODbL). When present,
# Paris is split into its 20 arrondissements instead of one point.
PARIS_ARR_GEOJSON = DATA_DIR / "paris_arrondissements" / "arrondissements.geojson"
PARIS_CODE = "75056"
EMP1_CSV = DATA_DIR / "DS_RP_TD_EMPLOI_LT_AGEEMPFORM_COMP_2023_CSV_FR" / "DS_RP_TD_EMPLOI_LT_AGEEMPFORM_COMP_2023_data.csv"
NAV_CSV = DATA_DIR / "DS_RP_TD_NAVETTES_SEXTRANSPORT_COMP_2023_CSV_FR" / "DS_RP_TD_NAVETTES_SEXTRANSPORT_COMP_2023_data.csv"
POPULATION_CSV = DATA_DIR / "ensemble" / "donnees_communes.csv"
ZONES_CSV = DATA_DIR / "Base_des_zone_d_emploi(composition_communale)" / "base-des-zones-demploi.csv"
INCOME_GLOB = "revenu_des_*/revenu-des-francais-a-la-commune-*.csv"  # folder name has an accent

GTFS_DIR = DATA_DIR / "IDFM-gtfs"
OSM_URL = "https://download.geofabrik.de/europe/france/ile-de-france-latest.osm.pbf"
OSM_PBF = DATA_DIR / "osm" / "ile-de-france-latest.osm.pbf"

# --- Outputs -----------------------------------------------------------------

COMMUNES_PARQUET = PROCESSED_DIR / "communes.parquet"
GTFS_ZIP = PROCESSED_DIR / "idfm-gtfs.zip"
TTM_DIR = PROCESSED_DIR / "ttm"
ACCESS_PARQUET = PROCESSED_DIR / "access.parquet"
SUMMARY_PARQUET = PROCESSED_DIR / "access_summary.parquet"

# --- Analysis parameters -----------------------------------------------------

THRESHOLDS_MIN = [30, 45, 60]
MAX_TRAVEL_TIME = dt.timedelta(minutes=90)
# Transit: R5 computes one trip per departure minute in a window centred on the scenario time
# (08:30 -> 08:00 to 09:00), and we keep the 25th percentile. One hour covers a full cycle of an
# hourly train, so the result no longer depends on where that train falls in the window; the
# 25th percentile stands for a traveller who roughly times their departure to the timetable.
# (A 30-minute window with the median made Mormant "miss" its 08:25 train on every departure.)
DEPARTURE_WINDOW = dt.timedelta(minutes=60)
TRANSIT_PERCENTILE = 25
JVM_MAX_MEMORY = "10G"  # of 16 GB on the dev machine


@dataclass(frozen=True)
class Scenario:
    name: str
    mode: str  # "transit" or "car"
    departure: dt.datetime
    label: str


# GTFS calendar covers 2026-11-07 to 2026-12-09. Tue 17 Nov is a normal weekday
# (Wed 11 Nov is a public holiday). Car times in R5 do not depend on the clock
# (free-flow, no traffic), so the car benchmark has a single scenario.
TUESDAY = dt.date(2026, 11, 17)
SATURDAY = dt.date(2026, 11, 21)


def _at(day: dt.date, hour: int, minute: int = 0) -> dt.datetime:
    return dt.datetime.combine(day, dt.time(hour, minute))


SCENARIOS = [
    Scenario("transit_tue_0830", "transit", _at(TUESDAY, 8, 30), "Transit, weekday around 08:30 (peak)"),
    Scenario("car_tue_0830", "car", _at(TUESDAY, 8, 30), "Car, free-flow"),
    Scenario("transit_tue_0500", "transit", _at(TUESDAY, 5, 0), "Transit, weekday around 05:00 (early shift)"),
    Scenario("transit_tue_2230", "transit", _at(TUESDAY, 22, 30), "Transit, weekday around 22:30 (late shift)"),
    Scenario("transit_tue_1200", "transit", _at(TUESDAY, 12, 0), "Transit, weekday around 12:00 (off-peak)"),
    Scenario("transit_sat_0830", "transit", _at(SATURDAY, 8, 30), "Transit, Saturday around 08:30"),
]
SCENARIOS_BY_NAME = {s.name: s for s in SCENARIOS}
