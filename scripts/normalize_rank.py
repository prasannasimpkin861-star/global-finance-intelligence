#!/usr/bin/env python3
"""Normalize, cluster, deduplicate and rank finance-news records using only stdlib."""

from __future__ import annotations

import argparse
import json
import math
import re
import unicodedata
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit, urlunsplit

CATEGORY_WEIGHTS = {
    "central_bank": 24,
    "regulation": 22,
    "macro_data": 20,
    "geopolitics": 19,
    "company_filing": 18,
    "ma_financing": 18,
    "earnings": 17,
    "rates_credit": 16,
    "commodities": 15,
    "fx": 14,
    "crypto": 13,
    "market_move": 12,
    "analysis": 5,
}

TIER_WEIGHTS = {1: 20, 2: 12, 3: 6, 4: 0}
STATUS_WEIGHTS = {"confirmed": 10, "reported": 4, "analysis": 1, "rumor": -8}

HIGH_IMPACT_TERMS = (
    "央行", "降息", "加息", "降准", "利率决议", "fomc", "federal reserve", "ecb",
    "制裁", "战争", "停火", "关税", "违约", "破产", "并购", "收购", "重组",
    "业绩预告", "盈利预警", "财报", "回购", "停牌", "退市", "监管处罚",
    "cpi", "ppi", "gdp", "payroll", "就业", "通胀", "opec", "出口管制",
)

TRACKING_QUERY_KEYS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "spm", "from", "source", "ref", "share_token",
}


def load_records(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8-sig")
    stripped = text.lstrip()
    if not stripped:
        return []
    if stripped.startswith("["):
        data = json.loads(text)
        if not isinstance(data, list):
            raise ValueError("JSON 顶层必须是数组")
        return [item for item in data if isinstance(item, dict)]
    records: list[dict[str, Any]] = []
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        item = json.loads(line)
        if not isinstance(item, dict):
            raise ValueError(f"JSONL 第 {number} 行不是对象")
        records.append(item)
    return records


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def canonical_url(value: Any) -> str:
    url = clean_text(value)
    if not url:
        return ""
    try:
        parts = urlsplit(url)
        query_parts = []
        for pair in parts.query.split("&"):
            if not pair:
                continue
            key = pair.split("=", 1)[0].lower()
            if key not in TRACKING_QUERY_KEYS and not key.startswith("utm_"):
                query_parts.append(pair)
        path = parts.path.rstrip("/") or "/"
        return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, "&".join(query_parts), ""))
    except ValueError:
        return url


