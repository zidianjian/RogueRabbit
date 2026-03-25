"""
实验 05: LLM + MCP 组合
=======================

学习目标:
--------
1. 理解 LLM 如何与 MCP 工具配合
2. 实现简单的 ReAct 循环
3. 理解 Agent 的基本工作原理

核心概念:
--------
Agent = LLM + Tools
- LLM 决定调用哪个工具
- 工具执行并返回结果
- LLM 根据结果继续推理

运行方式:
--------
    python -m rogue_rabbit.experiments.05_mcp_with_llm
"""

import asyncio
import json
import re

from rogue_rabbit.adapters import GLMClient
from rogue_rabbit.contracts import Message, Role, LLMClient
from rogue_rabbit.contracts.mcp import (
    MCPTool,
    MCPToolInputSchema,
    MockMCPClient,
    MCPToolResult,
)


# ========================================
# 简单的 ReAct Agent
# ========================================


class SimpleReActAgent:
    """
    简单的 ReAct Agent - LLM + Tools

    ReAct = Reasoning + Acting
    1. Reasoning: LLM 思考应该做什么
    2. Acting: 执行工具调用
    3. 循环直到完成任务

    这是一个简化的实现，展示 Agent 的核心原理。
    真正的 Agent 需要更复杂的错误处理和状态管理。
    """

    def __init__(
        self,
        llm_client: LLMClient,
        mcp_client: MockMCPClient,
        max_iterations: int = 5,
    ):
        """
        初始化 Agent

        参数:
        -----
        llm_client: LLM 客户端
        mcp_client: MCP 客户端
        max_iterations: 最大迭代次数（防止无限循环）
        """
        self._llm = llm_client
        self._mcp = mcp_client
        self._max_iterations = max_iterations

    async def run(self, question: str) -> str:
        """
        运行 Agent

        参数:
        -----
        question: 用户问题

        返回:
        -----
        str: 最终答案
        """
        # 获取可用工具
        tools = await self._mcp.list_tools()
        tool_descriptions = self._format_tools(tools)

        # 构建系统提示
        system_prompt = f"""你是一个智能助手，可以使用以下工具来回答问题：

{tool_descriptions}

当需要使用工具时，请按以下格式回复：
THOUGHT: 你的思考
ACTION: 工具名称
ARGUMENTS: {{"参数名": "参数值"}}

当得出最终答案时，请按以下格式回复：
THOUGHT: 你的思考
ANSWER: 最终答案

请开始回答用户的问题。"""

        messages: list[Message] = [
            Message(role=Role.SYSTEM, content=system_prompt),
            Message(role=Role.USER, content=question),
        ]

        # ReAct 循环
        for i in range(self._max_iterations):
            print(f"\n[迭代 {i + 1}]")

            # 调用 LLM
            response = self._llm.complete(messages)
            print(f"[LLM] {response[:200]}...")

            # 检查是否有 ACTION
            if "ACTION:" in response:
                # 解析工具调用
                action, arguments = self._parse_action(response)
                print(f"[工具调用] {action}({arguments})")

                # 执行工具
                result = await self._mcp.call_tool(action, arguments)
                print(f"[工具结果] {result.text}")

                # 将结果添加到消息
                messages.append(Message(role=Role.ASSISTANT, content=response))
                messages.append(
                    Message(role=Role.USER, content=f"工具执行结果: {result.text}")
                )

            elif "ANSWER:" in response:
                # 提取最终答案
                answer = self._extract_answer(response)
                return answer

            else:
                # 没有 ACTION 或 ANSWER，直接返回
                return response

        return "达到最大迭代次数，未能完成任务"

    def _format_tools(self, tools: list[MCPTool]) -> str:
        """格式化工具描述"""
        lines = []
        for tool in tools:
            params = ", ".join(tool.input_schema.required)
            lines.append(f"- {tool.name}({params}): {tool.description}")
        return "\n".join(lines)

    def _parse_action(self, response: str) -> tuple[str, dict]:
        """解析工具调用"""
        # 提取 ACTION
        action_match = re.search(r"ACTION:\s*(\w+)", response)
        action = action_match.group(1) if action_match else ""

        # 提取 ARGUMENTS
        args_match = re.search(r"ARGUMENTS:\s*(\{.*?\})", response, re.DOTALL)
        arguments = {}
        if args_match:
            try:
                arguments = json.loads(args_match.group(1))
            except json.JSONDecodeError:
                pass

        return action, arguments

    def _extract_answer(self, response: str) -> str:
        """提取最终答案"""
        answer_match = re.search(r"ANSWER:\s*(.+)", response, re.DOTALL)
        return answer_match.group(1).strip() if answer_match else response


# ========================================
# Demo
# ========================================


