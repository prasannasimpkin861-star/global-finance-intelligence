#!/usr/bin/env python3
"""Collect broad finance-news items through the installed news-aggregator-skill."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

DEFAULT_SOURCES = "wallstreetcn,international"
SOURCE_TIERS = {
    "reuters": 1,
    "reuters (google news fallback)": 2,
    "bbc": 2,
    "bbc world": 2,
    "bbc chinese": 2,
    "the guardian": 2,
    "al jazeera": 2,
    "france 24": 2,
    "wall street cn": 2,
    "华尔街见闻": 2,
    "36kr": 3,
    "36氪": 3,
    "tencent": 3,
    "腾讯新闻": 3,
    "weibo": 4,
    "微博": 4,
}


def locate_fetcher() -> Path:
    roots = []
    if os.environ.get("CODEX_HOME"):
        roots.append(Path(os.environ["CODEX_HOME"]) / "skills")
    roots.extend([Path.home() / ".codex" / "skills", Path.home() / ".agents" / "skills"])
    for root in roots:
        candidate = root / "news-aggregator-skill" / "scripts" / "fetch_news.py"
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("未发现 news-aggregator-skill/scripts/fetch_news.py")


def parse_json_output(text: str) -> list[dict[str, Any]]:
    decoder = json.JSONDecoder()
    for match in re.finditer(r"[\[{]", text):
        try:
            value, _ = decoder.raw_decode(text[match.start():])
        except json.JSONDecodeError:
            continue
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            for key in ("items", "data", "news"):
                if isinstance(value.get(key), list):
                    return [item for item in value[key] if isinstance(item, dict)]
    raise ValueError("采集器没有返回可解析的 JSON 数组")


def iso_time(value: Any, timezone_suffix: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(:\d{2})?", text):
        return text.replace(" ", "T") + timezone_suffix
    if text.endswith("Z") or re.search(r"[+-]\d{2}:?\d{2}$", text):
        return text
    try:
        datetime.fromisoformat(text)
        return text
    except ValueError:
        return text


def infer_category(title: str) -> str:
    text = title.casefold()
    rules = [
        ("central_bank", ("央行", "美联储", "fed", "fomc", "ecb", "降息", "加息", "降准")),
        ("macro_data", ("cpi", "ppi", "gdp", "就业", "非农", "通胀", "pmi")),
        ("regulation", ("监管", "证监会", "处罚", "新规", "关税", "制裁")),
        ("earnings", ("财报", "业绩", "营收", "净利润", "earnings")),
        ("ma_financing", ("并购", "收购", "融资", "增发", "ipo")),
        ("commodities", ("原油", "黄金", "铜", "铝", "煤炭", "opec")),
        ("crypto", ("比特币", "以太坊", "crypto", "bitcoin", "ethereum")),
        ("fx", ("汇率", "美元", "人民币", "日元", "欧元")),
    ]
    for category, terms in rules:
        if any(term in text for term in terms):
            return category
    return "analysis"


def normalize(items: list[dict[str, Any]], timezone_suffix: str) -> list[dict[str, Any]]:
    output = []
    for item in items:
        title = str(item.get("title") or item.get("headline") or "").strip()
        if not title:
            continue
        source = str(item.get("source") or item.get("publisher") or "unknown").strip()
        tier = SOURCE_TIERS.get(source.casefold(), 3)
        output.append({
            "title": title,
            "url": item.get("url") or item.get("link") or "",
            "source": source,
            "source_tier": tier,
            "official": False,
            "published_at": iso_time(item.get("time") or item.get("published_at") or item.get("published"), timezone_suffix),
            "event_time": "",
            "summary": item.get("summary") or item.get("description") or "",
            "category": infer_category(title),
            "region": [],
            "markets": [],
            "assets": [],
            "status": "reported",
            "tags": ["news-aggregator-skill"],
        })
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", default=DEFAULT_SOURCES, help=f"数据源，默认 {DEFAULT_SOURCES}")
    parser.add_argument("--limit", type=int, default=15, help="每个来源最多条数")
    parser.add_argument("--keyword", help="逗号分隔关键词")
    parser.add_argument("--deep", action="store_true", help="让上游尝试抓正文")
    parser.add_argument("--timezone", default="+08:00", help="无时区时间的默认偏移，默认 +08:00")
    parser.add_argument("--output", type=Path, help="输出 JSON 文件；省略时写到标准输出")
    parser.add_argument("--raw-output", type=Path, help="可选：保存上游原始标准输出")
    args = parser.parse_args()

    fetcher = locate_fetcher()
    command = [sys.executable, str(fetcher), "--source", args.sources, "--limit", str(args.limit), "--no-save"]
    if args.keyword:
        command.extend(["--keyword", args.keyword])
    if args.deep:
        command.append("--deep")

    completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if args.raw_output:
        args.raw_output.parent.mkdir(parents=True, exist_ok=True)
        args.raw_output.write_text(completed.stdout + completed.stderr, encoding="utf-8")
    if completed.returncode != 0:
        print(completed.stderr.strip(), file=sys.stderr)
        return completed.returncode

    records = normalize(parse_json_output(completed.stdout), args.timezone)
    text = json.dumps(records, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
