# Roadmap

## 学习路径设计思路

**核心原则：**
1. 每个版本只聚焦一个主题
2. 按依赖关系排序，先学基础再学高级
3. 强调接口清晰与最小闭环

**依赖关系：**
```
LLM 交互 → MCP 工具 → Skill 知识 → Session 状态 → Memory 记忆
                                                    ↓
                        Logging ← Permissions ←────┘
                              ↓
                           Hooks
                              ↓
                         Commands
                              ↓
                         Gateways
                              ↓
                      Checkpoint & Restore
                              ↓
                         Planning
                              ↓
                         Agent Team
                              ↓
                         Integration
```

---

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

### v0.4.x - Session 会话管理
- **0.4.0**: Session 管理最小闭环
  - Session 协议定义（Session, SessionMeta, SessionStatus）
  - SessionManager 会话生命周期管理
  - ContextWindowManager 上下文窗口控制
  - 存储后端（MemorySessionStore, FileSessionStore）
  - 实验: 10-11

### v0.5.x - Memory 长期记忆
- **0.5.0**: Memory 记忆管理最小闭环
  - Memory 协议定义（MemoryItem, MemoryMeta, Memory）
  - MemoryManager 记忆管理器
  - 记忆检索（关键词匹配、分类过滤、重要性排序）
  - 存储后端（InMemoryStore, FileMemoryStore）
  - Session + Memory 集成
  - 实验: 12-13

---

## Phase 1 计划

### 状态管理层

| 版本 | 功能 | 描述 | 状态 |
|------|------|------|------|
| **0.4** | **Session 管理** | 会话生命周期、对话历史、上下文控制 | ✅ 已完成 |
| **0.5** | **Memory** | 长期记忆、知识存储、检索机制 | ✅ 已完成 |
| **0.6** | **Permissions** | 工具权限、资源访问控制、安全边界 | ✅ 已完成 |

### 安全与可观测层

| 版本 | 功能 | 描述 | 状态 |
|------|------|------|------|
| **0.6** | **Permissions** | 工具权限、资源访问控制、安全边界 | ✅ 已完成 |
| **0.7** | **Logging** | 结构化日志、追踪、性能监控 | ✅ 已完成 |

### 扩展与交互层

| 版本 | 功能 | 描述 | 状态 |
|------|------|------|------|
| **0.8** | **Hooks** | 生命周期钩子、事件拦截、行为扩展 | 📋 计划中 |
| **0.9** | **Commands** | 命令路由、分发、用户交互模式 | 📋 计划中 |
| **0.10** | **Gateways** | 协议适配、路由、多通道接入 | 📋 计划中 |

### 协作与集成层

| 版本 | 功能 | 描述 | 状态 |
|------|------|------|------|
| **0.11** | **Checkpoint** | 会话快照、链式检查点、状态恢复与分支 | 📋 计划中 |
| **0.12** | **Planning** | 任务分解、计划生成、执行与重规划 | 📋 计划中 |
| **0.13** | **Agent Team** | 多 Agent 通信、任务分解、协作模式 | 📋 计划中 |
| **0.14** | **Integration** | 配置管理、错误处理、完整应用 | 📋 计划中 |

---

## 各版本详细规划

### 0.4 Session 管理
```
学习目标:
- 理解会话生命周期
- 掌握对话历史管理
- 学会上下文窗口控制

核心概念:
- Session: 会话对象，包含状态和历史
- SessionManager: 创建、存储、恢复会话
- ContextWindow: 上下文窗口管理（截断、摘要）

实验:
- 10_session_basic: 基础会话管理
- 11_session_persistence: 会话持久化
```

### 0.5 Memory
```
学习目标:
- 理解短期记忆 vs 长期记忆
- 掌握记忆存储和检索
- 学会记忆总结和遗忘

核心概念:
- MemoryItem: 单条记忆（内容、时间、重要性、分类）
- Memory: 记忆空间（按 user_id 组织）
- MemoryManager: 记忆管理器
- MemoryStore: 存储后端（InMemoryStore, FileMemoryStore）

实验:
- 12_memory_basic: 基础记忆操作
- 13_memory_with_session: 记忆与会话集成
```

### 0.6 Permissions
```
学习目标:
- 理解 Agent 安全边界
- 掌握权限控制机制（DENY 优先、默认拒绝）
- 学会用户授权流程和 RBAC

核心概念:
- Permission: 权限规则（action + resource + effect）
- Policy: 策略集合，绑定角色
- AccessRequest/AccessResult: 授权检查
- Authorizer: 授权管理器
- PolicyStore: 存储后端（InMemoryPolicyStore, FilePolicyStore）

实验:
- 15_permission_basic: 基础权限检查
- 16_tool_permission: 工具调用权限
- 17_resource_permission: 资源访问控制
```

### 0.7 Logging
```
学习目标:
- 理解可观测性三支柱
- 掌握结构化日志
- 学会追踪和调试

核心概念:
- Logger: 结构化日志
- Tracer: 请求追踪
- Metrics: 性能指标

实验:
- 18_logging_basic: 结构化日志
- 19_tracing: 请求追踪
- 20_debugging: 调试支持
```

