"""
实验 11: 会话持久化
===================

学习目标:
--------
1. 理解会话持久化的必要性
2. 掌握 Memory vs File 存储的区别
3. 学会会话恢复和导出导入

核心概念:
--------
- MemorySessionStore: 内存存储，进程重启后丢失
- FileSessionStore: 文件存储，持久化保存
- Session 序列化: to_dict() / from_dict()

使用场景:
--------
- Memory: 测试、临时会话
- File: 单机部署、长期保存

运行方式:
--------
    python -m rogue_rabbit.experiments.11_session_persistence
"""

import tempfile
from pathlib import Path

from rogue_rabbit.adapters import GLMClient
from rogue_rabbit.contracts import Session, SessionMeta, SessionStatus
from rogue_rabbit.core import SessionManager
from rogue_rabbit.runtime import FileSessionStore, MemorySessionStore


def demo_memory_store() -> None:
    """
    Demo 1: 内存存储

    演示内存存储的特点和限制
    """
    print("\n" + "=" * 60)
    print("Demo 1: 内存存储")
    print("-" * 60)

    # 创建内存存储
    store = MemorySessionStore()

    # 创建会话
    session = Session(
        meta=SessionMeta(metadata={"demo": "memory"}),
        system_prompt="你是助手",
    )
    session.add_message(
        __import__("rogue_rabbit.contracts", fromlist=["Message", "Role"]).Message(
            role=__import__("rogue_rabbit.contracts", fromlist=["Role"]).Role.USER,
            content="你好",
        )
    )

    # 保存
    store.save(session)
    print(f"[保存] 会话ID: {session.meta.session_id}")

    # 加载
    loaded = store.load(session.meta.session_id)
    print(f"[加载] 会话ID: {loaded.meta.session_id}")
    print(f"[加载] 消息数: {len(loaded.messages)}")

    # 列出
    sessions = store.list_sessions()
    print(f"[列表] 共 {len(sessions)} 个会话")

    # 删除
    result = store.delete(session.meta.session_id)
    print(f"[删除] 结果: {result}")

    # 验证删除
    loaded = store.load(session.meta.session_id)
    print(f"[验证] 加载结果: {loaded}")

    # 限制说明
    print("\n[注意] 内存存储的限制:")
    print("  - 进程重启后数据丢失")
    print("  - 无法跨进程共享")
    print("  - 适合测试和临时使用")

    print("\n[完成] 内存存储演示结束")


def demo_file_store() -> None:
    """
    Demo 2: 文件存储

    演示文件存储的持久化能力
    """
    print("\n" + "=" * 60)
    print("Demo 2: 文件存储")
    print("-" * 60)

    # 使用固定目录（便于查看文件内容）
    store_path = Path(__file__).parent.parent.parent.parent / "tmp_sessions"
    print(f"[初始化] 存储目录: {store_path}")

    # 创建文件存储
    store = FileSessionStore(store_path)

    # 创建并保存会话
    session = Session(
        meta=SessionMeta(metadata={"demo": "file"}),
        system_prompt="你是助手",
    )
    store.save(session)
    print(f"[保存] 会话ID: {session.meta.session_id}")

    # 查看文件
    files = list(store_path.glob("*.json"))
    print(f"[文件] 创建了 {len(files)} 个文件: {[f.name for f in files]}")

    # 加载会话
    loaded = store.load(session.meta.session_id)
    print(f"[加载] 会话ID: {loaded.meta.session_id}")

    # 修改并保存
    from rogue_rabbit.contracts import Message, Role

    loaded.add_message(Message(role=Role.USER, content="测试消息"))
    store.save(loaded)
    print(f"[更新] 添加了消息")

    # 重新加载验证
    reloaded = store.load(session.meta.session_id)
    print(f"[验证] 消息数: {len(reloaded.messages)}")

    # 读取文件内容展示
    json_file = store_path / f"{session.meta.session_id}.json"
    print(f"\n[文件内容] {json_file}:")
    print(json_file.read_text(encoding="utf-8")[:300] + "...")

    # 清理
    store.clear()
    store_path.rmdir()
    print(f"\n[清理] 已删除临时目录")

    print("\n[完成] 文件存储演示结束")


