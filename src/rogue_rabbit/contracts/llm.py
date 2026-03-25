"""
LLM 协议 - 定义 LLM 客户端的标准接口

学习要点:
=========
1. Protocol 是什么？为什么需要它？
2. 抽象层的作用：解耦"定义"与"实现"
3. 如何让代码支持多种 LLM 提供商

Protocol vs ABC (抽象基类):
--------------------------
- Protocol: 结构化子类型（鸭子类型的静态检查版）
  - 不需要显式继承
  - 只要有相同的方法签名就满足协议

- ABC: 需要显式继承
  - 强制继承关系
  - 更严格的约束

对于 LLM 客户端，用 Protocol 更灵活：
- 第三方库的客户端不需要修改就能适配
- 便于 mock 测试
"""

from typing import Protocol, runtime_checkable

from rogue_rabbit.contracts.messages import Message, MessageList


@runtime_checkable
class LLMClient(Protocol):
    """
    LLM 客户端协议 - 任何 LLM 都应该实现这个接口

    这个协议定义了 LLM 客户端的"契约"：
    - 只要实现了 complete 方法，就是合法的 LLM 客户端
    - 调用方不需要知道具体是哪个 LLM

    为什么需要协议层?
    ---------------
    1. **解耦**: 业务代码不依赖具体的 LLM 实现
    2. **可替换**: 可以随时切换 LLM 提供商
    3. **可测试**: 可以轻松创建 mock 客户端

    设计决策:
    --------
    - complete() 返回 str 而不是复杂对象：保持简单，阶段一够用
    - messages 参数是 list[Message]：统一的消息格式
    - 没有异步版本：阶段一优先简单，后续再扩展

    使用示例:
    --------
    >>> def ask(client: LLMClient, question: str) -> str:
    ...     msg = Message(role=Role.USER, content=question)
    ...     return client.complete([msg])
    """

    def complete(self, messages: MessageList) -> str:
        """
        发送消息列表给 LLM，获取回复

        参数:
        -----
        messages: 消息列表，包含完整的对话上下文

        返回:
        -----
        str: LLM 的文本回复

        注意:
        -----
        - messages 应该按时间顺序排列
        - 通常以 system 消息开头（可选）
        - 然后是 user/assistant 交替的消息
        """
        ...


class MockLLMClient:
    """
    Mock LLM 客户端 - 用于测试和学习

    这个客户端不调用真实的 LLM API，而是返回固定响应。
    用途:
    1. 在没有 API key 时测试代码
    2. 学习 LLM 调用流程
    3. 单元测试

    使用示例:
    --------
    >>> client = MockLLMClient(response="这是一个测试回复")
    >>> client.complete([Message(role=Role.USER, content="你好")])
    '这是一个测试回复'
    """

    def __init__(self, response: str = "这是 Mock 客户端的默认回复"):
        """
        初始化 Mock 客户端

        参数:
        -----
        response: 固定返回的响应文本
        """
        self._response = response

    def complete(self, messages: MessageList) -> str:
        """返回预设的响应"""
        return self._response
