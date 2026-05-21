# AIFlow 浏览器扩展

这个目录是 Chrome/Edge 扩展源码。扩展运行时保持零 npm 依赖：

- 运行和打包不需要 bundler
- 浏览器运行时不需要 npm 包
- `aiflow browser pack` 直接打包浏览器需要的静态文件

`package.json` 只提供本地开发检查脚本：

```bat
npm run check
```

## 当前主流程

1. 在项目里启动 bridge：

```bat
aiflow browser serve
```

2. 在扩展侧栏填写 bridge 地址和 project token。
3. 点击 `连接`。
4. 点击 `选择页面元素`，在当前网页中单击目标元素。
5. bridge 会把元素摘要写到 `.aiflow/browser/elements/`。

元素选择器不会读取 cookie、localStorage、sessionStorage 或请求头；`password` 和 `hidden` 输入框的值不会写回。

## 后台自动化

自动化任务由项目后台排队控制：

```bat
aiflow browser automate --step "fill;;#search;;aiflow" --step "click;;button[type=submit]" --step "wait;;;;1000" --step "extract;;main"
aiflow browser serve
```

扩展侧栏的 `高级功能` 里可以手动执行下一条任务，也可以启动轮询执行器。插件只负责在当前浏览器页面执行任务，任务来源和结果落盘都在项目后台。

只有在明确需要 TypeScript 编译、lint 或 Playwright 扩展端到端验证时，才在这里增加开发依赖。页面动作本身应优先保持直接 DOM 和 Chrome extension API 调用。
