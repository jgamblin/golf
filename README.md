# Golf Range Analytics — Garmin R10 Edition

**[Live dashboard →](https://jgamblin.github.io/golf/)** &nbsp;|&nbsp; **[Source on GitHub →](https://github.com/jgamblin/golf)**

A self-hosted analytics pipeline purpose-built for the **Garmin Approach R10** launch monitor and the **Garmin Golf** app.  Drop your range-session CSVs into `Data/`, run one command, and get a multi-page GitHub Pages dashboard with dispersion maps, gapping analysis, club path infographics, environment context, and personalised practice recommendations — all derived from your own R10 data.

---

## Quick start

```bash
# 1. Install (requires Python 3.11+)
pip install -e .

# 2. Export a session CSV from the Garmin Golf app and drop it into Data/
#    (see "Data Workflow" below)

# 3. Build the dashboard
golf-build build --data-dir Data --output-dir output/site

# 4. Open the dashboard
open output/site/index.html
```

Push to GitHub and GitHub Actions automatically deploys the same output to GitHub Pages on every commit.

---

## Pages

| Page | URL | What's on it |
|---|---|---|
| **Overview** | `index.html` | Session trend, miss-direction chart, session table with pagination |
| **Club Lab** | `clubs.html` | Per-club drilldown with path/face infographic, path cloud scatter, consistency heatmap |
| **Session Replay** | `sessions.html` | Full stat breakdown for every individual session |
| **Gapping** | `gapping.html` | Carry ladder, target-error chart, gapping table with aspirational targets, Progress To Goal slope chart, environment context |
| **Coaching** | `coaching.html` | Ranked recommendations with confidence scores, next-session focus list |
| **Data Quality** | `data-quality.html` | Flagged-shot trends, miss reasons, critical-field coverage |

---

## Data workflow

### Exporting from the Garmin Golf app

1. Open the **Garmin Golf** app on your phone.
2. Tap **Range** → select the session you want to export.
3. Tap the **share / export** icon (top-right corner).
4. Choose **Export CSV** and save the file.
5. Copy the `.csv` file into the **`Data/`** directory at the root of this repo.
6. Run the build command (or push to GitHub to trigger the Actions workflow).

The pipeline accepts **both** export formats the Garmin Golf app produces:

| Export path | Header style | Notes |
|---|---|---|
| Range session | `Date`, `Club Type`, `Ball Speed`, … | Standard format; units row immediately follows headers |
| Activity / round | `Shot Number`, `Club`, `Ball Speed (mph)`, … | May have several metadata rows above the headers; the loader skips them automatically |

> **Tip:** Keep one CSV per session.  The pipeline processes every `.csv` in `Data/` and aggregates trends across all sessions automatically.

---

## Features — mapped to R10 metrics

### Dispersion map & session trend
Plots carry distance and smash factor over time with forecast confidence bands.  Each session is also shown as a sortable row with carry, smash, offline, and outlier-rate stats.

### Consistency score (0 – 100)
A single per-club number derived from four R10 signals:

| R10 metric | What it measures |
|---|---|
| Carry distance CV | Distance repeatability |
| Lateral deviation std dev | Directional control |
| Face-to-path std dev | Clubface delivery consistency |
| Swing tempo CV | Sequencing repeatability |

The weights are calibrated from the *population* of your clubs so the score is comparable across sessions regardless of R10 firmware updates.

### Club Path infographic
Each club's drilldown panel includes a **path/face relationship diagram** — a visual showing your average club path direction, face-to-path angle, and the resulting ball-flight bias.  A scatter chart plots every shot's club path against face-to-path so you can spot patterns and outliers at a glance.

### Gapping analysis & aspirational carry targets
Sorted carry distances across your bag are compared pair-by-pair:

- **Bunching** — clubs within 7 yards of each other, or whose carry SD windows overlap, are flagged.
- **Distance void** — a gap greater than 25 yards suggests a missing club or a loft that needs adjustment.

Carry targets are generated **aspirationally** from a club-type anchor ladder (Driver → woods → hybrids → irons → wedges) so the target always represents a realistic improvement goal rather than a mirror of your current average.  A **Progress To Goal** slope chart shows every club moving from current carry to target carry in a single glance.

### Environment context
Each build captures temperature, humidity, air pressure, and air density from your session data and calculates:

- **Carry vs. temperature slope** — how many yards of carry you gain/lose per °F.
- **Carry vs. air density slope** — the density effect on ball flight across your sessions.

### Potential smash factor
Rather than comparing your smash factor against a generic industry benchmark, the pipeline calculates your **personal 90th-percentile smash factor** for each club from your own historical shots.  The recommendation engine only flags a strike-quality issue when your average falls more than 0.08 below *your own best*.  The benchmark grows as your ball-striking improves.

### Miss direction trend
A session-by-session bar chart showing whether your average lateral miss is trending left or right.

### Practice recommendations
Ranked recommendations on the **Coaching** page, covering:

- Directional bias (`avg_carry_deviation_distance`)
- Clubface control (`face_to_path_stddev`)
- Strike quality (`avg_smash_factor` vs. your personal potential)
- Tempo stability (`tempo_stddev`)
- Outlier rate (anomaly model)
- Distance gapping (bunching and voids)
- Data quality (high flagged-shot rate)

Each recommendation includes a confidence score, confidence reason, and priority explanation so you always know *why* it's ranked where it is.

### Data quality
Per-session flagged-shot rates, missing critical-field counts, suspicious-reading breakdowns, and a doughnut chart of flag reasons — so you can trust the analytics driving your coaching.

---

## Project layout

```
Data/                          ← drop Garmin Golf app CSV exports here
src/golf/
  ingest.py                    ← CSV parsing, unit conversion, zero-shot cleaning
  analytics.py                 ← club/session summaries, targets, recommendations
  ml.py                        ← lightweight anomaly scoring
  site.py                      ← multi-page static dashboard generation
  cli.py                       ← `golf-build` entry point
  config/
    field_aliases.yaml         ← column-name aliases for all supported monitors
                                  (edit here to add new Garmin app column names)
tests/
  test_pipeline.py             ← pipeline integration + unit tests (52 tests)
.github/workflows/             ← GitHub Actions: build + deploy to Pages
```

---

## Dependency management

The project uses **[uv](https://github.com/astral-sh/uv)** and **hatchling**.

```bash
# Install uv (once)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create a virtual environment and install all dependencies
uv sync

# Run the build
uv run golf-build build

# Run tests
uv run pytest tests/ -v

# Add a new dependency
uv add some-package
```

Lockfile (`uv.lock`) is committed so builds are fully reproducible.

---

## Adding support for new Garmin column names

Garmin Golf app updates sometimes rename or reformat column headers.  No Python changes are needed — just add the new mapping to `src/golf/config/field_aliases.yaml`:

```yaml
aliases:
  # ...existing entries...
  "New Column Name (units)": internal_field_name
```

Run `pytest tests/ -v` to verify the change doesn't break existing test data.

---

## Recommendation model

All recommendations are explainable and derived from your R10 data — no black-box models:

| Signal | Threshold | Recommendation |
|---|---|---|
| Avg lateral deviation | ≥ 10 yds | Reduce left/right miss |
| Face-to-path std dev | ≥ 6° | Tighten clubface variance |
| Avg face-to-path | ≥ 5° | Neutralise face bias |
| Smash vs. personal 90th-pct | gap ≥ 0.08 | Improve centred contact |
| Tempo std dev | ≥ 0.35 | Stabilise tempo |
| Outlier rate | ≥ 25% | Trim high-variance swings |
| Carry gap (bunching) | < 7 yds or overlap | Check bag setup |
| Carry gap (void) | > 25 yds | Consider adding a club |
| Flagged shot rate | ≥ 10% | Review R10 placement / lighting |

---

## FAQ

**Q: My R10 export has extra rows at the top before the column headers — will it parse?**
A: Yes. The loader scans every row and identifies the header row by looking for known column names and Garmin-specific anchor keywords (`Shot Number`, `Club`, `Date`, etc.).  Metadata preamble rows are skipped automatically.

**Q: Some shots show 0 for ball speed in the app but aren't in my analytics — is that right?**
A: Yes.  Zero ball-speed shots are phantom detections (the R10 detected your swing but didn't track the ball).  The pipeline nulls them out and excludes them from averages to prevent skewing your stats.

**Q: Can I use this with a different launch monitor?**
A: Yes.  Trackman 4, Rapsodo MLM2, SkyTrak, and FlightScope/Mevo+ are all supported via the same `field_aliases.yaml` config.


---

## Quick start

```bash
# 1. Install (requires Python 3.11+)
pip install -e .

# 2. Export a session CSV from the Garmin Golf app and drop it into Data/
#    (see "Data Workflow" below)

# 3. Build the dashboard
golf-build build --data-dir Data --output-dir output/site

# 4. Open the dashboard
open output/site/index.html
```

Push to GitHub and GitHub Actions automatically deploys the same output to GitHub Pages on every commit.

---

## Data workflow

### Exporting from the Garmin Golf app

1. Open the **Garmin Golf** app on your phone.
2. Tap **Range** → select the session you want to export.
3. Tap the **share / export** icon (top-right corner).
4. Choose **Export CSV** and save the file.
5. Copy the `.csv` file into the **`Data/`** directory at the root of this repo.
6. Run the build command (or push to GitHub to trigger the Actions workflow).

The pipeline accepts **both** export formats the Garmin Golf app produces:

| Export path | Header style | Notes |
|---|---|---|
| Range session | `Date`, `Club Type`, `Ball Speed`, … | Standard format; units row immediately follows headers |
| Activity / round | `Shot Number`, `Club`, `Ball Speed (mph)`, … | May have several metadata rows above the headers; the loader skips them automatically |

> **Tip:** Keep one CSV per session.  The pipeline processes every `.csv` in `Data/` and aggregates trends across all sessions automatically.

---

## Features — mapped to R10 metrics

### Dispersion map
Plots every shot's carry distance vs. lateral offline deviation on an interactive scatter chart.  Each club gets its own colour and a toggle button so you can isolate or hide specific clubs.  Outlier shots (flagged by the anomaly model) are visually differentiated.

### Consistency score (0 – 100)
A single per-club number derived from four R10 signals:

| R10 metric | What it measures |
|---|---|
| Carry distance CV | Distance repeatability |
| Lateral deviation std dev | Directional control |
| Face-to-path std dev | Clubface delivery consistency |
| Swing tempo CV | Sequencing repeatability |

The weights are calibrated from the *population* of your clubs so the score is comparable across sessions and clubs regardless of R10 firmware updates.

### Potential smash factor
Rather than comparing your smash factor against a generic industry benchmark, the pipeline calculates your **personal 90th-percentile smash factor** for each club from your own historical R10 shots.  The recommendation engine only flags a strike-quality issue when your average falls more than 0.08 below *your own best*.  This makes the benchmark grow as your ball-striking improves.

### Gapping analysis
Sorted carry distances across your bag are compared pair-by-pair:

- **Bunching** — clubs within 7 yards of each other, or whose carry standard-deviation windows overlap, are flagged.  This is a common R10 finding when a player carries two similarly-lofted wedges or has inconsistent contact with short irons.
- **Distance void** — a gap greater than 25 yards between adjacent clubs suggests a missing club or a loft that needs adjustment.

### Miss direction trend
A session-by-session bar chart showing whether your average lateral miss is trending left or right over time.  Red bars = right miss, blue bars = left miss.

### Zero-shot detection
The R10 occasionally saves a phantom shot (swing detected, ball not tracked) with `ball_speed = 0`.  The pipeline automatically nulls these values, excludes them from averages, and flags the session if more than 10% of shots are affected — prompting you to check sensor placement and lighting.

### Practice recommendations
Up to eight ranked recommendations per build, covering:

- Directional bias (`avg_carry_deviation_distance`)
- Clubface control (`face_to_path_stddev`)
- Strike quality (`avg_smash_factor` vs. your personal potential)
- Tempo stability (`tempo_stddev`)
- Outlier rate (anomaly model)
- Distance gapping (bunching and voids)
- Data quality (high flagged-shot rate)

---

## Project layout

```
Data/                          ← drop Garmin Golf app CSV exports here
src/golf/
  ingest.py                    ← CSV parsing, unit conversion, zero-shot cleaning
  analytics.py                 ← club/session summaries and recommendations
  ml.py                        ← lightweight anomaly scoring
  site.py                      ← static dashboard generation
  cli.py                       ← `golf-build` entry point
  config/
    field_aliases.yaml         ← column-name aliases for all supported monitors
                                  (edit here to add new Garmin app column names)
tests/
  test_pipeline.py             ← pipeline integration + unit tests
.github/workflows/             ← GitHub Actions: build + deploy to Pages
```

---

## Dependency management

The project uses **[uv](https://github.com/astral-sh/uv)** and **hatchling** (migrated from setuptools).

```bash
# Install uv (once)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create a virtual environment and install all dependencies
uv sync

# Run the build
uv run golf-build build

# Run tests
uv run pytest tests/ -v

# Add a new dependency
uv add some-package

# Add a dev-only dependency
uv add --dev some-dev-package
```

Lockfile (`uv.lock`) is committed so builds are fully reproducible.

---

## Adding support for new Garmin column names

Garmin Golf app updates sometimes rename or reformat column headers.  No Python changes are needed — just add the new mapping to `src/golf/config/field_aliases.yaml` under the Garmin section:

```yaml
aliases:
  # ...existing entries...
  "New Column Name (units)": internal_field_name
```

Run `pytest tests/ -v` to verify the change doesn't break existing test data.

---

## Recommendation model

All recommendations are explainable and derived from your R10 data — no black-box models:

| Signal | Threshold | Recommendation |
|---|---|---|
| Avg lateral deviation | ≥ 10 yds | Reduce left/right miss |
| Face-to-path std dev | ≥ 6° | Tighten clubface variance |
| Avg face-to-path | ≥ 5° | Neutralise face bias |
| Smash vs. personal 90th-pct | gap ≥ 0.08 | Improve centred contact |
| Tempo std dev | ≥ 0.35 | Stabilise tempo |
| Outlier rate | ≥ 25% | Trim high-variance swings |
| Carry gap (bunching) | < 7 yds or overlap | Check bag setup |
| Carry gap (void) | > 25 yds | Consider adding a club |
| Flagged shot rate | ≥ 10% | Review R10 placement / lighting |

---

## FAQ

**Q: My R10 export has extra rows at the top before the column headers — will it parse?**
A: Yes. The loader scans every row and identifies the header row by looking for known column names and Garmin-specific anchor keywords (`Shot Number`, `Club`, `Date`, etc.).  Metadata preamble rows are skipped automatically.

**Q: Some shots show 0 for ball speed in the app but aren't in my analytics — is that right?**
A: Yes.  Zero ball-speed shots are phantom detections (the R10 detected your swing but didn't track the ball).  The pipeline nulls them out and excludes them from averages to prevent skewing your stats.

**Q: Can I use this with a different launch monitor?**
A: Yes.  Trackman 4, Rapsodo MLM2, SkyTrak, and FlightScope/Mevo+ are all supported via the same `field_aliases.yaml` config.

