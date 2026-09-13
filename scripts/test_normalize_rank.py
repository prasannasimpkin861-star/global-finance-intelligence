#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("normalize_rank.py")
spec = importlib.util.spec_from_file_location("normalize_rank", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


class NormalizeRankTests(unittest.TestCase):
    def test_tracking_parameters_removed(self):
        self.assertEqual(
            module.canonical_url("https://example.com/a?utm_source=x&id=2#frag"),
            "https://example.com/a?id=2",
        )

    def test_exact_url_clusters(self):
        raw = [
            {"title": "央行发布政策", "url": "https://example.com/a?utm_source=x", "source": "A", "official": True},
            {"title": "央行政策发布", "url": "https://example.com/a", "source": "B"},
        ]
        normalized = [module.normalize_record(item, i) for i, item in enumerate(raw)]
        self.assertEqual(len(module.cluster_records(normalized, 0.68)), 1)

    def test_event_key_clusters_cross_language_titles(self):
        raw = [
            {"title": "美联储维持利率不变", "event_key": "fed-2026-09", "source": "A"},
            {"title": "Fed leaves rates unchanged", "event_key": "FED-2026-09", "source": "B"},
        ]
        normalized = [module.normalize_record(item, i) for i, item in enumerate(raw)]
        self.assertEqual(len(module.cluster_records(normalized, 0.68)), 1)

    def test_official_source_is_representative(self):
        raw = [
            {"title": "事件消息", "source": "论坛", "source_tier": 4, "official": False},
            {"title": "事件消息", "source": "监管机构", "source_tier": 1, "official": True},
        ]
        normalized = [module.normalize_record(item, i) for i, item in enumerate(raw)]
        representative = module.choose_representative(normalized)
        self.assertEqual(representative["source"], "监管机构")

    def test_impact_analysis_is_preserved(self):
        impact = {
            "market_direction": [{"market": "A-share", "bias": "mixed"}],
            "confidence": "medium",
        }
        normalized = module.normalize_record(
            {"title": "政策事件", "source": "官方", "impact_analysis": impact},
            0,
        )
        self.assertEqual(normalized["impact_analysis"], impact)
        self.assertEqual(module.public_record(normalized)["impact_analysis"], impact)

    def test_json_array_loads(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "items.json"
            path.write_text('[{"title":"测试"}]', encoding="utf-8")
            self.assertEqual(len(module.load_records(path)), 1)


if __name__ == "__main__":
    unittest.main()
