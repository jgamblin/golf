# Golf Dashboard Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the golf dashboard with a light green palette, "Bad at golf. Great at data." hero, per-club detail pages with click-through navigation, rolling 3-session ML forecasts with prediction-vs-actual comparison, and all-green coaching recommendations.

**Architecture:** All frontend lives in `src/golf/site.py` as one large `render_html()` string. Python analytics in `src/golf/analytics.py`; orchestration in `src/golf/cli.py`. New data flow: `build_forecasts()` produces `analysis["forecasts"]` which is embedded in `window.GOLF_SITE_DATA` and consumed by chart JS. Forecasts persist between builds via `output/site/predictions.json` so previous predictions can be drawn over actuals.

**Tech Stack:** Python 3.11+ (`statistics.linear_regression`), Chart.js 4.4.3 (existing), Google Fonts Playfair Display (CDN), vanilla JS/HTML/CSS (no new dependencies).

**Security note:** The existing codebase uses `innerHTML` throughout to render data from the user's own CSV files (not external user input). New code follows the same pattern. Club labels used in DOM operations are set via `data-club` attributes and read back with `dataset.club` — never injected into event handler strings — to avoid XSS.

**Run tests with:** `python -m pytest tests/ -v`

---

## File Map

| File | Changes |
|---|---|
| `src/golf/analytics.py` | Add `_linear_forecast()`, `build_forecasts()`, `_club_velocity()`, `potential_gap_pct()`, `_severity_label()`; update `build_recommendations()`, `chart_payload()`, `build_analysis()` |
| `src/golf/cli.py` | Read `predictions.json` before build; write it after |
| `src/golf/site.py` | All CSS, HTML, JS: palette, hero, charts, club nav, detail panel |
| `tests/test_pipeline.py` | Tests for all new Python functions |
| `.gitignore` | Add `.superpowers/` |

---

## Task 1: Python — `build_forecasts()` + dispersion session index + club enrichment fields

**Files:**
- Modify: `src/golf/analytics.py`
- Test: `tests/test_pipeline.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_pipeline.py` (import block at top already imports from `golf.analytics`):

```python
from golf.analytics import build_forecasts, potential_gap_pct


class TestLinearForecast(unittest.TestCase):
    def _sessions(self, carries):
        return [
            {"club_summaries": [{"club_label": "7 Iron", "avg_carry_distance": c, "avg_smash_factor": 1.25 + i * 0.01}]}
            for i, c in enumerate(carries)
        ]

    def test_requires_min_three_sessions(self) -> None:
        result = build_forecasts(self._sessions([145.0, 147.0]))
        self.assertEqual(result["per_club"], {})

    def test_produces_three_predictions(self) -> None:
        result = build_forecasts(self._sessions([140.0, 143.0, 146.0]))
        carry = result["per_club"]["7 Iron"]["carry"]
        self.assertEqual(len(carry["predictions"]), 3)
        self.assertEqual(len(carry["confidence_band"]), 3)

    def test_slope_correct_for_linear_data(self) -> None:
        result = build_forecasts(self._sessions([140.0, 143.0, 146.0]))
        self.assertAlmostEqual(result["per_club"]["7 Iron"]["carry"]["slope"], 3.0, places=1)

    def test_predictions_continue_trend(self) -> None:
        result = build_forecasts(self._sessions([140.0, 143.0, 146.0]))
        preds = result["per_club"]["7 Iron"]["carry"]["predictions"]
        self.assertAlmostEqual(preds[0], 149.0, places=0)
        self.assertAlmostEqual(preds[1], 152.0, places=0)
        self.assertAlmostEqual(preds[2], 155.0, places=0)

    def test_has_generated_at(self) -> None:
        result = build_forecasts(self._sessions([140.0, 143.0, 146.0]))
        self.assertIn("generated_at", result)

    def test_potential_gap_pct_normal(self) -> None:
        club = {"avg_smash_factor": 1.28, "potential_smash_factor": 1.45}
        result = potential_gap_pct(club)
        self.assertAlmostEqual(result, 88.3, places=0)

    def test_potential_gap_pct_missing_returns_none(self) -> None:
        self.assertIsNone(potential_gap_pct({"avg_smash_factor": None, "potential_smash_factor": 1.45}))
        self.assertIsNone(potential_gap_pct({"avg_smash_factor": 1.28, "potential_smash_factor": None}))

    def test_potential_gap_pct_capped_at_100(self) -> None:
        club = {"avg_smash_factor": 1.50, "potential_smash_factor": 1.45}
        self.assertLessEqual(potential_gap_pct(club), 100.0)
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
python -m pytest tests/test_pipeline.py::TestLinearForecast -v
```
Expected: all fail with `ImportError`.

