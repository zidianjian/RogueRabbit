# RogueRabbit

RogueRabbit 是一个用 Python 构建的 agent 学习与工程化项目。

当前仓库采用三阶段路线：

- 阶段一：以 0.x 版本逐项学习 agent 常见能力
- 阶段二：将已有能力扩展到可用程度
- 阶段三：将已有能力优化到生产可用程度

当前骨架优先服务于阶段一，并参考 Harness Engineering 的思路组织仓库结构、文档结构与验证方式。

## 当前目录

- `docs/`：设计、架构、阶段路线、能力说明与模板
- `src/rogue_rabbit/`：Python 包骨架
- `tests/`：最小验证

## 版本进度

| 版本 | 功能 | 状态 |
|------|------|------|
| 0.1 | LLM 交互最小闭环 | ✅ 完成 |
| 0.2 | MCP 调用最小闭环 | ✅ 完成 |
| 0.2.1 | REST + MCP Server + LLM 集成 | ✅ 完成 |
| 0.3 | Skill 调用最小闭环 | ✅ 完成 |
| 0.4 | Session 会话管理 | ✅ 完成 |
| 0.5 | Memory 记忆管理 | ✅ 完成 |
| 0.6 | Permissions 权限控制 | ✅ 完成 |

## 快速开始

```bash
# 安装依赖
pip install -e .

# 运行实验
python -m rogue_rabbit.experiments.01_hello_llm
python -m rogue_rabbit.experiments.06_mcp_real
python -m rogue_rabbit.experiments.07_rest_mcp_llm
python -m rogue_rabbit.experiments.08_skill_basic
python -m rogue_rabbit.experiments.10_session_basic
python -m rogue_rabbit.experiments.11_session_persistence
python -m rogue_rabbit.experiments.12_memory_basic
python -m rogue_rabbit.experiments.13_memory_with_session
python -m rogue_rabbit.experiments.15_permission_basic
python -m rogue_rabbit.experiments.16_tool_permission
python -m rogue_rabbit.experiments.17_resource_permission
```

## 实验列表

### LLM 基础 (v0.1)
- `01_hello_llm`: 最简单的 LLM 调用
- `02_conversation`: 多轮对话管理
- `03_system_prompt`: 系统提示词的作用

### MCP 工具调用 (v0.2)
- `04_mcp_basic`: 基础 MCP 调用
- `05_mcp_with_llm`: LLM + MCP 组合
- `06_mcp_real`: 真实 LLM + 真实 MCP

### REST + MCP + LLM (v0.2.1)
- `07_rest_mcp_llm`: REST API + MCP Server + LLM 完整演示

### Skill 调用 (v0.3)
- `08_skill_basic`: Skill 基础调用
- `09_skill_with_llm`: LLM + Skill 集成

### Session 会话管理 (v0.4)
- `10_session_basic`: 基础会话管理
- `11_session_persistence`: 会话持久化

### Memory 记忆管理 (v0.5)
- `12_memory_basic`: 基础记忆操作
- `13_memory_with_session`: 记忆与会话集成

### Permissions 权限控制 (v0.6)
- `15_permission_basic`: 基础权限检查
- `16_tool_permission`: 工具调用权限
- `17_resource_permission`: 资源访问控制

## 架构

```
src/rogue_rabbit/
├── adapters/       # 外部服务适配器（LLM, MCP）
├── apps/           # 应用入口（CLI, REST）
│   └── rest/       # FastAPI REST 应用
├── contracts/      # 核心接口定义（Message, Session, Skill, MCP, Permission）
├── core/           # 核心功能（ReAct Agent, Skill Manager, Session Manager, Authorizer）
├── runtime/        # 运行时组件（Session Store, Policy Store）
├── servers/        # MCP Server 实现
├── skills/         # 内置 Skills
│   ├── calculator/ # 数学计算
│   ├── file_reader/# 文件读取
│   └── code_review/# 代码审查
└── experiments/    # 学习实验
```

## Skill vs MCP vs Session

| 特性 | MCP | Skill | Session | Permission |
|------|-----|-------|---------|------------|
| 类型 | 工具/函数 | 提示词扩展 | 会话管理 | 权限控制 |
| 输入 | 结构化参数 | 自然语言 | 对话消息 | 访问请求 |
| 输出 | 结构化结果 | 指导性内容 | 对话历史 | 允许/拒绝 |
| 调用方式 | Tool Call | 上下文注入 | 生命周期管理 | 授权检查 |
| 适合场景 | 明确操作 | 灵活任务 | 多轮对话 | 安全边界 |

## 启动脚本

```bash
# 启动 REST API 服务
start_rest.bat

# 启动 MCP Server（需要 REST API 先运行）
start_mcp_server.bat
```
