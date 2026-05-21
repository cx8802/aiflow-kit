# pyenv 安装使用教程

> 说明：Windows 上通常使用 `pyenv-win`，Linux / macOS 上使用原版 `pyenv`。本文以 Windows 为主，同时补充 Linux / macOS 的安装方式。

## 一、pyenv 是什么

`pyenv` 是一个 Python 多版本管理工具，可以在同一台电脑上安装和切换多个 Python 版本。

常见用途：

- 同时安装 Python 3.8、3.10、3.12 等版本
- 全局指定默认 Python 版本
- 为某个项目单独指定 Python 版本
- 避免系统 Python、Anaconda、项目 Python 之间互相冲突

Windows 对应工具：

```text
pyenv-win
```

Linux / macOS 对应工具：

```text
pyenv
```

## 二、Windows 安装 pyenv-win

### 1. 安装方式一：使用 PowerShell 安装

打开 PowerShell，执行：

```powershell
Invoke-WebRequest -UseBasicParsing -Uri "https://pyenv.run" -OutFile "./pyenv-install.ps1"
```

如果上面的方式不可用，推荐直接使用 Git 克隆安装。

### 2. 安装方式二：使用 Git 克隆，推荐

先安装 Git，然后执行：

```powershell
New-Item -ItemType Directory -Force "D:\program"
git clone https://github.com/pyenv-win/pyenv-win.git "D:\program\pyenv-win"
```

安装完成后的 pyenv-win 工具目录是：

```text
D:\program\pyenv-win\pyenv-win
```

## 三、配置环境变量

### 1. 配置 PYENV 相关变量

如果安装在用户目录：

```text
PYENV = C:\Users\你的用户名\.pyenv\pyenv-win
PYENV_HOME = C:\Users\你的用户名\.pyenv\pyenv-win
PYENV_ROOT = C:\Users\你的用户名\.pyenv\pyenv-win
```

如果安装在 D 盘：

```text
PYENV = D:\program\pyenv-win\pyenv-win
PYENV_HOME = D:\program\pyenv-win\pyenv-win
PYENV_ROOT = D:\program\pyenv-win\pyenv-win
```

### 2. 配置 Path

在用户变量 `Path` 中添加：

```text
%PYENV%\bin
%PYENV%\shims
```

也可以直接写绝对路径，例如：

```text
D:\program\pyenv-win\pyenv-win\bin
D:\program\pyenv-win\pyenv-win\shims
```

注意：`pyenv` 的路径要放在其他 Python 路径前面。

推荐顺序：

```text
pyenv-win\bin
pyenv-win\shims
Anaconda
其他 Python
WindowsApps
```

配置完成后，关闭当前终端，重新打开 CMD 或 PowerShell。

## 四、验证 pyenv 是否安装成功

执行：

```powershell
pyenv --version
```

如果能看到版本号，说明安装成功。

再检查命令位置：

```powershell
where pyenv
```

正常应该指向：

```text
D:\program\pyenv-win\pyenv-win\bin\pyenv.bat
```

或者：

```text
C:\Users\你的用户名\.pyenv\pyenv-win\bin\pyenv.bat
```

## 五、安装 Python 版本

### 1. 查看可安装版本

```powershell
pyenv install -l
```

输出很多版本，例如：

```text
3.8.10
3.9.13
3.10.11
3.11.9
3.12.10
```

### 2. 安装指定版本

必须写完整版本号：

```powershell
pyenv install 3.12.10
```

错误写法：

```powershell
pyenv install 12
```

这种写法会报错：

```text
definition not found: 12
```

### 3. 查看已安装版本

```powershell
pyenv versions
```

示例：

```text
  3.10.11
* 3.12.10
```

星号表示当前正在使用的版本。

## 六、切换 Python 版本

### 1. 全局切换

设置整台电脑默认使用 Python 3.12.10：

```powershell
pyenv global 3.12.10
```

验证：

```powershell
python --version
pyenv version
pyenv which python
```

正确结果类似：

```text
Python 3.12.10
3.12.10
D:\program\pyenv-win\pyenv-win\versions\3.12.10\python.exe
```

### 2. 项目级切换

进入项目目录：

```powershell
cd D:\code\my-python-project
```

为当前项目指定 Python 版本：

```powershell
pyenv local 3.10.11
```

执行后，项目目录下会生成一个文件：

```text
.python-version
```

以后只要进入这个项目目录，`pyenv` 就会自动使用指定版本。

### 3. 临时切换

只在当前终端临时使用某个版本：

```powershell
pyenv shell 3.11.9
```

关闭终端后失效。

## 七、配合虚拟环境使用

`pyenv` 负责管理 Python 解释器版本，`venv` 负责隔离项目依赖。

推荐流程：

```powershell
cd D:\code\my-python-project
pyenv local 3.12.10
python -m venv .venv
```

