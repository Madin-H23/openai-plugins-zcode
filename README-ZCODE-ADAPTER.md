# openai-plugins-zcode

[openai/plugins](https://github.com/openai/plugins)（OpenAI Codex 官方插件市场）的 **ZCode 适配版 fork**。

openai/plugins 的市场清单位于 `.agents/plugins/marketplace.json`（Codex 专有格式），
ZCode 3.11.x 克隆仓库后只在根目录查找 `.claude-plugin/marketplace.json` 或 `marketplace.json`，
且不识别 Codex 的 `{"source":"local","path":"./plugins/xxx"}` 嵌套源写法——
因此直接在 ZCode 里添加 `openai/plugins` 会报
`Marketplace manifest not found in git repo`。

本仓库在 fork 基础上追加了一个 ZCode 兼容的 `.claude-plugin/marketplace.json`
（由脚本从上游 Codex 清单自动生成），使 ZCode 可以直接以 git 仓库形式添加本市场。

## 在 ZCode 中使用

UI「添加插件市场」直接填：

```
Madin-H23/openai-plugins-zcode
```

或完整 URL `https://github.com/Madin-H23/openai-plugins-zcode`。

> 注意：这些插件原本面向 Codex 构建。skills / commands / MCP 配置类内容在 ZCode
> 中可用；标注 `products: ["CODEX"]` 的插件及依赖 Codex 专属运行时（如 `.app.json`）
> 的功能可能不完整。多数企业集成类插件（gmail/slack/notion 等）安装时需要对应
> 服务的 OAuth 授权。

## 与上游保持同步

上游 `openai/plugins` 更新后同步 fork（GitHub fork 页面的 Sync fork 按钮或
`gh repo sync Madin-H23/openai-plugins-zcode --source openai/plugins`），
然后重新生成清单并推送：

```bash
python generate_marketplace.py
git add .claude-plugin/marketplace.json
git commit -m "chore: regenerate ZCode marketplace manifest"
git push
```

`generate_marketplace.py` 的转换规则：

| 上游 Codex 写法 | 生成到 ZCode 清单 |
|---|---|
| `{"source":"local","path":"./plugins/x"}` | 字符串源 `"plugins/x"`（相对清单所在根目录解析） |
| `{"source":"url","url":"...git"}` | `{"source":"git","url":"...git"}` |
| `.codex-plugin/plugin.json` 的 name/version | 插件 name/version 字段 |

上游 2 个 CrowdStrike 远程 git 源插件同样以 `git` 源输出；name 不符合
`^[a-z0-9][a-z0-9._-]{0,127}$` 的条目会被跳过并打印。

## 文件结构

- `.claude-plugin/marketplace.json` — **生成物**，ZCode 市场清单（勿手改）
- `generate_marketplace.py` — 生成/校验脚本
- `.agents/plugins/marketplace.json`、`plugins/` — 上游原样内容

## License

上游仓库未声明顶层 License（部分插件目录内有各自 LICENSE）。本仓库新增的
适配脚本与生成的清单按原样提供，仅做格式转换，不引入新的许可主张。
