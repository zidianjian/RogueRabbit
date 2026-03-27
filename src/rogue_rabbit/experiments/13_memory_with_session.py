"""
实验 13: 记忆与会话集成
=====================

学习目标:
--------
1. 理解 Session 和 Memory 的协作方式
2. 从对话中提取关键信息存入记忆
3. 对话时注入相关记忆增强上下文
4. 跨会话记忆保持

核心概念:
--------
- Session: 短期对话历史
- Memory: 长期知识存储
- 集成: Session 的对话信息可提取到 Memory，Memory 的内容可注入 Session

运行方式:
--------
    python -m rogue_rabbit.experiments.13_memory_with_session
"""

import logging
from pathlib import Path

from rogue_rabbit.adapters import GLMClient
from rogue_rabbit.contracts import Message, Role, Session, SessionMeta
from rogue_rabbit.core import MemoryManager, SessionManager
from rogue_rabbit.runtime import FileMemoryStore, FileSessionStore, InMemoryStore

logging.basicConfig(level=logging.INFO, format="%(name)s - %(message)s")
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)


def demo_extract_memory_from_session() -> None:
    """Demo 1: 从对话中提取记忆"""
    print("\n" + "=" * 60)
    print("Demo 1: 从对话中提取记忆")
    print("-" * 60)

    llm = GLMClient()
    memory_manager = MemoryManager(store=InMemoryStore(), llm_client=llm)
    session_manager = SessionManager(store=InMemoryStore(), llm_client=llm)

    # 创建会话和记忆空间
    session = session_manager.create(system_prompt="你是一个有帮助的助手。")
    memory = memory_manager.create(user_id="user1")
    print(f"[创建] 会话: {session.meta.session_id}, 记忆: user1")

    # 对话
    response = session_manager.chat(session.meta.session_id, "我叫张三，我是一名Python开发者")
    print(f"\n[用户] 我叫张三，我是一名Python开发者")
    print(f"[AI] {response[:80]}...")

    # 使用 LLM 提取记忆
    extract_prompt = f"""请从以下对话中提取关键信息，每条一行，格式为"类别: 内容"。

用户: 我叫张三，我是一名Python开发者
AI: {response}

提取结果:"""

    extraction = llm.complete([Message(role=Role.USER, content=extract_prompt)])
    print(f"\n[提取] LLM提取结果:")
    print(f"  {extraction}")

    # 手动添加提取的记忆
    memory_manager.add_memory("user1", "用户的名字叫张三", importance=0.9, category="fact")
    memory_manager.add_memory("user1", "用户是Python开发者", importance=0.8, category="fact")

    # 验证
    memory = memory_manager.get("user1")
    print(f"\n[记忆] 已保存 {len(memory.items)} 条记忆")
    for item in memory.items:
        print(f"  - [{item.category}] {item.content}")

    print("\n[完成] 提取记忆演示结束")


def demo_memory_injected_session() -> None:
    """Demo 2: 对话时注入相关记忆"""
    print("\n" + "=" * 60)
    print("Demo 2: 对话时注入相关记忆")
    print("-" * 60)

    llm = GLMClient()
    memory_manager = MemoryManager(store=InMemoryStore())
    session_manager = SessionManager(store=InMemoryStore(), llm_client=llm)

    # 预先存储记忆
    memory_manager.create(user_id="user2")
    memory_manager.add_memory("user2", "用户的名字叫李四", importance=0.9, category="fact")
    memory_manager.add_memory("user2", "用户喜欢简洁的回答", importance=0.8, category="preference")
    memory_manager.add_memory("user2", "用户是Java开发者", importance=0.7, category="fact")

    print("[记忆] 已存储 3 条记忆:")
    memory = memory_manager.get("user2")
    for item in memory.items:
        print(f"  - [{item.category}] {item.content}")

    # 获取相关记忆并注入上下文
    context = memory_manager.get_context_for_session("user2", "我叫什么名字？")
    print(f"\n[注入] 相关记忆上下文:")
    print(f"  {context}")

    # 创建带记忆的会话
    system_with_memory = f"你是一个有帮助的助手。\n\n{context}"
    session = session_manager.create(system_prompt=system_with_memory)

    response = session_manager.chat(session.meta.session_id, "我叫什么名字？")
    print(f"\n[用户] 我叫什么名字？")
    print(f"[AI] {response}")

    print("\n[完成] 记忆注入演示结束")