- [ ] **Step 3: Add `_linear_forecast()`, `build_forecasts()`, `potential_gap_pct()` to `analytics.py`**

Insert after the `score_sessions()` function and before `build_analysis()`:

```python
def _linear_forecast(values: list[float], steps: int = 3) -> dict[str, Any]:
    from statistics import linear_regression as _linreg
    n = len(values)
    fit = _linreg(list(range(n)), values)
    slope, intercept = fit.slope, fit.intercept
    residuals = [values[i] - (slope * i + intercept) for i in range(n)]
    se = (sum(r * r for r in residuals) / max(n - 2, 1)) ** 0.5
    predictions: list[float] = []
    confidence_band: list[list[float]] = []
    for step in range(1, steps + 1):
        x = n - 1 + step
        pred = round(slope * x + intercept, 1)
        half = round(1.96 * se, 1)
        predictions.append(pred)
        confidence_band.append([round(pred - half, 1), round(pred + half, 1)])
    return {
        "slope": round(slope, 3),
        "last_actual": round(values[-1], 1),
        "predictions": predictions,
        "confidence_band": confidence_band,
    }


def build_forecasts(
    session_summaries: list[dict[str, Any]], min_sessions: int = 3
) -> dict[str, Any]:
    club_carry: dict[str, list[float]] = {}
    club_smash: dict[str, list[float]] = {}
    for session in session_summaries:
        for club_sum in session.get("club_summaries", []):
            label = club_sum["club_label"]
            carry = club_sum.get("avg_carry_distance")
            smash = club_sum.get("avg_smash_factor")
            if isinstance(carry, (int, float)):
                club_carry.setdefault(label, []).append(float(carry))
            if isinstance(smash, (int, float)):
                club_smash.setdefault(label, []).append(float(smash))
    per_club: dict[str, dict[str, Any]] = {}
    for club in set(club_carry) | set(club_smash):
        club_data: dict[str, Any] = {}
        carries = club_carry.get(club, [])
        smashs = club_smash.get(club, [])
        if len(carries) >= min_sessions:
            club_data["carry"] = _linear_forecast(carries)
        if len(smashs) >= min_sessions:
            club_data["smash"] = _linear_forecast(smashs)
        if club_data:
            per_club[club] = club_data
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "per_club": per_club,
    }


def potential_gap_pct(club_summary: dict[str, Any]) -> float | None:
    avg = club_summary.get("avg_smash_factor")
    potential = club_summary.get("potential_smash_factor")
    if not isinstance(avg, (int, float)) or not isinstance(potential, (int, float)) or potential == 0:
        return None
    return round(min(100.0, float(avg) / float(potential) * 100.0), 1)
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_pipeline.py::TestLinearForecast -v
```
Expected: all pass.

- [ ] **Step 5: Add `session_index` to dispersion points in `chart_payload()`**

In `analytics.py`, find the dispersion loop inside `chart_payload()`:

```python
    for session in sessions:
        for shot in session["shots"]:
```

Replace with:

```python
    for session_idx, session in enumerate(sessions):
        for shot in session["shots"]:
```

And add `"session_index": session_idx` to the `dispersion.append(...)` dict so it reads:

```python
            dispersion.append(
                {
                    "club": shot["club_label"],
                    "x": round(x, 1),
                    "y": round(y, 1),
                    "outlier": shot.get("is_outlier", False),
                    "session_index": session_idx,
                }
            )
```

- [ ] **Step 6: Commit**

