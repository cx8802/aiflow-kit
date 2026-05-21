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

DevTools 面板还提供：

- `发送页面代码`：写入 `.aiflow/browser/pages/`
- `发送请求摘要`：写入 `.aiflow/browser/requests/`
- `执行后端下一条任务`：读取并执行当前项目的 automation queue

配置页也提供 `执行后端下一条任务`。这个按钮不会让用户手工输入 URL，而是读取 bridge 中已经排队的任务；遇到 `open` 步骤时，扩展会用浏览器标签页打开后端提供的网址，再继续执行后续步骤。

请求摘要只保留 method、脱敏 URL、status、MIME、resource type 和耗时，不写 headers、cookies、请求体或响应体。

## 后台自动化

自动化任务由项目后台排队控制：

```bat
aiflow browser automate --step "open;;https://example.com" --step "fill;;#search;;aiflow" --step "click;;button[type=submit]" --step "wait;;;;1000" --step "extract;;main"
aiflow browser serve
```

扩展配置页只负责连接 bridge 和触发队列任务。打开网站、点击、填表、等待和提取内容都应该由项目后台排队，再通过配置页或 DevTools 面板的 `执行后端下一条任务` 执行。
