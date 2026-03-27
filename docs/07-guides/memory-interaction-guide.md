# Memory 交互指南

本指南介绍如何使用 RogueRabbit 的 Memory 长期记忆系统。

## 什么是 Memory？

Memory 是**长期知识存储**，用于跨会话保存和检索信息。与 Session 的短期对话历史不同，Memory 存储的是提取后的关键知识。

### Session vs Memory

| 特性 | Session | Memory |
|------|---------|--------|
| 类型 | 短期对话历史 | 长期知识存储 |
| 生命周期 | 随会话关闭 | 跨会话持久 |
| 内容 | 完整对话消息 | 提取的关键信息 |
| 检索 | 按顺序回放 | 按关键词/分类搜索 |

## 核心概念

### MemoryItem（单条记忆）

- `content`: 记忆内容
- `timestamp`: 记忆时间
- `importance`: 重要性评分 (0.0-1.0)
- `category`: 分类标签（fact, preference, skill, event 等）

### 重要性评分

| 范围 | 含义 | 示例 |
|------|------|------|
| 0.9-1.0 | 核心信息 | 用户名、关键偏好 |
| 0.7-0.8 | 重要信息 | 常用设置、重要决策 |
| 0.4-0.6 | 一般信息 | 普通对话内容 |
| 0.0-0.3 | 低价值信息 | 可遗忘 |

## 使用方式

### 1. 创建记忆管理器

```python
from rogue_rabbit.core import MemoryManager
from rogue_rabbit.runtime import InMemoryStore

manager = MemoryManager(store=InMemoryStore())
```

### 2. 添加记忆

```python
# 创建记忆空间
manager.create(user_id="user1")

# 添加记忆
manager.add_memory(
    "user1",
    "用户喜欢简洁的回答",
    importance=0.8,
    category="preference"
)
```

### 3. 搜索记忆

```python
# 关键词搜索
results = manager.search("user1", "Python")

# 按分类过滤
results = manager.search("user1", "工具", category="preference")

# 按重要性过滤
results = manager.search("user1", "设置", min_importance=0.7)
```

### 4. 遗忘记忆

```python
# 按关键词遗忘
removed = manager.forget("user1", "过期信息")
print(f"遗忘了 {removed} 条记忆")
```

### 5. 记忆摘要

```python
# 简单摘要（无 LLM）
summary = manager.summarize("user1")

# LLM 生成摘要
from rogue_rabbit.adapters import GLMClient
manager = MemoryManager(store=InMemoryStore(), llm_client=GLMClient())
summary = manager.summarize("user1")
```

## 与 Session 集成

### 注入记忆到对话上下文

```python
from rogue_rabbit.core import SessionManager
from rogue_rabbit.runtime import InMemoryStore

# 获取相关记忆
context = manager.get_context_for_session("user1", "用户问题")

# 创建带记忆的会话
session_manager = SessionManager(store=InMemoryStore(), llm_client=llm)
session = session_manager.create(
    system_prompt=f"你是一个助手。\n\n{context}"
)

# 对话时 LLM 可以引用记忆
response = session_manager.chat(session.meta.session_id, "推荐工具")
```

### 从对话中提取记忆

```python
# 对话结束后，提取关键信息
manager.add_memory("user1", "用户提到了偏好XXX", category="preference")
```

## 存储后端

### InMemoryStore

内存存储，适合测试。

```python
from rogue_rabbit.runtime import InMemoryStore

store = InMemoryStore()
```

### FileMemoryStore

文件存储，适合持久化。

```python
from pathlib import Path
from rogue_rabbit.runtime import FileMemoryStore

store = FileMemoryStore(Path("./memories"))
```

## 最佳实践

1. **合理设置重要性**
   - 核心信息: 0.9+
   - 偏好/习惯: 0.7-0.8
   - 一般信息: 0.4-0.6

2. **使用分类标签**
   - `fact`: 事实信息
   - `preference`: 用户偏好
   - `skill`: 技能相关
   - `event`: 事件记录

3. **定期清理低价值记忆**
   - 使用 `forget()` 清理过期信息
   - 使用重要性阈值过滤

4. **记忆注入控制**
   - 只注入与当前对话相关的记忆
   - 限制注入数量（建议 3-5 条）

## 相关文件

- `contracts/memory.py`: Memory 数据结构定义
- `core/memory_manager.py`: Memory 管理器
- `runtime/memory_store.py`: 存储后端实现
- `experiments/12_memory_basic.py`: 基础实验
- `experiments/13_memory_with_session.py`: 集成实验
- `notebooks/06_memory_basics.ipynb`: 学习 notebook
