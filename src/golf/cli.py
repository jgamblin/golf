from __future__ import annotations

import argparse
import json
from pathlib import Path

from .analytics import build_analysis
from .ingest import load_sessions
from .site import write_site


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


def parser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser(description="Build golf range analytics and a static site.")
    subcommands = cli.add_subparsers(dest="command", required=True)

    build = subcommands.add_parser("build", help="Build analytics outputs and the static site.")
    build.add_argument("--data-dir", default="Data", type=Path, help="Directory that contains raw CSV exports.")
    build.add_argument(
        "--output-dir",
        default=Path("output/site"),
        type=Path,
        help="Directory that will receive generated analytics and site files.",
    )
    return cli


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "build":
        build_command(args.data_dir, args.output_dir)
        return 0
    raise ValueError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
