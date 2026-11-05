"""Shared chart style and figure export."""

from pathlib import Path

import seaborn as sns
from matplotlib.figure import Figure

from utils.loaders import FIGURES_DIR


def set_style() -> None:
    """Apply the team chart style. Call once at the top of a notebook."""
    sns.set_theme(
        style   = "whitegrid",
        context = "notebook",
    )


def save_figure(fig: Figure, name: str, dpi: int = 200) -> Path:
    """Save a figure to outputs/figures/<name>.png and return its path."""
    path = FIGURES_DIR / f"{name}.png"

    fig.savefig(
        path,
        dpi         = dpi,
        bbox_inches = "tight",
    )

    return path
