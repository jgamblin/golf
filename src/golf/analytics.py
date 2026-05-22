from __future__ import annotations

import datetime as dt
import re
from collections import defaultdict
from math import ceil
from statistics import StatisticsError, linear_regression, median, pstdev, quantiles
from typing import Any

from .ml import score_shot_anomalies


def average(values: list[float | int | None]) -> float | None:
    usable = [float(value) for value in values if isinstance(value, (int, float))]
    if not usable:
        return None
    return sum(usable) / len(usable)


def deviation(values: list[float | int | None]) -> float | None:
    usable = [float(value) for value in values if isinstance(value, (int, float))]
    if len(usable) < 2:
        return None
    return pstdev(usable)


def coefficient_of_variation(values: list[float | int | None]) -> float | None:
    avg = average(values)
    dev = deviation(values)
    if avg in (None, 0) or dev is None:
        return None
    return abs(dev / avg)


def round_or_none(value: float | None, digits: int = 1) -> float | None:
    return None if value is None else round(value, digits)


def first_value(*values: float | int | None) -> float | int | None:
    for value in values:
        if value is not None:
            return value
    return None


def _SMASH_FALLBACK(club_label: str) -> float | None:
    """Hardcoded smash-factor benchmarks used when historical data is sparse."""
    club = club_label.lower()
    if "putter" in club:
        return None
    if "driver" in club:
        return 1.45
    if "wood" in club or "hybrid" in club:
        return 1.38
    if "wedge" in club or "pitching" in club or "sand" in club or "gap" in club or "lob" in club:
        return 1.10
    if "iron" in club:
        leading = club.split()[0]
        if leading.isdigit():
            iron_number = int(leading)
            if iron_number <= 4:
                return 1.33
            if iron_number <= 6:
                return 1.28
            return 1.20
        return 1.24
    return 1.20


def potential_smash_factor(club_label: str, shots: list[dict[str, Any]], *, min_shots: int = 5) -> float | None:
    """Return the 90th-percentile smash factor from *shots* for *club_label*.

    This represents the player's *achievable* peak for that specific club
    rather than an industry-average benchmark.  When fewer than *min_shots*
    valid readings exist we fall back to the hardcoded standard.
    """
    values = sorted(
        float(shot["smash_factor"])
        for shot in shots
        if shot.get("club_label") == club_label and isinstance(shot.get("smash_factor"), (int, float))
    )
    if len(values) < min_shots:
        return _SMASH_FALLBACK(club_label)
    # quantiles(n=10) returns [10th, 20th, ..., 90th] — index 8 is the 90th.
    return round(quantiles(values, n=10)[8], 3)


# Keep the old name as a convenience alias used elsewhere in the codebase.
def expected_smash_factor(club_label: str) -> float | None:
    return _SMASH_FALLBACK(club_label)


def signed_direction_label(value: float) -> str:
    return "right" if value > 0 else "left"


def _consistency_weights(all_club_summaries: list[dict[str, Any]]) -> dict[str, float]:
    """Derive penalty multipliers from the population of club summaries.

    Each weight is scaled so that a value equal to the population mean
    produces ~10 penalty points, keeping the 0-100 score range intuitive
    regardless of the dataset's physical units.
    """
    fields = {
        "carry_cv": 120.0,
        "offline_stddev": 1.3,
        "face_to_path_stddev": 4.0,
        "tempo_cv": 90.0,
    }
    weights: dict[str, float] = {}
    for field, default_weight in fields.items():
        values = [float(s[field]) for s in all_club_summaries if isinstance(s.get(field), (int, float)) and s[field] > 0]
        if len(values) >= 3:
            pop_mean = sum(values) / len(values)
            # Target: mean value → 10 penalty points.
            weights[field] = (10.0 / pop_mean) if pop_mean > 0 else default_weight
        else:
            weights[field] = default_weight
    return weights


def consistency_score(summary: dict[str, Any], weights: dict[str, float] | None = None) -> float | None:
    """Return a 0-100 consistency score for a single club summary.

    When *weights* are supplied (computed by :func:`_consistency_weights`)
    the penalty multipliers are calibrated to the current dataset so scores
    are comparable across sessions and monitor types.  Without *weights* the
    original fixed multipliers are used as a sensible fallback.
    """
    if weights is None:
        weights = {"carry_cv": 120.0, "offline_stddev": 1.3, "face_to_path_stddev": 4.0, "tempo_cv": 90.0}

    carry_cv = summary.get("carry_cv")
    offline_std = summary.get("offline_stddev")
    face_std = summary.get("face_to_path_stddev")
    tempo_cv = summary.get("tempo_cv")

    pieces = []
    if carry_cv is not None:
        pieces.append(carry_cv * weights.get("carry_cv", 120.0))
    if offline_std is not None:
        pieces.append(offline_std * weights.get("offline_stddev", 1.3))
    if face_std is not None:
        pieces.append(face_std * weights.get("face_to_path_stddev", 4.0))
    if tempo_cv is not None:
        pieces.append(tempo_cv * weights.get("tempo_cv", 90.0))
    if not pieces:
        return None
    return round(max(0.0, 100.0 - min(100.0, sum(pieces))), 1)


