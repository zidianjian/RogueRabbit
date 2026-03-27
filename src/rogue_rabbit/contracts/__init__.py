"""
contracts 包 - 协议与数据模型

这个包定义了 agent 系统的"契约"：
- 数据结构：消息、角色等
- 接口协议：LLM 客户端、MCP 客户端等

为什么叫 contracts（契约）?
=========================
契约定义了系统各部分之间的"协议"：
- 调用方只需要知道契约，不需要知道具体实现
- 实现方只需要满足契约，可以被任何调用方使用

这就像现实中的合同：
- 定义了双方的责任和期望
- 只要满足合同，具体怎么做可以灵活变化

学习建议:
========
1. 先理解 Message 和 Role - 这是 LLM 交互的基础
2. 再理解 LLMClient Protocol - 这是抽象层的核心
3. 最后理解 MockLLMClient - 这是测试和学习的工具
4. v0.2 新增: MCP 相关的数据模型和协议
5. v0.3 新增: Skill 相关的数据模型
"""

from rogue_rabbit.contracts.llm import LLMClient, MockLLMClient
from rogue_rabbit.contracts.messages import Message, MessageList, Role
from rogue_rabbit.contracts.mcp import (
    MCPClient,
    MCPTool,
    MCPToolInputSchema,
    MCPToolResult,
    MCPResource,
    MCPResourceContent,
    MCPPrompt,
    MCPPromptArgument,
    MCPServerConfig,
    MCPTransportType,
    MockMCPClient,
)
from rogue_rabbit.contracts.skill import Skill, SkillDiscoveryResult, SkillMeta
from rogue_rabbit.contracts.session import Session, SessionMeta, SessionStatus, SessionStore
from rogue_rabbit.contracts.memory import Memory, MemoryItem, MemoryMeta, MemoryStore

__all__ = [
    # 消息相关
    "Message",
    "MessageList",
    "Role",
    # LLM 客户端相关
    "LLMClient",
    "MockLLMClient",
    # MCP 相关 (v0.2 新增)
    "MCPClient",
    "MCPTool",
    "MCPToolInputSchema",
    "MCPToolResult",
    "MCPResource",
    "MCPResourceContent",
    "MCPPrompt",
    "MCPPromptArgument",
    "MCPServerConfig",
    "MCPTransportType",
    "MockMCPClient",
    # Skill 相关 (v0.3 新增)
    "Skill",
    "SkillMeta",
    "SkillDiscoveryResult",
    # Session 相关 (v0.4 新增)
    "Session",
    "SessionMeta",
    "SessionStatus",
    "SessionStore",
    # Memory 相关 (v0.5 新增)
    "Memory",
    "MemoryItem",
    "MemoryMeta",
    "MemoryStore",
]
