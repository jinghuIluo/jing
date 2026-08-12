#!/usr/bin/env python3
"""Validate template selection, material budget, and timed video source windows."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def number(value: Any, field: str, errors: list[str]) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        errors.append(f"{field} must be a number")
        return 0.0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--profile", choices=("fast", "standard", "premium"), default="standard")
    args = parser.parse_args()
    errors: list[str] = []
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    template = plan.get("template_match")
    if not isinstance(template, dict):
        errors.append("template_match is required")
    else:
        if not isinstance(template.get("style"), str) or not template["style"].strip():
            errors.append("template_match.style is required")
        if not isinstance(template.get("selected_templates"), list) or not template["selected_templates"]:
            errors.append("template_match.selected_templates is required")
        if not isinstance(template.get("banned_elements"), list) or not template["banned_elements"]:
            errors.append("template_match.banned_elements is required")

    duration = number(plan.get("timeline_duration"), "timeline_duration", errors)
    if duration <= 0:
        errors.append("timeline_duration must be positive")
    budget = plan.get("visual_budget")
    if not isinstance(budget, dict):
        errors.append("visual_budget is required")
        budget = {}
    source_count = number(budget.get("unique_real_sources"), "visual_budget.unique_real_sources", errors)
    footage_seconds = number(budget.get("real_footage_seconds"), "visual_budget.real_footage_seconds", errors)
    exception = budget.get("exception")
    if args.profile == "standard" and not (isinstance(exception, str) and exception.strip()):
        if source_count < 3 or footage_seconds < duration * 0.4:
            errors.append("standard profile requires 3 real sources and 40% real footage, or a documented exception")
    if args.profile == "premium" and not (isinstance(exception, str) and exception.strip()):
        if source_count < 5 or footage_seconds < duration * 0.6:
            errors.append("premium profile requires 5 real sources and 60% real footage, or a documented exception")

    scenes = plan.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        errors.append("scenes is required")
        scenes = []
    ids: set[str] = set()
    for index, scene in enumerate(scenes, 1):
        if not isinstance(scene, dict):
            errors.append(f"scene {index} must be an object")
            continue
        scene_id = scene.get("id")
        if not isinstance(scene_id, str) or not scene_id.strip():
            errors.append(f"scene {index} id is required")
            scene_id = f"scene-{index}"
        if scene_id in ids:
            errors.append(f"scene id duplicated: {scene_id}")
        ids.add(scene_id)
        start = number(scene.get("timeline_start"), f"scene {scene_id} timeline_start", errors)
        end = number(scene.get("timeline_end"), f"scene {scene_id} timeline_end", errors)
        if end <= start:
            errors.append(f"scene {scene_id} timeline end must be after start")
        if end > duration + 0.001:
            errors.append(f"scene {scene_id} extends beyond timeline_duration")
        if scene.get("kind") != "video":
            continue
        if not isinstance(scene.get("source_path"), str) or not scene["source_path"].strip():
            errors.append(f"video scene {scene_id} source_path is required")
            continue
        source_start = number(scene.get("source_start"), f"scene {scene_id} source_start", errors)
        source_end = number(scene.get("source_end"), f"scene {scene_id} source_end", errors)
        if source_end <= source_start:
            errors.append(f"video scene {scene_id} source end must be after start")
        elif end - start > source_end - source_start + 0.001:
            errors.append(f"video scene {scene_id} exceeds source duration; trim or replace it")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"PASS: validated {len(scenes)} scenes for {args.profile}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
