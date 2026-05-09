from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from golf.cli import build_command
from golf.ingest import parse_float, parse_timestamp
from golf.analytics import score_sessions, build_forecasts, potential_gap_pct, build_recommendations


SAMPLE_CSV = """Date,Player,Club Name,Brand/Model,Club Type,Club Speed,Attack Angle,Club Path,Club Face,Face to Path,Ball Speed,Smash Factor,Launch Angle,Launch Direction,Backspin,Sidespin,Spin Rate,Spin Rate Type,Spin Axis,Apex Height,Carry Distance,Carry Deviation Angle,Carry Deviation Distance,Total Distance,Total Deviation Angle,Total Deviation Distance,Target Total Distance,Target Carry Distance,Note,Tag,Air Density,Temperature,Air Pressure,Relative Humidity,Back Stroke Length,Target Backswing Time,Target Downswing Time,Forward Stroke Length,Backswing Time,Downswing Time,Target Tempo,Swing Tempo
,,,,,[mph],[deg],[deg],[deg],[deg],[mph],,[deg],[deg],[rpm],[rpm],[rpm],,[deg],[yds],[Yards],[deg],[Yards],[Yards],[deg],[Yards],[Yards],[Yards],,,[g/L],[deg F],[kPa],[%],[Inches],[sec],[sec],[Inches],[sec],[sec],,
4/19/26 11:45:45,Jerry Gamblin,,,9 Iron,50,8,1,10,9,53,1.06,24,8,1200,190,1210,Estimated,-9,6,70,8,9,82,8,12,,,,,1.20,60,100.4,39,,,,,520,310,,1.7
4/19/26 11:46:45,Jerry Gamblin,,,9 Iron,52,7,-1,13,14,55,1.04,23,9,1400,-200,1410,Estimated,12,8,72,11,13,83,12,16,,,,,1.20,60,100.4,39,,,,,530,300,,2.8
4/19/26 11:47:45,Jerry Gamblin,,,Pitching Wedge,55,3,-2,5,7,58,1.02,28,4,2500,-400,2510,Estimated,8,10,64,5,6,75,5,6,,,,,1.20,60,100.4,39,,,,,560,220,,2.5
4/19/26 11:48:45,Jerry Gamblin,,,Pitching Wedge,57,2,-1,4,5,61,1.01,29,5,2600,-300,2610,Estimated,6,11,65,5,5,76,5,5,,,,,1.20,60,100.4,39,,,,,565,215,,3.4
"""


