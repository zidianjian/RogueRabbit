"""
实验 20: 调试支持
================

学习目标:
--------
1. 理解可观测性三支柱联动：日志 + 追踪 + 指标
2. 掌握性能指标收集：计数器、量表、直方图
3. 学会完整调试场景：模拟 Agent 请求全流程

核心概念:
--------
- MetricsCollector: 性能指标收集器
- Counter: 单调递增计数（如请求次数）
- Gauge: 可增可减的当前值（如连接数）
- Histogram: 分布统计（如响应时间）
- Timer: 上下文管理器自动计时

运行方式:
--------
    python -m rogue_rabbit.experiments.20_debugging
"""

import logging
import time

from rogue_rabbit.contracts.log import (
    LogEntry,
    LogLevel,
    MetricPoint,
    MetricType,
    Span,
)
from rogue_rabbit.core.log_manager import MetricsCollector, StructuredLogger, Tracer
from rogue_rabbit.runtime.log_store import (
    InMemoryLogStore,
    InMemoryMetricStore,
    InMemorySpanStore,
)

logging.basicConfig(level=logging.INFO, format="%(name)s - %(message)s")


def demo_metrics_basic() -> None:
    """Demo 1: 性能指标基础"""
    print("\n" + "=" * 60)
    print("Demo 1: 性能指标基础")
    print("-" * 60)

    store = InMemoryMetricStore()
    metrics = MetricsCollector(store=store)

    # 计数器 (Counter)
    metrics.increment("request.count")
    metrics.increment("request.count")
    metrics.increment("request.count", tags={"status": "200"})
    metrics.increment("request.count", tags={"status": "500"})

    # 量表 (Gauge)
    metrics.gauge("active_connections", value=5)
    metrics.gauge("active_connections", value=3)

    # 直方图 (Histogram)
    metrics.histogram("response.time", value=150.5, unit="ms")
    metrics.histogram("response.time", value=200.3, unit="ms")
    metrics.histogram("response.time", value=80.1, unit="ms")

    # 查询指标
    print(f"\n[计数器] request.count:")
    for point in store.query(name="request.count"):
        print(f"  value={point.value} tags={point.tags}")

    print(f"\n[量表] active_connections:")
    for point in store.query(name="active_connections"):
        print(f"  value={point.value}")

    print(f"\n[直方图] response.time:")
    for point in store.query(name="response.time"):
        print(f"  value={point.value}{point.unit}")

    # 聚合
    total = store.aggregate("request.count", agg="sum")
    avg_time = store.aggregate("response.time", agg="avg")
    print(f"\n[聚合] 请求总数: {total}")
    print(f"[聚合] 平均响应时间: {avg_time:.1f}ms")

    print("\n[完成] 性能指标基础演示结束")


def demo_timer() -> None:
    """Demo 2: 计时器"""
    print("\n" + "=" * 60)
    print("Demo 2: 计时器（上下文管理器）")
    print("-" * 60)

    store = InMemoryMetricStore()
    metrics = MetricsCollector(store=store)

    # 使用 timer 自动计时
    with metrics.timer("db.query", tags={"table": "users"}):
        time.sleep(0.05)

    with metrics.timer("db.query", tags={"table": "orders"}):
        time.sleep(0.03)

    with metrics.timer("http.request", tags={"endpoint": "/api/chat"}):
        time.sleep(0.08)

    # 查看计时结果
    durations = store.query(name="db.query")
    print(f"\n[计时] db.query:")
    for point in durations:
        print(f"  {point.value:.1f}{point.unit} | tags={point.tags}")

    # 摘要
    summary = metrics.summary("db.query")
    print(f"\n[摘要] db.query:")
    for key, val in summary.items():
        if val is not None:
            print(f"  {key}: {val:.1f}")

    print("\n[要点] timer() 自动记录操作耗时")


def demo_summary() -> None:
    """Demo 3: 指标查询和聚合"""
    print("\n" + "=" * 60)
    print("Demo 3: 指标查询和聚合")
    print("-" * 60)

    store = InMemoryMetricStore()
    metrics = MetricsCollector(store=store)

    # 模拟多次 LLM 调用
    response_times = [120, 230, 150, 80, 310, 95, 180, 200, 110, 260]
    for t in response_times:
        metrics.histogram("llm.response_time", value=t, unit="ms")
        metrics.increment("llm.call_count")

    # 查询
    all_points = store.query(name="llm.response_time")
    print(f"\n[数据] LLM 响应时间数据点: {len(all_points)}")

    # 聚合
    print(f"\n[聚合] LLM 响应时间:")
    print(f"  调用次数: {store.aggregate('llm.call_count', agg='sum')}")
    print(f"  总时间:   {store.aggregate('llm.response_time', agg='sum'):.1f}ms")
    print(f"  平均时间: {store.aggregate('llm.response_time', agg='avg'):.1f}ms")
    print(f"  最快:     {store.aggregate('llm.response_time', agg='min'):.1f}ms")
    print(f"  最慢:     {store.aggregate('llm.response_time', agg='max'):.1f}ms")

    # Summary
    summary = metrics.summary("llm.response_time")
    print(f"\n[摘要] llm.response_time:")
    for key, val in summary.items():
        if val is not None:
            unit = "ms" if key != "count" else ""
            print(f"  {key}: {val:.1f}{unit}")

    print("\n[要点] summary() 一次性返回 count/sum/avg/min/max")


