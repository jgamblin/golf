# Golf Dashboard Redesign — Design Spec

**Date:** 2026-05-09  
**Project:** `golf` — personal Garmin R10 range analytics  
**Scope:** Visual redesign + per-club detail pages + rolling ML forecast  

---

## 1. Hero & Typography

### Headline
Replace the current "Golf range analytics" title and dark badge with a personality-driven hero:

- **Title font:** Playfair Display (Google Fonts, weights 700 + 900 + italic) loaded via CDN
- **Body font:** Inter (unchanged)
- **Headline text:** `Bad at golf.` (regular weight) + `Great` (italic, `#408114`) + ` at data.` 
- **Page `<title>`:** `Bad at golf. Great at data. — Jerry Gamblin`
- **Badge:** Remove "Range Performance Lab" pill; replace with small eyebrow line: `Jerry Gamblin · Range Performance Lab` in Inter uppercase muted text

### Hero subtext
Self-deprecating, shareable copy (generated dynamically from data):

> Tracking every swing, every miss, and every small win with a Garmin R10 and way too much Python. The handicap isn't improving as fast as the analytics.

### Hero stat row
Four inline stats below the subtext, pulled from `data.overview` (existing fields only):
- Sessions · Shots tracked · Clubs · Avg consistency score

### Meta line
`Last session <date> · Auto-generated from Garmin R10 CSV exports`  
GitHub link retained in the header row.

---

## 2. Light Color Palette

Replace all dark-mode CSS variables with the user's Adobe Color golf palette:

| Variable | Old (dark) | New (light) |
|---|---|---|
| `--bg` | `#081018` | `#F2F2F0` |
| `--panel` | `#0f1d2c` | `#ffffff` |
| `--text` | `#f4f7fb` | `#1E340A` |
| `--muted` | `#9fb2c8` | `#4D6E24` |
| `--accent` | `#57b5ff` | `#408114` |
| `--accent2` *(new)* | — | `#1B7114` |
| `--border` | `rgba(255,255,255,0.08)` | `rgba(30,52,10,0.12)` |
| `--good` | `#5fd18b` | `#1B7114` |
| `--warn` | `#ffb454` | `#b45309` (amber, used sparingly) |
| `--bad` | `#ff7b72` | *(removed — see recommendations)* |

Remove `color-scheme: dark` from `:root`. Update `body` background gradient to use `#F2F2F0` → `#ebebea`.

### Chart colors
Rekey `COLORS` array in the JS to golf-green palette:
```js
const COLORS = ["#408114","#1B7114","#4D6E24","#b45309","#6b7280","#0369a1","#7c3aed","#0d9488"];
```

---

## 3. Per-Club Click-Through Detail Pages

### Navigation
- Club names in the **Club summary table** render as `<button>` links styled `color: #1B7114; text-decoration: underline; text-underline-offset: 3px`
- Clicking a club name hides `#tab-dashboard` content and shows a `#club-detail` panel injected into the same tab container
- A `← Back to overview` button at the top of the detail panel restores the dashboard view
- No page reload — pure JS show/hide

### Club detail panel contents (in order)
1. **Club header** — club name (Playfair Display), shot count, improvement velocity badge (see §5)
2. **Key stat strip** — avg carry, smash factor, consistency score, avg offline, outlier rate, potential gap % (see §5)
3. **Carry trend + forecast chart** — session history (solid line) + 3-session forecast (dashed, see §4)
4. **Dispersion scatter** — shot-by-shot scatter for this club only, with session-age opacity fade (see below)
5. **Smash vs potential chart** — existing smash headroom chart filtered to this club across sessions
6. **Session breakdown table** — per-session: date, shots, avg carry, smash, offline, consistency score

### Dispersion scatter — session-age opacity
Each session's shots rendered as a separate dataset. Opacity assigned by recency:
- Most recent session: `1.0` (full opacity)
- Second most recent: `0.55`
- Third most recent: `0.25`
- Older: `0.12`

Point radius: 4px recent, 3px older. Outlier shots rendered as triangles regardless of age.

---

## 4. Rolling ML Forecast

### Overview
On every `golf build`, linear regression runs per club per metric (carry distance, smash factor) over all available sessions. Produces a 3-session rolling lookahead that always extends from the latest session.

### Python side — `analytics.py` additions
New function `build_forecasts(session_summaries, club_summaries)` returns:

```python
{
  "generated_at": "<iso timestamp>",
  "per_club": {
    "<club_label>": {
      "carry": {
        "slope": float,          # yds per session
        "last_actual": float,    # last session avg carry
        "predictions": [float, float, float],   # next 3 sessions
        "confidence_band": [[lo, hi], [lo, hi], [lo, hi]]  # ±1 SE
      },
      "smash": { ... same shape ... }
    }
  }
}
```

