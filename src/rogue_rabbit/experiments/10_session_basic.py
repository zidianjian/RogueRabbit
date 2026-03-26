"""
实验 10: 基础会话管理
=====================

学习目标:
--------
1. 理解会话生命周期：创建、活跃、暂停、恢复、关闭
2. 掌握 SessionManager 的使用
3. 体验上下文窗口管理

核心概念:
--------
- Session: 会话对象，包含状态和历史
- SessionManager: 会话生命周期管理
- ContextWindow: 上下文窗口控制

Session vs Conversation:
-----------------------
- Conversation (实验02): 简单的消息列表封装
- Session: 完整的会话生命周期管理，支持持久化

运行方式:
--------
    python -m rogue_rabbit.experiments.10_session_basic
"""

from rogue_rabbit.adapters import GLMClient
from rogue_rabbit.contracts import Message, Role, Session, SessionMeta, SessionStatus
from rogue_rabbit.core import ContextWindowConfig, ContextWindowManager, SessionManager, TruncationStrategy
from rogue_rabbit.runtime import MemorySessionStore


def demo_session_lifecycle() -> None:
    """
    Demo 1: 会话生命周期

    演示会话的完整生命周期：
    创建 -> 活跃对话 -> 暂停 -> 恢复 -> 关闭
    """
    print("\n" + "=" * 60)
    print("Demo 1: 会话生命周期")
    print("-" * 60)

    # 创建会话管理器（使用内存存储）
    store = MemorySessionStore()
    llm = GLMClient()
    manager = SessionManager(store=store, llm_client=llm)

    # 1. 创建会话
    session = manager.create(
        system_prompt="你是一个有帮助的助手，回答要简洁。",
        metadata={"user": "demo", "topic": "lifecycle"},
    )
    print(f"[创建] 会话ID: {session.meta.session_id}")
    print(f"[状态] {session.meta.status.value}")

    # 2. 活跃对话
    response1 = manager.chat(session.meta.session_id, "你好，请介绍一下自己")
    print(f"\n[对话] 用户: 你好，请介绍一下自己")
    print(f"[对话] AI: {response1[:50]}...")

    # 3. 暂停会话
    manager.pause(session.meta.session_id)
    session = manager.get(session.meta.session_id)
    print(f"\n[暂停] 状态: {session.meta.status.value}")

    # 4. 恢复会话（通过 get 自动恢复）
    response2 = manager.chat(session.meta.session_id, "继续聊")
    print(f"\n[恢复] 用户: 继续聊")
    print(f"[恢复] AI: {response2[:50]}...")

    # 5. 关闭会话
    manager.close(session.meta.session_id)
    session = manager.get(session.meta.session_id)
    print(f"\n[关闭] 状态: {session.meta.status.value}")

    # 6. 尝试在关闭的会话中对话
    try:
        manager.chat(session.meta.session_id, "还能聊吗？")
    except ValueError as e:
        print(f"[异常] {e}")

    print("\n[完成] 会话生命周期演示结束")


def demo_multiple_sessions() -> None:
    """
    Demo 2: 多会话并行管理

    演示如何同时管理多个会话
    """
    print("\n" + "=" * 60)
    print("Demo 2: 多会话并行管理")
    print("-" * 60)

    store = MemorySessionStore()
    llm = GLMClient()
    manager = SessionManager(store=store, llm_client=llm)

    # 创建多个会话
    session1 = manager.create(
        system_prompt="你是一个技术专家，专注于 Python 编程。",
        metadata={"topic": "python"},
    )
    session2 = manager.create(
        system_prompt="你是一个历史学家，专注于中国古代历史。",
        metadata={"topic": "history"},
    )
    session3 = manager.create(
        system_prompt="你是一个厨师，专注于中餐烹饪。",
        metadata={"topic": "cooking"},
    )

    print(f"[创建] 会话1: {session1.meta.session_id} (Python专家)")
    print(f"[创建] 会话2: {session2.meta.session_id} (历史学家)")
    print(f"[创建] 会话3: {session3.meta.session_id} (厨师)")

    # 在不同会话中对话
    print("\n[对话] 会话1: 请推荐一个 Python Web 框架")
    response1 = manager.chat(session1.meta.session_id, "请推荐一个 Python Web 框架")
    print(f"[回答] {response1[:80]}...")

    print("\n[对话] 会话2: 唐朝持续了多少年？")
    response2 = manager.chat(session2.meta.session_id, "唐朝持续了多少年？")
    print(f"[回答] {response2[:80]}...")

    print("\n[对话] 会话3: 如何做红烧肉？")
    response3 = manager.chat(session3.meta.session_id, "如何做红烧肉？")
    print(f"[回答] {response3[:80]}...")

    # 列出所有会话
    sessions = manager.list_sessions()
    print(f"\n[列表] 共 {len(sessions)} 个会话:")
    for meta in sessions:
        print(f"  - {meta.session_id}: {meta.metadata.get('topic', 'unknown')}")

    print("\n[完成] 多会话管理演示结束")


