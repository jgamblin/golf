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
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>
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
      .hero-header {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
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
      .hero-chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 0.82rem;
        font-weight: 600;
        color: var(--muted);
      }
      .hero-title {
        font-size: clamp(1.7rem, 4vw, 2.4rem);
        letter-spacing: 0.01em;
      }
      .hero-sub {
        margin-top: 6px;
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
      .next-session {
        margin-bottom: 28px;
      }
      .next-session-list {
        list-style: none;
        padding: 0;
        margin: 0;
        display: grid;
        gap: 10px;
      }
      .next-session-item {
        border-left: 4px solid var(--good);
        padding: 12px 14px;
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.03);
      }
      .next-session-item h3 {
        margin: 0 0 4px;
        font-size: 1rem;
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
        display: flex;
        flex-direction: column;
      }
      .chart-canvas {
        position: relative;
        height: 320px;
        width: 100%;
      }
      .chart-canvas.tall {
        height: 420px;
      }
      .chart-canvas canvas {
        width: 100% !important;
        height: 100% !important;
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
      .delta {
        font-weight: 700;
        white-space: nowrap;
      }
      .delta-pos { color: var(--good); }
      .delta-neg { color: var(--bad); }
      .delta-neutral { color: var(--muted); }
      .club-toggles {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 14px;
      }
      .club-toggle {
        padding: 5px 12px;
        border-radius: 999px;
        border: 1.5px solid transparent;
        font-size: 0.85rem;
        font-weight: 600;
        cursor: pointer;
        transition: opacity 0.2s, border-color 0.2s;
        background: rgba(255, 255, 255, 0.07);
        color: var(--text);
      }
      .club-toggle.off {
        opacity: 0.35;
        border-color: transparent;
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
        <div class="panel">
          <div class="hero-header">
            <div class="badge">Range Performance Lab</div>
            <div class="hero-chip" id="latest-session-chip"></div>
          </div>
          <h1 class="hero-title">Golf range analytics</h1>
          <p id="hero-text"></p>
          <p class="hero-sub" id="hero-subtext"></p>
          <p class="small" id="generated-at"></p>
        </div>
      </section>

      <section class="grid stats" id="overview"></section>

      <section class="grid charts">
        <div class="panel chart-wrap">
          <h2>Session trend</h2>
          <div class="chart-canvas">
            <canvas id="sessionTrend"></canvas>
          </div>
        </div>
        <div class="panel chart-wrap">
          <h2>Club carry and consistency</h2>
          <div class="chart-canvas">
            <canvas id="clubBars"></canvas>
          </div>
        </div>
        <div class="panel chart-wrap" style="grid-column: 1 / -1;">
          <h2>Dispersion map</h2>
          <div class="club-toggles" id="dispersionToggles"></div>
          <div class="chart-canvas tall">
            <canvas id="dispersionChart"></canvas>
          </div>
        </div>
        <div class="panel chart-wrap" style="grid-column: 1 / -1;">
          <h2>Miss direction trend</h2>
          <p style="margin:0 0 8px;font-size:0.88rem;color:var(--muted)">Positive = right miss &nbsp;|&nbsp; Negative = left miss</p>
          <div class="chart-canvas">
            <canvas id="missDirectionChart"></canvas>
          </div>
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
        <div class="panel">
          <h2>Latest vs previous session</h2>
          <p class="small" id="delta-caption"></p>
          <div style="overflow-x:auto;">
            <table>
              <thead>
                <tr>
                  <th>Club</th>
                  <th>Shots</th>
                  <th>Carry delta</th>
                  <th>Smash delta</th>
                  <th>Offline delta</th>
                </tr>
              </thead>
              <tbody id="session-delta-body"></tbody>
            </table>
          </div>
        </div>
      </section>

      <section class="panel next-session">
        <h2>Work on next session</h2>
        <div class="next-session-list" id="next-session-list"></div>
      </section>

      <section class="panel recommendations">
        <h2>What to work on</h2>
        <div class="recommendation-list" id="recommendations"></div>
      </section>
    </main>

    <script src="./site-data.js"></script>
    <script>
      const data = window.GOLF_SITE_DATA;
      const chartGrid = document.querySelector(".charts");

      const number = (value, digits = 1, suffix = "") => {
        if (value === null || value === undefined || Number.isNaN(value)) return "—";
        return `${Number(value).toFixed(digits)}${suffix}`;
      };

      const deltaHtml = (value, digits = 1, suffix = "", invertGood = false) => {
        if (value === null || value === undefined || Number.isNaN(value)) {
          return '<span class="delta delta-neutral">—</span>';
        }
        const numeric = Number(value);
        const isNeutral = Math.abs(numeric) < 0.001;
        const direction = isNeutral ? "" : numeric > 0 ? " &uarr;" : " &darr;";
        const isPositiveOutcome = isNeutral ? null : (invertGood ? numeric < 0 : numeric > 0);
        const cls = isNeutral ? "delta-neutral" : (isPositiveOutcome ? "delta-pos" : "delta-neg");
        const sign = numeric > 0 ? "+" : "";
        return `<span class="delta ${cls}">${sign}${numeric.toFixed(digits)}${suffix}${direction}</span>`;
      };

      const showChartError = (message) => {
        if (!chartGrid) return;
        const error = document.createElement("p");
        error.className = "small";
        error.textContent = message;
        chartGrid.prepend(error);
      };

      const createChart = (elementId, config) => {
        const canvas = document.getElementById(elementId);
        if (!canvas || typeof window.Chart === "undefined") {
          return null;
        }
        return new window.Chart(canvas, config);
      };

      document.getElementById("hero-text").textContent =
        `Tracking ${data.overview.total_sessions} session(s), ${data.overview.total_shots} shots, and ${data.overview.tracked_clubs} clubs. The recommendations below are generated from your uploaded CSVs.`;
      document.getElementById("generated-at").textContent = `Generated ${new Date(data.generated_at).toLocaleString()}`;

      const latestSession = data.sessions.length ? data.sessions[data.sessions.length - 1] : null;
      document.getElementById("latest-session-chip").textContent = latestSession && latestSession.session_timestamp
        ? `Latest session ${new Date(latestSession.session_timestamp).toLocaleDateString()}`
        : "Latest session unavailable";
      document.getElementById("hero-subtext").textContent = data.next_session_worklist?.length
        ? `${data.next_session_worklist.length} focus item(s) generated for your next practice block.`
        : "Add another session to unlock a personalized next-session focus list.";

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

      const nextSessionList = document.getElementById("next-session-list");
      if (!data.next_session_worklist || !data.next_session_worklist.length) {
        const empty = document.createElement("p");
        empty.className = "small";
        empty.textContent = "No specific next-session priorities yet. Keep uploading sessions to build trend-aware tasks.";
        nextSessionList.appendChild(empty);
      } else {
        data.next_session_worklist.forEach((item) => {
          const card = document.createElement("div");
          card.className = "next-session-item";
          card.innerHTML = `
            <h3>${item.title}</h3>
            <p>${item.summary}</p>
            <div class="small">${item.focus_area} • ${item.evidence}</div>
          `;
          nextSessionList.appendChild(card);
        });
      }

      const deltaCaption = document.getElementById("delta-caption");
      const deltaBody = document.getElementById("session-delta-body");
      const deltas = data.latest_session_deltas;
      if (!deltas || !deltas.available || !deltas.clubs.length) {
        deltaCaption.textContent = "Need at least two sessions with overlapping clubs to show deltas.";
        const row = document.createElement("tr");
        row.innerHTML = `<td colspan="5" class="small">No comparable clubs available.</td>`;
        deltaBody.appendChild(row);
      } else {
        const latestLabel = deltas.latest_label ? String(deltas.latest_label).slice(0, 10) : "latest";
        const previousLabel = deltas.previous_label ? String(deltas.previous_label).slice(0, 10) : "previous";
        deltaCaption.textContent = `${latestLabel} compared with ${previousLabel}`;
        deltas.clubs.forEach((item) => {
          const row = document.createElement("tr");
          row.innerHTML = `
            <td>${item.club_label}</td>
            <td>${item.latest_shot_count ?? "-"}</td>
            <td>${deltaHtml(item.carry_delta, 1, " yds")}</td>
            <td>${deltaHtml(item.smash_delta, 2)}</td>
            <td>${deltaHtml(item.offline_delta, 1, " yds", true)}</td>
          `;
          deltaBody.appendChild(row);
        });
      }

      const sessionTrendChart = createChart("sessionTrend", {
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

      const clubBarChart = createChart("clubBars", {
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
              yAxisID: "y1",
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: { beginAtZero: true, title: { display: true, text: "Carry distance (yds)" } },
            y1: {
              beginAtZero: true,
              position: "right",
              max: 100,
              grid: { drawOnChartArea: false },
              title: { display: true, text: "Consistency score" },
            },
          },
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
        data: points.map((point) => ({ x: point.x, y: point.y })),
        pointRadius: 4,
        pointHoverRadius: 6,
        borderWidth: 0,
        backgroundColor: colors[index % colors.length],
      }));
      const dispersionChart = createChart("dispersionChart", {
        type: "scatter",
        data: { datasets: dispersionDatasets },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { type: "linear", title: { display: true, text: "Offline / deviation (yds)" } },
            y: { type: "linear", title: { display: true, text: "Carry distance (yds)" } },
          },
        },
      });

      // ── Club toggle buttons for dispersion map ──────────────────────────
      const togglesContainer = document.getElementById("dispersionToggles");
      if (togglesContainer && dispersionChart) {
        dispersionDatasets.forEach((ds, index) => {
          const btn = document.createElement("button");
          btn.className = "club-toggle";
          btn.textContent = ds.label;
          btn.style.borderColor = colors[index % colors.length];
          btn.addEventListener("click", () => {
            const meta = dispersionChart.getDatasetMeta(index);
            meta.hidden = !meta.hidden;
            btn.classList.toggle("off", meta.hidden);
            dispersionChart.update();
          });
          togglesContainer.appendChild(btn);
        });
      }

      // ── Miss direction trend chart ───────────────────────────────────────
      const missDirectionChart = createChart("missDirectionChart", {
        type: "bar",
        data: {
          labels: data.charts.timeline.labels,
          datasets: [
            {
              label: "Avg lateral miss (yds)",
              data: data.charts.timeline.miss_direction,
              backgroundColor: data.charts.timeline.miss_direction.map((v) =>
                v === null ? "transparent" : v > 0 ? "rgba(255, 123, 114, 0.7)" : "rgba(87, 181, 255, 0.7)"
              ),
              borderColor: data.charts.timeline.miss_direction.map((v) =>
                v === null ? "transparent" : v > 0 ? "#ff7b72" : "#57b5ff"
              ),
              borderWidth: 1,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            tooltip: {
              callbacks: {
                label: (ctx) => {
                  const v = ctx.parsed.y;
                  if (v === null) return "No data";
                  return `${Math.abs(v).toFixed(1)} yds ${v > 0 ? "right" : "left"}`;
                },
              },
            },
          },
          scales: {
            y: {
              title: { display: true, text: "Lateral deviation (yds)" },
              ticks: {
                callback: (v) => (v > 0 ? `+${v} R` : v < 0 ? `${v} L` : "0"),
              },
            },
          },
        },
      });

      if (!sessionTrendChart || !clubBarChart || !dispersionChart || !missDirectionChart) {
        showChartError("Some charts could not be initialized. Refresh after the page assets finish loading.");
      }
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
