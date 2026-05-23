from __future__ import annotations

import csv
import datetime as dt
import re
from pathlib import Path
from typing import Any

try:
    import yaml as _yaml

    def _load_yaml(path: Path) -> Any:
        with path.open("r", encoding="utf-8") as fh:
            return _yaml.safe_load(fh)

except ImportError:  # pragma: no cover — yaml optional at runtime
    def _load_yaml(path: Path) -> Any:  # type: ignore[misc]
        raise RuntimeError("PyYAML is required to load external field-alias configs. Run: pip install pyyaml")


_CONFIG_PATH = Path(__file__).parent / "config" / "field_aliases.yaml"

# Loaded lazily so tests can patch _CONFIG_PATH before first import.
_FIELD_CONFIG: dict[str, Any] | None = None


def _get_field_config() -> dict[str, Any]:
    global _FIELD_CONFIG
    if _FIELD_CONFIG is None:
        _FIELD_CONFIG = _load_yaml(_CONFIG_PATH)
    return _FIELD_CONFIG


def _get_aliases() -> dict[str, str]:
    return _get_field_config().get("aliases", {})


def _get_unit_conversions() -> dict[str, float]:
    return _get_field_config().get("unit_conversions", {})


def _get_distance_speed_fields() -> list[str]:
    return _get_field_config().get("distance_speed_fields", [])


def _get_header_anchors() -> set[str]:
    """Return lowercase anchor strings that confirm a row is a header row."""
    return {a.lower() for a in _get_field_config().get("header_anchors", [])}


def _get_zero_critical_fields() -> set[str]:
    """Return field names where a value of 0.0 means 'no data recorded'."""
    return set(_get_field_config().get("zero_critical_fields", []))


