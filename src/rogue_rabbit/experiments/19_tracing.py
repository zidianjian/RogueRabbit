"""
实验 19: 请求追踪
================

学习目标:
--------
1. 理解请求追踪：跟踪请求在系统中的流转路径
2. 掌握 Span 模型：开始、结束、嵌套、事件
3. 学会跨模块追踪：同一 trace_id 贯穿多个操作

核心概念:
--------
- Span: 一次操作的开始和结束，包含名称、时间、状态
- Trace: 一组 Span 通过 trace_id 组成的调用链
- SpanEvent: Span 内的关键节点记录
- Tracer: 追踪管理器

运行方式:
--------
    python -m rogue_rabbit.experiments.19_tracing
"""

import logging
import time

from rogue_rabbit.contracts.log import Span, SpanStatus
from rogue_rabbit.core.log_manager import Tracer
from rogue_rabbit.runtime.log_store import InMemorySpanStore

logging.basicConfig(level=logging.INFO, format="%(name)s - %(message)s")


def demo_basic_trace() -> None:
    """Demo 1: 基础追踪"""
    print("\n" + "=" * 60)
    print("Demo 1: 基础追踪")
    print("-" * 60)

    store = InMemorySpanStore()
    tracer = Tracer(store=store)

    # 创建追踪
    trace_id = tracer.start_trace("agent.request", attributes={"user_id": "user1"})
    print(f"[追踪] 创建: trace_id={trace_id}")

    # 创建 Span（模拟 LLM 调用）
    with tracer.start_span("llm.call", trace_id=trace_id) as span:
        span.add_event("request_sent", {"model": "gpt-4", "tokens": 100})
        time.sleep(0.05)  # 模拟耗时
        span.add_event("response_received", {"tokens": 150})

    # 查看追踪结果
    spans = tracer.get_trace(trace_id)
    print(f"\n[结果] 追踪中的 Span 数: {len(spans)}")
    for s in spans:
        status = s.status.value
        duration = f"{s.duration_ms:.1f}ms" if s.duration_ms else "N/A"
        events = len(s.events)
        print(f"  {s.name} | status={status} | duration={duration} | events={events}")
        for evt in s.events:
            print(f"    event: {evt.name} {evt.attributes}")

    print("\n[完成] 基础追踪演示结束")


def demo_nested_spans() -> None:
    """Demo 2: 嵌套 Span"""
    print("\n" + "=" * 60)
    print("Demo 2: 嵌套 Span")
    print("-" * 60)

    store = InMemorySpanStore()
    tracer = Tracer(store=store)

    trace_id = tracer.start_trace("agent.chat", attributes={"user_id": "user1"})

    # 嵌套调用：agent.chat -> permission.check -> authorizer.check_policy
    with tracer.start_span("permission.check", trace_id=trace_id) as perm_span:
        perm_span.add_event("start_check", {"role": "user", "action": "execute"})
        time.sleep(0.02)

        with tracer.start_span("authorizer.check_policy") as policy_span:
            policy_span.add_event("policy_loaded", {"policy": "user-basic"})
            time.sleep(0.01)

    # 嵌套调用：agent.chat -> llm.call -> llm.tokenize + llm.inference
    with tracer.start_span("llm.call", trace_id=trace_id) as llm_span:
        llm_span.add_event("request_prepared")

        with tracer.start_span("llm.tokenize") as tok_span:
            time.sleep(0.01)
            tok_span.add_event("tokens_counted", {"count": 50})

        with tracer.start_span("llm.inference") as inf_span:
            time.sleep(0.03)
            inf_span.add_event("completed", {"output_tokens": 100})

    # 展示追踪树
    spans = tracer.get_trace(trace_id)
    print(f"\n[追踪树] trace_id={trace_id}")
    _print_trace_tree(spans)

    print("\n[要点] 嵌套 Span 通过 parent_span_id 形成调用树")


def demo_error_tracking() -> None:
    """Demo 3: 错误追踪"""
    print("\n" + "=" * 60)
    print("Demo 3: 错误追踪")
    print("-" * 60)

    store = InMemorySpanStore()
    tracer = Tracer(store=store)

    trace_id = tracer.start_trace("agent.request")

    # 正常操作
    with tracer.start_span("session.load", trace_id=trace_id):
        time.sleep(0.01)

    # 失败操作（模拟异常）
    try:
        with tracer.start_span("tool.execute", trace_id=trace_id) as span:
            span.add_event("tool_selected", {"tool": "file_reader"})
            raise FileNotFoundError("文件不存在: /secret/data.txt")
    except FileNotFoundError:
        pass  # 异常被 SpanContext.__exit__ 自动捕获

    # 查看结果
    spans = tracer.get_trace(trace_id)
    print(f"\n[结果] 追踪中的 Span:")
    for s in spans:
        duration = f"{s.duration_ms:.1f}ms" if s.duration_ms else "N/A"
        print(f"  {s.name} | status={s.status.value} | duration={duration}")
        for evt in s.events:
            print(f"    event: {evt.name} {evt.attributes}")

    print("\n[要点] 异常自动标记 status=ERROR 并记录错误事件")


