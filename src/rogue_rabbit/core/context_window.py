"""
上下文窗口管理

学习要点:
=========
1. LLM 有 token 限制（如 GPT-4: 8K/32K）
2. 长对话会超出限制导致错误
3. 过多历史会降低响应质量
4. 需要策略来管理对话历史

为什么需要上下文窗口管理?
=======================
1. 成本控制：减少 token 使用，降低 API 调用成本
2. 质量保证：过多的历史会稀释当前问题的相关性
3. 错误预防：避免超出 token 限制导致的 API 错误

截断策略:
========
- KEEP_FIRST: 保留前N条，适合早期上下文重要场景
- KEEP_LAST: 保留后N条，适合最近上下文重要场景（默认）
- KEEP_FIRST_LAST: 保留首尾，兼顾开始和最近
- SUMMARIZE: 生成摘要替换中间内容（需要 LLM 支持）
"""

from dataclasses import dataclass
from enum import Enum

from rogue_rabbit.contracts.messages import Message, MessageList, Role


class TruncationStrategy(Enum):
    """
    截断策略

    策略选择指南:
    ------------
    - KEEP_FIRST: 系统提示词和第一条用户消息很重要
    - KEEP_LAST: 最近几轮对话最相关（推荐）
    - KEEP_FIRST_LAST: 兼顾历史背景和最新上下文
    - SUMMARIZE: 保留关键信息，但需要额外 LLM 调用

    注意:
    -----
    系统消息（SYSTEM role）总是会被保留
    """

    KEEP_FIRST = "keep_first"
    KEEP_LAST = "keep_last"
    KEEP_FIRST_LAST = "keep_first_last"
    SUMMARIZE = "summarize"


@dataclass
class ContextWindowConfig:
    """
    上下文窗口配置

    属性:
    -----
    - max_messages: 最大消息数量（不包括系统消息）
    - strategy: 截断策略
    - keep_first: 保留前N条（用于 KEEP_FIRST_LAST 策略）
    - keep_last: 保留后M条（用于 KEEP_FIRST_LAST 策略）

    默认值设计:
    ----------
    - max_messages=20: 平衡上下文质量和长度
    - strategy=KEEP_LAST: 最近对话最相关
    - keep_first=2: 系统提示词 + 第一条用户消息
    - keep_last=10: 最近5轮对话（10条消息）
    """

    max_messages: int = 20
    strategy: TruncationStrategy = TruncationStrategy.KEEP_LAST
    keep_first: int = 2
    keep_last: int = 10


class ContextWindowManager:
    """
    上下文窗口管理器

    使用方式:
    --------
    >>> manager = ContextWindowManager(
    ...     config=ContextWindowConfig(max_messages=20),
    ...     llm_client=llm_client  # 可选，用于摘要
    ... )
    >>> managed_context = manager.manage(messages)

    设计考量:
    --------
    - 可选的 LLM 客户端：只有 SUMMARIZE 策略需要
    - 不修改原消息列表：返回新的列表
    - 系统消息总是保留：不受截断影响
    """

    def __init__(
        self,
        config: ContextWindowConfig | None = None,
        llm_client=None,  # 可选，用于生成摘要
    ):
        """
        初始化上下文窗口管理器

        参数:
        -----
        config: 配置项，默认使用 ContextWindowConfig()
        llm_client: LLM 客户端，用于 SUMMARIZE 策略
        """
        self._config = config or ContextWindowConfig()
        self._llm = llm_client

    def manage(self, messages: MessageList) -> MessageList:
        """
        管理上下文窗口

        如果消息数量超过限制，根据策略进行截断

        参数:
        -----
        messages: 原始消息列表

        返回:
        -----
        管理后的消息列表（新列表，不修改原列表）
        """
        # 分离系统消息和对话消息
        system_messages = [m for m in messages if m.role == Role.SYSTEM]
        conversation = [m for m in messages if m.role != Role.SYSTEM]

        # 检查是否需要截断
        if len(conversation) <= self._config.max_messages:
            return messages.copy() if system_messages else messages

        # 根据策略截断
        if self._config.strategy == TruncationStrategy.KEEP_FIRST:
            truncated = conversation[: self._config.max_messages]

        elif self._config.strategy == TruncationStrategy.KEEP_LAST:
            truncated = conversation[-self._config.max_messages :]

        elif self._config.strategy == TruncationStrategy.KEEP_FIRST_LAST:
            first = conversation[: self._config.keep_first]
            last = conversation[-self._config.keep_last :]
            truncated = first + last

        elif self._config.strategy == TruncationStrategy.SUMMARIZE:
            truncated = self._summarize_middle(conversation)

        else:
            # 默认使用 KEEP_LAST
            truncated = conversation[-self._config.max_messages :]

        return system_messages + truncated

    def _summarize_middle(self, messages: MessageList) -> MessageList:
        """
        生成摘要替换中间消息

        保留: [前N条] + [摘要] + [后M条]

        注意:
        -----
        如果没有 LLM 客户端，降级为 KEEP_FIRST_LAST
        """
        if not self._llm:
            # 没有 LLM，降级为 KEEP_FIRST_LAST
            return messages[: self._config.keep_first] + messages[-self._config.keep_last :]

        first = messages[: self._config.keep_first]
        last = messages[-self._config.keep_last :]
        middle = messages[self._config.keep_first : -self._config.keep_last]

        if not middle:
            return first + last

        # 生成摘要
        summary_text = self._generate_summary(middle)
        summary_message = Message(
            role=Role.SYSTEM, content=f"[对话摘要]\n{summary_text}"
        )

        return first + [summary_message] + last

    def _generate_summary(self, messages: MessageList) -> str:
        """
        使用 LLM 生成对话摘要

        参数:
        -----
        messages: 需要摘要的消息列表

        返回:
        -----
        摘要文本
        """
        # 构建摘要提示
        conversation_text = "\n".join(
            [f"{m.role.value}: {m.content}" for m in messages]
        )

        prompt = f"""请将以下对话总结为简洁的摘要，保留关键信息：

{conversation_text}

摘要："""

        return self._llm.complete([Message(role=Role.USER, content=prompt)])

    def estimate_tokens(self, messages: MessageList) -> int:
        """
        估算消息列表的 token 数量

        简单估算：平均每 4 个字符约 1 个 token

        注意:
        -----
        这只是一个粗略估算，实际 token 数量取决于：
        - 使用的 tokenizer（不同模型不同）
        - 中英文比例（中文通常更多 token）
        - 特殊字符和格式
        """
        total_chars = sum(len(m.content) for m in messages)
        return total_chars // 4
