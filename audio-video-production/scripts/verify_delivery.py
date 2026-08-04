#!/usr/bin/env python3
"""Verify a rendered short video against its source audio and delivery contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def find_binary(name: str) -> str | None:
    candidates = [
        os.environ.get(f"AUDIO_VIDEO_{name.upper()}"),
        shutil.which(name),
        f"/Users/anlinliu/Documents/短视频制作/英国钢厂风险短片/tools/ffmpeg/{name}",
        f"/Users/anlinliu/Developer/video-use/.venv/lib/python3.12/site-packages/static_ffmpeg/bin/darwin_arm64/{name}",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return candidate
    return None


def run_json(command: list[str]) -> dict[str, Any]:
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "media probe failed")
    return json.loads(result.stdout)


def probe_media(ffprobe: str, path: Path) -> dict[str, Any]:
    return run_json(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration,size:stream=index,codec_name,codec_type,width,height,r_frame_rate,avg_frame_rate,sample_rate,channels",
            "-of",
            "json",
            str(path),
        ]
    )


def ratio(value: str | None) -> float:
    if not value or value == "0/0":
        return 0.0
    numerator, denominator = value.split("/", 1)
    return float(numerator) / float(denominator)


def frame_hash(ffmpeg: str, path: Path, timestamp: float, region: list[int] | None = None) -> str:
    command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-ss", f"{timestamp:.3f}", "-i", str(path), "-frames:v", "1"]
    if region:
        x, y, width, height = region
        command += ["-vf", f"crop={width}:{height}:{x}:{y}"]
    command += ["-f", "image2pipe", "-vcodec", "png", "-"]
    result = subprocess.run(command, capture_output=True, check=False)
    if result.returncode != 0 or not result.stdout:
        raise RuntimeError(result.stderr.decode("utf-8", errors="replace").strip() or "frame extraction failed")
    return hashlib.sha256(result.stdout).hexdigest()


def keyframe_interval(ffprobe: str, path: Path) -> float | None:
    payload = run_json(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_frames",
            "-show_entries",
            "frame=key_frame,best_effort_timestamp_time",
            "-of",
            "json",
            str(path),
        ]
    )
    stamps = [
        float(frame["best_effort_timestamp_time"])
        for frame in payload.get("frames", [])
        if frame.get("key_frame") == 1 and frame.get("best_effort_timestamp_time") is not None
    ]
    if len(stamps) < 2:
        return None
    return max(b - a for a, b in zip(stamps, stamps[1:]))


def check_motion_windows(
    manifest_path: Path,
    rendered: Path,
    ffmpeg: str,
    ffprobe: str,
    errors: list[str],
    checks: dict[str, Any],
) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    windows = manifest.get("motion_windows", [])
    motion_results: list[dict[str, Any]] = []
    for index, window in enumerate(windows, 1):
        start, end = float(window["start"]), float(window["end"])
        if end - start < 0.2:
            errors.append(f"motion window {index} is too short")
            continue
        source = Path(window["source_path"]).expanduser()
        if not source.is_absolute():
            source = (manifest_path.parent / source).resolve()
        if not source.is_file():
            errors.append(f"motion source not found: {source}")
            continue
        sample_a = start + min(0.25, (end - start) * 0.2)
        sample_b = end - min(0.25, (end - start) * 0.2)
        source_start = float(window.get("source_start", 0.0))
        source_a = source_start + (sample_a - start)
        source_b = source_start + (sample_b - start)
        region = window.get("region")
        source_changed = frame_hash(ffmpeg, source, source_a) != frame_hash(ffmpeg, source, source_b)
        render_changed = frame_hash(ffmpeg, rendered, sample_a, region) != frame_hash(ffmpeg, rendered, sample_b, region)
        interval = keyframe_interval(ffprobe, source)
        if not source_changed:
            errors.append(f"motion window {index} source frames are static")
        if not render_changed:
            errors.append(f"motion window {index} rendered region is static or hidden")
        if interval is not None and interval > 1.2:
            errors.append(f"motion window {index} keyframe interval {interval:.2f}s exceeds 1.2s")
        motion_results.append(
            {
                "index": index,
                "source_changed": source_changed,
                "render_changed": render_changed,
                "max_keyframe_interval": interval,
            }
        )
    checks["motion_windows"] = motion_results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--source-audio", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--fps", type=float, default=30.0)
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []
    checks: dict[str, Any] = {}
    media_summary: dict[str, Any] = {}
    try:
        if not args.video.is_file():
            raise RuntimeError(f"video not found: {args.video}")
        if not args.source_audio.is_file():
            raise RuntimeError(f"source audio not found: {args.source_audio}")
        ffprobe, ffmpeg = find_binary("ffprobe"), find_binary("ffmpeg")
        if not ffprobe:
            raise RuntimeError("ffprobe not found")
        rendered = probe_media(ffprobe, args.video)
        source = probe_media(ffprobe, args.source_audio)
        streams = rendered.get("streams", [])
        video_streams = [stream for stream in streams if stream.get("codec_type") == "video"]
        audio_streams = [stream for stream in streams if stream.get("codec_type") == "audio"]
        subtitle_streams = [stream for stream in streams if stream.get("codec_type") == "subtitle"]
        if not video_streams:
            errors.append("video stream is missing")
        if not audio_streams:
            errors.append("audio stream is missing")
        if subtitle_streams:
            errors.append("subtitle stream is not allowed")
        if video_streams:
            video = video_streams[0]
            width, height = int(video.get("width", 0)), int(video.get("height", 0))
            fps = ratio(video.get("avg_frame_rate") or video.get("r_frame_rate"))
            if (width, height) != (args.width, args.height):
                errors.append(f"resolution {width}x{height} does not match {args.width}x{args.height}")
            if video.get("codec_name") != "h264":
                errors.append(f"video codec {video.get('codec_name')} is not h264")
            if abs(fps - args.fps) > 0.01:
                errors.append(f"frame rate {fps:.3f} does not match {args.fps:.3f}")
            media_summary.update({"width": width, "height": height, "fps": fps, "video_codec": video.get("codec_name")})
        if audio_streams and audio_streams[0].get("codec_name") != "aac":
            errors.append(f"audio codec {audio_streams[0].get('codec_name')} is not aac")
        if audio_streams:
            media_summary.update(
                {
                    "audio_codec": audio_streams[0].get("codec_name"),
                    "audio_sample_rate": int(audio_streams[0]["sample_rate"]) if audio_streams[0].get("sample_rate") else None,
                    "audio_channels": audio_streams[0].get("channels"),
                }
            )
        rendered_duration = float(rendered.get("format", {}).get("duration", 0))
        source_duration = float(source.get("format", {}).get("duration", 0))
        tolerance = max(2 / args.fps + 0.05, 0.12)
        difference = abs(rendered_duration - source_duration)
        if difference > tolerance:
            errors.append(f"duration difference {difference:.3f}s exceeds tolerance {tolerance:.3f}s")
        checks["duration"] = {
            "rendered_seconds": rendered_duration,
            "source_seconds": source_duration,
            "difference_seconds": difference,
            "tolerance_seconds": tolerance,
        }
        media_summary["duration_seconds"] = rendered_duration
        if args.manifest:
            if not args.manifest.is_file():
                errors.append(f"manifest not found: {args.manifest}")
            elif not ffmpeg:
                errors.append("ffmpeg not found; motion verification cannot run")
            else:
                check_motion_windows(args.manifest, args.video, ffmpeg, ffprobe, errors, checks)
        warnings.extend(
            [
                "Manual check required: no burned captions are visible.",
                "Manual check required: bottom subtitle-safe area remains unobstructed.",
                "Manual check required: background text does not interfere with foreground copy.",
                "Manual check required: scene midpoints and transition boundaries were visually reviewed.",
            ]
        )
    except (RuntimeError, OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(str(exc))

    report = {"passed": not errors, "media": media_summary, "checks": checks, "warnings": warnings, "errors": errors}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"PASS: verified {args.video}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
