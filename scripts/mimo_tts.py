#!/usr/bin/env python3
"""MiMo chat-completions TTS. Secrets come from the environment or hidden input."""

from __future__ import annotations

import argparse
import base64
import binascii
import getpass
import json
import os
import sys
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request
import wave


DEFAULT_BASE_URL = "https://api.hotday.uk/v1"
DEFAULT_MODEL = "mimo-v2.5-tts"
DEFAULT_STYLE = "用自然、清晰的中文讲解，像在和朋友算一笔账。语速适中，句尾干净，不要播音腔。"


class TtsError(RuntimeError):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise TtsError("API 返回重定向；为避免向其他地址转发密钥，已停止。")


def tts_config(config=None):
    config = config or {}
    return {
        "base_url": config.get("base_url") or os.environ.get("MIMO_BASE_URL") or DEFAULT_BASE_URL,
        "model": config.get("model") or os.environ.get("MIMO_MODEL") or DEFAULT_MODEL,
        "voice": config.get("voice", "白桦"),
        "style": config.get("style", DEFAULT_STYLE),
    }


def api_request(base_url, key, route, payload=None):
    parsed = urllib.parse.urlsplit(base_url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.query or parsed.fragment:
        raise TtsError("base-url 必须是无账号、查询参数或片段的 HTTPS 地址。")
    data = json.dumps(payload, ensure_ascii=False).encode() if payload is not None else None
    request = urllib.request.Request(
        base_url.rstrip("/") + route, data=data,
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=120) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        # Do not print the response: gateways can echo credentials or request contents.
        raise TtsError(f"API HTTP {exc.code}；请检查模型授权、余额及接口地址。") from None
    except urllib.error.URLError:
        raise TtsError("连接 API 失败；请检查网络及接口地址。") from None
    except (ValueError, TimeoutError):
        raise TtsError("API 超时或返回了无效 JSON。") from None


def make_payload(text, model=DEFAULT_MODEL, voice="白桦", style=DEFAULT_STYLE):
    if not text.strip():
        raise TtsError("朗读正文不能为空。")
    return {
        "model": model,
        "messages": [{"role": "user", "content": style}, {"role": "assistant", "content": text}],
        "audio": {"format": "wav", "voice": voice},
        "stream": False,
    }


def synthesize(text, output, key, base_url=DEFAULT_BASE_URL, model=DEFAULT_MODEL,
               voice="白桦", style=DEFAULT_STYLE):
    response = api_request(base_url, key, "/chat/completions", make_payload(text, model, voice, style))
    try:
        data = base64.b64decode(response["choices"][0]["message"]["audio"]["data"], validate=True)
    except (KeyError, IndexError, TypeError, ValueError, binascii.Error):
        raise TtsError("API 未返回有效的 message.audio.data；中转站可能不兼容 MiMo TTS。") from None
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".partial.wav")
    try:
        temporary.write_bytes(data)
        with wave.open(str(temporary), "rb") as wav:
            if wav.getnframes() == 0:
                raise TtsError("API 返回空音频。")
            duration = wav.getnframes() / wav.getframerate()
        temporary.replace(output)
    except (wave.Error, EOFError):
        raise TtsError("API 返回的音频不是有效的 PCM WAV。") from None
    finally:
        temporary.unlink(missing_ok=True)
    return duration


def read_key():
    key = os.environ.get("MIMO_API_KEY", "").strip()
    if not key and not sys.stdin.isatty():
        raise TtsError("缺少 MIMO_API_KEY；请使用 uv run --env-file .env 加载本地配置。")
    if not key:
        key = getpass.getpass("MiMo API key（隐藏输入）: ")
    if not key.strip():
        raise TtsError("缺少 MIMO_API_KEY。")
    return key.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.environ.get("MIMO_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--model", default=os.environ.get("MIMO_MODEL", DEFAULT_MODEL))
    parser.add_argument("--voice", default="白桦")
    parser.add_argument("--style", default=DEFAULT_STYLE)
    parser.add_argument("--list-models", action="store_true")
    parser.add_argument("--text", help="UTF-8 纯口播文件")
    parser.add_argument("--output", default="outputs/tts-probe.wav")
    args = parser.parse_args()
    try:
        key = read_key()
        if args.list_models:
            response = api_request(args.base_url, key, "/models")
            models = [item["id"] for item in response.get("data", []) if "mimo" in item.get("id", "").lower()]
            print(json.dumps({"mimo_models": models}, ensure_ascii=False))
        if args.text:
            duration = synthesize(Path(args.text).read_text(encoding="utf-8"), args.output, key,
                                  args.base_url, args.model, args.voice, args.style)
            print(json.dumps({"output": str(Path(args.output).resolve()), "seconds": round(duration, 3)}, ensure_ascii=False))
        if not args.list_models and not args.text:
            parser.error("需要 --list-models 或 --text")
    except (TtsError, OSError) as exc:
        print(str(exc))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
