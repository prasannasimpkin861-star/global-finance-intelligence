#!/usr/bin/env python3
"""Run lightweight release checks for the public skill package."""

from __future__ import annotations

import json
import py_compile
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "SKILL.md",
    "README.md",
    "LICENSE",
    "SECURITY.md",
    "agents/openai.yaml",
    "assets/source_registry.json",
    "references/provider-routing.md",
    "references/record-schema.md",
    "references/source-map.md",
    "scripts/audit_environment.py",
    "scripts/collect_local_news.py",
    "scripts/normalize_rank.py",
]
SECRET_PATTERNS = {
    "OpenAI-style key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "GitHub classic token": re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    "GitHub fine-grained token": re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}
TEXT_SUFFIXES = {".md", ".py", ".yaml", ".yml", ".json", ".txt"}


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)


def main() -> int:
    failures: list[str] = []
    for relative in REQUIRED:
        if not (ROOT / relative).is_file():
            fail(f"缺少必需文件：{relative}", failures)

    skill = ROOT / "SKILL.md"
    if skill.is_file():
        text = skill.read_text(encoding="utf-8-sig")
        if not text.startswith("---\n"):
            fail("SKILL.md 缺少 YAML frontmatter", failures)
        if "name: global-finance-intelligence" not in text:
            fail("SKILL.md 名称不正确", failures)
        if "TODO" in text:
            fail("SKILL.md 仍包含 TODO", failures)

    for json_path in (ROOT / "assets").glob("*.json"):
        try:
            json.loads(json_path.read_text(encoding="utf-8-sig"))
        except Exception as exc:  # noqa: BLE001 - release checker should report all parse errors
            fail(f"JSON 无法解析：{json_path.relative_to(ROOT)}: {exc}", failures)

    for script in (ROOT / "scripts").glob("*.py"):
        try:
            py_compile.compile(str(script), doraise=True)
        except py_compile.PyCompileError as exc:
            fail(f"Python 语法错误：{script.name}: {exc}", failures)

    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8-sig", errors="ignore")
        if re.search(r"(?i)C:\\Users\\[A-Za-z0-9._-]+", text):
            fail(f"发现 Windows 用户绝对路径：{path.relative_to(ROOT)}", failures)
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                fail(f"发现疑似 {label}：{path.relative_to(ROOT)}", failures)

    if failures:
        print("Package validation failed:")
        for item in failures:
            print(f"- {item}")
        return 1

    print("Package validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