def demo_trace_visualization() -> None:
    """Demo 4: 追踪可视化"""
    print("\n" + "=" * 60)
    print("Demo 4: 追踪可视化")
    print("-" * 60)

    store = InMemorySpanStore()
    tracer = Tracer(store=store)

    # 模拟一个完整的 Agent 请求
    trace_id = tracer.start_trace(
        "agent.complete_request", attributes={"user_id": "user1", "input": "帮我写一个函数"}
    )

    # Step 1: 权限检查
    with tracer.start_span("permission.check", trace_id=trace_id) as span:
        time.sleep(0.01)
        span.add_event("checked", {"result": "allowed"})

    # Step 2: LLM 调用
    with tracer.start_span("llm.generate", trace_id=trace_id) as llm_span:
        llm_span.add_event("request_sent", {"model": "gpt-4", "tokens": 30})

        with tracer.start_span("llm.api_call") as api_span:
            time.sleep(0.05)
            api_span.add_event("response_received")

        llm_span.add_event("response_parsed", {"output_tokens": 80})

    # Step 3: 保存记忆
    with tracer.start_span("memory.save", trace_id=trace_id) as mem_span:
        time.sleep(0.01)
        mem_span.add_event("saved", {"memory_id": "mem_123"})

    # 展示追踪摘要
    spans = tracer.get_trace(trace_id)
    total_duration = spans[0].duration_ms  # 根 Span 的持续时间

    print(f"\n[追踪摘要] trace_id={trace_id}")
    print(f"  总 Span 数: {len(spans)}")
    print(f"  总耗时: {total_duration:.1f}ms" if total_duration else "  总耗时: N/A")
    print(f"\n[调用链]:")
    for s in spans:
        indent = "  " if s.parent_span_id else ""
        duration = f"{s.duration_ms:.1f}ms" if s.duration_ms else "N/A"
        parent = f"parent={s.parent_span_id[:8]}... " if s.parent_span_id else ""
        print(f"  {indent}{s.name} ({s.span_id}) | {parent}duration={duration}")

    # 按耗时排序
    print(f"\n[耗时排序]:")
    timed_spans = [s for s in spans if s.duration_ms is not None]
    for s in sorted(timed_spans, key=lambda x: x.duration_ms or 0, reverse=True):
        print(f"  {s.duration_ms:7.1f}ms  {s.name}")

    print("\n[要点] 通过追踪数据可以分析调用链和性能瓶颈")


def _print_trace_tree(spans: list[Span]) -> None:
    """打印追踪树"""
    span_map = {s.span_id: s for s in spans}
    children_map: dict[str | None, list[Span]] = {}
    for s in spans:
        pid = s.parent_span_id
        if pid not in children_map:
            children_map[pid] = []
        children_map[pid].append(s)

    def _print_node(span: Span, indent: str = "") -> None:
        duration = f"{span.duration_ms:.1f}ms" if span.duration_ms else "N/A"
        print(f"{indent}{span.name} ({span.status.value}) [{duration}]")
        for child in children_map.get(span.span_id, []):
            _print_node(child, indent + "  ")

    # 找到根 Span
    roots = children_map.get(None, [])
    for root in roots:
        _print_node(root)


def main() -> None:
    """主函数"""
    print("=" * 60)
    print("实验 19: 请求追踪")
    print("=" * 60)

    demo_basic_trace()
    demo_nested_spans()
    demo_error_tracking()
    demo_trace_visualization()

    # 总结
    print("\n" + "=" * 60)
    print("学习总结")
    print("-" * 60)
    print("1. Span = 一次操作（名称 + 开始/结束时间 + 状态）")
    print("2. Trace = 一组 Span 通过 trace_id 组成的调用链")
    print("3. 嵌套 Span: 通过 parent_span_id 形成树状调用关系")
    print("4. SpanEvent: 记录 Span 内的关键节点")
    print("5. 错误追踪: 异常自动标记 status=ERROR")
    print("6. Tracer: 支持 start_trace / start_span / get_trace")
    print("=" * 60)


if __name__ == "__main__":
    main()
