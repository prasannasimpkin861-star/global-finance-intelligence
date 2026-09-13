# Security Policy

## Reporting a vulnerability

请不要在公开 Issue 中提交 API Key、Token、Cookie、账号信息或可被直接利用的安全细节。

发现安全问题时，请通过 GitHub Security Advisory 的私密报告功能联系维护者。报告中建议包含：

- 受影响的文件和版本
- 可复现步骤
- 可能影响
- 建议修复方式（如有）

## Secrets

本项目不需要内置任何密钥。第三方 MCP、API 或数据服务的凭证应保存在本地环境变量或 Codex 配置中，不得提交到仓库。

`audit_environment.py` 只报告可能相关的环境变量名称，不会读取或显示变量值。

## Third-party content

本项目只提供来源编排和数据处理流程。第三方新闻、市场数据、公告、研报和付费内容仍受原网站条款、版权和数据许可约束。
