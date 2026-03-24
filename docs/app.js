const DATA_FILES = {
  games: "./data/fact_knicks_games.csv",
  weekly: "./data/fact_weekly_retention.csv",
  players: "./data/fact_player_clutch_knicks.csv",
  teams: "./data/fact_team_clutch_knicks.csv",
  seasons: "./data/fact_season_summary.csv",
};

const state = {
  games: [],
  weekly: [],
  players: [],
  teams: [],
  seasons: [],
  charts: {},
};

function parseCsv(url) {
  return new Promise((resolve, reject) => {
    Papa.parse(url, {
      download: true,
      header: true,
      dynamicTyping: true,
      skipEmptyLines: true,
      complete: (results) => {
        if (results.errors && results.errors.length > 0) {
          reject(results.errors[0]);
          return;
        }
        resolve(results.data);
      },
      error: reject,
    });
  });
}

function loadEmbeddedData() {
  if (!window.__KNICKS_DASHBOARD_DATA__) {
    throw new Error("Embedded dashboard data is unavailable.");
  }

  return {
    games: window.__KNICKS_DASHBOARD_DATA__.games || [],
    weekly: window.__KNICKS_DASHBOARD_DATA__.weekly || [],
    players: window.__KNICKS_DASHBOARD_DATA__.players || [],
    teams: window.__KNICKS_DASHBOARD_DATA__.teams || [],
    seasons: window.__KNICKS_DASHBOARD_DATA__.seasons || [],
  };
}

function toPercent(value) {
  return `${Number(value).toFixed(1)}%`;
}

function toSigned(value) {
  const number = Number(value || 0);
  return `${number > 0 ? "+" : ""}${number.toFixed(1)}`;
}

function buildSeasonOptions() {
  const seasonFilter = document.getElementById("seasonFilter");
  const seasons = [...new Set(state.games.map((row) => row.SEASON))];

  seasons.forEach((season) => {
    const option = document.createElement("option");
    option.value = season;
    option.textContent = season;
    seasonFilter.appendChild(option);
  });

  seasonFilter.value = seasons[seasons.length - 1];
}

function getFilters() {
  return {
    season: document.getElementById("seasonFilter").value,
    venue: document.getElementById("venueFilter").value,
    stage: document.getElementById("stageFilter").value,
  };
}

function applyFilters() {
  const filters = getFilters();
  const filteredGames = state.games
    .filter((game) => game.SEASON === filters.season)
    .filter((game) => filters.venue === "ALL" || game.HOME_AWAY === filters.venue)
    .filter((game) => filters.stage === "ALL" || game.FAN_STAGE === filters.stage)
    .sort((a, b) => a.GAME_NUMBER - b.GAME_NUMBER);

  const filteredWeekly = state.weekly.filter((week) => week.SEASON === filters.season);
  const filteredPlayers = state.players
    .filter((player) => player.SEASON === filters.season)
    .sort((a, b) => b.PTS - a.PTS)
    .slice(0, 8);
  const teamSeason = state.teams.find((team) => team.SEASON === filters.season);

  return { filters, filteredGames, filteredWeekly, filteredPlayers, teamSeason };
}

function summarize(filteredGames, filteredWeekly, teamSeason) {
  const awareness = filteredGames.length;
  const activationCount = filteredGames.filter((game) => game.ACTIVATION_EVENT === 1).length;
  const engagementCount = filteredGames.filter((game) => game.ENGAGEMENT_EVENT === 1).length;
  const retentionCount = filteredWeekly.filter((week) => week.RETENTION_EVENT === 1).length;

  return {
    awareness,
    activationRate: awareness ? (activationCount / awareness) * 100 : 0,
    engagementRate: awareness ? (engagementCount / awareness) * 100 : 0,
    retentionRate: filteredWeekly.length ? (retentionCount / filteredWeekly.length) * 100 : 0,
    activationCount,
    engagementCount,
    retentionCount,
    clutchRecord: teamSeason ? `${teamSeason.W}-${teamSeason.L}` : "0-0",
    clutchWinPct: teamSeason ? Number(teamSeason.W_PCT) * 100 : 0,
  };
}

function buildSignal(summary) {
  if (summary.activationRate >= 20 && summary.clutchWinPct >= 55) {
    return "Momentum Up";
  }
  if (summary.activationRate >= 18) {
    return "Strong Spikes";
  }
  return "Moments Matter";
}

