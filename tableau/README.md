# Tableau Public Build Guide

Run the export script:

```bash
./.venv/bin/python src/05_prepare_tableau.py
```

This creates four Tableau-ready CSVs in `tableau/`:

- `knicks_season_summary.csv`
- `knicks_game_engagement.csv`
- `knicks_clutch_players.csv`
- `knicks_weekly_retention.csv`

Use `SEASON` as the main relationship key between tables.

## Recommended Tableau Public workbook structure

### Sheet 1: Season KPI Header
- Data source: `knicks_season_summary.csv`
- Filter: `SEASON`
- Marks: Text
- Show:
  - `Record`
  - `ActivationRate`
  - `AvgEngagementScore`
  - `RetentionRate`
  - `ClutchWinPct`

### Sheet 2: Engagement Pulse
- Data source: `knicks_game_engagement.csv`
- Columns: `GameNumber`
- Rows: `ENGAGEMENT_SCORE`
- Filter: `SEASON`
- Marks: Line
- Add `ACTIVATION_EVENT` to Color or Shape to highlight activation games
- Tooltip:
  - `GAME_DATE`
  - `MATCHUP`
  - `WL`
  - `PTS`
  - `PTS_DIFF`
  - `ENGAGEMENT_SCORE`

### Sheet 3: Fan Funnel
- Data source: `knicks_season_summary.csv`
- Filter: `SEASON`
- Use Measure Names / Measure Values with:
  - `AwarenessGames`
  - `ActivationGames`
  - `EngagementGames`
  - `RetainedWeeks`
- Recommended chart: horizontal bars sorted descending

### Sheet 4: League Context
- Data source: `knicks_season_summary.csv`
- Filter: `SEASON`
- Use these rank fields:
  - `ClutchWinPctRank`
  - `ClutchPointsRank`
  - `ClutchPlusMinusRank`
  - `ClutchFgPctRank`
- Recommended chart: bar chart with reversed axis so lower ranks look better

### Sheet 5: Top Clutch Moments
- Data source: `knicks_game_engagement.csv`
- Filter: `SEASON`
- Sort descending by `ENGAGEMENT_SCORE`, then descending by `PTS_DIFF`
- Show:
  - `GAME_DATE`
  - `MATCHUP`
  - `WL`
  - `PTS`
  - `PTS_DIFF`
  - `ENGAGEMENT_SCORE`

### Sheet 6: Clutch Players
- Data source: `knicks_clutch_players.csv`
- Filter: `SEASON`
- Sort descending by `PTS`
- Show:
  - `PLAYER_NAME`
  - `PTS`
  - `PLUS_MINUS`
  - `FG_PCT`
  - `GP`

## Useful Tableau calculated fields

### Win/Loss Color
```text
IF [WL] = "W" THEN "Win" ELSE "Loss" END
```

### Activation Flag
```text
IF [ACTIVATION_EVENT] = 1 THEN "Activated" ELSE "Non-Activated" END
```

### Engagement Score Band
```text
IF [ENGAGEMENT_SCORE] >= 5 THEN "Elite Moment"
ELSEIF [ENGAGEMENT_SCORE] >= 4 THEN "High Moment"
ELSEIF [ENGAGEMENT_SCORE] >= 2 THEN "Moderate Moment"
ELSE "Low Moment"
END
```

## Dashboard layout

Build a single dashboard with:

- Top row: Season filter plus KPI header
- Middle row: Engagement Pulse on the left, Fan Funnel on the right
- Bottom row: League Context, Top Clutch Moments, Clutch Players

Use Knicks colors:

- Blue: `#1D428A`
- Orange: `#F58426`
- Neutral background: `#F7F3EA`
