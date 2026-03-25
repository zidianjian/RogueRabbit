"""
MCP 协议 - 定义 MCP 客户端的标准接口和数据模型

学习要点:
=========
1. MCP (Model Context Protocol) 是什么？
2. Tool、Resource、Prompt 三大原语
3. 如何设计 MCP 相关的数据模型

MCP 核心概念:
============
- Tool: 可调用的函数，LLM 可以请求执行
- Resource: 可读取的资源（文件、数据等）
- Prompt: 预定义的提示模板

设计原则:
========
- 使用 frozen dataclass 保证不可变性
- 保持与 MCP SDK 类型兼容
- 提供类型别名提高可读性
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable


# ========================================
# 工具相关
# ========================================


@dataclass(frozen=True)
class MCPToolInputSchema:
    """
    工具输入参数的 JSON Schema

    属性:
    -----
    type: 类型，通常是 "object"
    properties: 参数定义
    required: 必需参数列表

    使用示例:
    --------
    >>> schema = MCPToolInputSchema(
    ...     properties={"city": {"type": "string"}},
    ...     required=["city"]
    ... )
    """

    type: str = "object"
    properties: dict[str, Any] = field(default_factory=dict)
    required: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class MCPTool:
    """
    MCP 工具定义

    属性:
    -----
    name: 工具名称（唯一标识）
    description: 工具描述（LLM 会看到）
    input_schema: 输入参数的 JSON Schema

    使用示例:
    --------
    >>> tool = MCPTool(
    ...     name="get_weather",
    ...     description="获取指定城市的天气信息",
    ...     input_schema=MCPToolInputSchema(
    ...         properties={"city": {"type": "string", "description": "城市名称"}},
    ...         required=["city"]
    ...     )
    ... )
    """

    name: str
    description: str
    input_schema: MCPToolInputSchema = field(default_factory=MCPToolInputSchema)


@dataclass(frozen=True)
class MCPToolResult:
    """
    工具调用结果

    属性:
    -----
    content: 结果内容（文本或结构化数据）
    is_error: 是否是错误结果

    设计说明:
    --------
    - 使用 is_error 而不是抛出异常，方便调用方统一处理
    - content 可以是字符串（文本结果）或字典（结构化数据）
    """

    content: str | dict[str, Any]
    is_error: bool = False

    @property
    def text(self) -> str:
        """获取文本内容（兼容性方法）"""
        if isinstance(self.content, str):
            return self.content
        return str(self.content)


# ========================================
# 资源相关
# ========================================


@dataclass(frozen=True)
class MCPResource:
    """
    MCP 资源定义

    属性:
    -----
    uri: 资源唯一标识（如 "file://config.json"）
    name: 资源名称
    description: 资源描述
    mime_type: MIME 类型（可选）
    """

    uri: str
    name: str
    description: str | None = None
    mime_type: str | None = None


@dataclass(frozen=True)
class MCPResourceContent:
    """
    资源内容

    属性:
    -----
    uri: 资源 URI
    text: 文本内容（如果是文本资源）
    blob: 二进制内容（如果是二进制资源）
    mime_type: MIME 类型
    """

    uri: str
    text: str | None = None
    blob: bytes | None = None
    mime_type: str | None = None


# ========================================
# Prompt 相关
# ========================================


@dataclass(frozen=True)
class MCPPromptArgument:
    """
    Prompt 参数定义

    属性:
    -----
    name: 参数名
    description: 参数描述
    required: 是否必需
    """

    name: str
    description: str | None = None
    required: bool = False


@dataclass(frozen=True)
class MCPPrompt:
    """
    MCP Prompt 定义

    属性:
    -----
    name: Prompt 名称
    description: Prompt 描述
    arguments: 参数列表
    """

    name: str
    description: str | None = None
    arguments: list[MCPPromptArgument] = field(default_factory=list)


# ========================================
# 连接配置
# ========================================


class MCPTransportType(Enum):
    """
    MCP 传输类型

    类型:
    ----
    - STDIO: 标准输入输出（本地进程通信）
    - SSE: Server-Sent Events（HTTP 流式）
    - STREAMABLE_HTTP: 可流式 HTTP（推荐）
    """

    STDIO = "stdio"
    SSE = "sse"
    STREAMABLE_HTTP = "streamable-http"


@dataclass(frozen=True)
class MCPServerConfig:
    """
    MCP 服务器配置

    属性:
    -----
    name: 服务器名称（用于标识）
    transport: 传输类型
    command: STDIO 模式下的命令（如 "python", "uv"）
    args: STDIO 模式下的命令参数
    url: HTTP 模式下的服务器地址
    env: 环境变量

    使用示例:
    --------
    >>> # STDIO 模式
    >>> config = MCPServerConfig(
    ...     name="my-server",
    ...     transport=MCPTransportType.STDIO,
    ...     command="python",
    ...     args=["-m", "my_mcp_server"]
    ... )

    >>> # HTTP 模式
    >>> config = MCPServerConfig(
    ...     name="remote-server",
    ...     transport=MCPTransportType.STREAMABLE_HTTP,
    ...     url="http://localhost:8000/mcp"
    ... )
    """

    name: str
    transport: MCPTransportType
    command: str | None = None
    args: list[str] = field(default_factory=list)
    url: str | None = None
    env: dict[str, str] = field(default_factory=dict)


# ========================================
# 客户端协议
# ========================================


@runtime_checkable
class MCPClient(Protocol):
    """
    MCP 客户端协议 - 定义 MCP 客户端的标准接口

    这个协议定义了 MCP 客户端的"契约"：
    - 连接 MCP 服务器
    - 发现和调用工具
    - 读取资源
    - 获取 Prompt

    为什么需要这个协议?
    ---------------
    1. **抽象**: 业务代码不依赖具体的 MCP SDK 实现
    2. **可测试**: 可以轻松创建 mock 客户端
    3. **统一**: 提供一致的 API 风格

    设计决策:
    --------
    - 使用异步方法：MCP 操作通常是 I/O 密集的
    - 返回自定义数据类型：隔离 MCP SDK 的类型变化
    - 提供 context manager：方便资源管理
    """

    async def connect(self) -> None:
        """
        连接到 MCP 服务器

        注意:
        -----
        - 应该支持重连
        - 连接失败应该抛出异常
        """
        ...

    async def disconnect(self) -> None:
        """断开与 MCP 服务器的连接"""
        ...

    async def list_tools(self) -> list[MCPTool]:
        """
        获取服务器提供的所有工具

        返回:
        -----
        list[MCPTool]: 工具列表
        """
        ...

    async def call_tool(
        self, name: str, arguments: dict[str, Any] | None = None
    ) -> MCPToolResult:
        """
        调用工具

        参数:
        -----
        name: 工具名称
        arguments: 工具参数

        返回:
        -----
        MCPToolResult: 工具执行结果
        """
        ...

    async def list_resources(self) -> list[MCPResource]:
        """
        获取服务器提供的所有资源

        返回:
        -----
        list[MCPResource]: 资源列表
        """
        ...

    async def read_resource(self, uri: str) -> MCPResourceContent:
        """
        读取资源内容

        参数:
        -----
        uri: 资源 URI

        返回:
        -----
        MCPResourceContent: 资源内容
        """
        ...

    async def list_prompts(self) -> list[MCPPrompt]:
        """
        获取服务器提供的所有 Prompt

        返回:
        -----
        list[MCPPrompt]: Prompt 列表
        """
        ...

    async def get_prompt(
        self, name: str, arguments: dict[str, str] | None = None
    ) -> list[str]:
        """
        获取 Prompt 内容

        参数:
        -----
        name: Prompt 名称
        arguments: Prompt 参数

        返回:
        -----
        list[str]: Prompt 消息列表
        """
        ...


# ========================================
# Mock 客户端（用于测试）
# ========================================


class MockMCPClient:
    """
    Mock MCP 客户端 - 用于测试和学习

    这个客户端不连接真实的 MCP 服务器，而是返回预设的响应。
    用途:
    1. 在没有 MCP 服务器时测试代码
    2. 学习 MCP 调用流程
    3. 单元测试

    使用示例:
    --------
    >>> client = MockMCPClient(tools=[MCPTool(...)])
    >>> async with client:
    ...     tools = await client.list_tools()
    """

    def __init__(
        self,
        tools: list[MCPTool] | None = None,
        resources: list[MCPResource] | None = None,
        tool_results: dict[str, MCPToolResult] | None = None,
    ):
        """
        初始化 Mock 客户端

        参数:
        -----
        tools: 预设的工具列表
        resources: 预设的资源列表
        tool_results: 工具名到结果的映射
        """
        self._tools = tools or []
        self._resources = resources or []
        self._tool_results = tool_results or {}
        self._connected = False

    async def connect(self) -> None:
        """模拟连接"""
        self._connected = True

    async def disconnect(self) -> None:
        """模拟断开"""
        self._connected = False

    async def __aenter__(self) -> "MockMCPClient":
        """进入异步上下文"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """退出异步上下文"""
        await self.disconnect()

    async def list_tools(self) -> list[MCPTool]:
        """返回预设的工具列表"""
        return self._tools

    async def call_tool(
        self, name: str, arguments: dict[str, Any] | None = None
    ) -> MCPToolResult:
        """返回预设的工具结果"""
        if name in self._tool_results:
            return self._tool_results[name]
        return MCPToolResult(content=f"Mock result for {name}")

    async def list_resources(self) -> list[MCPResource]:
        """返回预设的资源列表"""
        return self._resources

    async def read_resource(self, uri: str) -> MCPResourceContent:
        """返回预设的资源内容"""
        return MCPResourceContent(uri=uri, text=f"Mock content for {uri}")

    async def list_prompts(self) -> list[MCPPrompt]:
        """返回空的 Prompt 列表"""
        return []

    async def get_prompt(
        self, name: str, arguments: dict[str, str] | None = None
    ) -> list[str]:
        """返回空的 Prompt 内容"""
        return [f"Mock prompt: {name}"]
