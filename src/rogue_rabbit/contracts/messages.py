"""
消息模型 - LLM 交互的核心数据结构

学习要点:
=========
1. LLM 交互的本质是"消息的交换"
2. 每条消息由"角色"和"内容"组成
3. 角色决定了消息的语义：系统指令、用户输入、AI 回复

为什么用 dataclass?
- 自动生成 __init__, __repr__ 等方法
- 代码简洁，专注于数据本身
- 不可变性（frozen=True）保证数据安全
"""

from dataclasses import dataclass
from enum import Enum


class Role(Enum):
    """
    消息角色 - 定义消息的来源和语义

    三种角色:
    --------
    - SYSTEM: 系统指令，定义 AI 的行为准则
      示例: "你是一个有帮助的助手"

    - USER: 用户输入，人类的问题或请求
      示例: "什么是机器学习？"

    - ASSISTANT: AI 回复，模型的输出
      示例: "机器学习是人工智能的一个分支..."

    为什么需要角色区分?
    ------------------
    LLM 需要知道每条消息是谁说的，才能正确理解上下文。
    例如，同样的内容"好的"，来自 USER 和 ASSISTANT 有完全不同的含义。
    """

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass(frozen=True)
class Message:
    """
    消息 - LLM 交互的基本单位

    属性:
    -----
    - role: 谁发出的消息（系统/用户/AI）
    - content: 消息的具体内容

    为什么用 frozen=True?
    --------------------
    消息一旦创建就不应该被修改，这样可以:
    1. 避免意外的数据污染
    2. 安全地在多处共享消息对象
    3. 作为字典的 key 或放入集合

    使用示例:
    --------
    >>> msg = Message(role=Role.USER, content="你好")
    >>> msg.role
    <Role.USER: 'user'>
    >>> msg.content
    '你好'
    """

    role: Role
    content: str

    def __str__(self) -> str:
        """友好的字符串表示，便于调试和显示"""
        return f"[{self.role.value}]: {self.content}"


# 类型别名，提高代码可读性
MessageList = list[Message]
"""
消息列表 - 表示一段对话的所有消息

使用类型别名的好处:
- 代码更易读: `def chat(messages: MessageList)` 比 `def chat(messages: list[Message])` 更清晰
- 便于统一修改: 如果将来需要换成其他类型，只需改一处
"""
