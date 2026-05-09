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
    <title>Bad at golf. Great at data. — Jerry Gamblin</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,700;1,900&display=swap" rel="stylesheet">
    <style>
      :root {
        --bg: #F2F2F0;
        --panel: #ffffff;
        --text: #1E340A;
        --muted: #4D6E24;
        --accent: #408114;
        --accent2: #1B7114;
        --accent-soft: rgba(64, 129, 20, 0.10);
        --warn: #b45309;
        --good: #1B7114;
        --bad: #b45309;
        --border: rgba(30, 52, 10, 0.12);
      }

      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background: linear-gradient(180deg, #F2F2F0 0%, #ebebea 100%);
        color: var(--text);
      }
      main {
        max-width: 1200px;
        margin: 0 auto;
        padding: 40px 20px 64px;
      }
      h1, h2, h3 { margin: 0 0 12px; }
      p { color: var(--muted); line-height: 1.6; }

      /* ── Hero ───────────────────────────────────────── */
      .hero { display: grid; gap: 20px; margin-bottom: 28px; }
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
      .gh-link {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        font-size: 0.82rem;
        font-weight: 600;
        color: var(--muted);
        text-decoration: none;
        transition: color 0.15s;
      }
      .gh-link:hover { color: var(--accent); }
      .hero-title { font-size: clamp(1.7rem, 4vw, 2.4rem); letter-spacing: 0.01em; }
      .hero-sub { margin-top: 6px; }
      .hero-eyebrow {
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--muted);
        margin-bottom: 10px;
      }
      .hero-title {
        font-family: 'Playfair Display', Georgia, serif;
        font-size: clamp(1.9rem, 5vw, 2.8rem);
        font-weight: 700;
        line-height: 1.1;
        letter-spacing: 0;
      }
      .hero-title em { font-style: italic; color: var(--accent); }
      .hero-divider {
        width: 40px; height: 3px;
        background: var(--accent);
        border-radius: 2px;
        margin: 12px 0 14px;
      }
      .hero-stat-row { display: flex; gap: 28px; flex-wrap: wrap; margin-top: 16px; }
      .hero-stat-val { font-size: 1.3rem; font-weight: 800; color: var(--accent); line-height: 1; }
      .hero-stat-lbl {
        font-size: 0.72rem; font-weight: 600; color: var(--muted);
        text-transform: uppercase; letter-spacing: 0.04em; margin-top: 2px;
      }

      /* ── Grid & panels ──────────────────────────────── */
      .grid { display: grid; gap: 16px; }
      .stats {
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        margin-bottom: 24px;
      }
      .panel {
        background: rgba(15, 29, 44, 0.94);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 20px;
        box-shadow: 0 2px 16px rgba(30, 52, 10, 0.07);
      }
      .stat-value { font-size: 1.9rem; font-weight: 800; margin-bottom: 4px; }
      .stat-label { color: var(--muted); font-size: 0.92rem; }

      /* ── Next session focus ─────────────────────────── */
      .next-session { margin-bottom: 28px; }
      .next-session-list {
        list-style: none;
        padding: 0;
        margin: 0;
        display: grid;
        gap: 10px;
        grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      }
      .next-session-item {
        border-left: 4px solid var(--good);
        padding: 12px 14px;
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.03);
      }
      .next-session-item h3 { margin: 0 0 4px; font-size: 1rem; }

      /* ── Charts ─────────────────────────────────────── */
      .charts {
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        margin-bottom: 28px;
      }
      .chart-wrap { display: flex; flex-direction: column; }
      .chart-canvas { position: relative; height: 320px; width: 100%; }
      .chart-canvas.tall { height: 420px; }
      .chart-canvas canvas { width: 100% !important; height: 100% !important; }

      /* ── Club toggles ───────────────────────────────── */
      .club-toggles { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; }
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
      .club-toggle.off { opacity: 0.35; border-color: transparent; }

      /* ── Consistency heatmap ────────────────────────── */
      .heatmap-wrap { overflow-x: auto; }
      .heatmap-table {
        border-collapse: separate;
        border-spacing: 4px;
        font-size: 0.88rem;
      }
      .heatmap-table th {
        color: var(--muted);
        font-weight: 600;
        padding: 4px 10px;
        white-space: nowrap;
        text-align: center;
      }
      .heatmap-table th:first-child { text-align: left; }
      .heatmap-cell {
        padding: 8px 12px;
        border-radius: 8px;
        text-align: center;
        font-weight: 700;
        font-size: 0.85rem;
        min-width: 56px;
      }
      .heatmap-club {
        padding: 8px 12px 8px 0;
        font-weight: 600;
        font-size: 0.88rem;
        white-space: nowrap;
      }
      .heatmap-empty {
        padding: 8px 12px;
        border-radius: 8px;
        text-align: center;
        color: var(--muted);
        background: rgba(255, 255, 255, 0.03);
        min-width: 56px;
      }

      /* ── Tables ─────────────────────────────────────── */
      .tables { grid-template-columns: 1fr; margin-bottom: 28px; }
      table { width: 100%; border-collapse: collapse; font-size: 0.95rem; }
      th, td { padding: 12px 10px; border-bottom: 1px solid var(--border); text-align: left; }
      th { color: var(--muted); font-weight: 600; }

      /* ── Session cards ──────────────────────────────── */
      .sessions-grid {
        display: grid;
        gap: 14px;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      }
      .session-card {
        padding: 16px;
        border-radius: 14px;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid var(--border);
      }
      .session-date { font-size: 1.05rem; font-weight: 700; margin-bottom: 6px; }
      .session-rating-row {
        display: flex;
        align-items: baseline;
        gap: 6px;
        margin-bottom: 10px;
        font-size: 0.85rem;
      }
      .session-rating-label {
        color: var(--muted);
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        font-weight: 600;
      }
      .session-rating-value {
        font-size: 1.45rem;
        font-weight: 800;
        line-height: 1;
      }
      .session-rating-trend { font-weight: 700; font-size: 0.82rem; }
      .session-stats {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 8px;
      }
      .session-stat { display: flex; flex-direction: column; gap: 2px; }
      .session-stat-value { color: var(--text); font-weight: 600; font-size: 0.95rem; }
      .session-stat-label { font-size: 0.75rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; }

      /* ── Recommendations ────────────────────────────── */
      .recommendations { margin-bottom: 28px; }
      .recommendation-list { display: grid; gap: 12px; }
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
      .severity { color: var(--warn); font-weight: 700; }

      /* ── Tabs ────────────────────────────────────────── */
      .tab-nav {
        display: flex;
        gap: 4px;
        margin-bottom: 24px;
        border-bottom: 1px solid var(--border);
        padding-bottom: 0;
      }
      .tab-btn {
        padding: 10px 22px;
        background: none;
        border: none;
        border-bottom: 3px solid transparent;
        color: var(--muted);
        font-size: 0.97rem;
        font-weight: 600;
        cursor: pointer;
        transition: color 0.15s, border-color 0.15s;
        margin-bottom: -1px;
        border-radius: 6px 6px 0 0;
        font-family: inherit;
      }
      .tab-btn:hover { color: var(--text); }
      .tab-btn.active {
        color: var(--accent);
        border-bottom-color: var(--accent);
        background: rgba(87, 181, 255, 0.06);
      }
      .tab-panel { display: none; }
      .tab-panel.active { display: block; }

      /* ── Coaching tab ───────────────────────────────── */
      .coaching-grid {
        display: grid;
        gap: 24px;
      }

      /* ── Misc ───────────────────────────────────────── */
      .small { font-size: 0.88rem; color: var(--muted); }
      .delta { font-weight: 700; white-space: nowrap; }
      .delta-pos { color: var(--good); }
      .delta-neg { color: var(--bad); }
      .delta-neutral { color: var(--muted); }

      @media (max-width: 700px) {
        main { padding: 28px 14px 48px; }
        .panel { padding: 16px; }
        th, td { padding: 10px 8px; }
        .session-stats { grid-template-columns: repeat(2, 1fr); }
      }
    </style>
  </head>
  <body>
    <main>

      <!-- ── Hero ──────────────────────────────────────── -->
      <section class="hero">
        <div class="panel">
          <div class="hero-header">
            <div class="hero-eyebrow">Jerry Gamblin &bull; Range Performance Lab</div>
            <a class="gh-link" href="https://github.com/jgamblin/golf" target="_blank" rel="noopener">
              <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>
              GitHub
            </a>
          </div>
          <h1 class="hero-title">Bad at golf.<br><em>Great</em> at data.</h1>
          <div class="hero-divider"></div>
          <p id="hero-text"></p>
          <div class="hero-stat-row" id="hero-stats"></div>
          <p class="small" id="generated-at" style="margin-top:14px;"></p>
        </div>
      </section>

      <!-- ── Overview stats ─────────────────────────────── -->
      <section class="grid stats" id="overview"></section>

      <!-- ── Tab navigation ────────────────────────────── -->
      <nav class="tab-nav" role="tablist">
        <button class="tab-btn active" role="tab" aria-selected="true" aria-controls="tab-dashboard" id="btn-dashboard">Dashboard</button>
        <button class="tab-btn" role="tab" aria-selected="false" aria-controls="tab-coaching" id="btn-coaching">Coaching</button>
      </nav>

      <!-- ══ DASHBOARD TAB ════════════════════════════════ -->
      <div class="tab-panel active" id="tab-dashboard" role="tabpanel" aria-labelledby="btn-dashboard">

      <!-- ── Charts ────────────────────────────────────── -->
      <section class="grid charts">

        <div class="panel chart-wrap">
          <h2>Session trend</h2>
          <div class="chart-canvas">
            <canvas id="sessionTrend"></canvas>
          </div>
        </div>

        <div class="panel chart-wrap">
          <h2>Smash factor: actual vs potential</h2>
          <p class="small" style="margin:0 0 8px">Bars = session average &nbsp;|&nbsp; Line = your personal 90th-percentile ceiling</p>
          <div class="chart-canvas">
            <canvas id="smashHeadroomChart"></canvas>
          </div>
        </div>

        <div class="panel chart-wrap">
          <h2>Club carry and consistency</h2>
          <div class="chart-canvas">
            <canvas id="clubBars"></canvas>
          </div>
        </div>

        <div class="panel chart-wrap" style="grid-column: 1 / -1;">
          <h2>Bag gapping</h2>
          <p class="small" style="margin:0 0 8px">Clubs sorted by average carry — shaded band = avg &plusmn; 1 SD. Yellow = clubs within 7 yds of each other.</p>
          <div class="chart-canvas">
            <canvas id="bagGapChart"></canvas>
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

      <!-- ── Consistency heatmap ────────────────────────── -->
      <section class="panel" style="margin-bottom:28px;">
        <h2>Consistency by session</h2>
        <p class="small" style="margin:0 0 14px">Score per club per session. <span style="color:var(--good)">&#9646;</span> &ge;75 &nbsp;<span style="color:var(--warn)">&#9646;</span> 50&ndash;74 &nbsp;<span style="color:var(--bad)">&#9646;</span> &lt;50 &nbsp; &mdash; = not played</p>
        <div class="heatmap-wrap" id="consistency-heatmap"></div>
      </section>

      <!-- ── Tables ────────────────────────────────────── -->
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
          <div class="sessions-grid" id="sessions"></div>
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

      </div>
      <!-- ══ end DASHBOARD TAB ═══════════════════════════ -->

      <!-- ══ COACHING TAB ═════════════════════════════════ -->
      <div class="tab-panel" id="tab-coaching" role="tabpanel" aria-labelledby="btn-coaching">
        <div class="coaching-grid">

          <section class="panel next-session">
            <h2>Next session focus</h2>
            <div class="next-session-list" id="next-session-list"></div>
          </section>

          <section class="panel recommendations">
            <h2>What to work on</h2>
            <div class="recommendation-list" id="recommendations"></div>
          </section>

        </div>
      </div>
      <!-- ══ end COACHING TAB ═════════════════════════════ -->

    </main>

    <script src="./site-data.js"></script>
    <script>
      const data = window.GOLF_SITE_DATA;
      const chartGrid = document.querySelector(".charts");
      const COLORS = ["#408114","#1B7114","#4D6E24","#b45309","#6b7280","#0369a1","#7c3aed","#0d9488"];

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
        const err = document.createElement("p");
        err.className = "small";
        err.textContent = message;
        chartGrid.prepend(err);
      };

      const createChart = (elementId, config) => {
        const canvas = document.getElementById(elementId);
        if (!canvas || typeof window.Chart === "undefined") return null;
        return new window.Chart(canvas, config);
      };

      // ── Hero ──────────────────────────────────────────────────────────
      document.getElementById("hero-text").textContent =
        "Tracking every swing, every miss, and every small win with a Garmin R10 and way too much Python. The handicap isn't improving as fast as the analytics.";
      document.getElementById("generated-at").textContent =
        `Updated ${new Date(data.generated_at).toLocaleString()}`;
      const heroStats = document.getElementById("hero-stats");
      [
        ["Sessions", data.overview.total_sessions],
        ["Shots tracked", data.overview.total_shots],
        ["Clubs", data.overview.tracked_clubs],
        ["Avg consistency", data.overview.avg_consistency_score != null ? data.overview.avg_consistency_score.toFixed(1) : "—"],
      ].forEach(([label, val]) => {
        const div = document.createElement("div");
        const valEl = document.createElement("div");
        valEl.className = "hero-stat-val";
        valEl.textContent = val;
        const lblEl = document.createElement("div");
        lblEl.className = "hero-stat-lbl";
        lblEl.textContent = label;
        div.appendChild(valEl);
        div.appendChild(lblEl);
        heroStats.appendChild(div);
      });

      // ── Overview stats ────────────────────────────────────────────────
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

      // ── Next session focus ────────────────────────────────────────────
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
            <div class="small">${item.focus_area} &bull; ${item.evidence}</div>
          `;
          nextSessionList.appendChild(card);
        });
      }

      // ── Session trend chart ───────────────────────────────────────────
      const hasRatingData = data.charts.timeline.session_rating && data.charts.timeline.session_rating.some((v) => v != null);
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
            ...(hasRatingData ? [{
              label: "Session rating (0–100)",
              data: data.charts.timeline.session_rating,
              borderColor: "#ffb454",
              backgroundColor: "rgba(255, 180, 84, 0.12)",
              borderDash: [5, 3],
              tension: 0.3,
              yAxisID: "y2",
              pointRadius: 5,
              pointBackgroundColor: "#ffb454",
            }] : []),
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: { mode: "index", intersect: false },
          scales: {
            y: { beginAtZero: false, position: "left" },
            y1: { beginAtZero: false, position: "right", grid: { drawOnChartArea: false } },
            ...(hasRatingData ? {
              y2: {
                beginAtZero: true,
                min: 0,
                max: 100,
                position: "right",
                grid: { drawOnChartArea: false },
                ticks: { callback: (v) => `${v}` },
                title: { display: true, text: "Rating" },
              },
            } : {}),
          },
        },
      });

      // ── Smash headroom chart (actual vs personal potential) ───────────
      const smashLabels = data.clubs.map((c) => c.club_label);
      const smashActual = data.clubs.map((c) => (c.avg_smash_factor != null ? parseFloat(c.avg_smash_factor.toFixed(3)) : null));
      const smashPotential = data.clubs.map((c) => (c.potential_smash_factor != null ? parseFloat(c.potential_smash_factor.toFixed(3)) : null));
      createChart("smashHeadroomChart", {
        type: "bar",
        data: {
          labels: smashLabels,
          datasets: [
            {
              type: "bar",
              label: "Avg smash factor",
              data: smashActual,
              backgroundColor: "rgba(87, 181, 255, 0.65)",
              borderColor: "#57b5ff",
              borderWidth: 1,
              order: 2,
            },
            {
              type: "line",
              label: "Personal ceiling (90th %ile)",
              data: smashPotential,
              borderColor: "#5fd18b",
              backgroundColor: "transparent",
              borderWidth: 2,
              pointRadius: 5,
              pointBackgroundColor: "#5fd18b",
              tension: 0,
              order: 1,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: { mode: "index", intersect: false },
          scales: {
            y: {
              beginAtZero: false,
              min: 0.9,
              title: { display: true, text: "Smash factor" },
            },
          },
          plugins: { legend: { position: "top" } },
        },
      });

      // ── Club carry and consistency chart ──────────────────────────────
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

      // ── Bag gapping chart (floating bars: avg ± stddev) ───────────────
      const sortedClubs = [...data.clubs]
        .filter((c) => c.avg_carry_distance != null)
        .sort((a, b) => a.avg_carry_distance - b.avg_carry_distance);
      const bagLabels = sortedClubs.map((c) => c.club_label);
      const bagFloatData = sortedClubs.map((c) => {
        const avg = c.avg_carry_distance;
        const std = c.carry_stddev || 0;
        return [Math.max(0, avg - std), avg + std];
      });
      const bagAvgData = sortedClubs.map((c) => c.avg_carry_distance);
      const bagIsBunched = sortedClubs.map((c, i) => {
        const prev = i > 0 ? sortedClubs[i - 1] : null;
        const next = i < sortedClubs.length - 1 ? sortedClubs[i + 1] : null;
        return (prev && c.avg_carry_distance - prev.avg_carry_distance < 7) ||
               (next && next.avg_carry_distance - c.avg_carry_distance < 7);
      });
      createChart("bagGapChart", {
        type: "bar",
        data: {
          labels: bagLabels,
          datasets: [
            {
              type: "bar",
              label: "Carry range (avg \u00b1 1 SD)",
              data: bagFloatData,
              backgroundColor: bagIsBunched.map((b) => b ? "rgba(255, 180, 84, 0.45)" : "rgba(87, 181, 255, 0.35)"),
              borderColor: bagIsBunched.map((b) => b ? "#ffb454" : "#57b5ff"),
              borderWidth: 1.5,
              borderSkipped: false,
              order: 2,
            },
            {
              type: "line",
              label: "Avg carry",
              data: bagAvgData,
              borderColor: "rgba(255, 255, 255, 0.5)",
              backgroundColor: "transparent",
              borderWidth: 1.5,
              pointRadius: 4,
              pointBackgroundColor: "rgba(255, 255, 255, 0.85)",
              tension: 0,
              order: 1,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: { mode: "index", intersect: false },
          plugins: {
            legend: { position: "top" },
            tooltip: {
              callbacks: {
                label: (ctx) => {
                  if (ctx.datasetIndex === 0) {
                    const raw = ctx.raw;
                    if (Array.isArray(raw)) return `Range: ${raw[0].toFixed(0)}\u2013${raw[1].toFixed(0)} yds`;
                  }
                  return `Avg: ${ctx.parsed.y.toFixed(1)} yds`;
                },
              },
            },
          },
          scales: {
            y: { beginAtZero: false, title: { display: true, text: "Carry distance (yds)" } },
          },
        },
      });

      // ── Dispersion map ────────────────────────────────────────────────
      const dispersionByClub = {};
      data.charts.dispersion.forEach((point) => {
        if (!dispersionByClub[point.club]) dispersionByClub[point.club] = [];
        dispersionByClub[point.club].push(point);
      });
      const dispersionDatasets = Object.entries(dispersionByClub).map(([club, points], index) => ({
        label: club,
        data: points.map((p) => ({ x: p.x, y: p.y })),
        pointRadius: points.map((p) => (p.outlier ? 5 : 4)),
        pointStyle: points.map((p) => (p.outlier ? "triangle" : "circle")),
        pointHoverRadius: 7,
        borderWidth: 0,
        backgroundColor: points.map((p) =>
          p.outlier
            ? COLORS[index % COLORS.length] + "88"
            : COLORS[index % COLORS.length]
        ),
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

      // Club toggle buttons
      const togglesContainer = document.getElementById("dispersionToggles");
      if (togglesContainer && dispersionChart) {
        Object.keys(dispersionByClub).forEach((club, index) => {
          const btn = document.createElement("button");
          btn.className = "club-toggle";
          btn.textContent = club;
          btn.style.borderColor = COLORS[index % COLORS.length];
          btn.addEventListener("click", () => {
            const meta = dispersionChart.getDatasetMeta(index);
            meta.hidden = !meta.hidden;
            btn.classList.toggle("off", meta.hidden);
            dispersionChart.update();
          });
          togglesContainer.appendChild(btn);
        });
      }

      // ── Miss direction trend chart ────────────────────────────────────
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
              ticks: { callback: (v) => (v > 0 ? `+${v} R` : v < 0 ? `${v} L` : "0") },
            },
          },
        },
      });

      // ── Consistency heatmap ───────────────────────────────────────────
      const heatmapContainer = document.getElementById("consistency-heatmap");
      if (heatmapContainer && data.sessions.length) {
        const sessionLabels = data.sessions.map((s) =>
          s.session_timestamp
            ? new Date(s.session_timestamp).toLocaleDateString(undefined, { month: "short", day: "numeric" })
            : s.source_file.slice(0, 10)
        );
        const allClubLabels = [...new Set(
          data.sessions.flatMap((s) => (s.club_summaries || []).map((c) => c.club_label))
        )].sort();
        const scoreMap = {};
        data.sessions.forEach((session, sIdx) => {
          (session.club_summaries || []).forEach((club) => {
            if (!scoreMap[club.club_label]) scoreMap[club.club_label] = {};
            scoreMap[club.club_label][sIdx] = club.consistency_score;
          });
        });
        const scoreColor = (score) => {
          if (score == null) return null;
          if (score >= 75) return { bg: "rgba(95, 209, 139, 0.28)", text: "#5fd18b" };
          if (score >= 50) return { bg: "rgba(255, 180, 84, 0.28)", text: "#ffb454" };
          return { bg: "rgba(255, 123, 114, 0.28)", text: "#ff7b72" };
        };
        const table = document.createElement("table");
        table.className = "heatmap-table";
        const thead = table.createTHead();
        const headerRow = thead.insertRow();
        const clubTh = document.createElement("th");
        clubTh.textContent = "Club";
        clubTh.style.textAlign = "left";
        headerRow.appendChild(clubTh);
        sessionLabels.forEach((label) => {
          const th = document.createElement("th");
          th.textContent = label;
          headerRow.appendChild(th);
        });
        const tbody = table.createTBody();
        allClubLabels.forEach((clubLabel) => {
          const row = tbody.insertRow();
          const nameCell = row.insertCell();
          nameCell.className = "heatmap-club";
          nameCell.textContent = clubLabel;
          data.sessions.forEach((_, sIdx) => {
            const score = scoreMap[clubLabel]?.[sIdx];
            const cell = row.insertCell();
            if (score != null) {
              const c = scoreColor(score);
              cell.className = "heatmap-cell";
              cell.style.backgroundColor = c.bg;
              cell.style.color = c.text;
              cell.textContent = score.toFixed(0);
            } else {
              cell.className = "heatmap-empty";
              cell.textContent = "\u2014";
            }
          });
        });
        heatmapContainer.appendChild(table);
      }

      // ── Club summary table ────────────────────────────────────────────
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

      // ── Session cards (date + structured stats) ───────────────────────
      const sessions = document.getElementById("sessions");
      data.sessions.forEach((session) => {
        const card = document.createElement("div");
        card.className = "session-card";
        const dateStr = session.session_timestamp
          ? new Date(session.session_timestamp).toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" })
          : session.source_file;

        const ratingVal = session.session_rating;
        const ratingTrend = session.session_rating_trend;
        const ratingColor = ratingVal == null ? "var(--muted)"
          : ratingVal >= 70 ? "var(--good)"
          : ratingVal >= 50 ? "var(--warn)"
          : "var(--bad)";
        const ratingDisplay = ratingVal == null
          ? `<span style="color:var(--muted)">—</span>`
          : `<span class="session-rating-value" style="color:${ratingColor}">${ratingVal.toFixed(0)}</span>`;
        let trendHtml = "";
        if (ratingTrend != null) {
          if (ratingTrend > 0.05) {
            trendHtml = `<span class="session-rating-trend delta-pos">&#9650; ${ratingTrend.toFixed(1)}</span>`;
          } else if (ratingTrend < -0.05) {
            trendHtml = `<span class="session-rating-trend delta-neg">&#9660; ${Math.abs(ratingTrend).toFixed(1)}</span>`;
          } else {
            trendHtml = `<span class="session-rating-trend delta-neutral">&rarr;</span>`;
          }
        }

        card.innerHTML = `
          <div class="session-date">${dateStr}</div>
          <div class="session-rating-row">
            <span class="session-rating-label">Rating</span>
            ${ratingDisplay}
            ${trendHtml}
          </div>
          <div class="session-stats">
            <div class="session-stat">
              <span class="session-stat-value">${session.shot_count}</span>
              <span class="session-stat-label">Shots</span>
            </div>
            <div class="session-stat">
              <span class="session-stat-value">${session.club_count}</span>
              <span class="session-stat-label">Clubs</span>
            </div>
            <div class="session-stat">
              <span class="session-stat-value">${number(session.avg_carry_distance, 1)}</span>
              <span class="session-stat-label">Avg carry</span>
            </div>
            <div class="session-stat">
              <span class="session-stat-value">${number(session.avg_smash_factor, 2)}</span>
              <span class="session-stat-label">Smash</span>
            </div>
            <div class="session-stat">
              <span class="session-stat-value">${number(session.avg_offline_distance, 1)}</span>
              <span class="session-stat-label">Avg offline</span>
            </div>
            <div class="session-stat">
              <span class="session-stat-value">${number(session.outlier_rate, 0, "%")}</span>
              <span class="session-stat-label">Outliers</span>
            </div>
          </div>
        `;
        sessions.appendChild(card);
      });

      // ── Session deltas ────────────────────────────────────────────────
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

      // ── Recommendations ───────────────────────────────────────────────
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
            <div class="small">${item.focus_area} &bull; ${item.evidence}</div>
          `;
          recommendations.appendChild(div);
        });
      }

      if (!sessionTrendChart || !clubBarChart || !dispersionChart || !missDirectionChart) {
        showChartError("Some charts could not be initialized. Refresh after the page assets finish loading.");
      }

      // ── Tab switching ─────────────────────────────────────────────────
      const tabBtns = document.querySelectorAll(".tab-btn");
      const tabPanels = document.querySelectorAll(".tab-panel");
      tabBtns.forEach((btn) => {
        btn.addEventListener("click", () => {
          tabBtns.forEach((b) => { b.classList.remove("active"); b.setAttribute("aria-selected", "false"); });
          tabPanels.forEach((p) => p.classList.remove("active"));
          btn.classList.add("active");
          btn.setAttribute("aria-selected", "true");
          document.getElementById(btn.getAttribute("aria-controls")).classList.add("active");
        });
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
