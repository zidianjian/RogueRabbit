"""
可观测性存储后端实现

学习要点:
=========
1. 三种存储类型：日志存储、Span 存储、指标存储
2. 每种类型都有内存和文件两种实现
3. 不同查询模式：日志按级别/时间、Span 按 trace_id、指标按名称聚合

实现对比:
=========
内存存储:
- 优点：速度快，实现简单
- 缺点：进程重启后数据丢失
- 适用：测试、开发

文件存储:
- 优点：数据持久化
- 缺点：IO 开销
- 适用：单机部署、调试分析
"""

import json
import logging
from datetime import datetime
from pathlib import Path

from rogue_rabbit.contracts.log import (
    LogEntry,
    LogLevel,
    MetricPoint,
    MetricType,
    Span,
)

logger = logging.getLogger("log-store")


# ========================================
# 日志存储
# ========================================


class InMemoryLogStore:
    """
    内存日志存储

    特点:
    -----
    - 日志条目存储在内存列表中
    - 支持按级别、模块、时间范围查询
    - 进程重启后数据丢失

    使用示例:
    --------
    >>> store = InMemoryLogStore()
    >>> store.append(LogEntry(level=LogLevel.INFO, message="启动完成"))
    >>> entries = store.query(level=LogLevel.INFO)
    """

    def __init__(self):
        self._entries: list[LogEntry] = []

    def append(self, entry: LogEntry) -> None:
        """追加日志"""
        self._entries.append(entry)
        logger.debug(f"[InMemoryLogStore] 追加日志: {entry.level.value} - {entry.message[:50]}")

    def query(
        self,
        level: LogLevel | None = None,
        module: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[LogEntry]:
        """查询日志"""
        results = self._entries

        if level is not None:
            results = [e for e in results if e.level == level]
        if module is not None:
            results = [e for e in results if e.module == module]
        if start_time is not None:
            results = [e for e in results if e.timestamp >= start_time]
        if end_time is not None:
            results = [e for e in results if e.timestamp <= end_time]

        # 按时间倒序，取最新的
        results = sorted(results, key=lambda e: e.timestamp, reverse=True)
        return results[:limit]

    def count(self, level: LogLevel | None = None) -> int:
        """统计日志数量"""
        if level is None:
            return len(self._entries)
        return sum(1 for e in self._entries if e.level == level)

    def clear(self) -> None:
        """清空日志"""
        self._entries.clear()
        logger.debug("[InMemoryLogStore] 清空日志")


class FileLogStore:
    """
    文件日志存储

    文件结构:
    --------
    logs/
    ├── 2024-01-15.log   # 按日期分文件（JSONL 格式）
    └── ...

    每行一个 JSON 对象，方便追加和按行读取。

    使用示例:
    --------
    >>> from pathlib import Path
    >>> store = FileLogStore(Path("./logs"))
    >>> store.append(LogEntry(level=LogLevel.INFO, message="启动完成"))
    """

    def __init__(self, base_path: Path):
        """
        初始化文件日志存储

        参数:
        -----
        base_path: 日志文件存储目录
        """
        self._base_path = base_path
        self._base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"[FileLogStore] 初始化日志目录: {base_path}")

    def _get_file_path(self, date: datetime) -> Path:
        """获取日期对应的日志文件路径"""
        return self._base_path / f"{date.strftime('%Y-%m-%d')}.log"

    def append(self, entry: LogEntry) -> None:
        """追加日志到文件"""
        file_path = self._get_file_path(entry.timestamp)
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")
        logger.debug(f"[FileLogStore] 追加日志: {entry.level.value}")

    def query(
        self,
        level: LogLevel | None = None,
        module: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[LogEntry]:
        """查询日志"""
        entries: list[LogEntry] = []

        # 确定要读取的文件范围
        files = sorted(self._base_path.glob("*.log"), reverse=True)
        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            entry = LogEntry.from_dict(json.loads(line))
                            # 过滤
                            if level and entry.level != level:
                                continue
                            if module and entry.module != module:
                                continue
                            if start_time and entry.timestamp < start_time:
                                continue
                            if end_time and entry.timestamp > end_time:
                                continue
                            entries.append(entry)
                        except (json.JSONDecodeError, KeyError):
                            continue
            except Exception as e:
                logger.warning(f"[FileLogStore] 读取日志文件失败 {file_path}: {e}")

        # 按时间倒序
        entries.sort(key=lambda e: e.timestamp, reverse=True)
        return entries[:limit]

    def count(self, level: LogLevel | None = None) -> int:
        """统计日志数量"""
        return len(self.query(level=level, limit=999999))

    def clear(self) -> None:
        """清空所有日志文件"""
        for file_path in self._base_path.glob("*.log"):
            file_path.unlink()
        logger.debug("[FileLogStore] 清空所有日志文件")


# ========================================
# Span 存储
# ========================================


class InMemorySpanStore:
    """
    内存 Span 存储

    特点:
    -----
    - 使用字典存储 Span，按 span_id 索引
    - 维护 trace_id -> span_id 的索引，加速按 trace 查询
    - 支持嵌套 Span（通过 parent_span_id）

    使用示例:
    --------
    >>> store = InMemorySpanStore()
    >>> span = Span(name="operation", trace_id="trace1")
    >>> store.save(span)
    >>> spans = store.find_by_trace("trace1")
    """

    def __init__(self):
        self._spans: dict[str, Span] = {}
        self._trace_index: dict[str, list[str]] = {}

    def save(self, span: Span) -> None:
        """保存 Span"""
        self._spans[span.span_id] = span

        # 维护 trace 索引
        if span.trace_id not in self._trace_index:
            self._trace_index[span.trace_id] = []
        if span.span_id not in self._trace_index[span.trace_id]:
            self._trace_index[span.trace_id].append(span.span_id)

        logger.debug(f"[InMemorySpanStore] 保存 Span: {span.name} ({span.span_id})")

    def load(self, span_id: str) -> Span | None:
        """加载 Span"""
        return self._spans.get(span_id)

    def find_by_trace(self, trace_id: str) -> list[Span]:
        """按 trace_id 查找所有 Span"""
        span_ids = self._trace_index.get(trace_id, [])
        spans = [self._spans[sid] for sid in span_ids if sid in self._spans]
        # 按开始时间排序
        return sorted(spans, key=lambda s: s.start_time)

    def list_spans(self, limit: int = 100) -> list[Span]:
        """列出所有 Span"""
        spans = sorted(self._spans.values(), key=lambda s: s.start_time, reverse=True)
        return spans[:limit]

    def clear(self) -> None:
        """清空 Span"""
        self._spans.clear()
        self._trace_index.clear()
        logger.debug("[InMemorySpanStore] 清空 Span")


class FileSpanStore:
    """
    文件 Span 存储

    文件结构:
    --------
    spans/
    ├── <trace_id>/
    │   ├── <span_id>.json
    │   └── ...
    └── ...

    使用示例:
    --------
    >>> from pathlib import Path
    >>> store = FileSpanStore(Path("./spans"))
    >>> span = Span(name="operation", trace_id="trace1")
    >>> store.save(span)
    """

    def __init__(self, base_path: Path):
        """
        初始化文件 Span 存储

        参数:
        -----
        base_path: Span 文件存储目录
        """
        self._base_path = base_path
        self._base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"[FileSpanStore] 初始化 Span 目录: {base_path}")

    def save(self, span: Span) -> None:
        """保存 Span 到文件"""
        trace_dir = self._base_path / span.trace_id
        trace_dir.mkdir(parents=True, exist_ok=True)
        file_path = trace_dir / f"{span.span_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(span.to_dict(), f, ensure_ascii=False, indent=2)
        logger.debug(f"[FileSpanStore] 保存 Span: {span.name} ({span.span_id})")

    def load(self, span_id: str) -> Span | None:
        """加载 Span"""
        for trace_dir in self._base_path.iterdir():
            if not trace_dir.is_dir():
                continue
            file_path = trace_dir / f"{span_id}.json"
            if file_path.exists():
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        return Span.from_dict(json.load(f))
                except Exception as e:
                    logger.error(f"[FileSpanStore] 加载 Span 失败 {span_id}: {e}")
                    return None
        return None

    def find_by_trace(self, trace_id: str) -> list[Span]:
        """按 trace_id 查找所有 Span"""
        trace_dir = self._base_path / trace_id
        if not trace_dir.exists():
            return []

        spans: list[Span] = []
        for file_path in trace_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    spans.append(Span.from_dict(json.load(f)))
            except Exception as e:
                logger.warning(f"[FileSpanStore] 加载 Span 失败 {file_path}: {e}")

        return sorted(spans, key=lambda s: s.start_time)

    def list_spans(self, limit: int = 100) -> list[Span]:
        """列出所有 Span"""
        spans: list[Span] = []
        for trace_dir in self._base_path.iterdir():
            if not trace_dir.is_dir():
                continue
            for file_path in trace_dir.glob("*.json"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        spans.append(Span.from_dict(json.load(f)))
                except Exception as e:
                    logger.warning(f"[FileSpanStore] 加载 Span 失败 {file_path}: {e}")

        spans.sort(key=lambda s: s.start_time, reverse=True)
        return spans[:limit]

    def clear(self) -> None:
        """清空所有 Span 文件"""
        import shutil

        for trace_dir in self._base_path.iterdir():
            if trace_dir.is_dir():
                shutil.rmtree(trace_dir)
        logger.debug("[FileSpanStore] 清空所有 Span 文件")


# ========================================
# 指标存储
# ========================================


class InMemoryMetricStore:
    """
    内存指标存储

    特点:
    -----
    - 数据点存储在内存列表中
    - 维护 name -> 索引的映射，加速按名称查询
    - 支持聚合计算（sum/avg/min/max/count）

    使用示例:
    --------
    >>> store = InMemoryMetricStore()
    >>> store.record(MetricPoint(name="req.count", value=1))
    >>> result = store.aggregate("req.count", agg="sum")
    """

    def __init__(self):
        self._points: list[MetricPoint] = []
        self._name_index: dict[str, list[int]] = {}

    def record(self, point: MetricPoint) -> None:
        """记录指标"""
        idx = len(self._points)
        self._points.append(point)

        if point.name not in self._name_index:
            self._name_index[point.name] = []
        self._name_index[point.name].append(idx)

        logger.debug(f"[InMemoryMetricStore] 记录指标: {point.name} = {point.value}")

    def query(
        self,
        name: str | None = None,
        metric_type: MetricType | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[MetricPoint]:
        """查询指标"""
        if name is not None:
            indices = self._name_index.get(name, [])
            results = [self._points[i] for i in indices if i < len(self._points)]
        else:
            results = list(self._points)

        if metric_type is not None:
            results = [p for p in results if p.metric_type == metric_type]
        if start_time is not None:
            results = [p for p in results if p.timestamp >= start_time]
        if end_time is not None:
            results = [p for p in results if p.timestamp <= end_time]

        return results

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
        points = self.query(name=name, start_time=start_time, end_time=end_time)
        if not points:
            return None

        values = [p.value for p in points]
        if agg == "sum":
            return sum(values)
        elif agg == "avg":
            return sum(values) / len(values)
        elif agg == "min":
            return min(values)
        elif agg == "max":
            return max(values)
        elif agg == "count":
            return float(len(values))
        return None

    def clear(self) -> None:
        """清空指标"""
        self._points.clear()
        self._name_index.clear()
        logger.debug("[InMemoryMetricStore] 清空指标")


class FileMetricStore:
    """
    文件指标存储

    文件结构:
    --------
    metrics/
    ├── req.count.jsonl    # 每行一个 MetricPoint JSON
    ├── req.duration.jsonl
    └── ...

    使用 JSONL 格式方便追加和按名称分文件。

    使用示例:
    --------
    >>> from pathlib import Path
    >>> store = FileMetricStore(Path("./metrics"))
    >>> store.record(MetricPoint(name="req.count", value=1))
    """

    def __init__(self, base_path: Path):
        """
        初始化文件指标存储

        参数:
        -----
        base_path: 指标文件存储目录
        """
        self._base_path = base_path
        self._base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"[FileMetricStore] 初始化指标目录: {base_path}")

    def _get_file_path(self, name: str) -> Path:
        """获取指标文件路径"""
        # 替换特殊字符
        safe_name = name.replace("/", "_").replace(":", "_")
        return self._base_path / f"{safe_name}.jsonl"

    def record(self, point: MetricPoint) -> None:
        """记录指标到文件"""
        file_path = self._get_file_path(point.name)
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(point.to_dict(), ensure_ascii=False) + "\n")
        logger.debug(f"[FileMetricStore] 记录指标: {point.name} = {point.value}")

    def query(
        self,
        name: str | None = None,
        metric_type: MetricType | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[MetricPoint]:
        """查询指标"""
        if name is not None:
            files = [self._get_file_path(name)]
            files = [f for f in files if f.exists()]
        else:
            files = list(self._base_path.glob("*.jsonl"))

        points: list[MetricPoint] = []
        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            point = MetricPoint.from_dict(json.loads(line))
                            if metric_type and point.metric_type != metric_type:
                                continue
                            if start_time and point.timestamp < start_time:
                                continue
                            if end_time and point.timestamp > end_time:
                                continue
                            points.append(point)
                        except (json.JSONDecodeError, KeyError):
                            continue
            except Exception as e:
                logger.warning(f"[FileMetricStore] 读取指标文件失败 {file_path}: {e}")

        return points

    def aggregate(
        self,
        name: str,
        agg: str = "sum",
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> float | None:
        """聚合计算"""
        points = self.query(name=name, start_time=start_time, end_time=end_time)
        if not points:
            return None

        values = [p.value for p in points]
        if agg == "sum":
            return sum(values)
        elif agg == "avg":
            return sum(values) / len(values)
        elif agg == "min":
            return min(values)
        elif agg == "max":
            return max(values)
        elif agg == "count":
            return float(len(values))
        return None

    def clear(self) -> None:
        """清空所有指标文件"""
        for file_path in self._base_path.glob("*.jsonl"):
            file_path.unlink()
        logger.debug("[FileMetricStore] 清空所有指标文件")