def demo_full_debugging() -> None:
    """Demo 4: 完整调试场景"""
    print("\n" + "=" * 60)
    print("Demo 4: 完整调试场景（日志 + 追踪 + 指标联动）")
    print("-" * 60)

    # 创建三个存储
    log_store = InMemoryLogStore()
    span_store = InMemorySpanStore()
    metric_store = InMemoryMetricStore()

    # 创建三个管理器
    log = StructuredLogger(store=log_store, module="agent")
    tracer = Tracer(store=span_store)
    metrics = MetricsCollector(store=metric_store)

    # === 模拟一个完整的 Agent 请求 ===
    trace_id = tracer.start_trace("agent.chat", attributes={"user_id": "user1"})

    # Step 1: 接收输入
    log.info("收到用户输入", trace_id=trace_id, input="帮我写一个 hello world")
    with metrics.timer("agent.input_processing"):
        time.sleep(0.01)

    # Step 2: 权限检查
    with tracer.start_span("permission.check", trace_id=trace_id) as span:
        log.info("检查权限", trace_id=trace_id, span_id=span.span_id, action="execute", tool="code_writer")
        time.sleep(0.02)
        span.add_event("checked", {"result": "allowed"})
        metrics.increment("permission.check.count", tags={"result": "allowed"})

    # Step 3: LLM 调用
    with tracer.start_span("llm.call", trace_id=trace_id) as llm_span:
        log.info("调用 LLM", trace_id=trace_id, span_id=llm_span.span_id, model="gpt-4")
        with metrics.timer("llm.call.duration", tags={"model": "gpt-4"}):
            time.sleep(0.06)
        llm_span.add_event("response_received", {"output_tokens": 80})
        metrics.increment("llm.call.count", tags={"model": "gpt-4"})
        metrics.histogram("llm.tokens.output", value=80, unit="tokens")

    # Step 4: 保存记忆
    with tracer.start_span("memory.save", trace_id=trace_id) as mem_span:
        log.info("保存对话记忆", trace_id=trace_id, span_id=mem_span.span_id)
        time.sleep(0.01)
        mem_span.add_event("saved", {"memory_id": "mem_abc"})
        metrics.increment("memory.save.count")

    log.info("请求处理完成", trace_id=trace_id)

    # === 事后分析 ===
    print(f"\n{'=' * 40}")
    print(f"事后分析 | trace_id={trace_id}")
    print(f"{'=' * 40}")

    # 调用链分析
    spans = tracer.get_trace(trace_id)
    print(f"\n[调用链] {len(spans)} 个 Span:")
    for s in spans:
        duration = f"{s.duration_ms:.1f}ms" if s.duration_ms else "N/A"
        indent = "  " if s.parent_span_id else ""
        print(f"  {indent}{s.name} | {duration} | {s.status.value}")

    # 日志上下文
    logs = log_store.query()
    print(f"\n[日志] {len(logs)} 条:")
    for entry in logs:
        ctx_parts = [f"{k}={v}" for k, v in entry.context.items()]
        ctx_str = " | ".join(ctx_parts[:3])
        print(f"  [{entry.level.value:7s}] {entry.message} ({ctx_str})")

    # 性能指标
    print(f"\n[指标]:")
    for name in ["permission.check.count", "llm.call.count", "memory.save.count"]:
        total = metric_store.aggregate(name, agg="sum")
        print(f"  {name}: {int(total) if total else 0}")

    llm_summary = metrics.summary("llm.call.duration")
    if llm_summary["avg"] is not None:
        print(f"  llm.call.duration avg: {llm_summary['avg']:.1f}ms")

    print("\n[要点] 日志 + 追踪 + 指标 三者联动，提供完整的调试视角")


def main() -> None:
    """主函数"""
    print("=" * 60)
    print("实验 20: 调试支持")
    print("=" * 60)

    demo_metrics_basic()
    demo_timer()
    demo_summary()
    demo_full_debugging()

    # 总结
    print("\n" + "=" * 60)
    print("学习总结")
    print("-" * 60)
    print("1. Counter: 单调递增计数（请求次数、错误次数）")
    print("2. Gauge: 可增可减的当前值（连接数、队列长度）")
    print("3. Histogram: 分布统计（响应时间、数据大小）")
    print("4. Timer: 上下文管理器自动计时")
    print("5. Summary: 一次性返回 count/sum/avg/min/max")
    print("6. 三支柱联动: trace_id 关联日志、追踪、指标")
    print("=" * 60)


if __name__ == "__main__":
    main()
