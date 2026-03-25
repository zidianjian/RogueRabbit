"""
实验 01: 最简单的 LLM 调用
==========================

学习目标:
--------
1. 理解 Message 是什么
2. 理解 LLM 客户端如何工作
3. 完成第一次 LLM 调用

前置知识:
--------
- 确保已配置 .env 文件中的 ZHIPU_API_KEY
- 或者在下方代码中直接传入 api_key

运行方式:
--------
    python -m rogue_rabbit.experiments.01_hello_llm
"""

from rogue_rabbit.adapters import GLMClient
from rogue_rabbit.contracts import Message, Role


def main() -> None:
    """最简单的 LLM 调用示例"""

    print("=" * 50)
    print("实验 01: Hello LLM")
    print("=" * 50)

    # ========================================
    # Step 1: 创建消息
    # ========================================
    # Message 是 LLM 交互的基本单位
    # - role: 谁说的（USER = 用户）
    # - content: 说了什么
    messages = [
        Message(role=Role.USER, content="Hello! 你是谁？请用一句话介绍自己。")
    ]

    print(f"\n>> 发送消息:")
    for msg in messages:
        print(f"   {msg}")

    # ========================================
    # Step 2: 创建 LLM 客户端
    # ========================================
    # GLMClient 会自动从 .env 文件读取 ZHIPU_API_KEY
    # 默认使用 glm-4-flash 模型（性价比高）
    client = GLMClient()

    # ========================================
    # Step 3: 调用 LLM
    # ========================================
    # complete() 方法：
    # 1. 将我们的 Message 格式转换成 API 格式
    # 2. 调用 GLM API
    # 3. 返回 AI 的回复文本
    print("\n>> 等待 AI 回复...")
    response = client.complete(messages)

    print(f"\n>> AI 回复:")
    print(f"   {response}")

    # ========================================
    # 总结
    # ========================================
    print("\n" + "=" * 50)
    print("学习总结:")
    print("-" * 50)
    print("1. Message = 角色 + 内容，是 LLM 交互的基本单位")
    print("2. LLMClient 定义了统一的调用接口")
    print("3. GLMClient 是具体的实现，封装了智谱 AI API")
    print("4. 一次调用 = 创建消息 -> 创建客户端 -> 调用 complete")
    print("=" * 50)


if __name__ == "__main__":
    main()
