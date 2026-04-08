"""
可观测性管理器

学习要点:
=========
1. 结构化日志：上下文关联的日志记录，支持查询和过滤
2. 请求追踪：分布式追踪的 Span 模型，记录请求流转路径
3. 性能指标：计数器/量表/直方图，量化系统行为

设计模式:
=========
StructuredLogger: 日志的"写入口"，封装 LogStore
  - with_context() 返回预绑定上下文的 BoundLogger
  - 支持 trace_id/span_id 关联

Tracer: 追踪的"协调者"，封装 SpanStore
  - start_trace() 创建新的追踪
  - start_span() 返回上下文管理器，自动计时
  - 支持嵌套 Span

MetricsCollector: 指标的"收集器"，封装 MetricStore
  - increment/gauge/histogram 三种指标类型
  - timer() 上下文管理器自动计时
  - summary() 提供聚合统计

注意:
=====
- 当前设计为单线程场景（notebook/实验）
- Tracer 的 active_spans 栈不支持多线程
"""

import logging
import time
from datetime import datetime

from rogue_rabbit.contracts.log import (
    LogEntry,
    LogLevel,
    LogStore,
    MetricPoint,
    MetricStore,
    MetricType,
    Span,
    SpanStatus,
    SpanStore,
)

logger = logging.getLogger("log-manager")


# ========================================
# 结构化日志
# ========================================


class BoundLogger:
    """
    预绑定上下文的 Logger

    由 StructuredLogger.with_context() 创建。
    调用 debug/info/warning/error 时自动合并预绑定上下文。

    使用示例:
    --------
    >>> bound = structured_logger.with_context(session_id="sess1", user_id="user1")
    >>> bound.info("处理请求")  # 自动附加 session_id 和 user_id
    """

    def __init__(self, parent: "StructuredLogger", bound_context: dict):
        self._parent = parent
        self._bound_context = bound_context

    def debug(self, message: str, **context) -> None:
        """记录 DEBUG 日志"""
        merged = {**self._bound_context, **context}
        self._parent._log(LogLevel.DEBUG, message, merged)

    def info(self, message: str, **context) -> None:
        """记录 INFO 日志"""
        merged = {**self._bound_context, **context}
        self._parent._log(LogLevel.INFO, message, merged)

    def warning(self, message: str, **context) -> None:
        """记录 WARNING 日志"""
        merged = {**self._bound_context, **context}
        self._parent._log(LogLevel.WARNING, message, merged)

    def error(self, message: str, **context) -> None:
        """记录 ERROR 日志"""
        merged = {**self._bound_context, **context}
        self._parent._log(LogLevel.ERROR, message, merged)


class StructuredLogger:
    """
    结构化日志器

    职责:
    ----
    1. 提供标准的日志级别方法 (debug/info/warning/error)
    2. 自动附加模块名和时间戳
    3. 支持上下文注入（每次调用可携带额外 context）
    4. 写入 LogStore

    使用示例:
    --------
    >>> from rogue_rabbit.runtime import InMemoryLogStore
    >>>
    >>> store = InMemoryLogStore()
    >>> log = StructuredLogger(store=store, module="demo")
    >>>
    >>> log.info("用户登录", user_id="user1")
    >>> log.error("连接失败", host="localhost", port=5432)
    >>>
    >>> # 预绑定上下文
    >>> session_log = log.with_context(session_id="sess1")
    >>> session_log.info("处理请求")  # 自动附加 session_id
    """

    def __init__(self, store: LogStore, module: str = "app"):
        """
        初始化结构化日志器

        参数:
        -----
        store: 日志存储后端
        module: 模块名称
        """
        self._store = store
        self._module = module

    def debug(self, message: str, **context) -> None:
        """记录 DEBUG 日志"""
        self._log(LogLevel.DEBUG, message, context)

    def info(self, message: str, **context) -> None:
        """记录 INFO 日志"""
        self._log(LogLevel.INFO, message, context)

    def warning(self, message: str, **context) -> None:
        """记录 WARNING 日志"""
        self._log(LogLevel.WARNING, message, context)

    def error(self, message: str, **context) -> None:
        """记录 ERROR 日志"""
        self._log(LogLevel.ERROR, message, context)

    def with_context(self, **context) -> BoundLogger:
        """
        创建预绑定上下文的子 Logger

        参数:
        -----
        **context: 要绑定的上下文键值对

        返回:
        -----
        BoundLogger 实例
        """
        return BoundLogger(self, context)

    def _log(self, level: LogLevel, message: str, context: dict) -> None:
        """
        内部日志方法

        构建 LogEntry 并写入 LogStore
        """
        # 提取 trace_id 和 span_id
        trace_id = context.pop("trace_id", None)
        span_id = context.pop("span_id", None)

        entry = LogEntry(
            level=level,
            message=message,
            module=self._module,
            context=context,
            trace_id=trace_id,
            span_id=span_id,
        )
        self._store.append(entry)
        logger.debug(f"[StructuredLogger] {level.value}: {message}")