```bash
git add src/golf/analytics.py tests/test_pipeline.py
git commit -m "feat: add build_forecasts, potential_gap_pct, dispersion session_index"
```

---

## Task 2: Python — severity labels + recommendation copy

**Files:**
- Modify: `src/golf/analytics.py`
- Test: `tests/test_pipeline.py`

- [ ] **Step 1: Write failing tests**

```python
from golf.analytics import build_recommendations


class TestRecommendationLabels(unittest.TestCase):
    def _club(self, **kwargs) -> dict:
        base = {
            "club_label": "7 Iron", "avg_total_deviation_distance": None,
            "avg_carry_deviation_distance": None, "face_to_path_stddev": None,
            "avg_face_to_path": None, "avg_smash_factor": None,
            "potential_smash_factor": None, "tempo_stddev": None,
            "outlier_rate": None, "avg_carry_distance": None,
            "carry_stddev": None, "shot_count": 10,
        }
        base.update(kwargs)
        return base

    def test_severity_label_present_on_all_recs(self) -> None:
        clubs = [self._club(avg_total_deviation_distance=15.0)]
        recs = build_recommendations([], clubs)
        for rec in recs:
            self.assertIn("severity_label", rec)
            self.assertIn(rec["severity_label"], ("High", "Medium", "Low"))

    def test_high_offline_gets_high_label(self) -> None:
        clubs = [self._club(avg_total_deviation_distance=15.0)]
        recs = build_recommendations([], clubs)
        self.assertTrue(any(r["severity_label"] == "High" for r in recs))

    def test_no_word_bad_in_any_rec(self) -> None:
        clubs = [self._club(avg_total_deviation_distance=15.0, face_to_path_stddev=8.0)]
        recs = build_recommendations([], clubs)
        for rec in recs:
            for field in ("title", "summary"):
                self.assertNotIn(" bad ", f" {rec.get(field, '').lower()} ")
```

- [ ] **Step 2: Run to confirm failure**

```bash
python -m pytest tests/test_pipeline.py::TestRecommendationLabels -v
```
Expected: fail with `KeyError: 'severity_label'`.

- [ ] **Step 3: Add `_severity_label()` before `build_recommendations()` in `analytics.py`**

```python
def _severity_label(severity: int) -> str:
    if severity >= 60:
        return "High"
    if severity >= 30:
        return "Medium"
    return "Low"
```

- [ ] **Step 4: Update every `recommendations.append({...})` call in `build_recommendations()`**

There are 7 such calls. For each one, add `"severity_label": _severity_label(<same severity expression>)` to the dict. Also update the copy strings:

- `f"Reduce your {club_label} {signed_direction_label(bias)} miss"` → `f"Improve {club_label} start-line control"`
- `f"Tighten {club_label} face-to-path variance"` → `f"Dial in {club_label} face-to-path"`
- `f"Tighten {club_label} face-to-path"` → keep as-is (already softer)
- `f"Trim high-variance {club_label} swings"` → `f"Build {club_label} shot pattern consistency"`
- `f"Bunching: {left['club_label']} and {right['club_label']} overlap"` → `f"Gapping opportunity: {left['club_label']} and {right['club_label']}"`

Example — the directional-control recommendation becomes:

```python
            recommendations.append(
                {
                    "title": f"Improve {club_label} start-line control",
                    "focus_area": "directional control",
                    "severity": min(100, round(abs(bias) * 2.5)),
                    "severity_label": _severity_label(min(100, round(abs(bias) * 2.5))),
                    "club_label": club_label,
                    "summary": (
                        f"Average offline is {abs(bias):.1f} yards {signed_direction_label(bias)}. "
                        "Work on start-line control with alignment-stick drills."
                    ),
                    "evidence": f"Average deviation: {bias:.1f} yds",
                }
            )
```

Apply the same `"severity_label": _severity_label(...)` addition to all 6 remaining `recommendations.append` calls.

- [ ] **Step 5: Run tests**

