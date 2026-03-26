# Session 交互指南

本指南介绍如何使用 RogueRabbit 的 Session 会话管理系统。

## 什么是 Session？

Session 是**完整的会话对象**，用于管理用户与 LLM 的对话。与简单的 Conversation 不同，Session 提供完整的生命周期管理和持久化能力。

### Session vs Conversation

| 特性 | Conversation | Session |
|------|-------------|---------|
| 类型 | 简单封装 | 完整管理 |
| 元数据 | 无 | 有（ID、时间、状态） |
| 生命周期 | 无 | 完整管理（创建/暂停/恢复/关闭） |
| 持久化 | 不支持 | 支持多种存储后端 |
| 上下文管理 | 无 | 支持窗口控制 |

## 核心概念

### SessionStatus（会话状态）

```
ACTIVE <-> IDLE -> CLOSED
```

- **ACTIVE**: 活跃状态，可以正常对话
- **IDLE**: 暂停状态，可以通过 `get()` 恢复
- **CLOSED**: 关闭状态，不可恢复，但数据保留

### SessionMeta（会话元数据）

- `session_id`: 唯一标识（8位短ID）
- `created_at`: 创建时间
- `updated_at`: 最后更新时间
- `status`: 会话状态
- `metadata`: 自定义元数据

## 使用方式

### 1. 创建会话管理器

```python
from rogue_rabbit.adapters import GLMClient
from rogue_rabbit.core import SessionManager
from rogue_rabbit.runtime import MemorySessionStore

# 使用内存存储
store = MemorySessionStore()
llm = GLMClient()
manager = SessionManager(store=store, llm_client=llm)
```

### 2. 创建会话

```python
# 创建新会话
session = manager.create(
    system_prompt="你是一个有帮助的助手。",
    metadata={"user": "demo", "topic": "chat"}
)

print(f"会话 ID: {session.meta.session_id}")
```

### 3. 进行对话

```python
# 发送消息
response = manager.chat(session.meta.session_id, "你好")
print(f"AI: {response}")

# 继续对话
response = manager.chat(session.meta.session_id, "介绍一下你自己")
print(f"AI: {response}")
```

### 4. 管理会话生命周期

```python
# 暂停会话
manager.pause(session.meta.session_id)

# 恢复会话（自动恢复为 ACTIVE）
session = manager.get(session.meta.session_id)
response = manager.chat(session.meta.session_id, "继续")

# 关闭会话
manager.close(session.meta.session_id)

# 删除会话（数据将被清除）
manager.delete(session.meta.session_id)
```

### 5. 查看会话列表和历史

```python
# 列出所有会话
sessions = manager.list_sessions()
for meta in sessions:
    print(f"- {meta.session_id}: {meta.status.value}")

# 获取会话历史
history = manager.get_history(session.meta.session_id)
for msg in history:
    print(f"[{msg.role.value}]: {msg.content}")
```

## 存储后端

### MemorySessionStore

内存存储，适合测试和临时使用。

```python
from rogue_rabbit.runtime import MemorySessionStore

store = MemorySessionStore()
```

**特点：**
- 速度快
- 进程重启后数据丢失
- 适合测试和开发

### FileSessionStore

文件存储，适合单机部署和持久化。

```python
from pathlib import Path
from rogue_rabbit.runtime import FileSessionStore

store = FileSessionStore(Path("./sessions"))
```

**特点：**
- 数据持久化
- 文件格式可读（JSON）
- 适合单机部署

## 上下文窗口管理

长对话需要管理上下文窗口，避免超出 LLM token 限制。

### 配置

```python
from rogue_rabbit.core import (
    ContextWindowManager,
    ContextWindowConfig,
    TruncationStrategy
)

config = ContextWindowConfig(
    max_messages=20,              # 最大消息数
    strategy=TruncationStrategy.KEEP_LAST,  # 截断策略
    keep_first=2,                 # 保留前N条（用于 KEEP_FIRST_LAST）
    keep_last=10,                 # 保留后M条（用于 KEEP_FIRST_LAST）
)

context_manager = ContextWindowManager(config=config)
```

### 截断策略

| 策略 | 描述 |
|------|------|
| `KEEP_LAST` | 保留最近 N 条消息（默认） |
| `KEEP_FIRST` | 保留前 N 条消息 |
| `KEEP_FIRST_LAST` | 保留首尾消息 |
| `SUMMARIZE` | 生成摘要替换中间内容（需要 LLM） |

### 与 SessionManager 集成

```python
# 创建带上下文窗口管理的会话管理器
manager = SessionManager(
    store=store,
    llm_client=llm,
    context_window_manager=context_manager
)
```

## 会话序列化

Session 支持序列化和反序列化，便于备份和迁移。

### 导出

```python
session = manager.get(session_id)
data = session.to_dict()

# 保存为 JSON
import json
with open("session.json", "w") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

### 导入

```python
with open("session.json", "r") as f:
    data = json.load(f)

from rogue_rabbit.contracts import Session
session = Session.from_dict(data)
```

## 多会话管理

```python
# 创建多个不同主题的会话
python_session = manager.create(
    system_prompt="你是 Python 专家。",
    metadata={"topic": "python"}
)

history_session = manager.create(
    system_prompt="你是历史学家。",
    metadata={"topic": "history"}
)

# 在不同会话中对话
manager.chat(python_session.meta.session_id, "推荐一个 Web 框架")
manager.chat(history_session.meta.session_id, "介绍唐朝历史")

# 列出所有会话
for meta in manager.list_sessions():
    print(f"{meta.session_id}: {meta.metadata.get('topic')}")
```

## 最佳实践

1. **选择合适的存储后端**
   - 开发测试：MemorySessionStore
   - 生产部署：FileSessionStore 或自定义后端

2. **设置合理的上下文窗口**
   - 根据模型 token 限制设置 `max_messages`
   - 一般场景使用 `KEEP_LAST` 策略

3. **正确管理会话状态**
   - 临时离开使用 `pause()`
   - 彻底结束使用 `close()`
   - 清理数据使用 `delete()`

4. **使用 metadata 存储业务信息**
   - 用户 ID、会话主题等
   - 便于会话分类和查询

## 相关文件

- `contracts/session.py`: Session 数据结构定义
- `core/session_manager.py`: Session 管理器
- `core/context_window.py`: 上下文窗口管理
- `runtime/session_store.py`: 存储后端实现
- `experiments/10_session_basic.py`: 基础实验
- `experiments/11_session_persistence.py`: 持久化实验
- `notebooks/05_session_basics.ipynb`: 学习 notebook