### 0.8 Hooks
```
学习目标:
- 理解 Agent 生命周期事件
- 掌握钩子机制（前置/后置拦截）
- 学会通过钩子扩展 Agent 行为

核心概念:
- Hook: 钩子函数（事件类型 + 回调）
- HookManager: 钩子管理器（注册/触发/卸载）
- HookEvent: 生命周期事件（LLM调用前后、工具调用前后、错误处理等）
- HookContext: 钩子上下文（传递数据和状态）

设计原则（提炼自 Claude Code Hooks 和 FastAPI Middleware）:
- 洋葱模型: 请求穿过多层钩子，每层可拦截或修改
- 正交扩展: 不修改核心逻辑即可添加行为
- 顺序控制: 钩子按优先级执行，支持短路

实验:
- 21_hook_basic: 基础钩子注册与触发
- 22_hook_lifecycle: Agent 生命周期钩子
- 23_hook_chain: 钩子链与优先级
```

### 0.9 Commands
```
学习目标:
- 理解用户与 Agent 的结构化交互模式
- 掌握命令路由与分发
- 学会命令解析和参数处理

核心概念:
- Command: 命令定义（名称、描述、参数、处理函数）
- CommandRegistry: 命令注册表（注册/查找/列表）
- CommandDispatcher: 命令分发器（解析/路由/执行）
- CommandContext: 命令上下文（参数、会话、Agent 状态）

设计原则（提炼自 Claude Code Slash Commands 和 CLI 框架）:
- 统一入口: 所有用户交互通过命令系统
- 可发现性: 命令自描述，支持帮助和补全
- 可组合: 命令可嵌套和组合

实验:
- 24_command_basic: 基础命令定义与分发
- 25_command_with_agent: 命令与 Agent 集成
- 26_command_advanced: 参数解析、子命令、帮助系统
```

### 0.10 Gateways
```
学习目标:
- 理解 Agent 的外部接口层
- 掌握协议适配（HTTP、WebSocket、CLI）
- 学会路由和中间件模式

核心概念:
- Gateway: 网关（协议 + 路由 + 中间件）
- Route: 路由规则（路径 + 方法 + 处理函数）
- Middleware: 中间件（请求/响应拦截）
- GatewayBuilder: 网关构建器（配置式构建）

设计原则（提炼自 API Gateway 和 MCP Server）:
- 协议无关: 核心逻辑不依赖具体协议
- 中间件栈: 请求穿过多层中间件处理
- 统一错误: 不同协议的错误统一处理

实验:
- 27_gateway_http: HTTP 网关（REST API）
- 28_gateway_websocket: WebSocket 网关（实时交互）
- 29_gateway_cli: CLI 网关（命令行交互）
```

### 0.11 Checkpoint & Restore
```
学习目标:
- 理解 OpenAI 的链式引用（previous_response_id）和 Claude Code 的本地快照原理
- 掌握检查点的创建、恢复和分支
- 学会会话状态快照与回滚

核心概念:
- Checkpoint: 会话状态快照（消息历史 + 元数据）
- CheckpointManager: 检查点管理器（创建/恢复/分支/谱系查询）
- CheckpointStore: 存储后端（InMemoryCheckpointStore, FileCheckpointStore）
- 链式引用: parent_id 支持检查点树和分支
- 正交恢复: 消息历史和运行状态独立管理

设计原则（提炼自 OpenAI 和 Claude Code）:
- 快照粒度: 每次关键操作前保存状态
- 链式引用: 通过 ID 引用历史节点，支持分支
- 自动触发: 关键操作时自动创建检查点

实验:
- 30_checkpoint_basic: 检查点创建、恢复与分支
```

### 0.12 Planning
```
学习目标:
- 理解 Agent 规划的核心模式（Plan-and-Execute、ReWOO、Reflexion）
- 掌握任务分解与计划表示
- 学会执行循环与动态重规划
- 理解 Planning 与 ReAct 的混合模式

核心概念:
- Plan: 执行计划（目标 + 步骤列表）
- PlanStep: 计划步骤（描述、状态、结果）
- Planner: 计划生成（LLM 驱动的任务分解）
- PlanExecutor: 按步骤执行，收集观察结果
- Replanner: 基于观察结果动态调整计划

设计原则（提炼自 Claude Code Plan Mode 和 LangGraph）:
- 先规划后执行: 复杂任务先生成完整计划
- 动态调整: 执行中可根据观察结果重规划
- 混合模式: 顶层 Plan-and-Execute，底层步骤可用 ReAct
- 计划持久化: 结合 v0.11 Checkpoint 保存计划状态

实验:
- 31_plan_basic: Plan-and-Execute 基础模式
- 32_plan_with_react: Plan + ReAct 混合模式
- 33_plan_replanning: 动态重规划
- 34_plan_checkpoint: 计划状态持久化（结合 Checkpoint）
```

### 0.13 Agent Team
```
学习目标:
- 理解多 Agent 协作模式
- 掌握任务分解和分配
- 学会结果汇总

核心概念:
- Team: Agent 团队
- Role: Agent 角色（规划者、执行者、审核者）
- Communication: Agent 间通信
- Orchestrator: 任务编排

实验:
- 35_team_basic: 基础多 Agent
- 36_task_decomposition: 任务分解
- 37_collaboration: 协作模式
```

### 0.14 Integration
```
学习目标:
- 理解完整 Agent 应用架构
- 掌握配置管理
- 学会错误处理和恢复

核心概念:
- Config: 配置管理
- ErrorHandler: 错误处理
- HealthCheck: 健康检查
- AgentApp: 完整应用

实验:
- 38_config: 配置管理
- 39_error_handling: 错误处理
- 40_complete_agent: 完整 Agent 应用
```

---

## Phase 2

- 提升可靠性、配置化与可持续使用能力
- 生产级错误处理
- 性能优化

## Phase 3

- 提升生产约束、恢复能力与运维可读性
- 分布式部署
- 高可用设计
