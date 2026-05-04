from __future__ import annotations

import datetime as dt
from collections import defaultdict
from statistics import pstdev, quantiles
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
    return {
        "session_id": session["session_id"],
        "source_file": session["source_file"],
        "player": session.get("player"),
        "session_timestamp": session.get("session_timestamp"),
        "shot_count": len(shots),
        "club_count": len(club_summaries),
        "avg_carry_distance": average([shot.get("carry_distance") for shot in shots]),
        "avg_total_distance": average([shot.get("total_distance") for shot in shots]),
        "avg_smash_factor": average([shot.get("smash_factor") for shot in shots]),
        "avg_ball_speed": average([shot.get("ball_speed") for shot in shots]),
        "avg_offline_distance": avg_offline,
        "outlier_rate": average([1.0 if shot.get("is_outlier") else 0.0 for shot in shots]),
        "flagged_shot_count": session.get("flagged_shot_count", 0),
        "club_summaries": club_summaries,
    }


def build_recommendations(
    session_summaries: list[dict[str, Any]],
    club_summaries: list[dict[str, Any]],
    all_shots: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    recommendations: list[dict[str, Any]] = []

    for club in club_summaries:
        club_label = club["club_label"]
        bias = club.get("avg_total_deviation_distance")
        if bias is None:
            bias = club.get("avg_carry_deviation_distance")
        if bias is not None and abs(bias) >= 10:
            recommendations.append(
                {
                    "title": f"Reduce your {club_label} {signed_direction_label(bias)} miss",
                    "focus_area": "directional control",
                    "severity": min(100, round(abs(bias) * 2.5)),
                    "club_label": club_label,
                    "summary": (
                        f"Average dispersion is {abs(bias):.1f} yards {signed_direction_label(bias)}. "
                        "Practice start-line control and face delivery with alignment-stick work."
                    ),
                    "evidence": f"Average deviation: {bias:.1f} yds",
                }
            )

        face_std = club.get("face_to_path_stddev")
        avg_face_to_path = club.get("avg_face_to_path")
        if face_std is not None and face_std >= 6:
            recommendations.append(
                {
                    "title": f"Tighten {club_label} face-to-path variance",
                    "focus_area": "clubface control",
                    "severity": min(100, round(face_std * 9)),
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
                    "title": f"Trim high-variance {club_label} swings",
                    "focus_area": "shot pattern",
                    "severity": min(100, round(outlier_rate * 120)),
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
                    "title": f"Bunching: {left['club_label']} and {right['club_label']} overlap",
                    "focus_area": "distance gapping",
                    "severity": min(100, round(max(0, 7 - gap) * 8 + max(0, overlap) * 3)),
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
    return recommendations[:8]


def chart_payload(session_summaries: list[dict[str, Any]], club_summaries: list[dict[str, Any]], sessions: list[dict[str, Any]]) -> dict[str, Any]:
    timeline_labels = []
    carry_trend = []
    smash_trend = []
    offline_trend = []
    rating_trend = []
    for session in session_summaries:
        stamp = session.get("session_timestamp")
        label = stamp[:10] if stamp else session["source_file"]
        timeline_labels.append(label)
        carry_trend.append(round_or_none(session.get("avg_carry_distance")))
        smash_trend.append(round_or_none(session.get("avg_smash_factor"), 2))
        offline_trend.append(round_or_none(session.get("avg_offline_distance")))
        rating_trend.append(round_or_none(session.get("session_rating")))

    club_labels = [club["club_label"] for club in club_summaries]
    dispersion = []
    for session in sessions:
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
            "session_rating": rating_trend,
        },
        "clubs": {
            "labels": club_labels,
            "avg_carry_distance": [round_or_none(club.get("avg_carry_distance")) for club in club_summaries],
            "avg_smash_factor": [round_or_none(club.get("avg_smash_factor"), 2) for club in club_summaries],
            "consistency_score": [round_or_none(club.get("consistency_score")) for club in club_summaries],
        },
        "dispersion": dispersion,
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


def build_analysis(sessions: list[dict[str, Any]]) -> dict[str, Any]:
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

    # Compute per-session ratings (requires all session summaries to be ready).
    session_ratings = score_sessions(session_summaries)
    for i, summary in enumerate(session_summaries):
        summary["session_rating"] = session_ratings[i]
        prev_rating = session_ratings[i - 1] if i > 0 else None
        curr_rating = session_ratings[i]
        summary["session_rating_trend"] = (
            round(curr_rating - prev_rating, 1)
            if curr_rating is not None and prev_rating is not None
            else None
        )

    recommendations = build_recommendations(session_summaries, club_summaries, all_shots)
    latest_session_deltas = build_latest_session_deltas(session_summaries)
    next_session_worklist = build_next_session_worklist(session_summaries, recommendations, latest_session_deltas)

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
                "session_rating": session.get("session_rating"),
                "session_rating_trend": session.get("session_rating_trend"),
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
            }
            for club in club_summaries
        ],
        "recommendations": recommendations,
        "latest_session_deltas": latest_session_deltas,
        "next_session_worklist": next_session_worklist,
        "charts": chart_payload(session_summaries, club_summaries, enriched_sessions),
    }