```bash
python -m pytest tests/test_pipeline.py::TestRecommendationLabels -v
```
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add src/golf/analytics.py tests/test_pipeline.py
git commit -m "feat: severity labels and reframed recommendation copy"
```

---

## Task 3: Python — wire forecasts + club velocity into `build_analysis()`

**Files:**
- Modify: `src/golf/analytics.py`
- Test: `tests/test_pipeline.py`

- [ ] **Step 1: Write failing tests**

```python
class TestBuildAnalysisForecasts(unittest.TestCase):
    def _three_csv_dir(self, tmp: Path) -> Path:
        data_dir = tmp / "Data"
        data_dir.mkdir(parents=True)
        for name in ["s1.csv", "s2.csv", "s3.csv"]:
            (data_dir / name).write_text(SAMPLE_CSV, encoding="utf-8")
        return data_dir

    def test_forecasts_key_in_analysis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            analysis = build_command(self._three_csv_dir(Path(tmp)), Path(tmp) / "out")
            self.assertIn("forecasts", analysis)
            self.assertIn("per_club", analysis["forecasts"])

    def test_clubs_have_velocity_and_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            analysis = build_command(self._three_csv_dir(Path(tmp)), Path(tmp) / "out")
            for club in analysis["clubs"]:
                self.assertIn("improvement_velocity", club)
                self.assertIn("potential_gap_pct", club)

    def test_dispersion_has_session_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            analysis = build_command(self._three_csv_dir(Path(tmp)), Path(tmp) / "out")
            for pt in analysis["charts"]["dispersion"]:
                self.assertIn("session_index", pt)
```

- [ ] **Step 2: Run to confirm failure**

```bash
python -m pytest tests/test_pipeline.py::TestBuildAnalysisForecasts -v
```
Expected: fail — `forecasts` key missing.

- [ ] **Step 3: Add `_club_velocity()` before `build_analysis()` in `analytics.py`**

```python
def _club_velocity(club_label: str, session_summaries: list[dict[str, Any]], n: int = 3) -> str:
    from statistics import linear_regression as _linreg
    values: list[float] = []
    for session in session_summaries[-n:]:
        for club_sum in session.get("club_summaries", []):
            if club_sum["club_label"] == club_label:
                carry = club_sum.get("avg_carry_distance")
                if isinstance(carry, (int, float)):
                    values.append(float(carry))
                break
    if len(values) < 2:
        return "Holding steady"
    fit = _linreg(list(range(len(values))), values)
    if fit.slope > 1.5:
        return "Most improved"
    if fit.slope < -1.5:
        return "Work needed"
    return "Holding steady"
```

- [ ] **Step 4: Update `build_analysis()` signature**

Change:
```python
def build_analysis(sessions: list[dict[str, Any]]) -> dict[str, Any]:
```
to:
```python
def build_analysis(sessions: list[dict[str, Any]], previous_forecasts: dict[str, Any] | None = None) -> dict[str, Any]:
```

- [ ] **Step 5: Add `forecasts = build_forecasts(session_summaries)` inside `build_analysis()`**

After the lines that compute `session_rating_trend` (the loop ending with `summary["session_rating_trend"] = ...`), add:

```python
    forecasts = build_forecasts(session_summaries)
```

- [ ] **Step 6: Add `improvement_velocity` and `potential_gap_pct` to the clubs list in the return dict**

In the `"clubs"` list comprehension in the `return` dict, find the last field already there (`"outlier_rate": ...`) and add two more entries inside the same per-club dict:

```python
                "improvement_velocity": _club_velocity(club["club_label"], session_summaries),
                "potential_gap_pct": potential_gap_pct(club),
```

- [ ] **Step 7: Add `forecasts` and `previous_forecasts` to the return dict**

In the `return { ... }` at the bottom of `build_analysis()`, add:

```python
        "forecasts": forecasts,
        "previous_forecasts": previous_forecasts or {},
