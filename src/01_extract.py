from __future__ import annotations

from pathlib import Path

import pandas as pd
from nba_api.stats.endpoints import (
    leaguedashplayerclutch,
    leaguedashteamclutch,
    teamgamelogs,
)
from nba_api.stats.static import teams

from utils import (
    DEFAULT_END_YEAR,
    DEFAULT_START_YEAR,
    KNICKS_FULL_NAME,
    RAW_DIR,
    ensure_directories,
    season_strings,
    sleep_between_calls,
)


def get_team_id(team_full_name: str) -> int:
    """Look up a team's NBA ID from its full name."""
    for team in teams.get_teams():
        if team["full_name"] == team_full_name:
            return int(team["id"])
    raise ValueError(f"Could not find team named {team_full_name!r}.")


def save_csv(df: pd.DataFrame, path: Path) -> None:
    """Save a DataFrame and print a friendly status message."""
    df.to_csv(path, index=False)
    print(f"Saved {path.name}: {len(df):,} rows x {df.shape[1]} columns")


def extract_knicks_games(seasons: list[str], knicks_team_id: int) -> pd.DataFrame:
    """Download regular-season Knicks game logs for each requested season."""
    frames: list[pd.DataFrame] = []

    for season in seasons:
        print(f"Downloading Knicks game logs for {season}...")
        response = teamgamelogs.TeamGameLogs(
            season_nullable=season,
            season_type_nullable="Regular Season",
            team_id_nullable=knicks_team_id,
        )
        frame = response.get_data_frames()[0].copy()
        frame["SEASON"] = season
        frames.append(frame)
        sleep_between_calls()

    return pd.concat(frames, ignore_index=True)


def extract_team_clutch(seasons: list[str]) -> pd.DataFrame:
    """Download league clutch team stats for each requested season."""
    frames: list[pd.DataFrame] = []

    for season in seasons:
        print(f"Downloading league team clutch stats for {season}...")
        response = leaguedashteamclutch.LeagueDashTeamClutch(
            season=season,
            season_type_all_star="Regular Season",
            clutch_time="Last 5 Minutes",
            ahead_behind="Ahead or Behind",
        )
        frame = response.get_data_frames()[0].copy()
        frame["SEASON"] = season
        frames.append(frame)
        sleep_between_calls()

    return pd.concat(frames, ignore_index=True)


def extract_player_clutch(seasons: list[str]) -> pd.DataFrame:
    """Download league clutch player stats for each requested season."""
    frames: list[pd.DataFrame] = []

    for season in seasons:
        print(f"Downloading league player clutch stats for {season}...")
        response = leaguedashplayerclutch.LeagueDashPlayerClutch(
            season=season,
            season_type_all_star="Regular Season",
            clutch_time="Last 5 Minutes",
            ahead_behind="Ahead or Behind",
        )
        frame = response.get_data_frames()[0].copy()
        frame["SEASON"] = season
        frames.append(frame)
        sleep_between_calls()

    return pd.concat(frames, ignore_index=True)


def main() -> None:
    ensure_directories()
    seasons = season_strings(DEFAULT_START_YEAR, DEFAULT_END_YEAR)
    knicks_team_id = get_team_id(KNICKS_FULL_NAME)

    print(f"Project raw data directory: {RAW_DIR}")
    print(f"Downloading seasons: {', '.join(seasons)}")
    print(f"Knicks team ID: {knicks_team_id}")

    knicks_games = extract_knicks_games(seasons, knicks_team_id)
    team_clutch = extract_team_clutch(seasons)
    player_clutch = extract_player_clutch(seasons)

    save_csv(knicks_games, RAW_DIR / "knicks_games_raw.csv")
    save_csv(team_clutch, RAW_DIR / "team_clutch_raw.csv")
    save_csv(player_clutch, RAW_DIR / "player_clutch_raw.csv")

    print("Extraction complete.")


if __name__ == "__main__":
    main()
