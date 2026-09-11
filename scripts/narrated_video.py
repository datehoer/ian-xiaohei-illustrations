#!/usr/bin/env python3
"""Build a narrated MP4, SRT and measured timeline from an explicit shot manifest."""

from __future__ import annotations

import argparse
from functools import lru_cache
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import wave

from mimo_tts import DEFAULT_BASE_URL, DEFAULT_MODEL, DEFAULT_STYLE, TtsError, make_payload, read_key, synthesize


def run(command, cwd=None):
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr[-2500:])
    return result.stdout


def timestamp(seconds):
    ms = round(seconds * 1000)
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def validate(manifest, root):
    if not isinstance(manifest.get("segments"), list) or not manifest["segments"]:
        raise ValueError("manifest 需要非空 segments。")
    for i, segment in enumerate(manifest["segments"], 1):
        if not isinstance(segment.get("text"), str) or not segment["text"].strip():
            raise ValueError(f"第 {i} 段缺少纯口播 text。")
        if "[画面" in segment["text"] or "[停]" in segment["text"]:
            raise ValueError(f"第 {i} 段仍含分镜标签；请先拆出纯口播。")
        if len(segment.get("subtitle", segment["text"])) > 54:
            raise ValueError(f"第 {i} 段字幕过长；请将口播拆成更短的段落。")
        if not isinstance(segment.get("image"), str) or not (root / segment["image"]).is_file():
            raise ValueError(f"第 {i} 段没有可用配图，不能生成悬空镜头。")
        if len(segment.get("rows", [])) > 7:
            raise ValueError(f"第 {i} 段数据表最多 7 行。")
    return manifest


def font_path(manifest):
    candidates = [manifest.get("font"), os.environ.get("VIDEO_FONT"),
                  "/System/Library/Fonts/STHeiti Medium.ttc",
                  "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return candidate
    raise ValueError("找不到中文字体，请设置 VIDEO_FONT 或 manifest.font。")


@lru_cache(maxsize=16)
def simplified_font_index(path):
    """Select the Simplified Chinese face inside a font collection, not face zero.

    macOS Heiti starts with TC; PingFang starts with HK; Noto CJK starts with JP.
    The Unicode text alone does not select the mainland Chinese glyph variants.
    """
    from PIL import ImageFont
    if Path(path).suffix.lower() not in ('.ttc', '.otc'):
        return 0
    for index in range(64):
        try:
            family, _ = ImageFont.truetype(path, 20, index=index).getname()
        except OSError:
            break
        if re.search(r'(^|[\s-])(SC|CN)(\s|$)', family, re.IGNORECASE):
            return index
    raise ValueError("字体集合中没有识别到简体中文字体；请指定 manifest.font_index。")


def font_index(manifest):
    if 'font_index' in manifest:
        index = manifest['font_index']
        if not isinstance(index, int) or isinstance(index, bool) or index < 0:
            raise ValueError('font_index 必须是非负整数')
        return index
    return simplified_font_index(font_path(manifest))


def overlay(segment, manifest, output, index, count, font):
    # This is a transparent typography layer for video compositing, not an image edit.
    from PIL import Image, ImageDraw, ImageFont
    face = font_index(manifest)
    image = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    black, muted, orange, red = "#202422", "#737A76", "#C76C28", "#BA473C"

    def text(x, y, content, size, color=black, anchor=None):
        draw.text((x, y), str(content), font=ImageFont.truetype(font, size, index=face), fill=color, anchor=anchor)

    text(86, 38, "拥有一门生意 · 账本试算", 23, muted)
    text(84, 88, segment.get("heading", manifest["title"]), 56)
    text(1832, 54, manifest.get("disclosure", "演示假设 · 非行业均值"), 24, muted, "ra")
    draw.line((86, 180, 1834, 180), fill="#DDE0DC", width=2)
    x = 1090
    text(x, 253, segment.get("eyebrow", ""), 25, muted)
    rows = segment.get("rows", [])
    if rows:
        for row_index, row in enumerate(rows):
            y = 326 + row_index * 66
            color = red if row.get("accent") else black
            text(x, y, row["label"], 30, color)
            text(1816, y, row["value"], 33, color, "ra")
            if row_index < len(rows) - 1:
                draw.line((x, y + 47, 1816, y + 47), fill="#E8EAE6", width=1)
    else:
        text(x, 348, segment.get("metric", ""), 91, orange)
        text(x, 470, segment.get("detail", ""), 33)
    for line_index, line in enumerate(segment.get("note", "").split("\n")):
        text(x, 808 + line_index * 34, line, 24, muted)
    subtitle = segment.get("subtitle", segment["text"])
    subtitle_font = ImageFont.truetype(font, 43, index=face)
    lines, line = [], ""
    for character in subtitle:
        if draw.textlength(line + character, font=subtitle_font) > 1680:
            lines.append(line)
            line = ""
        line += character
    if line:
        lines.append(line)
    draw.rectangle((0, 912, 1920, 1080), fill="#FFFFFF")
    for line_index, line in enumerate(lines):
        text(960, 934 + line_index * 57, line, 43, anchor="ma")
    draw.rectangle((86, 1055, 1834, 1059), fill="#EBEDE9")
    draw.rectangle((86, 1055, 86 + round(1748 * (index + 1) / count), 1059), fill=orange)
    image.save(output)


def read_audio(path):
    with wave.open(str(path), "rb") as wav:
        if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate()) != (1, 2, 48000):
            raise ValueError("内部音频必须是 48kHz mono PCM16。")
        return wav.readframes(wav.getnframes())


