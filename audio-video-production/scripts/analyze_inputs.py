#!/usr/bin/env python3
"""Validate audio/SRT inputs and create a semantic storyboard skeleton."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import wave
from pathlib import Path
from typing import Any


TIMECODE = re.compile(r"^(\d{2}):(\d{2}):(\d{2})[,.](\d{3})$")
SPEAKER = re.compile(r"^([^：:\n]{1,12})[：:]\s*(.*)$", re.DOTALL)
TRANSITIONS = ("但是", "不过", "所以", "关键", "问题", "换句话说", "更重要", "同时", "最后", "那么")


class InputError(ValueError):
    pass


def parse_timestamp(value: str) -> float:
    match = TIMECODE.match(value.strip())
    if not match:
        raise InputError(f"invalid timestamp: {value}")
    hours, minutes, seconds, millis = (int(part) for part in match.groups())
    if minutes >= 60 or seconds >= 60:
        raise InputError(f"invalid timestamp: {value}")
    return hours * 3600 + minutes * 60 + seconds + millis / 1000


def parse_srt(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").strip()
    if not text:
        raise InputError("SRT contains no segment")
    segments: list[dict[str, Any]] = []
    for block in re.split(r"\n\s*\n", text):
        lines = [line.rstrip() for line in block.splitlines()]
        if len(lines) < 2:
            raise InputError(f"invalid SRT segment: {block!r}")
        if "-->" in lines[0]:
            index = len(segments) + 1
            timing, body = lines[0], lines[1:]
        else:
            try:
                index = int(lines[0].strip())
            except ValueError as exc:
                raise InputError(f"invalid segment index: {lines[0]}") from exc
            timing, body = lines[1], lines[2:]
        if "-->" not in timing or not body:
            raise InputError(f"invalid SRT segment {index}")
        start_raw, end_raw = (part.strip().split()[0] for part in timing.split("-->", 1))
        start, end = parse_timestamp(start_raw), parse_timestamp(end_raw)
        if end <= start:
            raise InputError(f"segment {index} end must be after start")
        content = " ".join(part.strip() for part in body if part.strip())
        if not content:
            raise InputError(f"segment {index} has empty text")
        speaker_match = SPEAKER.match(content)
        speaker = speaker_match.group(1).strip() if speaker_match else None
        spoken_text = speaker_match.group(2).strip() if speaker_match else content
        segments.append(
            {
                "index": index,
                "start": round(start, 3),
                "end": round(end, 3),
                "duration": round(end - start, 3),
                "speaker": speaker,
                "text": content,
                "spoken_text": spoken_text,
            }
        )
    if not segments:
        raise InputError("SRT contains no segment")
    previous_end = -1.0
    for segment in segments:
        if segment["start"] < previous_end - 0.001:
            raise InputError(f"segment {segment['index']} overlap detected")
        previous_end = segment["end"]
    return segments


def find_binary(name: str) -> str | None:
    env_name = f"AUDIO_VIDEO_{name.upper()}"
    candidates = [
        os.environ.get(env_name),
        shutil.which(name),
        f"/Users/anlinliu/Documents/短视频制作/英国钢厂风险短片/tools/ffmpeg/{name}",
        f"/Users/anlinliu/Developer/video-use/.venv/lib/python3.12/site-packages/static_ffmpeg/bin/darwin_arm64/{name}",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return candidate
    return None


def probe_audio(path: Path) -> dict[str, Any]:
    ffprobe = find_binary("ffprobe")
    if ffprobe:
        result = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-select_streams",
                "a:0",
                "-show_entries",
                "stream=codec_name,sample_rate,channels:format=duration",
                "-of",
                "json",
                str(path),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode == 0:
            payload = json.loads(result.stdout)
            streams = payload.get("streams", [])
            if streams and payload.get("format", {}).get("duration"):
                stream = streams[0]
                return {
                    "path": str(path),
                    "duration_seconds": round(float(payload["format"]["duration"]), 6),
                    "codec": stream.get("codec_name"),
                    "sample_rate": int(stream["sample_rate"]) if stream.get("sample_rate") else None,
                    "channels": stream.get("channels"),
                    "probe": "ffprobe",
                }
    if path.suffix.lower() == ".wav":
        with wave.open(str(path), "rb") as source:
            duration = source.getnframes() / source.getframerate()
            return {
                "path": str(path),
                "duration_seconds": round(duration, 6),
                "codec": "pcm",
                "sample_rate": source.getframerate(),
                "channels": source.getnchannels(),
                "probe": "wave",
            }
    raise InputError("ffprobe is required to inspect this audio format")


def group_beats(segments: list[dict[str, Any]], target_seconds: float = 22.0) -> list[dict[str, Any]]:
    beats: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []
    for segment in segments:
        if current:
            elapsed = segment["end"] - current[0]["start"]
            speaker_changed = bool(segment["speaker"] and segment["speaker"] != current[-1]["speaker"])
            semantic_turn = any(segment["spoken_text"].startswith(word) for word in TRANSITIONS)
            long_gap = segment["start"] - current[-1]["end"] >= 1.2
            if elapsed > target_seconds or long_gap or (elapsed >= 8 and (speaker_changed or semantic_turn)):
                beats.append(make_beat(len(beats) + 1, current))
                current = []
        current.append(segment)
    if current:
        beats.append(make_beat(len(beats) + 1, current))
    return beats


def make_beat(number: int, items: list[dict[str, Any]]) -> dict[str, Any]:
    joined = " ".join(item["spoken_text"] for item in items)
    return {
        "beat": number,
        "start": items[0]["start"],
        "end": items[-1]["end"],
        "duration": round(items[-1]["end"] - items[0]["start"], 3),
        "segment_indices": [item["index"] for item in items],
        "summary_seed": joined[:80],
        "visual_purpose": "evidence/context/emotion/contrast/transition/cta",
        "asset_type": "photo/video/data-card",
        "search_terms": "",
    }


def format_time(seconds: float) -> str:
    minutes = int(seconds // 60)
    return f"{minutes:02d}:{seconds - minutes * 60:05.2f}"


def write_outputs(output_dir: Path, audio: dict[str, Any], segments: list[dict[str, Any]], beats: list[dict[str, Any]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "audio": audio,
        "segment_count": len(segments),
        "srt_end_seconds": segments[-1]["end"],
        "tail_difference_seconds": round(audio["duration_seconds"] - segments[-1]["end"], 6),
        "segments": segments,
        "candidate_beats": beats,
    }
    (output_dir / "input-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# 候选语义分镜",
        "",
        "> SRT 仅用于语义与时间对齐；最终画面需结合事实核验和素材质量调整。",
        "",
        "| 段落 | 时间 | 语义种子 | 视觉目的 | 素材类型 | 搜索词 |",
        "|---|---|---|---|---|---|",
    ]
    for beat in beats:
        seed = beat["summary_seed"].replace("|", "｜")
        lines.append(
            f"| {beat['beat']} | {format_time(beat['start'])}–{format_time(beat['end'])} | {seed} | "
            f"{beat['visual_purpose']} | {beat['asset_type']} |  |"
        )
    (output_dir / "storyboard-beats.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audio", type=Path, required=True)
    parser.add_argument("--srt", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        if not args.audio.is_file():
            raise InputError(f"audio file not found: {args.audio}")
        if not args.srt.is_file():
            raise InputError(f"SRT file not found: {args.srt}")
        audio = probe_audio(args.audio)
        segments = parse_srt(args.srt)
        if segments[-1]["end"] > audio["duration_seconds"] + 0.25:
            raise InputError(
                f"SRT end {segments[-1]['end']:.3f}s exceeds audio duration {audio['duration_seconds']:.3f}s"
            )
        beats = group_beats(segments)
        write_outputs(args.output_dir, audio, segments, beats)
    except (InputError, OSError, json.JSONDecodeError, wave.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"PASS: analyzed {len(segments)} SRT segments into {len(beats)} candidate beats")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
