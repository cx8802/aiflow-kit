# Windows 创建 Tauri 2 开发环境

> 适用场景：Windows 上开发 Tauri 2 桌面应用。本文假设已经安装好 Node.js 和 npm。

## 1. 先确认已有 Node 环境

打开 PowerShell，检查版本：

```powershell
node -v
npm -v
```

如果你准备使用 pnpm，可以启用 Corepack：

```powershell
corepack enable
pnpm -v
```

不想额外安装 pnpm 也没关系，后面的命令都可以直接使用 npm。

## 2. 安装 Microsoft C++ Build Tools

Tauri 在 Windows 上需要使用 MSVC 工具链编译 Rust 后端，所以必须安装 Microsoft C++ Build Tools。

1. 打开官方下载页：<https://visualstudio.microsoft.com/visual-cpp-build-tools/>
2. 下载并运行 Build Tools 安装器。
3. 在工作负载中勾选 `Desktop development with C++`。
4. 确认右侧组件里包含 MSVC 编译工具和 Windows SDK。
5. 安装完成后重启 PowerShell。

常见现象：

- 如果后面编译时报 `link.exe not found`、`Microsoft C++ Build Tools is required`，通常就是这一步没装好。
- 如果已经安装 Visual Studio，也要确认安装了 `Desktop development with C++` 工作负载。

## 3. 检查或安装 WebView2 Runtime

Tauri 在 Windows 上使用 Microsoft Edge WebView2 渲染界面。

Windows 10 1803 及以上版本通常已经带有 WebView2；Windows 11 默认预装。可以先继续后面的步骤，如果运行时报缺少 WebView2，再手动安装。

手动安装地址：

<https://developer.microsoft.com/microsoft-edge/webview2/>

选择 `Evergreen Bootstrapper` 下载并安装即可。

## 4. 安装 Rust

Tauri 2 使用 Rust 构建桌面端能力。推荐用 `rustup` 安装和管理 Rust。

PowerShell 执行：

```powershell
winget install --id Rustlang.Rustup
```

也可以去 Rust 官方页面下载安装器：

<https://www.rust-lang.org/tools/install>

安装过程中注意选择 MSVC 工具链。安装完成后，重启 PowerShell，然后检查：

```powershell
rustc -V
cargo -V
rustup show
```

如果默认工具链不是 MSVC，执行：

```powershell
rustup default stable-msvc
```

一般 64 位 Windows 对应的是：

```text
x86_64-pc-windows-msvc
```

## 5. 创建 Tauri 2 项目

### 方式一：使用官方 PowerShell 脚本

在你准备放项目的目录下执行：

```powershell
irm https://create.tauri.app/ps | iex
```

根据提示选择：

```text
Project name: 自己的项目名
Identifier: com.example.app
Frontend language: TypeScript / JavaScript
Package manager: npm
UI template: Vanilla / Vue / React / Svelte 等
UI flavor: TypeScript 或 JavaScript
```

如果只是学习 Tauri，建议先选：

```text
TypeScript / JavaScript
npm
Vanilla
TypeScript
```

### 方式二：使用 npm 创建

```powershell
npm create tauri-app@latest
```

后面的选项和 PowerShell 脚本方式基本一样。

## 6. 启动开发环境

进入项目目录：

```powershell
cd tauri-app
npm install
npm run tauri dev
```

第一次运行会下载 Rust 依赖并编译，时间会比较长。成功后会打开一个桌面窗口。

如果使用 pnpm，则命令是：

```powershell
cd tauri-app
pnpm install
pnpm tauri dev
```

## 7. 打包 Windows 应用

开发完成后执行：

```powershell
npm run tauri build
```

打包产物通常在：

```text
src-tauri/target/release/bundle/
```

如果打 MSI 安装包时报 `failed to run light.exe`，需要检查 Windows 的 `VBSCRIPT` 可选功能是否启用：

```text
Settings -> Apps -> Optional features -> More Windows features -> VBSCRIPT
```

## 8. 给已有前端项目接入 Tauri

如果已经有一个 Vite / Vue / React 项目，不想重新创建项目，可以在现有项目根目录执行：

```powershell
npm install -D @tauri-apps/cli@latest
npx tauri init
```

初始化时常见配置：

```text
What is your app name? 项目名
What should the window title be? 窗口标题
Where are your web assets located? ../dist
What is the url of your dev server? http://localhost:5173
What is your frontend dev command? npm run dev
What is your frontend build command? npm run build
```

然后运行：

```powershell
npx tauri dev
```

## 9. 常见问题

### PowerShell 提示脚本禁止运行

如果执行 npm 或脚本时报 `running scripts is disabled on this system`，可以执行：

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

然后重新打开 PowerShell。

### 编译时报找不到 link.exe

原因通常是没有安装 `Desktop development with C++`，或者安装后没有重启终端。

处理：

1. 重新打开 Visual Studio Installer。
2. 修改 Build Tools。
3. 勾选 `Desktop development with C++`。
4. 安装完成后重启 PowerShell。

### Rust 工具链不是 MSVC

执行：

```powershell
rustup default stable-msvc
rustup show
```

确认 active toolchain 是 `stable-x86_64-pc-windows-msvc` 这类名称。

### 第一次运行很慢

正常。第一次 `npm run tauri dev` 会下载 npm 依赖、Cargo 依赖，并编译 Rust 代码。后续增量编译会快很多。

### WebView2 缺失

安装 WebView2 Evergreen Runtime：

<https://developer.microsoft.com/microsoft-edge/webview2/>

## 10. 最小流程汇总

已经安装 Node 后，最短流程是：

```powershell
# 1. 安装 C++ Build Tools
# 勾选 Desktop development with C++

# 2. 安装 Rust
winget install --id Rustlang.Rustup
rustup default stable-msvc

# 3. 创建项目
npm create tauri-app@latest

# 4. 启动
cd tauri-app
npm install
npm run tauri dev
```

## 参考资料

- Tauri 2 Windows prerequisites: <https://v2.tauri.app/start/prerequisites/>
- Tauri 2 create project: <https://v2.tauri.app/start/create-project/>
- Tauri WebView versions: <https://v2.tauri.app/reference/webview-versions/>