# ========================================
# 请求追踪
# ========================================


class SpanContext:
    """
    Span 上下文管理器

    由 Tracer.start_span() 返回，支持 with 语句。

    用法:
    -----
    >>> with tracer.start_span("operation") as span:
    ...     span.add_event("step1")
    ...     # 操作执行...
    ... # __exit__ 自动调用 span.finish() 并保存
    """

    def __init__(self, span: Span, tracer: "Tracer"):
        self._span = span
        self._tracer = tracer

    @property
    def span(self) -> Span:
        """获取 Span 对象"""
        return self._span

    def __enter__(self) -> Span:
        self._tracer._active_spans.append(self._span)
        return self._span

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._tracer._active_spans.pop()

        if exc_type is not None:
            self._span.status = SpanStatus.ERROR
            self._span.add_event("error", {"type": exc_type.__name__, "message": str(exc_val)})

        self._span.finish()
        self._tracer._store.save(self._span)
        return False


class Tracer:
    """
    请求追踪器

    职责:
    ----
    1. 创建和管理 trace
    2. 创建嵌套 span
    3. 自动记录时间
    4. 支持跨模块追踪（通过 trace_id 关联）

    使用示例:
    --------
    >>> from rogue_rabbit.runtime import InMemorySpanStore
    >>>
    >>> store = InMemorySpanStore()
    >>> tracer = Tracer(store=store)
    >>>
    >>> # 创建追踪
    >>> trace_id = tracer.start_trace("agent.request")
    >>>
    >>> # 创建 Span
    >>> with tracer.start_span("llm.call", trace_id=trace_id) as span:
    ...     span.add_event("request_sent")
    ...     # 调用 LLM...
    ...     span.add_event("response_received")
    >>>
    >>> # 查看追踪结果
    >>> spans = tracer.get_trace(trace_id)
    """

    def __init__(self, store: SpanStore):
        """
        初始化追踪器

        参数:
        -----
        store: Span 存储后端
        """
        self._store = store
        self._active_spans: list[Span] = []

    def start_trace(self, name: str, attributes: dict | None = None) -> str:
        """
        创建新的追踪

        创建根 Span 并保存，返回 trace_id。

        参数:
        -----
        name: 追踪名称
        attributes: 追踪属性

        返回:
        -----
        trace_id
        """
        root_span = Span(
            name=name,
            attributes=attributes or {},
        )
        self._store.save(root_span)
        logger.info(f"[Tracer] 开始追踪: {name} (trace={root_span.trace_id})")
        return root_span.trace_id

    def start_span(
        self,
        name: str,
        trace_id: str | None = None,
        parent_span_id: str | None = None,
        attributes: dict | None = None,
    ) -> SpanContext:
        """
        创建 Span

        参数:
        -----
        name: Span 名称
        trace_id: 所属追踪 ID（可选，默认使用当前活跃 trace）
        parent_span_id: 父 Span ID（可选，默认使用当前活跃 span）
        attributes: Span 属性

        返回:
        -----
        SpanContext（上下文管理器）
        """
        # 自动关联当前活跃的 span
        if trace_id is None and self._active_spans:
            trace_id = self._active_spans[0].trace_id

        if parent_span_id is None and self._active_spans:
            parent_span_id = self._active_spans[-1].span_id

        span = Span(
            trace_id=trace_id or "",
            parent_span_id=parent_span_id,
            name=name,
            attributes=attributes or {},
        )
        return SpanContext(span, self)

    def get_trace(self, trace_id: str) -> list[Span]:
        """
        获取一个 trace 的所有 span

        参数:
        -----
        trace_id: 追踪 ID

        返回:
        -----
        按 start_time 排序的 Span 列表
        """
        return self._store.find_by_trace(trace_id)

    def get_active_span(self) -> Span | None:
        """获取当前活跃的 Span"""
        if self._active_spans:
            return self._active_spans[-1]
        return None


# ========================================
# 性能指标
# ========================================


