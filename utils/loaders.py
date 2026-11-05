"""Load datasets from data/. Paths work from notebooks and from the app."""

from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT_DIR    = Path(__file__).resolve().parent.parent
DATA_DIR    = ROOT_DIR / "data"
FIGURES_DIR = ROOT_DIR / "outputs" / "figures"


def load_csv(name: str, **kwargs) -> pd.DataFrame:
    """Read data/<name> as a CSV. Extra arguments go to pandas.read_csv."""
    return pd.read_csv(DATA_DIR / name, **kwargs)


def load_parquet(name: str, **kwargs) -> pd.DataFrame:
    """Read data/<name> as a Parquet file."""
    return pd.read_parquet(DATA_DIR / name, **kwargs)


def load_geo(name: str, **kwargs) -> gpd.GeoDataFrame:
    """Read data/<name> as a geographic file (GeoJSON, GeoPackage, Shapefile...)."""
    return gpd.read_file(DATA_DIR / name, **kwargs)