def demo_context_window() -> None:
    """
    Demo 3: 上下文窗口管理

    演示长对话的上下文窗口管理
    """
    print("\n" + "=" * 60)
    print("Demo 3: 上下文窗口管理")
    print("-" * 60)

    # 创建不同策略的上下文窗口管理器
    configs = [
        ("KEEP_LAST (默认)", ContextWindowConfig(
            max_messages=5,
            strategy=TruncationStrategy.KEEP_LAST,
        )),
        ("KEEP_FIRST_LAST", ContextWindowConfig(
            max_messages=10,
            strategy=TruncationStrategy.KEEP_FIRST_LAST,
            keep_first=2,
            keep_last=3,
        )),
    ]

    # 创建模拟消息列表
    messages = [Message(role=Role.USER, content=f"消息 {i}") for i in range(10)]

    for name, config in configs:
        manager = ContextWindowManager(config=config)
        managed = manager.manage(messages)
        print(f"\n[策略] {name}")
        print(f"[原始] {len(messages)} 条消息")
        print(f"[截断后] {len(managed)} 条消息")
        print(f"[内容] {[m.content for m in managed]}")

    print("\n[完成] 上下文窗口管理演示结束")


def demo_integration() -> None:
    """
    Demo 4: 与 LLM 组件集成

    演示 Session 与 LLM 的完整集成
    """
    print("\n" + "=" * 60)
    print("Demo 4: 与 LLM 组件集成")
    print("-" * 60)

    # 创建带上下文窗口管理的会话管理器
    store = MemorySessionStore()
    llm = GLMClient()
    context_manager = ContextWindowManager(
        config=ContextWindowConfig(max_messages=10)
    )
    manager = SessionManager(
        store=store,
        llm_client=llm,
        context_window_manager=context_manager,
    )

    # 创建会话
    session = manager.create(
        system_prompt="你是一个有帮助的助手。"
    )
    print(f"[创建] 会话ID: {session.meta.session_id}")

    # 多轮对话
    questions = [
        "1+1等于几？",
        "2+2等于几？",
        "那1+1+1等于几？",
    ]

    for q in questions:
        response = manager.chat(session.meta.session_id, q)
        print(f"\n[用户] {q}")
        print(f"[AI] {response}")

    # 查看历史
    history = manager.get_history(session.meta.session_id)
    print(f"\n[历史] 共 {len(history)} 条消息")

    # 导出会话
    session = manager.get(session.meta.session_id)
    export_data = session.to_dict()
    print(f"\n[导出] 会话数据: {len(str(export_data))} 字符")

    print("\n[完成] LLM 集成演示结束")


def main() -> None:
    """主函数"""
    print("=" * 60)
    print("实验 10: 基础会话管理")
    print("=" * 60)

    # 运行所有 Demo
    demo_session_lifecycle()
    demo_multiple_sessions()
    demo_context_window()
    demo_integration()

    # 总结
    print("\n" + "=" * 60)
    print("学习总结")
    print("-" * 60)
    print("1. Session 是完整的会话对象，包含元数据和历史")
    print("2. SessionManager 负责会话生命周期管理")
    print("3. 会话状态: ACTIVE <-> IDLE -> CLOSED")
    print("4. ContextWindowManager 处理长对话截断")
    print("5. 多种截断策略: KEEP_LAST, KEEP_FIRST_LAST, SUMMARIZE")
    print("=" * 60)


if __name__ == "__main__":
    main()
