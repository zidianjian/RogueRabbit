"""
记忆协议定义

学习要点:
=========
1. 短期记忆 vs 长期记忆：Session 负责短期对话，Memory 负责长期知识
2. 记忆存储和检索：支持关键词匹配、分类过滤、重要性排序
3. 记忆总结和遗忘：自动总结低价值记忆，支持主动遗忘

Memory vs Session:
-----------------
- Session: 短期对话历史，随会话关闭而停止
- Memory: 长期知识存储，跨会话持久化

为什么需要长期记忆?
==================
1. 用户偏好：记住用户喜欢的风格、语言等
2. 知识积累：从历史对话中提取有价值的知识
3. 上下文延续：新会话可以引用历史信息
4. 个性化：根据历史记忆提供个性化服务
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Protocol, runtime_checkable
from uuid import uuid4


@dataclass
class MemoryItem:
    """
    单条记忆

    属性:
    -----
    - content: 记忆内容
    - timestamp: 记忆时间
    - importance: 重要性评分 (0.0-1.0)
    - category: 分类标签（如 preference, fact, event 等）
    - metadata: 扩展信息

    重要性评分:
    ----------
    - 1.0: 核心信息（用户名、关键偏好）
    - 0.7-0.9: 重要信息（常用设置、重要决策）
    - 0.4-0.6: 一般信息（普通对话内容）
    - 0.0-0.3: 低价值信息（可遗忘）

    使用示例:
    --------
    >>> item = MemoryItem(
    ...     content="用户喜欢简洁的回答",
    ...     importance=0.8,
    ...     category="preference"
    ... )
    """

    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    importance: float = 1.0
    category: str = "general"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "importance": self.importance,
            "category": self.category,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryItem":
        """从字典反序列化"""
        return cls(
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            importance=data.get("importance", 1.0),
            category=data.get("category", "general"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class MemoryMeta:
    """
    记忆空间元数据

    每个 user_id 对应一个记忆空间

    属性:
    -----
    - memory_id: 记忆空间唯一标识
    - user_id: 所属用户
    - created_at: 创建时间
    - updated_at: 最后更新时间
    - categories: 所有分类标签
    - item_count: 记忆条目数量
    """

    memory_id: str = field(default_factory=lambda: str(uuid4())[:8])
    user_id: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    categories: set[str] = field(default_factory=set)
    item_count: int = 0

    def touch(self) -> None:
        """更新最后活动时间"""
        self.updated_at = datetime.now()


@dataclass
class Memory:
    """
    完整记忆对象

    一个用户的长期记忆空间，包含多条 MemoryItem

    核心方法:
    --------
    - add_item(): 添加记忆
    - search(): 搜索记忆（关键词匹配）
    - forget(): 遗忘记忆
    - get_by_category(): 按分类获取
    - get_important(): 获取重要记忆
    - summarize_items(): 生成摘要文本

    使用示例:
    --------
    >>> memory = Memory(meta=MemoryMeta(user_id="user1"))
    >>> memory.add_item(MemoryItem(content="用户喜欢Python", category="preference"))
    >>> results = memory.search("Python")
    """

    meta: MemoryMeta
    items: list[MemoryItem] = field(default_factory=list)

    def add_item(self, item: MemoryItem) -> None:
        """
        添加记忆并更新元数据

        自动更新 categories 和 item_count
        """
        self.items.append(item)
        self.meta.categories.add(item.category)
        self.meta.item_count = len(self.items)
        self.meta.touch()

    def search(self, query: str, limit: int = 10) -> list[MemoryItem]:
        """
        搜索记忆（关键词匹配）

        参数:
        -----
        query: 搜索关键词
        limit: 最大返回数量

        返回:
        -----
        按重要性排序的匹配记忆列表
        """
        query_lower = query.lower()
        results = [
            item for item in self.items
            if query_lower in item.content.lower()
        ]
        # 按重要性降序排序
        results.sort(key=lambda x: x.importance, reverse=True)
        return results[:limit]

    def forget(self, content_match: str) -> int:
        """
        遗忘记忆

        参数:
        -----
        content_match: 匹配内容（关键词）

        返回:
        -----
        被遗忘的记忆数量
        """
        match_lower = content_match.lower()
        before = len(self.items)
        self.items = [
            item for item in self.items
            if match_lower not in item.content.lower()
        ]
        removed = before - len(self.items)
        if removed > 0:
            self.meta.item_count = len(self.items)
            self._rebuild_categories()
            self.meta.touch()
        return removed

    def get_by_category(self, category: str) -> list[MemoryItem]:
        """按分类获取记忆"""
        return [item for item in self.items if item.category == category]

    def get_important(self, threshold: float = 0.7) -> list[MemoryItem]:
        """获取重要记忆（重要性 >= threshold）"""
        return [
            item for item in self.items
            if item.importance >= threshold
        ]

    def summarize_items(self) -> str:
        """
        生成记忆摘要文本（用于注入 LLM 上下文）

        返回:
        -----
        格式化的记忆摘要
        """
        if not self.items:
            return "暂无记忆。"

        lines = []
        for item in sorted(self.items, key=lambda x: x.importance, reverse=True):
            lines.append(f"- [{item.category}] {item.content}")
        return "\n".join(lines)

    def _rebuild_categories(self) -> None:
        """重建分类集合"""
        self.meta.categories = {item.category for item in self.items}

    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            "meta": {
                "memory_id": self.meta.memory_id,
                "user_id": self.meta.user_id,
                "created_at": self.meta.created_at.isoformat(),
                "updated_at": self.meta.updated_at.isoformat(),
                "categories": list(self.meta.categories),
                "item_count": self.meta.item_count,
            },
            "items": [item.to_dict() for item in self.items],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Memory":
        """从字典反序列化"""
        meta_data = data["meta"]
        meta = MemoryMeta(
            memory_id=meta_data["memory_id"],
            user_id=meta_data.get("user_id", ""),
            created_at=datetime.fromisoformat(meta_data["created_at"]),
            updated_at=datetime.fromisoformat(meta_data["updated_at"]),
            categories=set(meta_data.get("categories", [])),
            item_count=meta_data.get("item_count", 0),
        )

        items = [
            MemoryItem.from_dict(item_data)
            for item_data in data.get("items", [])
        ]

        memory = cls(meta=meta, items=items)
        return memory


@runtime_checkable
class MemoryStore(Protocol):
    """
    记忆存储协议

    与 SessionStore 类似的抽象，支持多种存储后端

    方法说明:
    --------
    - save: 保存或更新记忆空间
    - load: 加载记忆空间，不存在返回 None
    - delete: 删除记忆空间，返回是否成功
    - list_memories: 列出所有记忆空间的元数据
    """

    def save(self, memory: Memory) -> None:
        """保存记忆空间"""
        ...

    def load(self, user_id: str) -> Memory | None:
        """加载记忆空间，按 user_id 查找"""
        ...

    def delete(self, user_id: str) -> bool:
        """删除记忆空间"""
        ...

    def list_memories(self) -> list[MemoryMeta]:
        """列出所有记忆空间的元数据"""
        ...
