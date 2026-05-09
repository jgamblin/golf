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
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        margin-bottom: 28px;
      }
      .chart-wrap { display: flex; flex-direction: column; }
      .chart-canvas { position: relative; height: 320px; width: 100%; }
      .chart-canvas.tall { height: 420px; }
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
        grid-template-columns: 1fr auto auto auto auto auto auto auto;
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
        background: rgba(64, 129, 20, 0.08);
      }
      .tab-panel { display: none; }
      .tab-panel.active { display: block; }

      /* ── Coaching tab ───────────────────────────────── */
      .coaching-grid {
        display: grid;
        gap: 24px;
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
      .club-link-btn {
        background: none; border: none; color: var(--accent2); font-weight: 600;
        font-size: 0.95rem; cursor: pointer; text-decoration: underline;
        text-underline-offset: 3px; font-family: inherit; padding: 0;
      }
      .club-link-btn:hover { color: var(--accent); }
      .club-nav-pill {
        display: inline-flex; align-items: center; gap: 4px;
        background: var(--accent-soft); border: 1.5px solid var(--accent);
        border-radius: 999px; padding: 6px 16px;
        font-size: 0.88rem; font-weight: 600; color: var(--accent2);
        cursor: pointer; font-family: inherit;
        transition: background 0.15s, color 0.15s;
      }
      .club-nav-pill:hover { background: var(--accent); color: #fff; }

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

      <!-- ── Club quick-nav ─────────────────────────────── -->
      <div class="panel" style="margin-bottom:20px;">
        <h2 style="margin-bottom:6px;">Clubs</h2>
        <p class="small" style="margin:0 0 12px">Select a club for carry trend, forecast, dispersion &amp; session breakdown.</p>
        <div id="club-nav-pills" style="display:flex;flex-wrap:wrap;gap:8px;"></div>
      </div>

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
          <h2>Avg offline by club</h2>
          <p class="small" style="margin:0 0 10px">Average lateral miss per club. Green = within 10 yds &nbsp;|&nbsp; Amber = 10+ yds. Full shot-by-shot scatter is on each club's detail page.</p>
          <div class="chart-canvas" style="height:200px;">
            <canvas id="offlineSummaryChart"></canvas>
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
          <p class="small" style="margin:0 0 10px">Click any club name to open its detail page — carry trend, dispersion, forecast &amp; more.</p>
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
          <div class="sessions-list" id="sessions"></div>
          <div class="session-pagination" id="sessions-pagination" style="display:none;">
            <button id="sessions-prev">&#8592; Prev</button>
            <span class="session-pagination-info" id="sessions-page-info"></span>
            <button id="sessions-next">Next &#8594;</button>
          </div>
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

      <!-- ── Club detail panel ────────────────────────── -->
      <div class="club-detail" id="club-detail">
        <button class="back-btn" id="club-back-btn">&#8592; Back to overview</button>
        <div class="panel">
          <div class="club-detail-header">
            <span class="club-detail-name" id="club-detail-name"></span>
            <span class="velocity-badge" id="club-velocity-badge"></span>
          </div>
          <div class="club-stat-strip" id="club-stat-strip"></div>
          <div id="club-prediction-callout"></div>
        </div>
        <div class="grid charts" style="margin-top:16px;">
          <div class="panel chart-wrap">
            <h2>Carry trend &amp; forecast</h2>
            <div class="chart-canvas"><canvas id="clubCarryChart"></canvas></div>
            <div class="forecast-callout" id="club-carry-callout" style="display:none;"></div>
          </div>
          <div class="panel chart-wrap">
            <h2>Smash factor vs potential</h2>
            <div class="chart-canvas"><canvas id="clubSmashChart"></canvas></div>
          </div>
          <div class="panel chart-wrap" style="grid-column: 1 / -1;">
            <h2>Shot dispersion</h2>
            <p class="small" style="margin:0 0 10px">Most recent session = full opacity. Older sessions fade. Triangles = outliers.</p>
            <div class="chart-canvas tall"><canvas id="clubDispersionChart"></canvas></div>
          </div>
        </div>
        <div class="panel" style="margin-top:16px;">
          <h2>Session breakdown</h2>
          <div style="overflow-x:auto;">
            <table>
              <thead><tr>
                <th>Date</th><th>Shots</th><th>Avg carry</th><th>Smash</th><th>Offline</th><th>Consistency</th>
              </tr></thead>
              <tbody id="club-session-table-body"></tbody>
            </table>
          </div>
        </div>
      </div>

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
              backgroundColor: "rgba(64, 129, 20, 0.65)",
              borderColor: "#408114",
              borderWidth: 1,
              order: 2,
            },
            {
              type: "line",
              label: "Personal ceiling (90th %ile)",
              data: smashPotential,
              borderColor: "#1B7114",
              backgroundColor: "transparent",
              borderWidth: 2,
              pointRadius: 5,
              pointBackgroundColor: "#1B7114",
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
              backgroundColor: "rgba(64, 129, 20, 0.6)",
            },
            {
              label: "Consistency score",
              data: data.charts.clubs.consistency_score,
              backgroundColor: "rgba(27, 113, 20, 0.6)",
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
              backgroundColor: bagIsBunched.map((b) => b ? "rgba(30, 52, 10, 0.45)" : "rgba(64, 129, 20, 0.35)"),
              borderColor: bagIsBunched.map((b) => b ? "#1E340A" : "#408114"),
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

      // ── Avg offline summary bar (replaces dashboard scatter) ─────────────
      (() => {
        const sorted = [...data.clubs]
          .filter((c) => c.avg_total_deviation_distance != null || c.avg_carry_deviation_distance != null)
          .sort((a, b) => {
            const va = Math.abs(a.avg_total_deviation_distance ?? a.avg_carry_deviation_distance ?? 0);
            const vb = Math.abs(b.avg_total_deviation_distance ?? b.avg_carry_deviation_distance ?? 0);
            return vb - va;
          });
        const labels = sorted.map((c) => c.club_label);
        const vals = sorted.map((c) => parseFloat(Math.abs(c.avg_total_deviation_distance ?? c.avg_carry_deviation_distance ?? 0).toFixed(1)));
        createChart("offlineSummaryChart", {
          type: "bar",
          data: {
            labels,
            datasets: [{
              label: "Avg offline (yds)",
              data: vals,
              backgroundColor: vals.map((v) => v >= 10 ? "rgba(30,52,10,0.7)" : "rgba(64,129,20,0.7)"),
              borderColor: vals.map((v) => v >= 10 ? "#1E340A" : "#408114"),
              borderWidth: 1.5,
            }],
          },
          options: {
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,
            scales: { x: { beginAtZero: true, title: { display: true, text: "Absolute offline (yds)" } } },
            plugins: { legend: { display: false } },
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
          if (score >= 75) return { bg: "rgba(27, 113, 20, 0.18)", text: "#1B7114" };
          if (score >= 50) return { bg: "rgba(77, 110, 36, 0.18)", text: "#4D6E24" };
          return { bg: "rgba(30, 52, 10, 0.15)", text: "#1E340A" };
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

      // ── Club nav pills ────────────────────────────────────────────────
      const clubNavPills = document.getElementById("club-nav-pills");
      data.clubs.forEach((club) => {
        const pill = document.createElement("button");
        pill.className = "club-nav-pill";
        pill.textContent = club.club_label;
        pill.dataset.club = club.club_label;
        clubNavPills.appendChild(pill);
      });
      clubNavPills.addEventListener("click", (e) => {
        const pill = e.target.closest(".club-nav-pill");
        if (pill) showClubDetail(pill.dataset.club);
      });

      // ── Club summary table ────────────────────────────────────────────
      const clubSummaryBody = document.getElementById("club-summary-body");
      data.clubs.forEach((club) => {
        const row = document.createElement("tr");
        const offline = club.avg_total_deviation_distance ?? club.avg_carry_deviation_distance;
        // First cell: button built with DOM methods (no untrusted innerHTML)
        const nameTd = document.createElement("td");
        const linkBtn = document.createElement("button");
        linkBtn.className = "club-link-btn";
        linkBtn.dataset.club = club.club_label;
        linkBtn.textContent = club.club_label;
        linkBtn.appendChild(document.createTextNode(" ↗"));
        nameTd.appendChild(linkBtn);
        row.appendChild(nameTd);
        // Remaining cells are numeric/formatted values (no user input)
        const restTd = document.createElement("tbody");
        restTd.innerHTML = `
          <tr>
          <td>${club.shot_count}</td>
          <td>${number(club.avg_carry_distance, 1, " yds")}</td>
          <td>${number(club.avg_smash_factor, 2)}</td>
          <td>${number(offline, 1, " yds")}</td>
          <td>${number(club.consistency_score, 1)}</td>
          <td>${number(club.outlier_rate, 0, "%")}</td>
          </tr>
        `;
        const cells = restTd.rows[0].cells;
        for (let i = 0; i < cells.length; i++) row.appendChild(cells[0]);
        clubSummaryBody.appendChild(row);
      });
      document.getElementById("club-summary-body").addEventListener("click", (e) => {
        const btn = e.target.closest(".club-link-btn");
        if (btn) showClubDetail(btn.dataset.club);
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
            const ratingVal = session.session_rating;
            const ratingTrend = session.session_rating_trend;
            const ratingColor = ratingVal == null ? "var(--muted)"
              : ratingVal >= 70 ? "var(--good)"
              : ratingVal >= 50 ? "var(--muted)"
              : "var(--text)";

            const row = document.createElement("div");
            row.className = "session-row";

            const datEl = document.createElement("div");
            datEl.className = "session-row-date";
            datEl.textContent = dateStr;

            const ratEl = document.createElement("div");
            ratEl.className = "session-row-rating";
            const ratLbl = document.createElement("span");
            ratLbl.className = "session-row-stat-lbl";
            ratLbl.textContent = "Rating";
            const ratVal = document.createElement("span");
            ratVal.className = "session-row-rating-val";
            ratVal.style.color = ratingColor;
            ratVal.textContent = ratingVal != null ? ratingVal.toFixed(0) : "—";
            ratEl.appendChild(ratLbl);
            ratEl.appendChild(ratVal);
            if (ratingTrend != null && Math.abs(ratingTrend) > 0.05) {
              const trendEl = document.createElement("span");
              trendEl.style.fontSize = "0.8rem";
              trendEl.style.fontWeight = "600";
              trendEl.style.color = ratingTrend > 0 ? "var(--good)" : "var(--muted)";
              trendEl.textContent = (ratingTrend > 0 ? "▲ " : "▼ ") + Math.abs(ratingTrend).toFixed(1);
              ratEl.appendChild(trendEl);
            }

            row.appendChild(datEl);
            row.appendChild(ratEl);
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
          const label = item.severity_label || (item.severity >= 60 ? "High" : item.severity >= 30 ? "Medium" : "Low");
          const recCls = label === "High" ? "rec-high" : label === "Medium" ? "rec-med" : "rec-low";
          const badgeCls = label === "High" ? "badge-high" : label === "Medium" ? "badge-med" : "badge-low";
          const div = document.createElement("div");
          div.className = `recommendation ${recCls}`;
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
          div.appendChild(header);
          div.appendChild(body);
          div.appendChild(meta);
          recommendations.appendChild(div);
        });
      }

      if (!sessionTrendChart || !clubBarChart || !missDirectionChart) {
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

      // ── Club detail navigation ────────────────────────────────────────────
      const clubDetailPanel = document.getElementById("club-detail");
      const dashboardChildren = Array.from(document.getElementById("tab-dashboard").children)
        .filter((el) => el.id !== "club-detail");

      let _clubCarryChart = null, _clubSmashChart = null, _clubDispChart = null;

      function renderClubDetail(clubLabel) {
        const club = data.clubs.find((c) => c.club_label === clubLabel);
        if (!club) return;
        [_clubCarryChart, _clubSmashChart, _clubDispChart].forEach((ch) => { if (ch) ch.destroy(); });

        // Header
        document.getElementById("club-detail-name").textContent = clubLabel;
        const velBadge = document.getElementById("club-velocity-badge");
        const vel = club.improvement_velocity || "Holding steady";
        velBadge.textContent = vel;
        velBadge.className = "velocity-badge " + (vel === "Most improved" ? "vel-improved" : vel === "Work needed" ? "vel-needed" : "vel-steady");

        // Stat strip
        const strip = document.getElementById("club-stat-strip");
        strip.innerHTML = "";
        const offline = club.avg_total_deviation_distance ?? club.avg_carry_deviation_distance;
        [
          ["Avg carry", number(club.avg_carry_distance, 1, " yds")],
          ["Smash factor", number(club.avg_smash_factor, 2)],
          ["Consistency", number(club.consistency_score, 1)],
          ["Avg offline", number(offline, 1, " yds")],
          ["Outlier rate", number(club.outlier_rate, 0, "%")],
          ["Shots", club.shot_count],
        ].forEach(([lbl, val]) => {
          const card = document.createElement("div");
          card.className = "club-stat-card";
          const v = document.createElement("div");
          v.className = "stat-value";
          v.textContent = val;
          const l = document.createElement("div");
          l.className = "stat-label";
          l.textContent = lbl;
          card.appendChild(v);
          card.appendChild(l);
          strip.appendChild(card);
        });
        if (club.potential_gap_pct != null) {
          const gapCard = document.createElement("div");
          gapCard.className = "club-stat-card";
          const gv = document.createElement("div");
          gv.className = "stat-value";
          gv.textContent = club.potential_gap_pct.toFixed(0) + "%";
          const gl = document.createElement("div");
          gl.className = "stat-label";
          gl.textContent = "Strike potential";
          const barWrap = document.createElement("div");
          barWrap.className = "gap-bar-wrap";
          const bar = document.createElement("div");
          bar.className = "gap-bar";
          bar.style.width = Math.min(100, club.potential_gap_pct) + "%";
          barWrap.appendChild(bar);
          gapCard.appendChild(gv);
          gapCard.appendChild(gl);
          gapCard.appendChild(barWrap);
          strip.appendChild(gapCard);
        }

        // Prediction callout
        const predCallout = document.getElementById("club-prediction-callout");
        predCallout.innerHTML = "";
        const clubFc = ((data.forecasts || {}).per_club || {})[clubLabel];
        if (clubFc && clubFc.carry) {
          const band = clubFc.carry.confidence_band[0];
          const callout = document.createElement("div");
          callout.className = "forecast-callout";
          callout.style.marginTop = "12px";
          const strong = document.createElement("strong");
          strong.textContent = "Next session: ";
          callout.appendChild(strong);
          callout.appendChild(document.createTextNode(
            `carry forecast ${band[0]}–${band[1]} yds (trending ${clubFc.carry.slope >= 0 ? "+" : ""}${clubFc.carry.slope.toFixed(1)} yds/session)`
          ));
          predCallout.appendChild(callout);
        }

        // Carry trend + forecast chart
        const sessionDates = [];
        const perSessionCarry = [];
        data.sessions.forEach((s) => {
          const cs = (s.club_summaries || []).find((c) => c.club_label === clubLabel);
          if (!cs) return;
          sessionDates.push(
            s.session_timestamp
              ? new Date(s.session_timestamp).toLocaleDateString(undefined, { month: "short", day: "numeric" })
              : s.source_file.slice(0, 10)
          );
          perSessionCarry.push(cs.avg_carry_distance != null ? parseFloat(cs.avg_carry_distance.toFixed(1)) : null);
        });

        let carryLabels = [...sessionDates];
        const carryDatasets = [{
          label: "Avg carry (yds)",
          data: [...perSessionCarry],
          borderColor: "#408114",
          backgroundColor: "rgba(64,129,20,0.12)",
          tension: 0.3,
          pointRadius: 5,
        }];

        if (clubFc && clubFc.carry) {
          carryLabels = [...sessionDates, "+1", "+2", "+3"];
          const nullPad = sessionDates.map(() => null);
          const lastVal = perSessionCarry[perSessionCarry.length - 1];
          carryDatasets[0].data = [...perSessionCarry, null, null, null];
          carryDatasets.push({
            label: "Forecast",
            data: [...nullPad.slice(0, -1), lastVal, ...clubFc.carry.predictions],
            borderColor: "rgba(64,129,20,0.55)",
            backgroundColor: "transparent",
            borderDash: [6, 4],
            borderWidth: 2,
            pointRadius: [...nullPad.slice(0, -1).map(() => 0), 5, 3, 3, 3],
            tension: 0,
          });
          const prevFc = ((data.previous_forecasts || {}).per_club || {})[clubLabel];
          if (prevFc && prevFc.carry) {
            carryDatasets.push({
              label: "Previous forecast",
              data: [...nullPad.slice(0, -1), prevFc.carry.last_actual, ...prevFc.carry.predictions.slice(0, 3)],
              borderColor: "rgba(77,110,36,0.35)",
              backgroundColor: "transparent",
              borderDash: [3, 4],
              borderWidth: 1.5,
              pointRadius: 0,
              tension: 0,
            });
          }
          const cc = document.getElementById("club-carry-callout");
          cc.style.display = "block";
          const strong = document.createElement("strong");
          strong.textContent = "Forecast: ";
          cc.innerHTML = "";
          cc.appendChild(strong);
          cc.appendChild(document.createTextNode(
            `trending ${clubFc.carry.slope >= 0 ? "+" : ""}${clubFc.carry.slope.toFixed(1)} yds/session — projected ${clubFc.carry.predictions[2]} yds in 3 sessions`
          ));
        } else {
          document.getElementById("club-carry-callout").style.display = "none";
        }

        _clubCarryChart = createChart("clubCarryChart", {
          type: "line",
          data: { labels: carryLabels, datasets: carryDatasets },
          options: {
            responsive: true, maintainAspectRatio: false,
            interaction: { mode: "index", intersect: false },
            scales: { y: { beginAtZero: false, title: { display: true, text: "Carry (yds)" } } },
          },
        });

        // Smash vs potential chart
        const smashVals = sessionDates.map((_, i) => {
          const s = data.sessions[i];
          const cs = s && (s.club_summaries || []).find((c) => c.club_label === clubLabel);
          return cs && cs.avg_smash_factor != null ? parseFloat(cs.avg_smash_factor.toFixed(3)) : null;
        });
        _clubSmashChart = createChart("clubSmashChart", {
          type: "bar",
          data: {
            labels: sessionDates,
            datasets: [
              { type: "bar", label: "Avg smash factor", data: smashVals, backgroundColor: "rgba(64,129,20,0.65)", borderColor: "#408114", borderWidth: 1, order: 2 },
              { type: "line", label: "Personal ceiling (90th %ile)", data: sessionDates.map(() => club.potential_smash_factor), borderColor: "#1B7114", backgroundColor: "transparent", borderWidth: 2, pointRadius: 0, tension: 0, order: 1 },
            ],
          },
          options: {
            responsive: true, maintainAspectRatio: false,
            scales: { y: { beginAtZero: false, min: 0.9, title: { display: true, text: "Smash factor" } } },
            plugins: { legend: { position: "top" } },
          },
        });

        // Dispersion scatter with session-age opacity fade
        const totalSess = data.sessions.length;
        const ageOpacity = (age) => age === 0 ? 1.0 : age === 1 ? 0.55 : age === 2 ? 0.25 : 0.12;
        const dispBySession = {};
        (data.charts.dispersion || []).forEach((pt) => {
          if (pt.club !== clubLabel) return;
          const idx = pt.session_index ?? 0;
          (dispBySession[idx] = dispBySession[idx] || []).push(pt);
        });
        const dispDatasets = Object.entries(dispBySession).map(([idxStr, points]) => {
          const idx = parseInt(idxStr, 10);
          const age = totalSess - 1 - idx;
          const hex = Math.round(ageOpacity(age) * 255).toString(16).padStart(2, "0");
          const sessDate = data.sessions[idx]
            ? new Date(data.sessions[idx].session_timestamp || "").toLocaleDateString(undefined, { month: "short", day: "numeric" })
            : `Session ${idx + 1}`;
          return {
            label: age === 0 ? `${sessDate} (latest)` : sessDate,
            data: points.map((p) => ({ x: p.x, y: p.y })),
            pointRadius: points.map((p) => (p.outlier ? 6 : 4)),
            pointStyle: points.map((p) => (p.outlier ? "triangle" : "circle")),
            pointHoverRadius: 7,
            borderWidth: 0,
            backgroundColor: points.map((p) => (p.outlier ? "#1E340A" : "#408114") + hex),
          };
        });
        _clubDispChart = createChart("clubDispersionChart", {
          type: "scatter",
          data: { datasets: dispDatasets },
          options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { position: "top" } },
            scales: {
              x: { type: "linear", title: { display: true, text: "Offline / deviation (yds)" } },
              y: { type: "linear", title: { display: true, text: "Carry distance (yds)" } },
            },
          },
        });

        // Session breakdown table
        const tbody = document.getElementById("club-session-table-body");
        tbody.innerHTML = "";
        data.sessions.forEach((s) => {
          const cs = (s.club_summaries || []).find((c) => c.club_label === clubLabel);
          if (!cs) return;
          const dateStr = s.session_timestamp
            ? new Date(s.session_timestamp).toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" })
            : s.source_file;
          const offlineVal = cs.avg_total_deviation_distance ?? cs.avg_carry_deviation_distance;
          const row = document.createElement("tr");
          ["", "", "", "", "", ""].forEach(() => row.insertCell());
          row.cells[0].textContent = dateStr;
          row.cells[1].textContent = cs.shot_count;
          row.cells[2].textContent = number(cs.avg_carry_distance, 1, " yds");
          row.cells[3].textContent = number(cs.avg_smash_factor, 2);
          row.cells[4].textContent = number(offlineVal, 1, " yds");
          row.cells[5].textContent = number(cs.consistency_score, 1);
          tbody.appendChild(row);
        });
      }

      function showClubDetail(clubLabel) {
        dashboardChildren.forEach((el) => { el.style.display = "none"; });
        clubDetailPanel.classList.add("active");
        renderClubDetail(clubLabel);
      }

      function hideClubDetail() {
        dashboardChildren.forEach((el) => { el.style.display = ""; });
        clubDetailPanel.classList.remove("active");
      }

      document.getElementById("club-back-btn").addEventListener("click", hideClubDetail);
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
