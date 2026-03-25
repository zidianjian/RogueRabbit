"""
实验 02: 多轮对话
=================

学习目标:
--------
1. 理解对话上下文（Context）的概念
2. 学习如何维护消息历史
3. 实现一个简单的多轮对话循环

核心概念:
--------
多轮对话的本质是把所有历史消息都发给 LLM：
- LLM 本身是"无状态"的
- 每次调用都需要完整的对话历史
- 由调用方负责维护消息列表

运行方式:
--------
    python -m rogue_rabbit.experiments.02_conversation
"""

from rogue_rabbit.adapters import GLMClient
from rogue_rabbit.contracts import LLMClient, Message, Role


class Conversation:
    """
    对话管理器 - 封装多轮对话的复杂性

    职责:
    ----
    1. 维护消息历史
    2. 提供简单的对话接口
    3. 自动添加 AI 回复到历史

    为什么需要这个类?
    ----------------
    - 封装"维护消息列表"的重复逻辑
    - 让调用方专注于业务，而不是消息管理
    - 后续可以扩展更多功能（如消息截断、持久化）
    """

    def __init__(self, client: LLMClient, system_prompt: str | None = None):
        """
        初始化对话

        参数:
        -----
        client: LLM 客户端
        system_prompt: 系统提示词（可选），用于定义 AI 的行为
        """
        self._client = client
        self._messages: list[Message] = []

        # 如果有系统提示词，添加到消息列表开头
        if system_prompt:
            self._messages.append(
                Message(role=Role.SYSTEM, content=system_prompt)
            )

    def say(self, user_input: str) -> str:
        """
        发送用户消息并获取 AI 回复

        流程:
        ----
        1. 将用户消息添加到历史
        2. 调用 LLM（发送所有历史消息）
        3. 将 AI 回复添加到历史
        4. 返回 AI 回复
        """
        # 1. 添加用户消息
        self._messages.append(
            Message(role=Role.USER, content=user_input)
        )

        # 2. 调用 LLM
        ai_response = self._client.complete(self._messages)

        # 3. 添加 AI 回复
        self._messages.append(
            Message(role=Role.ASSISTANT, content=ai_response)
        )

        # 4. 返回回复
        return ai_response

    @property
    def history(self) -> list[Message]:
        """获取消息历史（只读）"""
        return self._messages.copy()

    def clear(self) -> None:
        """清空对话历史"""
        self._messages.clear()


def main() -> None:
    """多轮对话示例"""

    print("=" * 50)
    print("实验 02: 多轮对话")
    print("=" * 50)

    # 创建客户端和对话管理器
    client = GLMClient()
    conversation = Conversation(
        client,
        system_prompt="你是一个有帮助的助手，回答要简洁。"
    )

    print("\n[Chat] 开始对话（输入 'quit' 退出）\n")

    while True:
        # 获取用户输入
        user_input = input("👤 你: ").strip()

        if not user_input:
            continue

        if user_input.lower() == "quit":
            print("\n[End] 对话结束")
            break

        # 发送消息并获取回复
        response = conversation.say(user_input)
        print(f"[AI] {response}\n")

    # 显示对话历史
    print("\n" + "=" * 50)
    print("[History] 完整对话历史:")
    print("-" * 50)
    for msg in conversation.history:
        print(f"   {msg}")

    # ========================================
    # 总结
    # ========================================
    print("\n" + "=" * 50)
    print("学习总结:")
    print("-" * 50)
    print("1. LLM 是无状态的，每次调用需要完整历史")
    print("2. Conversation 类封装了消息历史管理")
    print("3. 消息顺序: SYSTEM → USER → ASSISTANT → USER → ...")
    print("4. 后续可以扩展: 消息截断、持久化、上下文窗口管理")
    print("=" * 50)


if __name__ == "__main__":
    main()
