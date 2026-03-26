"""
实验 06: 真实 LLM + 真实 MCP
============================

学习目标:
--------
1. 使用真实的 LLM（GLM）进行推理
2. 连接真实的 MCP 服务器
3. 实现 LLM 自主决定工具调用的完整流程

前置条件:
--------
1. 配置 .env 文件中的 ZHIPU_API_KEY
2. 安装一个 MCP 服务器（可选，本示例提供多种方案）

运行方式:
--------
    python -m rogue_rabbit.experiments.06_mcp_real
"""

import asyncio
import json
import os
import re
from pathlib import Path

from rogue_rabbit.adapters import GLMClient, create_mcp_client
from rogue_rabbit.contracts import Message, Role
from rogue_rabbit.contracts.mcp import (
    MCPTool,
    MCPToolInputSchema,
    MCPToolResult,
    MCPServerConfig,
    MCPTransportType,
    MockMCPClient,
)


# ========================================
# 配置检查
# ========================================


def check_api_key() -> bool:
    """检查 API key 是否配置"""
    from dotenv import load_dotenv

    # 尝试加载 .env
    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    load_dotenv(env_path)

    api_key = os.environ.get("ZHIPU_API_KEY")
    if not api_key:
        print("[!] 未配置 ZHIPU_API_KEY")
        print("\n请在项目根目录创建 .env 文件:")
        print("  ZHIPU_API_KEY=your-api-key")
        return False

    print("[OK] ZHIPU_API_KEY 已配置")
    return True


# ========================================
# ReAct Agent 实现
# ========================================


class ReActAgent:
    """
    ReAct Agent - 使用真实 LLM 进行推理

    ReAct = Reasoning + Acting
    - LLM 分析问题，决定使用什么工具
    - 执行工具调用
    - 根据结果继续推理
    - 直到得出最终答案
    """

    def __init__(
        self,
        llm_client,
        mcp_client,
        max_iterations: int = 10,
        verbose: bool = True,
    ):
        self._llm = llm_client
        self._mcp = mcp_client
        self._max_iterations = max_iterations
        self._verbose = verbose

    def _log(self, message: str):
        """打印日志"""
        if self._verbose:
            print(message)

    async def run(self, question: str) -> str:
        """运行 Agent"""
        # 获取可用工具
        tools = await self._mcp.list_tools()
        tool_descriptions = self._format_tools(tools)

        # 构建系统提示
        system_prompt = f"""你是一个智能助手，可以使用工具来回答问题。

可用工具:
{tool_descriptions}

使用规则:
1. 当需要使用工具时，按以下格式回复：
   THOUGHT: 你的分析
   ACTION: 工具名称
   ARGUMENTS: {{"参数名": "参数值"}}

2. 当可以给出最终答案时，按以下格式回复：
   THOUGHT: 你的分析
   ANSWER: 最终答案

3. 如果工具返回错误，尝试其他方法或告诉用户无法完成。

请始终用中文回复。"""

        messages: list[Message] = [
            Message(role=Role.SYSTEM, content=system_prompt),
            Message(role=Role.USER, content=question),
        ]

        # ReAct 循环
        for i in range(self._max_iterations):
            self._log(f"\n{'='*50}")
            self._log(f"[轮次 {i + 1}]")

            # 调用 LLM
            response = self._llm.complete(messages)
            self._log(f"\n[LLM 回复]\n{response}")

            # 检查是否需要调用工具
            if "ACTION:" in response and "ANSWER:" not in response:
                # 解析工具调用
                action, arguments = self._parse_action(response)
                self._log(f"\n[调用工具] {action}({arguments})")

                # 执行工具
                try:
                    result = await self._mcp.call_tool(action, arguments)
                    self._log(f"[工具结果] {result.text[:200]}{'...' if len(result.text) > 200 else ''}")

                    # 添加到消息历史
                    messages.append(Message(role=Role.ASSISTANT, content=response))
                    messages.append(
                        Message(
                            role=Role.USER,
                            content=f"工具执行结果:\n{result.text}",
                        )
                    )
                except Exception as e:
                    error_msg = f"工具调用失败: {str(e)}"
                    self._log(f"[错误] {error_msg}")
                    messages.append(Message(role=Role.ASSISTANT, content=response))
                    messages.append(
                        Message(role=Role.USER, content=f"工具执行出错:\n{error_msg}")
                    )

            elif "ANSWER:" in response:
                # 提取最终答案
                answer = self._extract_answer(response)
                return answer

            else:
                # LLM 直接回答了问题
                return response

        return "达到最大轮次限制，未能完成任务"

    def _format_tools(self, tools: list[MCPTool]) -> str:
        """格式化工具描述"""
        lines = []
        for tool in tools:
            params_desc = []
            for name, prop in tool.input_schema.properties.items():
                param_type = prop.get("type", "any")
                desc = prop.get("description", "")
                required = name in tool.input_schema.required
                req_mark = "必需" if required else "可选"
                params_desc.append(f"    - {name} ({param_type}, {req_mark}): {desc}")

            lines.append(f"- {tool.name}: {tool.description}")
            if params_desc:
                lines.extend(params_desc)

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
                self._log("[警告] 无法解析参数，使用空参数")

        return action, arguments

    def _extract_answer(self, response: str) -> str:
        """提取最终答案"""
        answer_match = re.search(r"ANSWER:\s*(.+)", response, re.DOTALL)
        return answer_match.group(1).strip() if answer_match else response


