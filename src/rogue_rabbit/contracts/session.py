"""
会话协议定义

学习要点:
=========
1. 会话生命周期：创建 -> 活跃 -> 暂停 -> 恢复 -> 销毁
2. 会话状态管理：消息历史 + 元数据
3. 存储抽象：支持多种后端

Session vs Conversation:
-----------------------
- Conversation: 简单的消息列表封装（实验02）
- Session: 完整的会话生命周期管理，包含持久化能力

为什么需要会话管理?
==================
1. LLM 是无状态的，需要调用方维护对话历史
2. 用户可能有多个并行对话（不同主题、不同场景）
3. 会话需要持久化，支持跨进程恢复
4. 长对话需要上下文窗口管理
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Protocol, runtime_checkable
from uuid import uuid4

from rogue_rabbit.contracts.messages import Message, MessageList, Role


class SessionStatus(Enum):
    """
    会话状态

    状态转换:
    --------
    ACTIVE <-> IDLE -> CLOSED

    - ACTIVE: 正在进行对话
    - IDLE: 暂停，可恢复
    - CLOSED: 已关闭，不可恢复

    设计考量:
    --------
    - 区分 IDLE 和 CLOSED: 暂停的会话可以恢复，关闭的会话只能归档
    - 状态由 SessionManager 管理，不直接修改
    """

    ACTIVE = "active"
    IDLE = "idle"
    CLOSED = "closed"


@dataclass
class SessionMeta:
    """
    会话元数据

    属性:
    -----
    - session_id: 唯一标识（8位短ID，便于调试）
    - created_at: 创建时间
    - updated_at: 最后更新时间
    - status: 会话状态
    - metadata: 自定义元数据（如用户ID、标题等）

    为什么需要元数据?
    ----------------
    1. session_id: 唯一标识，用于恢复会话
    2. 时间戳: 用于会话列表排序、过期清理
    3. metadata: 扩展字段，存储业务相关信息

    注意:
    -----
    此类不是 frozen=True，因为需要更新 updated_at 和 status
    """

    session_id: str = field(default_factory=lambda: str(uuid4())[:8])
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    status: SessionStatus = SessionStatus.ACTIVE
    metadata: dict[str, Any] = field(default_factory=dict)

    def touch(self) -> None:
        """更新最后活动时间"""
        self.updated_at = datetime.now()


@dataclass
class Session:
    """
    完整会话对象

    包含:
    -----
    - meta: 会话元数据
    - messages: 完整对话历史
    - system_prompt: 系统提示词

    核心方法:
    --------
    - add_message(): 添加消息并更新时间戳
    - get_context_for_llm(): 获取发送给 LLM 的消息上下文
    - to_dict() / from_dict(): 序列化/反序列化（用于持久化）

    使用示例:
    --------
    >>> session = Session(meta=SessionMeta(), system_prompt="你是助手")
    >>> session.add_message(Message(role=Role.USER, content="你好"))
    >>> context = session.get_context_for_llm()
    """

    meta: SessionMeta
    messages: MessageList = field(default_factory=list)
    system_prompt: str | None = None

    def add_message(self, message: Message) -> None:
        """
        添加消息并更新时间戳

        为什么自动更新时间戳?
        --------------------
        会话的任何变化都应该反映在 updated_at 上，
        便于后续实现会话过期清理等功能。
        """
        self.messages.append(message)
        self.meta.touch()

    def get_context_for_llm(self) -> MessageList:
        """
        获取发送给 LLM 的消息上下文

        返回:
        -----
        包含系统提示词（如果有）和所有对话消息的列表

        注意:
        -----
        此方法返回新列表，不修改原消息列表
        """
        result: MessageList = []
        if self.system_prompt:
            result.append(Message(role=Role.SYSTEM, content=self.system_prompt))
        result.extend(self.messages)
        return result

    def to_dict(self) -> dict:
        """
        序列化为字典（用于持久化）

        格式设计:
        --------
        - 使用 ISO 格式存储时间，便于跨平台
        - 使用枚举的 value，便于 JSON 序列化
        """
        return {
            "meta": {
                "session_id": self.meta.session_id,
                "created_at": self.meta.created_at.isoformat(),
                "updated_at": self.meta.updated_at.isoformat(),
                "status": self.meta.status.value,
                "metadata": self.meta.metadata,
            },
            "system_prompt": self.system_prompt,
            "messages": [
                {"role": msg.role.value, "content": msg.content}
                for msg in self.messages
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        """
        从字典反序列化

        参数:
        -----
        data: to_dict() 生成的字典

        返回:
        -----
        Session 对象

        注意:
        -----
        此方法假设数据格式正确，不做严格校验
        """
        meta_data = data["meta"]
        meta = SessionMeta(
            session_id=meta_data["session_id"],
            created_at=datetime.fromisoformat(meta_data["created_at"]),
            updated_at=datetime.fromisoformat(meta_data["updated_at"]),
            status=SessionStatus(meta_data["status"]),
            metadata=meta_data.get("metadata", {}),
        )

        messages = [
            Message(role=Role(msg["role"]), content=msg["content"])
            for msg in data.get("messages", [])
        ]

        return cls(
            meta=meta,
            messages=messages,
            system_prompt=data.get("system_prompt"),
        )


@runtime_checkable
class SessionStore(Protocol):
    """
    会话存储协议 - 定义会话持久化的标准接口

    为什么需要存储抽象?
    ------------------
    1. 支持多种后端：内存、文件、数据库
    2. 便于测试：可以用 Mock 存储
    3. 灵活切换：生产环境可以换存储而不改代码

    使用 Protocol 的好处:
    -------------------
    - 不需要继承，只需要实现相同的方法
    - @runtime_checkable 支持 isinstance() 检查
    - 符合 Python 的鸭子类型哲学

    方法说明:
    --------
    - save: 保存或更新会话
    - load: 加载会话，不存在返回 None
    - delete: 删除会话，返回是否成功
    - list_sessions: 列出所有会话的元数据
    """

    def save(self, session: Session) -> None:
        """保存会话"""
        ...

    def load(self, session_id: str) -> Session | None:
        """加载会话，不存在返回 None"""
        ...

    def delete(self, session_id: str) -> bool:
        """删除会话，返回是否成功"""
        ...

    def list_sessions(self) -> list[SessionMeta]:
        """列出所有会话的元数据"""
        ...
