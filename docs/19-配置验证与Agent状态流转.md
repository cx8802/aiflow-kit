# 配置验证与 Agent 状态流转

本文说明 `aiflow-kit` 新增的三个基础能力：

- 项目配置查看、修改、校验
- 自动推断验证命令
- 多 Agent 任务状态流转

## 配置命令

查看完整合并配置：

```bat
aiflow config show
```

查看单个配置项：

```bat
aiflow config show commands.test
```

修改配置项：

```bat
aiflow config set commands.test "python -m unittest discover -s tests"
aiflow config set frontend.enabled true
aiflow config set context.include "[\"README.md\", \"src\", \"tests\"]"
```

校验配置：

```bat
aiflow config check
```

`config set` 会写入项目级 `.aiflow/config.toml`，不会写用户全局配置。

## 自动验证

如果 `.aiflow/config.toml` 里已经配置了命令，继续使用：

```bat
aiflow verify
```

如果还没配置，可以自动推断：

```bat
aiflow verify --auto --dry-run
```

当前自动识别规则：

| 项目文件 | 推断命令 |
| --- | --- |
| `tests/` 或 `pyproject.toml` | `python -m unittest discover -s tests` |
| `pytest.ini` 或 `conftest.py` | `python -m pytest` |
| `package.json` | `npm.cmd test` |
| `go.mod` | `go test ./...` |
| `pom.xml` | `mvn test` |

多个生态同时存在时，会用 `&&` 串联测试命令。`--auto` 不会自动修改 `.aiflow/config.toml`，只是当前这次验证使用。

## Agent 状态流转

先生成任务：

```bat
aiflow agents plan "实现订单导出"
```

查看任务：

```bat
aiflow agents status
```

开始任务：

```bat
aiflow agents start 001-explore "reading files"
```

完成任务：

```bat
aiflow agents done 001-explore
```

阻塞任务：

```bat
aiflow agents block 002-implement "waiting for API decision"
```

这些命令会更新：

```text
.aiflow/agents/status.md
.aiflow/agents/tasks/<task>.md
```

`.aiflow/agents/` 是项目运行态目录，已加入 `.gitignore`，不提交到远程。

## 推荐流程

```bat
aiflow config check
aiflow verify --auto --dry-run
aiflow agents plan "目标"
aiflow agents start 001-explore
aiflow agents done 001-explore
aiflow verify --auto
```

## 边界

- 配置是项目级的。
- Agent 状态是项目运行态的。
- 自动验证不会修改配置。
- 不写用户全局环境变量。
- 不把数据库、token、内网地址写入全局 Skills。
