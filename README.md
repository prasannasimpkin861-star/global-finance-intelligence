# Global Finance Intelligence

面向 Codex 的全球财经资讯采集、核验、去重、重要性排序与市场影响分析 Skill。

它把本机已有的新闻、A 股数据和联网检索能力组织成一套统一流程，适用于财经早报/晚报、全市场扫描、事件追踪、异动归因和跨来源核验。

> English: A Codex skill for collecting, verifying, deduplicating, clustering, and ranking important financial news across China and global markets.

## 功能

- 覆盖中国内地、香港、美国、欧洲、日本及全球宏观市场。
- 覆盖股票、债券、外汇、商品、加密资产、公司公告、财报、并购和监管事件。
- 优先核验政府、央行、监管机构、交易所、统计机构和公司官方披露。
- 区分事件发生时间、媒体发布时间和市场反应时间。
- 区分官方确认、媒体报道、市场传闻和分析推断。
- 对重点资讯标注大盘方向、市场风格、受益行业和承压行业。
- 给出“事件 → 利率/汇率/价格/需求/成本 → 盈利或估值 → 行业”的传导路径。
- 区分已发生的盘面反应与尚待开盘验证的预期影响，并标注时间窗口和置信度。
- 固定生成 **Serenity 专栏**：分析 `@aleabitoreddit` 最近 24 小时 X 帖子、观点变化及对美股与 A/H 股行业的可能影响。
- 支持 JSON/JSONL 标准化、URL 清洗、近似去重、跨语言事件标识和重要性评分。
- 可调用已安装的 `news-aggregator-skill` 采集国内外新闻。
- 可与 `a-stock-data`、`agent-reach`、`humanizer-zh` 及可选 MCP/API 协同工作。

## 目录结构

```text
global-finance-intelligence/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── assets/
│   ├── sample_items.json
│   └── source_registry.json
├── references/
│   ├── provider-routing.md
│   ├── serenity-column.md
│   ├── record-schema.md
│   └── source-map.md
└── scripts/
    ├── audit_environment.py
    ├── collect_local_news.py
    ├── normalize_rank.py
    └── test_normalize_rank.py
```

## 安装

### 直接克隆到 Codex Skills 目录

Windows PowerShell：

```powershell
git clone https://github.com/prasannasimpkin861-star/global-finance-intelligence.git "$HOME\.codex\skills\global-finance-intelligence"
```

macOS/Linux：

```bash
git clone https://github.com/prasannasimpkin861-star/global-finance-intelligence.git \
  "$HOME/.codex/skills/global-finance-intelligence"
```

发布后请把上面的 `OWNER` 替换为实际 GitHub 用户名。安装后重启 Codex 或新建任务。

## 使用

```text
$global-finance-intelligence 扫描最近24小时国内外最重要的财经资讯，
重点关注中国政策、美联储、美股、港股、原油、黄金和人民币，
合并重复事件并核验官方来源；逐条标注对大盘、市场风格及行业板块的影响、传导路径和置信度，并单列 Serenity 最近24小时 X 帖子分析。
```

其他示例：

```text
$global-finance-intelligence 给我做一份今天的全球财经早报。
```

```text
$global-finance-intelligence 核查今天黄金上涨的主要原因，区分确定因素和市场猜测。
```

## 环境检查

```bash
python scripts/audit_environment.py
python scripts/audit_environment.py --json
```

它会检查相关 Skill、常用命令和可选提供方的配置痕迹。脚本不会读取或输出密钥值。

## 采集本机新闻源

需要预先安装 `news-aggregator-skill`：

```bash
python scripts/collect_local_news.py \
  --sources wallstreetcn,international \
  --limit 20 \
  --output raw_items.json
```

可以使用 `--keyword`、`--deep`、`--timezone` 和 `--raw-output` 调整行为。

## 去重、聚类和排序

输入可以是 JSON 数组或 JSONL：

```bash
python scripts/normalize_rank.py \
  --input raw_items.json \
  --output ranked_events.json \
  --pretty
```

评分考虑：

- 是否官方或一手来源
- 来源层级
- 事件类别
- 确认状态
- 独立来源数量
- 时效性
- 重大事件关键词
- 是否存在原文链接

评分仅用于初步排序，不代表事实可信度或投资收益概率。

## 可选协同能力

本 Skill 不捆绑第三方密钥或服务。检测到以下能力时，可以按 `references/provider-routing.md` 组合使用：

- `a-stock-data`
- `news-aggregator-skill`
- `agent-reach`
- `humanizer-zh`
- OpenNews MCP
- TrendRadar
- Jin10 MCP
- Yahoo Finance/yfmcp
- RSSHub
- ForgeRSS

## 数据来源与限制

`assets/source_registry.json` 收录了一批国内外官方机构、交易所、媒体和行业来源。它是来源地图，不代表本项目拥有这些站点的内容，也不保证所有页面、RSS、API 或付费内容始终可访问。

使用者应遵守：

- 来源网站的服务条款、版权和许可要求
- robots.txt 及合理的抓取频率
- API 限额、付费墙和登录限制
- 证券市场数据的授权要求
- 所在司法辖区的相关法律法规

本项目不转载或重新授权第三方付费内容，只提供信息源编排、标准化和分析流程。

## 开发与测试

项目只依赖 Python 标准库：

```bash
python scripts/test_normalize_rank.py
python scripts/check_package.py
```

## 免责声明

本项目提供资讯采集和研究辅助流程，不构成投资建议、交易建议或收益承诺。重大决策应核对官方原文，并结合自身情况独立判断。

## License

MIT License，见 [LICENSE](LICENSE)。
