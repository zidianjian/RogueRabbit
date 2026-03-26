"""
experiments 包 - 学习实验

这个包包含各种学习实验，帮助你理解 agent 开发的核心技术。

阶段一的学习方式:
===============
- 每个实验聚焦一个核心概念
- 代码简洁，注释详细
- 可以独立运行

实验列表:
========
LLM 基础:
- 01_hello_llm: 最简单的 LLM 调用
- 02_conversation: 多轮对话管理
- 03_system_prompt: 系统提示词的作用

MCP 工具调用:
- 04_mcp_basic: 基础 MCP 调用
- 05_mcp_with_llm: LLM + MCP 组合（简单 ReAct Agent）
- 06_mcp_real: 真实 LLM + 真实 MCP

运行方式:
========
    python -m rogue_rabbit.experiments.01_hello_llm
    python -m rogue_rabbit.experiments.02_conversation
    python -m rogue_rabbit.experiments.03_system_prompt
    python -m rogue_rabbit.experiments.04_mcp_basic
    python -m rogue_rabbit.experiments.05_mcp_with_llm
    python -m rogue_rabbit.experiments.06_mcp_real
"""

__all__ = []
