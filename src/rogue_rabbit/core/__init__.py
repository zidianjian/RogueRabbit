"""
core 包 - 核心功能

提供 Agent、工具管理、Skill 管理、会话管理等核心能力。
"""

from rogue_rabbit.core.context_window import (
    ContextWindowConfig,
    ContextWindowManager,
    TruncationStrategy,
)
from rogue_rabbit.core.log_manager import MetricsCollector, StructuredLogger, Tracer
from rogue_rabbit.core.memory_manager import MemoryManager
from rogue_rabbit.core.authorizer import Authorizer
from rogue_rabbit.core.react_agent import ReActAgent
from rogue_rabbit.core.session_manager import SessionManager
from rogue_rabbit.core.skill_manager import SkillManager

__all__ = [
    "ReActAgent",
    "SkillManager",
    # Session 相关 (v0.4 新增)
    "SessionManager",
    "ContextWindowManager",
    "ContextWindowConfig",
    "TruncationStrategy",
    # Memory 相关 (v0.5 新增)
    "MemoryManager",
    # Permission 相关 (v0.6 新增)
    "Authorizer",
    # Logging 相关 (v0.7 新增)
    "StructuredLogger",
    "Tracer",
    "MetricsCollector",
]
