"""
实验 03: 系统提示词 (System Prompt)
===================================

学习目标:
--------
1. 理解系统提示词的作用
2. 学习如何使用系统提示词定义 AI 行为
3. 对比有无系统提示词的差异

核心概念:
--------
系统提示词（System Prompt）是特殊的消息：
- 角色是 SYSTEM，不是 USER 或 ASSISTANT
- 通常放在消息列表的最前面
- 用于定义 AI 的"人设"和行为准则

系统提示词的作用:
---------------
1. **角色定义**: "你是一个专业的程序员"
2. **行为约束**: "回答要简洁，不超过100字"
3. **输出格式**: "用 JSON 格式返回结果"
4. **安全边界**: "不要回答敏感问题"

运行方式:
--------
    python -m rogue_rabbit.experiments.03_system_prompt
"""

from rogue_rabbit.adapters import GLMClient
from rogue_rabbit.contracts import Message, Role


def demo_without_system_prompt() -> None:
    """演示：没有系统提示词的情况"""
    print("\n" + "-" * 50)
    print("[Demo 1] 没有系统提示词")
    print("-" * 50)

    client = GLMClient()

    # 直接问问题，没有系统提示词
    messages = [
        Message(role=Role.USER, content="什么是机器学习？")
    ]

    response = client.complete(messages)
    print(f"用户: 什么是机器学习？")
    print(f"AI: {response[:200]}...")


def demo_with_system_prompt() -> None:
    """演示：有系统提示词的情况"""
    print("\n" + "-" * 50)
    print("[Demo 2] 有系统提示词 - 简洁模式")
    print("-" * 50)

    client = GLMClient()

    # 添加系统提示词，要求简洁回答
    messages = [
        Message(role=Role.SYSTEM, content="你是一个简洁的助手。所有回答不超过20个字。"),
        Message(role=Role.USER, content="什么是机器学习？")
    ]

    response = client.complete(messages)
    print(f"系统提示: 你是一个简洁的助手。所有回答不超过20个字。")
    print(f"用户: 什么是机器学习？")
    print(f"AI: {response}")


def demo_role_play() -> None:
    """演示：角色扮演"""
    print("\n" + "-" * 50)
    print("[Demo 3] 角色扮演 - 资深程序员")
    print("-" * 50)

    client = GLMClient()

    # 系统提示词定义角色
    messages = [
        Message(
            role=Role.SYSTEM,
            content=(
                "你是一位有20年经验的资深程序员。"
                "回答问题时："
                "1. 使用专业术语"
                "2. 给出具体建议"
                "3. 提到可能的坑"
            )
        ),
        Message(role=Role.USER, content="如何学习编程？")
    ]

    response = client.complete(messages)
    print(f"系统提示: 你是一位有20年经验的资深程序员...")
    print(f"用户: 如何学习编程？")
    print(f"AI: {response[:300]}...")


def demo_output_format() -> None:
    """演示：输出格式控制"""
    print("\n" + "-" * 50)
    print("[Demo 4] 输出格式控制 - JSON")
    print("-" * 50)

    client = GLMClient()

    # 系统提示词要求 JSON 输出
    messages = [
        Message(
            role=Role.SYSTEM,
            content="你是一个数据分析助手。所有回答必须是有效的 JSON 格式。"
        ),
        Message(role=Role.USER, content="给我三个编程语言的名称和特点")
    ]

    response = client.complete(messages)
    print(f"系统提示: 你是一个数据分析助手。所有回答必须是有效的 JSON 格式。")
    print(f"用户: 给我三个编程语言的名称和特点")
    print(f"AI: {response}")


def main() -> None:
    """系统提示词学习示例"""

    print("=" * 50)
    print("实验 03: 系统提示词 (System Prompt)")
    print("=" * 50)

    print("\n系统提示词是 LLM 应用的核心配置：")
    print("- 定义 AI 的角色和行为")
    print("- 控制输出格式")
    print("- 设置安全边界")

    # 运行各种演示
    demo_without_system_prompt()
    demo_with_system_prompt()
    demo_role_play()
    demo_output_format()

    # ========================================
    # 总结
    # ========================================
    print("\n" + "=" * 50)
    print("学习总结:")
    print("-" * 50)
    print("1. 系统提示词是特殊的 SYSTEM 角色消息")
    print("2. 通常放在消息列表最前面")
    print("3. 作用: 角色定义、行为约束、输出格式、安全边界")
    print("4. 好的系统提示词能显著提升 LLM 输出质量")
    print("5. 实际应用中，系统提示词通常需要精心设计和迭代")
    print("=" * 50)


if __name__ == "__main__":
    main()
