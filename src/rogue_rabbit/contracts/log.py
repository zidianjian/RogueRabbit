"""
可观测性协议定义

学习要点:
=========
1. 可观测性三支柱：日志(Logging)、追踪(Tracing)、指标(Metrics)
2. 结构化日志：带上下文的机器可读日志
3. 请求追踪：跟踪请求在系统中的流转路径
4. 性能指标：量化系统行为的数值数据

为什么需要可观测性?
==================
1. 调试：出问题时能快速定位原因
2. 性能分析：找出系统的瓶颈
3. 审计：记录谁在什么时候做了什么
4. 运维监控：实时了解系统健康状态

Logging vs Tracing vs Metrics:
------------------------------
- Logging: 离散的事件记录（"发生了什么"）
- Tracing: 请求在系统中的流转路径（"经过了哪里"）
- Metrics: 量化的性能数据（"有多快/多少次"）
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Protocol, runtime_checkable
from uuid import uuid4


def _short_id() -> str:
    """生成短 ID（uuid4 前 8 位）"""
    return uuid4().hex[:8]


# ========================================
# 枚举
# ========================================


class LogLevel(str, Enum):
    """
    日志级别

    DEBUG: 调试信息，开发时使用
    INFO: 常规信息，记录正常流程
    WARNING: 警告，可能的问题
    ERROR: 错误，需要关注的问题
    """

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class SpanStatus(str, Enum):
    """
    Span 状态

    OK: 正常完成
    ERROR: 执行出错
    TIMEOUT: 执行超时
    """

    OK = "ok"
    ERROR = "error"
    TIMEOUT = "timeout"


class MetricType(str, Enum):
    """
    指标类型

    COUNTER: 计数器，单调递增（如请求次数）
    GAUGE: 量表，可增可减（如当前连接数）
    HISTOGRAM: 直方图，记录分布（如响应时间）
    """

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


# ========================================
# 数据模型
# ========================================


@dataclass(frozen=True)
class LogEntry:
    """
    单条结构化日志

    属性:
    -----
    - entry_id: 唯一标识
    - timestamp: 时间戳
    - level: 日志级别
    - message: 日志消息
    - module: 来源模块（如 "session-manager", "authorizer"）
    - context: 结构化上下文（键值对）
    - span_id: 关联的 Span ID（可选）
    - trace_id: 关联的 Trace ID（可选）

    使用示例:
    --------
    >>> entry = LogEntry(
    ...     level=LogLevel.INFO,
    ...     message="用户登录",
    ...     module="auth",
    ...     context={"user_id": "user1"},
    ... )
    """

    entry_id: str = field(default_factory=_short_id)
    timestamp: datetime = field(default_factory=datetime.now)
    level: LogLevel = LogLevel.INFO
    message: str = ""
    module: str = "app"
    context: dict[str, Any] = field(default_factory=dict)
    span_id: str | None = None
    trace_id: str | None = None

    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "message": self.message,
            "module": self.module,
            "context": self.context,
            "span_id": self.span_id,
            "trace_id": self.trace_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LogEntry":
        """从字典反序列化"""
        return cls(
            entry_id=data.get("entry_id", _short_id()),
            timestamp=(
                datetime.fromisoformat(data["timestamp"])
                if "timestamp" in data
                else datetime.now()
            ),
            level=LogLevel(data.get("level", "info")),
            message=data.get("message", ""),
            module=data.get("module", "app"),
            context=data.get("context", {}),
            span_id=data.get("span_id"),
            trace_id=data.get("trace_id"),
        )


@dataclass(frozen=True)
class SpanEvent:
    """
    Span 内的事件

    属性:
    -----
    - name: 事件名称
    - timestamp: 事件时间
    - attributes: 事件属性

    使用示例:
    --------
    >>> event = SpanEvent(name="cache_hit", attributes={"key": "user:1"})
    """

    name: str
    timestamp: datetime = field(default_factory=datetime.now)
    attributes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            "name": self.name,
            "timestamp": self.timestamp.isoformat(),
            "attributes": self.attributes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SpanEvent":
        """从字典反序列化"""
        return cls(
            name=data["name"],
            timestamp=(
                datetime.fromisoformat(data["timestamp"])
                if "timestamp" in data
                else datetime.now()
            ),
            attributes=data.get("attributes", {}),
        )


@dataclass
class Span:
    """
    追踪跨度

    一个 Span 表示一次操作的开始和结束。
    多个 Span 通过 trace_id 组成一个完整的追踪。

    属性:
    -----
    - span_id: 唯一标识
    - trace_id: 所属追踪 ID
    - parent_span_id: 父 Span ID（可选，用于嵌套）
    - name: Span 名称（如 "session.chat", "authorizer.check"）
    - status: Span 状态
    - start_time: 开始时间
    - end_time: 结束时间（可选，未结束时为 None）
    - attributes: 结构化属性
    - events: Span 内事件列表

    使用示例:
    --------
    >>> span = Span(name="llm.call", trace_id="abc123")
    >>> span.add_event("request_sent")
    >>> # ... 执行操作 ...
    >>> span.finish()
    >>> print(f"耗时: {span.duration_ms}ms")
    """

    span_id: str = field(default_factory=_short_id)
    trace_id: str = field(default_factory=_short_id)
    parent_span_id: str | None = None
    name: str = ""
    status: SpanStatus = SpanStatus.OK
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[SpanEvent] = field(default_factory=list)

    @property
    def duration_ms(self) -> float | None:
        """计算持续时间（毫秒）"""
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time).total_seconds() * 1000

    def finish(self) -> None:
        """标记 Span 结束"""
        self.end_time = datetime.now()

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        """添加事件"""
        self.events.append(
            SpanEvent(name=name, attributes=attributes or {})
        )

    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "parent_span_id": self.parent_span_id,
            "name": self.name,
            "status": self.status.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "attributes": self.attributes,
            "events": [e.to_dict() for e in self.events],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Span":
        """从字典反序列化"""
        span = cls(
            span_id=data.get("span_id", _short_id()),
            trace_id=data.get("trace_id", _short_id()),
            parent_span_id=data.get("parent_span_id"),
            name=data.get("name", ""),
            status=SpanStatus(data.get("status", "ok")),
            start_time=(
                datetime.fromisoformat(data["start_time"])
                if "start_time" in data
                else datetime.now()
            ),
            end_time=(
                datetime.fromisoformat(data["end_time"])
                if data.get("end_time")
                else None
            ),
            attributes=data.get("attributes", {}),
            events=[
                SpanEvent.from_dict(e) for e in data.get("events", [])
            ],
        )
        return span


@dataclass(frozen=True)
class MetricPoint:
    """
    单个指标数据点

    属性:
    -----
    - name: 指标名称（如 "llm.call.count", "session.duration"）
    - metric_type: 指标类型
    - value: 数值
    - timestamp: 时间戳
    - tags: 标签（用于分组和过滤）
    - unit: 单位（如 "ms", "count", "bytes"）

    使用示例:
    --------
    >>> point = MetricPoint(
    ...     name="llm.call.duration",
    ...     metric_type=MetricType.HISTOGRAM,
    ...     value=150.5,
    ...     tags={"model": "gpt-4"},
    ...     unit="ms",
    ... )
    """

    name: str
    metric_type: MetricType = MetricType.COUNTER
    value: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    tags: dict[str, str] = field(default_factory=dict)
    unit: str = "count"

    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            "name": self.name,
            "metric_type": self.metric_type.value,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
            "unit": self.unit,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MetricPoint":
        """从字典反序列化"""
        return cls(
            name=data["name"],
            metric_type=MetricType(data.get("metric_type", "counter")),
            value=data.get("value", 0.0),
            timestamp=(
                datetime.fromisoformat(data["timestamp"])
                if "timestamp" in data
                else datetime.now()
            ),
            tags=data.get("tags", {}),
            unit=data.get("unit", "count"),
        )


# ========================================
# 存储协议
# ========================================


@runtime_checkable
class LogStore(Protocol):
    """
    日志存储协议

    方法说明:
    --------
    - append: 追加日志条目
    - query: 按条件查询日志
    - count: 统计日志数量
    - clear: 清空所有日志
    """

    def append(self, entry: LogEntry) -> None:
        """追加日志"""
        ...

    def query(
        self,
        level: LogLevel | None = None,
        module: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[LogEntry]:
        """查询日志"""
        ...

    def count(self, level: LogLevel | None = None) -> int:
        """统计日志数量"""
        ...

    def clear(self) -> None:
        """清空日志"""
        ...


@runtime_checkable
class SpanStore(Protocol):
    """
    Span 存储协议

    方法说明:
    --------
    - save: 保存或更新 Span
    - load: 加载 Span
    - find_by_trace: 按 trace_id 查找所有 Span
    - list_spans: 列出所有 Span
    - clear: 清空所有 Span
    """

    def save(self, span: Span) -> None:
        """保存 Span"""
        ...

    def load(self, span_id: str) -> Span | None:
        """加载 Span"""
        ...

    def find_by_trace(self, trace_id: str) -> list[Span]:
        """按 trace_id 查找 Span"""
        ...

    def list_spans(self, limit: int = 100) -> list[Span]:
        """列出所有 Span"""
        ...

    def clear(self) -> None:
        """清空 Span"""
        ...


@runtime_checkable
class MetricStore(Protocol):
    """
    指标存储协议

    方法说明:
    --------
    - record: 记录指标数据点
    - query: 按条件查询指标
    - aggregate: 聚合计算（sum/avg/min/max/count）
    - clear: 清空所有指标
    """

    def record(self, point: MetricPoint) -> None:
        """记录指标"""
        ...

    def query(
        self,
        name: str | None = None,
        metric_type: MetricType | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[MetricPoint]:
        """查询指标"""
        ...

    def aggregate(
        self,
        name: str,
        agg: str = "sum",
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> float | None:
        """
        聚合计算

        参数:
        -----
        - name: 指标名称
        - agg: 聚合方式（sum/avg/min/max/count）
        - start_time/end_time: 时间范围
        """
        ...

    def clear(self) -> None:
        """清空指标"""
        ...
