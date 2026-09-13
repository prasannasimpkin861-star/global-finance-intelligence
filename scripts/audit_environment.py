#!/usr/bin/env python3
"""Inspect locally available finance/news skills and optional provider configuration."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path


KNOWN_SKILLS = {
    "a-stock-data": "A股行情、公告、研报、资金和市场信号",
    "news-aggregator-skill": "国内外新闻、RSS、华尔街见闻和 Reuters fallback",
    "agent-reach": "联网搜索与官方来源核验",
    "humanizer-zh": "中文财经简报终稿语言检查",
    "global-finance-intelligence": "当前全球财经资讯编排 Skill",
}

OPTIONAL_MARKERS = {
    "opennews": ("opennews", "open-news", "6551"),
    "trendradar": ("trendradar", "trend-radar"),
    "jin10": ("jin10", "金十"),
    "yfmcp": ("yfmcp", "yfinance"),
    "rsshub": ("rsshub",),
    "forgerss": ("forgerss", "forge-rss"),
}


def skill_roots() -> list[Path]:
    home = Path.home()
    roots = [home / ".codex" / "skills", home / ".agents" / "skills"]
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        roots.insert(0, Path(codex_home) / "skills")
    unique: list[Path] = []
    for root in roots:
        resolved = root.expanduser()
        if resolved not in unique:
            unique.append(resolved)
    return unique


def find_skill(name: str) -> str | None:
    for root in skill_roots():
        candidate = root / name / "SKILL.md"
        if candidate.is_file():
            return str(candidate.parent)
    return None


def read_config_text() -> tuple[list[str], str]:
    candidates = [
        Path.home() / ".codex" / "config.toml",
        Path.home() / ".codex" / "config.json",
        Path.home() / ".config" / "codex" / "config.toml",
    ]
    found: list[str] = []
    chunks: list[str] = []
    for path in candidates:
        if path.is_file():
            found.append(str(path))
            try:
                chunks.append(path.read_text(encoding="utf-8", errors="ignore").lower())
            except OSError:
                pass
    return found, "\n".join(chunks)


def audit() -> dict:
    config_files, config_text = read_config_text()
    skills = {
        name: {"available": bool(path := find_skill(name)), "path": path, "role": role}
        for name, role in KNOWN_SKILLS.items()
    }
    optional = {}
    for provider, markers in OPTIONAL_MARKERS.items():
        configured = any(marker.lower() in config_text for marker in markers)
        env_hits = sorted(
            key for key in os.environ if any(marker.upper().replace("-", "_") in key.upper() for marker in markers)
        )
        optional[provider] = {
            "config_marker_found": configured,
            "environment_variable_names": env_hits,
            "status": "possibly_configured" if configured or env_hits else "not_detected",
        }

    commands = {
        command: shutil.which(command)
        for command in ("python", "git", "docker", "node", "uv")
    }

    return {
        "skill_roots": [str(p) for p in skill_roots()],
        "skills": skills,
        "optional_providers": optional,
        "config_files_checked": config_files,
        "commands": commands,
        "notes": [
            "检测到配置痕迹不等于接口已经可用，正式调用前仍需做一次只读测试。",
            "脚本不会读取或输出密钥值，只报告可能相关的环境变量名称。",
        ],
    }


def print_text(result: dict) -> None:
    print("全球财经资讯雷达：环境检查")
    print("\n已安装 Skills：")
    for name, item in result["skills"].items():
        status = "可用" if item["available"] else "未发现"
        suffix = f" — {item['path']}" if item["path"] else ""
        print(f"- {name}: {status}{suffix}")

    print("\n可选提供方配置痕迹：")
    for name, item in result["optional_providers"].items():
        print(f"- {name}: {item['status']}")

    print("\n常用命令：")
    for name, path in result["commands"].items():
        print(f"- {name}: {path or '未发现'}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()
    result = audit()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_text(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