def normalize_title(value: Any) -> str:
    text = unicodedata.normalize("NFKC", clean_text(value)).lower()
    text = re.sub(r"[\[【(（].{0,18}?[\]】)）]", " ", text)
    text = re.sub(r"[^\w\u3400-\u9fff]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def features(title: str) -> set[str]:
    compact = title.replace(" ", "")
    chars = {compact[i : i + 3] for i in range(max(0, len(compact) - 2))}
    words = {word for word in title.split() if len(word) > 1}
    return chars | words


def similarity(a: dict[str, Any], b: dict[str, Any]) -> float:
    if a.get("event_key") and a["event_key"] == b.get("event_key"):
        return 1.0
    if a["canonical_url"] and a["canonical_url"] == b["canonical_url"]:
        return 1.0
    ta, tb = a["normalized_title"], b["normalized_title"]
    if not ta or not tb:
        return 0.0
    sequence = SequenceMatcher(None, ta, tb).ratio()
    fa, fb = a["features"], b["features"]
    union = fa | fb
    jaccard = len(fa & fb) / len(union) if union else 0.0
    return max(sequence, jaccard)


def parse_datetime(value: Any) -> datetime | None:
    text = clean_text(value)
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def to_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [clean_text(v) for v in value if clean_text(v)]
    text = clean_text(value)
    return [text] if text else []


def normalize_record(item: dict[str, Any], index: int) -> dict[str, Any]:
    title = clean_text(item.get("title") or item.get("headline"))
    source = clean_text(item.get("source") or item.get("publisher") or "unknown")
    try:
        tier = int(item.get("source_tier", 3))
    except (TypeError, ValueError):
        tier = 3
    tier = max(1, min(4, tier))
    official = bool(item.get("official", False))
    status = clean_text(item.get("status") or ("confirmed" if official else "reported")).lower()
    category = clean_text(item.get("category") or "analysis").lower()
    published_at = clean_text(item.get("published_at") or item.get("time") or item.get("published"))
    url = canonical_url(item.get("url") or item.get("link"))
    normalized = {
        "id": clean_text(item.get("id")) or f"item-{index + 1}",
        "title": title,
        "event_key": clean_text(item.get("event_key") or item.get("canonical_event_id")).casefold(),
        "url": url,
        "canonical_url": url,
        "source": source,
        "source_tier": tier,
        "official": official,
        "published_at": published_at,
        "event_time": clean_text(item.get("event_time")),
        "summary": clean_text(item.get("summary") or item.get("description") or item.get("content")),
        "category": category,
        "region": to_list(item.get("region")),
        "markets": to_list(item.get("markets") or item.get("market")),
        "assets": to_list(item.get("assets") or item.get("asset")),
        "status": status if status in STATUS_WEIGHTS else "reported",
        "tags": to_list(item.get("tags")),
        "input_importance": item.get("importance"),
        "normalized_title": normalize_title(title),
    }
    normalized["features"] = features(normalized["normalized_title"])
    normalized["published_dt"] = parse_datetime(published_at)
    return normalized


def choose_representative(records: list[dict[str, Any]]) -> dict[str, Any]:
    def key(record: dict[str, Any]) -> tuple:
        timestamp = record["published_dt"].timestamp() if record["published_dt"] else 0
        return (record["official"], -record["source_tier"], timestamp, len(record["summary"]))
    return max(records, key=key)


def calculate_score(records: list[dict[str, Any]], now: datetime) -> tuple[int, list[str]]:
    rep = choose_representative(records)
    score = 0.0
    reasons: list[str] = []

    if rep["official"]:
        score += 25
        reasons.append("官方或一手来源 +25")

    tier_points = TIER_WEIGHTS.get(rep["source_tier"], 0)
    score += tier_points
    reasons.append(f"来源层级 T{rep['source_tier']} +{tier_points}")

    category_points = CATEGORY_WEIGHTS.get(rep["category"], 5)
    score += category_points
    reasons.append(f"类别 {rep['category']} +{category_points}")

    status_points = STATUS_WEIGHTS.get(rep["status"], 0)
    score += status_points
    if status_points:
        reasons.append(f"状态 {rep['status']} {status_points:+d}")

    independent_sources = len({r["source"].casefold() for r in records if r["source"]})
    corroboration = min(16, max(0, independent_sources - 1) * 4)
    score += corroboration
    if corroboration:
        reasons.append(f"{independent_sources} 个来源交叉印证 +{corroboration}")

    dt = rep["published_dt"]
    if dt:
        hours = max(0.0, (now - dt).total_seconds() / 3600)
        recency = max(0, round(15 * math.exp(-hours / 36)))
        score += recency
        reasons.append(f"时效性 +{recency}")
    else:
        score -= 5
        reasons.append("缺少可解析发布时间 -5")

    haystack = f"{rep['title']} {rep['summary']}".lower()
    hits = sum(1 for term in HIGH_IMPACT_TERMS if term in haystack)
    impact = min(12, hits * 3)
    if impact:
        score += impact
        reasons.append(f"重大事件关键词 +{impact}")

    if not rep["url"]:
        score -= 6
        reasons.append("缺少原文链接 -6")

    supplied = rep.get("input_importance")
    if isinstance(supplied, (int, float)):
        contribution = max(-10, min(10, float(supplied) / 10))
        score += contribution
        reasons.append(f"输入重要性修正 {contribution:+.1f}")

    return max(0, min(100, round(score))), reasons


def public_record(record: dict[str, Any]) -> dict[str, Any]:
    hidden = {"canonical_url", "normalized_title", "features", "published_dt", "input_importance"}
    return {key: value for key, value in record.items() if key not in hidden}


def cluster_records(records: Iterable[dict[str, Any]], threshold: float) -> list[list[dict[str, Any]]]:
    clusters: list[list[dict[str, Any]]] = []
    for record in records:
        best_index = None
        best_score = 0.0
        for index, cluster in enumerate(clusters):
            score = max(similarity(record, existing) for existing in cluster[:8])
            if score > best_score:
                best_index, best_score = index, score
        if best_index is not None and best_score >= threshold:
            clusters[best_index].append(record)
        else:
            clusters.append([record])
    return clusters


def process(items: list[dict[str, Any]], threshold: float, min_score: int, hours: float | None) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    normalized = [normalize_record(item, index) for index, item in enumerate(items)]
    normalized = [item for item in normalized if item["title"]]
    if hours is not None:
        cutoff_seconds = hours * 3600
        normalized = [
            item for item in normalized
            if item["published_dt"] is None or (now - item["published_dt"]).total_seconds() <= cutoff_seconds
        ]
    normalized.sort(key=lambda item: item["published_dt"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)

    output: list[dict[str, Any]] = []
    for number, cluster in enumerate(cluster_records(normalized, threshold), 1):
        rep = choose_representative(cluster)
        score, reasons = calculate_score(cluster, now)
        if score < min_score:
            continue
        evidence = sorted(
            (public_record(item) for item in cluster),
            key=lambda item: item.get("published_at", ""),
            reverse=True,
        )
        output.append({
            "cluster_id": f"event-{number}",
            "score": score,
            "score_reasons": reasons,
            "source_count": len({item["source"].casefold() for item in cluster}),
            "representative": public_record(rep),
            "evidence": evidence,
        })
    output.sort(key=lambda item: (item["score"], item["representative"].get("published_at", "")), reverse=True)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="JSON 数组或 JSONL 文件")
    parser.add_argument("--output", type=Path, help="输出路径；省略时写到标准输出")
    parser.add_argument("--threshold", type=float, default=0.68, help="聚类相似度阈值，默认 0.68")
    parser.add_argument("--min-score", type=int, default=0, help="最低保留分数")
    parser.add_argument("--hours", type=float, help="只保留最近若干小时；无时间记录不会被自动删除")
    parser.add_argument("--pretty", action="store_true", help="缩进输出 JSON")
    args = parser.parse_args()

    if not 0.0 <= args.threshold <= 1.0:
        parser.error("--threshold 必须在 0 到 1 之间")
    items = load_records(args.input)
    result = process(items, args.threshold, args.min_score, args.hours)
    text = json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