async def demo_react_agent() -> None:
    """演示：简单的 ReAct Agent"""
    print("\n" + "-" * 50)
    print("[Demo] 简单的 ReAct Agent")
    print("-" * 50)

    # 创建工具
    tools = [
        MCPTool(
            name="calculator",
            description="计算数学表达式，返回结果",
            input_schema=MCPToolInputSchema(
                properties={
                    "expression": {"type": "string", "description": "数学表达式"}
                },
                required=["expression"],
            ),
        ),
        MCPTool(
            name="search",
            description="搜索信息",
            input_schema=MCPToolInputSchema(
                properties={"query": {"type": "string", "description": "搜索关键词"}},
                required=["query"],
            ),
        ),
    ]

    # 创建 Mock 工具结果
    tool_results = {
        "calculator": MCPToolResult(content="42"),
        "search": MCPToolResult(content="Python 是一种高级编程语言，由 Guido van Rossum 创建..."),
    }

    # 创建客户端
    mcp_client = MockMCPClient(tools=tools, tool_results=tool_results)
    await mcp_client.connect()

    # 使用 Mock LLM 客户端演示（避免需要真实 API）
    from rogue_rabbit.contracts import MockLLMClient

    # 模拟 LLM 的多轮响应
    llm_responses = [
        # 第一轮：决定调用 calculator
        """THOUGHT: 用户问 6 乘以 7 的结果，我需要使用计算器工具
ACTION: calculator
ARGUMENTS: {"expression": "6*7"}""",
        # 第二轮：得到结果后给出答案
        """THOUGHT: 计算器返回了结果 42
ANSWER: 6 * 7 = 42""",
    ]

    mock_llm = MockLLMClient()
    mock_llm._response_index = 0

    def mock_complete(messages):
        response = llm_responses[mock_llm._response_index]
        mock_llm._response_index += 1
        if mock_llm._response_index >= len(llm_responses):
            mock_llm._response_index = 0
        return response

    mock_llm.complete = mock_complete

    # 创建 Agent
    agent = SimpleReActAgent(mock_llm, mcp_client)

    # 运行
    question = "计算 6 * 7 的结果"
    print(f"\n问题: {question}")

    answer = await agent.run(question)
    print(f"\n最终答案: {answer}")

    await mcp_client.disconnect()


async def demo_tool_discovery() -> None:
    """演示：工具发现"""
    print("\n" + "-" * 50)
    print("[Demo] 工具发现")
    print("-" * 50)

    # 创建多个工具
    tools = [
        MCPTool(
            name="get_weather",
            description="获取指定城市的天气信息",
            input_schema=MCPToolInputSchema(
                properties={
                    "city": {"type": "string", "description": "城市名称"},
                    "unit": {"type": "string", "description": "温度单位（celsius/fahrenheit）"},
                },
                required=["city"],
            ),
        ),
        MCPTool(
            name="send_email",
            description="发送电子邮件",
            input_schema=MCPToolInputSchema(
                properties={
                    "to": {"type": "string", "description": "收件人邮箱"},
                    "subject": {"type": "string", "description": "邮件主题"},
                    "body": {"type": "string", "description": "邮件正文"},
                },
                required=["to", "subject", "body"],
            ),
        ),
        MCPTool(
            name="query_database",
            description="执行 SQL 查询",
            input_schema=MCPToolInputSchema(
                properties={
                    "sql": {"type": "string", "description": "SQL 查询语句"},
                },
                required=["sql"],
            ),
        ),
    ]

    client = MockMCPClient(tools=tools)
    await client.connect()

    print("\n发现的工具:")
    discovered_tools = await client.list_tools()
    for tool in discovered_tools:
        print(f"\n  {tool.name}:")
        print(f"    描述: {tool.description}")
        print(f"    必需参数: {', '.join(tool.input_schema.required)}")

    await client.disconnect()


# ========================================
# Main
# ========================================


async def main() -> None:
    """LLM + MCP 学习示例"""

    print("=" * 50)
    print("实验 05: LLM + MCP 组合")
    print("=" * 50)

    print("\nAgent = LLM + Tools")
    print("- LLM 负责'思考'和'决策'")
    print("- Tools 负责'执行'和'获取信息'")
    print("- ReAct 循环: Reasoning → Acting → Observing")

    # 运行演示
    await demo_tool_discovery()
    await demo_react_agent()

    # ========================================
    # 总结
    # ========================================
    print("\n" + "=" * 50)
    print("学习总结:")
    print("-" * 50)
    print("1. Agent 是 LLM 和工具的组合")
    print("2. ReAct 是一种常见的 Agent 模式")
    print("3. MCP 提供标准化的工具接口")
    print("4. 真正的 Agent 需要更复杂的状态管理")
    print("5. 这是 Claude Code 等 AI 工具的基本原理")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
