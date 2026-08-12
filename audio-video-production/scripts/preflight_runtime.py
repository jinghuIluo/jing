#!/usr/bin/env python3
"""Check the local binaries required before an audio-led video render."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path


def resolve(explicit: str | None, env_name: str, fallbacks: list[str]) -> str | None:
    if explicit:
        path = Path(explicit).expanduser()
        return str(path.resolve()) if path.is_file() and os.access(path, os.X_OK) else None
    candidates = [os.environ.get(env_name), *fallbacks]
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate).expanduser()
        if path.is_file() and os.access(path, os.X_OK):
            return str(path.resolve())
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--renderer", choices=("hyperframes", "remotion"), required=True)
    parser.add_argument("--ffmpeg")
    parser.add_argument("--ffprobe")
    parser.add_argument("--node")
    parser.add_argument("--browser")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    binaries = {
        "ffmpeg": resolve(args.ffmpeg, "AUDIO_VIDEO_FFMPEG", [shutil.which("ffmpeg") or "", "/Users/anlinliu/Developer/video-use/.venv/lib/python3.12/site-packages/static_ffmpeg/bin/darwin_arm64/ffmpeg"]),
        "ffprobe": resolve(args.ffprobe, "AUDIO_VIDEO_FFPROBE", [shutil.which("ffprobe") or "", "/Users/anlinliu/Developer/video-use/.venv/lib/python3.12/site-packages/static_ffmpeg/bin/darwin_arm64/ffprobe"]),
        "node": resolve(args.node, "AUDIO_VIDEO_NODE", [shutil.which("node") or ""]),
        "browser": resolve(args.browser, "PRODUCER_HEADLESS_SHELL_PATH", ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "/Applications/Chromium.app/Contents/MacOS/Chromium"]),
    }
    errors = [f"{name} executable not found" for name, path in binaries.items() if not path]
    report = {"passed": not errors, "renderer": args.renderer, "binaries": binaries, "errors": errors}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"PASS: {args.renderer} runtime preflight")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
