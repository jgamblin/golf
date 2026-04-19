from __future__ import annotations

import csv
import datetime as dt
import re
from pathlib import Path
from typing import Any

TEXT_FIELDS = {
    "date",
    "player",
    "club_name",
    "brand_model",
    "club_type",
    "spin_rate_type",
    "note",
    "tag",
}

HEADER_ALIASES = {
    "Brand/Model": "brand_model",
    "Club Name": "club_name",
    "Club Type": "club_type",
    "Club Speed": "club_speed",
    "Attack Angle": "attack_angle",
    "Club Path": "club_path",
    "Club Face": "club_face",
    "Face to Path": "face_to_path",
    "Ball Speed": "ball_speed",
    "Smash Factor": "smash_factor",
    "Launch Angle": "launch_angle",
    "Launch Direction": "launch_direction",
    "Spin Rate": "spin_rate",
    "Spin Rate Type": "spin_rate_type",
    "Spin Axis": "spin_axis",
    "Apex Height": "apex_height",
    "Carry Distance": "carry_distance",
    "Carry Deviation Angle": "carry_deviation_angle",
    "Carry Deviation Distance": "carry_deviation_distance",
    "Total Distance": "total_distance",
    "Total Deviation Angle": "total_deviation_angle",
    "Total Deviation Distance": "total_deviation_distance",
    "Target Total Distance": "target_total_distance",
    "Target Carry Distance": "target_carry_distance",
    "Air Density": "air_density",
    "Air Pressure": "air_pressure",
    "Relative Humidity": "relative_humidity",
    "Back Stroke Length": "back_stroke_length",
    "Target Backswing Time": "target_backswing_time",
    "Target Downswing Time": "target_downswing_time",
    "Forward Stroke Length": "forward_stroke_length",
    "Backswing Time": "backswing_time",
    "Downswing Time": "downswing_time",
    "Target Tempo": "target_tempo",
    "Swing Tempo": "swing_tempo",
}


def normalize_header(value: str) -> str:
    if value in HEADER_ALIASES:
        return HEADER_ALIASES[value]
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def parse_float(value: str) -> float | None:
    cleaned = value.strip()
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_timestamp(value: str) -> str | None:
    cleaned = value.strip()
    if not cleaned:
        return None
    for fmt in ("%m/%d/%y %H:%M:%S", "%m/%d/%Y %H:%M:%S"):
        try:
            parsed = dt.datetime.strptime(cleaned, fmt)
            return parsed.isoformat()
        except ValueError:
            continue
    return None


def preferred_club_label(shot: dict[str, Any]) -> str:
    return (
        shot.get("club_name")
        or shot.get("club_type")
        or shot.get("brand_model")
        or "Unknown club"
    )


def load_session(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        headers = next(reader)
        units_row = next(reader, [])
        normalized_headers = [normalize_header(header) for header in headers]
        units = {
            normalized_headers[index]: units_row[index].strip()
            for index in range(min(len(headers), len(units_row)))
            if units_row[index].strip()
        }

        shots: list[dict[str, Any]] = []
        for row_index, row in enumerate(reader, start=1):
            if not any(cell.strip() for cell in row):
                continue

            padded_row = row + [""] * (len(headers) - len(row))
            shot: dict[str, Any] = {}
            for index, header in enumerate(normalized_headers):
                raw_value = padded_row[index].strip() if index < len(padded_row) else ""
                if header == "date":
                    shot["shot_timestamp"] = parse_timestamp(raw_value)
                elif header in TEXT_FIELDS:
                    shot[header] = raw_value or None
                else:
                    shot[header] = parse_float(raw_value)

            shot["session_id"] = slugify(path.stem)
            shot["source_file"] = path.name
            shot["shot_number"] = row_index
            shot["club_label"] = preferred_club_label(shot)
            shots.append(shot)

    if not shots:
        raise ValueError(f"{path.name} did not contain any shot rows.")

    timestamps = [shot["shot_timestamp"] for shot in shots if shot.get("shot_timestamp")]
    return {
        "session_id": slugify(path.stem),
        "source_file": path.name,
        "source_path": str(path),
        "player": next((shot["player"] for shot in shots if shot.get("player")), None),
        "session_timestamp": timestamps[0] if timestamps else None,
        "units": units,
        "shots": shots,
    }


def load_sessions(data_dir: Path) -> list[dict[str, Any]]:
    csv_files = sorted(data_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files were found in {data_dir}.")
    return [load_session(path) for path in csv_files]