# ========================================
# Demo 1: 使用 Mock MCP + 真实 LLM
# ========================================


async def demo_mock_mcp_real_llm():
    """Demo 1: Mock MCP + 真实 LLM"""
    print("\n" + "=" * 60)
    print("Demo 1: Mock MCP + 真实 LLM")
    print("=" * 60)
    print("\n这个演示使用 Mock MCP 客户端，但使用真实的 GLM 进行推理。")

    if not check_api_key():
        return

    # 创建工具
    tools = [
        MCPTool(
            name="calculator",
            description="执行数学计算，支持加减乘除和括号",
            input_schema=MCPToolInputSchema(
                properties={
                    "expression": {
                        "type": "string",
                        "description": "数学表达式，如 '(10 + 5) * 2'",
                    }
                },
                required=["expression"],
            ),
        ),
        MCPTool(
            name="get_time",
            description="获取当前日期和时间",
            input_schema=MCPToolInputSchema(properties={}, required=[]),
        ),
    ]

    # 模拟工具执行结果
    from datetime import datetime

    def mock_calculator(expr: str) -> str:
        try:
            # 安全地计算简单数学表达式
            result = eval(expr, {"__builtins__": {}}, {})
            return str(result)
        except:
            return "计算错误"

    tool_results = {
        "calculator": MCPToolResult(content=""),  # 动态生成
        "get_time": MCPToolResult(content=datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    }

    # 创建动态 Mock 客户端
    class DynamicMockClient(MockMCPClient):
        def __init__(self, tools, calculator_func):
            super().__init__(tools=tools)
            self._calculator = calculator_func

        async def call_tool(self, name: str, arguments: dict | None = None):
            if name == "calculator":
                result = self._calculator(arguments.get("expression", ""))
                return MCPToolResult(content=result)
            elif name == "get_time":
                return MCPToolResult(
                    content=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
            return MCPToolResult(content="未知工具")

    mcp_client = DynamicMockClient(tools, mock_calculator)
    await mcp_client.connect()

    # 创建 LLM 客户端
    llm_client = GLMClient()

    # 创建 Agent
    agent = ReActAgent(llm_client, mcp_client)

    # 运行
    question = "现在几点了？另外帮我算一下 (123 + 456) * 2 等于多少"
    print(f"\n问题: {question}")

    answer = await agent.run(question)
    print(f"\n{'='*50}")
    print(f"最终答案: {answer}")

    await mcp_client.disconnect()


# ========================================
# Demo 2: 连接真实 MCP 服务器
# ========================================


async def demo_real_mcp_server():
    """Demo 2: 连接真实 MCP 服务器"""
    print("\n" + "=" * 60)
    print("Demo 2: 连接真实 MCP 服务器")
    print("=" * 60)

    # 检查是否有 MCP 服务器可用
    print("\n要连接真实的 MCP 服务器，你需要:")
    print("1. 安装 MCP 服务器（如 filesystem、puppeteer 等）")
    print("2. 配置服务器的启动命令")

    print("\n常见 MCP 服务器:")
    print("  - @modelcontextprotocol/server-filesystem: 文件系统操作")
    print("  - @modelcontextprotocol/server-puppeteer: 浏览器自动化")
    print("  - @modelcontextprotocol/server-sqlite: SQLite 数据库")

    print("\n安装示例 (需要 Node.js):")
    print("  npm install -g @modelcontextprotocol/server-filesystem")

    # 示例配置
    print("\n" + "-" * 40)
    print("示例配置:")
    print("-" * 40)

    # filesystem MCP 服务器配置示例
    config = MCPServerConfig(
        name="filesystem",
        transport=MCPTransportType.STDIO,
        command="npx",
        args=[
            "-y",
            "@modelcontextprotocol/server-filesystem",
            str(Path.home()),  # 允许访问用户目录
        ],
    )

    print(f"服务器名称: {config.name}")
    print(f"传输类型: {config.transport.value}")
    print(f"启动命令: {config.command} {' '.join(config.args)}")

    # 尝试连接（如果服务器可用）
    print("\n" + "-" * 40)
    print("尝试连接...")
    print("-" * 40)

    try:
        async with create_mcp_client(config) as client:
            tools = await client.list_tools()
            print(f"\n[OK] 连接成功！发现 {len(tools)} 个工具:")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")

            # 如果有 LLM，可以进行交互
            if check_api_key():
                print("\n是否要使用这些工具回答问题？(y/n): ", end="")
                # 在自动化脚本中跳过交互
                print("跳过交互式输入")
    except Exception as e:
        print(f"\n[FAIL] 连接失败: {e}")
        print("\n这是正常的，如果没有安装 MCP 服务器。")


# ========================================
# Demo 3: 自定义 MCP 服务器配置
# ========================================


async def demo_custom_mcp_config():
    """Demo 3: 自定义 MCP 服务器配置"""
    print("\n" + "=" * 60)
    print("Demo 3: 自定义 MCP 服务器配置")
    print("=" * 60)

    print("\n你可以配置自己的 MCP 服务器。示例配置:")

    # Python MCP 服务器配置
    print("\n1. Python MCP 服务器 (STDIO):")
    print("""
    config = MCPServerConfig(
        name="my-python-server",
        transport=MCPTransportType.STDIO,
        command="python",
        args=["-m", "my_mcp_server"],
        env={"DEBUG": "1"}  # 可选的环境变量
    )
    """)

    # HTTP MCP 服务器配置
    print("\n2. HTTP MCP 服务器:")
    print("""
    config = MCPServerConfig(
        name="my-http-server",
        transport=MCPTransportType.STREAMABLE_HTTP,
        url="http://localhost:8000/mcp"
    )
    """)

    # 如何创建 MCP 服务器
    print("\n3. 创建简单的 MCP 服务器 (Python):")
    print("""
    # my_mcp_server.py
    from mcp.server import Server
    from mcp.server.stdio import stdio_server

    server = Server("my-server")

    @server.list_tools()
    async def list_tools():
        return [Tool(name="hello", description="说你好", inputSchema={...})]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        return [TextContent(type="text", text="Hello!")]

    # 运行服务器
    async with stdio_server() as (read, write):
        await server.run(read, write)
    """)


# ========================================
# Main
# ========================================


async def main():
    """主函数"""
    print("=" * 60)
    print("实验 06: 真实 LLM + 真实 MCP")
    print("=" * 60)

    print("\n本实验展示如何使用真实的 LLM 和 MCP 服务器。")

    # 运行 Demo 1（Mock MCP + 真实 LLM）
    await demo_mock_mcp_real_llm()

    # 运行 Demo 2（尝试连接真实 MCP）
    await demo_real_mcp_server()

    # 运行 Demo 3（自定义配置说明）
    await demo_custom_mcp_config()

    # 总结
    print("\n" + "=" * 60)
    print("学习总结")
    print("=" * 60)
    print("""
1. ReAct Agent 需要 LLM 能够理解工具描述并生成正确的调用格式
2. MCP 服务器可以通过 STDIO 或 HTTP 方式连接
3. 实际应用中需要处理各种错误情况
4. 工具的描述质量会影响 LLM 的调用准确性

下一步:
- 安装一个 MCP 服务器并尝试连接
- 添加更多自定义工具
- 优化系统提示以提高工具调用准确性
""")


if __name__ == "__main__":
    asyncio.run(main())