function topGame(filteredGames) {
  return [...filteredGames]
    .sort((a, b) => {
      if (b.ACTIVATION_SCORE !== a.ACTIVATION_SCORE) return b.ACTIVATION_SCORE - a.ACTIVATION_SCORE;
      return b.PTS_DIFF - a.PTS_DIFF;
    })[0];
}

function updateHero(filteredGames, summary) {
  const bestGame = topGame(filteredGames);
  const signal = buildSignal(summary);

  document.getElementById("heroRecord").textContent = summary.clutchRecord;
  document.getElementById("heroPeakGame").textContent = bestGame ? bestGame.MATCHUP : "No games";
  document.getElementById("heroSignal").textContent = signal;
  document.getElementById("scoreboardPulse").textContent = String(bestGame ? bestGame.ACTIVATION_SCORE : 0).padStart(2, "0");
  document.getElementById("filterSummary").textContent = `${filteredGames.length} games in view`;

  if (bestGame) {
    document.getElementById("peakMatchup").textContent = bestGame.MATCHUP;
    document.getElementById("peakMeta").textContent =
      `${bestGame.GAME_DATE} | ${bestGame.RESULT_LABEL} | ${bestGame.PTS} points | ${toSigned(bestGame.PTS_DIFF)} differential | Activation score ${bestGame.ACTIVATION_SCORE}`;
  } else {
    document.getElementById("peakMatchup").textContent = "No games match the current filters";
    document.getElementById("peakMeta").textContent = "Try widening the venue or fan-stage filters.";
  }
}

function updateKpis(summary) {
  document.getElementById("awarenessValue").textContent = summary.awareness;
  document.getElementById("activationRateValue").textContent = toPercent(summary.activationRate);
  document.getElementById("engagementRateValue").textContent = toPercent(summary.engagementRate);
  document.getElementById("retentionRateValue").textContent = toPercent(summary.retentionRate);
}

function renderTopGames(filteredGames) {
  const rows = [...filteredGames]
    .sort((a, b) => {
      if (b.ACTIVATION_EVENT !== a.ACTIVATION_EVENT) return b.ACTIVATION_EVENT - a.ACTIVATION_EVENT;
      if (b.ACTIVATION_SCORE !== a.ACTIVATION_SCORE) return b.ACTIVATION_SCORE - a.ACTIVATION_SCORE;
      return b.PTS_DIFF - a.PTS_DIFF;
    })
    .slice(0, 8);

  const tableBody = document.getElementById("topGamesTable");
  tableBody.innerHTML = rows
    .map(
      (game) => `
        <tr>
          <td>${game.GAME_DATE}</td>
          <td>${game.MATCHUP}</td>
          <td><span class="result-pill ${game.WL === "W" ? "win" : "loss"}">${game.WL}</span></td>
          <td>${game.ACTIVATION_SCORE}</td>
        </tr>
      `
    )
    .join("");
}

function renderLeaderboard(filteredPlayers) {
  const tableBody = document.getElementById("leaderboardTable");
  tableBody.innerHTML = filteredPlayers
    .map(
      (player) => `
        <tr>
          <td>${player.PLAYER_NAME}</td>
          <td>${player.PTS}</td>
          <td>${player.PLUS_MINUS > 0 ? "+" : ""}${player.PLUS_MINUS}</td>
          <td>${(Number(player.FG_PCT) * 100).toFixed(1)}%</td>
        </tr>
      `
    )
    .join("");
}

