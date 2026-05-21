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

2. 点击扩展图标，打开独立配置页。
3. 填写 bridge 地址和 project token，点击 `连接`。
4. 打开目标网页的 DevTools。
5. 用 DevTools 左上角的原生元素选择工具选中页面元素。
6. 切到 DevTools 的 `AIFlow` 面板，点击 `发送当前选中元素`。
7. bridge 会把元素摘要写到 `.aiflow/browser/elements/`。

元素读取基于 DevTools 当前 `$0` 元素。扩展不会读取 cookie、localStorage、sessionStorage 或请求头；`password` 和 `hidden` 输入框的值不会写回。

## 后台自动化

自动化任务由项目后台排队控制：

```bat
aiflow browser automate --step "fill;;#search;;aiflow" --step "click;;button[type=submit]" --step "wait;;;;1000" --step "extract;;main"
aiflow browser serve
```

扩展页面不提供队列执行器或 adapter 表单。插件只负责配置连接，以及在 DevTools 面板读取当前选中的页面元素；任务来源、动作决策和结果落盘都在项目后台。
