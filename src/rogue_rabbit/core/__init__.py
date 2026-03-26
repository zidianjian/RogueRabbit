"""
core 包 - 核心功能

提供 Agent、工具管理、Skill 管理、会话管理等核心能力。
"""

from rogue_rabbit.core.context_window import (
    ContextWindowConfig,
    ContextWindowManager,
    TruncationStrategy,
)
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
]
