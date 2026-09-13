# Contributing

欢迎提交 Issue 和 Pull Request。

## 基本要求

- 不要提交 API Key、Token、Cookie、账号或个人路径。
- 新增来源时说明来源类型、地区、覆盖类别和访问方式。
- 官方来源优先于聚合来源；聚合源不能冒充官方接口。
- 新增确定性处理逻辑时补充测试。
- 不要在示例中包含真实用户数据或受版权保护的全文内容。

## 提交前检查

```bash
python scripts/test_normalize_rank.py
python scripts/check_package.py
```

请确保：

- `SKILL.md` 没有未完成的 TODO。
- JSON 文件可以正常解析。
- Python 脚本可以通过语法检查。
- 文档中的相对路径有效。
- 没有写入本机绝对路径。
