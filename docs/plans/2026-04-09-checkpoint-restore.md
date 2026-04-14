# Checkpoint & Restore 设计方案 (v0.11.0)

**日期**: 2026-04-09
**状态**: 计划中
**前置版本**: v0.10.0 (Gateways)

---

## 背景

通过研究 OpenAI 和 Claude Code 的检查点/恢复机制，提炼核心设计原理，在 RogueRabbit 中实现最小化 Checkpoint 模块，学习"会话状态快照与回滚"的设计思想。

## 原理研究

### OpenAI 的三代演进

| 代际 | 机制 | 核心思想 |
|------|------|---------|
| Assistants API | Thread | 服务端持久化消息列表，append-only |
| Responses API | `previous_response_id` 链表 | 每个响应是节点，通过 ID 引用实现分支 |
| Conversations API | Conversation + Items | 持久容器 + 条目，支持 compaction |

**核心原理**: 链式引用 + 服务端状态。每个响应有唯一 ID，天然支持分支（从任意节点开始新链路 = 对话树）。

### Claude Code 的本地快照

| 维度 | 机制 |
|------|------|
| 文件状态 | 每次文件编辑前自动创建快照 |
| 对话上下文 | 会话历史存储在本地 |
| 恢复模式 | 代码回退 / 对话回退 / 两者同时（正交维度） |

**核心原理**: 自动快照 + 正交恢复。快照绑定到 user message UUID，文件状态和对话上下文独立恢复。

### 提炼的设计原则

1. **快照粒度** — 每次关键操作前保存状态
2. **链式引用** — 通过 ID 引用历史节点，支持分支
3. **正交维度** — 消息历史和运行状态可独立恢复
4. **自动触发** — 关键操作时自动创建检查点

## 最小实现设计

### 数据模型 (contracts/checkpoint.py)

```
CheckpointSnapshot
├── messages: MessageList       # 消息历史快照
├── metadata: dict              # 运行状态 (token数、工具调用等)
└── created_at: datetime

Checkpoint
├── checkpoint_id: str          # uuid[:8]
├── session_id: str             # 关联会话
├── parent_id: str | None       # 父检查点 (链式引用)
├── label: str                  # 可读标签
├── snapshot: CheckpointSnapshot
└── children: list[str]         # 子节点 (树结构)
```

### 存储协议 (contracts/checkpoint.py)

```
CheckpointStore (Protocol)
├── save(checkpoint) -> None
├── load(checkpoint_id) -> Checkpoint | None
├── list_by_session(session_id) -> list[Checkpoint]
├── get_latest(session_id) -> Checkpoint | None
└── delete(checkpoint_id) -> bool
```

### 管理器 (core/checkpoint_manager.py)

```
CheckpointManager
├── create(session, label?) -> Checkpoint
├── restore(checkpoint_id, session) -> Session
├── branch(checkpoint_id, session) -> Checkpoint
├── list(session_id) -> list[Checkpoint]
└── get_lineage(checkpoint_id) -> list[Checkpoint]
```

### 存储实现 (runtime/checkpoint_store.py)

- `InMemoryCheckpointStore`: 内存存储
- `FileCheckpointStore`: JSONL 文件持久化

## 文件变更

### 新增 (5个)
- `src/rogue_rabbit/contracts/checkpoint.py`
- `src/rogue_rabbit/core/checkpoint_manager.py`
- `src/rogue_rabbit/runtime/checkpoint_store.py`
- `experiments/19_checkpoint_basic.py`
- `notebooks/09_checkpoint_basics.ipynb`

### 修改 (3个)
- `src/rogue_rabbit/contracts/__init__.py`
- `src/rogue_rabbit/core/__init__.py`
- `src/rogue_rabbit/runtime/__init__.py`

## Notebook 大纲 (09_checkpoint_basics.ipynb)

1. 什么是检查点？— 对比 OpenAI 链式引用 vs Claude Code 本地快照
2. 创建检查点 — 手动创建会话快照
3. 链式检查点 — 父子关系，展示检查点树
4. 恢复检查点 — 回滚会话到历史状态
5. 分支检查点 — 从历史节点创建新分支
6. 文件持久化 — FileCheckpointStore 的使用
7. 与 ReAct Agent 集成 — 工具调用前后自动创建检查点

## 验证

1. 运行 `experiments/19_checkpoint_basic.py`
2. 运行 notebook 各 cell
3. 验证链/树结构（parent-child 关系）
4. 验证恢复后 Session.messages 回到快照状态
5. 验证分支功能
6. 验证 FileCheckpointStore 持久化和重新加载
