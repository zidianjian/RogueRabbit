"""
实验 12: 基础记忆操作
=====================

学习目标:
--------
1. 理解短期记忆 vs 长期记忆的区别
2. 掌握记忆的添加、检索、遗忘操作
3. 学会记忆分类和重要性管理
4. 体验记忆摘要生成

核心概念:
--------
- MemoryItem: 单条记忆（内容、重要性、分类）
- Memory: 记忆空间（一个用户的所有长期记忆）
- MemoryManager: 记忆管理器

Session vs Memory:
-----------------
- Session: 短期对话历史，随会话关闭而停止
- Memory: 长期知识存储，跨会话持久化

运行方式:
--------
    python -m rogue_rabbit.experiments.12_memory_basic
"""

import logging

from rogue_rabbit.contracts import MemoryItem, MemoryMeta
from rogue_rabbit.core import MemoryManager
from rogue_rabbit.runtime import InMemoryStore

logging.basicConfig(level=logging.INFO, format="%(name)s - %(message)s")
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)


def demo_memory_lifecycle() -> None:
    """Demo 1: 记忆生命周期"""
    print("\n" + "=" * 60)
    print("Demo 1: 记忆生命周期")
    print("-" * 60)

    manager = MemoryManager(store=InMemoryStore())

    # 创建记忆空间
    memory = manager.create(user_id="alice")
    print(f"[创建] 用户: alice, 记忆空间ID: {memory.meta.memory_id}")

    # 添加记忆
    manager.add_memory("alice", "用户的名字叫张三", importance=0.9, category="fact")
    manager.add_memory("alice", "用户喜欢Python编程", importance=0.8, category="preference")
    manager.add_memory("alice", "用户是软件工程师", importance=0.7, category="fact")

    # 查看记忆
    memory = manager.get("alice")
    print(f"[查看] 共 {len(memory.items)} 条记忆")
    for item in memory.items:
        print(f"  - [{item.category}] {item.content} (重要性: {item.importance})")

    # 搜索记忆
    results = manager.search("alice", "Python")
    print(f"\n[搜索] 关键词 'Python' 找到 {len(results)} 条:")
    for r in results:
        print(f"  - {r.content}")

    # 遗忘记忆
    removed = manager.forget("alice", "张三")
    print(f"\n[遗忘] 删除了 {removed} 条包含'张三'的记忆")

    memory = manager.get("alice")
    print(f"[验证] 剩余 {len(memory.items)} 条记忆")

    print("\n[完成] 记忆生命周期演示结束")


def demo_categories_and_importance() -> None:
    """Demo 2: 记忆分类和重要性"""
    print("\n" + "=" * 60)
    print("Demo 2: 记忆分类和重要性")
    print("-" * 60)

    manager = MemoryManager(store=InMemoryStore())
    manager.create(user_id="bob")

    # 添加不同分类的记忆
    memories = [
        ("用户喜欢简洁的回答", "preference", 0.8),
        ("用户的邮箱是 bob@example.com", "contact", 0.9),
        ("用户昨天问了关于Docker的问题", "event", 0.3),
        ("用户偏好深色主题", "preference", 0.7),
        ("用户是后端开发者", "fact", 0.6),
    ]

    for content, category, importance in memories:
        manager.add_memory("bob", content, importance=importance, category=category)

    # 按分类查看
    memory = manager.get("bob")
    print(f"[总数] {len(memory.items)} 条记忆")
    print(f"[分类] {memory.meta.categories}")

    # 按分类过滤
    preferences = memory.get_by_category("preference")
    print(f"\n[偏好] preference 分类 ({len(preferences)} 条):")
    for item in preferences:
        print(f"  - {item.content} (重要性: {item.importance})")

    # 按重要性过滤
    important = memory.get_important(threshold=0.7)
    print(f"\n[重要] 重要性 >= 0.7 ({len(important)} 条):")
    for item in important:
        print(f"  - [{item.category}] {item.content}")

    print("\n[完成] 分类和重要性演示结束")


def demo_memory_summary() -> None:
    """Demo 3: 记忆摘要生成"""
    print("\n" + "=" * 60)
    print("Demo 3: 记忆摘要生成")
    print("-" * 60)

    manager = MemoryManager(store=InMemoryStore())
    manager.create(user_id="charlie")

    # 添加记忆
    manager.add_memory("charlie", "用户是数据科学家", importance=0.8, category="fact")
    manager.add_memory("charlie", "用户熟悉Python和R", importance=0.7, category="skill")
    manager.add_memory("charlie", "用户正在学习机器学习", importance=0.6, category="status")

    # 简单摘要（无 LLM）
    summary = manager.summarize("charlie")
    print(f"[摘要] (无LLM)")
    print(summary)

    # LLM 摘要
    from rogue_rabbit.adapters import GLMClient

    manager_with_llm = MemoryManager(store=InMemoryStore(), llm_client=GLMClient())
    manager_with_llm.create(user_id="charlie2")
    manager_with_llm.add_memory("charlie2", "用户是前端开发者", category="fact")
    manager_with_llm.add_memory("charlie2", "用户熟悉React和Vue", category="skill")

    llm_summary = manager_with_llm.summarize("charlie2")
    print(f"\n[摘要] (LLM生成):")
    print(llm_summary)

    print("\n[完成] 记忆摘要演示结束")


def demo_memory_export() -> None:
    """Demo 4: 记忆导出导入"""
    print("\n" + "=" * 60)
    print("Demo 4: 记忆导出导入")
    print("-" * 60)

    import json

    manager = MemoryManager(store=InMemoryStore())
    manager.create(user_id="dave")
    manager.add_memory("dave", "用户喜欢咖啡", category="preference")
    manager.add_memory("dave", "用户在北京工作", category="fact")

    # 导出
    memory = manager.get("dave")
    data = memory.to_dict()
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    print(f"[导出] JSON ({len(json_str)} 字符):")
    print(json_str[:300] + "...")

    # 导入
    from rogue_rabbit.contracts import Memory

    restored = Memory.from_dict(data)
    print(f"\n[导入] 用户: {restored.meta.user_id}")
    print(f"[导入] 记忆数: {len(restored.items)}")
    assert restored.meta.user_id == memory.meta.user_id
    assert len(restored.items) == len(memory.items)
    print("[验证] 导出导入一致 [OK]")

    print("\n[完成] 导出导入演示结束")


def main() -> None:
    """主函数"""
    print("=" * 60)
    print("实验 12: 基础记忆操作")
    print("=" * 60)

    demo_memory_lifecycle()
    demo_categories_and_importance()
    demo_memory_summary()
    demo_memory_export()

    # 总结
    print("\n" + "=" * 60)
    print("学习总结")
    print("-" * 60)
    print("1. Memory 是跨会话的长期知识存储")
    print("2. MemoryItem 包含内容、重要性、分类")
    print("3. 支持关键词搜索、分类过滤、重要性排序")
    print("4. 记忆摘要可由 LLM 生成或简单格式化")
    print("5. 支持序列化导出导入")
    print("=" * 60)


if __name__ == "__main__":
    main()