def demo_cross_session_memory() -> None:
    """Demo 3: 跨会话记忆保持"""
    print("\n" + "=" * 60)
    print("Demo 3: 跨会话记忆保持")
    print("-" * 60)

    import tempfile

    llm = GLMClient()

    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir)
        session_store = InMemoryStore()
        memory_store = InMemoryStore()

        # === 会话 1 ===
        print("[会话1] 第一次对话")
        session_manager1 = SessionManager(store=session_store, llm_client=llm)
        memory_manager = MemoryManager(store=memory_store)

        session1 = session_manager1.create(system_prompt="你是一个有帮助的助手。")
        memory_manager.create(user_id="user3")

        response1 = session_manager1.chat(session1.meta.session_id, "我喜欢使用Vim编辑器")
        print(f"  [用户] 我喜欢使用Vim编辑器")
        print(f"  [AI] {response1[:60]}...")

        # 存入记忆
        memory_manager.add_memory("user3", "用户喜欢使用Vim编辑器", importance=0.7, category="preference")
        print(f"  [记忆] 已保存: 用户喜欢Vim")

        # === 会话 2（新会话，但使用相同记忆） ===
        print("\n[会话2] 新会话，使用长期记忆")

        # 检索相关记忆
        memory_context = memory_manager.get_context_for_session("user3", "编辑器")
        print(f"  [检索] 找到相关记忆: {memory_context}")

        # 新会话注入记忆
        session_manager2 = SessionManager(store=session_store, llm_client=llm)
        session2 = session_manager2.create(
            system_prompt=f"你是一个有帮助的助手。\n\n{memory_context}"
        )

        response2 = session_manager2.chat(session2.meta.session_id, "推荐一个编辑器配置")
        print(f"  [用户] 推荐一个编辑器配置")
        print(f"  [AI] {response2[:80]}...")

        # 验证记忆持久化
        memory = memory_manager.get("user3")
        print(f"\n[验证] 记忆空间共 {len(memory.items)} 条记忆")
        for item in memory.items:
            print(f"  - [{item.category}] {item.content}")

    print("\n[完成] 跨会话记忆演示结束")


def demo_file_persistence() -> None:
    """Demo 4: 文件持久化记忆"""
    print("\n" + "=" * 60)
    print("Demo 4: 文件持久化记忆")
    print("-" * 60)

    import json

    store_path = Path(__file__).parent.parent.parent.parent / "tmp_memories"
    memory_store = FileMemoryStore(store_path)
    memory_manager = MemoryManager(store=memory_store)

    # 创建并添加记忆
    memory_manager.create(user_id="persistent_user")
    memory_manager.add_memory("persistent_user", "这是持久化的记忆", importance=0.8, category="test")

    # 查看文件
    files = list(store_path.glob("*.json"))
    print(f"[文件] 创建了 {len(files)} 个文件: {[f.name for f in files]}")

    # 读取文件内容
    if files:
        content = files[0].read_text(encoding="utf-8")
        data = json.loads(content)
        print(f"[内容] 用户: {data['meta']['user_id']}, 记忆数: {len(data['items'])}")

    # 从文件重新加载
    loaded = memory_manager.get("persistent_user")
    print(f"[加载] 用户: {loaded.meta.user_id}, 记忆数: {len(loaded.items)}")

    # 清理
    memory_store.clear()
    store_path.rmdir()
    print(f"[清理] 已删除临时目录")

    print("\n[完成] 文件持久化演示结束")


def main() -> None:
    """主函数"""
    print("=" * 60)
    print("实验 13: 记忆与会话集成")
    print("=" * 60)

    demo_extract_memory_from_session()
    demo_memory_injected_session()
    demo_cross_session_memory()
    demo_file_persistence()

    # 总结
    print("\n" + "=" * 60)
    print("学习总结")
    print("-" * 60)
    print("1. Session 负责短期对话，Memory 负责长期知识")
    print("2. 可以用 LLM 从对话中提取关键信息存入 Memory")
    print("3. 对话时检索相关记忆注入上下文，增强对话质量")
    print("4. 记忆跨会话保持，新会话可以引用历史信息")
    print("5. FileMemoryStore 支持记忆持久化")
    print("=" * 60)


if __name__ == "__main__":
    main()
