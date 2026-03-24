from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "dashboard"
OUTPUT_FILE = OUTPUT_DIR / "index.html"
ASSETS_DIR = OUTPUT_DIR / "assets"


def find_logo_path() -> str | None:
    candidates = [
        ASSETS_DIR / "knicks-logo.svg",
        ASSETS_DIR / "knicks-logo.png",
        ASSETS_DIR / "knicks-logo.webp",
        ASSETS_DIR / "knicks-logo.jpg",
        ASSETS_DIR / "knicks-logo.jpeg",
    ]
    for path in candidates:
        if path.exists():
            return f"assets/{path.name}"
    return None


def season_summary(
    games: pd.DataFrame, weekly: pd.DataFrame, team: pd.DataFrame, players: pd.DataFrame
) -> list[dict]:
    summaries: list[dict] = []

    for season in sorted(games["SEASON"].unique()):
        season_games = games[games["SEASON"] == season].sort_values("GAME_DATE").copy()
        season_weekly = weekly[weekly["SEASON"] == season].copy()
        season_team = team[team["SEASON"] == season].iloc[0]
        season_players = (
            players[players["SEASON"] == season]
            .sort_values(["PTS", "PLUS_MINUS"], ascending=[False, False])
            .head(6)
            .copy()
        )

        top_games = (
            season_games.sort_values(
                ["ENGAGEMENT_SCORE", "ACTIVATION_EVENT", "PTS_DIFF"],
                ascending=[False, False, False],
            )
            .head(5)
            .copy()
        )

        top_games["GAME_DATE"] = top_games["GAME_DATE"].dt.strftime("%b %d, %Y")
        season_games["GAME_DATE"] = season_games["GAME_DATE"].dt.strftime("%Y-%m-%d")

        peak_game = top_games.iloc[0]
        signal = "Momentum Up" if float(season_team["W_PCT"]) >= 0.55 else "Moments Matter"

        summaries.append(
            {
                "season": season,
                "record": f"{int(season_team['W'])}-{int(season_team['L'])}",
                "clutchWinPct": round(float(season_team["W_PCT"]) * 100, 1),
                "clutchPlusMinus": round(float(season_team["PLUS_MINUS"]), 1),
                "clutchPoints": int(season_team["PTS"]),
                "gamesPlayed": int(len(season_games)),
                "closeGameRate": round(float(season_games["IS_CLOSE"].mean()) * 100, 1),
                "activationRate": round(
                    float(season_games["ACTIVATION_EVENT"].mean()) * 100, 1
                ),
                "engagementRate": round(
                    float(season_games["ENGAGEMENT_EVENT"].mean()) * 100, 1
                ),
                "retentionRate": round(
                    float(season_weekly["RETENTION_EVENT"].mean()) * 100, 1
                ),
                "avgEngagementScore": round(
                    float(season_games["ENGAGEMENT_SCORE"].mean()), 2
                ),
                "awarenessGames": int(season_games["AWARENESS_EVENT"].sum()),
                "activationGames": int(season_games["ACTIVATION_EVENT"].sum()),
                "engagedGames": int(season_games["ENGAGEMENT_EVENT"].sum()),
                "retainedWeeks": int(season_weekly["RETENTION_EVENT"].sum()),
                "peakMoment": {
                    "date": peak_game["GAME_DATE"],
                    "matchup": peak_game["MATCHUP"],
                    "result": peak_game["WL"],
                    "score": int(peak_game["ENGAGEMENT_SCORE"]),
                    "diff": round(float(peak_game["PTS_DIFF"]), 1),
                    "points": int(peak_game["PTS"]),
                },
                "signal": signal,
                "games": season_games[
                    [
                        "GAME_DATE",
                        "MATCHUP",
                        "WL",
                        "PTS",
                        "PTS_DIFF",
                        "ENGAGEMENT_SCORE",
                        "ACTIVATION_EVENT",
                        "ENGAGEMENT_EVENT",
                    ]
                ].to_dict(orient="records"),
                "topGames": top_games[
                    [
                        "GAME_DATE",
                        "MATCHUP",
                        "WL",
                        "PTS",
                        "PTS_DIFF",
                        "ENGAGEMENT_SCORE",
                        "ACTIVATION_EVENT",
                    ]
                ].to_dict(orient="records"),
                "topPlayers": season_players[
                    ["PLAYER_NAME", "PTS", "PLUS_MINUS", "FG_PCT", "GP"]
                ].to_dict(orient="records"),
            }
        )

    return summaries


def league_context(team: pd.DataFrame) -> list[dict]:
    return (
        team.sort_values("SEASON")[
            ["SEASON", "W_PCT_RANK", "PTS_RANK", "PLUS_MINUS_RANK", "FG_PCT_RANK"]
        ]
        .assign(
            W_PCT_RANK=lambda df: df["W_PCT_RANK"].astype(int),
            PTS_RANK=lambda df: df["PTS_RANK"].astype(int),
            PLUS_MINUS_RANK=lambda df: df["PLUS_MINUS_RANK"].astype(int),
            FG_PCT_RANK=lambda df: df["FG_PCT_RANK"].astype(int),
        )
        .rename(columns={"SEASON": "season"})
        .to_dict(orient="records")
    )


