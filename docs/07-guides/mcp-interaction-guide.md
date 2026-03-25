# MCP 交互指南

本文档介绍 MCP (Model Context Protocol) 的核心概念和使用方式。

## 什么是 MCP？

MCP 是 Anthropic 推出的开放协议，用于连接 AI 助手与外部系统（工具、数据源等）。

### 解决的问题

在 MCP 出现之前：
- 每个 LLM 应用需要为每个工具写专门的集成代码
- 工具无法在不同应用间复用
- 集成成本高，维护困难

MCP 的解决方案：
- 提供统一的工具接口规范
- 工具服务器可被多个应用使用
- 一次开发，到处使用

## MCP 三大原语

### 1. Tool（工具）

Tool 是 MCP 最常用的原语，允许 LLM 调用外部函数。

```python
from rogue_rabbit.contracts import MCPTool, MCPToolInputSchema

tool = MCPTool(
    name="get_weather",
    description="获取指定城市的天气信息",
    input_schema=MCPToolInputSchema(
        properties={
            "city": {"type": "string", "description": "城市名称"}
        },
        required=["city"]
    )
)
```

### 2. Resource（资源）

Resource 用于暴露可读取的数据，如文件、数据库记录等。

```python
from rogue_rabbit.contracts import MCPResource

resource = MCPResource(
    uri="file:///config.json",
    name="配置文件",
    description="应用程序配置",
    mime_type="application/json"
)
```

### 3. Prompt（提示模板）

Prompt 是预定义的提示模板，可以被 LLM 复用。

```python
from rogue_rabbit.contracts import MCPPrompt, MCPPromptArgument

prompt = MCPPrompt(
    name="code_review",
    description="代码审查模板",
    arguments=[
        MCPPromptArgument(name="language", description="编程语言", required=True)
    ]
)
```

## 客户端使用

### Mock 客户端（学习/测试）

```python
from rogue_rabbit.contracts import MockMCPClient, MCPTool, MCPToolResult

# 创建工具和预设结果
tools = [MCPTool(name="echo", description="回显输入", input_schema=...)]
results = {"echo": MCPToolResult(content="hello")}

# 使用客户端
client = MockMCPClient(tools=tools, tool_results=results)
async with client:
    result = await client.call_tool("echo", {"text": "hello"})
    print(result.text)
```

### 真实 MCP 服务器

```python
from rogue_rabbit.contracts import MCPServerConfig, MCPTransportType
from rogue_rabbit.adapters import create_mcp_client

# STDIO 方式（本地进程）
config = MCPServerConfig(
    name="local-tools",
    transport=MCPTransportType.STDIO,
    command="python",
    args=["-m", "my_mcp_server"]
)

# HTTP 方式（远程服务）
config = MCPServerConfig(
    name="remote-tools",
    transport=MCPTransportType.STREAMABLE_HTTP,
    url="http://localhost:8000/mcp"
)

# 连接并使用
async with create_mcp_client(config) as client:
    tools = await client.list_tools()
    result = await client.call_tool("tool_name", {"arg": "value"})
```

## 传输方式

| 方式 | 适用场景 | 说明 |
|------|----------|------|
| STDIO | 本地工具、开发调试 | 通过标准输入输出通信 |
| STREAMABLE_HTTP | 远程服务、生产环境 | HTTP 长连接，支持流式响应 |
| SSE | 旧版兼容 | Server-Sent Events |

## Agent 模式

将 LLM 和 MCP 工具结合，构成 Agent 的核心能力：

```
用户问题 → LLM 思考 → 决定调用工具 → 执行工具 → 获取结果 → LLM 继续思考 → 最终答案
```

这就是 ReAct (Reasoning + Acting) 模式：

1. **Reasoning**: LLM 分析问题，决定下一步行动
2. **Acting**: 调用工具执行操作
3. **Observing**: 获取工具结果
4. **循环**: 直到得出最终答案

## 相关文件

- `contracts/mcp.py` - MCP 协议和数据模型定义
- `adapters/mcp_client.py` - MCP 客户端实现
- `experiments/04_mcp_basic.py` - 基础 MCP 调用示例
- `experiments/05_mcp_with_llm.py` - LLM + MCP 组合示例
- `notebooks/02_mcp_basics.ipynb` - MCP 学习 notebook

## 延伸阅读

- [MCP 官方规范](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