class PipelineTests(unittest.TestCase):
    def test_build_command_generates_analysis_and_site(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            data_dir = root / "Data"
            output_dir = root / "output" / "site"
            data_dir.mkdir(parents=True)
            (data_dir / "session.csv").write_text(SAMPLE_CSV, encoding="utf-8")

            analysis = build_command(data_dir, output_dir)

            self.assertEqual(analysis["overview"]["total_sessions"], 1)
            self.assertEqual(analysis["overview"]["tracked_clubs"], 2)
            self.assertTrue((output_dir / "analysis.json").exists())
            self.assertTrue((output_dir / "index.html").exists())
            self.assertTrue((output_dir / "site-data.js").exists())

            payload = json.loads((output_dir / "analysis.json").read_text(encoding="utf-8"))
            self.assertGreaterEqual(len(payload["recommendations"]), 1)
            self.assertEqual(payload["clubs"][0]["club_label"], "9 Iron")


class TestParseFloat(unittest.TestCase):
    def test_valid_integer_string(self) -> None:
        self.assertEqual(parse_float("42"), 42.0)

    def test_valid_float_string(self) -> None:
        self.assertAlmostEqual(parse_float("3.14"), 3.14)

    def test_valid_negative(self) -> None:
        self.assertAlmostEqual(parse_float("-7.5"), -7.5)

    def test_empty_string_returns_none(self) -> None:
        self.assertIsNone(parse_float(""))

    def test_whitespace_only_returns_none(self) -> None:
        self.assertIsNone(parse_float("   "))

    def test_non_numeric_text_returns_none(self) -> None:
        self.assertIsNone(parse_float("abc"))

    def test_mixed_alphanumeric_returns_none(self) -> None:
        self.assertIsNone(parse_float("12px"))

    def test_bracketed_unit_annotation_returns_none(self) -> None:
        self.assertIsNone(parse_float("[mph]"))

    def test_leading_and_trailing_whitespace_stripped(self) -> None:
        self.assertAlmostEqual(parse_float("  1.5  "), 1.5)

    def test_zero_string(self) -> None:
        self.assertEqual(parse_float("0"), 0.0)


class TestParseTimestamp(unittest.TestCase):
    def test_short_year_format(self) -> None:
        result = parse_timestamp("4/19/26 11:45:45")
        self.assertIsNotNone(result)
        self.assertTrue(result.startswith("2026-04-19"))

    def test_four_digit_year_format(self) -> None:
        result = parse_timestamp("04/19/2026 11:45:45")
        self.assertIsNotNone(result)
        self.assertTrue(result.startswith("2026-04-19"))

    def test_empty_string_returns_none(self) -> None:
        self.assertIsNone(parse_timestamp(""))

    def test_whitespace_only_returns_none(self) -> None:
        self.assertIsNone(parse_timestamp("   "))

    def test_plain_text_returns_none(self) -> None:
        self.assertIsNone(parse_timestamp("not-a-date"))

    def test_partial_date_returns_none(self) -> None:
        self.assertIsNone(parse_timestamp("4/19/26"))

    def test_iso_format_not_supported_returns_none(self) -> None:
        # The parser only supports MM/DD/YY and MM/DD/YYYY; ISO strings should
        # return None rather than raise.
        self.assertIsNone(parse_timestamp("2026-04-19T11:45:45"))

    def test_result_is_iso_string(self) -> None:
        result = parse_timestamp("4/19/26 11:45:45")
        self.assertIsInstance(result, str)
        # Basic ISO-8601 shape check
        self.assertRegex(result, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")

    def test_whitespace_stripped_before_parse(self) -> None:
        result = parse_timestamp("  4/19/26 11:45:45  ")
        self.assertIsNotNone(result)


# ── Garmin R10-specific ingestion tests ──────────────────────────────────────

# Simulates the Garmin Golf app's activity/round export: several metadata rows
# followed by "Shot Number,Club,..." headers (no timestamp column).
GARMIN_ROUND_CSV = """\
Session Title,My Practice Round
Date,2026-04-19
Player,Jerry Gamblin
Notes,Warm-up session at the range

Shot Number,Club,Ball Speed (mph),Club Speed (mph),Carry (yds),Total (yds),Offline (yds),Launch Angle (deg),Spin Rate (rpm),Smash Factor
1,9 Iron,120,88,148,162,-3,19,6800,1.36
2,9 Iron,118,87,145,159,2,18,6900,1.36
3,9 Iron,0,85,0,0,-1,17,0,0
4,Pitching Wedge,105,79,120,130,4,22,7200,1.33
5,Pitching Wedge,107,80,123,133,-2,21,7100,1.34
"""

# Simulates the Garmin Golf app's range export (FlightScope-style headers) but
# with a BOM and units-suffixed column names.
GARMIN_RANGE_SUFFIXED_CSV = """\
Date,Player,Club Type,Ball Speed (mph),Club Speed (mph),Carry (yds),Total (yds),Offline (yds),Launch Angle (deg),Smash Factor,Apex Height (ft)
,,,[mph],[mph],[yds],[yds],[yds],[deg],,[ft]
4/19/26 11:50:00,Jerry Gamblin,7 Iron,130,91,165,178,5,19,1.43,82
4/19/26 11:51:00,Jerry Gamblin,7 Iron,128,90,162,175,-3,18,1.42,80
4/19/26 11:52:00,Jerry Gamblin,7 Iron,131,92,168,181,2,20,1.42,85
"""


class TestGarminR10Ingestion(unittest.TestCase):
    """Verify that Garmin-specific CSV quirks are handled correctly."""

    def _write_and_load(self, csv_text: str) -> dict:
        from golf.ingest import load_session

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "session.csv"
            path.write_text(csv_text, encoding="utf-8")
            return load_session(path)

    # ── Preamble rows are skipped ──────────────────────────────────────────
    def test_metadata_preamble_rows_skipped(self) -> None:
        session = self._write_and_load(GARMIN_ROUND_CSV)
        self.assertGreater(len(session["shots"]), 0, "No shots were parsed")

    def test_correct_shot_count_after_preamble(self) -> None:
        session = self._write_and_load(GARMIN_ROUND_CSV)
        # Row 3 has ball_speed=0 → cleaned to None but still a shot row.
        self.assertEqual(len(session["shots"]), 5)

    # ── Club column maps to club_label ─────────────────────────────────────
    def test_club_column_maps_to_club_label(self) -> None:
        session = self._write_and_load(GARMIN_ROUND_CSV)
        club_labels = {shot["club_label"] for shot in session["shots"]}
        self.assertIn("9 Iron", club_labels)
        self.assertIn("Pitching Wedge", club_labels)

    # ── Unit-suffixed column names resolve correctly ────────────────────────
    def test_unit_suffixed_ball_speed_maps_correctly(self) -> None:
        session = self._write_and_load(GARMIN_RANGE_SUFFIXED_CSV)
        shot = session["shots"][0]
        self.assertIsNotNone(shot.get("ball_speed"), "ball_speed should be parsed")
        self.assertAlmostEqual(shot["ball_speed"], 130.0, places=1)

    def test_unit_suffixed_carry_maps_correctly(self) -> None:
        session = self._write_and_load(GARMIN_RANGE_SUFFIXED_CSV)
        shot = session["shots"][0]
        self.assertIsNotNone(shot.get("carry_distance"))
        self.assertAlmostEqual(shot["carry_distance"], 165.0, places=1)

    def test_apex_height_in_feet_converted_to_yards(self) -> None:
        session = self._write_and_load(GARMIN_RANGE_SUFFIXED_CSV)
        shot = session["shots"][0]
        apex = shot.get("apex_height")
        self.assertIsNotNone(apex)
        # 82 ft × 0.33333 ≈ 27.3 yds
        self.assertAlmostEqual(apex, 82 * 0.33333, places=1)

    # ── Zero-value phantom shot cleaning ──────────────────────────────────
    def test_zero_ball_speed_nulled(self) -> None:
        session = self._write_and_load(GARMIN_ROUND_CSV)
        flagged = [s for s in session["shots"] if s.get("data_quality_flags")]
        self.assertEqual(len(flagged), 1, "Expected exactly one flagged shot")
        self.assertIsNone(flagged[0]["ball_speed"])

    def test_zero_carry_nulled(self) -> None:
        session = self._write_and_load(GARMIN_ROUND_CSV)
        flagged = [s for s in session["shots"] if s.get("data_quality_flags")]
        self.assertIsNone(flagged[0].get("carry_distance"))

    def test_data_quality_flag_label_correct(self) -> None:
        session = self._write_and_load(GARMIN_ROUND_CSV)
        flagged = [s for s in session["shots"] if s.get("data_quality_flags")]
        flags = flagged[0]["data_quality_flags"]
        self.assertIn("zero_ball_speed", flags)

    def test_flagged_shot_count_in_session(self) -> None:
        session = self._write_and_load(GARMIN_ROUND_CSV)
        self.assertEqual(session["flagged_shot_count"], 1)

    # ── Non-flagged shots have valid numeric values ────────────────────────
    def test_clean_shots_have_ball_speed(self) -> None:
        session = self._write_and_load(GARMIN_ROUND_CSV)
        clean = [s for s in session["shots"] if not s.get("data_quality_flags")]
        for shot in clean:
            self.assertIsNotNone(shot.get("ball_speed"))
            self.assertGreater(shot["ball_speed"], 0)

    # ── Full pipeline processes Garmin round CSV without error ─────────────
    def test_full_pipeline_garmin_round_format(self) -> None:
        from golf.cli import build_command

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "Data"
            output_dir = root / "output" / "site"
            data_dir.mkdir(parents=True)
            (data_dir / "garmin_round.csv").write_text(GARMIN_ROUND_CSV, encoding="utf-8")
            analysis = build_command(data_dir, output_dir)
            self.assertGreaterEqual(analysis["overview"]["total_shots"], 4)
            self.assertGreaterEqual(analysis["overview"]["tracked_clubs"], 2)


class TestScoreSessions(unittest.TestCase):
    """Unit tests for the session performance rating function."""

    def _make_session(
        self,
        avg_smash: float | None,
        avg_offline: float | None,
        outlier_rate: float | None,
        consistency: float | None,
    ) -> dict:
        club = {"consistency_score": consistency} if consistency is not None else {}
        return {
            "avg_smash_factor": avg_smash,
            "avg_offline_distance": avg_offline,
            "outlier_rate": outlier_rate,
            "club_summaries": [club] if club else [],
        }

    def test_single_session_returns_none(self) -> None:
        result = score_sessions([self._make_session(1.3, 5.0, 0.1, 70.0)])
        self.assertEqual(result, [None])

    def test_empty_list_returns_empty(self) -> None:
        self.assertEqual(score_sessions([]), [])

    def test_two_sessions_return_two_values(self) -> None:
        sessions = [
            self._make_session(1.25, 8.0, 0.2, 60.0),
            self._make_session(1.35, 4.0, 0.1, 80.0),
        ]
        result = score_sessions(sessions)
        self.assertEqual(len(result), 2)
        self.assertIsNotNone(result[0])
        self.assertIsNotNone(result[1])

    def test_better_session_has_higher_rating(self) -> None:
        # Second session has better smash, less offline, lower outlier rate,
        # higher consistency — it should always score higher.
        sessions = [
            self._make_session(1.20, 12.0, 0.30, 55.0),
            self._make_session(1.40, 2.0, 0.05, 90.0),
        ]
        result = score_sessions(sessions)
        self.assertGreater(result[1], result[0])

    def test_ratings_in_zero_to_hundred_range(self) -> None:
        sessions = [
            self._make_session(1.30, 6.0, 0.15, 70.0),
            self._make_session(1.38, 3.0, 0.08, 85.0),
            self._make_session(1.22, 10.0, 0.25, 50.0),
        ]
        result = score_sessions(sessions)
        for rating in result:
            if rating is not None:
                self.assertGreaterEqual(rating, 0.0)
                self.assertLessEqual(rating, 100.0)

    def test_identical_sessions_get_midpoint_rating(self) -> None:
        session = self._make_session(1.30, 5.0, 0.10, 70.0)
        result = score_sessions([session, session])
        # When all values are equal each metric is clamped to 50.
        for rating in result:
            self.assertAlmostEqual(rating, 50.0, places=1)

    def test_session_rating_included_in_pipeline_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            data_dir = root / "Data"
            output_dir = root / "output" / "site"
            data_dir.mkdir(parents=True)
            (data_dir / "session.csv").write_text(SAMPLE_CSV, encoding="utf-8")
            analysis = build_command(data_dir, output_dir)
            # With one session, rating should be None (not enough data to rank).
            self.assertIn("session_rating", analysis["sessions"][0])
            self.assertIsNone(analysis["sessions"][0]["session_rating"])


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
        self.assertAlmostEqual(result, 88.3, places=1)

    def test_potential_gap_pct_missing_returns_none(self) -> None:
        self.assertIsNone(potential_gap_pct({"avg_smash_factor": None, "potential_smash_factor": 1.45}))
        self.assertIsNone(potential_gap_pct({"avg_smash_factor": 1.28, "potential_smash_factor": None}))

    def test_potential_gap_pct_capped_at_100(self) -> None:
        club = {"avg_smash_factor": 1.50, "potential_smash_factor": 1.45}
        self.assertLessEqual(potential_gap_pct(club), 100.0)


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


if __name__ == "__main__":
    unittest.main()
