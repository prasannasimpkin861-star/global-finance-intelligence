# 标准记录结构

采集器输出可以是 JSON 数组或 JSONL。字段缺失时保留为空，不要编造。

```json
{
  "title": "事件标题",
  "event_key": "可选；同一事件的跨语言稳定标识",
  "url": "https://原文链接",
  "source": "来源名称",
  "source_tier": 1,
  "official": true,
  "published_at": "2026-09-13T08:30:00+08:00",
  "event_time": "2026-09-13T08:30:00+08:00",
  "summary": "只写来源明确表达的事实",
  "category": "central_bank",
  "region": ["CN"],
  "markets": ["A-share", "CNY", "CN-bonds"],
  "assets": ["CNY", "CN10Y"],
  "status": "confirmed",
  "impact_analysis": {
    "market_direction": [
      {
        "market": "A-share",
        "bias": "mixed",
        "horizon": "1-3d",
        "reason": "一句话说明指数或风险偏好的传导依据"
      }
    ],
    "style": ["value-over-growth"],
    "beneficiary_sectors": [
      {
        "sector": "受益行业",
        "reason": "订单、价格、成本、政策或估值依据",
        "directness": "direct",
        "confidence": "medium"
      }
    ],
    "pressured_sectors": [],
    "transmission_path": ["事件", "中间变量", "盈利或估值", "市场/行业"],
    "priced_in": "partial",
    "evidence_type": "expected",
    "confidence": "medium",
    "conditions": ["结论成立的关键条件"]
  },
  "importance": 0,
  "tags": ["monetary-policy"]
}
```

## 字段口径

- `event_key`：可选。采集或整理阶段确认两条记录属于同一事件时，为它们填写相同标识；这能合并中英文标题或措辞差异很大的报道。
- `source_tier`：1 为官方和一线媒体；2 为专业财经媒体和大型数据平台；3 为行业网站、聚合器和研究评论；4 为社交媒体、论坛或未知来源。
- `official`：只有政府、央行、监管、交易所、统计机构、法定公告或公司官方发布才为 `true`。
- `published_at`：来源发布文章的时间，使用 ISO 8601 并带时区。
- `event_time`：事件真正发生或数据正式公布的时间；未知时为空。
- `category` 推荐值：`central_bank`、`macro_data`、`regulation`、`company_filing`、`earnings`、`ma_financing`、`geopolitics`、`rates_credit`、`fx`、`commodities`、`crypto`、`market_move`、`analysis`。
- `status` 推荐值：`confirmed`、`reported`、`rumor`、`analysis`。
- `importance` 可由采集器提供；没有时交给 `normalize_rank.py` 初步计算。

- `impact_analysis` 是分析字段，不是来源事实。没有充分依据时可留空，不能从标题机械生成。
- `market_direction[].bias` 推荐值：`positive`、`negative`、`mixed`、`unclear`。
- `horizon` 推荐值：`observed`、`intraday`、`1-3d`、`1-4w`、`quarter+`。
- `directness` 推荐值：`direct`、`indirect`；`confidence` 推荐值：`high`、`medium`、`low`。
- `priced_in` 推荐值：`yes`、`partial`、`no`、`unknown`；休市期间通常为 `unknown`，正文表述为“尚待开盘验证”。
- `evidence_type` 推荐值：`observed`、`expected`、`mixed`，用于区分真实盘面反应和分析预期。

### Serenity/X 帖子可选字段

- `author_handle`：固定为经过核验的 `@aleabitoreddit`；账号异常时不要自动替换。
- `post_id`、`conversation_id`：用于去重和合并 thread。
- `post_type`：`original`、`quote`、`reply`、`repost`、`article_share`。
- `tickers`、`themes`：原帖明确涉及或经核验后可靠映射的标的与主题。
- `stance`：`bullish`、`bearish`、`neutral`、`unclear`。
- `stance_change`：`new`、`strengthened`、`maintained`、`reduced`、`reversed`、`unclear`。
- `claim_types`：`verifiable_fact`、`supply_chain_inference`、`opinion`、`price_prediction`、`position_or_performance_self_report`。

以上字段记录作者内容，不代表帖子中的外部事实已经核实。

## 聚类后的输出

脚本会生成事件簇，保留：

- `representative`：优先选择官方、来源层级高且时间较新的记录。
- `evidence`：事件簇内所有来源。
- `source_count`：独立来源数。
- `score`：确定性初步评分。
- `score_reasons`：评分依据，便于人工复核。

评分只用于排序，不代表投资收益概率或事实可信度。

