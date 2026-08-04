import json
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "analyze_inputs.py"


def write_wav(path: Path, duration: float = 2.0) -> None:
    frames = int(16000 * duration)
    with wave.open(str(path), "wb") as target:
        target.setnchannels(1)
        target.setsampwidth(2)
        target.setframerate(16000)
        target.writeframes(b"\0\0" * frames)


def run_cli(audio: Path, srt: Path, output_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--audio", str(audio), "--srt", str(srt), "--output-dir", str(output_dir)],
        text=True,
        capture_output=True,
        check=False,
    )


class AnalyzeInputsTests(unittest.TestCase):
    def test_valid_chinese_paths_create_report_and_storyboard(self) -> None:
        with tempfile.TemporaryDirectory(prefix="语音 视频 ") as tmp:
            root = Path(tmp)
            audio = root / "双人 对话.wav"
            srt = root / "内容 时间轴.srt"
            output = root / "分析 输出"
            write_wav(audio)
            srt.write_text(
                "1\n00:00:00,000 --> 00:00:00,800\n景辉：先看用户的总时间。\n\n"
                "2\n00:00:00,900 --> 00:00:01,700\n晓曼：但速度也很重要。\n",
                encoding="utf-8",
            )

            result = run_cli(audio, srt, output)

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((output / "input-report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["segment_count"], 2)
            self.assertAlmostEqual(report["audio"]["duration_seconds"], 2.0, places=2)
            self.assertEqual(report["segments"][0]["speaker"], "景辉")
            self.assertTrue((output / "storyboard-beats.md").exists())

    def test_overlap_returns_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio, srt = root / "a.wav", root / "a.srt"
            write_wav(audio)
            srt.write_text(
                "1\n00:00:00,000 --> 00:00:01,200\n第一句\n\n"
                "2\n00:00:01,000 --> 00:00:01,500\n第二句\n",
                encoding="utf-8",
            )
            result = run_cli(audio, srt, root / "out")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("overlap", result.stderr.lower())

    def test_reversed_timestamp_returns_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio, srt = root / "a.wav", root / "a.srt"
            write_wav(audio)
            srt.write_text("1\n00:00:01,000 --> 00:00:00,500\n错误时间\n", encoding="utf-8")
            result = run_cli(audio, srt, root / "out")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("end", result.stderr.lower())

    def test_srt_beyond_audio_returns_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio, srt = root / "a.wav", root / "a.srt"
            write_wav(audio, 1.0)
            srt.write_text("1\n00:00:00,000 --> 00:00:02,000\n太长\n", encoding="utf-8")
            result = run_cli(audio, srt, root / "out")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("exceeds audio", result.stderr.lower())

    def test_empty_srt_returns_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio, srt = root / "a.wav", root / "a.srt"
            write_wav(audio)
            srt.write_text("", encoding="utf-8")
            result = run_cli(audio, srt, root / "out")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("segment", result.stderr.lower())


if __name__ == "__main__":
    unittest.main()
