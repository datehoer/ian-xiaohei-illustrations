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
from mimo_tts import read_key, tts_config
from episode_video import fingerprint
from grok_research import research_payload, research_result
from narrated_video import timestamp, validate


class PipelineTests(unittest.TestCase):
    def test_tts_environment_and_manifest_precedence_change_cache_identity(self):
        block = {"text": "口播正文"}
        with patch.dict("os.environ", {"MIMO_BASE_URL": "https://first.example/v1", "MIMO_MODEL": "first-model"}):
            first = fingerprint({}, block)
            self.assertEqual(tts_config()["model"], "first-model")
            fixed = {"tts": {"base_url": "https://fixed.example/v1", "model": "fixed-model"}}
            fixed_hash = fingerprint(fixed, block)
        with patch.dict("os.environ", {"MIMO_BASE_URL": "https://second.example/v1", "MIMO_MODEL": "second-model"}):
            self.assertNotEqual(fingerprint({}, block), first)
            self.assertEqual(fingerprint(fixed, block), fixed_hash)
            self.assertEqual(tts_config(fixed["tts"])["model"], "fixed-model")

    def test_missing_key_fails_without_prompt_in_noninteractive_execution(self):
        with patch.dict("os.environ", {"MIMO_API_KEY": ""}), patch("sys.stdin.isatty", return_value=False), patch("getpass.getpass") as prompt:
            with self.assertRaises(TtsError):
                read_key()
            prompt.assert_not_called()

    def test_research_requires_completed_search_and_preserves_citations(self):
        payload = research_payload("原始来源", "grok-chat-fast")
        self.assertEqual(payload["model"], "grok-chat-fast")
        self.assertEqual(payload["tools"], [{"type": "web_search"}])
        response = {"status": "completed", "model": "grok-chat-fast", "output": [
            {"type": "message", "content": [{"type": "output_text", "text": "资料", "annotations": [
                {"type": "url_citation", "url": "https://source.example/report", "title": "原始报告"}]}]},
        ]}
        with self.assertRaises(TtsError):
            research_result(response, "原始来源")
        response["output"].insert(0, {"type": "web_search_call", "status": "completed", "action": {"sources": [
            {"url": "https://source.example/report", "title": "原始报告"}]}})
        result = research_result(response, "原始来源")
        self.assertEqual(len(result["sources"]), 1)
        self.assertEqual(result["answer"], "资料")
        self.assertTrue(result["sources_require_verification"])
        response["status"] = "incomplete"
        with self.assertRaises(TtsError):
            research_result(response, "原始来源")

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
        path = Path(__file__).resolve().parents[1] / "examples/minimal-video/manifest.json"
        manifest = json.loads(path.read_text())
        self.assertEqual(manifest["segments"][7]["rows"][-1]["value"], "42,000")
        self.assertEqual(manifest["segments"][8]["rows"][-1]["value"], "−6,000")


if __name__ == "__main__":
    unittest.main()
