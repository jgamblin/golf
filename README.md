# golf

Drop launch-monitor CSV exports into `Data/`, run the pipeline, and this repo will build a GitHub Pages dashboard with session summaries, charts, and practice recommendations.

## What it does

- ingests every CSV in `Data/`
- normalizes the launch-monitor fields into a consistent shot dataset
- runs a lightweight recommendation pipeline that flags dispersion, strike, tempo, and gapping issues
- generates a static dashboard in `output/site`
- deploys that dashboard to GitHub Pages with GitHub Actions

## Local usage

```bash
python3 -m pip install -e .
python3 -m golf.cli build --data-dir Data --output-dir output/site
```

Then open `output/site/index.html` locally, or let GitHub Actions publish the same output to Pages.

## Project layout

- `Data/`: raw range-session CSV exports
- `src/golf/ingest.py`: CSV parsing and normalization
- `src/golf/ml.py`: lightweight anomaly scoring for high-variance swings
- `src/golf/analytics.py`: club/session summaries and recommendation generation
- `src/golf/site.py`: static site generation
- `.github/workflows/build-and-deploy.yml`: GitHub Pages automation

## Recommendation model

The first version favors explainable analytics over heavyweight modeling:

- directional bias from average carry/total deviation
- face-to-path variance for clubface control
- smash-factor benchmarks for strike quality
- tempo variability for sequencing consistency
- simple anomaly scoring to flag outlier swings

That gives you useful coaching prompts immediately while keeping the pipeline easy to trust and tune as more sessions accumulate.
