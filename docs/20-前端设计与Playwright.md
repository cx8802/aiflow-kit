# 前端设计与 Playwright

`aiflow-kit` 默认安装前端设计和浏览器验证能力：

- `frontend-design`：负责 UI 设计、视觉质量、布局、组件状态和响应式方案。
- `frontend-verify`：负责 UI 改动后的验证清单。
- `playwright-verify`：负责浏览器截图、交互和视口验证流程。
- `@playwright/test`：安装到项目级 `.tools/frontend-tools`，不写用户全局 npm。

## 自动安装

快速安装和更新会自动执行：

```bat
aiflow frontend install
```

对应脚本：

```bat
scripts\quick-install.bat
scripts\aiflow-update.bat
```

安装位置：

```text
.tools/frontend-tools
.tools/ms-playwright
```

`.tools/` 已加入 `.gitignore`。

在其他项目里执行 `aiflow frontend install` 时，如果目标项目缺少忽略规则，会自动给 `.gitignore` 追加：

```text
.tools/
.cache/
```

## 手动安装

```bat
scripts\use-project-env.bat
aiflow frontend install
```

只看命令，不执行：

```bat
aiflow frontend install --dry-run
```

只安装 npm 包，不下载浏览器：

```bat
aiflow frontend install --skip-browsers
```

浏览器下载默认按海外资源处理，会使用 `http://127.0.0.1:10808`。如果不需要代理：

```bat
aiflow frontend install --no-proxy
```

## 设计与验证分工

| 能力 | 用途 |
| --- | --- |
| `frontend-design` | 从产品目标出发设计页面、组件、状态、响应式布局 |
| `frontend-verify` | 检查 UI 实现是否符合项目、是否有溢出和状态缺失 |
| `playwright-verify` | 用浏览器打开页面、截图、测试交互 |

## 推荐流程

```text
需求 -> frontend-design -> 实现 -> playwright-verify -> frontend-verify -> review
```

## 项目配置

`.aiflow/config.toml` 里有前端配置：

```toml
[frontend]
enabled = false
dev_url = "http://localhost:3000"
desktop_viewport = "1440x900"
mobile_viewport = "390x844"
```

前端项目可以启用：

```bat
aiflow config set frontend.enabled true
aiflow config set frontend.dev_url "http://localhost:5173"
```

## 边界

- 不使用 PowerShell `.ps1`。
- 不执行 `npm install -g` 到用户全局。
- 不把 Playwright 浏览器下载到用户全局目录。
- 不把具体项目的 UI 规则写入全局 Skills。
