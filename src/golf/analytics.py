from __future__ import annotations

import datetime as dt
from collections import defaultdict
from statistics import pstdev
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


def expected_smash_factor(club_label: str) -> float | None:
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


def signed_direction_label(value: float) -> str:
    return "right" if value > 0 else "left"


def consistency_score(summary: dict[str, Any]) -> float | None:
    carry_cv = summary.get("carry_cv")
    offline_std = summary.get("offline_stddev")
    face_std = summary.get("face_to_path_stddev")
    tempo_cv = summary.get("tempo_cv")

    pieces = []
    if carry_cv is not None:
        pieces.append(carry_cv * 120)
    if offline_std is not None:
        pieces.append(offline_std * 1.3)
    if face_std is not None:
        pieces.append(face_std * 4)
    if tempo_cv is not None:
        pieces.append(tempo_cv * 90)
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


def summarize_club(club_label: str, shots: list[dict[str, Any]]) -> dict[str, Any]:
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
    }
    summary["consistency_score"] = consistency_score(summary)
    return summary


def summarize_session(session: dict[str, Any]) -> dict[str, Any]:
    shots = session["shots"]
    clubs: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for shot in shots:
        clubs[shot["club_label"]].append(shot)

    club_summaries = [
        summarize_club(club_label, club_shots)
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
        "club_summaries": club_summaries,
    }


def build_recommendations(
    session_summaries: list[dict[str, Any]],
    club_summaries: list[dict[str, Any]],
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

        expected_smash = expected_smash_factor(club_label)
        avg_smash = club.get("avg_smash_factor")
        if expected_smash is not None and avg_smash is not None and avg_smash <= expected_smash - 0.08:
            recommendations.append(
                {
                    "title": f"Improve centered contact with {club_label}",
                    "focus_area": "strike quality",
                    "severity": min(100, round((expected_smash - avg_smash) * 150)),
                    "club_label": club_label,
                    "summary": (
                        f"Average smash factor is {avg_smash:.2f} against an expected benchmark near {expected_smash:.2f}. "
                        "Prioritize centered strike drills before speed work."
                    ),
                    "evidence": f"Smash factor: {avg_smash:.2f}",
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

    sorted_clubs = sorted(
        [club for club in club_summaries if club.get("avg_carry_distance") is not None],
        key=lambda club: club["avg_carry_distance"],
    )
    for left, right in zip(sorted_clubs, sorted_clubs[1:]):
        gap = right["avg_carry_distance"] - left["avg_carry_distance"]
        if gap < 7 or gap > 25:
            recommendations.append(
                {
                    "title": f"Check the gap between {left['club_label']} and {right['club_label']}",
                    "focus_area": "distance gapping",
                    "severity": min(100, round(abs(15 - gap) * 5)),
                    "club_label": f"{left['club_label']} -> {right['club_label']}",
                    "summary": (
                        f"The current carry gap is {gap:.1f} yards. "
                        "Use a focused gapping session to confirm whether this is a true distance bucket or a strike-quality artifact."
                    ),
                    "evidence": f"Carry gap: {gap:.1f} yds",
                }
            )

    recommendations.sort(key=lambda item: item["severity"], reverse=True)
    return recommendations[:8]


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

    return {
        "timeline": {
            "labels": timeline_labels,
            "avg_carry_distance": carry_trend,
            "avg_smash_factor": smash_trend,
            "avg_offline_distance": offline_trend,
        },
        "clubs": {
            "labels": club_labels,
            "avg_carry_distance": [round_or_none(club.get("avg_carry_distance")) for club in club_summaries],
            "avg_smash_factor": [round_or_none(club.get("avg_smash_factor"), 2) for club in club_summaries],
            "consistency_score": [round_or_none(club.get("consistency_score")) for club in club_summaries],
        },
        "dispersion": dispersion,
    }


def build_analysis(sessions: list[dict[str, Any]]) -> dict[str, Any]:
    enriched_sessions = attach_ml_scores(sessions)
    session_summaries = [summarize_session(session) for session in enriched_sessions]

    club_buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for session in enriched_sessions:
        for shot in session["shots"]:
            club_buckets[shot["club_label"]].append(shot)
    club_summaries = [
        summarize_club(club_label, club_shots)
        for club_label, club_shots in sorted(club_buckets.items(), key=lambda item: item[0])
    ]

    recommendations = build_recommendations(session_summaries, club_summaries)

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
            }
            for club in club_summaries
        ],
        "recommendations": recommendations,
        "charts": chart_payload(session_summaries, club_summaries, enriched_sessions),
    }