def demo_session_recovery() -> None:
    """
    Demo 3: 会话恢复

    演示从文件恢复会话并继续对话
    """
    print("\n" + "=" * 60)
    print("Demo 3: 会话恢复")
    print("-" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir)
        store = FileSessionStore(store_path)
        llm = GLMClient()

        # 第一次：创建会话并对话
        print("[阶段1] 创建会话并对话")
        manager1 = SessionManager(store=store, llm_client=llm)
        session1 = manager1.create(
            system_prompt="你是一个有帮助的助手。",
            metadata={"user": "demo"},
        )
        session_id = session1.meta.session_id
        print(f"[创建] 会话ID: {session_id}")

        response1 = manager1.chat(session_id, "我叫张三")
        print(f"[对话] 用户: 我叫张三")
        print(f"[对话] AI: {response1[:50]}...")

        # 模拟"断开连接"
        print("\n[断开] 模拟会话结束...")
        del manager1

        # 第二次：恢复会话并继续对话
        print("\n[阶段2] 恢复会话并继续")
        manager2 = SessionManager(store=store, llm_client=llm)

        # 获取历史会话
        session2 = manager2.get(session_id)
        if session2:
            print(f"[恢复] 会话ID: {session2.meta.session_id}")
            print(f"[历史] 共 {len(session2.messages)} 条消息")

            # 继续对话
            response2 = manager2.chat(session_id, "你还记得我的名字吗？")
            print(f"[对话] 用户: 你还记得我的名字吗？")
            print(f"[对话] AI: {response2[:80]}...")

            # 查看完整历史
            history = manager2.get_history(session_id)
            print(f"\n[历史] 完整对话:")
            for i, msg in enumerate(history):
                print(f"  {i + 1}. [{msg.role.value}]: {msg.content[:30]}...")

    print("\n[完成] 会话恢复演示结束")


def demo_session_export_import() -> None:
    """
    Demo 4: 会话导出导入

    演示会话的序列化和反序列化
    """
    print("\n" + "=" * 60)
    print("Demo 4: 会话导出导入")
    print("-" * 60)

    from rogue_rabbit.contracts import Message, Role
    import json

    # 创建会话
    session = Session(
        meta=SessionMeta(
            metadata={"user": "demo", "version": "1.0"},
        ),
        system_prompt="你是助手",
    )
    session.add_message(Message(role=Role.USER, content="你好"))
    session.add_message(Message(role=Role.ASSISTANT, content="你好！有什么可以帮助你的？"))

    print(f"[创建] 会话ID: {session.meta.session_id}")
    print(f"[状态] {session.meta.status.value}")

    # 导出为字典
    export_dict = session.to_dict()
    print(f"\n[导出] 字典格式:")
    print(f"  - session_id: {export_dict['meta']['session_id']}")
    print(f"  - status: {export_dict['meta']['status']}")
    print(f"  - messages: {len(export_dict['messages'])} 条")

    # 导出为 JSON 字符串
    json_str = json.dumps(export_dict, ensure_ascii=False, indent=2)
    print(f"\n[导出] JSON 格式 ({len(json_str)} 字符):")
    print(json_str[:200] + "...")

    # 从字典导入
    imported = Session.from_dict(export_dict)
    print(f"\n[导入] 会话ID: {imported.meta.session_id}")
    print(f"[导入] 消息数: {len(imported.messages)}")
    print(f"[导入] 状态: {imported.meta.status.value}")

    # 验证一致性
    assert imported.meta.session_id == session.meta.session_id
    assert len(imported.messages) == len(session.messages)
    print("\n[验证] 导出导入数据一致 [OK]")

    # 使用场景
    print("\n[场景] 导出导入的用途:")
    print("  - 备份会话数据")
    print("  - 跨系统迁移")
    print("  - 调试和分析")

    print("\n[完成] 导出导入演示结束")


def main() -> None:
    """主函数"""
    print("=" * 60)
    print("实验 11: 会话持久化")
    print("=" * 60)

    # 运行所有 Demo
    demo_memory_store()
    demo_file_store()
    demo_session_recovery()
    demo_session_export_import()

    # 总结
    print("\n" + "=" * 60)
    print("学习总结")
    print("-" * 60)
    print("1. MemorySessionStore: 内存存储，适合测试和临时使用")
    print("2. FileSessionStore: 文件存储，适合单机部署和长期保存")
    print("3. 会话可以通过 to_dict() / from_dict() 序列化")
    print("4. 持久化支持跨进程恢复会话")
    print("5. JSON 格式便于查看和调试")
    print("=" * 60)


if __name__ == "__main__":
    main()
