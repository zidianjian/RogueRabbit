"""
runtime 包 - 运行时组件

提供会话存储、记忆存储等运行时能力。
"""

from rogue_rabbit.runtime.log_store import (
    FileLogStore,
    FileMetricStore,
    FileSpanStore,
    InMemoryLogStore,
    InMemoryMetricStore,
    InMemorySpanStore,
)
from rogue_rabbit.runtime.memory_store import FileMemoryStore, InMemoryStore
from rogue_rabbit.runtime.policy_store import FilePolicyStore, InMemoryPolicyStore
from rogue_rabbit.runtime.session_store import FileSessionStore, MemorySessionStore

__all__ = [
    # Session 存储后端 (v0.4 新增)
    "MemorySessionStore",
    "FileSessionStore",
    # Memory 存储后端 (v0.5 新增)
    "InMemoryStore",
    "FileMemoryStore",
    # Policy 存储后端 (v0.6 新增)
    "InMemoryPolicyStore",
    "FilePolicyStore",
    # Logging 存储后端 (v0.7 新增)
    "InMemoryLogStore",
    "FileLogStore",
    "InMemorySpanStore",
    "FileSpanStore",
    "InMemoryMetricStore",
    "FileMetricStore",
]