def dashboard_html(payload: dict) -> str:
    data_blob = json.dumps(payload, separators=(",", ":"))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Knicks Clutch Analytics Dashboard</title>
  <style>
    :root {{
      --knicks-blue: #1d428a;
      --knicks-orange: #f58426;
      --knicks-cream: #f7f1e3;
      --navy-deep: #09152d;
      --navy-mid: #13264f;
      --ink: #0d1a36;
      --muted: #6f7b97;
      --line: rgba(15, 25, 54, 0.12);
      --card: rgba(255, 250, 242, 0.82);
      --card-strong: rgba(255, 255, 255, 0.92);
      --success: #22a06b;
      --danger: #d9624b;
      --shadow: 0 18px 40px rgba(8, 18, 41, 0.16);
      --radius: 28px;
    }}

    * {{
      box-sizing: border-box;
    }}

    html {{
      scroll-behavior: smooth;
    }}

    body {{
      margin: 0;
      color: var(--ink);
      font-family: "Avenir Next", "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at 12% 12%, rgba(245, 132, 38, 0.18), transparent 20%),
        radial-gradient(circle at 88% 10%, rgba(29, 66, 138, 0.22), transparent 22%),
        linear-gradient(180deg, #fbf6ec 0%, #f4ecdc 44%, #f6efe2 100%);
      min-height: 100vh;
    }}

    body::before {{
      content: "";
      position: fixed;
      inset: 0;
      background-image:
        linear-gradient(rgba(255,255,255,0.08) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.08) 1px, transparent 1px);
      background-size: 26px 26px;
      opacity: 0.15;
      pointer-events: none;
      z-index: -2;
    }}

    .page {{
      width: min(1320px, calc(100vw - 32px));
      margin: 0 auto;
      padding: 20px 0 42px;
    }}

    .hero {{
      position: relative;
      overflow: hidden;
      padding: 36px;
      border-radius: 36px;
      background:
        linear-gradient(120deg, rgba(8, 18, 41, 0.98), rgba(19, 38, 79, 0.96) 46%, rgba(29, 66, 138, 0.92)),
        radial-gradient(circle at 82% 30%, rgba(245,132,38,0.3), transparent 22%);
      color: white;
      box-shadow: var(--shadow);
      min-height: 400px;
    }}

    .scoreboard-strip {{
      position: relative;
      z-index: 2;
      display: grid;
      grid-template-columns: 1.2fr 0.9fr 1.2fr;
      gap: 12px;
      margin-bottom: 18px;
    }}

    .scoreboard-cell {{
      padding: 12px 16px;
      border-radius: 18px;
      background: rgba(255,255,255,0.08);
      border: 1px solid rgba(255,255,255,0.12);
      backdrop-filter: blur(10px);
      min-height: 78px;
      display: flex;
      flex-direction: column;
      justify-content: center;
    }}

    .scoreboard-label {{
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.16em;
      color: rgba(255,255,255,0.62);
      margin-bottom: 6px;
    }}

    .scoreboard-main {{
      font-size: 32px;
      line-height: 1;
      font-weight: 800;
      letter-spacing: -0.04em;
    }}

    .scoreboard-sub {{
      font-size: 13px;
      color: rgba(255,255,255,0.78);
      line-height: 1.4;
    }}

    .hero-art {{
      position: absolute;
      inset: auto 0 0 0;
      height: 220px;
      pointer-events: none;
      opacity: 0.92;
      z-index: 0;
    }}

    .hero::before {{
      content: "";
      position: absolute;
      inset: auto -70px -120px auto;
      width: 340px;
      height: 340px;
      border-radius: 50%;
      background:
        radial-gradient(circle at 36% 36%, rgba(255,255,255,0.28), transparent 12%),
        radial-gradient(circle, rgba(245,132,38,0.92), rgba(245,132,38,0.08));
      filter: blur(2px);
      opacity: 0.96;
    }}

    .hero::after {{
      content: "";
      position: absolute;
      left: -10%;
      right: -10%;
      bottom: -2px;
      height: 130px;
      background:
        linear-gradient(180deg, rgba(245,132,38,0.1), rgba(245,132,38,0.18)),
        repeating-linear-gradient(
          90deg,
          rgba(255,255,255,0.06) 0 120px,
          rgba(255,255,255,0.02) 120px 240px
        );
      clip-path: polygon(0 100%, 0 36%, 8% 44%, 14% 22%, 21% 44%, 29% 26%, 37% 52%, 45% 18%, 55% 48%, 63% 24%, 71% 56%, 78% 30%, 86% 44%, 92% 18%, 100% 40%, 100% 100%);
      opacity: 0.75;
    }}

    .hero-grid {{
      position: relative;
      z-index: 2;
      display: grid;
      grid-template-columns: 1.5fr 0.95fr;
      gap: 24px;
      align-items: stretch;
    }}

    .eyebrow {{
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.2em;
      color: rgba(255,255,255,0.66);
      margin-bottom: 14px;
    }}

    h1 {{
      margin: 0;
      max-width: 760px;
      font-family: Georgia, "Times New Roman", serif;
      font-size: clamp(40px, 6.6vw, 76px);
      line-height: 0.95;
      letter-spacing: -0.03em;
    }}

    .hero-copy {{
      max-width: 700px;
      margin-top: 16px;
      font-size: 17px;
      line-height: 1.62;
      color: rgba(255,255,255,0.82);
    }}

    .info-tip {{
      position: relative;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 18px;
      height: 18px;
      margin-left: 8px;
      border-radius: 50%;
      background: rgba(255,255,255,0.14);
      border: 1px solid rgba(255,255,255,0.2);
      color: rgba(255,255,255,0.88);
      font-size: 11px;
      font-weight: 700;
      cursor: help;
      vertical-align: middle;
    }}

    .info-tip.dark {{
      background: rgba(29,66,138,0.08);
      border-color: rgba(29,66,138,0.14);
      color: var(--knicks-blue);
    }}

    .info-tip::after {{
      content: attr(data-tip);
      position: absolute;
      left: 50%;
      bottom: calc(100% + 10px);
      transform: translateX(-50%) translateY(6px);
      min-width: 150px;
      max-width: 220px;
      padding: 8px 10px;
      border-radius: 10px;
      background: rgba(9,21,45,0.96);
      color: white;
      font-size: 12px;
      line-height: 1.35;
      text-transform: none;
      letter-spacing: normal;
      box-shadow: 0 14px 28px rgba(0,0,0,0.2);
      opacity: 0;
      pointer-events: none;
      transition: opacity 180ms ease, transform 180ms ease;
      z-index: 10;
      text-align: left;
    }}

    .info-tip::before {{
      content: "";
      position: absolute;
      left: 50%;
      bottom: calc(100% + 4px);
      transform: translateX(-50%) translateY(6px);
      border-left: 6px solid transparent;
      border-right: 6px solid transparent;
      border-top: 6px solid rgba(9,21,45,0.96);
      opacity: 0;
      transition: opacity 180ms ease, transform 180ms ease;
      z-index: 10;
    }}

    .info-tip:hover::after,
    .info-tip:hover::before,
    .info-tip:focus-visible::after,
    .info-tip:focus-visible::before {{
      opacity: 1;
      transform: translateX(-50%) translateY(0);
    }}

    .hero-strip {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
      margin-top: 24px;
      max-width: 760px;
    }}

    .strip-card {{
      padding: 16px 18px;
      border-radius: 20px;
      background: rgba(255,255,255,0.08);
      border: 1px solid rgba(255,255,255,0.14);
      backdrop-filter: blur(10px);
    }}

    .strip-card span {{
      display: block;
      color: rgba(255,255,255,0.66);
      text-transform: uppercase;
      letter-spacing: 0.12em;
      font-size: 11px;
      margin-bottom: 6px;
    }}

    .strip-card strong {{
      display: block;
      font-size: 28px;
      line-height: 1;
    }}

    .hero-side {{
      display: grid;
      gap: 16px;
      align-content: start;
    }}

    .brand-row {{
      display: flex;
      align-items: center;
      gap: 14px;
      margin-bottom: 14px;
    }}

    .logo-badge {{
      width: 112px;
      height: 112px;
      border-radius: 28px;
      display: grid;
      place-items: center;
      overflow: hidden;
      background:
        radial-gradient(circle at 30% 30%, rgba(255,255,255,0.28), transparent 24%),
        linear-gradient(180deg, rgba(245,132,38,0.22), rgba(29,66,138,0.18)),
        rgba(255,255,255,0.1);
      border: 1px solid rgba(255,255,255,0.24);
      backdrop-filter: blur(12px);
      box-shadow:
        0 24px 45px rgba(0,0,0,0.18),
        inset 0 0 0 1px rgba(255,255,255,0.08);
    }}

    .logo-badge img {{
      width: 82%;
      height: 82%;
      object-fit: contain;
      filter: drop-shadow(0 8px 18px rgba(0,0,0,0.22));
    }}

    .logo-fallback {{
      text-align: center;
      font-weight: 800;
      line-height: 0.95;
      letter-spacing: 0.08em;
      font-size: 26px;
      color: white;
    }}

    .logo-fallback small {{
      display: block;
      font-size: 11px;
      letter-spacing: 0.28em;
      margin-top: 6px;
      color: rgba(255,255,255,0.74);
    }}

    .skyline-note {{
      font-size: 12px;
      color: rgba(255,255,255,0.68);
      line-height: 1.45;
    }}

    .floating-card {{
      background: rgba(255,255,255,0.1);
      border: 1px solid rgba(255,255,255,0.14);
      border-radius: 24px;
      padding: 20px;
      backdrop-filter: blur(12px);
    }}

    .spotlight {{
      position: absolute;
      width: 440px;
      height: 440px;
      top: -180px;
      right: 18%;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(255,255,255,0.16), rgba(255,255,255,0.02) 42%, transparent 62%);
      filter: blur(3px);
      opacity: 0.92;
      z-index: 1;
      pointer-events: none;
      animation: sway 8s ease-in-out infinite alternate;
    }}

    .spotlight.left {{
      right: auto;
      left: -80px;
      top: -140px;
      animation-duration: 10s;
    }}

    @keyframes sway {{
      from {{ transform: translate3d(0, 0, 0) rotate(-7deg); }}
      to {{ transform: translate3d(18px, 10px, 0) rotate(6deg); }}
    }}

    .floating-card h2 {{
      margin: 0 0 10px;
      font-size: 18px;
    }}

    .peak-title {{
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.16em;
      color: rgba(255,255,255,0.62);
      margin-bottom: 10px;
    }}

    .peak-game {{
      font-size: 28px;
      font-weight: 700;
      line-height: 1.1;
      margin-bottom: 8px;
    }}

    .peak-meta {{
      color: rgba(255,255,255,0.78);
      font-size: 14px;
      line-height: 1.5;
    }}

    .season-switcher {{
      display: grid;
      gap: 10px;
    }}

    .season-switcher label {{
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.18em;
      color: rgba(255,255,255,0.7);
    }}

    select {{
      width: 100%;
      border: none;
      border-radius: 16px;
      padding: 14px 16px;
      font-size: 16px;
      color: var(--ink);
      background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(247,241,227,0.94));
      box-shadow: inset 0 0 0 1px rgba(29,66,138,0.12);
    }}

    .signal-pill {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      border-radius: 999px;
      padding: 8px 12px;
      font-size: 12px;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      background: rgba(245,132,38,0.16);
      color: #ffd9b8;
      margin-top: 14px;
    }}

    .main-grid {{
      display: grid;
      grid-template-columns: repeat(12, minmax(0, 1fr));
      gap: 18px;
      margin-top: 20px;
    }}

    .panel {{
      position: relative;
      overflow: hidden;
      background: var(--card);
      border: 1px solid rgba(255,255,255,0.52);
      border-radius: 28px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(12px);
    }}

    .panel::before {{
      content: "";
      position: absolute;
      inset: 0;
      background: linear-gradient(180deg, rgba(255,255,255,0.1), transparent 30%);
      pointer-events: none;
    }}

    .panel-content {{
      position: relative;
      z-index: 1;
      padding: 22px;
    }}

    .panel h3 {{
      margin: 0;
      font-size: 23px;
    }}

    .panel-copy {{
      margin: 8px 0 0;
      color: var(--muted);
      line-height: 1.55;
      font-size: 14px;
    }}

    .kpi {{
      grid-column: span 3;
      min-height: 190px;
    }}

    .kpi .metric-label {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.16em;
      display: inline-flex;
      align-items: center;
    }}

    .metric-value {{
      font-size: 42px;
      line-height: 0.95;
      margin: 16px 0 10px;
      font-weight: 800;
      letter-spacing: -0.04em;
    }}

    .metric-accent {{
      position: absolute;
      right: -28px;
      bottom: -32px;
      width: 140px;
      height: 140px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(245,132,38,0.22), rgba(245,132,38,0.02));
    }}

    .kpi .panel-content {{
      min-height: 100%;
    }}

    .wide {{
      grid-column: span 8;
    }}

    .side {{
      grid-column: span 4;
    }}

    .full {{
      grid-column: span 12;
    }}

    .chart-wrap {{
      margin-top: 18px;
      border-radius: 24px;
      overflow: hidden;
      background:
        linear-gradient(180deg, rgba(29,66,138,0.08), rgba(255,255,255,0.68)),
        linear-gradient(90deg, rgba(255,255,255,0.14), rgba(255,255,255,0.04));
      border: 1px solid var(--line);
    }}

    #pulseChart {{
      display: block;
      width: 100%;
      height: 350px;
    }}

    .chart-caption {{
      display: flex;
      gap: 16px;
      align-items: center;
      flex-wrap: wrap;
      padding: 0 18px 18px;
      color: var(--muted);
      font-size: 13px;
    }}

    .dot {{
      width: 12px;
      height: 12px;
      border-radius: 50%;
      display: inline-block;
    }}

    .cta-band {{
      margin-top: 18px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 16px 18px;
      border-radius: 22px;
      background: linear-gradient(90deg, rgba(29,66,138,0.12), rgba(245,132,38,0.16));
      border: 1px solid rgba(29,66,138,0.08);
      color: var(--ink);
    }}

    .cta-band strong {{
      display: block;
      font-size: 14px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      color: var(--knicks-blue);
      margin-bottom: 4px;
    }}

    .cta-score {{
      font-size: 34px;
      line-height: 1;
      font-weight: 800;
      color: var(--knicks-orange);
      letter-spacing: -0.04em;
      white-space: nowrap;
    }}

    .court {{
      margin-top: 18px;
      padding: 18px;
      border-radius: 24px;
      background:
        linear-gradient(180deg, rgba(250, 214, 180, 0.55), rgba(245, 208, 170, 0.76)),
        linear-gradient(90deg, rgba(255,255,255,0.06), rgba(255,255,255,0.0));
      border: 1px solid rgba(164, 98, 43, 0.18);
    }}

    .court-grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
    }}

    .court-step {{
      position: relative;
      min-height: 98px;
      padding: 14px;
      border-radius: 18px;
      background: rgba(255,255,255,0.58);
      border: 1px solid rgba(125, 76, 36, 0.12);
    }}

    .court-step::after {{
      content: "";
      position: absolute;
      inset: auto 12px 12px 12px;
      height: 6px;
      border-radius: 999px;
      background: linear-gradient(90deg, rgba(29,66,138,0.18), rgba(245,132,38,0.45));
    }}

    .court-step span {{
      display: block;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.14em;
      color: #835026;
    }}

    .court-step strong {{
      display: block;
      margin-top: 8px;
      font-size: 30px;
      line-height: 1;
      color: #7a3900;
    }}

    .bars {{
      display: grid;
      gap: 16px;
      margin-top: 18px;
    }}

    .bar-row {{
      display: grid;
      grid-template-columns: 88px 1fr 48px;
      gap: 12px;
      align-items: center;
      font-size: 14px;
    }}

    .bar-track {{
      height: 14px;
      border-radius: 999px;
      overflow: hidden;
      background: rgba(29,66,138,0.1);
    }}

    .bar-fill {{
      height: 100%;
      border-radius: inherit;
      background: linear-gradient(90deg, var(--knicks-blue), var(--knicks-orange));
    }}

    .story-list {{
      display: grid;
      gap: 14px;
      margin-top: 18px;
    }}

    .story-card {{
      padding: 18px;
      border-radius: 20px;
      background: linear-gradient(135deg, rgba(255,255,255,0.9), rgba(255,244,231,0.9));
      border: 1px solid rgba(29,66,138,0.08);
    }}

    .story-card strong {{
      display: block;
      margin-bottom: 6px;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      color: var(--knicks-orange);
    }}

    .moments-grid {{
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 14px;
      margin-top: 18px;
    }}

    .moment-card {{
      padding: 18px;
      border-radius: 22px;
      background:
        linear-gradient(180deg, rgba(19,38,79,0.96), rgba(13,26,54,0.96)),
        radial-gradient(circle at top right, rgba(245,132,38,0.25), transparent 30%);
      color: white;
      min-height: 188px;
    }}

    .moment-card .date {{
      color: rgba(255,255,255,0.64);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
    }}

    .moment-card .matchup {{
      margin-top: 10px;
      font-size: 22px;
      line-height: 1.12;
      font-weight: 700;
    }}

    .moment-stats {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-top: 16px;
    }}

    .chip {{
      padding: 8px 10px;
      border-radius: 999px;
      background: rgba(255,255,255,0.1);
      border: 1px solid rgba(255,255,255,0.12);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}

    .tables {{
      display: grid;
      grid-template-columns: 1.2fr 0.8fr;
      gap: 18px;
      margin-top: 18px;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
    }}

    th, td {{
      text-align: left;
      padding: 12px 8px;
      border-bottom: 1px solid var(--line);
      font-size: 14px;
    }}

    th {{
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      color: var(--muted);
    }}

    tr:last-child td {{
      border-bottom: none;
    }}

    .result {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 7px 10px;
      border-radius: 999px;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-weight: 700;
    }}

    .result.win {{
      color: var(--success);
      background: rgba(34,160,107,0.12);
    }}

    .result.loss {{
      color: var(--danger);
      background: rgba(217,98,75,0.12);
    }}

    .footer {{
      padding: 18px 4px 6px;
      color: var(--muted);
      text-align: center;
      font-size: 13px;
    }}

    @media (max-width: 1100px) {{
      .hero-grid,
      .main-grid,
      .tables,
      .court-grid,
      .moments-grid {{
        grid-template-columns: 1fr;
      }}

      .kpi, .wide, .side, .full {{
        grid-column: span 1;
      }}

      .hero-strip {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <section class="hero">
      <div class="hero-grid">
        <div>
          <div class="scoreboard-strip">
            <div class="scoreboard-cell">
              <div class="scoreboard-label">Home</div>
              <div class="scoreboard-main">Knicks</div>
              <div class="scoreboard-sub">Madison Square Garden energy model</div>
            </div>
            <div class="scoreboard-cell">
              <div class="scoreboard-label">Clutch Board</div>
              <div class="scoreboard-main" id="scoreboardPulse">00</div>
              <div class="scoreboard-sub">Peak engagement pulse</div>
            </div>
            <div class="scoreboard-cell">
              <div class="scoreboard-label">Away</div>
              <div class="scoreboard-main">Fan Funnel</div>
              <div class="scoreboard-sub">Awareness to retention conversion</div>
            </div>
          </div>

          <div class="brand-row">
            <div class="logo-badge" id="logoBadge">
              <div class="logo-fallback">NYK<small>NEW YORK</small></div>
            </div>
            <div>
              <div class="eyebrow">Knicks Analytics Dashboard</div>
              <div class="skyline-note">NYC skyline and Statue of Liberty are original inline illustrations. The Knicks logo appears automatically if an asset is added.</div>
            </div>
          </div>
          <h1>Clutch moments become fan momentum when the Garden drama keeps stacking.</h1>
          <p class="hero-copy">
            This dashboard shows how Knicks clutch performance across a season connects to fan engagement,
            highlighting the games, players, and weekly patterns that can turn big moments into repeat attention.
          </p>
          <div class="hero-strip">
            <div class="strip-card">
              <span>Clutch Record</span>
              <strong id="heroRecord">0-0</strong>
            </div>
            <div class="strip-card">
              <span>Peak Moment</span>
              <strong id="heroPeakScore">0</strong>
            </div>
            <div class="strip-card">
              <span>Signal</span>
              <strong id="heroSignal">Momentum</strong>
            </div>
          </div>
        </div>

        <div class="hero-side">
          <div class="floating-card">
            <div class="season-switcher">
              <label for="seasonSelect">Season View</label>
              <select id="seasonSelect"></select>
            </div>
            <div class="signal-pill" id="signalPill">Loading season signal</div>
          </div>

          <div class="floating-card">
            <div class="peak-title">Signature Clutch Night</div>
            <div class="peak-game" id="peakMatchup">NYK vs BOS</div>
            <div class="peak-meta" id="peakMeta">Loading top game...</div>
          </div>
        </div>
      </div>
      <div class="spotlight"></div>
      <div class="spotlight left"></div>
      <svg class="hero-art" viewBox="0 0 1440 240" preserveAspectRatio="none" aria-hidden="true">
        <defs>
          <linearGradient id="skyGlow" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stop-color="rgba(255,255,255,0.22)"/>
            <stop offset="100%" stop-color="rgba(255,255,255,0.02)"/>
          </linearGradient>
          <linearGradient id="libertyFill" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stop-color="rgba(245,132,38,0.70)"/>
            <stop offset="100%" stop-color="rgba(245,132,38,0.18)"/>
          </linearGradient>
        </defs>
        <rect x="0" y="170" width="1440" height="70" fill="rgba(9,21,45,0.92)"/>
        <path d="M0 185 L0 155 L30 155 L30 130 L56 130 L56 166 L74 166 L74 120 L104 120 L104 178 L130 178 L130 140 L154 140 L154 180 L180 180 L180 112 L210 112 L210 180 L236 180 L236 150 L256 150 L256 182 L286 182 L286 90 L318 90 L318 182 L344 182 L344 142 L368 142 L368 182 L404 182 L404 122 L432 122 L432 182 L470 182 L470 102 L505 102 L505 182 L530 182 L530 156 L554 156 L554 182 L590 182 L590 136 L612 136 L612 182 L650 182 L650 116 L676 116 L676 182 L720 182 L720 150 L750 150 L750 182 L786 182 L786 112 L820 112 L820 182 L856 182 L856 134 L884 134 L884 182 L920 182 L920 102 L954 102 L954 182 L986 182 L986 145 L1010 145 L1010 182 L1044 182 L1044 122 L1074 122 L1074 182 L1110 182 L1110 100 L1140 100 L1140 182 L1170 182 L1170 138 L1194 138 L1194 182 L1228 182 L1228 116 L1260 116 L1260 182 L1294 182 L1294 144 L1320 144 L1320 182 L1360 182 L1360 128 L1394 128 L1394 182 L1440 182 L1440 240 L0 240 Z" fill="url(#skyGlow)"/>
        <path d="M112 180 L130 180 L130 158 L136 154 L138 144 L143 140 L146 126 L150 122 L154 126 L156 138 L163 144 L165 155 L172 160 L172 180 L191 180 L191 188 L112 188 Z" fill="url(#libertyFill)"/>
        <path d="M150 120 L146 112 L149 105 L143 99 L151 101 L156 92 L158 102 L166 100 L161 106 L164 114 Z" fill="#ffd480"/>
        <rect x="0" y="188" width="1440" height="52" fill="rgba(6,13,30,0.96)"/>
      </svg>
    </section>

    <section class="main-grid">
      <article class="panel kpi">
        <div class="panel-content">
          <div class="metric-label">Activation Rate <span class="info-tip dark" tabindex="0" data-tip="Percent of games that sparked a strong fan-response moment.">i</span></div>
          <div class="metric-value" id="activationRate">0%</div>
          <p class="panel-copy">Games that created enough late-game intensity to trigger a meaningful fan-response event.</p>
          <div class="metric-accent"></div>
        </div>
      </article>

      <article class="panel kpi">
        <div class="panel-content">
          <div class="metric-label">Engagement Score <span class="info-tip dark" tabindex="0" data-tip="Blended score from close games, rivalries, wins, and star moments.">i</span></div>
          <div class="metric-value" id="avgScore">0.00</div>
          <p class="panel-copy">A blended signal of close finishes, rivalries, wins, and star scoring bursts.</p>
          <div class="metric-accent"></div>
        </div>
      </article>

      <article class="panel kpi">
        <div class="panel-content">
          <div class="metric-label">Weekly Retention <span class="info-tip dark" tabindex="0" data-tip="Weeks where fan momentum carried into the following week.">i</span></div>
          <div class="metric-value" id="retentionRate">0%</div>
          <p class="panel-copy">How often one activated week was followed by another, a proxy for repeat fan energy.</p>
          <div class="metric-accent"></div>
        </div>
      </article>

      <article class="panel kpi">
        <div class="panel-content">
          <div class="metric-label">Clutch Win Rate <span class="info-tip dark" tabindex="0" data-tip="Win percentage in official NBA clutch situations.">i</span></div>
          <div class="metric-value" id="clutchWinRate">0%</div>
          <p class="panel-copy">League clutch performance that helps turn thrilling moments into trust and loyalty.</p>
          <div class="metric-accent"></div>
        </div>
      </article>

      <article class="panel wide">
        <div class="panel-content">
          <h3>Engagement Pulse</h3>
          <p class="panel-copy">The orange line tracks game-level engagement, while blue and orange markers call out activated and engaged nights across the season.</p>
          <div class="chart-wrap">
            <svg id="pulseChart" viewBox="0 0 860 350" preserveAspectRatio="none"></svg>
            <div class="chart-caption">
              <span><i class="dot" style="background: var(--knicks-blue)"></i> Standard game</span>
              <span><i class="dot" style="background: var(--knicks-orange)"></i> Activation event</span>
              <span><i class="dot" style="background: #ffd480"></i> Engaged streak</span>
            </div>
          </div>
        </div>
      </article>

      <article class="panel side">
        <div class="panel-content">
          <h3>Fan Funnel On Court</h3>
          <p class="panel-copy">A hardwood-style view of how broad attention narrows into stronger and more repeat behavior.</p>
          <div class="court">
            <div class="court-grid" id="courtGrid"></div>
          </div>
        </div>
      </article>

      <article class="panel side">
        <div class="panel-content">
          <h3>League Rank Snapshot</h3>
          <p class="panel-copy">Lower ranks are better. This shows where the Knicks landed against the rest of the NBA in clutch play.</p>
          <div class="bars" id="leagueBars"></div>
        </div>
      </article>

      <article class="panel wide">
        <div class="panel-content">
          <h3>What The Season Is Saying</h3>
          <p class="panel-copy">Three strategic takeaways generated directly from the selected season profile.</p>
          <div class="story-list" id="storyList"></div>
          <div class="cta-band">
            <div>
              <strong>Campaign Hook</strong>
              <div id="ctaText">Signature moments are where the fan-growth story gets its strongest emotional lift.</div>
            </div>
            <div class="cta-score" id="ctaScore">0%</div>
          </div>
        </div>
      </article>

      <article class="panel full">
        <div class="panel-content">
          <h3>Top Clutch Moments</h3>
          <p class="panel-copy">The five highest-engagement Knicks games from the selected season, styled like feature cards for an executive presentation.</p>
          <div class="moments-grid" id="momentsGrid"></div>
        </div>
      </article>

      <article class="panel full">
        <div class="panel-content">
          <h3>Player And Game Detail</h3>
          <p class="panel-copy">Top performers in clutch minutes alongside the specific games that generated the strongest fan-response signal.</p>
          <div class="tables">
            <div>
              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Matchup</th>
                    <th>Result</th>
                    <th>PTS</th>
                    <th>Diff</th>
                    <th>Score</th>
                  </tr>
                </thead>
                <tbody id="gamesTable"></tbody>
              </table>
            </div>
            <div>
              <table>
                <thead>
                  <tr>
                    <th>Player</th>
                    <th>PTS</th>
                    <th>+/-</th>
                    <th>FG%</th>
                    <th>GP</th>
                  </tr>
                </thead>
                <tbody id="playersTable"></tbody>
              </table>
            </div>
          </div>
        </div>
      </article>
    </section>

    <div class="footer">
      Standalone HTML dashboard built from <code>data/processed</code>. Visual treatment uses Knicks-inspired colors and basketball-inspired graphics while preserving your source metrics.
    </div>
  </main>

  <script>
    const DATA = {data_blob};
    const seasonSelect = document.getElementById("seasonSelect");

    function pct(value) {{
      return `${{Number(value).toFixed(1)}}%`;
    }}

    function signed(value) {{
      const n = Number(value);
      return `${{n > 0 ? "+" : ""}}${{n.toFixed(1)}}`;
    }}

    function storylines(summary) {{
      const lines = [];

      if (summary.activationRate >= 20) {{
        lines.push({{
          title: "High-Energy Season",
          body: `${{summary.season}} produced activation in ${{summary.activationRate.toFixed(1)}}% of games, which means the Knicks generated enough late-game heat to support recurring social, email, and ticket retargeting moments.`
        }});
      }} else {{
        lines.push({{
          title: "Selective Spike Strategy",
          body: `${{summary.season}} activated fans in ${{summary.activationRate.toFixed(1)}}% of games, so the smartest growth play is to over-invest in the sharpest clutch nights instead of spreading energy evenly.`
        }});
      }}

      if (summary.retentionRate >= 25) {{
        lines.push({{
          title: "Momentum Carried Week To Week",
          body: `Weekly retention reached ${{summary.retentionRate.toFixed(1)}}%, which suggests the season had enough back-to-back drama to keep fans emotionally connected beyond a single final buzzer.`
        }});
      }} else {{
        lines.push({{
          title: "Need Better Postgame Follow-Through",
          body: `Retention landed at ${{summary.retentionRate.toFixed(1)}}%, so the opportunity is packaging each signature finish into content and offers that bridge into the next week.`
        }});
      }}

      if (summary.clutchWinPct >= 55) {{
        lines.push({{
          title: "Winning Reinforced The Story",
          body: `A ${{summary.clutchWinPct.toFixed(1)}}% clutch win rate gave the Knicks late-game credibility. That matters because fan drama compounds more effectively when the team closes.`
        }});
      }} else {{
        lines.push({{
          title: "Drama Without Enough Conversion",
          body: `Clutch win rate finished at ${{summary.clutchWinPct.toFixed(1)}}%. The excitement is there, but more wins in big moments would likely raise repeat engagement and brand confidence.`
        }});
      }}

      return lines;
    }}

    function createPulseChart(summary) {{
      const svg = document.getElementById("pulseChart");
      const width = 860;
      const height = 350;
      const padding = {{ top: 24, right: 18, bottom: 36, left: 42 }};
      const plotW = width - padding.left - padding.right;
      const plotH = height - padding.top - padding.bottom;
      const values = summary.games.map((game) => Number(game.ENGAGEMENT_SCORE));
      const maxY = Math.max(6, ...values);

      const x = (index) => padding.left + (plotW * index) / Math.max(summary.games.length - 1, 1);
      const y = (value) => padding.top + plotH - (plotH * value) / maxY;

      let grid = "";
      for (let i = 0; i <= maxY; i += 1) {{
        const gy = y(i);
        grid += `<line x1="${{padding.left}}" y1="${{gy}}" x2="${{width - padding.right}}" y2="${{gy}}" stroke="rgba(9,21,45,0.10)" stroke-width="1" />`;
        grid += `<text x="10" y="${{gy + 4}}" fill="rgba(111,123,151,0.9)" font-size="11">${{i}}</text>`;
      }}

      const points = summary.games.map((game, index) => `${{x(index)}},${{y(Number(game.ENGAGEMENT_SCORE))}}`);
      const linePath = `M ${{points.join(" L ")}}`;
      const areaPath = `${{linePath}} L ${{x(summary.games.length - 1)}},${{height - padding.bottom}} L ${{x(0)}},${{height - padding.bottom}} Z`;

      const dots = summary.games.map((game, index) => {{
        const engaged = Number(game.ENGAGEMENT_EVENT) === 1;
        const activated = Number(game.ACTIVATION_EVENT) === 1;
        const fill = engaged ? "#ffd480" : activated ? "#f58426" : "#1d428a";
        const radius = engaged ? 5.5 : activated ? 4.5 : 3.2;
        return `<circle cx="${{x(index)}}" cy="${{y(Number(game.ENGAGEMENT_SCORE))}}" r="${{radius}}" fill="${{fill}}" stroke="rgba(255,255,255,0.85)" stroke-width="1.2">
          <title>${{game.GAME_DATE}} | ${{game.MATCHUP}} | Engagement ${{game.ENGAGEMENT_SCORE}}</title>
        </circle>`;
      }}).join("");

      const labels = [0, Math.floor((summary.games.length - 1) / 2), summary.games.length - 1]
        .filter((value, index, arr) => arr.indexOf(value) === index)
        .map((index) => `<text x="${{x(index)}}" y="${{height - 10}}" text-anchor="middle" fill="rgba(111,123,151,0.9)" font-size="11">${{summary.games[index].GAME_DATE}}</text>`)
        .join("");

      svg.innerHTML = `
        <defs>
          <linearGradient id="pulseFill" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stop-color="rgba(245,132,38,0.32)" />
            <stop offset="100%" stop-color="rgba(245,132,38,0.02)" />
          </linearGradient>
        </defs>
        ${{grid}}
        <path d="${{areaPath}}" fill="url(#pulseFill)" />
        <path d="${{linePath}}" fill="none" stroke="#f58426" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" />
        ${{dots}}
        ${{labels}}
      `;
    }}

    function renderCourt(summary) {{
      const courtGrid = document.getElementById("courtGrid");
      const rows = [
        ["Awareness", summary.awarenessGames],
        ["Activation", summary.activationGames],
        ["Engaged", summary.engagedGames],
        ["Retained Weeks", summary.retainedWeeks]
      ];

      courtGrid.innerHTML = rows.map(([label, value]) => `
        <div class="court-step">
          <span>${{label}}</span>
          <strong>${{value}}</strong>
        </div>
      `).join("");
    }}

    function renderLeague(summary) {{
      const league = DATA.league.find((row) => row.season === summary.season);
      const bars = document.getElementById("leagueBars");
      const rows = [
        ["Win%", league.W_PCT_RANK],
        ["Points", league.PTS_RANK],
        ["+/-", league.PLUS_MINUS_RANK],
        ["FG%", league.FG_PCT_RANK]
      ];

      bars.innerHTML = rows.map(([label, rank]) => {{
        const width = ((30 - rank + 1) / 30) * 100;
        return `<div class="bar-row">
          <strong>${{label}}</strong>
          <div class="bar-track"><div class="bar-fill" style="width:${{width}}%"></div></div>
          <span>#${{rank}}</span>
        </div>`;
      }}).join("");
    }}

    function renderStories(summary) {{
      document.getElementById("storyList").innerHTML = storylines(summary).map((item) => `
        <div class="story-card">
          <strong>${{item.title}}</strong>
          <div>${{item.body}}</div>
        </div>
      `).join("");
    }}

    function renderMoments(summary) {{
      document.getElementById("momentsGrid").innerHTML = summary.topGames.map((game) => `
        <div class="moment-card">
          <div class="date">${{game.GAME_DATE}}</div>
          <div class="matchup">${{game.MATCHUP}}</div>
          <div class="moment-stats">
            <span class="chip">${{game.WL === "W" ? "Win" : "Loss"}}</span>
            <span class="chip">${{game.PTS}} pts</span>
            <span class="chip">${{signed(game.PTS_DIFF)}} diff</span>
            <span class="chip">Score ${{game.ENGAGEMENT_SCORE}}</span>
          </div>
        </div>
      `).join("");
    }}

    function renderTables(summary) {{
      document.getElementById("gamesTable").innerHTML = summary.topGames.map((game) => `
        <tr>
          <td>${{game.GAME_DATE}}</td>
          <td>${{game.MATCHUP}}</td>
          <td><span class="result ${{game.WL === "W" ? "win" : "loss"}}">${{game.WL}}</span></td>
          <td>${{game.PTS}}</td>
          <td>${{signed(game.PTS_DIFF)}}</td>
          <td>${{game.ENGAGEMENT_SCORE}}</td>
        </tr>
      `).join("");

      document.getElementById("playersTable").innerHTML = summary.topPlayers.map((player) => `
        <tr>
          <td>${{player.PLAYER_NAME}}</td>
          <td>${{player.PTS}}</td>
          <td>${{player.PLUS_MINUS > 0 ? "+" : ""}}${{player.PLUS_MINUS}}</td>
          <td>${{(Number(player.FG_PCT) * 100).toFixed(1)}}%</td>
          <td>${{player.GP}}</td>
        </tr>
      `).join("");
    }}

    function renderHeader(summary) {{
      document.getElementById("heroRecord").textContent = summary.record;
      document.getElementById("heroPeakScore").textContent = summary.peakMoment.score;
      document.getElementById("heroSignal").textContent = summary.signal;
      document.getElementById("scoreboardPulse").textContent = String(summary.peakMoment.score).padStart(2, "0");
      document.getElementById("signalPill").textContent = `${{summary.season}} | ${{summary.signal}}`;
      document.getElementById("peakMatchup").textContent = summary.peakMoment.matchup;
      document.getElementById("peakMeta").textContent =
        `${{summary.peakMoment.date}} | ${{summary.peakMoment.result === "W" ? "Win" : "Loss"}} | ${{summary.peakMoment.points}} pts | ${{signed(summary.peakMoment.diff)}} point margin swing | Engagement score ${{summary.peakMoment.score}}`;
    }}

    function renderMetrics(summary) {{
      document.getElementById("activationRate").textContent = pct(summary.activationRate);
      document.getElementById("avgScore").textContent = Number(summary.avgEngagementScore).toFixed(2);
      document.getElementById("retentionRate").textContent = pct(summary.retentionRate);
      document.getElementById("clutchWinRate").textContent = pct(summary.clutchWinPct);
      document.getElementById("ctaScore").textContent = pct(summary.activationRate);
      document.getElementById("ctaText").textContent =
        summary.activationRate >= 20
          ? "High-heat clutch nights were frequent enough to support a bigger Knicks growth campaign around repeat fan activation."
          : "The biggest growth upside lives in packaging the sharpest clutch nights as signature Knicks moments fans want to come back to.";
    }}

    function render(season) {{
      const summary = DATA.seasons.find((row) => row.season === season) || DATA.seasons[0];
      renderHeader(summary);
      renderMetrics(summary);
      createPulseChart(summary);
      renderCourt(summary);
      renderLeague(summary);
      renderStories(summary);
      renderMoments(summary);
      renderTables(summary);
    }}

    DATA.seasons.forEach((summary) => {{
      const option = document.createElement("option");
      option.value = summary.season;
      option.textContent = summary.season;
      seasonSelect.appendChild(option);
    }});

    seasonSelect.value = DATA.defaultSeason;
    if (DATA.logoPath) {{
      document.getElementById("logoBadge").innerHTML = `<img src="${{DATA.logoPath}}" alt="New York Knicks logo" />`;
    }}
    seasonSelect.addEventListener("change", (event) => render(event.target.value));
    render(DATA.defaultSeason);
  </script>
</body>
</html>
"""


def main() -> None:
    games = pd.read_csv(PROCESSED_DIR / "fact_knicks_games.csv", parse_dates=["GAME_DATE"])
    weekly = pd.read_csv(PROCESSED_DIR / "fact_weekly_retention.csv")
    team = pd.read_csv(PROCESSED_DIR / "fact_team_clutch_knicks.csv")
    players = pd.read_csv(PROCESSED_DIR / "fact_player_clutch_knicks.csv")

    payload = {
        "defaultSeason": sorted(games["SEASON"].unique())[-1],
        "seasons": season_summary(games, weekly, team, players),
        "league": league_context(team),
        "logoPath": find_logo_path(),
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(dashboard_html(payload), encoding="utf-8")
    print(f"Dashboard written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
