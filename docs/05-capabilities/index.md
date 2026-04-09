# Capabilities

本目录用于记录每项能力的目标、边界、阶段目标与验证方式。

## 能力清单

| 能力 | 版本 | 状态 | 描述 |
|------|------|------|------|
| **LLM** | v0.1.x | ✅ 已完成 | LLM 交互基础，支持 OpenAI/GLM |
| **MCP** | v0.2.x | ✅ 已完成 | MCP 工具调用，支持 STDIO/HTTP |
| **Skill** | v0.3.x | ✅ 已完成 | Skill 知识包，上下文注入 |
| **Session** | v0.4.x | ✅ 已完成 | 会话管理，生命周期，持久化 |
| **Memory** | v0.5.x | ✅ 已完成 | 长期记忆，知识存储，检索 |
| **Permissions** | v0.6.x | ✅ 已完成 | 权限控制，安全边界 |
| **Logging** | v0.7.x | ✅ 已完成 | 结构化日志，追踪 |
| **Checkpoint** | v0.8.x | 📋 计划中 | 会话快照、链式检查点、状态恢复与分支 |
| **Agent Team** | v0.9.x | 📋 计划中 | 多 Agent 协作 |

## 能力详情

### LLM (v0.1.x)

LLM 交互基础能力。

**核心组件：**
- `contracts/messages.py`: 消息模型（Message, Role）
- `contracts/llm.py`: LLM 客户端协议
- `adapters/openai_client.py`: OpenAI 适配器
- `adapters/glm_client.py`: GLM 适配器

**学习资源：**
- `experiments/01_hello_llm.py`
- `experiments/02_conversation.py`
- `experiments/03_system_prompt.py`
- `notebooks/01_llm_basics.ipynb`

---

### MCP (v0.2.x)

MCP 工具调用能力。

**核心组件：**
- `contracts/mcp.py`: MCP 协议定义
- `adapters/mcp_client.py`: MCP 客户端
- `core/react_agent.py`: ReAct Agent

**学习资源：**
- `experiments/04_mcp_basic.py`
- `experiments/05_mcp_with_llm.py`
- `experiments/06_mcp_real.py`
- `experiments/07_rest_mcp_llm.py`
- `notebooks/02_mcp_basics.ipynb`
- `notebooks/03_rest_mcp_llm.ipynb`
- `docs/07-guides/mcp-interaction-guide.md`

---

### Skill (v0.3.x)

Skill 知识包能力。

**核心组件：**
- `contracts/skill.py`: Skill 协议定义
- `core/skill_manager.py`: Skill 管理器
- `skills/`: 内置 Skills 目录

**学习资源：**
- `experiments/08_skill_basic.py`
- `experiments/09_skill_with_llm.py`
- `notebooks/04_skill_basics.ipynb`
- `docs/07-guides/skill-interaction-guide.md`

---

### Session (v0.4.x)

会话管理能力。

**核心组件：**
- `contracts/session.py`: Session 协议定义
- `core/session_manager.py`: 会话管理器
- `core/context_window.py`: 上下文窗口管理
- `runtime/session_store.py`: 存储后端

**学习资源：**
- `experiments/10_session_basic.py`
- `experiments/11_session_persistence.py`
- `notebooks/05_session_basics.ipynb`
- `docs/07-guides/session-interaction-guide.md`

**关键特性：**
- 会话生命周期管理（创建/暂停/恢复/关闭）
- 多种存储后端（内存/文件）
- 上下文窗口控制（多种截断策略）
- 会话序列化和恢复

---

### Memory (v0.5.x)

长期记忆能力。

**核心组件：**
- `contracts/memory.py`: Memory 协议定义（MemoryItem, Memory, MemoryStore）
- `core/memory_manager.py`: Memory 管理器
- `runtime/memory_store.py`: 存储后端（InMemoryStore, FileMemoryStore）

**学习资源：**
- `experiments/12_memory_basic.py`
- `experiments/13_memory_with_session.py`
- `notebooks/06_memory_basics.ipynb`
- `docs/07-guides/memory-interaction-guide.md`

**关键特性：**
- 记忆分类和重要性评分
- 关键词搜索和过滤
- LLM 记忆摘要生成
- 与 Session 集成（记忆注入上下文）

---

## 能力依赖关系

```
LLM 交互 → MCP 工具 → Skill 知识 → Session 状态 → Memory 记忆
                                                    ↓
                        Logging ← Permissions ←────┘
                              ↓
                      Checkpoint & Restore
                              ↓
                         Agent Team
                              ↓
                         Integration
```

---

### Checkpoint (v0.8.x)

会话检查点与恢复能力。

**核心组件：**
- `contracts/checkpoint.py`: Checkpoint 协议定义（Checkpoint, CheckpointSnapshot, CheckpointStore）
- `core/checkpoint_manager.py`: 检查点管理器
- `runtime/checkpoint_store.py`: 存储后端（InMemoryCheckpointStore, FileCheckpointStore）

**学习资源：**
- `experiments/19_checkpoint_basic.py`
- `notebooks/09_checkpoint_basics.ipynb`

**关键特性：**
- 会话状态快照（消息历史 + 元数据）
- 链式检查点（parent_id 支持分支，源于 OpenAI previous_response_id 思想）
- 状态恢复与回滚（源于 Claude Code 本地快照思想）
- 检查点谱系查询（get_lineage 追溯完整路径）
- 文件持久化（JSONL 格式）

## 扩展指南

添加新能力时，请参考：
1. `docs/templates/capability-spec.md` - 能力规范模板
2. `docs/07-guides/add-capability.md` - 添加能力指南
