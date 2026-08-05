from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "verify_delivery.py"


def find_ffmpeg() -> str | None:
    candidates = [
        os.environ.get("AUDIO_VIDEO_FFMPEG"),
        shutil.which("ffmpeg"),
        "/Users/anlinliu/Documents/短视频制作/英国钢厂风险短片/tools/ffmpeg/ffmpeg",
        "/Users/anlinliu/Developer/video-use/.venv/lib/python3.12/site-packages/static_ffmpeg/bin/darwin_arm64/ffmpeg",
    ]
    return next((item for item in candidates if item and Path(item).is_file()), None)


def write_wav(path: Path, duration: float) -> None:
    with wave.open(str(path), "wb") as target:
        target.setnchannels(1)
        target.setsampwidth(2)
        target.setframerate(16000)
        target.writeframes(b"\0\0" * int(16000 * duration))


def make_video(ffmpeg: str, path: Path, audio: Path | None, size: str = "1280x720", duration: float = 1.0) -> None:
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c=0x17342d:s={size}:r=30:d={duration}",
    ]
    if audio:
        command += ["-i", str(audio), "-shortest"]
    command += ["-c:v", "libx264", "-pix_fmt", "yuv420p"]
    if audio:
        command += ["-c:a", "aac"]
    command += [str(path)]
    subprocess.run(command, check=True)


def run_cli(video: Path, audio: Path, report: Path, review: Path | None = None) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(SCRIPT), "--video", str(video), "--source-audio", str(audio), "--report", str(report)]
    if review:
        command += ["--review", str(review)]
    return subprocess.run(
        command,
        text=True,
        capture_output=True,
        check=False,
    )


@unittest.skipUnless(find_ffmpeg(), "ffmpeg fixture generator is unavailable")
class VerifyDeliveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ffmpeg = find_ffmpeg()

    def test_valid_delivery_passes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="成片 验收 ") as tmp:
            root = Path(tmp)
            audio, video, report = root / "源 音频.wav", root / "成片 视频.mp4", root / "报告.json"
            write_wav(audio, 1.0)
            make_video(self.ffmpeg, video, audio)
            result = run_cli(video, audio, report)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(report.read_text(encoding="utf-8"))
            self.assertTrue(payload["passed"])
            self.assertEqual(payload["media"]["width"], 1280)
            self.assertEqual(payload["media"]["height"], 720)

    def test_wrong_resolution_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio, video, report = root / "a.wav", root / "v.mp4", root / "r.json"
            write_wav(audio, 1.0)
            make_video(self.ffmpeg, video, audio, size="640x360")
            result = run_cli(video, audio, report)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("resolution", result.stderr.lower())

    def test_missing_audio_stream_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio, video, report = root / "a.wav", root / "v.mp4", root / "r.json"
            write_wav(audio, 1.0)
            make_video(self.ffmpeg, video, None)
            result = run_cli(video, audio, report)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("audio stream", result.stderr.lower())

    def test_duration_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio, video, report = root / "a.wav", root / "v.mp4", root / "r.json"
            short_audio = root / "short.wav"
            write_wav(audio, 2.0)
            write_wav(short_audio, 1.0)
            make_video(self.ffmpeg, video, short_audio)
            result = run_cli(video, audio, report)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("duration", result.stderr.lower())

    def test_missing_video_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio, report = root / "a.wav", root / "r.json"
            write_wav(audio, 1.0)
            result = run_cli(root / "missing.mp4", audio, report)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not found", result.stderr.lower())

    def test_subtitle_track_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio, base, video, report = root / "a.wav", root / "base.mp4", root / "subbed.mp4", root / "r.json"
            subtitle = root / "caption.srt"
            write_wav(audio, 1.0)
            make_video(self.ffmpeg, base, audio)
            subtitle.write_text("1\n00:00:00,000 --> 00:00:00,500\n字幕\n", encoding="utf-8")
            subprocess.run(
                [self.ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(base), "-i", str(subtitle), "-c", "copy", "-c:s", "mov_text", str(video)],
                check=True,
            )
            result = run_cli(video, audio, report)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("subtitle", result.stderr.lower())

    def test_incomplete_manual_review_fails_when_review_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio, video, report, review = root / "a.wav", root / "v.mp4", root / "r.json", root / "review.json"
            write_wav(audio, 1.0)
            make_video(self.ffmpeg, video, audio)
            review.write_text(json.dumps({"approved": True, "checks": {"captions": True}}), encoding="utf-8")
            result = run_cli(video, audio, report, review)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("review missing checks", result.stderr.lower())

    def test_complete_manual_review_allows_delivery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio, video, report, review = root / "a.wav", root / "v.mp4", root / "r.json", root / "review.json"
            write_wav(audio, 1.0)
            make_video(self.ffmpeg, video, audio)
            review.write_text(
                json.dumps(
                    {
                        "approved": True,
                        "checks": {
                            "no_burned_captions": True,
                            "subtitle_safe_area": True,
                            "background_text": True,
                            "scene_midpoints": True,
                            "transition_boundaries": True,
                            "opening_and_ending": True,
                            "video_motion": True,
                        },
                    }
                ),
                encoding="utf-8",
            )
            result = run_cli(video, audio, report, review)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
