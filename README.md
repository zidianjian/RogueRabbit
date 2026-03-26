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
| 0.3 | Skill 调用最小闭环 | 📋 计划中 |

## 快速开始

```bash
# 安装依赖
pip install -e .

# 运行实验
python -m rogue_rabbit.experiments.01_hello_llm
python -m rogue_rabbit.experiments.06_mcp_real
python -m rogue_rabbit.experiments.07_rest_mcp_llm
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

## 架构

```
src/rogue_rabbit/
├── adapters/       # 外部服务适配器（LLM, MCP）
├── apps/           # 应用入口（CLI, REST）
│   └── rest/       # FastAPI REST 应用
├── contracts/      # 核心接口定义
├── core/           # 核心功能（ReAct Agent）
├── servers/        # MCP Server 实现
└── experiments/    # 学习实验
```