Minimum 3 sessions required to produce a forecast; clubs with fewer sessions omitted.

### Persistence — `predictions.json`
Written alongside `site-data.js` on each build. On the **next** build, the previous file is read first and merged into `site-data.js` as `data.previous_forecasts` so the frontend can draw the old forecast line and compare it to actuals.

### Frontend — forecast line rendering
On the **session trend chart** (dashboard) and **carry trend chart** (club detail):
- Solid line = actual session history (unchanged)
- Dashed line = forecast continuation, color `rgba(64,129,20,0.6)`, `stroke-dasharray: [6,4]`
- Shaded confidence band = dataset with `fill: true`, `backgroundColor: rgba(64,129,20,0.07)`
- Prediction callout beneath chart: *"Trending +2.1 yds/session — forecast 152 yds in 3 sessions"*

When `data.previous_forecasts` exists:
- Old forecast draws as a second dashed line in `rgba(77,110,36,0.35)`
- Actual results that landed in the forecast window draw over it in solid green
- No extra UI needed — the overlap tells the story visually

### Forecast labels on x-axis
Forecast x-axis labels rendered as `+1`, `+2`, `+3` in muted color to distinguish from real session dates.

---

## 5. Per-Club ML Signals

### Potential gap meter
Displayed in the club detail key stat strip:

> **Strike potential: 84%** ▓▓▓▓▓▓▓░░░

Calculated as `(avg_smash_factor / potential_smash_factor) * 100`. Shown as a small inline progress bar + percentage. Copy: *"You're hitting 84% of your personal ceiling for this club."*

### Improvement velocity badge
Calculated from the slope of the last 3 sessions' avg carry for the club:
- Slope > +1.5 yds/session → `Most improved` badge (`#1B7114` bg, white text)
- Slope between −1.5 and +1.5 → `Holding steady` badge (`#4D6E24` bg, white text)
- Slope < −1.5 → `Work needed` badge (`#b45309` bg, white text)

Badge appears in the club detail header and in the club summary table as a small pill.

### Next-session carry prediction
Single sentence in the club detail header:
> *"Based on your trend, expect 145–152 yds next session."*

Derived from `predictions.per_club[club].carry.predictions[0]` ± confidence band half-width.

---

## 6. Recommendations Redesign

### No red, no amber for severity
All three severity tiers use the golf green palette:

| Priority | Border + badge color | Background tint |
|---|---|---|
| High | `#1E340A` (dark forest) | `rgba(30,52,10,0.07)` |
| Medium | `#408114` (grass green) | `rgba(64,129,20,0.08)` |
| Low | `#4D6E24` (olive) | `rgba(77,110,36,0.07)` |

Severity badge: small pill (`High` / `Medium` / `Low`) replaces numeric `Severity N` display.

### Language
No "bad", "error", "wrong", or alarming framing. Recommendations read as:
- *"Focus area: …"* not *"Problem: …"*
- *"Opportunity to improve …"* not *"You're missing …"*

The `build_recommendations` function in `analytics.py` gets updated copy strings to match.

---

## 7. Dashboard Dispersion Summary (replaces scatter on main page)

The full scatter chart is removed from the dashboard tab. In its place, a compact **Avg offline by club** horizontal bar chart:
- One bar per club, sorted by absolute offline distance
- Bar color: `#408114` if avg offline < 10 yds, `#b45309` if ≥ 10 yds
- Error whiskers at ± 1 SD
- Chart height: 200px (vs 420px for the old scatter)

Full shot-by-shot scatter lives only on the per-club detail page.

---

## 8. Implementation Notes

### Files changed
- `src/golf/site.py` — all CSS variables, font imports, hero HTML, recommendation copy, JS chart colors, club link rendering, club detail panel, forecast chart rendering
- `src/golf/analytics.py` — `build_forecasts()`, `build_recommendations()` copy update, `build_analysis()` wiring
- `src/golf/cli.py` — before building: read `output_dir/predictions.json` if it exists and pass as `previous_forecasts` to `build_analysis`; after building: write new `output_dir/predictions.json` from the freshly computed forecasts

### New data in `site-data.js`
```js
window.GOLF_SITE_DATA = {
  ...existing fields...,
  forecasts: { per_club: { ... } },         // current build forecasts
  previous_forecasts: { per_club: { ... } } // from predictions.json of prior build
}
```

### Google Fonts CDN
Add to `<head>`:
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,700&display=swap" rel="stylesheet">
```

### `.gitignore`
Add `.superpowers/` to `.gitignore` so brainstorm session files don't get committed.

---

## Out of Scope
- Mobile-specific layout changes beyond existing responsive grid
- Dark mode toggle
- Multi-player support
- Any changes to the CSV ingest pipeline (`ingest.py`)
