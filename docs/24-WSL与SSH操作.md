# WSL 与 SSH 操作

`aiflow` 提供项目级 WSL/SSH 辅助命令，方便 AI Agent 在明确授权的边界内调用本机 WSL 或远程主机。

## WSL

检查本机是否可用：

```powershell
aiflow wsl doctor
```

列出发行版：

```powershell
aiflow wsl list --verbose
```

执行命令：

```powershell
aiflow wsl run --distro Ubuntu --user dev --cwd /repo --dry-run uname -a
aiflow wsl run --distro Ubuntu --user dev --cwd /repo uname -a
```

转换路径：

```powershell
aiflow wsl path --to-wsl "C:\Users\demo\project"
aiflow wsl path --to-win /home/demo/project
```

## SSH

SSH 配置分为两个文件：

- `.aiflow/ssh.toml`：可提交的 profile 元数据，例如 host、user、port、环境变量名和 OpenSSH option。
- `.aiflow/ssh.local.toml`：本机私有配置，例如 private key 路径、密码或 passphrase 元数据。

添加 profile：

```powershell
aiflow ssh add dev --host example.test --user deploy --port 2222 --key-path-env DEPLOY_KEY
```

如果要写入本机 key 路径，必须显式使用本地 secret 文件：

```powershell
aiflow ssh add dev --host example.test --user deploy --key-path "C:\Users\demo\.ssh\id_ed25519" --secret-local
```

查看与执行：

```powershell
aiflow ssh list
aiflow ssh show dev
aiflow ssh run dev --dry-run uname -a
aiflow ssh run dev uname -a
```

`ssh run` 使用系统 OpenSSH 客户端，不托管交互式密码输入；推荐使用 SSH agent、key 文件或环境变量指向本机凭据。
