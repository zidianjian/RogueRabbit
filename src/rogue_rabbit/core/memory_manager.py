"""
记忆管理器

学习要点:
=========
1. 长期记忆的增删改查
2. 记忆检索策略（关键词匹配、分类过滤、重要性排序）
3. 与 LLM 集成的记忆摘要生成
4. 与 Session 集成的记忆注入

设计模式:
=========
MemoryManager 是记忆系统的"协调者"：
- 委托 MemoryStore 处理持久化
- 可选地使用 LLM 生成记忆摘要
- 提供与 Session 集成的接口
"""

import logging

from rogue_rabbit.contracts.memory import Memory, MemoryItem, MemoryMeta, MemoryStore
from rogue_rabbit.contracts.messages import Message, Role

logger = logging.getLogger("memory-manager")


class MemoryManager:
    """
    记忆管理器

    职责:
    ----
    1. 创建和管理记忆空间
    2. 添加、检索、遗忘记忆
    3. 生成记忆摘要
    4. 与 LLM 和 Session 集成

    使用示例:
    --------
    >>> from rogue_rabbit.runtime import InMemoryStore
    >>> manager = MemoryManager(store=InMemoryStore())
    >>>
    >>> # 创建记忆空间
    >>> memory = manager.create(user_id="user1")
    >>>
    >>> # 添加记忆
    >>> manager.add_memory("user1", "用户喜欢简洁的回答", category="preference")
    >>>
    >>> # 搜索记忆
    >>> results = manager.search("user1", "回答")
    >>>
    >>> # 生成摘要
    >>> summary = manager.summarize("user1")
    """

    def __init__(
        self,
        store: MemoryStore,
        llm_client=None,  # 可选，用于摘要生成
    ):
        """
        初始化记忆管理器

        参数:
        -----
        store: 记忆存储后端
        llm_client: LLM 客户端（可选，用于生成摘要）
        """
        self._store = store
        self._llm = llm_client

    def create(self, user_id: str) -> Memory:
        """
        创建记忆空间

        参数:
        -----
        user_id: 用户标识

        返回:
        -----
        新创建的记忆对象
        """
        memory = Memory(meta=MemoryMeta(user_id=user_id))
        self._store.save(memory)
        logger.info(f"[Memory] 创建记忆空间: {user_id}")
        return memory

    def get(self, user_id: str) -> Memory | None:
        """
        获取记忆空间

        参数:
        -----
        user_id: 用户标识

        返回:
        -----
        记忆对象或 None
        """
        return self._store.load(user_id)

    def add_memory(
        self,
        user_id: str,
        content: str,
        importance: float = 1.0,
        category: str = "general",
        metadata: dict | None = None,
    ) -> None:
        """
        添加记忆

        参数:
        -----
        user_id: 用户标识
        content: 记忆内容
        importance: 重要性 (0.0-1.0)
        category: 分类标签
        metadata: 扩展信息
        """
        memory = self._store.load(user_id)
        if not memory:
            memory = self.create(user_id)

        item = MemoryItem(
            content=content,
            importance=importance,
            category=category,
            metadata=metadata or {},
        )
        memory.add_item(item)
        self._store.save(memory)
        logger.info(f"[Memory] 添加记忆: {user_id} [{category}] {content[:30]}...")

    def search(
        self,
        user_id: str,
        query: str,
        category: str | None = None,
        min_importance: float = 0.0,
        limit: int = 10,
    ) -> list[MemoryItem]:
        """
        搜索记忆

        参数:
        -----
        user_id: 用户标识
        query: 搜索关键词
        category: 按分类过滤（可选）
        min_importance: 最低重要性过滤
        limit: 最大返回数量

        返回:
        -----
        匹配的记忆列表
        """
        memory = self._store.load(user_id)
        if not memory:
            return []

        # 先按关键词搜索
        results = memory.search(query, limit=limit * 2)

        # 按分类过滤
        if category:
            results = [r for r in results if r.category == category]

        # 按重要性过滤
        if min_importance > 0:
            results = [r for r in results if r.importance >= min_importance]

        return results[:limit]

    def forget(self, user_id: str, content_match: str) -> int:
        """
        遗忘记忆

        参数:
        -----
        user_id: 用户标识
        content_match: 匹配内容（关键词）

        返回:
        -----
        被遗忘的记忆数量
        """
        memory = self._store.load(user_id)
        if not memory:
            return 0

        removed = memory.forget(content_match)
        if removed > 0:
            self._store.save(memory)
            logger.info(f"[Memory] 遗忘 {removed} 条记忆: {user_id}")
        return removed

    def summarize(self, user_id: str) -> str:
        """
        生成记忆摘要

        优先使用 LLM 生成摘要，否则使用简单的格式化输出

        参数:
        -----
        user_id: 用户标识

        返回:
        -----
        摘要文本
        """
        memory = self._store.load(user_id)
        if not memory or not memory.items:
            return "暂无记忆。"

        if self._llm:
            return self._generate_summary_with_llm(memory)
        return memory.summarize_items()

    def _generate_summary_with_llm(self, memory: Memory) -> str:
        """使用 LLM 生成记忆摘要"""
        items_text = memory.summarize_items()
        prompt = f"""请将以下记忆条目总结为简洁的摘要，保留关键信息：

{items_text}

摘要："""
        return self._llm.complete([Message(role=Role.USER, content=prompt)])

    def get_context_for_session(self, user_id: str, query: str) -> str:
        """
        获取注入到 Session 上下文的记忆

        根据当前查询检索相关记忆，格式化为可注入的文本

        参数:
        -----
        user_id: 用户标识
        query: 当前对话内容（用于检索相关记忆）

        返回:
        -----
        格式化的记忆上下文文本
        """
        results = self.search(user_id, query, min_importance=0.5, limit=5)
        if not results:
            return ""

        lines = ["[相关记忆]"]
        for item in results:
            lines.append(f"- [{item.category}] {item.content}")
        return "\n".join(lines)

    def list_memories(self) -> list[MemoryMeta]:
        """列出所有记忆空间"""
        return self._store.list_memories()

    def delete(self, user_id: str) -> bool:
        """删除记忆空间"""
        result = self._store.delete(user_id)
        if result:
            logger.info(f"[Memory] 删除记忆空间: {user_id}")
        return result
