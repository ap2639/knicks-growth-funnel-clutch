from __future__ import annotations

import json
import shutil

import pandas as pd

from utils import DOCS_DATA_DIR, KNICKS_TEAM_ID, PROCESSED_DIR, RAW_DIR, ensure_directories


def copy_to_docs(filename: str) -> None:
    """Copy a processed CSV into the docs data folder for the static dashboard."""
    source = PROCESSED_DIR / filename
    destination = DOCS_DATA_DIR / filename
    shutil.copy2(source, destination)
    print(f"Copied {source.name} -> {destination}")


def write_dashboard_data_bundle() -> None:
    """Create a JS fallback bundle so the dashboard can open without a local server."""
    bundle = {
        "games": pd.read_csv(PROCESSED_DIR / "fact_knicks_games.csv").to_dict(orient="records"),
        "weekly": pd.read_csv(PROCESSED_DIR / "fact_weekly_retention.csv").to_dict(orient="records"),
        "players": pd.read_csv(PROCESSED_DIR / "fact_player_clutch_knicks.csv").to_dict(orient="records"),
        "teams": pd.read_csv(PROCESSED_DIR / "fact_team_clutch_knicks.csv").to_dict(orient="records"),
        "seasons": pd.read_csv(PROCESSED_DIR / "fact_season_summary.csv").to_dict(orient="records"),
    }
    output = DOCS_DATA_DIR / "dashboard-data.js"
    output.write_text(
        "window.__KNICKS_DASHBOARD_DATA__ = " + json.dumps(bundle, separators=(",", ":")) + ";",
        encoding="utf-8",
    )
    print(f"Created fallback bundle -> {output}")


def main() -> None:
    ensure_directories()

    team_path = RAW_DIR / "team_clutch_raw.csv"
    player_path = RAW_DIR / "player_clutch_raw.csv"
    if not team_path.exists() or not player_path.exists():
        raise FileNotFoundError(
            "Missing raw clutch files. Run src/01_extract.py before src/03_export.py."
        )

    team_clutch = pd.read_csv(team_path)
    player_clutch = pd.read_csv(player_path)

    team_clutch.to_csv(PROCESSED_DIR / "fact_team_clutch_league.csv", index=False)
    player_clutch.to_csv(PROCESSED_DIR / "fact_player_clutch_league.csv", index=False)
    team_clutch[team_clutch["TEAM_ID"] == KNICKS_TEAM_ID].to_csv(
        PROCESSED_DIR / "fact_team_clutch_knicks.csv", index=False
    )
    player_clutch[player_clutch["TEAM_ID"] == KNICKS_TEAM_ID].to_csv(
        PROCESSED_DIR / "fact_player_clutch_knicks.csv", index=False
    )

    for filename in [
        "fact_knicks_games.csv",
        "fact_weekly_retention.csv",
        "fact_season_summary.csv",
        "fact_team_clutch_knicks.csv",
        "fact_player_clutch_knicks.csv",
    ]:
        copy_to_docs(filename)

    write_dashboard_data_bundle()
    print("Export complete. Processed files are ready for the static dashboard.")


if __name__ == "__main__":
    main()
