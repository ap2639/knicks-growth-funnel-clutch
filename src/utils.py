from __future__ import annotations

import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DOCS_DATA_DIR = PROJECT_ROOT / "docs" / "data"

KNICKS_TEAM_ID = 1610612752
KNICKS_FULL_NAME = "New York Knicks"
DEFAULT_START_YEAR = 2021
DEFAULT_END_YEAR = 2024


def ensure_directories() -> None:
    """Create project output folders if they do not exist yet."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DATA_DIR.mkdir(parents=True, exist_ok=True)


def sleep_between_calls(seconds: float = 0.8) -> None:
    """Pause between NBA API requests to reduce throttling issues."""
    time.sleep(seconds)


def season_strings(start_year: int, end_year: int) -> list[str]:
    """Build NBA season labels such as 2021-22, 2022-23, and so on."""
    return [f"{year}-{str(year + 1)[-2:]}" for year in range(start_year, end_year + 1)]


def percent(series) -> float:
    """Convert a boolean/integer series mean into a percentage."""
    return round(float(series.mean()) * 100, 1)
