"""
会话管理器

学习要点:
=========
1. 会话生命周期管理：创建、获取、暂停、关闭、删除
2. 协调存储后端和 LLM 客户端
3. 与上下文窗口管理器集成

设计模式:
=========
SessionManager 是一个"协调者"（Coordinator）：
- 不直接存储数据，委托给 SessionStore
- 不直接处理对话，委托给 LLMClient
- 可选地使用 ContextWindowManager 管理上下文

这种设计遵循"单一职责"原则：
- SessionStore: 只负责存储
- LLMClient: 只负责 LLM 调用
- ContextWindowManager: 只负责上下文管理
- SessionManager: 只负责协调
"""

import logging
from typing import Protocol

from rogue_rabbit.contracts.messages import Message, Role
from rogue_rabbit.contracts.session import Session, SessionMeta, SessionStatus, SessionStore

logger = logging.getLogger("session-manager")


class SessionManager:
    """
    会话管理器

    职责:
    ----
    1. 创建新会话
    2. 获取/恢复会话
    3. 管理会话生命周期
    4. 协调存储后端和 LLM 客户端

    使用示例:
    --------
    >>> from rogue_rabbit.adapters import GLMClient
    >>> from rogue_rabbit.runtime import MemorySessionStore
    >>>
    >>> manager = SessionManager(
    ...     store=MemorySessionStore(),
    ...     llm_client=GLMClient()
    ... )
    >>>
    >>> # 创建新会话
    >>> session = manager.create(system_prompt="你是一个助手")
    >>>
    >>> # 对话
    >>> response = manager.chat(session.meta.session_id, "你好")
    >>>
    >>> # 关闭会话
    >>> manager.close(session.meta.session_id)
    """

    def __init__(
        self,
        store: SessionStore,
        llm_client,  # LLMClient 协议
        context_window_manager=None,  # 可选的上下文窗口管理器
    ):
        """
        初始化会话管理器

        参数:
        -----
        store: 会话存储后端
        llm_client: LLM 客户端
        context_window_manager: 上下文窗口管理器（可选）
        """
        self._store = store
        self._llm = llm_client
        self._context_window = context_window_manager

    def create(
        self,
        system_prompt: str | None = None,
        metadata: dict | None = None,
    ) -> Session:
        """
        创建新会话

        参数:
        -----
        system_prompt: 系统提示词（可选）
        metadata: 自定义元数据（可选）

        返回:
        -----
        新创建的会话对象
        """
        session = Session(
            meta=SessionMeta(metadata=metadata or {}),
            system_prompt=system_prompt,
        )
        self._store.save(session)
        logger.info(f"[Session] 创建会话: {session.meta.session_id}")
        return session

    def get(self, session_id: str) -> Session | None:
        """
        获取会话

        参数:
        -----
        session_id: 会话ID

        返回:
        -----
        会话对象或 None（如果不存在）

        注意:
        -----
        如果会话处于 IDLE 状态，会自动恢复为 ACTIVE
        """
        session = self._store.load(session_id)
        if session:
            # 恢复活跃状态
            if session.meta.status == SessionStatus.IDLE:
                session.meta.status = SessionStatus.ACTIVE
                session.meta.touch()
                self._store.save(session)
                logger.info(f"[Session] 恢复会话: {session_id}")
        return session

    def chat(self, session_id: str, user_input: str) -> str:
        """
        在会话中进行对话

        参数:
        -----
        session_id: 会话ID
        user_input: 用户输入

        返回:
        -----
        AI 回复

        异常:
        -----
        ValueError: 会话不存在或已关闭
        """
        session = self.get(session_id)
        if not session:
            raise ValueError(f"会话不存在: {session_id}")

        if session.meta.status == SessionStatus.CLOSED:
            raise ValueError(f"会话已关闭: {session_id}")

        # 添加用户消息
        session.add_message(Message(role=Role.USER, content=user_input))

        # 获取上下文（可能经过窗口管理）
        context = session.get_context_for_llm()
        if self._context_window:
            context = self._context_window.manage(context)

        # 调用 LLM
        response = self._llm.complete(context)

        # 添加 AI 回复
        session.add_message(Message(role=Role.ASSISTANT, content=response))

        # 保存会话
        self._store.save(session)

        return response

    def pause(self, session_id: str) -> bool:
        """
        暂停会话

        暂停的会话可以通过 get() 恢复

        参数:
        -----
        session_id: 会话ID

        返回:
        -----
        是否成功
        """
        session = self._store.load(session_id)
        if session:
            session.meta.status = SessionStatus.IDLE
            self._store.save(session)
            logger.info(f"[Session] 暂停会话: {session_id}")
            return True
        return False

    def close(self, session_id: str) -> bool:
        """
        关闭会话

        关闭的会话不能再使用，但数据保留

        参数:
        -----
        session_id: 会话ID

        返回:
        -----
        是否成功
        """
        session = self._store.load(session_id)
        if session:
            session.meta.status = SessionStatus.CLOSED
            self._store.save(session)
            logger.info(f"[Session] 关闭会话: {session_id}")
            return True
        return False

    def delete(self, session_id: str) -> bool:
        """
        删除会话

        删除的会话数据将被清除

        参数:
        -----
        session_id: 会话ID

        返回:
        -----
        是否成功
        """
        result = self._store.delete(session_id)
        if result:
            logger.info(f"[Session] 删除会话: {session_id}")
        return result

    def list_sessions(self) -> list[SessionMeta]:
        """
        列出所有会话

        返回:
        -----
        所有会话的元数据列表
        """
        return self._store.list_sessions()

    def get_history(self, session_id: str) -> list[Message]:
        """
        获取会话历史

        参数:
        -----
        session_id: 会话ID

        返回:
        -----
        消息历史列表
        """
        session = self._store.load(session_id)
        if session:
            return session.messages.copy()
        return []
