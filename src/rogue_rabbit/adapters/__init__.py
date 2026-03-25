"""
adapters 包 - 外部接口适配器

这个包包含各种外部服务的适配器：
- LLM 提供商（OpenAI, GLM 等）
- MCP 服务

适配器的职责:
============
1. **格式转换**: 将内部数据格式转换为外部 API 需要的格式
2. **错误处理**: 将外部错误转换为内部错误类型
3. **协议实现**: 实现 contracts 中定义的协议

设计原则:
========
- 每个外部服务一个适配器
- 适配器只负责"翻译"，不包含业务逻辑
- 适配器应该是无状态的（或状态最小化）

学习路径:
========
1. 先看 OpenAIClient - 理解适配器的基本结构
2. 再看 GLMClient - 理解如何复用已有适配器
3. 对比 contracts/llm.py - 理解协议与实现的关系
4. v0.2 新增: 看 mcp_client.py - 理解 MCP 适配器
"""

from rogue_rabbit.adapters.glm_client import GLMClient
from rogue_rabbit.adapters.openai_client import OpenAIClient
from rogue_rabbit.adapters.mcp_client import (
    StdioMCPClient,
    HttpMCPClient,
    create_mcp_client,
)

__all__ = [
    "OpenAIClient",
    "GLMClient",
    # MCP 相关 (v0.2 新增)
    "StdioMCPClient",
    "HttpMCPClient",
    "create_mcp_client",
]
