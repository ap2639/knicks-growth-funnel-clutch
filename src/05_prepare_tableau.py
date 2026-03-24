from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
TABLEAU_DIR = PROJECT_ROOT / "tableau"


def build_season_summary(
    games: pd.DataFrame, weekly: pd.DataFrame, team: pd.DataFrame
) -> pd.DataFrame:
    game_summary = (
        games.groupby("SEASON", as_index=False)
        .agg(
            Games=("SEASON", "size"),
            AvgEngagementScore=("ENGAGEMENT_SCORE", "mean"),
            CloseGameRate=("IS_CLOSE", "mean"),
            ActivationRate=("ACTIVATION_EVENT", "mean"),
            EngagementRate=("ENGAGEMENT_EVENT", "mean"),
            AwarenessGames=("AWARENESS_EVENT", "sum"),
            ActivationGames=("ACTIVATION_EVENT", "sum"),
            EngagementGames=("ENGAGEMENT_EVENT", "sum"),
        )
    )

    retention = (
        weekly.groupby("SEASON", as_index=False)
        .agg(
            WeeklyActivationCount=("WeekActivation", "sum"),
            RetainedWeeks=("RETENTION_EVENT", "sum"),
            RetentionRate=("RETENTION_EVENT", "mean"),
        )
    )

    team_summary = team[
        [
            "SEASON",
            "W",
            "L",
            "W_PCT",
            "PTS",
            "PLUS_MINUS",
            "W_PCT_RANK",
            "PTS_RANK",
            "PLUS_MINUS_RANK",
            "FG_PCT_RANK",
        ]
    ].rename(
        columns={
            "W": "ClutchWins",
            "L": "ClutchLosses",
            "W_PCT": "ClutchWinPct",
            "PTS": "ClutchPoints",
            "PLUS_MINUS": "ClutchPlusMinus",
            "W_PCT_RANK": "ClutchWinPctRank",
            "PTS_RANK": "ClutchPointsRank",
            "PLUS_MINUS_RANK": "ClutchPlusMinusRank",
            "FG_PCT_RANK": "ClutchFgPctRank",
        }
    )

    summary = game_summary.merge(retention, on="SEASON", how="left").merge(
        team_summary, on="SEASON", how="left"
    )

    pct_columns = [
        "CloseGameRate",
        "ActivationRate",
        "EngagementRate",
        "RetentionRate",
        "ClutchWinPct",
    ]
    for col in pct_columns:
        summary[col] = (summary[col] * 100).round(1)

    summary["AvgEngagementScore"] = summary["AvgEngagementScore"].round(2)
    summary["ClutchPlusMinus"] = summary["ClutchPlusMinus"].round(1)
    summary["Record"] = (
        summary["ClutchWins"].astype(int).astype(str)
        + "-"
        + summary["ClutchLosses"].astype(int).astype(str)
    )
    return summary.sort_values("SEASON")


def build_game_export(games: pd.DataFrame) -> pd.DataFrame:
    export = games.copy().sort_values(["SEASON", "GAME_DATE"])
    export["GAME_DATE"] = export["GAME_DATE"].dt.strftime("%Y-%m-%d")
    export["GameNumber"] = export.groupby("SEASON").cumcount() + 1
    export["ResultLabel"] = export["WL"].map({"W": "Win", "L": "Loss"})
    export["MomentType"] = "Standard"
    export.loc[export["IS_CLOSE"] == 1, "MomentType"] = "Close Game"
    export.loc[export["IS_RIVALRY"] == 1, "MomentType"] = "Rivalry"
    export.loc[export["IS_STAR_MOMENT"] == 1, "MomentType"] = "Star Moment"
    export.loc[
        (export["IS_CLOSE"] == 1) & (export["IS_RIVALRY"] == 1), "MomentType"
    ] = "Close Rivalry"
    export.loc[
        (export["IS_CLOSE"] == 1) & (export["IS_STAR_MOMENT"] == 1), "MomentType"
    ] = "Close Star Moment"
    export.loc[export["ACTIVATION_EVENT"] == 1, "FanResponseTier"] = "Activated"
    export.loc[export["ENGAGEMENT_EVENT"] == 1, "FanResponseTier"] = "Engaged"
    export["FanResponseTier"] = export["FanResponseTier"].fillna("Aware")
    return export[
        [
            "SEASON",
            "GAME_DATE",
            "GameNumber",
            "MATCHUP",
            "HOME_AWAY",
            "OPP_ABBR",
            "WL",
            "ResultLabel",
            "PTS",
            "PTS_DIFF",
            "MARGIN",
            "IS_CLOSE",
            "IS_RIVALRY",
            "IS_STAR_MOMENT",
            "ENGAGEMENT_SCORE",
            "AWARENESS_EVENT",
            "ACTIVATION_EVENT",
            "ENGAGEMENT_EVENT",
            "MomentType",
            "FanResponseTier",
            "ISO_YEAR",
            "ISO_WEEK",
        ]
    ]


def build_player_export(players: pd.DataFrame) -> pd.DataFrame:
    export = players.copy()
    export["FG_PCT"] = (export["FG_PCT"] * 100).round(1)
    export["W_PCT"] = (export["W_PCT"] * 100).round(1)
    export["PLUS_MINUS"] = export["PLUS_MINUS"].round(1)
    return export[
        [
            "SEASON",
            "PLAYER_NAME",
            "GP",
            "W",
            "L",
            "W_PCT",
            "PTS",
            "PLUS_MINUS",
            "FG_PCT",
            "FG3M",
            "AST",
            "REB",
            "STL",
            "BLK",
            "PTS_RANK",
            "PLUS_MINUS_RANK",
            "FG_PCT_RANK",
        ]
    ].sort_values(["SEASON", "PTS"], ascending=[True, False])


def build_weekly_export(weekly: pd.DataFrame) -> pd.DataFrame:
    export = weekly.copy().sort_values(["SEASON", "ISO_YEAR", "ISO_WEEK"])
    export["RetentionLabel"] = export["RETENTION_EVENT"].map(
        {1: "Retained", 0: "Not Retained"}
    )
    export["ActivationLabel"] = export["WeekActivation"].map(
        {1: "Activated Week", 0: "No Activation"}
    )
    return export


def main() -> None:
    games = pd.read_csv(PROCESSED_DIR / "fact_knicks_games.csv", parse_dates=["GAME_DATE"])
    weekly = pd.read_csv(PROCESSED_DIR / "fact_weekly_retention.csv")
    team = pd.read_csv(PROCESSED_DIR / "fact_team_clutch_knicks.csv")
    players = pd.read_csv(PROCESSED_DIR / "fact_player_clutch_knicks.csv")

    TABLEAU_DIR.mkdir(parents=True, exist_ok=True)

    build_season_summary(games, weekly, team).to_csv(
        TABLEAU_DIR / "knicks_season_summary.csv", index=False
    )
    build_game_export(games).to_csv(TABLEAU_DIR / "knicks_game_engagement.csv", index=False)
    build_player_export(players).to_csv(TABLEAU_DIR / "knicks_clutch_players.csv", index=False)
    build_weekly_export(weekly).to_csv(TABLEAU_DIR / "knicks_weekly_retention.csv", index=False)

    print(f"Tableau-ready files written to {TABLEAU_DIR}")


if __name__ == "__main__":
    main()