class TimerContext:
    """
    计时器上下文管理器

    由 MetricsCollector.timer() 返回。

    用法:
    -----
    >>> with metrics.timer("operation.duration", tags={"type": "api"}):
    ...     do_something()
    ... # 自动记录持续时间（毫秒）
    """

    def __init__(self, collector: "MetricsCollector", name: str, tags: dict | None):
        self._collector = collector
        self._name = name
        self._tags = tags
        self._start: float = 0.0

    def __enter__(self) -> "TimerContext":
        self._start = time.monotonic()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.monotonic() - self._start) * 1000
        self._collector._store.record(
            MetricPoint(
                name=self._name,
                metric_type=MetricType.HISTOGRAM,
                value=duration_ms,
                tags=self._tags or {},
                unit="ms",
            )
        )
        return False


class MetricsCollector:
    """
    性能指标收集器

    职责:
    ----
    1. 记录计数器（counter）：单调递增
    2. 记录量表（gauge）：当前值
    3. 记录直方图（histogram）：分布
    4. 提供查询和聚合

    使用示例:
    --------
    >>> from rogue_rabbit.runtime import InMemoryMetricStore
    >>>
    >>> store = InMemoryMetricStore()
    >>> metrics = MetricsCollector(store=store)
    >>>
    >>> # 计数器
    >>> metrics.increment("request.count")
    >>> metrics.increment("request.count", value=2, tags={"status": "200"})
    >>>
    >>> # 量表
    >>> metrics.gauge("active_connections", value=5)
    >>>
    >>> # 直方图
    >>> metrics.histogram("response.time", value=150.5, unit="ms")
    >>>
    >>> # 计时器
    >>> with metrics.timer("operation.duration"):
    ...     do_something()
    >>>
    >>> # 查询
    >>> summary = metrics.summary("request.count")
    """

    def __init__(self, store: MetricStore):
        """
        初始化指标收集器

        参数:
        -----
        store: 指标存储后端
        """
        self._store = store

    def increment(
        self, name: str, value: float = 1.0, tags: dict | None = None
    ) -> None:
        """
        递增计数器

        参数:
        -----
        name: 指标名称
        value: 递增量（默认 1）
        tags: 标签
        """
        self._store.record(
            MetricPoint(
                name=name,
                metric_type=MetricType.COUNTER,
                value=value,
                tags=tags or {},
                unit="count",
            )
        )

    def gauge(self, name: str, value: float, tags: dict | None = None) -> None:
        """
        记录量表值

        参数:
        -----
        name: 指标名称
        value: 当前值
        tags: 标签
        """
        self._store.record(
            MetricPoint(
                name=name,
                metric_type=MetricType.GAUGE,
                value=value,
                tags=tags or {},
                unit="value",
            )
        )

    def histogram(
        self,
        name: str,
        value: float,
        tags: dict | None = None,
        unit: str = "ms",
    ) -> None:
        """
        记录直方图数据点

        参数:
        -----
        name: 指标名称
        value: 数值
        tags: 标签
        unit: 单位
        """
        self._store.record(
            MetricPoint(
                name=name,
                metric_type=MetricType.HISTOGRAM,
                value=value,
                tags=tags or {},
                unit=unit,
            )
        )

    def timer(self, name: str, tags: dict | None = None) -> TimerContext:
        """
        创建计时器

        用法:
        -----
        >>> with metrics.timer("operation.duration"):
        ...     do_something()

        参数:
        -----
        name: 指标名称
        tags: 标签

        返回:
        -----
        TimerContext（上下文管理器）
        """
        return TimerContext(self, name, tags)

    def query(
        self,
        name: str | None = None,
        metric_type: MetricType | None = None,
        **kwargs,
    ) -> list[MetricPoint]:
        """查询指标"""
        return self._store.query(name=name, metric_type=metric_type, **kwargs)

    def summary(
        self,
        name: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> dict:
        """
        返回指标摘要

        参数:
        -----
        name: 指标名称
        start_time/end_time: 时间范围

        返回:
        -----
        {"count", "sum", "avg", "min", "max"} 字典
        """
        return {
            "count": self._store.aggregate(name, "count", start_time, end_time),
            "sum": self._store.aggregate(name, "sum", start_time, end_time),
            "avg": self._store.aggregate(name, "avg", start_time, end_time),
            "min": self._store.aggregate(name, "min", start_time, end_time),
            "max": self._store.aggregate(name, "max", start_time, end_time),
        }
