#!/usr/bin/env python3
"""Search with the configured Grok model and preserve source evidence for verification."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile

from mimo_tts import TtsError, api_request


def research_payload(query, model, max_output_tokens=2048):
    if not query.strip():
        raise ValueError("检索问题不能为空。")
    if not 256 <= max_output_tokens <= 8192:
        raise ValueError("max-output-tokens 必须在 256–8192 之间。")
    return {
        "model": model,
        "input": [
            {"role": "system", "content": "为中文科普和经营经济学口播查找资料。必须联网检索，优先原始发布方；给出直接来源链接、发布日期、适用地区和数据口径。区分事实、假设和推算。不把搜索摘要或模型记忆当作已核验事实，找不到时明确说明。"},
            {"role": "user", "content": query},
        ],
        "tools": [{"type": "web_search"}],
        "tool_choice": "required",
        "include": ["web_search_call.action.sources"],
        "max_output_tokens": max_output_tokens,
        "stream": False,
        "store": False,
    }


def research_result(response, query):
    if response.get("status") != "completed":
        raise TtsError("检索响应未完成；停止并检查本次记录，不自动重试。")
    paragraphs, sources, searches = [], {}, []
    for item in response.get("output", []):
        if item.get("type") == "web_search_call":
            searches.append({k: item[k] for k in ("id", "status", "action") if k in item})
            for source in item.get("action", {}).get("sources", []):
                if source.get("url"):
                    sources[source["url"]] = {k: source[k] for k in ("url", "title") if k in source}
        if item.get("type") == "message":
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    paragraphs.append(content.get("text", ""))
                    for annotation in content.get("annotations", []):
                        if annotation.get("type") == "url_citation" and annotation.get("url"):
                            sources[annotation["url"]] = {k: annotation[k] for k in ("url", "title") if k in annotation}
    if not paragraphs:
        raise TtsError("检索响应没有正文；不自动重试。")
    if not any(item.get("status") == "completed" for item in searches):
        raise TtsError("响应缺少已完成的联网搜索记录，不能作为联网检索成功；不自动重试。")
    return {
        "queried_at": datetime.now(timezone.utc).isoformat(),
        "query": query,
        "model": response.get("model"),
        "response_id": response.get("id"),
        "answer": "\n\n".join(paragraphs),
        "sources": list(sources.values()),
        "search_calls": searches,
        "usage": response.get("usage"),
        "sources_require_verification": True,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="检索问题；请写明地区、时期和对象")
    parser.add_argument("--output", type=Path, required=True, help="本期来源线索 JSON，使用新文件名")
    parser.add_argument("--base-url", default=os.environ.get("XAI_BASE_URL", "https://api.hotday.uk/v1"))
    parser.add_argument("--model", default=os.environ.get("XAI_MODEL", "grok-chat-fast"))
    parser.add_argument("--max-output-tokens", type=int, default=2048)
    args = parser.parse_args()
    try:
        if args.output.exists():
            raise ValueError("输出文件已存在，请选择新文件名。")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        # Verify local storage before a potentially billable request.
        with tempfile.TemporaryFile(dir=args.output.parent) as probe:
            probe.write(b"write-check")
            probe.flush()
        key = os.environ.get("XAI_API_KEY", "").strip()
        if not key:
            raise ValueError("缺少 XAI_API_KEY；请使用 uv run --env-file .env 加载配置。")
        payload = research_payload(args.query, args.model, args.max_output_tokens)
        response = api_request(args.base_url, key, "/responses", payload)
        result = research_result(response, args.query)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        print(json.dumps({"output": str(args.output.resolve()), "model": result["model"],
                          "sources": len(result["sources"]), "search_calls": len(result["search_calls"])}, ensure_ascii=False))
    except (TtsError, ValueError, OSError) as exc:
        print(str(exc))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
