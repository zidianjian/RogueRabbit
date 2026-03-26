"""
REST API 应用

简单的物品管理 API，用于演示 MCP + LLM 集成。

运行方式:
    uvicorn rogue_rabbit.apps.rest.app:app --reload --port 8000
"""

from rogue_rabbit.apps.rest.app import app

__all__ = ["app"]
