# knicks-growth-funnel-clutch

A portfolio-ready sports analytics project that uses real New York Knicks data to connect clutch performance to fan growth funnel metrics across four NBA seasons.

## GitHub-ready summary

This project combines Python data engineering, sports analytics, and frontend dashboard development in one end-to-end workflow. It pulls real Knicks data with `nba_api`, transforms it into beginner-friendly funnel metrics, and presents the results in a polished GitHub Pages dashboard built with HTML, CSS, JavaScript, Chart.js, and Papa Parse.

## Why this project stands out

- End-to-end workflow from API extraction to deployed dashboard
- Real NBA historical data across four seasons
- Clear analytics framing through awareness, activation, engagement, and retention
- Clutch player and team analysis layered into the fan-growth story
- GitHub Pages-friendly static site for easy portfolio sharing

## What this project shows

- A Python data pipeline built with `nba_api` and `pandas`
- Four seasons of real Knicks historical data from `2021-22` through `2024-25`
- A simple growth funnel model with:
  - Awareness
  - Activation
  - Engagement
  - Retention
- League and player clutch tracking
- Raw and processed CSV outputs
- A static dashboard built with:
  - HTML
  - CSS
  - JavaScript
  - [Chart.js](https://www.chartjs.org/)
  - [Papa Parse](https://www.papaparse.com/)
- A GitHub Pages-friendly `docs/` site with Knicks blue/orange styling and NYC-inspired visuals

## Project structure

```text
knicks-growth-funnel-clutch/
├── data/
│   ├── raw/
│   └── processed/
├── docs/
│   ├── data/
│   ├── app.js
│   ├── index.html
│   └── styles.css
├── src/
│   ├── 01_extract.py
│   ├── 02_transform.py
│   ├── 03_export.py
│   └── utils.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Funnel definitions

- `Awareness`: Every Knicks game creates baseline visibility.
- `Activation`: A game with a strong emotional hook, such as a close finish, rivalry factor, win, or big scoring moment.
- `Engagement`: Repeated activation within a rolling 7-day window.
- `Retention`: Activated momentum that continues into the next week.

These are not official marketing system events. They are analytics-friendly proxy metrics built from the game data you pulled.

## Setup

### 1. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

## Run the pipeline

### 1. Extract raw Knicks and clutch data

```bash
python src/01_extract.py
```

This saves:

- `data/raw/knicks_games_raw.csv`
- `data/raw/team_clutch_raw.csv`
- `data/raw/player_clutch_raw.csv`

### 2. Transform the game data into funnel metrics

```bash
python src/02_transform.py
```

This saves:

- `data/processed/fact_knicks_games.csv`
- `data/processed/fact_weekly_retention.csv`
- `data/processed/fact_season_summary.csv`

### 3. Export clutch files and dashboard-ready CSVs

```bash
python src/03_export.py
```

This saves:

- `data/processed/fact_team_clutch_league.csv`
- `data/processed/fact_player_clutch_league.csv`
- `data/processed/fact_team_clutch_knicks.csv`
- `data/processed/fact_player_clutch_knicks.csv`

It also copies the dashboard data into:

- `docs/data/`

## Run the dashboard locally

Because the dashboard loads CSV files with JavaScript, it should be served from a local web server instead of opened directly as a `file://` page.

From the project root, run:

```bash
python3 -m http.server 8000 -d docs
```

Then open:

- [http://localhost:8000](http://localhost:8000)

## Dashboard features

- Knicks-themed recruiter-ready design
- NYC skyline and Statue of Liberty visuals
- KPI cards with clear plain-language labels
- Activation trend chart
- Growth funnel chart
- Top activation games table
- Clutch leaderboard
- Filters for season, venue, and fan stage

## Deploy on GitHub Pages

### Option 1: Use the `docs/` folder from the main branch

1. Push the repository to GitHub.
2. Open the repository `Settings`.
3. Click `Pages`.
4. Under `Build and deployment`, choose:
   - `Source`: `Deploy from a branch`
   - `Branch`: `main`
   - `Folder`: `/docs`
5. Save.

GitHub Pages will publish the dashboard using the files in `docs/`.

## Resume-friendly project summary

You can describe this project like this:

> Built a Knicks-themed sports analytics project using Python, nba_api, pandas, and a static JavaScript dashboard to model how clutch NBA moments may drive fan awareness, activation, engagement, and retention across four seasons.

## Suggested GitHub repository settings

### Repository description

```text
Knicks-themed sports analytics project using Python, nba_api, pandas, and a static dashboard to connect clutch performance with fan growth funnel metrics.
```

### Suggested topics

```text
python, pandas, nba-api, sports-analytics, data-analysis, data-visualization, chartjs, javascript, html, css, github-pages, portfolio-project
```

## Notes

- The dashboard uses processed CSVs, so the frontend stays simple and easy to explain in interviews.
- The funnel is intentionally beginner-friendly: it is designed to tell a business story, not claim perfect fan behavior measurement.