function createOrUpdateActivationChart(filteredGames) {
  const labels = filteredGames.map((game) => `G${game.GAME_NUMBER}`);
  const activationScores = filteredGames.map((game) => Number(game.ACTIVATION_SCORE));
  const activatedGames = filteredGames.map((game) =>
    game.ACTIVATION_EVENT === 1 ? Number(game.ACTIVATION_SCORE) : null
  );

  const data = {
    labels,
    datasets: [
      {
        type: "line",
        label: "Activation Score",
        data: activationScores,
        borderColor: "#f58426",
        backgroundColor: "rgba(245,132,38,0.18)",
        borderWidth: 4,
        pointRadius: 3,
        pointHoverRadius: 5,
        tension: 0.35,
        fill: true,
      },
      {
        type: "scatter",
        label: "Activated Game",
        data: activatedGames,
        borderColor: "#1d428a",
        backgroundColor: "#1d428a",
        pointRadius: 5,
        pointHoverRadius: 7,
      },
    ],
  };

  const config = {
    data,
    options: {
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: {
            color: "#122242",
            usePointStyle: true,
          },
        },
        tooltip: {
          callbacks: {
            title(items) {
              const game = filteredGames[items[0].dataIndex];
              return `${game.GAME_DATE} | ${game.MATCHUP}`;
            },
            label(context) {
              const game = filteredGames[context.dataIndex];
              return [
                `Activation score: ${game.ACTIVATION_SCORE}`,
                `Fan stage: ${game.FAN_STAGE}`,
                `Result: ${game.RESULT_LABEL}`,
              ];
            },
          },
        },
      },
      scales: {
        x: {
          ticks: {
            color: "#697692",
            maxTicksLimit: 10,
          },
          grid: {
            color: "rgba(18,34,66,0.06)",
          },
        },
        y: {
          beginAtZero: true,
          ticks: {
            color: "#697692",
          },
          grid: {
            color: "rgba(18,34,66,0.08)",
          },
        },
      },
    },
  };

  if (state.charts.activationTrend) {
    state.charts.activationTrend.data = data;
    state.charts.activationTrend.options = config.options;
    state.charts.activationTrend.update();
    return;
  }

  state.charts.activationTrend = new Chart(
    document.getElementById("activationTrendChart"),
    {
      type: "line",
      ...config,
    }
  );
}

function createOrUpdateFunnelChart(summary) {
  const data = {
    labels: ["Awareness", "Activation", "Engagement", "Retention"],
    datasets: [
      {
        label: "Funnel Count",
        data: [
          summary.awareness,
          summary.activationCount,
          summary.engagementCount,
          summary.retentionCount,
        ],
        backgroundColor: ["#1d428a", "#416fbf", "#f58426", "#ffb368"],
        borderRadius: 14,
      },
    ],
  };

  const options = {
    indexAxis: "y",
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        callbacks: {
          label(context) {
            return `Count: ${context.raw}`;
          },
        },
      },
    },
    scales: {
      x: {
        ticks: {
          color: "#697692",
        },
        grid: {
          color: "rgba(18,34,66,0.08)",
        },
      },
      y: {
        ticks: {
          color: "#122242",
        },
        grid: {
          display: false,
        },
      },
    },
  };

  if (state.charts.funnel) {
    state.charts.funnel.data = data;
    state.charts.funnel.options = options;
    state.charts.funnel.update();
    return;
  }

  state.charts.funnel = new Chart(document.getElementById("funnelChart"), {
    type: "bar",
    data,
    options,
  });
}

function renderDashboard() {
  const { filteredGames, filteredWeekly, filteredPlayers, teamSeason } = applyFilters();
  const summary = summarize(filteredGames, filteredWeekly, teamSeason);

  updateHero(filteredGames, summary);
  updateKpis(summary);
  renderTopGames(filteredGames);
  renderLeaderboard(filteredPlayers);
  createOrUpdateActivationChart(filteredGames);
  createOrUpdateFunnelChart(summary);
}

async function init() {
  let loadedData;

  try {
    const [games, weekly, players, teams, seasons] = await Promise.all([
      parseCsv(DATA_FILES.games),
      parseCsv(DATA_FILES.weekly),
      parseCsv(DATA_FILES.players),
      parseCsv(DATA_FILES.teams),
      parseCsv(DATA_FILES.seasons),
    ]);
    loadedData = { games, weekly, players, teams, seasons };
  } catch (csvError) {
    console.warn("CSV loading failed, falling back to embedded dashboard data.", csvError);
    loadedData = loadEmbeddedData();
    document.getElementById("filterSummary").textContent = "Using built-in dashboard data";
  }

  state.games = loadedData.games;
  state.weekly = loadedData.weekly;
  state.players = loadedData.players;
  state.teams = loadedData.teams;
  state.seasons = loadedData.seasons;

  buildSeasonOptions();

  document.getElementById("seasonFilter").addEventListener("change", renderDashboard);
  document.getElementById("venueFilter").addEventListener("change", renderDashboard);
  document.getElementById("stageFilter").addEventListener("change", renderDashboard);

  renderDashboard();
}

init().catch((error) => {
  console.error(error);
  document.getElementById("filterSummary").textContent = "Could not load CSV data";
});
