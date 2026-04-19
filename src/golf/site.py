from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def render_html() -> str:
    return """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Golf range analytics</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
      :root {
        color-scheme: dark;
        --bg: #081018;
        --panel: #0f1d2c;
        --text: #f4f7fb;
        --muted: #9fb2c8;
        --accent: #57b5ff;
        --accent-soft: rgba(87, 181, 255, 0.15);
        --warn: #ffb454;
        --good: #5fd18b;
        --bad: #ff7b72;
        --border: rgba(255, 255, 255, 0.08);
      }

      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background: linear-gradient(180deg, #07111a 0%, #091726 100%);
        color: var(--text);
      }
      main {
        max-width: 1200px;
        margin: 0 auto;
        padding: 40px 20px 64px;
      }
      h1, h2, h3 { margin: 0 0 12px; }
      p { color: var(--muted); line-height: 1.6; }
      .hero {
        display: grid;
        gap: 20px;
        margin-bottom: 28px;
      }
      .badge {
        display: inline-flex;
        padding: 6px 10px;
        border-radius: 999px;
        background: var(--accent-soft);
        color: var(--accent);
        font-size: 0.88rem;
        font-weight: 700;
        letter-spacing: 0.02em;
      }
      .grid {
        display: grid;
        gap: 16px;
      }
      .stats {
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        margin-bottom: 24px;
      }
      .panel {
        background: rgba(15, 29, 44, 0.94);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 20px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
      }
      .stat-value {
        font-size: 1.9rem;
        font-weight: 800;
        margin-bottom: 4px;
      }
      .stat-label {
        color: var(--muted);
        font-size: 0.92rem;
      }
      .recommendations {
        margin-bottom: 28px;
      }
      .recommendation-list {
        display: grid;
        gap: 12px;
      }
      .recommendation {
        border-left: 4px solid var(--warn);
        padding: 16px;
        border-radius: 14px;
        background: rgba(255, 255, 255, 0.03);
      }
      .recommendation-header {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        align-items: baseline;
      }
      .severity {
        color: var(--warn);
        font-weight: 700;
      }
      .charts {
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        margin-bottom: 28px;
      }
      .chart-wrap {
        min-height: 320px;
      }
      .tables {
        grid-template-columns: 1fr;
      }
      table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.95rem;
      }
      th, td {
        padding: 12px 10px;
        border-bottom: 1px solid var(--border);
        text-align: left;
      }
      th {
        color: var(--muted);
        font-weight: 600;
      }
      .session-card {
        padding: 14px 16px;
        border-radius: 14px;
        background: rgba(255, 255, 255, 0.03);
      }
      .session-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        color: var(--muted);
        font-size: 0.92rem;
      }
      .small {
        font-size: 0.88rem;
        color: var(--muted);
      }
      @media (max-width: 700px) {
        main { padding: 28px 14px 48px; }
        .panel { padding: 16px; }
        th, td { padding: 10px 8px; }
      }
    </style>
  </head>
  <body>
    <main>
      <section class="hero">
        <div class="badge">GitHub Pages range dashboard</div>
        <div class="panel">
          <h1>Golf range analytics</h1>
          <p id="hero-text"></p>
          <p class="small" id="generated-at"></p>
        </div>
      </section>

      <section class="grid stats" id="overview"></section>

      <section class="panel recommendations">
        <h2>What to work on</h2>
        <div class="recommendation-list" id="recommendations"></div>
      </section>

      <section class="grid charts">
        <div class="panel chart-wrap">
          <h2>Session trend</h2>
          <canvas id="sessionTrend"></canvas>
        </div>
        <div class="panel chart-wrap">
          <h2>Club carry and consistency</h2>
          <canvas id="clubBars"></canvas>
        </div>
        <div class="panel chart-wrap" style="grid-column: 1 / -1;">
          <h2>Dispersion map</h2>
          <canvas id="dispersionChart"></canvas>
        </div>
      </section>

      <section class="grid tables">
        <div class="panel">
          <h2>Club summary</h2>
          <div style="overflow-x:auto;">
            <table>
              <thead>
                <tr>
                  <th>Club</th>
                  <th>Shots</th>
                  <th>Avg carry</th>
                  <th>Avg smash</th>
                  <th>Avg offline</th>
                  <th>Consistency</th>
                  <th>Outliers</th>
                </tr>
              </thead>
              <tbody id="club-summary-body"></tbody>
            </table>
          </div>
        </div>
        <div class="panel">
          <h2>Sessions</h2>
          <div class="grid" id="sessions"></div>
        </div>
      </section>
    </main>

    <script src="./site-data.js"></script>
    <script>
      const data = window.GOLF_SITE_DATA;

      const number = (value, digits = 1, suffix = "") => {
        if (value === null || value === undefined || Number.isNaN(value)) return "—";
        return `${Number(value).toFixed(digits)}${suffix}`;
      };

      document.getElementById("hero-text").textContent =
        `Tracking ${data.overview.total_sessions} session(s), ${data.overview.total_shots} shots, and ${data.overview.tracked_clubs} clubs. The recommendations below are generated from your uploaded CSVs.`;
      document.getElementById("generated-at").textContent = `Generated ${new Date(data.generated_at).toLocaleString()}`;

      const overviewItems = [
        ["Sessions", data.overview.total_sessions, 0],
        ["Shots", data.overview.total_shots, 0],
        ["Tracked clubs", data.overview.tracked_clubs, 0],
        ["Avg consistency", data.overview.avg_consistency_score, 1],
        ["Outlier rate", data.overview.avg_outlier_rate, 1, "%"],
      ];

      const overview = document.getElementById("overview");
      overviewItems.forEach(([label, value, digits, suffix = ""]) => {
        const card = document.createElement("div");
        card.className = "panel";
        card.innerHTML = `<div class="stat-value">${number(value, digits, suffix)}</div><div class="stat-label">${label}</div>`;
        overview.appendChild(card);
      });

      const recommendations = document.getElementById("recommendations");
      if (!data.recommendations.length) {
        const empty = document.createElement("p");
        empty.textContent = "No high-priority recommendations yet. Add more sessions to unlock trend-based coaching prompts.";
        recommendations.appendChild(empty);
      } else {
        data.recommendations.forEach((item) => {
          const div = document.createElement("div");
          div.className = "recommendation";
          div.innerHTML = `
            <div class="recommendation-header">
              <h3>${item.title}</h3>
              <div class="severity">Severity ${item.severity}</div>
            </div>
            <p>${item.summary}</p>
            <div class="small">${item.focus_area} • ${item.evidence}</div>
          `;
          recommendations.appendChild(div);
        });
      }

      const clubSummaryBody = document.getElementById("club-summary-body");
      data.clubs.forEach((club) => {
        const row = document.createElement("tr");
        const offline = club.avg_total_deviation_distance ?? club.avg_carry_deviation_distance;
        row.innerHTML = `
          <td>${club.club_label}</td>
          <td>${club.shot_count}</td>
          <td>${number(club.avg_carry_distance, 1, " yds")}</td>
          <td>${number(club.avg_smash_factor, 2)}</td>
          <td>${number(offline, 1, " yds")}</td>
          <td>${number(club.consistency_score, 1)}</td>
          <td>${number(club.outlier_rate, 0, "%")}</td>
        `;
        clubSummaryBody.appendChild(row);
      });

      const sessions = document.getElementById("sessions");
      data.sessions.forEach((session) => {
        const card = document.createElement("div");
        card.className = "session-card";
        card.innerHTML = `
          <h3>${session.source_file}</h3>
          <div class="session-meta">
            <span>${session.player || "Unknown player"}</span>
            <span>${session.shot_count} shots</span>
            <span>${session.club_count} clubs</span>
            <span>${number(session.avg_carry_distance, 1, " yds avg carry")}</span>
            <span>${number(session.avg_offline_distance, 1, " yds avg offline")}</span>
            <span>${number(session.outlier_rate, 0, "%")} outliers</span>
          </div>
        `;
        sessions.appendChild(card);
      });

      new Chart(document.getElementById("sessionTrend"), {
        type: "line",
        data: {
          labels: data.charts.timeline.labels,
          datasets: [
            {
              label: "Avg carry (yds)",
              data: data.charts.timeline.avg_carry_distance,
              borderColor: "#57b5ff",
              backgroundColor: "rgba(87, 181, 255, 0.15)",
              tension: 0.3,
              yAxisID: "y",
            },
            {
              label: "Avg smash",
              data: data.charts.timeline.avg_smash_factor,
              borderColor: "#5fd18b",
              backgroundColor: "rgba(95, 209, 139, 0.15)",
              tension: 0.3,
              yAxisID: "y1",
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: { mode: "index", intersect: false },
          scales: {
            y: { beginAtZero: false, position: "left" },
            y1: { beginAtZero: false, position: "right", grid: { drawOnChartArea: false } },
          },
        },
      });

      new Chart(document.getElementById("clubBars"), {
        type: "bar",
        data: {
          labels: data.charts.clubs.labels,
          datasets: [
            {
              label: "Avg carry (yds)",
              data: data.charts.clubs.avg_carry_distance,
              backgroundColor: "rgba(87, 181, 255, 0.6)",
            },
            {
              label: "Consistency score",
              data: data.charts.clubs.consistency_score,
              backgroundColor: "rgba(95, 209, 139, 0.6)",
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
        },
      });

      const dispersionByClub = {};
      data.charts.dispersion.forEach((point) => {
        if (!dispersionByClub[point.club]) dispersionByClub[point.club] = [];
        dispersionByClub[point.club].push(point);
      });
      const colors = ["#57b5ff", "#5fd18b", "#ffb454", "#ff7b72", "#9b8cff", "#7ce2ff"];
      const dispersionDatasets = Object.entries(dispersionByClub).map(([club, points], index) => ({
        label: club,
        data: points,
        parsing: false,
        pointRadius: 4,
        pointHoverRadius: 6,
        borderWidth: 0,
        backgroundColor: colors[index % colors.length],
      }));
      new Chart(document.getElementById("dispersionChart"), {
        type: "scatter",
        data: { datasets: dispersionDatasets },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: { title: { display: true, text: "Offline / deviation (yds)" } },
            y: { title: { display: true, text: "Carry distance (yds)" } },
          },
        },
      });
    </script>
  </body>
</html>
"""


def write_site(data: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "site-data.js").write_text(
        "window.GOLF_SITE_DATA = " + json.dumps(data, indent=2) + ";\n",
        encoding="utf-8",
    )
    (output_dir / "index.html").write_text(render_html(), encoding="utf-8")
    (output_dir / ".nojekyll").write_text("", encoding="utf-8")
