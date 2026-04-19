from __future__ import annotations

import math
from statistics import mean, pstdev
from typing import Any

FEATURE_FIELDS = (
    "ball_speed",
    "smash_factor",
    "carry_distance",
    "carry_deviation_distance",
    "face_to_path",
    "spin_rate",
    "swing_tempo",
)


def score_shot_anomalies(shots: list[dict[str, Any]]) -> dict[tuple[str, int], dict[str, float | bool]]:
    baselines: dict[str, tuple[float, float]] = {}
    for field in FEATURE_FIELDS:
        values = [shot[field] for shot in shots if isinstance(shot.get(field), (int, float))]
        if len(values) >= 2:
            deviation = pstdev(values)
            baselines[field] = (mean(values), deviation if deviation > 0 else 0.0)

    results: dict[tuple[str, int], dict[str, float | bool]] = {}
    for shot in shots:
        z_scores: list[float] = []
        for field, (center, spread) in baselines.items():
            value = shot.get(field)
            if value is None:
                continue
            if spread == 0:
                z_score = 0.0
            else:
                z_score = abs((value - center) / spread)
            if math.isfinite(z_score):
                z_scores.append(z_score)

        mean_score = mean(z_scores) if z_scores else 0.0
        max_score = max(z_scores, default=0.0)
        outlier = max_score >= 2.5 or mean_score >= 1.6
        results[(shot["session_id"], shot["shot_number"])] = {
            "anomaly_score": round(mean_score, 3),
            "max_feature_z": round(max_score, 3),
            "is_outlier": outlier,
        }
    return results
