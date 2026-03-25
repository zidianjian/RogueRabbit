"""
MCP 客户端适配器 - 封装 MCP Python SDK

学习要点:
=========
1. 如何使用 MCP Python SDK
2. 异步上下文管理器的实现
3. 格式转换：SDK 类型 <-> 内部类型

MCP SDK 使用流程:
================
1. 创建 ServerParameters（配置连接）
2. 使用 stdio_client 或 streamable_http_client 建立连接
3. 使用 ClientSession 管理会话
4. 调用 list_tools, call_tool 等方法

设计原则:
========
- 使用 async context manager 管理连接生命周期
- 隔离 MCP SDK 的类型，转换为内部类型
- 提供同步包装器方便简单场景使用
"""

from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from rogue_rabbit.contracts.mcp import (
    MCPResource,
    MCPResourceContent,
    MCPPrompt,
    MCPPromptArgument,
    MCPTool,
    MCPToolInputSchema,
    MCPToolResult,
    MCPServerConfig,
    MCPTransportType,
)


class StdioMCPClient:
    """
    STDIO MCP 客户端 - 通过标准输入输出连接 MCP 服务器

    适用场景:
    --------
    - 连接本地 MCP 服务器进程
    - 开发和调试
    - 不需要网络通信的场景

    使用示例:
    --------
    >>> config = MCPServerConfig(
    ...     name="my-server",
    ...     transport=MCPTransportType.STDIO,
    ...     command="python",
    ...     args=["-m", "my_mcp_server"]
    ... )
    >>> async with StdioMCPClient(config) as client:
    ...     tools = await client.list_tools()
    ...     result = await client.call_tool("add", {"a": 1, "b": 2})
    """

    def __init__(self, config: MCPServerConfig):
        """
        初始化 STDIO MCP 客户端

        参数:
        -----
        config: 服务器配置
        """
        if config.transport != MCPTransportType.STDIO:
            raise ValueError("StdioMCPClient 只支持 STDIO 传输类型")

        self._config = config
        self._session: ClientSession | None = None
        self._read_stream = None
        self._write_stream = None
        self._cm = None  # 保存 context manager

    async def connect(self) -> None:
        """建立连接（由 __aenter__ 调用）"""
        server_params = StdioServerParameters(
            command=self._config.command or "python",
            args=list(self._config.args),
            env=self._config.env or None,
        )

        # 使用 context manager 管理连接
        self._cm = stdio_client(server_params)
        self._read_stream, self._write_stream = await self._cm.__aenter__()

        # 创建会话
        self._session = ClientSession(self._read_stream, self._write_stream)
        await self._session.__aenter__()

        # 初始化连接
        await self._session.initialize()

    async def disconnect(self) -> None:
        """断开连接（由 __aexit__ 调用）"""
        if self._session:
            await self._session.__aexit__(None, None, None)
            self._session = None

        if self._cm:
            await self._cm.__aexit__(None, None, None)
            self._cm = None

    async def __aenter__(self) -> "StdioMCPClient":
        """进入异步上下文"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """退出异步上下文"""
        await self.disconnect()

    async def list_tools(self) -> list[MCPTool]:
        """获取工具列表"""
        if not self._session:
            raise RuntimeError("未连接到服务器")

        result = await self._session.list_tools()
        return [_convert_tool(tool) for tool in result.tools]

    async def call_tool(
        self, name: str, arguments: dict[str, Any] | None = None
    ) -> MCPToolResult:
        """调用工具"""
        if not self._session:
            raise RuntimeError("未连接到服务器")

        result = await self._session.call_tool(name, arguments or {})

        # 提取内容
        if result.content:
            first_content = result.content[0]
            content = (
                first_content.text
                if hasattr(first_content, "text")
                else str(first_content)
            )
        else:
            content = ""

        return MCPToolResult(
            content=content,
            is_error=result.isError if hasattr(result, "isError") else False,
        )

    async def list_resources(self) -> list[MCPResource]:
        """获取资源列表"""
        if not self._session:
            raise RuntimeError("未连接到服务器")

        result = await self._session.list_resources()
        return [_convert_resource(res) for res in result.resources]

    async def read_resource(self, uri: str) -> MCPResourceContent:
        """读取资源内容"""
        if not self._session:
            raise RuntimeError("未连接到服务器")

        from pydantic import AnyUrl

        result = await self._session.read_resource(AnyUrl(uri))

        if result.contents:
            first_content = result.contents[0]
            return MCPResourceContent(
                uri=(
                    str(first_content.uri)
                    if hasattr(first_content, "uri")
                    else uri
                ),
                text=first_content.text if hasattr(first_content, "text") else None,
                mime_type=(
                    first_content.mimeType
                    if hasattr(first_content, "mimeType")
                    else None
                ),
            )

        return MCPResourceContent(uri=uri)

    async def list_prompts(self) -> list[MCPPrompt]:
        """获取 Prompt 列表"""
        if not self._session:
            raise RuntimeError("未连接到服务器")

        result = await self._session.list_prompts()
        return [_convert_prompt(prompt) for prompt in result.prompts]

    async def get_prompt(
        self, name: str, arguments: dict[str, str] | None = None
    ) -> list[str]:
        """获取 Prompt 内容"""
        if not self._session:
            raise RuntimeError("未连接到服务器")

        result = await self._session.get_prompt(name, arguments)
        return [
            msg.content.text for msg in result.messages if hasattr(msg.content, "text")
        ]


class HttpMCPClient:
    """
    HTTP MCP 客户端 - 通过 HTTP/SSE 连接 MCP 服务器

    适用场景:
    --------
    - 连接远程 MCP 服务器
    - 生产环境部署
    - 需要网络通信的场景

    使用示例:
    --------
    >>> config = MCPServerConfig(
    ...     name="remote-server",
    ...     transport=MCPTransportType.STREAMABLE_HTTP,
    ...     url="http://localhost:8000/mcp"
    ... )
    >>> async with HttpMCPClient(config) as client:
    ...     tools = await client.list_tools()
    """

    def __init__(self, config: MCPServerConfig):
        """初始化 HTTP MCP 客户端"""
        if config.transport not in (
            MCPTransportType.STREAMABLE_HTTP,
            MCPTransportType.SSE,
        ):
            raise ValueError("HttpMCPClient 只支持 HTTP 传输类型")

        self._config = config
        self._session: ClientSession | None = None
        self._cm = None
        self._read_stream = None
        self._write_stream = None

    async def connect(self) -> None:
        """建立连接"""
        from mcp.client.streamable_http import streamable_http_client

        self._cm = streamable_http_client(self._config.url)
        self._read_stream, self._write_stream, _ = await self._cm.__aenter__()

        self._session = ClientSession(self._read_stream, self._write_stream)
        await self._session.__aenter__()
        await self._session.initialize()

    async def disconnect(self) -> None:
        """断开连接"""
        if self._session:
            await self._session.__aexit__(None, None, None)
            self._session = None

        if self._cm:
            await self._cm.__aexit__(None, None, None)
            self._cm = None

    async def __aenter__(self) -> "HttpMCPClient":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.disconnect()

    async def list_tools(self) -> list[MCPTool]:
        """获取工具列表"""
        if not self._session:
            raise RuntimeError("未连接到服务器")
        result = await self._session.list_tools()
        return [_convert_tool(tool) for tool in result.tools]

    async def call_tool(
        self, name: str, arguments: dict[str, Any] | None = None
    ) -> MCPToolResult:
        """调用工具"""
        if not self._session:
            raise RuntimeError("未连接到服务器")
        result = await self._session.call_tool(name, arguments or {})
        if result.content:
            first_content = result.content[0]
            content = (
                first_content.text
                if hasattr(first_content, "text")
                else str(first_content)
            )
        else:
            content = ""
        return MCPToolResult(
            content=content,
            is_error=result.isError if hasattr(result, "isError") else False,
        )

    async def list_resources(self) -> list[MCPResource]:
        """获取资源列表"""
        if not self._session:
            raise RuntimeError("未连接到服务器")
        result = await self._session.list_resources()
        return [_convert_resource(res) for res in result.resources]

    async def read_resource(self, uri: str) -> MCPResourceContent:
        """读取资源内容"""
        if not self._session:
            raise RuntimeError("未连接到服务器")
        from pydantic import AnyUrl

        result = await self._session.read_resource(AnyUrl(uri))
        if result.contents:
            first_content = result.contents[0]
            return MCPResourceContent(
                uri=(
                    str(first_content.uri)
                    if hasattr(first_content, "uri")
                    else uri
                ),
                text=first_content.text if hasattr(first_content, "text") else None,
            )
        return MCPResourceContent(uri=uri)

    async def list_prompts(self) -> list[MCPPrompt]:
        """获取 Prompt 列表"""
        if not self._session:
            raise RuntimeError("未连接到服务器")
        result = await self._session.list_prompts()
        return [_convert_prompt(prompt) for prompt in result.prompts]

    async def get_prompt(
        self, name: str, arguments: dict[str, str] | None = None
    ) -> list[str]:
        """获取 Prompt 内容"""
        if not self._session:
            raise RuntimeError("未连接到服务器")
        result = await self._session.get_prompt(name, arguments)
        return [
            msg.content.text for msg in result.messages if hasattr(msg.content, "text")
        ]


# ========================================
# 辅助函数
# ========================================


def _convert_tool(tool) -> MCPTool:
    """将 MCP SDK 的 Tool 转换为内部类型"""
    schema = tool.inputSchema or {}
    input_schema = MCPToolInputSchema(
        type=schema.get("type", "object"),
        properties=schema.get("properties", {}),
        required=schema.get("required", []),
    )
    return MCPTool(
        name=tool.name,
        description=tool.description or "",
        input_schema=input_schema,
    )


def _convert_resource(resource) -> MCPResource:
    """将 MCP SDK 的 Resource 转换为内部类型"""
    return MCPResource(
        uri=str(resource.uri),
        name=resource.name,
        description=resource.description,
        mime_type=resource.mimeType,
    )


def _convert_prompt(prompt) -> MCPPrompt:
    """将 MCP SDK 的 Prompt 转换为内部类型"""
    arguments = [
        MCPPromptArgument(
            name=arg.name,
            description=arg.description,
            required=arg.required,
        )
        for arg in (prompt.arguments or [])
    ]
    return MCPPrompt(
        name=prompt.name,
        description=prompt.description,
        arguments=arguments,
    )


# ========================================
# 工厂函数
# ========================================


def create_mcp_client(config: MCPServerConfig) -> StdioMCPClient | HttpMCPClient:
    """
    根据配置创建 MCP 客户端

    参数:
    -----
    config: 服务器配置

    返回:
    -----
    对应类型的 MCP 客户端实例

    使用示例:
    --------
    >>> config = MCPServerConfig(...)
    >>> client = create_mcp_client(config)
    >>> async with client:
    ...     tools = await client.list_tools()
    """
    if config.transport == MCPTransportType.STDIO:
        return StdioMCPClient(config)
    elif config.transport in (
        MCPTransportType.STREAMABLE_HTTP,
        MCPTransportType.SSE,
    ):
        return HttpMCPClient(config)
    else:
        raise ValueError(f"不支持的传输类型: {config.transport}")
