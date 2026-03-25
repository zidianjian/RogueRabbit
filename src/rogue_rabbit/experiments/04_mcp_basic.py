"""
实验 04: 基础 MCP 调用
======================

学习目标:
--------
1. 理解 MCP 客户端的基本使用
2. 学习如何发现和调用工具
3. 理解 MCP 资源的概念

前置条件:
--------
- 安装 mcp 包: pip install mcp
- 有一个可用的 MCP 服务器（或使用 Mock 客户端）

运行方式:
--------
    python -m rogue_rabbit.experiments.04_mcp_basic
"""

import asyncio

from rogue_rabbit.contracts.mcp import (
    MCPTool,
    MCPToolInputSchema,
    MCPToolResult,
    MockMCPClient,
    MCPServerConfig,
    MCPTransportType,
)
from rogue_rabbit.adapters.mcp_client import create_mcp_client


# ========================================
# Demo 1: 使用 Mock 客户端
# ========================================


async def demo_mock_client() -> None:
    """演示：使用 Mock 客户端（不需要真实服务器）"""
    print("\n" + "-" * 50)
    print("[Demo 1] 使用 Mock 客户端")
    print("-" * 50)

    # 创建预设的工具
    tools = [
        MCPTool(
            name="add",
            description="计算两个数的和",
            input_schema=MCPToolInputSchema(
                properties={
                    "a": {"type": "number", "description": "第一个数"},
                    "b": {"type": "number", "description": "第二个数"},
                },
                required=["a", "b"],
            ),
        ),
        MCPTool(
            name="greet",
            description="生成问候语",
            input_schema=MCPToolInputSchema(
                properties={
                    "name": {"type": "string", "description": "名字"},
                },
                required=["name"],
            ),
        ),
    ]

    # 创建预设的工具结果
    tool_results = {
        "add": MCPToolResult(content="3"),
        "greet": MCPToolResult(content="你好，世界！"),
    }

    # 创建 Mock 客户端
    client = MockMCPClient(tools=tools, tool_results=tool_results)

    # 连接
    await client.connect()

    # 列出工具
    print("\n可用工具:")
    available_tools = await client.list_tools()
    for tool in available_tools:
        print(f"  - {tool.name}: {tool.description}")

    # 调用工具
    print("\n调用 add(1, 2):")
    result = await client.call_tool("add", {"a": 1, "b": 2})
    print(f"  结果: {result.text}")

    # 断开连接
    await client.disconnect()


# ========================================
# Demo 2: 连接真实 MCP 服务器（如果可用）
# ========================================


async def demo_real_server() -> None:
    """演示：连接真实 MCP 服务器"""
    print("\n" + "-" * 50)
    print("[Demo 2] 连接真实 MCP 服务器")
    print("-" * 50)

    # 配置服务器（示例配置，需要替换为实际的服务器）
    config = MCPServerConfig(
        name="example-server",
        transport=MCPTransportType.STDIO,
        command="python",
        args=["-m", "your_mcp_server"],  # 替换为实际的服务器模块
    )

    print(f"\n服务器配置:")
    print(f"  名称: {config.name}")
    print(f"  传输: {config.transport.value}")
    print(f"  命令: {config.command} {' '.join(config.args)}")

    print("\n注意: 此示例需要实际运行的 MCP 服务器")
    print("如果没有服务器，将跳过此演示")

    # 尝试连接（如果服务器可用）
    try:
        async with create_mcp_client(config) as client:
            tools = await client.list_tools()
            print(f"\n发现 {len(tools)} 个工具:")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")
    except Exception as e:
        print(f"\n连接失败（这是正常的，如果服务器未运行）: {e}")


# ========================================
# Demo 3: 异步上下文管理器
# ========================================


async def demo_context_manager() -> None:
    """演示：使用异步上下文管理器"""
    print("\n" + "-" * 50)
    print("[Demo 3] 异步上下文管理器")
    print("-" * 50)

    tools = [
        MCPTool(
            name="echo",
            description="返回输入内容",
            input_schema=MCPToolInputSchema(
                properties={"message": {"type": "string"}},
                required=["message"],
            ),
        ),
    ]

    client = MockMCPClient(tools=tools)

    # 使用 async with 自动管理连接
    async with client:
        print("\n在 async with 块中，客户端已连接")
        tools = await client.list_tools()
        print(f"工具数量: {len(tools)}")

    print("退出 async with 块后，客户端自动断开")


# ========================================
# Main
# ========================================


async def main() -> None:
    """MCP 基础学习示例"""

    print("=" * 50)
    print("实验 04: 基础 MCP 调用")
    print("=" * 50)

    print("\nMCP (Model Context Protocol) 核心概念:")
    print("- Tool: 可调用的函数")
    print("- Resource: 可读取的资源")
    print("- Prompt: 预定义的提示模板")

    # 运行演示
    await demo_mock_client()
    await demo_context_manager()
    await demo_real_server()

    # ========================================
    # 总结
    # ========================================
    print("\n" + "=" * 50)
    print("学习总结:")
    print("-" * 50)
    print("1. MCP 客户端通过 async with 管理连接生命周期")
    print("2. list_tools() 发现可用工具")
    print("3. call_tool(name, arguments) 调用工具")
    print("4. MockMCPClient 用于测试和学习")
    print("5. 支持 STDIO 和 HTTP 两种传输方式")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
