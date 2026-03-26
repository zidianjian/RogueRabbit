# Roadmap

## 版本历史

### v0.1.x - LLM 交互
- **0.1.0**: LLM 交互最小闭环
  - OpenAI/GLM 适配器
  - 消息和角色模型
  - 实验: 01-03

### v0.2.x - MCP 工具调用
- **0.2.0**: MCP 调用最小闭环
  - MCP 客户端（STDIO/HTTP）
  - Tool/Resource/Prompt 原语
  - ReAct Agent 核心
  - 实验: 04-06

- **0.2.1**: REST + MCP + LLM 集成
  - FastAPI REST 应用
  - MCP Server（封装 REST API）
  - 完整三层架构演示
  - 启动脚本
  - 实验: 07

### v0.3.x - Skill 调用
- **0.3.0**: Skill 调用最小闭环
  - Skill 协议定义
  - Skill 管理器
  - 内置 Skills (calculator, file-reader, code-review)
  - LLM + Skill 集成
  - 实验: 08-09

- **0.3.1**: 文档完善
  - 更新 roadmap
  - 添加 REST 集成指南
  - 添加 Skill 交互指南
  - 更新 notebooks

## Phase 1 计划

| 版本 | 功能 | 状态 |
|------|------|------|
| 0.1 | LLM 交互 | ✅ 完成 |
| 0.2 | MCP 调用 | ✅ 完成 |
| 0.3 | Skill 调用 | ✅ 完成 |
| 0.4 | Session 管理 | 📋 计划中 |
| 0.5 | Permissions | 📋 计划中 |
| 0.6 | Memory | 📋 计划中 |
| 0.7 | Logging | 📋 计划中 |
| 0.8 | Agent Team | 📋 计划中 |
| 0.9 | Integration | 📋 计划中 |

## Phase 2

- 提升可靠性、配置化与可持续使用能力

## Phase 3

- 提升生产约束、恢复能力与运维可读性