# Legacy in-process dict kept as a last-resort fallback so the module works
# even when the YAML file is missing (e.g., during editable installs before
# the config dir is copied).
HEADER_ALIASES: dict[str, str] = {
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

TEXT_FIELDS = {
    "date",
    "player",
    "club_name",
    "brand_model",
    "club_type",
    "spin_rate_type",
    "note",
    "tag",
    "garmin_hole",        # Garmin round-export hole label
    "garmin_shot_number", # Garmin round-export shot counter (informational)
}


def validate_shot(shot: dict[str, Any]) -> dict[str, Any]:
    """Null out zero values for critical metrics and record quality flags.

    The Garmin R10 occasionally saves phantom shots where ball speed and
    carry distance are exactly 0.0 — meaning the monitor did not detect a
    real ball flight.  Leaving those zeros in place would drag down averages
    and consistency scores.  This function converts them to ``None`` and
    records which fields were affected in ``data_quality_flags``.
    """
    try:
        zero_fields = _get_zero_critical_fields()
    except Exception:
        zero_fields = {"ball_speed", "carry_distance", "club_speed"}

    flags: list[str] = []
    for field in zero_fields:
        if shot.get(field) == 0.0:
            shot[field] = None
            flags.append(f"zero_{field}")
    if flags:
        shot["data_quality_flags"] = flags
    return shot


def normalize_header(value: str) -> str:
    try:
        aliases = _get_aliases()
    except Exception:
        aliases = HEADER_ALIASES
    if value in aliases:
        return aliases[value]
    # Fallback to the in-process dict for any alias not yet in the YAML.
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
    for fmt in (
        "%m/%d/%y %H:%M:%S",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%y %I:%M:%S %p",
        "%m/%d/%Y %I:%M:%S %p",
    ):
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


def _is_units_row(row: list[str]) -> bool:
    """Return True when most non-empty cells look like unit annotations, e.g. [mph]."""
    non_empty = [cell.strip() for cell in row if cell.strip()]
    if not non_empty:
        return False
    bracketed = sum(1 for cell in non_empty if re.match(r"^\[.*\]$", cell))
    return bracketed / len(non_empty) >= 0.3


def _resolve_conversion_factor(unit_string: str) -> float:
    """Return a multiply-by factor to convert *unit_string* to imperial."""
    key = unit_string.strip("[]").strip().lower()
    try:
        conversions = _get_unit_conversions()
    except Exception:
        conversions = {}
    return conversions.get(key, 1.0)


def _apply_unit_conversions(shot: dict[str, Any], units: dict[str, str]) -> dict[str, Any]:
    """Convert any metric distance/speed values in *shot* to imperial in-place."""
    try:
        convertible_fields = set(_get_distance_speed_fields())
    except Exception:
        convertible_fields = set()

    for field, unit_string in units.items():
        if field not in convertible_fields:
            continue
        factor = _resolve_conversion_factor(unit_string)
        if factor == 1.0:
            continue
        value = shot.get(field)
        if isinstance(value, (int, float)):
            shot[field] = round(value * factor, 4)
    return shot


def load_session(path: Path) -> dict[str, Any]:
    """Parse a launch-monitor CSV into a session dict.

    The loader is format-resilient: it scans past any preamble rows (title
    rows, blank rows, metadata blurbs) until it finds a header row whose
    cells match known column names.  The row immediately after the header is
    treated as the units row when it looks like unit annotations; otherwise
    it is treated as the first data row.  All distance/speed values that
    arrive in metric units are automatically converted to imperial before
    the shot dict is returned.
    """
    all_aliases = {**HEADER_ALIASES}
    try:
        all_aliases.update(_get_aliases())
    except Exception:
        pass

    known_headers: set[str] = set(all_aliases.keys())

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        raw_rows = list(csv.reader(handle))

    # ── Locate the header row ────────────────────────────────────────────────
    # A header row must contain cells matching known aliases AND/OR recognised
    # anchor keywords (e.g. "Shot Number", "Club") that appear in Garmin Golf
    # app activity/round exports which often have metadata preamble rows.
    try:
        anchor_keywords = _get_header_anchors()
    except Exception:
        anchor_keywords = {"date", "time", "timestamp", "datetime", "club", "shot number"}

    header_row_index: int | None = None
    for index, row in enumerate(raw_rows):
        stripped = [cell.strip() for cell in row]
        if not any(stripped):
            continue
        stripped_lower = [cell.lower() for cell in stripped]
        known_hits = sum(1 for cell in stripped if cell in known_headers)
        has_anchor = any(cell in anchor_keywords for cell in stripped_lower)
        # Fire when: 2+ known aliases, OR 1 known alias + an anchor keyword,
        # OR 2+ anchor keywords (covers minimal Garmin round exports).
        anchor_hits = sum(1 for cell in stripped_lower if cell in anchor_keywords)
        if known_hits >= 2 or (known_hits >= 1 and has_anchor) or anchor_hits >= 2:
            header_row_index = index
            break

    if header_row_index is None:
        raise ValueError(
            f"{path.name}: could not locate a recognisable header row. "
            "Ensure at least two column names match the field-alias config."
        )

    headers = [cell.strip() for cell in raw_rows[header_row_index]]
    normalized_headers = [normalize_header(h) for h in headers]

    # ── Determine units row ──────────────────────────────────────────────────
    next_index = header_row_index + 1
    if next_index < len(raw_rows) and _is_units_row(raw_rows[next_index]):
        units_row = raw_rows[next_index]
        data_start_index = next_index + 1
    else:
        units_row = []
        data_start_index = next_index

    units: dict[str, str] = {
        normalized_headers[i]: units_row[i].strip()
        for i in range(min(len(headers), len(units_row)))
        if units_row[i].strip()
    }

    # ── Parse data rows ──────────────────────────────────────────────────────
    shots: list[dict[str, Any]] = []
    shot_number = 0
    for row in raw_rows[data_start_index:]:
        if not any(cell.strip() for cell in row):
            continue

        # Skip rows that don't contain a valid timestamp in the date column
        # (catches sub-header rows, summary footers, etc.).
        date_index = next(
            (i for i, h in enumerate(normalized_headers) if h == "date"),
            None,
        )
        if date_index is not None:
            raw_date = row[date_index].strip() if date_index < len(row) else ""
            if raw_date and parse_timestamp(raw_date) is None:
                continue  # non-data row — skip

        shot_number += 1
        padded_row = row + [""] * max(0, len(headers) - len(row))
        shot: dict[str, Any] = {}
        for index, header in enumerate(normalized_headers):
            raw_value = padded_row[index].strip() if index < len(padded_row) else ""
            if header == "date":
                shot["shot_timestamp"] = parse_timestamp(raw_value)
            elif header in TEXT_FIELDS:
                shot[header] = raw_value or None
            else:
                shot[header] = parse_float(raw_value)

        _apply_unit_conversions(shot, units)
        validate_shot(shot)

        shot["session_id"] = slugify(path.stem)
        shot["source_file"] = path.name
        shot["shot_number"] = shot_number
        shot["club_label"] = preferred_club_label(shot)
        shots.append(shot)

    if not shots:
        raise ValueError(f"{path.name} did not contain any shot rows.")

    timestamps = [shot["shot_timestamp"] for shot in shots if shot.get("shot_timestamp")]
    flagged_shot_count = sum(1 for shot in shots if shot.get("data_quality_flags"))
    return {
        "session_id": slugify(path.stem),
        "source_file": path.name,
        "source_path": str(path),
        "player": next((shot["player"] for shot in shots if shot.get("player")), None),
        "session_timestamp": timestamps[0] if timestamps else None,
        "units": units,
        "flagged_shot_count": flagged_shot_count,
        "shots": shots,
    }


def load_sessions(data_dir: Path) -> list[dict[str, Any]]:
    csv_files = sorted(data_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files were found in {data_dir}.")
    return [load_session(path) for path in csv_files]
