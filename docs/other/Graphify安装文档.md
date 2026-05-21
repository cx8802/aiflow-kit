# Graphify 安装文档

本文档记录在 Windows + PowerShell 环境中，为 Claude Code 和 Codex 全局安装 `nodesify-graphify` 的步骤。

## 1. 前置条件

确认本机已安装 Node.js 和 npm：

```powershell
node --version
npm.cmd --version
```

如果直接运行 `npm` 报 PowerShell 执行策略错误，使用 `npm.cmd`。

## 2. 全局安装 Graphify CLI

`nodesify-graphify` 命令来自 npm 包 `@nodesify/graphify`：

```powershell
npm.cmd install -g @nodesify/graphify
```

验证安装：

```powershell
nodesify-graphify --version
nodesify-graphify --help
```

## 3. 处理 PowerShell 的 `.ps1` 拦截

npm 在 Windows 上会同时生成 `.ps1` 和 `.cmd` shim。当前 PowerShell 执行策略可能会阻止 `.ps1` 文件运行。

如果执行 `nodesify-graphify --help` 时看到类似错误：

```text
nodesify-graphify.ps1 cannot be loaded because running scripts is disabled on this system
```

有两种处理方式。

方式一：显式使用 `.cmd`：

```powershell
nodesify-graphify.cmd --help
```

方式二：删除被拦截的 `.ps1` shim，让 PowerShell 自动使用 `.cmd`：

```powershell
Remove-Item -Path D:\program\nodejs\nodesify-graphify.ps1
```

删除前可先确认 `.cmd` 存在：

```powershell
Test-Path D:\program\nodejs\nodesify-graphify.cmd
```

## 4. 安装 Claude Code 技能

运行：

```powershell
nodesify-graphify install --platform claude
```

安装后通常会写入：

```text
%USERPROFILE%\.claude\skills\graphify\SKILL.md
%USERPROFILE%\.claude\CLAUDE.md
```

验证：

```powershell
Test-Path $HOME\.claude\skills\graphify\SKILL.md
Get-Content $HOME\.claude\CLAUDE.md
```

## 5. 安装 Codex 技能

运行：

```powershell
nodesify-graphify install --platform codex
```

安装器可能会写入：

```text
%USERPROFILE%\.agents\skills\graphify\SKILL.md
```

当前 Codex 桌面环境实际读取的全局技能目录通常是：

```text
%USERPROFILE%\.codex\skills
```

因此建议确认并补齐：

```powershell
New-Item -ItemType Directory -Force -Path "$HOME\.codex\skills\graphify" | Out-Null
Copy-Item -Force "$HOME\.agents\skills\graphify\SKILL.md" "$HOME\.codex\skills\graphify\SKILL.md"
```

验证：

```powershell
Test-Path $HOME\.codex\skills\graphify\SKILL.md
```

## 6. 在项目中初始化图谱

进入项目根目录后运行：

```powershell
nodesify-graphify run .
```

该命令会生成 `.graphify/`，常见文件包括：

```text
.graphify/db.sqlite
.graphify/graph.json
.graphify/graph_report.md
```

验证：

```powershell
Test-Path .\.graphify\graph_report.md
nodesify-graphify stats --graph .
```

## 7. 日常使用规则

有 `.graphify/` 的项目中，Claude Code 和 Codex 应优先使用 Graphify 获取架构上下文：

```powershell
Get-Content .\.graphify\graph_report.md
nodesify-graphify query "authentication flow"
nodesify-graphify explain "SomeService"
nodesify-graphify path "A" "B"
```

修改代码后更新图谱：

```powershell
nodesify-graphify update .
```

## 8. 当前机器安装结果

本机已完成：

```text
@nodesify/graphify@0.2.2
Claude Code skill: %USERPROFILE%\.claude\skills\graphify\SKILL.md
Codex skill: %USERPROFILE%\.codex\skills\graphify\SKILL.md
Installer Codex skill: %USERPROFILE%\.agents\skills\graphify\SKILL.md
```

并已验证：

```powershell
nodesify-graphify --version
# 0.2.2
```