def build(manifest_path, output, offline=False):
    manifest_path = manifest_path.resolve()
    root = manifest_path.parent
    manifest = validate(json.loads(manifest_path.read_text(encoding="utf-8")), root)
    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            raise ValueError(f"需要安装 {tool}。")
    font = font_path(manifest)
    # Validate rendering dependency before any paid API calls.
    from PIL import ImageFont
    ImageFont.truetype(font, 43, index=font_index(manifest))
    output.mkdir(parents=True, exist_ok=True)
    cache = output / "audio-cache"
    cache.mkdir(exist_ok=True)
    render = output / "render"
    render.mkdir(exist_ok=True)
    tts = manifest.get("tts", {})
    base_url = tts.get("base_url", os.environ.get("MIMO_BASE_URL", DEFAULT_BASE_URL))
    model, voice = tts.get("model", DEFAULT_MODEL), tts.get("voice", "白桦")
    style = tts.get("style", DEFAULT_STYLE)
    key = None
    timeline, pcm_chunks, srt, clips = [], [], [], []
    total_frames = 0
    count = len(manifest["segments"])
    for index, segment in enumerate(manifest["segments"]):
        signature = json.dumps({"endpoint": base_url, "payload": make_payload(segment["text"], model, voice, style)},
                               ensure_ascii=False, sort_keys=True)
        digest = hashlib.sha256(signature.encode()).hexdigest()[:24]
        audio = cache / f"{digest}.wav"
        if not audio.exists():
            if offline:
                raise ValueError(f"第 {index + 1} 段没有匹配的缓存音频。")
            if key is None:
                key = read_key()
            print(f"配音 {index + 1}/{count}", flush=True)
            synthesize(segment["text"], audio, key, base_url, model, voice, style)
        normalized = render / f"{index:03}.wav"
        run(["ffmpeg", "-y", "-v", "error", "-i", str(audio), "-ar", "48000", "-ac", "1",
             "-c:a", "pcm_s16le", str(normalized)])
        pcm = read_audio(normalized)
        speech_seconds = len(pcm) / 96000
        frames = math.ceil(speech_seconds * 30)
        duration = frames / 30
        pcm_chunks.append(pcm + b"\0" * (frames * 1600 * 2 - len(pcm)))
        start, end = total_frames / 30, (total_frames + frames) / 30
        timeline.append({"segment": index + 1, "image": segment["image"], "text": segment["text"],
                         "start": start, "end": end, "speech_seconds": speech_seconds,
                         "audio": str(audio.relative_to(output))})
        srt.append(f"{index + 1}\n{timestamp(start)} --> {timestamp(start + speech_seconds)}\n"
                   f"{segment.get('subtitle', segment['text'])}\n")
        layer = render / f"{index:03}.png"
        overlay(segment, manifest, layer, index, count, font)
        clip = render / f"{index:03}.mp4"
        # Contain the original artwork; preserve its entire composition and safe areas.
        run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", "30", "-i", str((root / segment["image"]).resolve()),
             "-loop", "1", "-framerate", "30", "-i", str(layer), "-filter_complex",
             "[0:v]scale=1536:864:force_original_aspect_ratio=decrease,pad=1920:1080:70:140:color=white,setsar=1[bg];[bg][1:v]overlay=0:0,format=yuv420p[v]",
             "-map", "[v]", "-frames:v", str(frames), "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "19",
             "-threads", "4", str(clip)])
        clips.append(f"file '{clip.name}'")
        total_frames += frames
        print(f"镜头 {index + 1}/{count} · {duration:.2f} 秒", flush=True)
    narration = output / "narration.wav"
    with wave.open(str(narration), "wb") as wav:
        wav.setparams((1, 2, 48000, 0, "NONE", "not compressed"))
        for pcm in pcm_chunks:
            wav.writeframes(pcm)
    (output / "subtitles.srt").write_text("\n".join(srt), encoding="utf-8")
    (output / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8")
    (render / "concat.txt").write_text("\n".join(clips) + "\n", encoding="utf-8")
    raw = output / "picture.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "1", "-i", "concat.txt", "-c", "copy", str(raw.resolve())], cwd=render)
    final = output / "video.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-i", str(narration), "-map", "0:v:0", "-map", "1:a:0",
         "-c:v", "copy", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "48000", "-c:a", "aac", "-b:a", "192k",
         "-t", str(total_frames / 30), "-movflags", "+faststart", str(final)])
    metadata = json.loads(run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(final)]))
    (output / "media-info.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"完成：{final.resolve()}（{total_frames / 30:.2f} 秒）")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, default=Path("outputs/video"))
    parser.add_argument("--offline", action="store_true", help="只用匹配的本地语音缓存，禁止调用 API")
    args = parser.parse_args()
    try:
        build(args.manifest, args.output.resolve(), args.offline)
    except (ValueError, OSError, RuntimeError, TtsError) as exc:
        print(str(exc))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
