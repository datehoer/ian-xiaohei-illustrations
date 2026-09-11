import base64
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import wave

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from mimo_tts import TtsError, api_request, make_payload, synthesize
from narrated_video import timestamp, validate


class PipelineTests(unittest.TestCase):
    def test_tts_text_is_assistant_and_style_is_user(self):
        payload = make_payload("洗衣店的年账", style="自然讲解")
        self.assertEqual(payload["messages"], [
            {"role": "user", "content": "自然讲解"},
            {"role": "assistant", "content": "洗衣店的年账"}])
        self.assertEqual(payload["audio"]["format"], "wav")

    def test_credentials_are_not_sent_over_http(self):
        with self.assertRaises(TtsError):
            api_request("http://example.test/v1", "test", "/models")

    def test_invalid_audio_does_not_replace_existing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "speech.wav"
            output.write_bytes(b"existing")
            response = {"choices": [{"message": {"audio": {"data": base64.b64encode(b"not a wav").decode()}}}]}
            with patch("mimo_tts.api_request", return_value=response), self.assertRaises(TtsError):
                synthesize("正文", output, "test")
            self.assertEqual(output.read_bytes(), b"existing")
            self.assertFalse(output.with_suffix(".partial.wav").exists())

    def test_wav_duration_comes_from_samples(self):
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav:
            wav.setparams((1, 2, 24000, 0, "NONE", "not compressed"))
            wav.writeframes(b"\0" * 24000)
        response = {"choices": [{"message": {"audio": {"data": base64.b64encode(buffer.getvalue()).decode()}}}]}
        with tempfile.TemporaryDirectory() as directory, patch("mimo_tts.api_request", return_value=response):
            duration = synthesize("正文", Path(directory) / "speech.wav", "test")
            self.assertEqual(duration, 0.5)

    def test_srt_rounding_carries_to_next_minute(self):
        self.assertEqual(timestamp(59.9996), "00:01:00,000")

    def test_missing_image_fails_before_tts(self):
        with self.assertRaises(ValueError):
            validate({"segments": [{"text": "正文", "image": "missing.png"}]}, Path("/missing"))

    def test_pilot_ledger_and_order_sensitivity(self):
        from fractions import Fraction
        revenue = 20 * 50 * 360
        fixed_costs = 72000 + 96000 + 18000 + 12000
        self.assertEqual(revenue - 120000 - fixed_costs, 42000)
        unit_variable = Fraction(120000, 50 * 360)
        downside = (20 - unit_variable) * 40 * 360 - fixed_costs
        self.assertEqual(downside, -6000)
        path = Path(__file__).resolve().parents[1] / "examples/video/laundromat/manifest.json"
        manifest = json.loads(path.read_text())
        self.assertEqual(manifest["segments"][7]["rows"][-1]["value"], "42,000")
        self.assertEqual(manifest["segments"][8]["rows"][-1]["value"], "−6,000")


if __name__ == "__main__":
    unittest.main()
