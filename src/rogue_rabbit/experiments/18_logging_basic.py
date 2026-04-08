"""
实验 18: 结构化日志
==================

学习目标:
--------
1. 理解结构化日志：带上下文的机器可读日志
2. 掌握日志查询：按级别、模块、时间范围过滤
3. 学会上下文绑定：BoundLogger 自动附加上下文

核心概念:
--------
- LogEntry: 单条结构化日志（级别 + 消息 + 模块 + 上下文）
- StructuredLogger: 日志写入器
- BoundLogger: 预绑定上下文的子 Logger
- LogStore: 日志存储后端（内存/文件）

运行方式:
--------
    python -m rogue_rabbit.experiments.18_logging_basic
"""

import logging
from pathlib import Path
import tempfile

from rogue_rabbit.contracts.log import LogEntry, LogLevel
from rogue_rabbit.core.log_manager import StructuredLogger
from rogue_rabbit.runtime.log_store import FileLogStore, InMemoryLogStore

logging.basicConfig(level=logging.INFO, format="%(name)s - %(message)s")


def demo_basic_logging() -> None:
    """Demo 1: 基础日志记录"""
    print("\n" + "=" * 60)
    print("Demo 1: 基础日志记录")
    print("-" * 60)

    store = InMemoryLogStore()
    log = StructuredLogger(store=store, module="demo")

    # 四个日志级别
    log.debug("调试信息，只在开发时使用")
    log.info("用户登录", user_id="user1", ip="192.168.1.1")
    log.warning("磁盘空间不足", usage="85%")
    log.error("数据库连接失败", host="localhost", port=5432)

    # 查看日志条目
    entries = store.query(limit=10)
    print(f"\n[日志] 共 {len(entries)} 条:")
    for entry in entries:
        ctx = f" | context={entry.context}" if entry.context else ""
        print(f"  [{entry.level.value:7s}] {entry.module}: {entry.message}{ctx}")

    print("\n[完成] 基础日志记录演示结束")


def demo_log_levels() -> None:
    """Demo 2: 日志级别过滤"""
    print("\n" + "=" * 60)
    print("Demo 2: 日志级别过滤")
    print("-" * 60)

    store = InMemoryLogStore()
    log = StructuredLogger(store=store, module="app")

    # 产生各级别日志
    log.debug("debug message 1")
    log.info("info message 1")
    log.info("info message 2")
    log.warning("warning message 1")
    log.error("error message 1")
    log.error("error message 2")

    # 按级别统计
    print(f"\n[统计] 总数: {store.count()}")
    for level in LogLevel:
        count = store.count(level=level)
        print(f"  {level.value:7s}: {count}")

    # 按级别查询
    errors = store.query(level=LogLevel.ERROR)
    print(f"\n[查询] ERROR 级别日志:")
    for entry in errors:
        print(f"  - {entry.message}")

    print("\n[要点] 结构化日志支持按级别精确过滤")


def demo_structured_context() -> None:
    """Demo 3: 结构化上下文"""
    print("\n" + "=" * 60)
    print("Demo 3: 结构化上下文")
    print("-" * 60)

    store = InMemoryLogStore()
    log = StructuredLogger(store=store, module="agent")

    # 带丰富上下文的日志
    log.info(
        "LLM 调用完成",
        model="gpt-4",
        tokens=150,
        duration_ms=230,
        status="success",
    )

    log.error(
        "工具调用失败",
        tool="file_reader",
        error_type="PermissionDenied",
        path="/etc/passwd",
        retry_count=3,
    )

    # 展示结构化日志的内容
    entries = store.query()
    for entry in entries:
        print(f"\n  消息: {entry.message}")
        print(f"  模块: {entry.module}")
        print(f"  级别: {entry.level.value}")
        print(f"  上下文:")
        for k, v in entry.context.items():
            print(f"    {k}: {v}")

    print("\n[要点] 上下文是键值对，便于机器解析和查询")


def demo_bound_logger() -> None:
    """Demo 4: 上下文绑定 (BoundLogger)"""
    print("\n" + "=" * 60)
    print("Demo 4: 上下文绑定 (BoundLogger)")
    print("-" * 60)

    store = InMemoryLogStore()
    log = StructuredLogger(store=store, module="session")

    # 创建预绑定 session_id 的子 Logger
    session_log = log.with_context(session_id="sess_abc123", user_id="user1")

    session_log.info("会话开始")
    session_log.info("处理用户输入", input_length=42)
    session_log.warning("上下文窗口接近上限", usage="90%")
    session_log.info("会话结束")

    # 验证所有日志都有 session_id
    entries = store.query()
    print(f"\n[验证] 所有日志条目:")
    for entry in entries:
        ctx = entry.context
        sid = ctx.get("session_id", "N/A")
        uid = ctx.get("user_id", "N/A")
        print(f"  [{entry.level.value:7s}] {entry.message} | session={sid} user={uid}")

    print("\n[要点] BoundLogger 自动附加上下文，避免重复传参")


def demo_file_log_store() -> None:
    """Demo 5: 文件日志持久化"""
    print("\n" + "=" * 60)
    print("Demo 5: 文件日志持久化")
    print("-" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir) / "logs"

        # 写入日志
        store = FileLogStore(log_dir)
        log = StructuredLogger(store=store, module="app")

        log.info("服务启动", version="0.7.0")
        log.info("处理请求", endpoint="/api/chat", method="POST")
        log.error("请求超时", endpoint="/api/chat", timeout=30)

        # 查看文件内容
        log_files = list(log_dir.glob("*.log"))
        print(f"\n[文件] 日志文件数: {len(log_files)}")
        for f in log_files:
            print(f"  {f.name}:")
            with open(f, "r", encoding="utf-8") as fh:
                for line in fh:
                    print(f"    {line.strip()}")

        # 重新加载查询
        store2 = FileLogStore(log_dir)
        entries = store2.query()
        print(f"\n[查询] 重新加载后日志数: {len(entries)}")
        for entry in entries:
            print(f"  [{entry.level.value:7s}] {entry.message}")

    print("\n[要点] 文件存储支持持久化，进程重启后可查询")


def main() -> None:
    """主函数"""
    print("=" * 60)
    print("实验 18: 结构化日志")
    print("=" * 60)

    demo_basic_logging()
    demo_log_levels()
    demo_structured_context()
    demo_bound_logger()
    demo_file_log_store()

    # 总结
    print("\n" + "=" * 60)
    print("学习总结")
    print("-" * 60)
    print("1. LogEntry = 级别 + 消息 + 模块 + 上下文（结构化键值对）")
    print("2. StructuredLogger: 日志写入器，支持四个级别")
    print("3. BoundLogger: 预绑定上下文，避免重复传参")
    print("4. LogStore: 支持 InMemory 和 File 两种后端")
    print("5. 查询过滤: 按级别、模块、时间范围")
    print("=" * 60)


if __name__ == "__main__":
    main()