def attach_ml_scores(sessions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    all_shots = [shot for session in sessions for shot in session["shots"]]
    scores = score_shot_anomalies(all_shots)
    enriched_sessions: list[dict[str, Any]] = []
    for session in sessions:
        enriched_shots: list[dict[str, Any]] = []
        for shot in session["shots"]:
            score = scores[(shot["session_id"], shot["shot_number"])]
            enriched_shots.append({**shot, **score})
        enriched_sessions.append({**session, "shots": enriched_shots})
    return enriched_sessions


def summarize_club(club_label: str, shots: list[dict[str, Any]], weights: dict[str, float] | None = None) -> dict[str, Any]:
    summary = {
        "club_label": club_label,
        "shot_count": len(shots),
        "avg_carry_distance": average([shot.get("carry_distance") for shot in shots]),
        "avg_total_distance": average([shot.get("total_distance") for shot in shots]),
        "avg_ball_speed": average([shot.get("ball_speed") for shot in shots]),
        "avg_smash_factor": average([shot.get("smash_factor") for shot in shots]),
        "avg_face_to_path": average([shot.get("face_to_path") for shot in shots]),
        "avg_club_path": average([shot.get("club_path") for shot in shots]),
        "avg_attack_angle": average([shot.get("attack_angle") for shot in shots]),
        "avg_spin_rate": average([shot.get("spin_rate") for shot in shots]),
        "avg_launch_angle": average([shot.get("launch_angle") for shot in shots]),
        "avg_carry_deviation_distance": average([shot.get("carry_deviation_distance") for shot in shots]),
        "avg_total_deviation_distance": average([shot.get("total_deviation_distance") for shot in shots]),
        "avg_swing_tempo": average([shot.get("swing_tempo") for shot in shots]),
        "carry_stddev": deviation([shot.get("carry_distance") for shot in shots]),
        "offline_stddev": deviation(
            [first_value(shot.get("total_deviation_distance"), shot.get("carry_deviation_distance")) for shot in shots]
        ),
        "face_to_path_stddev": deviation([shot.get("face_to_path") for shot in shots]),
        "tempo_stddev": deviation([shot.get("swing_tempo") for shot in shots]),
        "carry_cv": coefficient_of_variation([shot.get("carry_distance") for shot in shots]),
        "tempo_cv": coefficient_of_variation([shot.get("swing_tempo") for shot in shots]),
        "outlier_rate": average([1.0 if shot.get("is_outlier") else 0.0 for shot in shots]),
        # Potential smash derived from the player's own top-10 % for this club.
        "potential_smash_factor": potential_smash_factor(club_label, shots),
    }
    summary["consistency_score"] = consistency_score(summary, weights)
    return summary


def _detect_club_mix(clubs: list[str]) -> dict[str, list[str]]:
    """Classify clubs by type and return groupings."""
    types: dict[str, list[str]] = {
        "drivers": [],
        "woods": [],
        "hybrids": [],
        "irons": [],
        "wedges": [],
        "putter": [],
    }
    for club in clubs:
        label = (club or "").strip().lower()
        if "driver" in label:
            types["drivers"].append(club)
        elif "wood" in label:
            types["woods"].append(club)
        elif "hybrid" in label or "rescue" in label:
            types["hybrids"].append(club)
        elif "iron" in label:
            types["irons"].append(club)
        elif "wedge" in label or "pitching" in label or re.search(r"\b(pw|gw|sw|lw|aw)\b", label):
            types["wedges"].append(club)
        elif "putter" in label:
            types["putter"].append(club)
    return types


def _format_club_mix_summary(types: dict[str, list[str]]) -> str:
    """Format club mix as a readable string like 'Irons (5, 6, 7)'."""
    parts = []
    if types["drivers"]:
        parts.append(f"Driver")
    if types["woods"]:
        parts.append(f"Woods ({len(types['woods'])} clubs)")
    if types["hybrids"]:
        parts.append(f"Hybrids ({len(types['hybrids'])} clubs)")
    if types["irons"]:
        irons_str = ", ".join([re.search(r"\d+", c).group(0) if re.search(r"\d+", c) else c for c in sorted(types["irons"], key=lambda x: _club_bag_order_key(x))])
        parts.append(f"Irons ({irons_str})")
    if types["wedges"]:
        wedges_str = ", ".join([re.search(r"\b(pw|gw|sw|lw|aw)\b", c.lower()).group(0).upper() if re.search(r"\b(pw|gw|sw|lw|aw)\b", c.lower()) else c for c in sorted(types["wedges"], key=lambda x: _club_bag_order_key(x))])
        parts.append(f"Wedges ({wedges_str})")
    if types["putter"]:
        parts.append("Putter")
    return " · ".join(parts) if parts else "Mixed"


def summarize_session(session: dict[str, Any], weights: dict[str, float] | None = None) -> dict[str, Any]:
    shots = session["shots"]
    clubs: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for shot in shots:
        clubs[shot["club_label"]].append(shot)

    club_summaries = [
        summarize_club(club_label, club_shots, weights)
        for club_label, club_shots in sorted(clubs.items(), key=lambda item: item[0])
    ]
    avg_offline = average(
        [first_value(shot.get("total_deviation_distance"), shot.get("carry_deviation_distance")) for shot in shots]
    )
    club_mix_types = _detect_club_mix(list(clubs.keys()))
    club_mix_summary = _format_club_mix_summary(club_mix_types)
    return {
        "session_id": session["session_id"],
        "source_file": session["source_file"],
        "player": session.get("player"),
        "session_timestamp": session.get("session_timestamp"),
        "shot_count": len(shots),
        "club_count": len(club_summaries),
        "club_mix": club_mix_summary,
        "avg_carry_distance": average([shot.get("carry_distance") for shot in shots]),
        "avg_total_distance": average([shot.get("total_distance") for shot in shots]),
        "avg_smash_factor": average([shot.get("smash_factor") for shot in shots]),
        "avg_ball_speed": average([shot.get("ball_speed") for shot in shots]),
        "avg_offline_distance": avg_offline,
        "outlier_rate": average([1.0 if shot.get("is_outlier") else 0.0 for shot in shots]),
        "flagged_shot_count": session.get("flagged_shot_count", 0),
        "club_summaries": club_summaries,
    }


def _severity_label(severity: int) -> str:
    if severity >= 60:
        return "High"
    if severity >= 30:
        return "Medium"
    return "Low"


def build_recommendations(
    session_summaries: list[dict[str, Any]],
    club_summaries: list[dict[str, Any]],
    all_shots: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    recommendations: list[dict[str, Any]] = []

    # ─── Composition awareness: detect club mix changes ──────────────────────
    if len(session_summaries) >= 2:
        latest = session_summaries[-1]
        prior_sessions = session_summaries[:-1]
        latest_mix = latest.get("club_mix", "")

        # Extract club types from mix string using word boundaries
        def extract_club_types(mix_str: str) -> set[str]:
            types = set()
            mix_lower = mix_str.lower()
            # Check for club types in order of specificity (longer patterns first)
            if "pitching wedge" in mix_lower or "pw" in mix_lower:
                types.add("pw")
            if "gap wedge" in mix_lower or "gw" in mix_lower:
                types.add("gw")
            if "sand wedge" in mix_lower or "sw" in mix_lower:
                types.add("sw")
            if "lob wedge" in mix_lower or "lw" in mix_lower:
                types.add("lw")
            if "wedge" in mix_lower and not any(x in types for x in ["pw", "gw", "sw", "lw"]):
                types.add("wedge")
            if "driver" in mix_lower:
                types.add("driver")
            if "wood" in mix_lower:
                types.add("woods")
            if "hybrid" in mix_lower or "rescue" in mix_lower:
                types.add("hybrid")
            if "iron" in mix_lower:
                types.add("irons")
            if "putter" in mix_lower:
                types.add("putter")
            return types

        latest_types = extract_club_types(latest_mix)
        if prior_sessions:
            prior_mix_combined = " ".join([s.get("club_mix", "") for s in prior_sessions])
            prior_types = extract_club_types(prior_mix_combined)

            # Detect missing club type (e.g., no driver when usually hit)
            missing_types = prior_types - latest_types
            if missing_types and latest_types:  # Only flag if we actually hit other clubs
                missing_label = ", ".join(sorted(missing_types))
                if "pw" in missing_label or "gw" in missing_label or "sw" in missing_label or "lw" in missing_label:
                    missing_label = missing_label.replace("pw", "Pitching Wedge").replace("gw", "Gap Wedge").replace("sw", "Sand Wedge").replace("lw", "Lob Wedge")
                recommendations.append(
                    {
                        "title": f"Note: Different composition today",
                        "focus_area": "practice composition",
                        "severity": 70,
                        "severity_label": "High",
                        "summary": (
                            f"Today you focused on {latest_mix.lower()}. This is different from your typical session, "
                            f"which explains metric fluctuations in carry, smash, and consistency."
                        ),
                        "evidence": f"Typical session includes: {missing_label}",
                    }
                )

    for club in club_summaries:
        club_label = club["club_label"]
        bias = club.get("avg_total_deviation_distance")
        if bias is None:
            bias = club.get("avg_carry_deviation_distance")
        if bias is not None and abs(bias) >= 10:
            recommendations.append(
                {
                    "title": f"Improve {club_label} start-line control",
                    "focus_area": "directional control",
                    "severity": min(100, round(abs(bias) * 4.0)),
                    "severity_label": _severity_label(min(100, round(abs(bias) * 4.0))),
                    "club_label": club_label,
                    "summary": (
                        f"Average offline is {abs(bias):.1f} yards {signed_direction_label(bias)}. "
                        "Work on start-line control with alignment-stick drills."
                    ),
                    "evidence": f"Average deviation: {bias:.1f} yds",
                }
            )

        face_std = club.get("face_to_path_stddev")
        avg_face_to_path = club.get("avg_face_to_path")
        if face_std is not None and face_std >= 6:
            recommendations.append(
                {
                    "title": f"Dial in {club_label} face-to-path",
                    "focus_area": "clubface control",
                    "severity": min(100, round(face_std * 9)),
                    "severity_label": _severity_label(min(100, round(face_std * 9))),
                    "club_label": club_label,
                    "summary": (
                        f"Face-to-path standard deviation is {face_std:.1f} degrees. "
                        "Use half-speed rehearsals and contact spray to stabilize delivery."
                    ),
                    "evidence": f"Face-to-path std dev: {face_std:.1f} deg",
                }
            )
        elif avg_face_to_path is not None and abs(avg_face_to_path) >= 5:
            recommendations.append(
                {
                    "title": f"Neutralize your {club_label} face-to-path bias",
                    "focus_area": "clubface control",
                    "severity": min(100, round(abs(avg_face_to_path) * 10)),
                    "severity_label": _severity_label(min(100, round(abs(avg_face_to_path) * 10))),
                    "club_label": club_label,
                    "summary": (
                        f"Average face-to-path is {avg_face_to_path:.1f} degrees. "
                        "Work on start line with gates or narrow targets."
                    ),
                    "evidence": f"Average face-to-path: {avg_face_to_path:.1f} deg",
                }
            )

        # Use the player's own potential (top-10%) as the smash benchmark.
        club_shots = [s for s in (all_shots or []) if s.get("club_label") == club_label]
        benchmark_smash = potential_smash_factor(club_label, club_shots)
        avg_smash = club.get("avg_smash_factor")
        if benchmark_smash is not None and avg_smash is not None and avg_smash <= benchmark_smash - 0.08:
            recommendations.append(
                {
                    "title": f"Improve centered contact with {club_label}",
                    "focus_area": "strike quality",
                    "severity": min(100, round((benchmark_smash - avg_smash) * 150)),
                    "severity_label": _severity_label(min(100, round((benchmark_smash - avg_smash) * 150))),
                    "club_label": club_label,
                    "summary": (
                        f"Average smash factor is {avg_smash:.2f} against your potential benchmark of {benchmark_smash:.2f}. "
                        "Prioritize centered strike drills before speed work."
                    ),
                    "evidence": f"Smash factor: {avg_smash:.2f} (potential: {benchmark_smash:.2f})",
                }
            )

        tempo_std = club.get("tempo_stddev")
        if tempo_std is not None and tempo_std >= 0.35:
            recommendations.append(
                {
                    "title": f"Stabilize {club_label} tempo",
                    "focus_area": "tempo",
                    "severity": min(100, round(tempo_std * 90)),
                    "severity_label": _severity_label(min(100, round(tempo_std * 90))),
                    "club_label": club_label,
                    "summary": (
                        f"Tempo swings by {tempo_std:.2f}. "
                        "Use a metronome or count-based routine to make backswing and transition more repeatable."
                    ),
                    "evidence": f"Tempo std dev: {tempo_std:.2f}",
                }
            )

        outlier_rate = club.get("outlier_rate")
        if outlier_rate is not None and outlier_rate >= 0.25:
            recommendations.append(
                {
                    "title": f"Build {club_label} shot pattern consistency",
                    "focus_area": "shot pattern",
                    "severity": min(100, round(outlier_rate * 120)),
                    "severity_label": _severity_label(min(100, round(outlier_rate * 120))),
                    "club_label": club_label,
                    "summary": (
                        f"{outlier_rate * 100:.0f}% of shots were flagged as pattern outliers by the anomaly model. "
                        "Favor repeatable stock swings and rebuild speed only after the strike window tightens."
                    ),
                    "evidence": f"Outlier rate: {outlier_rate * 100:.0f}%",
                }
            )

    # ── Gapping analysis: detect bunching (overlap) AND voids ───────────────
    sorted_clubs = sorted(
        [club for club in club_summaries if club.get("avg_carry_distance") is not None],
        key=lambda club: club["avg_carry_distance"],
    )
    for left, right in zip(sorted_clubs, sorted_clubs[1:]):
        gap = right["avg_carry_distance"] - left["avg_carry_distance"]
        left_std = left.get("carry_stddev") or 0.0
        right_std = right.get("carry_stddev") or 0.0
        overlap = (left_std + right_std) - gap

        if gap < 7 or overlap > 0:
            recommendations.append(
                {
                    "title": f"Gapping opportunity: {left['club_label']} and {right['club_label']}",
                    "focus_area": "distance gapping",
                    "severity": min(100, round(max(0, 7 - gap) * 8 + max(0, overlap) * 3)),
                    "severity_label": _severity_label(min(100, round(max(0, 7 - gap) * 8 + max(0, overlap) * 3))),
                    "club_label": f"{left['club_label']} → {right['club_label']}",
                    "summary": (
                        f"These clubs carry within {gap:.1f} yards of each other"
                        + (f" and their dispersion windows overlap by {overlap:.1f} yards" if overlap > 0 else "")
                        + ". Consider whether one club is redundant or a loft/shaft change would separate them."
                    ),
                    "evidence": f"Carry gap: {gap:.1f} yds | overlap: {max(0, overlap):.1f} yds",
                }
            )
        elif gap > 25:
            recommendations.append(
                {
                    "title": f"Distance void: {left['club_label']} to {right['club_label']}",
                    "focus_area": "distance gapping",
                    "severity": min(100, round((gap - 25) * 4)),
                    "severity_label": _severity_label(min(100, round((gap - 25) * 4))),
                    "club_label": f"{left['club_label']} → {right['club_label']}",
                    "summary": (
                        f"There is a {gap:.1f}-yard void between these clubs. "
                        "Evaluate adding a club (hybrid, utility iron, or strong-lofted wedge) to fill this window."
                    ),
                    "evidence": f"Carry gap: {gap:.1f} yds",
                }
            )

    # ── Data-quality advisory ────────────────────────────────────────────────
    total_shots = sum(s.get("shot_count", 0) for s in session_summaries)
    total_flagged = sum(s.get("flagged_shot_count", 0) for s in session_summaries)
    if total_shots > 0 and total_flagged / total_shots >= 0.10:
        flagged_pct = round(total_flagged / total_shots * 100)
        recommendations.append(
            {
                "title": "Review data quality: high rate of zero-value shots",
                "focus_area": "data quality",
                "severity": min(100, flagged_pct * 2),
                "severity_label": _severity_label(min(100, flagged_pct * 2)),
                "club_label": "all clubs",
                "summary": (
                    f"{flagged_pct}% of shots ({total_flagged}/{total_shots}) had zero ball speed or carry distance "
                    "and were excluded from averages. This is common when the Garmin R10 detects a swing but loses "
                    "the ball (e.g. hitting into a net seam or low-light conditions). "
                    "Consider re-checking your sensor placement and lighting."
                ),
                "evidence": f"Flagged shots: {total_flagged}/{total_shots}",
            }
        )

    recommendations.sort(key=lambda item: item["severity"], reverse=True)
    return recommendations[:10]


def chart_payload(session_summaries: list[dict[str, Any]], club_summaries: list[dict[str, Any]], sessions: list[dict[str, Any]]) -> dict[str, Any]:
    timeline_labels = []
    carry_trend = []
    smash_trend = []
    offline_trend = []
    for session in session_summaries:
        stamp = session.get("session_timestamp")
        label = stamp[:10] if stamp else session["source_file"]
        timeline_labels.append(label)
        carry_trend.append(round_or_none(session.get("avg_carry_distance")))
        smash_trend.append(round_or_none(session.get("avg_smash_factor"), 2))
        offline_trend.append(round_or_none(session.get("avg_offline_distance")))

    club_labels = [club["club_label"] for club in club_summaries]
    dispersion = []
    path_cloud = []
    for session_idx, session in enumerate(sessions):
        for shot in session["shots"]:
            y = first_value(shot.get("carry_distance"), shot.get("total_distance"))
            x = first_value(shot.get("carry_deviation_distance"), shot.get("total_deviation_distance"))
            if x is None or y is None:
                continue
            dispersion.append(
                {
                    "club": shot["club_label"],
                    "x": round(x, 1),
                    "y": round(y, 1),
                    "outlier": shot.get("is_outlier", False),
                    "session_index": session_idx,
                }
            )
            club_path = shot.get("club_path")
            face_to_path = shot.get("face_to_path")
            if isinstance(club_path, (int, float)) and isinstance(face_to_path, (int, float)):
                path_cloud.append(
                    {
                        "club": shot["club_label"],
                        "x": round(float(club_path), 2),
                        "y": round(float(face_to_path), 2),
                        "outlier": shot.get("is_outlier", False),
                        "session_index": session_idx,
                    }
                )

    miss_trend = []
    for session in session_summaries:
        miss_trend.append(round_or_none(session.get("avg_offline_distance")))

    return {
        "timeline": {
            "labels": timeline_labels,
            "avg_carry_distance": carry_trend,
            "avg_smash_factor": smash_trend,
            "avg_offline_distance": offline_trend,
            "miss_direction": miss_trend,
        },
        "clubs": {
            "labels": club_labels,
            "avg_carry_distance": [round_or_none(club.get("avg_carry_distance")) for club in club_summaries],
            "avg_smash_factor": [round_or_none(club.get("avg_smash_factor"), 2) for club in club_summaries],
            "consistency_score": [round_or_none(club.get("consistency_score")) for club in club_summaries],
        },
        "dispersion": dispersion,
        "path_cloud": path_cloud,
    }


def build_latest_session_deltas(session_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    if len(session_summaries) < 2:
        return {
            "available": False,
            "latest_label": None,
            "previous_label": None,
            "clubs": [],
        }

    previous = session_summaries[-2]
    latest = session_summaries[-1]

    previous_by_club = {club["club_label"]: club for club in previous.get("club_summaries", [])}
    latest_by_club = {club["club_label"]: club for club in latest.get("club_summaries", [])}
    shared_clubs = sorted(set(previous_by_club.keys()) & set(latest_by_club.keys()))

    club_deltas: list[dict[str, Any]] = []
    for club_label in shared_clubs:
        prev = previous_by_club[club_label]
        curr = latest_by_club[club_label]

        prev_offline = first_value(prev.get("avg_total_deviation_distance"), prev.get("avg_carry_deviation_distance"))
        curr_offline = first_value(curr.get("avg_total_deviation_distance"), curr.get("avg_carry_deviation_distance"))

        club_deltas.append(
            {
                "club_label": club_label,
                "latest_shot_count": curr.get("shot_count"),
                "carry_delta": round_or_none(
                    (curr.get("avg_carry_distance") - prev.get("avg_carry_distance"))
                    if curr.get("avg_carry_distance") is not None and prev.get("avg_carry_distance") is not None
                    else None,
                    1,
                ),
                "smash_delta": round_or_none(
                    (curr.get("avg_smash_factor") - prev.get("avg_smash_factor"))
                    if curr.get("avg_smash_factor") is not None and prev.get("avg_smash_factor") is not None
                    else None,
                    2,
                ),
                "offline_delta": round_or_none(
                    (curr_offline - prev_offline) if curr_offline is not None and prev_offline is not None else None,
                    1,
                ),
                "latest_avg_carry": round_or_none(curr.get("avg_carry_distance")),
                "latest_avg_smash": round_or_none(curr.get("avg_smash_factor"), 2),
                "latest_avg_offline": round_or_none(curr_offline),
            }
        )

    latest_label = latest.get("session_timestamp") or latest.get("source_file")
    previous_label = previous.get("session_timestamp") or previous.get("source_file")
    return {
        "available": True,
        "latest_label": latest_label,
        "previous_label": previous_label,
        "clubs": club_deltas,
    }


def build_next_session_worklist(
    session_summaries: list[dict[str, Any]],
    recommendations: list[dict[str, Any]],
    deltas: dict[str, Any],
) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []

    if deltas.get("available"):
        for club_delta in deltas.get("clubs", []):
            club_label = club_delta["club_label"]
            carry_delta = club_delta.get("carry_delta")
            smash_delta = club_delta.get("smash_delta")
            offline_delta = club_delta.get("offline_delta")

            if isinstance(carry_delta, (int, float)) and carry_delta <= -10:
                tasks.append(
                    {
                        "priority": 95,
                        "title": f"Rebuild {club_label} distance baseline",
                        "focus_area": "distance control",
                        "summary": f"Carry dropped by {abs(carry_delta):.1f} yds vs previous session.",
                        "evidence": f"Carry delta: {carry_delta:+.1f} yds",
                    }
                )
            if isinstance(smash_delta, (int, float)) and smash_delta <= -0.07:
                tasks.append(
                    {
                        "priority": 92,
                        "title": f"Prioritize centered contact with {club_label}",
                        "focus_area": "strike quality",
                        "summary": f"Smash factor trended down by {abs(smash_delta):.2f}.",
                        "evidence": f"Smash delta: {smash_delta:+.2f}",
                    }
                )
            if isinstance(offline_delta, (int, float)) and offline_delta >= 5:
                tasks.append(
                    {
                        "priority": 85,
                        "title": f"Tighten {club_label} start-line control",
                        "focus_area": "directional control",
                        "summary": f"Average offline miss widened by {offline_delta:.1f} yds.",
                        "evidence": f"Offline delta: {offline_delta:+.1f} yds",
                    }
                )

    if session_summaries:
        latest_session = session_summaries[-1]
        shot_count = latest_session.get("shot_count", 0) or 0
        flagged = latest_session.get("flagged_shot_count", 0) or 0
        if shot_count > 0:
            flagged_rate = flagged / shot_count
            if flagged_rate >= 0.08:
                tasks.append(
                    {
                        "priority": 88,
                        "title": "Check launch-monitor setup before warm-up",
                        "focus_area": "data quality",
                        "summary": "Too many zero-value shots can hide real progress.",
                        "evidence": f"Flagged shots: {flagged}/{shot_count} ({flagged_rate * 100:.0f}%)",
                    }
                )

    for recommendation in recommendations[:3]:
        tasks.append(
            {
                "priority": int(recommendation.get("severity", 50)),
                "title": recommendation.get("title", "Focus area for next session"),
                "focus_area": recommendation.get("focus_area", "practice"),
                "summary": recommendation.get("summary", ""),
                "evidence": recommendation.get("evidence", ""),
            }
        )

    deduped: list[dict[str, Any]] = []
    seen_titles: set[str] = set()
    for task in sorted(tasks, key=lambda item: item.get("priority", 0), reverse=True):
        title = str(task.get("title", "")).strip()
        if not title or title in seen_titles:
            continue
        seen_titles.add(title)
        deduped.append(task)
        if len(deduped) >= 6:
            break
    return deduped


def score_sessions(session_summaries: list[dict[str, Any]]) -> list[float | None]:
    """Return a 0-100 performance rating for each session, normalised across all sessions.

    The rating blends four signals with fixed weights:

    * Average consistency score  (40 %) — mean of per-club consistency scores
    * Average smash factor        (25 %) — higher is better
    * Average offline distance    (20 %) — absolute value, lower is better
    * Outlier rate                (15 %) — lower is better

    Each metric is min-max normalised to [0, 100] relative to the full set of
    sessions, so the best-ever session for each metric scores 100 and the worst
    scores 0.  When a metric is unavailable for a session its weight is
    redistributed to the remaining signals.

    With fewer than two sessions every score is ``None`` because a single data
    point cannot be ranked relative to itself.
    """
    if len(session_summaries) < 2:
        return [None] * len(session_summaries)

    WEIGHTS: dict[str, float] = {
        "consistency": 0.40,
        "smash": 0.25,
        "offline": 0.20,
        "outlier": 0.15,
    }

    # ── Collect raw metric values per session ────────────────────────────────
    raw: dict[str, list[float | None]] = {key: [] for key in WEIGHTS}
    for session in session_summaries:
        club_scores = [
            float(club["consistency_score"])
            for club in session.get("club_summaries", [])
            if isinstance(club.get("consistency_score"), (int, float))
        ]
        raw["consistency"].append(sum(club_scores) / len(club_scores) if club_scores else None)
        raw["smash"].append(
            float(session["avg_smash_factor"])
            if isinstance(session.get("avg_smash_factor"), (int, float))
            else None
        )
        offline = session.get("avg_offline_distance")
        raw["offline"].append(abs(float(offline)) if isinstance(offline, (int, float)) else None)
        outlier = session.get("outlier_rate")
        raw["outlier"].append(float(outlier) if isinstance(outlier, (int, float)) else None)

    # ── Min-max normalise each metric to [0, 100] ────────────────────────────
    def _normalize(values: list[float | None], invert: bool = False) -> list[float | None]:
        usable = [v for v in values if v is not None]
        if len(usable) < 2:
            return [50.0 if v is not None else None for v in values]
        lo, hi = min(usable), max(usable)
        if hi == lo:
            return [50.0 if v is not None else None for v in values]
        normed: list[float | None] = []
        for v in values:
            if v is None:
                normed.append(None)
                continue
            scaled = (v - lo) / (hi - lo) * 100.0
            normed.append(100.0 - scaled if invert else scaled)
        return normed

    normed: dict[str, list[float | None]] = {
        "consistency": _normalize(raw["consistency"], invert=False),
        "smash":       _normalize(raw["smash"],       invert=False),
        "offline":     _normalize(raw["offline"],      invert=True),
        "outlier":     _normalize(raw["outlier"],      invert=True),
    }

    # ── Weighted combination ──────────────────────────────────────────────────
    ratings: list[float | None] = []
    for i in range(len(session_summaries)):
        weighted_sum = 0.0
        total_weight = 0.0
        for key, weight in WEIGHTS.items():
            value = normed[key][i]
            if value is not None:
                weighted_sum += value * weight
                total_weight += weight
        if total_weight == 0.0:
            ratings.append(None)
        else:
            ratings.append(round(weighted_sum / total_weight, 1))
    return ratings


def _linear_forecast(values: list[float], steps: int = 3) -> dict[str, Any]:
    n = len(values)
    fit = linear_regression(list(range(n)), values)
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
        smash_values = club_smash.get(club, [])
        if len(carries) >= min_sessions:
            club_data["carry"] = _linear_forecast(carries)
        if len(smash_values) >= min_sessions:
            club_data["smash"] = _linear_forecast(smash_values)
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


def _club_velocity(club_label: str, session_summaries: list[dict[str, Any]], n: int = 3) -> str:
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
    fit = linear_regression(list(range(len(values))), values)
    if fit.slope > 1.5:
        return "Most improved"
    if fit.slope < -1.5:
        return "Work needed"
    return "Holding steady"


def _paired_values(shots: list[dict[str, Any]], left: str, right: str) -> list[tuple[float, float]]:
    pairs: list[tuple[float, float]] = []
    for shot in shots:
        a = shot.get(left)
        b = shot.get(right)
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            pairs.append((float(a), float(b)))
    return pairs


def _safe_slope(pairs: list[tuple[float, float]]) -> float | None:
    if len(pairs) < 3:
        return None
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    try:
        fit = linear_regression(xs, ys)
    except StatisticsError:
        return None
    return round(fit.slope, 4)


def _club_bag_order_key(club_label: str) -> tuple[int, int, str]:
    label = (club_label or "").strip().lower()

    if "driver" in label:
        return (0, 0, club_label)

    wood_match = re.search(r"(\d+)\s*wood|wood\s*(\d+)", label)
    if wood_match:
        number = next((int(part) for part in wood_match.groups() if part), 7)
        return (1, number, club_label)
    if "wood" in label:
        return (1, 99, club_label)

    hybrid_match = re.search(r"(\d+)\s*hybrid|hybrid\s*(\d+)", label)
    if hybrid_match:
        number = next((int(part) for part in hybrid_match.groups() if part), 4)
        return (2, number, club_label)
    if "hybrid" in label or "rescue" in label:
        return (2, 99, club_label)

    iron_match = re.search(r"(\d+)\s*iron|iron\s*(\d+)", label)
    if iron_match:
        number = next((int(part) for part in iron_match.groups() if part), 7)
        return (3, number, club_label)

    if "pitching" in label or re.search(r"\bpw\b", label):
        return (4, 0, club_label)
    if "gap" in label or "approach" in label or re.search(r"\baw\b|\bgw\b", label):
        return (4, 1, club_label)
    if "sand" in label or re.search(r"\bsw\b", label):
        return (4, 2, club_label)
    if "lob" in label or re.search(r"\blw\b", label):
        return (4, 3, club_label)
    if "wedge" in label:
        return (4, 9, club_label)

    if "putter" in label:
        return (5, 0, club_label)

    return (9, 99, club_label)


def _robust_carry_baseline(shots: list[dict[str, Any]]) -> float | None:
    carries = sorted(
        float(shot["carry_distance"])
        for shot in shots
        if isinstance(shot.get("carry_distance"), (int, float)) and float(shot["carry_distance"]) > 0
    )
    if not carries:
        return None
    top_count = max(3, ceil(len(carries) * 0.35))
    return float(median(carries[-top_count:]))


def _rollout_baseline(shots: list[dict[str, Any]]) -> float | None:
    rollout_values = [
        float(shot["total_distance"]) - float(shot["carry_distance"])
        for shot in shots
        if isinstance(shot.get("carry_distance"), (int, float))
        and isinstance(shot.get("total_distance"), (int, float))
        and float(shot["total_distance"]) >= float(shot["carry_distance"])
    ]
    rollout = average(rollout_values)
    if rollout is None:
        return None
    return max(0.0, min(30.0, float(rollout)))


def _minimum_gap_yards(previous_club: str, current_club: str) -> float:
    joined = f"{previous_club} {current_club}".lower()
    if any(token in joined for token in ["wedge", "pitching", "gap", "sand", "lob"]):
        return 6.0
    if any(token in joined for token in ["driver", "wood", "hybrid", "rescue"]):
        return 10.0
    return 8.0


def _goal_carry_anchor(club_label: str) -> float | None:
    label = (club_label or "").lower()
    if "driver" in label:
        return 200.0
    if re.search(r"\b3\s*hybrid\b|\bhybrid\s*3\b", label):
        return 175.0
    if re.search(r"\b5\s*iron\b|\biron\s*5\b", label):
        return 150.0
    if "pitching" in label or re.search(r"\bpw\b", label):
        return 95.0
    if "gap" in label or "approach" in label or re.search(r"\bgw\b|\baw\b", label):
        return 80.0
    if "sand" in label or re.search(r"\bsw\b", label):
        return 70.0
    if "lob" in label or re.search(r"\blw\b", label):
        return 60.0
    return None


def _automatic_gapping_targets(club_buckets: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, float | None]]:
    club_rows: list[dict[str, float | None | str]] = []
    for club_label, shots in club_buckets.items():
        carry_baseline = _robust_carry_baseline(shots)
        rollout_baseline = _rollout_baseline(shots)
        if carry_baseline is None:
            continue
        club_rows.append(
            {
                "club_label": club_label,
                "carry_baseline": carry_baseline,
                "rollout_baseline": rollout_baseline,
            }
        )

    club_rows.sort(key=lambda item: _club_bag_order_key(str(item["club_label"])))
    targets: dict[str, dict[str, float | None]] = {}
    if not club_rows:
        return targets

    goal_anchors: list[tuple[int, float]] = []
    for index, club in enumerate(club_rows):
        goal = _goal_carry_anchor(str(club["club_label"]))
        if goal is not None:
            goal_anchors.append((index, goal))

    goal_carries: list[float | None] = [None] * len(club_rows)
    if len(goal_anchors) >= 2:
        for index, goal in goal_anchors:
            goal_carries[index] = goal

        for (left_idx, left_goal), (right_idx, right_goal) in zip(goal_anchors, goal_anchors[1:]):
            span = right_idx - left_idx
            if span <= 1:
                continue
            for idx in range(left_idx + 1, right_idx):
                ratio = (idx - left_idx) / span
                goal_carries[idx] = left_goal + (right_goal - left_goal) * ratio

        first_idx, first_goal = goal_anchors[0]
        if first_idx > 0:
            if len(goal_anchors) >= 2 and goal_anchors[1][0] != first_idx:
                slope = (goal_anchors[1][1] - first_goal) / (goal_anchors[1][0] - first_idx)
            else:
                slope = -12.0
            for idx in range(first_idx - 1, -1, -1):
                goal_carries[idx] = (goal_carries[idx + 1] or first_goal) - slope

        last_idx, _ = goal_anchors[-1]
        for idx in range(last_idx + 1, len(club_rows)):
            goal_carries[idx] = (goal_carries[idx - 1] or 150.0) - 10.0

    previous_target: float | None = None
    previous_label = ""
    for index, club in enumerate(club_rows):
        club_label = str(club["club_label"])
        if goal_carries[index] is not None:
            target_carry = float(goal_carries[index] or 0.0)
        else:
            target_carry = float(club["carry_baseline"] or 0.0)
            if previous_target is not None:
                min_gap = _minimum_gap_yards(previous_label, club_label)
                target_carry = min(target_carry, previous_target - min_gap)
        target_carry = max(5.0, target_carry)

        rollout = float(club["rollout_baseline"]) if isinstance(club.get("rollout_baseline"), (int, float)) else None

        targets[club_label] = {
            "carry": round(target_carry, 0),
            "total": round(target_carry + rollout, 0) if rollout is not None else None,
        }

        previous_target = target_carry
        previous_label = club_label

    return targets


def build_spin_profile(club_buckets: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    per_club: dict[str, dict[str, float | int | None]] = {}
    for club_label, shots in club_buckets.items():
        spin_values = [shot.get("spin_rate") for shot in shots]
        axis_values = [shot.get("spin_axis") for shot in shots]
        launch_dir_values = [shot.get("launch_direction") for shot in shots]
        apex_values = [shot.get("apex_height") for shot in shots]
        per_club[club_label] = {
            "spin_rate_avg": round_or_none(average(spin_values)),
            "spin_rate_stddev": round_or_none(deviation(spin_values)),
            "spin_axis_avg": round_or_none(average(axis_values), 2),
            "spin_axis_stddev": round_or_none(deviation(axis_values), 2),
            "launch_direction_avg": round_or_none(average(launch_dir_values), 2),
            "launch_direction_stddev": round_or_none(deviation(launch_dir_values), 2),
            "apex_height_avg": round_or_none(average(apex_values), 1),
            "apex_height_stddev": round_or_none(deviation(apex_values), 1),
            "spin_to_launch_slope": _safe_slope(_paired_values(shots, "spin_axis", "launch_direction")),
            "sample_size": len(shots),
        }
    return {"per_club": per_club}


def build_tempo_profile(club_buckets: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    per_club: dict[str, dict[str, float | int | None]] = {}
    for club_label, shots in club_buckets.items():
        backswing = [shot.get("backswing_time") for shot in shots]
        downswing = [shot.get("downswing_time") for shot in shots]
        swing_tempo = [shot.get("swing_tempo") for shot in shots]
        target_tempo = [shot.get("target_tempo") for shot in shots]
        tempo_pairs = _paired_values(shots, "target_tempo", "swing_tempo")
        tempo_error_basis = "target"
        if tempo_pairs:
            tempo_error = [abs(actual - target) for target, actual in tempo_pairs]
            target_tempo_avg = round_or_none(average(target_tempo), 2)
        else:
            swing_values = [float(value) for value in swing_tempo if isinstance(value, (int, float))]
            baseline_tempo = median(swing_values) if swing_values else None
            tempo_error = [abs(value - baseline_tempo) for value in swing_values] if baseline_tempo is not None else []
            tempo_error_basis = "baseline"
            target_tempo_avg = round_or_none(baseline_tempo, 2)
        per_club[club_label] = {
            "backswing_time_avg": round_or_none(average(backswing), 3),
            "downswing_time_avg": round_or_none(average(downswing), 3),
            "swing_tempo_avg": round_or_none(average(swing_tempo), 2),
            "swing_tempo_stddev": round_or_none(deviation(swing_tempo), 2),
            "target_tempo_avg": target_tempo_avg,
            "tempo_error_avg": round_or_none(average(tempo_error), 2),
            "tempo_error_stddev": round_or_none(deviation(tempo_error), 2),
            "target_to_actual_tempo_slope": _safe_slope(tempo_pairs),
            "tempo_error_basis": tempo_error_basis,
            "sample_size": len(shots),
        }
    return {"per_club": per_club}


def build_target_control_profile(club_buckets: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    per_club: dict[str, dict[str, float | int | None]] = {}
    auto_targets = _automatic_gapping_targets(club_buckets)
    for club_label, shots in club_buckets.items():
        carry_target = auto_targets.get(club_label, {}).get("carry")
        total_target = auto_targets.get(club_label, {}).get("total")

        carry_pairs: list[tuple[float, float]] = []
        total_pairs: list[tuple[float, float]] = []
        manual_carry_count = 0
        manual_total_count = 0
        for shot in shots:
            carry = shot.get("carry_distance")
            total = shot.get("total_distance")

            shot_carry_target = shot.get("target_carry_distance")
            if isinstance(shot_carry_target, (int, float)):
                manual_carry_count += 1
            else:
                shot_carry_target = carry_target
            if isinstance(shot_carry_target, (int, float)) and isinstance(carry, (int, float)):
                carry_pairs.append((float(shot_carry_target), float(carry)))

            shot_total_target = shot.get("target_total_distance")
            if isinstance(shot_total_target, (int, float)):
                manual_total_count += 1
            else:
                shot_total_target = total_target
            if isinstance(shot_total_target, (int, float)) and isinstance(total, (int, float)):
                total_pairs.append((float(shot_total_target), float(total)))

        carry_error = [actual - target for target, actual in carry_pairs]
        total_error = [actual - target for target, actual in total_pairs]
        per_club[club_label] = {
            "auto_target_carry_distance_avg": round_or_none(carry_target, 0),
            "auto_target_total_distance_avg": round_or_none(total_target, 0),
            "carry_target_error_avg": round_or_none(average(carry_error), 1),
            "carry_target_error_stddev": round_or_none(deviation(carry_error), 1),
            "total_target_error_avg": round_or_none(average(total_error), 1),
            "total_target_error_stddev": round_or_none(deviation(total_error), 1),
            "carry_target_slope": _safe_slope(carry_pairs),
            "total_target_slope": _safe_slope(total_pairs),
            "target_shot_count": len(carry_pairs) + len(total_pairs),
            "manual_carry_target_count": manual_carry_count,
            "manual_total_target_count": manual_total_count,
        }
    return {"per_club": per_club}


def build_environment_profile(all_shots: list[dict[str, Any]]) -> dict[str, Any]:
    conditions = {
        "air_density_avg": round_or_none(average([shot.get("air_density") for shot in all_shots]), 3),
        "temperature_avg": round_or_none(average([shot.get("temperature") for shot in all_shots]), 1),
        "air_pressure_avg": round_or_none(average([shot.get("air_pressure") for shot in all_shots]), 2),
        "relative_humidity_avg": round_or_none(average([shot.get("relative_humidity") for shot in all_shots]), 1),
    }
    carry_temp_pairs = _paired_values(all_shots, "temperature", "carry_distance")
    carry_density_pairs = _paired_values(all_shots, "air_density", "carry_distance")
    return {
        "conditions": conditions,
        "carry_vs_temperature_slope": _safe_slope(carry_temp_pairs),
        "carry_vs_air_density_slope": _safe_slope(carry_density_pairs),
        "sample_size": len(all_shots),
    }


def _club_quality_profile(club_label: str | None) -> dict[str, tuple[float, float]]:
    club = (club_label or "").lower()
    if "driver" in club:
        return {
            "smash": (1.15, 1.65),
            "launch": (-5.0, 24.0),
            "spin": (800.0, 5000.0),
        }
    if "wood" in club or "hybrid" in club:
        return {
            "smash": (1.05, 1.55),
            "launch": (-2.0, 28.0),
            "spin": (1200.0, 7000.0),
        }
    if "wedge" in club or "pitching" in club or "sand" in club or "gap" in club or "lob" in club:
        return {
            "smash": (0.8, 1.35),
            "launch": (5.0, 50.0),
            "spin": (1500.0, 14000.0),
        }
    if "iron" in club:
        return {
            "smash": (0.9, 1.45),
            "launch": (0.0, 35.0),
            "spin": (1200.0, 10000.0),
        }
    return {
        "smash": (0.8, 1.6),
        "launch": (-10.0, 60.0),
        "spin": (200.0, 15000.0),
    }


def build_data_quality_profile(sessions: list[dict[str, Any]], all_shots: list[dict[str, Any]]) -> dict[str, Any]:
    flagged = [shot for shot in all_shots if shot.get("data_quality_flags")]
    total_shots = len(all_shots)
    reasons: dict[str, int] = defaultdict(int)
    critical_fields = [
        "club_speed",
        "ball_speed",
        "carry_distance",
        "total_distance",
        "smash_factor",
        "launch_angle",
        "spin_rate",
        "swing_tempo",
    ]

    def _suspicious_reason(shot: dict[str, Any]) -> list[str]:
        issues: list[str] = []
        carry = shot.get("carry_distance")
        total = shot.get("total_distance")
        smash = shot.get("smash_factor")
        launch = shot.get("launch_angle")
        spin = shot.get("spin_rate")
        offline = first_value(shot.get("total_deviation_distance"), shot.get("carry_deviation_distance"))
        club_label = str(shot.get("club_label") or "unknown")
        club_family = _club_quality_profile(club_label).get("label", "club")
        profile = _club_quality_profile(shot.get("club_label"))
        smash_min, smash_max = profile["smash"]
        launch_min, launch_max = profile["launch"]
        spin_min, spin_max = profile["spin"]

        if isinstance(total, (int, float)) and isinstance(carry, (int, float)) and total + 5 < carry:
            issues.append(f"{club_family}: total_lt_carry")
        if isinstance(smash, (int, float)) and (smash < smash_min or smash > smash_max):
            issues.append(f"{club_family}: smash_out_of_range")
        if isinstance(launch, (int, float)) and (launch < launch_min or launch > launch_max):
            issues.append(f"{club_family}: launch_out_of_range")
        if isinstance(spin, (int, float)) and (spin < spin_min or spin > spin_max):
            issues.append(f"{club_family}: spin_out_of_range")
        if isinstance(offline, (int, float)) and isinstance(carry, (int, float)) and abs(offline) > max(carry, 1):
            issues.append(f"{club_family}: offline_gt_carry")
        return issues

    for shot in flagged:
        for reason in shot.get("data_quality_flags", []):
            reasons[str(reason)] += 1

    missing_by_field: dict[str, int] = {}
    for field in critical_fields:
        missing_by_field[field] = sum(1 for shot in all_shots if shot.get(field) is None)

    suspicious_counts: dict[str, int] = defaultdict(int)
    suspicious_shot_count = 0
    for shot in all_shots:
        issues = _suspicious_reason(shot)
        if issues:
            suspicious_shot_count += 1
        for issue in issues:
            suspicious_counts[issue] += 1

    per_session: list[dict[str, Any]] = []
    for session in sessions:
        shot_count = len(session.get("shots", []))
        flagged_count = sum(1 for shot in session.get("shots", []) if shot.get("data_quality_flags"))
        missing_count = sum(
            1
            for shot in session.get("shots", [])
            if any(shot.get(field) is None for field in critical_fields)
        )
        suspicious_count = sum(1 for shot in session.get("shots", []) if _suspicious_reason(shot))
        per_session.append(
            {
                "session_id": session.get("session_id"),
                "source_file": session.get("source_file"),
                "session_timestamp": session.get("session_timestamp"),
                "shot_count": shot_count,
                "flagged_shot_count": flagged_count,
                "flagged_rate": round_or_none((flagged_count / shot_count) * 100 if shot_count else None, 1),
                "missing_critical_rate": round_or_none((missing_count / shot_count) * 100 if shot_count else None, 1),
                "suspicious_rate": round_or_none((suspicious_count / shot_count) * 100 if shot_count else None, 1),
            }
        )
    return {
        "total_shots": total_shots,
        "flagged_shot_count": len(flagged),
        "flagged_rate": round_or_none((len(flagged) / total_shots) * 100 if total_shots else None, 1),
        "flag_reasons": dict(sorted(reasons.items(), key=lambda item: item[1], reverse=True)),
        "missing_by_field": dict(sorted(missing_by_field.items(), key=lambda item: item[1], reverse=True)),
        "suspicious_checks": dict(sorted(suspicious_counts.items(), key=lambda item: item[1], reverse=True)),
        "suspicious_shot_count": suspicious_shot_count,
        "suspicious_rate": round_or_none((suspicious_shot_count / total_shots) * 100 if total_shots else None, 1),
        "per_session": per_session,
    }


def attach_recommendation_confidence(
    recommendations: list[dict[str, Any]],
    club_summaries: list[dict[str, Any]],
    data_quality: dict[str, Any],
) -> list[dict[str, Any]]:
    club_samples = {
        club.get("club_label"): int(club.get("shot_count") or 0)
        for club in club_summaries
    }
    quality_rate = data_quality.get("flagged_rate")
    quality_factor = 1.0
    if isinstance(quality_rate, (int, float)):
        # Higher flagged-shot rate lowers recommendation confidence.
        quality_factor = max(0.45, 1.0 - float(quality_rate) / 100.0)

    enriched: list[dict[str, Any]] = []
    for rec in recommendations:
        club_label = str(rec.get("club_label") or "")

        if "→" in club_label:
            parts = [p.strip() for p in club_label.split("→") if p.strip()]
            samples = [club_samples.get(p, 0) for p in parts]
            sample_size = int(sum(samples) / len(samples)) if samples else 0
        elif club_label == "all clubs":
            sample_size = int(sum(club_samples.values()) / max(len(club_samples), 1))
        else:
            sample_size = club_samples.get(club_label, 0)

        sample_factor = min(1.0, sample_size / 30.0)
        confidence_score = round((sample_factor * 0.65 + quality_factor * 0.35) * 100)
        if confidence_score >= 75:
            confidence_label = "High"
        elif confidence_score >= 50:
            confidence_label = "Medium"
        else:
            confidence_label = "Low"

        severity_score = float(rec.get("severity") or 0.0)
        # Blend severity and confidence so low-confidence items are deprioritized.
        severity_weight = 0.6
        confidence_weight = 0.4
        priority_score = round(severity_score * severity_weight + confidence_score * confidence_weight, 1)

        enriched.append(
            {
                **rec,
                "confidence_score": confidence_score,
                "confidence_label": confidence_label,
                "confidence_reason": f"Based on {sample_size} shots and {quality_factor * 100:.0f}% data-quality reliability.",
                "priority_score": priority_score,
                "priority_formula": {
                    "severity_weight": severity_weight,
                    "confidence_weight": confidence_weight,
                },
                "priority_reason": (
                    f"Rank score {priority_score:.1f} = severity {severity_score:.1f} x {severity_weight:.1f} "
                    f"+ confidence {confidence_score:.1f} x {confidence_weight:.1f}."
                ),
            }
        )
    enriched.sort(
        key=lambda rec: (
            float(rec.get("priority_score") or 0.0),
            float(rec.get("severity") or 0.0),
            float(rec.get("confidence_score") or 0.0),
        ),
        reverse=True,
    )
    return enriched


def _club_review_grade(club: dict[str, Any]) -> str:
    """Return 'good', 'bad', or 'ugly' for a single club based on key metrics."""
    issues = 0

    bias = club.get("avg_total_deviation_distance")
    if bias is None:
        bias = club.get("avg_carry_deviation_distance")
    if isinstance(bias, (int, float)) and abs(bias) >= 15:
        issues += 2
    elif isinstance(bias, (int, float)) and abs(bias) >= 8:
        issues += 1

    face_std = club.get("face_to_path_stddev")
    if isinstance(face_std, (int, float)) and face_std >= 8:
        issues += 2
    elif isinstance(face_std, (int, float)) and face_std >= 5:
        issues += 1

    outlier_rate = club.get("outlier_rate")
    if isinstance(outlier_rate, (int, float)):
        rate = outlier_rate / 100.0 if outlier_rate > 1 else outlier_rate
        if rate >= 0.35:
            issues += 2
        elif rate >= 0.20:
            issues += 1

    consistency = club.get("consistency_score")
    if isinstance(consistency, (int, float)):
        if consistency < 35:
            issues += 2
        elif consistency < 55:
            issues += 1

    if issues >= 4:
        return "ugly"
    if issues >= 2:
        return "bad"
    return "good"


def _club_review_notes(club: dict[str, Any]) -> list[str]:
    """Return a list of human-readable coaching observations for a single club."""
    notes: list[str] = []
    club_label = club.get("club_label", "this club")

    avg_carry = club.get("avg_carry_distance")
    carry_std = club.get("carry_stddev")
    if isinstance(avg_carry, (int, float)):
        note = f"Average carry: {avg_carry:.0f} yds"
        if isinstance(carry_std, (int, float)):
            note += f" (±{carry_std:.0f} yds)"
        notes.append(note)

    bias = club.get("avg_total_deviation_distance")
    if bias is None:
        bias = club.get("avg_carry_deviation_distance")
    if isinstance(bias, (int, float)):
        direction = "right" if bias > 0 else "left"
        if abs(bias) >= 8:
            notes.append(
                f"Offline bias: {abs(bias):.1f} yds {direction} — work on start-line alignment."
            )
        else:
            notes.append(f"Offline bias: {abs(bias):.1f} yds {direction} — solid direction control.")

    smash = club.get("avg_smash_factor")
    potential = club.get("potential_smash_factor")
    if isinstance(smash, (int, float)) and isinstance(potential, (int, float)):
        gap = potential - smash
        if gap >= 0.08:
            notes.append(
                f"Smash factor {smash:.2f} vs potential {potential:.2f} — centre-strike drills needed."
            )
        else:
            notes.append(f"Smash factor {smash:.2f} — good contact quality.")

    face_std = club.get("face_to_path_stddev")
    if isinstance(face_std, (int, float)):
        if face_std >= 6:
            notes.append(f"Face-to-path variability: {face_std:.1f}° — inconsistent delivery; use impact tape.")
        else:
            notes.append(f"Face-to-path variability: {face_std:.1f}° — face control is consistent.")

    outlier_rate = club.get("outlier_rate")
    if isinstance(outlier_rate, (int, float)):
        rate = outlier_rate / 100.0 if outlier_rate > 1 else outlier_rate
        if rate >= 0.20:
            notes.append(f"{rate * 100:.0f}% of shots were pattern outliers — focus on repeatable stock swings.")

    consistency = club.get("consistency_score")
    if isinstance(consistency, (int, float)):
        if consistency >= 70:
            notes.append(f"Consistency score: {consistency:.0f}/100 — excellent overall repeatability.")
        elif consistency >= 50:
            notes.append(f"Consistency score: {consistency:.0f}/100 — room to improve repeatability.")
        else:
            notes.append(f"Consistency score: {consistency:.0f}/100 — prioritise tighter, shorter swings.")

    return notes


def build_session_review(
    session_summary: dict[str, Any],
    all_session_summaries: list[dict[str, Any]],
    session_scores: list[float | None],
    session_index: int,
) -> dict[str, Any]:
    """Build a coaching review for a single session.

    Returns a dict with:
    * ``overview``        — high-level good/bad/ugly summary plus a numeric score
    * ``club_reviews``    — per-club grade, notes, and next-session focus
    * ``next_steps``      — 3-5 actionable priorities for the golfer's next visit
    """
    club_summaries = session_summary.get("club_summaries", [])
    shot_count = session_summary.get("shot_count", 0) or 0
    flagged_count = session_summary.get("flagged_shot_count", 0) or 0
    outlier_rate = session_summary.get("outlier_rate")
    avg_smash = session_summary.get("avg_smash_factor")
    avg_carry = session_summary.get("avg_carry_distance")
    avg_offline = session_summary.get("avg_offline_distance")
    session_score = session_scores[session_index] if session_index < len(session_scores) else None

    # ── Trend delta (vs previous session) ────────────────────────────────────
    trend_note: str | None = None
    if session_index > 0:
        prev = all_session_summaries[session_index - 1]
        prev_carry = prev.get("avg_carry_distance")
        if isinstance(avg_carry, (int, float)) and isinstance(prev_carry, (int, float)):
            delta = avg_carry - prev_carry
            if delta >= 3:
                trend_note = f"Carry improved by {delta:.1f} yds vs previous session. ↑"
            elif delta <= -3:
                trend_note = f"Carry dropped by {abs(delta):.1f} yds vs previous session. ↓"
            else:
                trend_note = "Carry distance held steady vs previous session. →"

    # ── Good / Bad / Ugly categorisation ─────────────────────────────────────
    good_items: list[str] = []
    bad_items: list[str] = []
    ugly_items: list[str] = []

    # Smash factor assessment
    if isinstance(avg_smash, (int, float)):
        if avg_smash >= 1.35:
            good_items.append(f"Strong contact quality — average smash factor {avg_smash:.2f}.")
        elif avg_smash >= 1.20:
            bad_items.append(f"Contact quality has room to improve — smash factor {avg_smash:.2f}.")
        else:
            ugly_items.append(f"Poor contact: smash factor only {avg_smash:.2f}. Prioritise centred-strike drills.")

    # Direction control
    if isinstance(avg_offline, (int, float)):
        abs_offline = abs(avg_offline)
        if abs_offline <= 5:
            good_items.append(f"Excellent direction control — average offline only {abs_offline:.1f} yds.")
        elif abs_offline <= 12:
            bad_items.append(f"Directional drift of {abs_offline:.1f} yds offline — alignment work recommended.")
        else:
            ugly_items.append(f"Severe offline bias: {abs_offline:.1f} yds average. Target gates and alignment drills needed urgently.")

    # Shot consistency / outlier rate
    if isinstance(outlier_rate, (int, float)):
        rate = outlier_rate / 100.0 if outlier_rate > 1 else outlier_rate
        if rate < 0.10:
            good_items.append(f"Shot pattern is tight — only {rate * 100:.0f}% outlier shots.")
        elif rate < 0.25:
            bad_items.append(f"{rate * 100:.0f}% of shots were outliers — work on repeatable swing mechanics.")
        else:
            ugly_items.append(f"High outlier rate: {rate * 100:.0f}%. Focus on short, controlled swings to rebuild consistency.")

    # Data quality (flagged shots)
    if shot_count > 0 and flagged_count / shot_count >= 0.10:
        flagged_pct = round(flagged_count / shot_count * 100)
        bad_items.append(
            f"{flagged_pct}% of shots were zero-value — check sensor positioning and lighting."
        )

    # Per-club grades
    good_clubs = [c["club_label"] for c in club_summaries if _club_review_grade(c) == "good"]
    bad_clubs  = [c["club_label"] for c in club_summaries if _club_review_grade(c) == "bad"]
    ugly_clubs = [c["club_label"] for c in club_summaries if _club_review_grade(c) == "ugly"]

    if good_clubs:
        good_items.append(f"Best clubs this session: {', '.join(good_clubs)}.")
    if bad_clubs:
        bad_items.append(f"Needs attention: {', '.join(bad_clubs)}.")
    if ugly_clubs:
        ugly_items.append(f"Struggled with: {', '.join(ugly_clubs)} — prioritise these next session.")

    # ── Per-club detailed reviews ─────────────────────────────────────────────
    club_reviews: list[dict[str, Any]] = []
    for club in club_summaries:
        grade = _club_review_grade(club)
        notes = _club_review_notes(club)
        bias = club.get("avg_total_deviation_distance") or club.get("avg_carry_deviation_distance")
        smash = club.get("avg_smash_factor")
        potential = club.get("potential_smash_factor")
        next_focus: str
        if grade == "ugly":
            next_focus = "Rebuild this club from scratch — short targets, slow swings, contact drills."
        elif grade == "bad":
            smash_gap = (potential - smash) if isinstance(smash, (int, float)) and isinstance(potential, (int, float)) else None
            face_std = club.get("face_to_path_stddev")
            if isinstance(smash_gap, float) and smash_gap >= 0.08:
                next_focus = "Prioritise centred-strike work — impact tape and tee drills."
            elif isinstance(face_std, (int, float)) and face_std >= 6:
                next_focus = "Stabilise face-to-path — half-speed rehearsals and narrow-gate targets."
            elif isinstance(bias, (int, float)) and abs(bias) >= 8:
                next_focus = "Use alignment sticks and start-line gate drills to tighten direction."
            else:
                next_focus = "Mix of issues — focus on one metric per bucket: start with carry distance."
        else:
            next_focus = "Maintain current form — challenge yourself with tighter targets or reduced swing speed."
        club_reviews.append(
            {
                "club_label": club.get("club_label"),
                "grade": grade,
                "shot_count": club.get("shot_count"),
                "avg_carry_distance": round_or_none(club.get("avg_carry_distance")),
                "avg_smash_factor": round_or_none(club.get("avg_smash_factor"), 2),
                "avg_offline": round_or_none(bias),
                "consistency_score": round_or_none(club.get("consistency_score")),
                "notes": notes,
                "next_focus": next_focus,
            }
        )

    # Sort so "ugly" first, then "bad", then "good"
    grade_order = {"ugly": 0, "bad": 1, "good": 2}
    club_reviews.sort(key=lambda r: grade_order.get(r["grade"], 3))

    # ── Next steps ────────────────────────────────────────────────────────────
    next_steps: list[str] = []
    for club_review in club_reviews:
        if club_review["grade"] in ("ugly", "bad"):
            next_steps.append(f"{club_review['club_label']}: {club_review['next_focus']}")
        if len(next_steps) >= 3:
            break
    if not next_steps:
        next_steps.append("Great session! Push your limits — tighten target windows or increase distance goals.")

    return {
        "session_id": session_summary.get("session_id"),
        "session_timestamp": session_summary.get("session_timestamp"),
        "source_file": session_summary.get("source_file"),
        "shot_count": shot_count,
        "club_mix": session_summary.get("club_mix"),
        "session_score": round_or_none(session_score),
        "trend_note": trend_note,
        "overview": {
            "good": good_items,
            "bad": bad_items,
            "ugly": ugly_items,
        },
        "club_reviews": club_reviews,
        "next_steps": next_steps,
    }


def build_session_reviews(
    session_summaries: list[dict[str, Any]],
    session_scores: list[float | None],
) -> list[dict[str, Any]]:
    """Return a coaching review for every session, most recent first."""
    reviews = [
        build_session_review(summary, session_summaries, session_scores, idx)
        for idx, summary in enumerate(session_summaries)
    ]
    reviews.reverse()
    return reviews


def build_analysis(sessions: list[dict[str, Any]], previous_forecasts: dict[str, Any] | None = None) -> dict[str, Any]:
    enriched_sessions = attach_ml_scores(sessions)

    # Collect all shots once so weights and benchmarks can use the full history.
    all_shots = [shot for session in enriched_sessions for shot in session["shots"]]

    club_buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for shot in all_shots:
        club_buckets[shot["club_label"]].append(shot)

    # First pass: build summaries without normalised weights.
    raw_club_summaries = [
        summarize_club(club_label, club_shots)
        for club_label, club_shots in sorted(club_buckets.items(), key=lambda item: item[0])
    ]

    # Derive population-calibrated consistency weights from the full club set.
    pop_weights = _consistency_weights(raw_club_summaries)

    # Second pass: rebuild summaries with calibrated weights.
    club_summaries = [
        summarize_club(club_label, club_buckets[club_label], pop_weights)
        for club_label in sorted(club_buckets.keys())
    ]

    session_summaries = [summarize_session(session, pop_weights) for session in enriched_sessions]

    forecasts = build_forecasts(session_summaries)
    spin_profile = build_spin_profile(club_buckets)
    tempo_profile = build_tempo_profile(club_buckets)
    target_control = build_target_control_profile(club_buckets)
    environment = build_environment_profile(all_shots)
    data_quality = build_data_quality_profile(enriched_sessions, all_shots)

    recommendations = build_recommendations(session_summaries, club_summaries, all_shots)
    latest_session_deltas = build_latest_session_deltas(session_summaries)
    recommendations = attach_recommendation_confidence(recommendations, club_summaries, data_quality)
    next_session_worklist = build_next_session_worklist(session_summaries, recommendations, latest_session_deltas)

    session_scores = score_sessions(session_summaries)
    session_reviews = build_session_reviews(session_summaries, session_scores)

    total_shots = sum(session["shot_count"] for session in session_summaries)
    avg_consistency = average([club.get("consistency_score") for club in club_summaries])
    avg_outlier_rate = average([session.get("outlier_rate") for session in session_summaries])
    generated_at = dt.datetime.now(dt.timezone.utc).isoformat()

    return {
        "generated_at": generated_at,
        "overview": {
            "total_sessions": len(session_summaries),
            "total_shots": total_shots,
            "tracked_clubs": len(club_summaries),
            "avg_consistency_score": round_or_none(avg_consistency),
            "avg_outlier_rate": round_or_none(avg_outlier_rate * 100 if avg_outlier_rate is not None else None),
        },
        "sessions": [
            {
                **session,
                "avg_carry_distance": round_or_none(session.get("avg_carry_distance")),
                "avg_total_distance": round_or_none(session.get("avg_total_distance")),
                "avg_smash_factor": round_or_none(session.get("avg_smash_factor"), 2),
                "avg_ball_speed": round_or_none(session.get("avg_ball_speed")),
                "avg_offline_distance": round_or_none(session.get("avg_offline_distance")),
                "outlier_rate": round_or_none(session.get("outlier_rate") * 100 if session.get("outlier_rate") is not None else None),
                "club_summaries": [
                    {
                        **club,
                        "avg_carry_distance": round_or_none(club.get("avg_carry_distance")),
                        "avg_total_distance": round_or_none(club.get("avg_total_distance")),
                        "avg_ball_speed": round_or_none(club.get("avg_ball_speed")),
                        "avg_smash_factor": round_or_none(club.get("avg_smash_factor"), 2),
                        "avg_face_to_path": round_or_none(club.get("avg_face_to_path"), 2),
                        "avg_club_path": round_or_none(club.get("avg_club_path"), 2),
                        "avg_attack_angle": round_or_none(club.get("avg_attack_angle"), 2),
                        "avg_spin_rate": round_or_none(club.get("avg_spin_rate")),
                        "avg_launch_angle": round_or_none(club.get("avg_launch_angle"), 1),
                        "avg_carry_deviation_distance": round_or_none(club.get("avg_carry_deviation_distance")),
                        "avg_total_deviation_distance": round_or_none(club.get("avg_total_deviation_distance")),
                        "avg_swing_tempo": round_or_none(club.get("avg_swing_tempo"), 2),
                        "carry_stddev": round_or_none(club.get("carry_stddev")),
                        "offline_stddev": round_or_none(club.get("offline_stddev")),
                        "face_to_path_stddev": round_or_none(club.get("face_to_path_stddev"), 2),
                        "tempo_stddev": round_or_none(club.get("tempo_stddev"), 2),
                        "consistency_score": round_or_none(club.get("consistency_score")),
                        "outlier_rate": round_or_none(club.get("outlier_rate") * 100 if club.get("outlier_rate") is not None else None),
                    }
                    for club in session["club_summaries"]
                ],
            }
            for session in session_summaries
        ],
        "clubs": [
            {
                **club,
                "avg_carry_distance": round_or_none(club.get("avg_carry_distance")),
                "avg_total_distance": round_or_none(club.get("avg_total_distance")),
                "avg_ball_speed": round_or_none(club.get("avg_ball_speed")),
                "avg_smash_factor": round_or_none(club.get("avg_smash_factor"), 2),
                "avg_face_to_path": round_or_none(club.get("avg_face_to_path"), 2),
                "avg_club_path": round_or_none(club.get("avg_club_path"), 2),
                "avg_attack_angle": round_or_none(club.get("avg_attack_angle"), 2),
                "avg_spin_rate": round_or_none(club.get("avg_spin_rate")),
                "avg_launch_angle": round_or_none(club.get("avg_launch_angle")),
                "avg_carry_deviation_distance": round_or_none(club.get("avg_carry_deviation_distance")),
                "avg_total_deviation_distance": round_or_none(club.get("avg_total_deviation_distance")),
                "avg_swing_tempo": round_or_none(club.get("avg_swing_tempo"), 2),
                "carry_stddev": round_or_none(club.get("carry_stddev")),
                "offline_stddev": round_or_none(club.get("offline_stddev")),
                "face_to_path_stddev": round_or_none(club.get("face_to_path_stddev"), 2),
                "tempo_stddev": round_or_none(club.get("tempo_stddev"), 2),
                "consistency_score": round_or_none(club.get("consistency_score")),
                "outlier_rate": round_or_none(club.get("outlier_rate") * 100 if club.get("outlier_rate") is not None else None),
                "improvement_velocity": _club_velocity(club["club_label"], session_summaries),
                "potential_gap_pct": potential_gap_pct(club),
            }
            for club in club_summaries
        ],
        "forecasts": forecasts,
        "spin_profile": spin_profile,
        "tempo_profile": tempo_profile,
        "target_control": target_control,
        "environment": environment,
        "data_quality": data_quality,
        "previous_forecasts": previous_forecasts or {},
        "recommendations": recommendations,
        "latest_session_deltas": latest_session_deltas,
        "next_session_worklist": next_session_worklist,
        "session_reviews": session_reviews,
        "charts": chart_payload(session_summaries, club_summaries, enriched_sessions),
    }
