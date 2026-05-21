# Frontend Design Skill 安装指南

## 简介

frontend-design 是 Anthropic 官方提供的 Claude Code skill，用于创建独特、生产级的前端界面，避免 generic "AI slop" 美学。

## 安装方式

### 方式一：官方插件命令安装（推荐）

```bash
/plugin install frontend-design@anthropics/claude-code
```

### 方式二：手动下载安装

```bash
mkdir -p ~/.claude/skills/frontend-design
curl -o ~/.claude/skills/frontend-design/SKILL.md \
  https://raw.githubusercontent.com/anthropics/claude-code/main/plugins/frontend-design/skills/frontend-design/SKILL.md
```

本项目已采用方式二完成安装，文件位于：
`C:\Users\15638\.claude\skills\frontend-design\SKILL.md`

## 功能特点

- **设计思维**: 在编码前理解上下文，确立大胆的美学方向
- **字体选择**: 使用独特、有特色的字体，避免 Inter、Roboto、Arial 等通用字体
- **配色方案**: 确立凝聚力的美学，使用 CSS 变量保证一致性
- **动效设计**: 使用动画实现效果和微交互，优先使用 CSS 解决方案
- **空间构图**: 不对称、重叠、对角线流动、打破网格的元素
- **视觉细节**: 创造氛围和深度，而非默认纯色

## 使用方式

Claude Code 会自动在以下场景使用此 skill：
- 构建 Web 组件
- 创建页面
- 开发应用程序
- 设计界面

## 设计指南

### 避免的 AI 生成美学
- 过度使用的字体家族（Inter、Roboto、Arial、system fonts）
- 陈词滥调的配色方案（特别是白色背景上的紫色渐变）
- 可预测的布局和组件模式
- 缺乏上下文特定特征的千篇一律的设计

### 推荐的美学方向
- 野兽派/原始风格
- 复古未来主义
- 有机/自然风格
- 奢华/精致风格
- 复古/玩具风格
- 编辑/杂志风格
- 艺术装饰/几何风格
- 柔和/ pastel 风格
- 工业/实用主义风格

## 参考资源

- [Frontend Design Plugin - GitHub](https://github.com/anthropics/claude-code/tree/main/plugins/frontend-design)
- [Frontend Aesthetics Cookbook](https://github.com/anthropics/claude-code/blob/main/plugins/frontend-design/docs/frontend-aesthetics-cookbook.md)
