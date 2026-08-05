from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "validate_production_plan.py"


def run_cli(plan: Path, profile: str = "standard") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--plan", str(plan), "--profile", profile],
        text=True,
        capture_output=True,
        check=False,
    )


def base_plan() -> dict[str, object]:
    return {
        "template_match": {
            "style": "雾瓷绿",
            "selected_templates": ["纪录片式素材穿插"],
            "banned_elements": ["可见网格", "完整烧录字幕"],
        },
        "timeline_duration": 30,
        "visual_budget": {
            "unique_real_sources": 3,
            "real_footage_seconds": 15,
        },
        "scenes": [
            {
                "id": "washer",
                "kind": "video",
                "timeline_start": 0,
                "timeline_end": 10,
                "source_path": "assets/washer.mp4",
                "source_start": 2,
                "source_end": 12,
            }
        ],
    }


class ProductionPlanTests(unittest.TestCase):
    def test_video_scene_cannot_outlast_its_source_window(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "plan.json"
            plan = base_plan()
            scene = plan["scenes"][0]
            assert isinstance(scene, dict)
            scene["timeline_end"] = 14
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            result = run_cli(plan_path)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("exceeds source", result.stderr.lower())

    def test_standard_profile_requires_material_budget_or_documented_exception(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "plan.json"
            plan = base_plan()
            budget = plan["visual_budget"]
            assert isinstance(budget, dict)
            budget["unique_real_sources"] = 1
            budget["real_footage_seconds"] = 4
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            result = run_cli(plan_path)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("standard profile", result.stderr.lower())

    def test_documented_exception_allows_a_constrained_standard_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "plan.json"
            plan = base_plan()
            budget = plan["visual_budget"]
            assert isinstance(budget, dict)
            budget.update({"unique_real_sources": 1, "real_footage_seconds": 4, "exception": "Only one licensed source is usable after decode checks."})
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            result = run_cli(plan_path)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
