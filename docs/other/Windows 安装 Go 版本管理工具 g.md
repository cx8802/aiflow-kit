# Windows 安装 Go 版本管理工具 g

## 安装信息

- 工具仓库：https://github.com/voidint/g
- 安装版本：g 1.8.0
- 安装目录：`D:\program\g`
- 可执行文件：`D:\program\g\bin\g.exe`
- 下载代理：`http://127.0.0.1:10808`

已设置用户环境变量：

```powershell
G_HOME=D:\program\g
GOROOT=D:\program\g\go
G_EXPERIMENTAL=true
G_MIRROR=official|https://golang.google.cn/dl/
```

已追加到用户 `Path`：

```text
D:\program\g\bin
D:\program\g\go\bin
```

> 重新打开 PowerShell / CMD / IDE 终端后，新的环境变量才会自动生效。CMD 中不要把 `%G_HOME%\bin` 这种嵌套变量写进 `Path`，否则可能出现 `'g' is not recognized as an internal or external command`。

## 验证安装

```powershell
g --version
```

当前验证结果：

```text
g version 1.8.0
Experimental:  true
```

如果当前终端还没有刷新环境变量，可以临时执行：

```powershell
$env:G_HOME='D:\program\g'
$env:GOROOT='D:\program\g\go'
$env:G_EXPERIMENTAL='true'
$env:Path='D:\program\g\bin;D:\program\g\go\bin;' + $env:Path
```

## 使用 10808 代理

如果访问 `https://go.dev/dl/` 出现 `TLS handshake timeout`，优先设置 Go 官方中国镜像：

```powershell
[Environment]::SetEnvironmentVariable('G_MIRROR','official|https://golang.google.cn/dl/','User')
$env:G_MIRROR='official|https://golang.google.cn/dl/'
```

查询或安装 Go 版本时，如果仍然需要走 10808 代理：

```powershell
$env:HTTP_PROXY='http://127.0.0.1:10808'
$env:HTTPS_PROXY='http://127.0.0.1:10808'
```

验证远程版本列表：

```powershell
g ls-remote stable
```

本次已验证可返回：

```text
1.25.10
1.26.3
```

## 常用命令

查看可安装版本：

```powershell
g ls-remote stable
g ls-remote
```

安装指定 Go 版本：

```powershell
g install 1.26.3
```

本次已安装并切换：

```powershell
g install 1.25.0
```

验证结果：

```text
go version go1.25.0 windows/amd64
D:\program\g\go\bin\go.exe
```

切换当前 Go 版本：

```powershell
g use 1.26.3
```

查看已安装版本：

```powershell
g ls
```

查看当前 Go 版本：

```powershell
go version
```

卸载某个 Go 版本：

```powershell
g uninstall 1.26.3
```

## 注意事项

- 如果 `g use` 创建符号链接失败，请用管理员权限打开终端，或在 Windows 设置中开启开发者模式。
- 如果电脑上已有其他 Go 安装路径，确认 `where go` 的结果优先指向 `D:\program\g\go\bin\go.exe`。
- 如果 CMD 提示 `'g' is not recognized as an internal or external command`，确认用户 `Path` 中包含真实路径 `D:\program\g\bin`，而不是字面量 `%G_HOME%\bin`。
- 官方 `install.ps1` 使用了 PowerShell 7 的语法；本机默认 Windows PowerShell 5.x 不能直接运行，所以本次按脚本逻辑手动下载安装并设置环境变量。