```

- [ ] **Step 8: Run tests**

```bash
python -m pytest tests/test_pipeline.py::TestBuildAnalysisForecasts -v
```
Expected: all pass.

- [ ] **Step 9: Run full suite**

```bash
python -m pytest tests/ -v
```
Expected: all pass.

- [ ] **Step 10: Commit**

```bash
git add src/golf/analytics.py tests/test_pipeline.py
git commit -m "feat: wire forecasts, velocity badges, potential gap into build_analysis"
```

---

## Task 4: Python — `cli.py` predictions.json persistence

**Files:**
- Modify: `src/golf/cli.py`
- Test: `tests/test_pipeline.py`

- [ ] **Step 1: Write failing tests**

```python
class TestPredictionsPersistence(unittest.TestCase):
    def _three_csv_dir(self, tmp: Path) -> Path:
        data_dir = tmp / "Data"
        data_dir.mkdir(parents=True)
        for name in ["s1.csv", "s2.csv", "s3.csv"]:
            (data_dir / name).write_text(SAMPLE_CSV, encoding="utf-8")
        return data_dir

    def test_predictions_json_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            build_command(self._three_csv_dir(Path(tmp)), out)
            self.assertTrue((out / "predictions.json").exists())

    def test_previous_forecasts_loaded_on_second_build(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            build_command(self._three_csv_dir(Path(tmp)), out)
            analysis2 = build_command(self._three_csv_dir(Path(tmp)), out)
            self.assertIn("previous_forecasts", analysis2)
```

- [ ] **Step 2: Run to confirm failure**

```bash
python -m pytest tests/test_pipeline.py::TestPredictionsPersistence -v
```
Expected: fail — `predictions.json` not written.

- [ ] **Step 3: Replace `build_command()` in `cli.py`**

```python
def build_command(data_dir: Path, output_dir: Path) -> dict:
    sessions = load_sessions(data_dir)

    predictions_path = output_dir / "predictions.json"
    previous_forecasts: dict | None = None
    if predictions_path.exists():
        try:
            previous_forecasts = json.loads(predictions_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            previous_forecasts = None

    analysis = build_analysis(sessions, previous_forecasts)

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "analysis.json").write_text(json.dumps(analysis, indent=2), encoding="utf-8")
    write_site(analysis, output_dir)

    if analysis.get("forecasts", {}).get("per_club"):
        predictions_path.write_text(json.dumps(analysis["forecasts"], indent=2), encoding="utf-8")

    return analysis
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_pipeline.py::TestPredictionsPersistence -v
```
Expected: all pass.

- [ ] **Step 5: Run full suite**

```bash
python -m pytest tests/ -v
```
Expected: all pass.

- [ ] **Step 6: Update `.gitignore`**

Add to `.gitignore`:
```
.superpowers/
```

- [ ] **Step 7: Commit**

```bash
git add src/golf/cli.py .gitignore tests/test_pipeline.py
git commit -m "feat: persist forecasts to predictions.json between builds"
```

---

## Task 5: Frontend — light palette + Playfair Display + hero redesign

**Files:**
- Modify: `src/golf/site.py`

- [ ] **Step 1: Replace CSS `:root` variables**

Find and replace the entire `:root { ... }` block:

```css
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
```

with:

```css
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
```

- [ ] **Step 2: Update body background and panel shadow**

Find `background: linear-gradient(180deg, #07111a 0%, #091726 100%);` and replace with:
```css
        background: linear-gradient(180deg, #F2F2F0 0%, #ebebea 100%);
```

Find `box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);` and replace with:
```css
        box-shadow: 0 2px 16px rgba(30, 52, 10, 0.07);
```

- [ ] **Step 3: Add Playfair Display font import**

Find:
```html
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>
    <style>
```
Replace with:
```html
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,700;1,900&display=swap" rel="stylesheet">
    <style>
```

- [ ] **Step 4: Add hero typography CSS**

Inside `<style>`, after `.hero-sub { margin-top: 6px; }`, add:

```css
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
```

- [ ] **Step 5: Replace hero HTML**

Find the full hero section from `<!-- ── Hero ──` to the closing `</section>` and replace it with:

```html
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
```

- [ ] **Step 6: Replace hero JS**

Find the `// ── Hero` JS block and replace it with:

```js
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
```

- [ ] **Step 7: Update `<title>` and JS COLORS**

Find `<title>Golf range analytics</title>` → replace with `<title>Bad at golf. Great at data. — Jerry Gamblin</title>`.

Find the `COLORS` array and replace:
```js
      const COLORS = ["#57b5ff", "#5fd18b", "#ffb454", "#ff7b72", "#9b8cff", "#7ce2ff", "#ffd166", "#f4a261"];
```
with:
```js
      const COLORS = ["#408114","#1B7114","#4D6E24","#b45309","#6b7280","#0369a1","#7c3aed","#0d9488"];
```

- [ ] **Step 8: Rebuild and verify**

```bash
cd /Users/gamblin/Code/golf && python -m golf.cli build && open output/site/index.html
```
Confirm: light green background, Playfair Display headline, hero stat row, no dark navy.

- [ ] **Step 9: Commit**

```bash
git add src/golf/site.py
git commit -m "feat: light palette, Playfair Display hero, stat row"
```

---

## Task 6: Frontend — forecast line on session trend + compact offline bar

**Files:**
- Modify: `src/golf/site.py`

- [ ] **Step 1: Add forecast callout CSS**

Inside `<style>`, after `.chart-canvas.tall { height: 420px; }`:

```css
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
```

- [ ] **Step 2: Add forecast callout element to session trend panel**

Find:
```html
        <div class="panel chart-wrap">
          <h2>Session trend</h2>
          <div class="chart-canvas">
            <canvas id="sessionTrend"></canvas>
          </div>
        </div>
```
Replace with:
```html
        <div class="panel chart-wrap">
          <h2>Session trend</h2>
          <div class="chart-canvas">
            <canvas id="sessionTrend"></canvas>
          </div>
          <div class="forecast-callout" id="trend-forecast-callout" style="display:none;"></div>
        </div>
```

- [ ] **Step 3: Replace session trend chart JS with forecast-aware version**

Find the entire `const sessionTrendChart = createChart("sessionTrend", { ... });` block. Replace it with:

```js
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
```

- [ ] **Step 4: Replace dispersion scatter panel HTML with compact offline bar**

Find the full dispersion panel:
```html
        <div class="panel chart-wrap" style="grid-column: 1 / -1;">
          <h2>Dispersion map</h2>
          <div class="club-toggles" id="dispersionToggles"></div>
          <div class="chart-canvas tall">
            <canvas id="dispersionChart"></canvas>
          </div>
        </div>
```
Replace with:
```html
        <div class="panel chart-wrap" style="grid-column: 1 / -1;">
          <h2>Avg offline by club</h2>
          <p class="small" style="margin:0 0 10px">Average lateral miss per club. Green = within 10 yds &nbsp;|&nbsp; Amber = 10+ yds. Full shot-by-shot scatter is on each club's detail page.</p>
          <div class="chart-canvas" style="height:200px;">
            <canvas id="offlineSummaryChart"></canvas>
          </div>
        </div>
```

- [ ] **Step 5: Replace the full dispersion JS block with offline bar JS**

Find the `// ── Dispersion map` JS block (from `const dispersionByClub = {};` to the end of the toggle buttons block). Replace the entire block with:

```js
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
              backgroundColor: vals.map((v) => v >= 10 ? "rgba(180,83,9,0.7)" : "rgba(64,129,20,0.7)"),
              borderColor: vals.map((v) => v >= 10 ? "#b45309" : "#408114"),
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
```

- [ ] **Step 6: Rebuild and verify**

```bash
python -m golf.cli build && open output/site/index.html
```
Confirm: session trend has dashed forecast line and callout; dispersion replaced by compact horizontal bar.

- [ ] **Step 7: Commit**

```bash
git add src/golf/site.py
git commit -m "feat: forecast line on session trend, compact offline bar chart"
```

---

## Task 7: Frontend — recommendations green severity tiers

**Files:**
- Modify: `src/golf/site.py`

- [ ] **Step 1: Replace recommendation CSS**

Find:
```css
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
```
Replace with:
```css
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
```

- [ ] **Step 2: Update recommendations JS renderer**

Find the `data.recommendations.forEach` loop inside `// ── Recommendations`. Replace the loop body with:

```js
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
```

- [ ] **Step 3: Rebuild and verify**

```bash
python -m golf.cli build && open output/site/index.html
```
Confirm: coaching tab shows green-tiered cards, no red elements anywhere.

- [ ] **Step 4: Commit**

```bash
git add src/golf/site.py
git commit -m "feat: all-green recommendation severity tiers"
```

---

## Task 8: Frontend — club links + detail panel scaffolding

**Files:**
- Modify: `src/golf/site.py`

- [ ] **Step 1: Add club detail CSS**

Inside `<style>`, after `.coaching-grid { display: grid; gap: 24px; }`, add:

```css
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
      .vel-needed   { background: #b45309; }
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
```

- [ ] **Step 2: Add club detail panel HTML inside dashboard tab**

Find `<!-- ══ end DASHBOARD TAB ═══════════════════════════ -->` and insert just before it:

```html
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
```

- [ ] **Step 3: Add navigation JS**

At the very end of `<script>`, after the `// ── Tab switching` block, add:

```js
      // ── Club detail navigation ────────────────────────────────────────────
      const clubDetailPanel = document.getElementById("club-detail");
      const dashboardChildren = Array.from(document.getElementById("tab-dashboard").children)
        .filter((el) => el.id !== "club-detail");

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
```

- [ ] **Step 4: Make club names in summary table clickable using data attributes**

Find the `// ── Club summary table` JS block. The current first `<td>` in the row template is:
```js
          <td>${club.club_label}</td>
```
Replace with:
```js
          <td><button class="club-link-btn" data-club="${club.club_label}">${club.club_label} &#8599;</button></td>
```

Then after the `clubSummaryBody.appendChild(row)` line, add event delegation (once, outside the loop, after the full `data.clubs.forEach` block):

```js
      document.getElementById("club-summary-body").addEventListener("click", (e) => {
        const btn = e.target.closest(".club-link-btn");
        if (btn) showClubDetail(btn.dataset.club);
      });
```

- [ ] **Step 5: Rebuild and verify navigation**

```bash
python -m golf.cli build && open output/site/index.html
```
Confirm: club names are underlined links; clicking one hides the dashboard and shows the (empty) club detail panel; Back restores overview.

- [ ] **Step 6: Commit**

```bash
git add src/golf/site.py
git commit -m "feat: club detail panel scaffolding and click-through navigation"
```

---

## Task 9: Frontend — club detail content (stat strip, charts, table)

**Files:**
- Modify: `src/golf/site.py`

- [ ] **Step 1: Add `renderClubDetail()` JS function**

In `<script>`, just before `function showClubDetail(clubLabel) {`, add the full `renderClubDetail` function:

```js
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
            backgroundColor: points.map((p) => (p.outlier ? "#b45309" : "#408114") + hex),
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
```

- [ ] **Step 2: Rebuild and verify full club detail**

```bash
python -m golf.cli build && open output/site/index.html
```
Confirm:
- Clicking a club shows the detail panel with velocity badge, stat strip with potential gap bar
- Carry trend chart renders; forecast line appears for clubs with ≥3 sessions
- Smash vs potential chart renders
- Dispersion scatter shows this club's shots with opacity fade by session age
- Session breakdown table populated
- Forecast callout visible with ±confidence range
- Back button restores overview cleanly

- [ ] **Step 3: Run full test suite**

```bash
python -m pytest tests/ -v
```
Expected: all pass.

- [ ] **Step 4: Commit**

```bash
git add src/golf/site.py
git commit -m "feat: full club detail page with charts, stat strip, dispersion, and forecast"
```

---

## Post-Implementation Verification

- [ ] Run a real build against actual data: `python -m golf.cli build --data-dir Data --output-dir output/site`
- [ ] Open `output/site/index.html` — light palette, Playfair hero, no dark navy anywhere
- [ ] Click each club in summary table — detail panel opens, Back restores dashboard cleanly
- [ ] Charts tab: dashed forecast line on session trend (if ≥3 sessions), compact offline bar replacing scatter
- [ ] Coaching tab: all recommendation cards use green tiers, no red/amber borders
- [ ] `output/site/predictions.json` exists after build
- [ ] Run build a second time — `previous_forecasts` present in `analysis.json`
- [ ] `python -m pytest tests/ -v` — all pass
