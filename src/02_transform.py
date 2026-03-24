from __future__ import annotations

from pathlib import Path

import pandas as pd

from utils import PROCESSED_DIR, RAW_DIR, ensure_directories, percent


RIVAL_OPPONENTS = {"BOS", "BKN", "PHI", "MIA", "LAL"}


def parse_matchup(matchup: str) -> tuple[str, str]:
    """Turn a matchup string into opponent code and home/away label."""
    opponent = matchup.split()[-1]
    home_away = "HOME" if "vs." in matchup or "vs " in matchup else "AWAY"
    return opponent, home_away


def build_game_facts(games: pd.DataFrame) -> pd.DataFrame:
    """Create game-level growth funnel and clutch-oriented metrics."""
    games = games.copy()
    games["GAME_DATE"] = pd.to_datetime(games["GAME_DATE"])
    games = games.sort_values("GAME_DATE").reset_index(drop=True)

    games["PTS_DIFF"] = games["PLUS_MINUS"]
    games["MARGIN"] = games["PTS_DIFF"].abs()
    games["IS_WIN"] = (games["WL"] == "W").astype(int)
    games["IS_CLOSE"] = (games["MARGIN"] <= 5).astype(int)
    games["OPP_ABBR"], games["HOME_AWAY"] = zip(*games["MATCHUP"].map(parse_matchup))
    games["IS_RIVALRY"] = games["OPP_ABBR"].isin(RIVAL_OPPONENTS).astype(int)
    games["IS_STAR_MOMENT"] = ((games["PTS"] >= 120) & (games["IS_CLOSE"] == 1)).astype(int)
    games["IS_BLOWOUT_WIN"] = ((games["IS_WIN"] == 1) & (games["MARGIN"] >= 15)).astype(int)

    # Beginner-friendly growth funnel:
    # Awareness: every game creates baseline visibility.
    # Activation: high-energy games with a strong emotional hook.
    # Engagement: repeated activation within a short rolling window.
    # Retention: activated weeks that continue into the next week.
    games["AWARENESS_EVENT"] = 1
    games["ACTIVATION_SCORE"] = (
        3 * games["IS_CLOSE"]
        + 1 * games["IS_RIVALRY"]
        + 1 * games["IS_STAR_MOMENT"]
        + 1 * games["IS_WIN"]
        + 1 * games["IS_BLOWOUT_WIN"]
    )
    games["ACTIVATION_EVENT"] = (games["ACTIVATION_SCORE"] >= 4).astype(int)

    rolling = games.set_index("GAME_DATE")
    rolling["ACTIVATIONS_LAST_7D"] = rolling["ACTIVATION_EVENT"].rolling("7D").sum()
    rolling["ENGAGEMENT_EVENT"] = (rolling["ACTIVATIONS_LAST_7D"] >= 2).astype(int)
    games = rolling.reset_index()

    games["ISO_YEAR"] = games["GAME_DATE"].dt.isocalendar().year.astype(int)
    games["ISO_WEEK"] = games["GAME_DATE"].dt.isocalendar().week.astype(int)
    games["MONTH"] = games["GAME_DATE"].dt.strftime("%b %Y")
    games["GAME_NUMBER"] = games.groupby("SEASON").cumcount() + 1
    games["RESULT_LABEL"] = games["WL"].map({"W": "Win", "L": "Loss"})
    games["FAN_STAGE"] = "Aware"
    games.loc[games["ACTIVATION_EVENT"] == 1, "FAN_STAGE"] = "Activated"
    games.loc[games["ENGAGEMENT_EVENT"] == 1, "FAN_STAGE"] = "Engaged"

    return games[
        [
            "SEASON",
            "GAME_DATE",
            "GAME_NUMBER",
            "MATCHUP",
            "HOME_AWAY",
            "OPP_ABBR",
            "WL",
            "RESULT_LABEL",
            "PTS",
            "PTS_DIFF",
            "MARGIN",
            "IS_WIN",
            "IS_CLOSE",
            "IS_RIVALRY",
            "IS_STAR_MOMENT",
            "IS_BLOWOUT_WIN",
            "ACTIVATION_SCORE",
            "AWARENESS_EVENT",
            "ACTIVATION_EVENT",
            "ACTIVATIONS_LAST_7D",
            "ENGAGEMENT_EVENT",
            "FAN_STAGE",
            "MONTH",
            "ISO_YEAR",
            "ISO_WEEK",
        ]
    ].copy()