激活虚拟环境：

```powershell
.\.venv\Scripts\activate
```

安装依赖：

```powershell
pip install requests
```

退出虚拟环境：

```powershell
deactivate
```

检查当前 Python 和 pip：

```powershell
where python
where pip
python --version
pip --version
```

## 八、配置 pip 国内镜像

如果下载 Python 包比较慢，可以配置 pip 镜像。

### 1. 临时使用清华源

```powershell
pip install requests -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 2. 永久配置清华源

```powershell
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

查看配置：

```powershell
pip config list
```

常用镜像：

```text
清华源：https://pypi.tuna.tsinghua.edu.cn/simple
阿里源：https://mirrors.aliyun.com/pypi/simple
腾讯源：https://mirrors.cloud.tencent.com/pypi/simple
```

## 九、常用命令速查

```powershell
# 查看 pyenv 版本
pyenv --version

# 查看可安装的 Python 版本
pyenv install -l

# 安装 Python
pyenv install 3.12.10

# 卸载 Python
pyenv uninstall 3.12.10

# 查看已安装版本
pyenv versions

# 设置全局版本
pyenv global 3.12.10

# 设置项目版本
pyenv local 3.12.10

# 查看当前版本
pyenv version

# 查看 python 实际路径
pyenv which python

# 刷新 shims
pyenv rehash
```

## 十、常见问题排查

### 1. pyenv 命令不存在

现象：

```text
'pyenv' 不是内部或外部命令，也不是可运行的程序
```

原因：

```text
Path 没有配置 pyenv-win\bin
```

解决：

确认 Path 中存在：

```text
D:\program\pyenv-win\pyenv-win\bin
D:\program\pyenv-win\pyenv-win\shims
```

然后重新打开终端。

### 2. python 版本没有切换成功

现象：

```powershell
pyenv global 3.12.10
python --version
```

结果还是旧版本。

原因通常是 Path 顺序错误。

检查：

```powershell
where python
```

如果排在第一位的是：

```text
C:\Users\你的用户名\AppData\Local\Microsoft\WindowsApps\python.exe
```

或者某个旧 Python / Anaconda 路径，说明它抢在了 pyenv 前面。

解决：

- 把 `pyenv-win\bin` 和 `pyenv-win\shims` 放到 Path 最前面
- 关闭 Windows 的 Python 应用执行别名

关闭位置：

```text
设置 -> 应用 -> 高级应用设置 -> 应用执行别名
```

关闭：

```text
python.exe
python3.exe
```

### 3. Found WindowsApps before pyenv in PATH

报错类似：

```text
Found C:\Users\xxx\AppData\Local\Microsoft\WindowsApps\python.exe version before pyenv in PATH
```

原因：

```text
WindowsApps 中的 python.exe 优先级高于 pyenv 的 shims
```

解决：

把下面路径移动到 pyenv 后面，或者从用户 Path 中删除：

```text
C:\Users\你的用户名\AppData\Local\Microsoft\WindowsApps
```

同时关闭应用执行别名中的：

```text
python.exe
python3.exe
```

### 4. 安装 Python 失败

可以尝试：

```powershell
pyenv update
pyenv install -l
pyenv install 3.12.10
```

如果网络下载失败，可以手动下载对应 Python 安装包，然后放到 pyenv-win 的缓存目录。一般目录是：

```text
%PYENV%\install_cache
```

### 5. pip 不是当前 Python 的 pip

检查：

```powershell
where pip
python -m pip --version
```

更稳妥的写法是：

```powershell
python -m pip install requests
```

这样可以确保 pip 属于当前 `python`。

## 十一、Linux / macOS 安装 pyenv

Linux / macOS 可以使用官方安装脚本：

```bash
curl https://pyenv.run | bash
```

安装后，根据终端类型，把下面内容加入 `~/.bashrc`、`~/.zshrc` 或 `~/.profile`：

```bash
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
```

重新加载配置：

```bash
source ~/.zshrc
```

或者：

```bash
source ~/.bashrc
```

验证：

```bash
pyenv --version
```

安装 Python：

```bash
pyenv install 3.12.10
pyenv global 3.12.10
python --version
```

## 十二、推荐工作流

新建 Python 项目时，建议按下面流程：

```powershell
mkdir D:\code\demo
cd D:\code\demo

pyenv install 3.12.10
pyenv local 3.12.10

python -m venv .venv
.\.venv\Scripts\activate

python -m pip install --upgrade pip
pip install requests
pip freeze > requirements.txt
```

以后重新进入项目：

```powershell
cd D:\code\demo
.\.venv\Scripts\activate
python --version
```

## 十三、一句话总结

`pyenv` 管 Python 版本，`venv` 管项目依赖。  
Windows 上最关键的是 Path 顺序：`pyenv-win\bin` 和 `pyenv-win\shims` 必须排在其他 Python 路径前面。
