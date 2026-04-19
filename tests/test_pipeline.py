from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from golf.cli import build_command


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


if __name__ == "__main__":
    unittest.main()