def build_weekly_retention(game_facts: pd.DataFrame) -> pd.DataFrame:
    """Aggregate the game facts into a weekly retention table."""
    weekly = (
        game_facts.groupby(["SEASON", "ISO_YEAR", "ISO_WEEK"], as_index=False)
        .agg(
            WEEK_START=("GAME_DATE", "min"),
            GAMES_PLAYED=("GAME_DATE", "size"),
            WEEKLY_AWARENESS=("AWARENESS_EVENT", "sum"),
            WEEKLY_ACTIVATION=("ACTIVATION_EVENT", "sum"),
            WEEKLY_ENGAGEMENT=("ENGAGEMENT_EVENT", "sum"),
            AVG_ACTIVATION_SCORE=("ACTIVATION_SCORE", "mean"),
        )
        .sort_values(["SEASON", "WEEK_START"])
        .reset_index(drop=True)
    )
    weekly["ACTIVATED_WEEK"] = (weekly["WEEKLY_ACTIVATION"] >= 1).astype(int)
    weekly["RETENTION_EVENT"] = (
        (weekly["ACTIVATED_WEEK"] == 1)
        & (weekly.groupby("SEASON")["ACTIVATED_WEEK"].shift(1).fillna(0) == 1)
    ).astype(int)
    weekly["WEEK_START"] = pd.to_datetime(weekly["WEEK_START"]).dt.strftime("%Y-%m-%d")
    weekly["AVG_ACTIVATION_SCORE"] = weekly["AVG_ACTIVATION_SCORE"].round(2)
    return weekly


def build_season_summary(game_facts: pd.DataFrame, weekly: pd.DataFrame) -> pd.DataFrame:
    """Create a simple season summary table for the dashboard."""
    summary = (
        game_facts.groupby("SEASON", as_index=False)
        .agg(
            GAMES=("SEASON", "size"),
            AWARENESS=("AWARENESS_EVENT", "sum"),
            ACTIVATION=("ACTIVATION_EVENT", "sum"),
            ENGAGEMENT=("ENGAGEMENT_EVENT", "sum"),
            AVG_ACTIVATION_SCORE=("ACTIVATION_SCORE", "mean"),
            CLOSE_GAME_RATE=("IS_CLOSE", "mean"),
            WIN_RATE=("IS_WIN", "mean"),
        )
        .sort_values("SEASON")
    )
    retention = (
        weekly.groupby("SEASON", as_index=False)
        .agg(
            RETAINED_WEEKS=("RETENTION_EVENT", "sum"),
            RETENTION_RATE=("RETENTION_EVENT", "mean"),
        )
        .sort_values("SEASON")
    )
    summary = summary.merge(retention, on="SEASON", how="left")

    for column in ["CLOSE_GAME_RATE", "WIN_RATE", "RETENTION_RATE"]:
        summary[column] = (summary[column] * 100).round(1)
    summary["ACTIVATION_RATE"] = (
        game_facts.groupby("SEASON")["ACTIVATION_EVENT"].mean().mul(100).round(1).values
    )
    summary["ENGAGEMENT_RATE"] = (
        game_facts.groupby("SEASON")["ENGAGEMENT_EVENT"].mean().mul(100).round(1).values
    )
    summary["AVG_ACTIVATION_SCORE"] = summary["AVG_ACTIVATION_SCORE"].round(2)
    return summary


def main() -> None:
    ensure_directories()
    raw_games_path = RAW_DIR / "knicks_games_raw.csv"
    if not raw_games_path.exists():
        raise FileNotFoundError(f"Missing raw file: {raw_games_path}")

    games = pd.read_csv(raw_games_path)
    game_facts = build_game_facts(games)
    weekly = build_weekly_retention(game_facts)
    season_summary = build_season_summary(game_facts, weekly)

    game_facts.to_csv(PROCESSED_DIR / "fact_knicks_games.csv", index=False)
    weekly.to_csv(PROCESSED_DIR / "fact_weekly_retention.csv", index=False)
    season_summary.to_csv(PROCESSED_DIR / "fact_season_summary.csv", index=False)

    print(f"Saved {PROCESSED_DIR / 'fact_knicks_games.csv'}")
    print(f"Saved {PROCESSED_DIR / 'fact_weekly_retention.csv'}")
    print(f"Saved {PROCESSED_DIR / 'fact_season_summary.csv'}")


if __name__ == "__main__":
    main()
