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
        --warn: #1E340A;
        --good: #1B7114;
        --bad: #1E340A;
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
      .site-links {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin: 8px 0 18px;
      }
      .site-link {
        text-decoration: none;
        color: var(--accent2);
        border: 1px solid var(--border);
        border-radius: 999px;
        padding: 6px 12px;
        font-size: 0.84rem;
        font-weight: 700;
        background: #fff;
      }
      .site-link:hover {
        border-color: var(--accent);
        color: var(--accent);
      }
      /* ── Grid & panels ──────────────────────────────── */
      .grid { display: grid; gap: 16px; }
      .stats {
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        margin-bottom: 24px;
      }
      .panel {
        background: var(--panel);
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
        grid-template-columns: 1fr;
        margin-bottom: 28px;
      }
      .chart-wrap { display: flex; flex-direction: column; }
      .chart-canvas { position: relative; height: 380px; width: 100%; }
      .chart-canvas.tall { height: 460px; }
      .chart-canvas canvas { width: 100% !important; height: 100% !important; }
      .forecast-callout {
        margin-top: 10px;
        padding: 10px 13px;
        background: var(--accent-soft);
        border-left: 3px solid var(--accent);
        border-radius: 6px;
        font-size: 0.83rem;
        color: var(--text);
      }
      .forecast-callout strong { color: var(--accent2); }

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
      .sessions-list { display: flex; flex-direction: column; gap: 0; }
      .session-row {
        display: grid;
        grid-template-columns: 1fr auto auto auto auto auto auto;
        align-items: center;
        gap: 0 16px;
        padding: 12px 4px;
        border-bottom: 1px solid var(--border);
      }
      .session-row:last-child { border-bottom: none; }
      .session-row:hover { background: rgba(64,129,20,0.04); border-radius: 8px; }
      .session-row-date { font-weight: 700; font-size: 0.95rem; color: var(--text); }
      .session-row-rating { display: flex; align-items: baseline; gap: 5px; }
      .session-row-rating-val { font-size: 1.3rem; font-weight: 800; line-height: 1; }
      .session-row-stat { text-align: right; }
      .session-row-stat-val { font-size: 0.95rem; font-weight: 700; color: var(--text); display: block; }
      .session-row-stat-lbl { font-size: 0.68rem; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; }
      .session-pagination {
        display: flex; align-items: center; justify-content: space-between;
        margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--border);
      }
      .session-pagination button {
        background: none; border: 1.5px solid var(--border); border-radius: 8px;
        padding: 5px 14px; font-size: 0.85rem; font-weight: 600; color: var(--muted);
        cursor: pointer; font-family: inherit; transition: color 0.15s, border-color 0.15s;
      }
      .session-pagination button:hover:not(:disabled) { color: var(--accent); border-color: var(--accent); }
      .session-pagination button:disabled { opacity: 0.35; cursor: default; }
      .session-pagination-info { font-size: 0.82rem; color: var(--muted); }
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
      .recommendation { padding: 14px 16px; border-radius: 12px; margin-bottom: 2px; }
      .rec-high { border-left: 4px solid #1E340A; background: rgba(30,52,10,0.07); }
      .rec-med  { border-left: 4px solid #408114; background: rgba(64,129,20,0.08); }
      .rec-low  { border-left: 4px solid #4D6E24; background: rgba(77,110,36,0.07); }
      .confidence-low { opacity: 0.72; }
      .confidence-high { box-shadow: 0 0 0 1px rgba(27,113,20,0.35) inset; }
      .recommendation-header {
        display: flex; justify-content: space-between; gap: 12px;
        align-items: baseline; margin-bottom: 4px;
      }
      .severity-badge {
        display: inline-block; padding: 2px 9px; border-radius: 999px;
        font-size: 0.73rem; font-weight: 700; color: #fff; white-space: nowrap;
      }
      .badge-high { background: #1E340A; }
      .badge-med  { background: #408114; }
      .badge-low  { background: #4D6E24; }
      .confidence {
        margin-top: 6px;
        font-size: 0.78rem;
        color: var(--muted);
      }
      .confidence-pill {
        display: inline-block;
        margin-top: 6px;
        padding: 2px 8px;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 700;
        color: #fff;
        background: #4D6E24;
      }
      .confidence-pill.high { background: #1B7114; }
      .confidence-pill.medium { background: #4D6E24; }
      .confidence-pill.low { background: #6b7280; }
      .rank-why {
        margin-top: 8px;
        font-size: 0.78rem;
        color: var(--muted);
      }
      .rank-why summary {
        cursor: pointer;
        font-weight: 700;
        color: var(--accent2);
      }

      /* ── Club detail panel ──────────────────────────── */
      .club-detail { display: none; }
      .club-detail.active { display: block; }
      .back-btn {
        display: inline-flex; align-items: center; gap: 6px;
        background: none; border: 1.5px solid var(--border); border-radius: 8px;
        padding: 7px 14px; font-size: 0.88rem; font-weight: 600; color: var(--muted);
        cursor: pointer; margin-bottom: 20px; font-family: inherit;
        transition: color 0.15s, border-color 0.15s;
      }
      .back-btn:hover { color: var(--accent); border-color: var(--accent); }
      .club-detail-header { display: flex; flex-wrap: wrap; align-items: baseline; gap: 12px; margin-bottom: 16px; }
      .club-detail-name {
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 1.9rem; font-weight: 700; color: var(--text);
      }
      .velocity-badge { display: inline-block; padding: 4px 11px; border-radius: 999px; font-size: 0.78rem; font-weight: 700; color: #fff; }
      .vel-improved { background: #1B7114; }
      .vel-steady   { background: #4D6E24; }
      .vel-needed   { background: #1E340A; }
      .club-stat-strip { display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 10px; margin-bottom: 22px; }
      .club-stat-card { background: var(--bg); border: 1px solid var(--border); border-radius: 10px; padding: 11px 13px; }
      .club-stat-card .stat-value { font-size: 1.35rem; }
      .gap-bar-wrap { margin-top: 6px; height: 6px; background: var(--border); border-radius: 3px; }
      .gap-bar { height: 6px; border-radius: 3px; background: var(--accent); }
      .club-link-btn { background: none; border: none; color: var(--accent2); font-weight: 600; font-size: 0.95rem; cursor: pointer; text-decoration: underline; text-underline-offset: 3px; font-family: inherit; padding: 0; }
      .club-link-btn:hover { color: var(--accent); }
      .club-nav-pill { display: inline-flex; align-items: center; gap: 4px; background: var(--accent-soft); border: 1.5px solid var(--accent); border-radius: 999px; padding: 6px 16px; font-size: 0.88rem; font-weight: 600; color: var(--accent2); cursor: pointer; font-family: inherit; transition: background 0.15s, color 0.15s; }
      .club-nav-pill:hover { background: var(--accent); color: #fff; }
      .path-lab-grid { display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); }
      .path-panel { display: flex; flex-direction: column; gap: 12px; }
      .path-rail { position: relative; height: 88px; border-radius: 16px; border: 1px solid var(--border); background: linear-gradient(90deg, rgba(30,52,10,0.05) 0%, rgba(255,255,255,0.92) 50%, rgba(64,129,20,0.06) 100%); overflow: hidden; }
      .path-rail::before { content: ""; position: absolute; top: 0; bottom: 0; left: 50%; width: 2px; background: rgba(30,52,10,0.14); }
      .path-marker { position: absolute; top: 18px; transform: translateX(-50%); display: flex; flex-direction: column; align-items: center; gap: 6px; min-width: 92px; }
      .path-marker-dot { width: 16px; height: 16px; border-radius: 999px; border: 2px solid #fff; box-shadow: 0 2px 8px rgba(30,52,10,0.14); }
      .path-marker-label { background: rgba(255,255,255,0.92); border: 1px solid var(--border); border-radius: 999px; padding: 2px 8px; font-size: 0.76rem; font-weight: 700; color: var(--text); }
      .path-metrics { display: grid; gap: 8px; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); }
      .path-metric { background: rgba(242,242,240,0.86); border: 1px solid var(--border); border-radius: 12px; padding: 10px 12px; }
      .path-metric .value { font-size: 1.2rem; font-weight: 800; color: var(--text); }
      .path-metric .label { font-size: 0.72rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; font-weight: 700; }
      .site-footer {
        margin-top: 24px;
        padding-top: 14px;
        border-top: 1px solid var(--border);
        text-align: right;
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
        <div style="display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));">
            <div class="hero-eyebrow">Jerry Gamblin &bull; Range Performance Lab</div>
            <a class="gh-link" href="https://github.com/jgamblin/golf" target="_blank" rel="noopener">
              GitHub
            </a>
          </div>
          <h1 class="hero-title">Bad at golf.<br><em>Great</em> at data.</h1>
          <div class="hero-divider"></div>
          <p id="hero-text"></p>
        </div>
      </section>

      <nav class="site-links" aria-label="Site sections">
        <a class="site-link" href="./clubs.html">Club Lab</a>
        <a class="site-link" href="./sessions.html">Session Replay</a>
        <a class="site-link" href="./gapping.html">Gapping</a>
        <a class="site-link" href="./coaching.html">Coaching</a>
        <a class="site-link" href="./data-quality.html">Data Quality</a>
      </nav>

      <!-- ── Overview stats ─────────────────────────────── -->
      <section class="grid stats" id="overview"></section>

      <!-- ── Dashboard content ───────────────────────── -->

      <!-- ── Charts ────────────────────────────────────── -->
      <section class="grid charts">

        <div class="panel chart-wrap">
          <h2>Session trend</h2>
          <div class="chart-canvas">
            <canvas id="sessionTrend"></canvas>
          </div>
          <div class="forecast-callout" id="trend-forecast-callout" style="display:none;"></div>
        </div>

        <div class="panel chart-wrap">
          <h2>Miss direction trend</h2>
          <p style="margin:0 0 8px;font-size:0.88rem;color:var(--muted)">Positive = right miss &nbsp;|&nbsp; Negative = left miss</p>
          <div class="chart-canvas">
            <canvas id="missDirectionChart"></canvas>
          </div>
        </div>

      </section>
      <!-- ── Tables ────────────────────────────────────── -->
      <section class="grid tables">
        <div class="panel">
          <h2>Sessions</h2>
          <div class="sessions-list" id="sessions"></div>
          <div class="session-pagination" id="sessions-pagination" style="display:none;">
            <button id="sessions-prev">&#8592; Prev</button>
            <span class="session-pagination-info" id="sessions-page-info"></span>
            <button id="sessions-next">Next &#8594;</button>
          </div>
        </div>
      </section>

      <!-- ── end Dashboard content ──────────────────── -->

      <footer class="site-footer">
        <p class="small" id="generated-at"></p>
      </footer>

    </main>

    <script src="./site-data.js"></script>
    <script>
      const data = window.GOLF_SITE_DATA;
      const chartGrid = document.querySelector(".charts");
      const COLORS = ["#408114","#1B7114","#4D6E24","#1E340A","#6b7280","#0369a1","#7c3aed","#0d9488"];

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


      // ── Session trend chart ───────────────────────────────────────────
      const sessionTrendChart = (() => {
        const fc = (data.forecasts || {}).per_club || {};
        const clubsWithFc = Object.entries(fc).filter(([, v]) => v.carry);
        const actualLabels = data.charts.timeline.labels;
        const allLabels = clubsWithFc.length ? [...actualLabels, "+1", "+2", "+3"] : actualLabels;
        const nulls3 = clubsWithFc.length ? [null, null, null] : [];

        const datasets = [
          {
            label: "Avg carry (yds)",
            data: [...data.charts.timeline.avg_carry_distance, ...nulls3],
            borderColor: "#408114",
            backgroundColor: "rgba(64,129,20,0.12)",
            tension: 0.3,
            yAxisID: "y",
          },
          {
            label: "Avg smash",
            data: [...data.charts.timeline.avg_smash_factor, ...nulls3],
            borderColor: "#1B7114",
            backgroundColor: "rgba(27,113,20,0.10)",
            tension: 0.3,
            yAxisID: "y1",
          },
        ];

        if (clubsWithFc.length) {
          const [, firstClubFc] = clubsWithFc[0];
          const carry = firstClubFc.carry;
          const nullPad = actualLabels.map(() => null);
          datasets.push({
            label: "Carry forecast",
            data: [...nullPad, ...carry.predictions],
            borderColor: "rgba(64,129,20,0.6)",
            backgroundColor: "transparent",
            borderDash: [6, 4],
            borderWidth: 2,
            pointRadius: [...nullPad.map(() => 0), 3, 3, 3],
            tension: 0,
            yAxisID: "y",
          });
          datasets.push({
            label: "_fc_hi",
            data: [...nullPad, ...carry.confidence_band.map((b) => b[1])],
            borderColor: "transparent",
            backgroundColor: "rgba(64,129,20,0.07)",
            fill: "+1",
            pointRadius: 0,
            tension: 0,
            yAxisID: "y",
          });
          datasets.push({
            label: "_fc_lo",
            data: [...nullPad, ...carry.confidence_band.map((b) => b[0])],
            borderColor: "transparent",
            backgroundColor: "transparent",
            fill: false,
            pointRadius: 0,
            tension: 0,
            yAxisID: "y",
          });

          const callout = document.getElementById("trend-forecast-callout");
          callout.style.display = "block";
          const dir = carry.slope >= 0 ? "+" : "";
          const strong = document.createElement("strong");
          strong.textContent = `Forecast (${clubsWithFc[0][0]}): `;
          callout.appendChild(strong);
          callout.appendChild(document.createTextNode(
            `trending ${dir}${carry.slope.toFixed(1)} yds/session — projected ${carry.predictions[2]} yds in 3 sessions`
          ));
        }

        return createChart("sessionTrend", {
          type: "line",
          data: { labels: allLabels, datasets },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: "index", intersect: false },
            plugins: {
              legend: { labels: { filter: (item) => !item.text.startsWith("_") } },
            },
            scales: {
              y: { beginAtZero: false, position: "left" },
              y1: { beginAtZero: false, position: "right", grid: { drawOnChartArea: false } },
            },
          },
        });
      })();

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
                v === null ? "transparent" : v > 0 ? "rgba(30, 52, 10, 0.7)" : "rgba(64, 129, 20, 0.7)"
              ),
              borderColor: data.charts.timeline.miss_direction.map((v) =>
                v === null ? "transparent" : v > 0 ? "#1E340A" : "#408114"
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

      // ── Sessions list (paginated, 5 per page, newest first) ──────────────
      (() => {
        const PAGE_SIZE = 5;
        const allSessions = [...data.sessions].reverse();
        let page = 0;
        const container = document.getElementById("sessions");
        const pagination = document.getElementById("sessions-pagination");
        const pageInfo = document.getElementById("sessions-page-info");
        const prevBtn = document.getElementById("sessions-prev");
        const nextBtn = document.getElementById("sessions-next");

        function statCell(val, lbl) {
          const el = document.createElement("div");
          el.className = "session-row-stat";
          const v = document.createElement("span");
          v.className = "session-row-stat-val";
          v.textContent = val;
          const l = document.createElement("span");
          l.className = "session-row-stat-lbl";
          l.textContent = lbl;
          el.appendChild(v);
          el.appendChild(l);
          return el;
        }

        function renderPage() {
          container.innerHTML = "";
          const start = page * PAGE_SIZE;
          const slice = allSessions.slice(start, start + PAGE_SIZE);
          slice.forEach((session) => {
            const dateStr = session.session_timestamp
              ? new Date(session.session_timestamp).toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" })
              : session.source_file;

            const row = document.createElement("div");
            row.className = "session-row";

            const datEl = document.createElement("div");
            datEl.className = "session-row-date";
            datEl.textContent = dateStr;

            row.appendChild(datEl);
            row.appendChild(statCell(session.shot_count, "Shots"));
            row.appendChild(statCell(session.club_count, "Clubs"));
            row.appendChild(statCell(number(session.avg_carry_distance, 1), "Carry"));
            row.appendChild(statCell(number(session.avg_smash_factor, 2), "Smash"));
            row.appendChild(statCell(number(session.avg_offline_distance, 1), "Offline"));
            row.appendChild(statCell(number(session.outlier_rate, 0, "%"), "Outliers"));
            container.appendChild(row);
          });

          const totalPages = Math.ceil(allSessions.length / PAGE_SIZE);
          if (totalPages > 1) {
            pagination.style.display = "flex";
            pageInfo.textContent = `${start + 1}–${Math.min(start + PAGE_SIZE, allSessions.length)} of ${allSessions.length}`;
            prevBtn.disabled = page === 0;
            nextBtn.disabled = page >= totalPages - 1;
          }
        }

        prevBtn.addEventListener("click", () => { page--; renderPage(); });
        nextBtn.addEventListener("click", () => { page++; renderPage(); });
        renderPage();
      })();


      if (!sessionTrendChart || !missDirectionChart) {
        showChartError("Some charts could not be initialized. Refresh after the page assets finish loading.");
      }

      // No tab switching needed — coaching moved to coaching.html

    </script>
  </body>
</html>
"""


def _render_subpage(title: str, heading: str, intro: str, content_html: str) -> str:
    return f"""<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
    <title>{title}</title>
    <script src=\"https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js\"></script>
    <script src=\"./site-data.js\"></script>
    <script>
      window.data = window.GOLF_SITE_DATA;
      window.fmt = (v, d = 1, s = "") =>
        v === null || v === undefined || Number.isNaN(v) ? "—" : `${{Number(v).toFixed(d)}}${{s}}`;
    </script>
    <style>
      :root {{
        --bg: #F2F2F0;
        --panel: #ffffff;
        --text: #1E340A;
        --muted: #4D6E24;
        --accent: #408114;
        --border: rgba(30, 52, 10, 0.12);
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif;
        background: linear-gradient(180deg, #F2F2F0 0%, #ebebea 100%);
        color: var(--text);
      }}
      main {{ max-width: 1100px; margin: 0 auto; padding: 36px 18px 56px; }}
      h1, h2 {{ margin: 0 0 12px; }}
      p {{ color: var(--muted); line-height: 1.5; }}
      .panel {{
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 18px;
        box-shadow: 0 2px 16px rgba(30, 52, 10, 0.07);
        margin-bottom: 16px;
      }}
      .chart-canvas {{
        position: relative;
        height: 260px;
        width: 100%;
      }}
      .chart-canvas.small {{
        height: 220px;
      }}
      .chart-canvas canvas {{
        width: 100% !important;
        height: 100% !important;
      }}
      .nav {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; }}
      .nav a {{
        text-decoration: none;
        border: 1px solid var(--border);
        color: var(--accent);
        padding: 7px 12px;
        border-radius: 999px;
        font-weight: 600;
        font-size: 0.9rem;
      }}
      .heatmap-wrap {{ overflow-x: auto; }}
      .heatmap-table {{ border-collapse: separate; border-spacing: 4px; font-size: 0.88rem; }}
      .heatmap-table th {{ color: var(--muted); font-weight: 600; padding: 4px 10px; white-space: nowrap; text-align: center; }}
      .heatmap-table th:first-child {{ text-align: left; }}
      .heatmap-cell {{ padding: 8px 12px; border-radius: 8px; text-align: center; font-weight: 700; font-size: 0.85rem; min-width: 56px; }}
      .heatmap-club {{ padding: 8px 12px 8px 0; font-weight: 600; font-size: 0.88rem; white-space: nowrap; }}
      .heatmap-empty {{ padding: 8px 12px; border-radius: 8px; text-align: center; color: var(--muted); background: rgba(255,255,255,0.03); min-width: 56px; }}
      .club-link-btn {{
        background: none;
        border: none;
        color: var(--accent);
        font: inherit;
        font-weight: 700;
        cursor: pointer;
        padding: 0;
        text-decoration: underline;
        text-underline-offset: 3px;
      }}
      table {{ width: 100%; border-collapse: collapse; font-size: 0.94rem; }}
      th, td {{ padding: 10px 8px; border-bottom: 1px solid var(--border); text-align: left; }}
      th {{ color: var(--muted); font-weight: 700; }}
      .small {{ font-size: 0.84rem; color: var(--muted); }}
      @media (max-width: 700px) {{
        main {{ padding: 26px 12px 44px; }}
      }}
    </style>
  </head>
  <body>
    <main>
      <nav class=\"nav\">
        <a href=\"./index.html\">Overview</a>
        <a href=\"./clubs.html\">Club Lab</a>
        <a href=\"./sessions.html\">Session Replay</a>
        <a href=\"./gapping.html\">Gapping</a>
        <a href=\"./coaching.html\">Coaching</a>
        <a href=\"./data-quality.html\">Data Quality</a>
      </nav>
      <section class=\"panel\">
        <h1>{heading}</h1>
        <p>{intro}</p>
      </section>
      {content_html}
    </main>
  </body>
</html>
"""


def render_clubs_page() -> str:
    body = """
      <section class=\"panel\">
        <h2>Club Overview</h2>
        <p class=\"small\">Club-specific scoring, strike quality, and dispersion now live here instead of the landing page.</p>
        <div style=\"display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));\">
          <div class=\"chart-canvas small\"><canvas id=\"clubBarsLab\"></canvas></div>
          <div class=\"chart-canvas small\"><canvas id=\"smashHeadroomLab\"></canvas></div>
          <div class=\"chart-canvas small\"><canvas id=\"offlineSummaryLab\"></canvas></div>
        </div>
      </section>
      <section class=\"panel\">
        <h2>Club Summary</h2>
        <p class=\"small\">Choose a club to open a deeper trend and dispersion view without returning to the landing page.</p>
        <div style=\"overflow-x:auto;\"><table>
          <thead><tr><th>Club</th><th>Shots</th><th>Avg carry</th><th>Avg smash</th><th>Avg offline</th><th>Consistency</th><th>Outliers</th></tr></thead>
          <tbody id=\"club-summary-body-lab\"></tbody>
        </table></div>
      </section>
      <section class=\"panel\">
        <h2>Spin And Tempo At A Glance</h2>
        <div style=\"display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));\">
          <div class=\"chart-canvas small\"><canvas id=\"spinChart\"></canvas></div>
          <div class=\"chart-canvas small\"><canvas id=\"tempoChart\"></canvas></div>
        </div>
      </section>
      <section class=\"panel\">
        <h2>Spin And Launch Profile</h2>
        <div style=\"overflow-x:auto;\"><table>
          <thead><tr><th>Club</th><th>Spin avg</th><th>Spin SD</th><th>Axis avg</th><th>Launch dir avg</th><th>Apex avg</th></tr></thead>
          <tbody id=\"spin-body\"></tbody>
        </table></div>
      </section>
      <section class=\"panel\">
        <h2>Tempo And Sequencing</h2>
        <div style=\"overflow-x:auto;\"><table>
          <thead><tr><th>Club</th><th>Backswing</th><th>Downswing</th><th>Swing tempo</th><th>Tempo baseline</th><th>Tempo error</th><th>Basis</th></tr></thead>
          <tbody id=\"tempo-body\"></tbody>
        </table></div>
      </section>
      <section class=\"panel\">
        <h2>Consistency By Session</h2>
        <div class=\"heatmap-wrap\" id=\"consistency-heatmap-club-lab\"></div>
      </section>
      <section class=\"panel\">
        <h2>Latest Vs Previous Session</h2>
        <p class=\"small\" id=\"delta-caption-lab\"></p>
        <div style=\"overflow-x:auto;\"><table>
          <thead><tr><th>Club</th><th>Shots</th><th>Carry delta</th><th>Smash delta</th><th>Offline delta</th></tr></thead>
          <tbody id=\"session-delta-body-lab\"></tbody>
        </table></div>
      </section>
      <section class=\"panel\">
        <div style=\"display:flex;justify-content:space-between;gap:12px;align-items:flex-start;flex-wrap:wrap;margin-bottom:14px;\">
          <div>
            <div class=\"small\" style=\"text-transform:uppercase;letter-spacing:0.08em;font-weight:700;\">Club drilldown</div>
            <h2 id=\"club-detail-name-lab\" style=\"margin-top:6px;\">Select a club</h2>
          </div>
          <span id=\"club-velocity-badge-lab\" class=\"small\" style=\"padding:6px 10px;border-radius:999px;background:rgba(64,129,20,0.1);font-weight:700;color:#1B7114;\">Waiting for selection</span>
        </div>
        <div class=\"small\" style=\"margin-bottom:10px;\">Select a club here:</div>
        <div id=\"club-nav-pills-lab\" style=\"display:flex;flex-wrap:wrap;gap:8px;margin:0 0 12px;\"></div>
        <div id=\"club-stat-strip-lab\" style=\"display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px;margin-bottom:16px;\"></div>
        <div class=\"path-lab-grid\" style=\"margin-bottom:16px;\">
          <div class=\"path-panel\">
            <div class=\"small\" style=\"text-transform:uppercase;letter-spacing:0.08em;font-weight:700;\">Path / Face Snapshot</div>
            <div class=\"path-rail\" id=\"club-path-rail-lab\">
              <div class=\"path-marker\" id=\"club-path-marker-lab\" style=\"left:50%;\">
                <div class=\"path-marker-dot\" style=\"background:#408114;\"></div>
                <div class=\"path-marker-label\">Club path</div>
              </div>
              <div class=\"path-marker\" id=\"club-face-marker-lab\" style=\"left:50%; top: 46px;\">
                <div class=\"path-marker-dot\" style=\"background:#1B7114;\"></div>
                <div class=\"path-marker-label\">Face to path</div>
              </div>
            </div>
            <div class=\"path-metrics\" id=\"club-path-metrics-lab\"></div>
            <p class=\"small\" style=\"margin:0;\">Positive values move right; negative values move left. The cloud shows the shot-by-shot relationship between club path and face-to-path.</p>
          </div>
          <div>
            <div class=\"small\" style=\"text-transform:uppercase;letter-spacing:0.08em;font-weight:700;margin-bottom:8px;\">Path Cloud</div>
            <div class=\"chart-canvas small\"><canvas id=\"clubPathCloudLab\"></canvas></div>
          </div>
        </div>
        <div id=\"club-prediction-callout-lab\"></div>
        <div style=\"display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));margin-top:16px;\">
          <div>
            <div class=\"chart-canvas\"><canvas id=\"clubCarryChartLab\"></canvas></div>
            <div class=\"small\" id=\"club-carry-callout-lab\" style=\"display:none;margin-top:10px;\"></div>
          </div>
          <div class=\"chart-canvas\"><canvas id=\"clubSmashChartLab\"></canvas></div>
        </div>
        <div class=\"chart-canvas\" style=\"margin-top:16px;height:320px;\"><canvas id=\"clubDispersionChartLab\"></canvas></div>
        <div style=\"overflow-x:auto;margin-top:16px;\"><table>
          <thead><tr><th>Session</th><th>Shots</th><th>Carry</th><th>Smash</th><th>Offline</th><th>Consistency</th></tr></thead>
          <tbody id=\"club-session-table-body-lab\"></tbody>
        </table></div>
      </section>
      <script>
        const number = (value, digits = 1, suffix = "") => {
          if (value === null || value === undefined || Number.isNaN(value)) return "—";
          return `${Number(value).toFixed(digits)}${suffix}`;
        };
        const deltaHtml = (value, digits = 1, suffix = "", invertGood = false) => {
          if (value === null || value === undefined || Number.isNaN(value)) return "—";
          const numeric = Number(value);
          const sign = numeric > 0 ? "+" : "";
          return `${sign}${numeric.toFixed(digits)}${suffix}`;
        };
        const spinBody = document.getElementById("spin-body");
        const tempoBody = document.getElementById("tempo-body");
        const clubSummaryBody = document.getElementById("club-summary-body-lab");
        const clubNavPills = document.getElementById("club-nav-pills-lab");
        const spin = (data.spin_profile || {}).per_club || {};
        const tempo = (data.tempo_profile || {}).per_club || {};
        const spinLabels = Object.keys(spin).sort();
        const smashLabels = (data.clubs || []).map((c) => c.club_label);
        const smashActual = (data.clubs || []).map((c) => c.avg_smash_factor != null ? parseFloat(c.avg_smash_factor.toFixed(3)) : null);
        const smashPotential = (data.clubs || []).map((c) => c.potential_smash_factor != null ? parseFloat(c.potential_smash_factor.toFixed(3)) : null);
        let clubCarryChart = null;
        let clubSmashChart = null;
        let clubDispersionChart = null;
        let clubPathCloudChart = null;
        if (window.Chart && spinLabels.length) {
          new window.Chart(document.getElementById("clubBarsLab"), {
            type: "bar",
            data: {
              labels: data.charts.clubs.labels,
              datasets: [
                { label: "Avg carry (yds)", data: data.charts.clubs.avg_carry_distance, backgroundColor: "rgba(64,129,20,0.6)" },
                { label: "Consistency score", data: data.charts.clubs.consistency_score, backgroundColor: "rgba(27,113,20,0.6)", yAxisID: "y1" },
              ],
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              scales: {
                y: { beginAtZero: true, title: { display: true, text: "Carry distance (yds)" } },
                y1: { beginAtZero: true, position: "right", max: 100, grid: { drawOnChartArea: false } },
              },
            },
          });
          new window.Chart(document.getElementById("smashHeadroomLab"), {
            type: "bar",
            data: {
              labels: smashLabels,
              datasets: [
                { type: "bar", label: "Avg smash factor", data: smashActual, backgroundColor: "rgba(64,129,20,0.65)", borderColor: "#408114", borderWidth: 1, order: 2 },
                { type: "line", label: "Personal ceiling", data: smashPotential, borderColor: "#1B7114", backgroundColor: "transparent", borderWidth: 2, pointRadius: 4, tension: 0, order: 1 },
              ],
            },
            options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: false, min: 0.9 } } },
          });
          const offlineSorted = [...data.clubs]
            .filter((c) => c.avg_total_deviation_distance != null || c.avg_carry_deviation_distance != null)
            .sort((a, b) => Math.abs(b.avg_total_deviation_distance ?? b.avg_carry_deviation_distance ?? 0) - Math.abs(a.avg_total_deviation_distance ?? a.avg_carry_deviation_distance ?? 0));
          new window.Chart(document.getElementById("offlineSummaryLab"), {
            type: "bar",
            data: {
              labels: offlineSorted.map((c) => c.club_label),
              datasets: [{
                label: "Avg offline (yds)",
                data: offlineSorted.map((c) => parseFloat(Math.abs(c.avg_total_deviation_distance ?? c.avg_carry_deviation_distance ?? 0).toFixed(1))),
                backgroundColor: "rgba(30,52,10,0.65)",
                borderColor: "#1E340A",
                borderWidth: 1.2,
              }],
            },
            options: { indexAxis: "y", responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } },
          });
          new window.Chart(document.getElementById("spinChart"), {
            type: "bar",
            data: {
              labels: spinLabels,
              datasets: [{
                label: "Spin rate avg",
                data: spinLabels.map((c) => spin[c].spin_rate_avg),
                backgroundColor: "rgba(64,129,20,0.65)",
                borderColor: "#408114",
                borderWidth: 1,
              }],
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } },
          });
          new window.Chart(document.getElementById("tempoChart"), {
            type: "line",
            data: {
              labels: spinLabels,
              datasets: [{
                label: "Tempo error avg",
                data: spinLabels.map((c) => (tempo[c] || {}).tempo_error_avg),
                borderColor: "#1B7114",
                backgroundColor: "rgba(27,113,20,0.1)",
                tension: 0.3,
              }],
            },
            options: { responsive: true, maintainAspectRatio: false },
          });
        }
        (data.clubs || []).forEach((club) => {
          const pill = document.createElement("button");
          pill.type = "button";
          pill.dataset.club = club.club_label;
          pill.textContent = club.club_label;
          pill.style.border = "1px solid rgba(30,52,10,0.12)";
          pill.style.background = "#fff";
          pill.style.borderRadius = "999px";
          pill.style.padding = "6px 12px";
          pill.style.fontWeight = "700";
          pill.style.color = "#1B7114";
          pill.style.cursor = "pointer";
          pill.style.fontFamily = "inherit";
          clubNavPills.appendChild(pill);

          const offline = club.avg_total_deviation_distance ?? club.avg_carry_deviation_distance;
          const row = document.createElement("tr");
          row.innerHTML = `
            <td><button type="button" class="club-link-btn" data-club="${club.club_label}">${club.club_label}</button></td>
            <td>${club.shot_count}</td>
            <td>${number(club.avg_carry_distance, 1, " yds")}</td>
            <td>${number(club.avg_smash_factor, 2)}</td>
            <td>${number(offline, 1, " yds")}</td>
            <td>${number(club.consistency_score, 1)}</td>
            <td>${number(club.outlier_rate, 0, "%")}</td>
          `;
          clubSummaryBody.appendChild(row);
        });
        Object.keys(spin).sort().forEach((club) => {
          const s = spin[club] || {};
          const row = document.createElement("tr");
          row.innerHTML = `
            <td>${club}</td>
            <td>${fmt(s.spin_rate_avg, 0)}</td>
            <td>${fmt(s.spin_rate_stddev, 0)}</td>
            <td>${fmt(s.spin_axis_avg, 2)}</td>
            <td>${fmt(s.launch_direction_avg, 2)}</td>
            <td>${fmt(s.apex_height_avg, 1, " yds")}</td>
          `;
          spinBody.appendChild(row);
        });
        Object.keys(tempo).sort().forEach((club) => {
          const t = tempo[club] || {};
          const row = document.createElement("tr");
          row.innerHTML = `
            <td>${club}</td>
            <td>${fmt(t.backswing_time_avg, 3, " s")}</td>
            <td>${fmt(t.downswing_time_avg, 3, " s")}</td>
            <td>${fmt(t.swing_tempo_avg, 2)}</td>
            <td>${fmt(t.target_tempo_avg, 2)}</td>
            <td>${fmt(t.tempo_error_avg, 2)}</td>
            <td>${t.tempo_error_basis || "—"}</td>
          `;
          tempoBody.appendChild(row);
        });

        const heatmapContainer = document.getElementById("consistency-heatmap-club-lab");
        if (heatmapContainer && data.sessions.length) {
          const sessionLabels = data.sessions.map((s) =>
            s.session_timestamp ? new Date(s.session_timestamp).toLocaleDateString(undefined, { month: "short", day: "numeric" }) : s.source_file.slice(0, 10)
          );
          const allClubLabels = [...new Set(data.sessions.flatMap((s) => (s.club_summaries || []).map((c) => c.club_label)))].sort();
          const scoreMap = {};
          data.sessions.forEach((session, sIdx) => {
            (session.club_summaries || []).forEach((club) => {
              if (!scoreMap[club.club_label]) scoreMap[club.club_label] = {};
              scoreMap[club.club_label][sIdx] = club.consistency_score;
            });
          });
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
                cell.className = "heatmap-cell";
                cell.style.backgroundColor = score >= 75 ? "rgba(27,113,20,0.18)" : score >= 50 ? "rgba(77,110,36,0.18)" : "rgba(30,52,10,0.15)";
                cell.style.color = score >= 75 ? "#1B7114" : score >= 50 ? "#4D6E24" : "#1E340A";
                cell.textContent = score.toFixed(0);
              } else {
                cell.className = "heatmap-empty";
                cell.textContent = "—";
              }
            });
          });
          heatmapContainer.appendChild(table);
        }

        const deltaCaption = document.getElementById("delta-caption-lab");
        const deltaBody = document.getElementById("session-delta-body-lab");
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
              <td>${deltaHtml(item.offline_delta, 1, " yds")}</td>
            `;
            deltaBody.appendChild(row);
          });
        }

        function renderClubDetail(clubLabel) {
          const club = (data.clubs || []).find((item) => item.club_label === clubLabel);
          if (!club) return;
          if (clubCarryChart) clubCarryChart.destroy();
          if (clubSmashChart) clubSmashChart.destroy();
          if (clubDispersionChart) clubDispersionChart.destroy();
          if (clubPathCloudChart) clubPathCloudChart.destroy();

          document.getElementById("club-detail-name-lab").textContent = clubLabel;
          const velocityBadge = document.getElementById("club-velocity-badge-lab");
          const velocity = club.improvement_velocity || "Holding steady";
          velocityBadge.textContent = velocity;
          velocityBadge.style.background = velocity === "Most improved" ? "rgba(27,113,20,0.14)" : velocity === "Work needed" ? "rgba(30,52,10,0.14)" : "rgba(77,110,36,0.14)";
          velocityBadge.style.color = velocity === "Most improved" ? "#1B7114" : velocity === "Work needed" ? "#1E340A" : "#4D6E24";

          const strip = document.getElementById("club-stat-strip-lab");
          strip.innerHTML = "";
          const offline = club.avg_total_deviation_distance ?? club.avg_carry_deviation_distance;
          [
            ["Avg carry", number(club.avg_carry_distance, 1, " yds")],
            ["Smash", number(club.avg_smash_factor, 2)],
            ["Consistency", number(club.consistency_score, 1)],
            ["Avg offline", number(offline, 1, " yds")],
            ["Outliers", number(club.outlier_rate, 0, "%")],
            ["Shots", club.shot_count ?? "—"],
          ].forEach(([label, value]) => {
            const card = document.createElement("div");
            card.style.background = "rgba(242,242,240,0.9)";
            card.style.border = "1px solid rgba(30,52,10,0.12)";
            card.style.borderRadius = "12px";
            card.style.padding = "12px";
            card.innerHTML = `<div style="font-size:1.3rem;font-weight:800;color:#1E340A;">${value}</div><div class="small">${label}</div>`;
            strip.appendChild(card);
          });
          if (club.potential_gap_pct != null) {
            const card = document.createElement("div");
            card.style.background = "rgba(242,242,240,0.9)";
            card.style.border = "1px solid rgba(30,52,10,0.12)";
            card.style.borderRadius = "12px";
            card.style.padding = "12px";
            card.innerHTML = `<div style="font-size:1.3rem;font-weight:800;color:#1E340A;">${club.potential_gap_pct.toFixed(0)}%</div><div class="small">Strike potential</div><div style="margin-top:8px;height:6px;background:rgba(30,52,10,0.12);border-radius:999px;"><div style="height:6px;border-radius:999px;background:#408114;width:${Math.min(100, club.potential_gap_pct)}%;"></div></div>`;
            strip.appendChild(card);
          }

          const pathMetrics = document.getElementById("club-path-metrics-lab");
          pathMetrics.innerHTML = "";
          [
            ["Club path", club.avg_club_path, 2, " deg"],
            ["Face to path", club.avg_face_to_path, 2, " deg"],
            ["Attack angle", club.avg_attack_angle, 2, " deg"],
          ].forEach(([label, value, digits, suffix]) => {
            const metric = document.createElement("div");
            metric.className = "path-metric";
            metric.innerHTML = `<div class="value">${number(value, digits, suffix)}</div><div class="label">${label}</div>`;
            pathMetrics.appendChild(metric);
          });
          const clampPct = (value) => Math.max(6, Math.min(94, 50 + (Number(value) || 0) * 4.5));
          const pathMarker = document.getElementById("club-path-marker-lab");
          const faceMarker = document.getElementById("club-face-marker-lab");
          pathMarker.style.left = `${clampPct(club.avg_club_path)}%`;
          faceMarker.style.left = `${clampPct(club.avg_face_to_path)}%`;

          const predictionCallout = document.getElementById("club-prediction-callout-lab");
          predictionCallout.innerHTML = "";
          const clubForecast = ((data.forecasts || {}).per_club || {})[clubLabel];
          if (clubForecast && clubForecast.carry) {
            const band = clubForecast.carry.confidence_band[0];
            const callout = document.createElement("div");
            callout.className = "forecast-callout";
            callout.innerHTML = `<strong>Next session:</strong> carry forecast ${band[0]}-${band[1]} yds with a ${clubForecast.carry.slope >= 0 ? "+" : ""}${clubForecast.carry.slope.toFixed(1)} yds/session slope.`;
            predictionCallout.appendChild(callout);
          }

          const sessionRows = [];
          (data.sessions || []).forEach((session) => {
            const summary = (session.club_summaries || []).find((item) => item.club_label === clubLabel);
            if (summary) sessionRows.push({ session, summary });
          });
          const sessionLabels = sessionRows.map(({ session }) =>
            session.session_timestamp
              ? new Date(session.session_timestamp).toLocaleDateString(undefined, { month: "short", day: "numeric" })
              : String(session.source_file || "session").slice(0, 10)
          );
          const carryValues = sessionRows.map(({ summary }) => summary.avg_carry_distance != null ? parseFloat(summary.avg_carry_distance.toFixed(1)) : null);
          const smashValues = sessionRows.map(({ summary }) => summary.avg_smash_factor != null ? parseFloat(summary.avg_smash_factor.toFixed(3)) : null);

          let carryChartLabels = [...sessionLabels];
          const carryDatasets = [{
            label: "Avg carry (yds)",
            data: [...carryValues],
            borderColor: "#408114",
            backgroundColor: "rgba(64,129,20,0.12)",
            tension: 0.3,
            pointRadius: 4,
          }];
          const carryCallout = document.getElementById("club-carry-callout-lab");
          if (clubForecast && clubForecast.carry && carryValues.length) {
            carryChartLabels = [...sessionLabels, "+1", "+2", "+3"];
            const nullPad = sessionLabels.map(() => null);
            carryDatasets[0].data = [...carryValues, null, null, null];
            carryDatasets.push({
              label: "Forecast",
              data: [...nullPad.slice(0, -1), carryValues[carryValues.length - 1], ...clubForecast.carry.predictions],
              borderColor: "rgba(64,129,20,0.55)",
              backgroundColor: "transparent",
              borderDash: [6, 4],
              borderWidth: 2,
              pointRadius: [...nullPad.slice(0, -1).map(() => 0), 4, 3, 3, 3],
              tension: 0,
            });
            carryCallout.style.display = "block";
            carryCallout.innerHTML = `<strong>Forecast:</strong> projected ${clubForecast.carry.predictions[2]} yds in 3 sessions.`;
          } else {
            carryCallout.style.display = "none";
          }

          if (window.Chart) {
            const pathPoints = (data.charts.path_cloud || []).filter((point) => point.club === clubLabel);
            const pathValues = pathPoints.flatMap((point) => [point.x, point.y]);
            const minVal = pathValues.length ? Math.min(...pathValues, club.avg_club_path ?? 0, club.avg_face_to_path ?? 0) : -8;
            const maxVal = pathValues.length ? Math.max(...pathValues, club.avg_club_path ?? 0, club.avg_face_to_path ?? 0) : 8;
            const clampMin = Math.min(-8, Math.floor(minVal) - 1);
            const clampMax = Math.max(8, Math.ceil(maxVal) + 1);
            clubPathCloudChart = new window.Chart(document.getElementById("clubPathCloudLab"), {
              type: "scatter",
              data: {
                datasets: [
                  {
                    label: "Shot cloud",
                    data: pathPoints.map((point) => ({ x: point.x, y: point.y })),
                    backgroundColor: pathPoints.map((point) => point.outlier ? "#1E340A" : "rgba(64,129,20,0.65)"),
                    pointRadius: pathPoints.map((point) => point.outlier ? 5 : 4),
                    pointStyle: pathPoints.map((point) => point.outlier ? "triangle" : "circle"),
                  },
                  {
                    label: "Club average",
                    data: [{ x: club.avg_club_path, y: club.avg_face_to_path }],
                    backgroundColor: "#1B7114",
                    borderColor: "#1B7114",
                    pointRadius: 8,
                    pointStyle: "rectRot",
                  },
                ],
              },
              options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: { position: "top" },
                  tooltip: {
                    callbacks: {
                      label: (ctx) => `${ctx.dataset.label}: path ${ctx.parsed.x?.toFixed(2)}°, face ${ctx.parsed.y?.toFixed(2)}°`,
                    },
                  },
                },
                scales: {
                  x: { min: clampMin, max: clampMax, title: { display: true, text: "Club path (deg)" } },
                  y: { min: clampMin, max: clampMax, title: { display: true, text: "Face to path (deg)" } },
                },
              },
            });
            clubCarryChart = new window.Chart(document.getElementById("clubCarryChartLab"), {
              type: "line",
              data: { labels: carryChartLabels, datasets: carryDatasets },
              options: { responsive: true, maintainAspectRatio: false, interaction: { mode: "index", intersect: false } },
            });
            clubSmashChart = new window.Chart(document.getElementById("clubSmashChartLab"), {
              type: "bar",
              data: {
                labels: sessionLabels,
                datasets: [
                  { type: "bar", label: "Avg smash factor", data: smashValues, backgroundColor: "rgba(64,129,20,0.65)", borderColor: "#408114", borderWidth: 1, order: 2 },
                  { type: "line", label: "Personal ceiling", data: sessionLabels.map(() => club.potential_smash_factor), borderColor: "#1B7114", backgroundColor: "transparent", borderWidth: 2, pointRadius: 0, tension: 0, order: 1 },
                ],
              },
              options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: "top" } }, scales: { y: { beginAtZero: false, min: 0.9 } } },
            });

            const dispersionGroups = {};
            (data.charts.dispersion || []).forEach((point) => {
              if (point.club !== clubLabel) return;
              const idx = point.session_index ?? 0;
              if (!dispersionGroups[idx]) dispersionGroups[idx] = [];
              dispersionGroups[idx].push(point);
            });
            const totalSessions = (data.sessions || []).length;
            clubDispersionChart = new window.Chart(document.getElementById("clubDispersionChartLab"), {
              type: "scatter",
              data: {
                datasets: Object.entries(dispersionGroups).map(([idxStr, points]) => {
                  const idx = Number(idxStr);
                  const age = totalSessions - 1 - idx;
                  const opacity = age <= 0 ? "ff" : age === 1 ? "99" : age === 2 ? "55" : "30";
                  const label = data.sessions[idx]?.session_timestamp
                    ? new Date(data.sessions[idx].session_timestamp).toLocaleDateString(undefined, { month: "short", day: "numeric" })
                    : `Session ${idx + 1}`;
                  return {
                    label,
                    data: points.map((point) => ({ x: point.x, y: point.y })),
                    pointRadius: points.map((point) => point.outlier ? 6 : 4),
                    pointStyle: points.map((point) => point.outlier ? "triangle" : "circle"),
                    backgroundColor: points.map((point) => (point.outlier ? "#1E340A" : "#408114") + opacity),
                  };
                }),
              },
              options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: "top" } },
                scales: {
                  x: { type: "linear", title: { display: true, text: "Offline / deviation (yds)" } },
                  y: { type: "linear", title: { display: true, text: "Carry distance (yds)" } },
                },
              },
            });
          }

          const sessionTableBody = document.getElementById("club-session-table-body-lab");
          sessionTableBody.innerHTML = "";
          sessionRows.forEach(({ session, summary }) => {
            const date = session.session_timestamp
              ? new Date(session.session_timestamp).toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" })
              : session.source_file;
            const row = document.createElement("tr");
            row.innerHTML = `
              <td>${date}</td>
              <td>${summary.shot_count ?? "—"}</td>
              <td>${number(summary.avg_carry_distance, 1, " yds")}</td>
              <td>${number(summary.avg_smash_factor, 2)}</td>
              <td>${number(summary.avg_total_deviation_distance ?? summary.avg_carry_deviation_distance, 1, " yds")}</td>
              <td>${number(summary.consistency_score, 1)}</td>
            `;
            sessionTableBody.appendChild(row);
          });

          document.querySelectorAll("#club-nav-pills-lab button").forEach((button) => {
            button.style.background = button.dataset.club === clubLabel ? "rgba(64,129,20,0.12)" : "#fff";
            button.style.borderColor = button.dataset.club === clubLabel ? "#408114" : "rgba(30,52,10,0.12)";
          });
        }

        clubNavPills.addEventListener("click", (event) => {
          const button = event.target.closest("button[data-club]");
          if (button) renderClubDetail(button.dataset.club);
        });
        clubSummaryBody.addEventListener("click", (event) => {
          const button = event.target.closest("button[data-club]");
          if (button) renderClubDetail(button.dataset.club);
        });
        if ((data.clubs || []).length) {
          renderClubDetail(data.clubs[0].club_label);
        }
      </script>
    """
    return _render_subpage(
        "Club Lab - Golf Range Analytics",
        "Club Lab",
        "Per-club ball-flight, spin, and tempo profiles built from your raw launch-monitor fields.",
        body,
    )


def render_sessions_page() -> str:
    body = """
      <section class=\"panel\">
        <h2>Session Trends</h2>
        <div class=\"chart-canvas\"><canvas id=\"sessionTrendsChart\"></canvas></div>
      </section>
      <section class=\"panel\">
        <h2>Session Replay</h2>
        <p class=\"small\">Review each session in chronological order with carry, smash, offline, and flagged-shot rate.</p>
        <div style=\"overflow-x:auto;\"><table>
          <thead><tr><th>Date</th><th>Shots</th><th>Carry</th><th>Smash</th><th>Offline</th><th>Flagged</th></tr></thead>
          <tbody id=\"session-body\"></tbody>
        </table></div>
      </section>
      <script>
        const sessionBody = document.getElementById("session-body");
        const qualityBySession = new Map(((data.data_quality || {}).per_session || []).map((s) => [s.session_id, s]));
        const labels = (data.sessions || []).map((s) =>
          s.session_timestamp ? new Date(s.session_timestamp).toLocaleDateString(undefined, { month: "short", day: "numeric" }) : s.source_file
        );
        if (window.Chart && labels.length) {
          new window.Chart(document.getElementById("sessionTrendsChart"), {
            type: "line",
            data: {
              labels,
              datasets: [
                {
                  label: "Avg carry (yds)",
                  data: (data.sessions || []).map((s) => s.avg_carry_distance),
                  borderColor: "#408114",
                  backgroundColor: "rgba(64,129,20,0.1)",
                  tension: 0.3,
                  yAxisID: "y",
                },
                {
                  label: "Flagged rate (%)",
                  data: (data.data_quality?.per_session || []).map((s) => s.flagged_rate),
                  borderColor: "#1E340A",
                  backgroundColor: "rgba(30,52,10,0.08)",
                  tension: 0.3,
                  yAxisID: "y1",
                },
              ],
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              scales: {
                y: { position: "left", beginAtZero: false },
                y1: { position: "right", beginAtZero: true, grid: { drawOnChartArea: false } },
              },
            },
          });
        }
        (data.sessions || []).forEach((s) => {
          const q = qualityBySession.get(s.session_id) || {};
          const date = s.session_timestamp ? new Date(s.session_timestamp).toLocaleDateString() : s.source_file;
          const row = document.createElement("tr");
          row.innerHTML = `
            <td>${date}</td>
            <td>${s.shot_count ?? "—"}</td>
            <td>${fmt(s.avg_carry_distance, 1, " yds")}</td>
            <td>${fmt(s.avg_smash_factor, 2)}</td>
            <td>${fmt(s.avg_offline_distance, 1, " yds")}</td>
            <td>${fmt(q.flagged_rate, 1, "%")}</td>
          `;
          sessionBody.appendChild(row);
        });
      </script>
    """
    return _render_subpage(
        "Session Replay - Golf Range Analytics",
        "Session Replay",
        "Track what changed from session to session and where quality or consistency shifted.",
        body,
    )


def render_gapping_page() -> str:
    body = """
      <section class=\"panel\">
        <h2>Carry Ladder And Target Error</h2>
        <div style=\"display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));\">
          <div class=\"chart-canvas small\"><canvas id=\"carryLadderChart\"></canvas></div>
          <div class=\"chart-canvas small\"><canvas id=\"targetErrorChart\"></canvas></div>
        </div>
      </section>
      <section class=\"panel\">
        <h2>Gapping And Target Control</h2>
        <div style=\"overflow-x:auto;\"><table>
          <thead><tr><th>Club</th><th>Target carry</th><th>Avg carry</th><th>Target total</th><th>Avg total</th><th>Carry SD</th><th>Carry target error</th><th>Total target error</th><th>Strike potential</th></tr></thead>
          <tbody id=\"gapping-body\"></tbody>
        </table></div>
        <div style=\"margin-top:18px;\">
          <div class=\"small\" style=\"text-transform:uppercase;letter-spacing:0.08em;font-weight:700;\">Progress To Goal</div>
          <div class=\"chart-canvas\" style=\"height:420px;margin-top:10px;\"><canvas id=\"goalSlopeChart\"></canvas></div>
          <p class=\"small\" style=\"margin-top:8px;\">Each line shows one club moving from your current average carry to the target carry goal.</p>
        </div>
      </section>
      <section class=\"panel\">
        <h2>Environment Context</h2>
        <div style=\"display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));align-items:stretch;\">
          <div style=\"padding:16px;border:1px solid rgba(30,52,10,0.12);border-radius:16px;background:linear-gradient(180deg,rgba(64,129,20,0.08),rgba(242,242,240,0.95));\">
            <div class=\"small\" style=\"text-transform:uppercase;letter-spacing:0.08em;font-weight:700;\">Atmosphere</div>
            <div id=\"env-summary\" style=\"margin-top:10px;font-size:1.05rem;line-height:1.5;font-weight:650;color:#1E340A;\"></div>
          </div>
          <div id=\"env-metrics\" style=\"display:grid;gap:10px;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));\"></div>
        </div>
      </section>
      <script>
        const target = (data.target_control || {}).per_club || {};
        const bagOrder = (clubLabel) => {
          const text = String(clubLabel || "").toLowerCase();
          if (text.includes("driver")) return 0;
          const wood = text.match(/(\\d+)\\s*wood|wood\\s*(\\d+)/);
          if (wood) return 100 + Number(wood[1] || wood[2]);
          if (text.includes("wood")) return 199;
          const hybrid = text.match(/(\\d+)\\s*hybrid|hybrid\\s*(\\d+)/);
          if (hybrid) return 200 + Number(hybrid[1] || hybrid[2]);
          if (text.includes("hybrid") || text.includes("rescue")) return 299;
          const iron = text.match(/(\\d+)\\s*iron|iron\\s*(\\d+)/);
          if (iron) return 300 + Number(iron[1] || iron[2]);
          if (text.includes("pitching") || /\\bpw\\b/.test(text)) return 400;
          if (text.includes("gap") || text.includes("approach") || /\\baw\\b|\\bgw\\b/.test(text)) return 401;
          if (text.includes("sand") || /\\bsw\\b/.test(text)) return 402;
          if (text.includes("lob") || /\\blw\\b/.test(text)) return 403;
          if (text.includes("wedge")) return 409;
          if (text.includes("putter")) return 500;
          return 999;
        };
        const clubsData = [...(data.clubs || [])].sort((left, right) => {
          const keyDiff = bagOrder(left.club_label) - bagOrder(right.club_label);
          if (keyDiff !== 0) return keyDiff;
          return String(left.club_label || "").localeCompare(String(right.club_label || ""));
        });
        const clubs = clubsData.map((c) => c.club_label);
        const targetCarryValues = clubs.map((clubLabel) => (target[clubLabel] || {}).auto_target_carry_distance_avg);
        const avgCarryValues = clubsData.map((club) => club.avg_carry_distance);
        const gapToGoalValues = clubs.map((clubLabel, index) => {
          const goal = targetCarryValues[index];
          const actual = avgCarryValues[index];
          if (goal === null || goal === undefined || actual === null || actual === undefined) return null;
          return Number(goal) - Number(actual);
        });
        if (window.Chart && clubs.length) {
          new window.Chart(document.getElementById("carryLadderChart"), {
            type: "bar",
            data: {
              labels: clubs,
              datasets: [{
                label: "Avg carry (yds)",
                data: avgCarryValues,
                backgroundColor: "rgba(64,129,20,0.65)",
                borderColor: "#408114",
              }],
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } },
          });
          new window.Chart(document.getElementById("targetErrorChart"), {
            type: "line",
            data: {
              labels: clubs,
              datasets: [{
                label: "Carry target error (yds)",
                data: clubs.map((c) => (target[c] || {}).carry_target_error_avg),
                borderColor: "#1B7114",
                backgroundColor: "rgba(27,113,20,0.1)",
                tension: 0.3,
              }],
            },
            options: { responsive: true, maintainAspectRatio: false },
          });

          const slopeDatasets = clubs.map((clubLabel, index) => {
            const avg = avgCarryValues[index];
            const targetCarry = targetCarryValues[index];
            const gap = gapToGoalValues[index];
            const isOnTrack = typeof gap === "number" && gap <= 0;
            return {
              label: clubLabel,
              data: [avg, targetCarry],
              borderColor: isOnTrack ? "#4D6E24" : "#1B7114",
              backgroundColor: isOnTrack ? "#4D6E24" : "#1B7114",
              pointBackgroundColor: ["#408114", isOnTrack ? "#4D6E24" : "#1B7114"],
              pointBorderColor: ["#408114", isOnTrack ? "#4D6E24" : "#1B7114"],
              borderWidth: 2,
              pointRadius: [4, 6],
              pointHoverRadius: [6, 8],
              tension: 0,
            };
          });

          new window.Chart(document.getElementById("goalSlopeChart"), {
            type: "line",
            data: {
              labels: ["Avg carry", "Target carry"],
              datasets: slopeDatasets,
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: { display: false },
                tooltip: {
                  callbacks: {
                    title: (items) => `${items[0].dataset.label} · ${items[0].label}`,
                    label: (ctx) => `Carry: ${ctx.parsed.y?.toFixed(1)} yds`,
                    afterLabel: (ctx) => {
                      const gap = gapToGoalValues[ctx.datasetIndex];
                      if (gap === null || gap === undefined) return "Gap to goal: —";
                      const sign = gap > 0 ? "+" : "";
                      return `Gap to goal: ${sign}${gap.toFixed(1)} yds`;
                    },
                  },
                },
              },
              scales: {
                y: { title: { display: true, text: "Carry distance (yds)" } },
                x: { grid: { color: "rgba(30,52,10,0.08)" } },
              },
            },
          });
        }
        const rows = document.getElementById("gapping-body");
        clubsData.forEach((club) => {
          const t = target[club.club_label] || {};
          const row = document.createElement("tr");
          row.innerHTML = `
            <td>${club.club_label}</td>
            <td>${fmt(t.auto_target_carry_distance_avg, 0, " yds")}</td>
            <td>${fmt(club.avg_carry_distance, 1, " yds")}</td>
            <td>${fmt(t.auto_target_total_distance_avg, 0, " yds")}</td>
            <td>${fmt(club.avg_total_distance, 1, " yds")}</td>
            <td>${fmt(club.carry_stddev, 1, " yds")}</td>
            <td>${fmt(t.carry_target_error_avg, 1, " yds")}</td>
            <td>${fmt(t.total_target_error_avg, 1, " yds")}</td>
            <td>${fmt(club.potential_gap_pct, 0, "%")}</td>
          `;
          rows.appendChild(row);
        });
        const env = data.environment || {};
        document.getElementById("env-summary").textContent = [
          `Average temp ${fmt((env.conditions || {}).temperature_avg, 1)} F`,
          `Humidity ${fmt((env.conditions || {}).relative_humidity_avg, 1)}%`,
          `Air pressure ${fmt((env.conditions || {}).air_pressure_avg, 2)} inHg`
        ].join(" · ");
        const envMetrics = document.getElementById("env-metrics");
        envMetrics.innerHTML = "";
        [
          ["Air density", fmt((env.conditions || {}).air_density_avg, 3), "g/L"],
          ["Carry vs temp", fmt(env.carry_vs_temperature_slope, 3), "yds/F"],
          ["Carry vs density", fmt(env.carry_vs_air_density_slope, 3), "yds/(g/L)"],
          ["Samples", fmt(env.sample_size, 0), "shots"],
        ].forEach(([label, value, suffix]) => {
          const card = document.createElement("div");
          card.style.padding = "14px";
          card.style.border = "1px solid rgba(30,52,10,0.12)";
          card.style.borderRadius = "14px";
          card.style.background = "rgba(242,242,240,0.92)";
          card.innerHTML = `<div style=\"font-size:1.35rem;font-weight:800;color:#1E340A;\">${value}</div><div class=\"small\" style=\"margin-top:4px;\">${label}${suffix ? ` <span style=\\\"opacity:0.7;\\\">${suffix}</span>` : ""}</div>`;
          envMetrics.appendChild(card);
        });
      </script>
    """
    return _render_subpage(
        "Gapping And Environment - Golf Range Analytics",
        "Gapping And Environment",
        "Distance spacing, target-distance control, and weather context to explain carry changes.",
        body,
    )


def render_data_quality_page() -> str:
    body = """
      <section class=\"panel\">
        <h2>Quality Trends</h2>
        <div style=\"display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));\">
          <div class=\"chart-canvas small\"><canvas id=\"qualitySessionChart\"></canvas></div>
          <div class=\"chart-canvas small\"><canvas id=\"qualityReasonChart\"></canvas></div>
        </div>
      </section>
      <section class=\"panel\">
        <h2>Data Quality Overview</h2>
        <p id=\"quality-summary\" class=\"small\"></p>
        <div style=\"overflow-x:auto;\"><table>
          <thead><tr><th>Session</th><th>Shots</th><th>Flagged</th><th>Flagged rate</th><th>Missing critical</th><th>Suspicious</th></tr></thead>
          <tbody id=\"quality-body\"></tbody>
        </table></div>
      </section>
      <section class=\"panel\">
        <h2 id=\"quality-breakdown-title\">Flag Reason Breakdown</h2>
        <div style=\"overflow-x:auto;\"><table>
          <thead><tr><th>Reason</th><th>Count</th></tr></thead>
          <tbody id=\"reason-body\"></tbody>
        </table></div>
      </section>
      <section class=\"panel\">
        <h2>Critical Field Coverage</h2>
        <div style=\"overflow-x:auto;\"><table>
          <thead><tr><th>Field</th><th>Missing shots</th></tr></thead>
          <tbody id=\"missing-body\"></tbody>
        </table></div>
      </section>
      <script>
        const dq = data.data_quality || {};
        const qualityLabel = (key) => {
          const text = String(key || "");
          const [family, code] = text.includes(":") ? text.split(":", 2) : [null, text];
          const labels = {
            total_lt_carry: "Total distance less than carry",
            smash_out_of_range: "Smash factor outside expected range",
            launch_out_of_range: "Launch angle outside club range",
            spin_out_of_range: "Spin rate outside club range",
            offline_gt_carry: "Offline distance exceeds carry",
            club_speed: "Club speed",
            ball_speed: "Ball speed",
            carry_distance: "Carry distance",
            total_distance: "Total distance",
            smash_factor: "Smash factor",
            launch_angle: "Launch angle",
            spin_rate: "Spin rate",
            swing_tempo: "Swing tempo",
          };
          const familyLabel = family ? `${family.replace(/_/g, " ").replace(/\\b\\w/g, (ch) => ch.toUpperCase())} club` : null;
          const codeLabel = labels[code] || code.replace(/_/g, " ").replace(/\\b\\w/g, (ch) => ch.toUpperCase());
          return familyLabel ? `${familyLabel} · ${codeLabel}` : codeLabel;
        };
        const qLabels = (dq.per_session || []).map((s) =>
          s.session_timestamp ? new Date(s.session_timestamp).toLocaleDateString(undefined, { month: "short", day: "numeric" }) : s.source_file
        );
        if (window.Chart) {
          new window.Chart(document.getElementById("qualitySessionChart"), {
            type: "bar",
            data: {
              labels: qLabels,
              datasets: [
                {
                  label: "Flagged rate (%)",
                  data: (dq.per_session || []).map((s) => s.flagged_rate),
                  backgroundColor: "rgba(30,52,10,0.65)",
                  borderColor: "#1E340A",
                },
                {
                  label: "Missing critical (%)",
                  data: (dq.per_session || []).map((s) => s.missing_critical_rate),
                  backgroundColor: "rgba(64,129,20,0.55)",
                  borderColor: "#408114",
                },
                {
                  label: "Suspicious (%)",
                  data: (dq.per_session || []).map((s) => s.suspicious_rate),
                  backgroundColor: "rgba(77,110,36,0.55)",
                  borderColor: "#4D6E24",
                },
              ],
            },
            options: { responsive: true, maintainAspectRatio: false },
          });
          const reasonLabels = Object.keys(dq.flag_reasons || {});
          if (reasonLabels.length) {
            new window.Chart(document.getElementById("qualityReasonChart"), {
              type: "doughnut",
              data: {
                labels: reasonLabels.map((key) => qualityLabel(key)),
                datasets: [{
                  data: reasonLabels.map((k) => dq.flag_reasons[k]),
                  backgroundColor: ["#1E340A", "#408114", "#4D6E24", "#6b7280"],
                }],
              },
              options: { responsive: true, maintainAspectRatio: false },
            });
          } else {
            const missingLabels = Object.keys(dq.missing_by_field || {}).slice(0, 6);
            document.getElementById("quality-breakdown-title").textContent = "Missing Critical Fields";
            new window.Chart(document.getElementById("qualityReasonChart"), {
              type: "bar",
              data: {
                labels: missingLabels.map((key) => qualityLabel(key)),
                datasets: [{
                  label: "Missing shots",
                  data: missingLabels.map((k) => dq.missing_by_field[k]),
                  backgroundColor: "rgba(64,129,20,0.65)",
                  borderColor: "#408114",
                }],
              },
              options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } },
            });
          }
        }
        document.getElementById("quality-summary").textContent =
          `Flagged ${fmt(dq.flagged_shot_count, 0)} of ${fmt(dq.total_shots, 0)} shots (${fmt(dq.flagged_rate, 1, "%")}) · Suspicious shots ${fmt(dq.suspicious_shot_count, 0)} (${fmt(dq.suspicious_rate, 1, "%")})`;
        const body = document.getElementById("quality-body");
        (dq.per_session || []).forEach((s) => {
          const date = s.session_timestamp ? new Date(s.session_timestamp).toLocaleDateString() : s.source_file;
          const row = document.createElement("tr");
          row.innerHTML = `
            <td>${date}</td>
            <td>${s.shot_count ?? "—"}</td>
            <td>${s.flagged_shot_count ?? "—"}</td>
            <td>${fmt(s.flagged_rate, 1, "%")}</td>
            <td>${fmt(s.missing_critical_rate, 1, "%")}</td>
            <td>${fmt(s.suspicious_rate, 1, "%")}</td>
          `;
          body.appendChild(row);
        });
        const reasons = document.getElementById("reason-body");
        const reasonSource = Object.keys(dq.flag_reasons || {}).length ? (dq.flag_reasons || {}) : (dq.suspicious_checks || {});
        Object.entries(reasonSource).forEach(([reason, count]) => {
          const row = document.createElement("tr");
          row.innerHTML = `<td>${qualityLabel(reason)}</td><td>${count}</td>`;
          reasons.appendChild(row);
        });
        const missingBody = document.getElementById("missing-body");
        Object.entries(dq.missing_by_field || {}).forEach(([field, count]) => {
          const row = document.createElement("tr");
          row.innerHTML = `<td>${qualityLabel(field)}</td><td>${count}</td>`;
          missingBody.appendChild(row);
        });
      </script>
    """
    return _render_subpage(
        "Data Quality - Golf Range Analytics",
        "Data Quality",
        "Quality flags and signal reliability to keep recommendations trustworthy.",
        body,
    )


def render_coaching_page() -> str:
    body = """
      <style>
        /* ── Next session focus ─────────────────────────── */
        .next-session-list {
          list-style: none; padding: 0; margin: 0;
          display: grid; gap: 10px;
          grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
        }
        .next-session-item {
          border-left: 4px solid var(--good);
          padding: 12px 14px; border-radius: 12px;
          background: rgba(64,129,20,0.06);
        }
        .next-session-item h3 { margin: 0 0 4px; font-size: 1rem; }
        /* ── Recommendations ─────────────────────────────── */
        .recommendation-list { display: grid; gap: 12px; }
        .recommendation { padding: 14px 16px; border-radius: 12px; margin-bottom: 2px; }
        .rec-high { border-left: 4px solid #1E340A; background: rgba(30,52,10,0.07); }
        .rec-med  { border-left: 4px solid #408114; background: rgba(64,129,20,0.08); }
        .rec-low  { border-left: 4px solid #4D6E24; background: rgba(77,110,36,0.07); }
        .confidence-low { opacity: 0.72; }
        .confidence-high { box-shadow: 0 0 0 1px rgba(27,113,20,0.35) inset; }
        .recommendation-header {
          display: flex; justify-content: space-between; gap: 12px;
          align-items: baseline; margin-bottom: 4px;
        }
        .severity-badge {
          display: inline-block; padding: 2px 9px; border-radius: 999px;
          font-size: 0.73rem; font-weight: 700; color: #fff; white-space: nowrap;
        }
        .badge-high { background: #1E340A; }
        .badge-med  { background: #408114; }
        .badge-low  { background: #4D6E24; }
        .confidence { margin-top: 6px; font-size: 0.78rem; color: var(--muted); }
        .confidence-pill {
          display: inline-block; margin-top: 6px; padding: 2px 8px;
          border-radius: 999px; font-size: 0.72rem; font-weight: 700;
          color: #fff; background: #4D6E24;
        }
        .confidence-pill.high { background: #1B7114; }
        .confidence-pill.medium { background: #4D6E24; }
        .confidence-pill.low { background: #6b7280; }
        .rank-why { margin-top: 8px; font-size: 0.78rem; color: var(--muted); }
        .rank-why summary { cursor: pointer; font-weight: 700; color: var(--accent); }
        .coaching-grid { display: grid; gap: 24px; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); }
      </style>
      <div class=\"coaching-grid\">
        <section class=\"panel\">
          <h2>Next Session Focus</h2>
          <div class=\"next-session-list\" id=\"next-session-list\"></div>
        </section>
        <section class=\"panel\">
          <h2>What To Work On</h2>
          <div class=\"recommendation-list\" id=\"recommendations\"></div>
        </section>
      </div>
      <script>
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

        // ── Recommendations ───────────────────────────────────────────────
        const recommendations = document.getElementById("recommendations");
        if (!data.recommendations || !data.recommendations.length) {
          const empty = document.createElement("p");
          empty.textContent = "No high-priority recommendations yet. Add more sessions to unlock trend-based coaching prompts.";
          recommendations.appendChild(empty);
        } else {
          data.recommendations.forEach((item) => {
            const label = item.severity_label || (item.severity >= 60 ? "High" : item.severity >= 30 ? "Medium" : "Low");
            const recCls = label === "High" ? "rec-high" : label === "Medium" ? "rec-med" : "rec-low";
            const badgeCls = label === "High" ? "badge-high" : label === "Medium" ? "badge-med" : "badge-low";
            const conf = (item.confidence_label || "Medium").toLowerCase();
            const div = document.createElement("div");
            div.className = `recommendation ${recCls}`;
            if (conf === "low") div.classList.add("confidence-low");
            if (conf === "high") div.classList.add("confidence-high");
            const header = document.createElement("div");
            header.className = "recommendation-header";
            const h3 = document.createElement("h3");
            h3.textContent = item.title;
            const badge = document.createElement("span");
            badge.className = `severity-badge ${badgeCls}`;
            badge.textContent = label;
            header.appendChild(h3);
            header.appendChild(badge);
            const body = document.createElement("p");
            body.textContent = item.summary;
            const meta = document.createElement("div");
            meta.className = "small";
            meta.textContent = `${item.focus_area} · ${item.evidence}`;
            const confPill = document.createElement("span");
            confPill.className = `confidence-pill ${conf}`;
            confPill.textContent = `${item.confidence_label || "Medium"} confidence`;
            const confidence = document.createElement("div");
            confidence.className = "confidence";
            confidence.textContent = `Confidence: ${item.confidence_label || "—"} (${item.confidence_score ?? "—"}/100) · ${item.confidence_reason || ""}`;
            const rankWhy = document.createElement("details");
            rankWhy.className = "rank-why";
            const rankSummary = document.createElement("summary");
            rankSummary.textContent = "Why this rank?";
            const reason = document.createElement("div");
            reason.textContent = item.priority_reason || `Priority ${item.priority_score ?? "—"} from severity and confidence blend.`;
            rankWhy.appendChild(rankSummary);
            rankWhy.appendChild(reason);
            div.appendChild(header);
            div.appendChild(body);
            div.appendChild(meta);
            div.appendChild(confPill);
            div.appendChild(confidence);
            div.appendChild(rankWhy);
            recommendations.appendChild(div);
          });
        }
      </script>
    """
    return _render_subpage(
        "Coaching - Golf Range Analytics",
        "Coaching",
        "Prioritised focus areas and practice recommendations based on your session history.",
        body,
    )


def write_site(data: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "site-data.js").write_text(
        "window.GOLF_SITE_DATA = " + json.dumps(data, indent=2) + ";\n",
        encoding="utf-8",
    )
    (output_dir / "index.html").write_text(render_html(), encoding="utf-8")
    (output_dir / "clubs.html").write_text(render_clubs_page(), encoding="utf-8")
    (output_dir / "sessions.html").write_text(render_sessions_page(), encoding="utf-8")
    (output_dir / "gapping.html").write_text(render_gapping_page(), encoding="utf-8")
    (output_dir / "data-quality.html").write_text(render_data_quality_page(), encoding="utf-8")
    (output_dir / "coaching.html").write_text(render_coaching_page(), encoding="utf-8")
    (output_dir / ".nojekyll").write_text("", encoding="utf-8")
