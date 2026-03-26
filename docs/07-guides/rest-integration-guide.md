# REST + MCP + LLM 集成指南

本指南介绍如何将 REST API、MCP Server 和 LLM 串联起来，构建完整的 AI Agent 应用。

## 架构概览

```
┌──────────────┐     HTTP      ┌──────────────┐     STDIO     ┌──────────────┐
│    用户      │ ────────────► │   LLM Agent  │ ────────────► │  MCP Server  │
│  (自然语言)  │               │    (GLM)     │               │  (FastMCP)   │
└──────────────┘               └──────────────┘               └──────────────┘
                                                              │
                                                              │ HTTP
                                                              ▼
                                                       ┌──────────────┐
                                                       │   REST API   │
                                                       │  (FastAPI)   │
                                                       └──────────────┘
```

## 各层职责

| 层 | 技术 | 职责 |
|---|------|------|
| **REST API** | FastAPI | 提供标准 HTTP 接口（CRUD） |
| **MCP Server** | FastMCP | 将 HTTP 接口封装为 AI 可调用的工具 |
| **LLM Agent** | GLM + ReAct | 理解自然语言，决定调用哪些工具 |

## 快速开始

### 1. 启动 REST API

```bash
# 方式 1: 使用启动脚本
start_rest.bat

# 方式 2: 命令行
python -m rogue_rabbit.apps.rest.app

# 方式 3: uvicorn
uvicorn rogue_rabbit.apps.rest.app:app --reload --port 8000
```

服务启动后：
- API 地址: http://127.0.0.1:8000
- API 文档: http://127.0.0.1:8000/docs

### 2. 启动 MCP Server

```bash
# 方式 1: 使用启动脚本
start_mcp_server.bat

# 方式 2: 命令行
python -m rogue_rabbit.servers.rest_mcp_server
```

### 3. 运行完整演示

```bash
python -m rogue_rabbit.experiments.07_rest_mcp_llm
```

## REST API 设计

### 数据模型

```python
from pydantic import BaseModel

class ItemBase(BaseModel):
    name: str
    price: float
    quantity: int = 0

class Item(ItemBase):
    id: int
```

### API 端点

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/items/` | 获取所有物品 |
| GET | `/items/{id}` | 获取单个物品 |
| POST | `/items/` | 创建物品 |
| PUT | `/items/{id}` | 更新物品 |
| DELETE | `/items/{id}` | 删除物品 |

### 生命周期管理

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化
    _init_sample_data()
    yield
    # 关闭时清理
    _items_db.clear()
```

## MCP Server 设计

### 工具定义

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("rogue-rabbit-rest")

@mcp.tool()
async def list_items() -> str:
    """获取所有物品列表"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{REST_API_URL}/items/")
        # 格式化返回...
```

### 可用工具

| 工具 | 描述 |
|------|------|
| `list_items` | 获取所有物品列表 |
| `get_item` | 获取单个物品详情 |
| `create_item` | 创建新物品 |
| `update_item` | 更新物品信息 |
| `delete_item` | 删除物品 |

## LLM Agent 设计

### ReAct 模式

```
用户问题 → LLM 思考 → 决定调用工具 → 执行工具 → 获取结果 → LLM 继续思考 → 最终答案
```

### 示例流程

```
用户: "请查看有哪些物品，然后创建一个新物品 Grape"

[轮次 1]
THOUGHT: 首先查看现有物品
ACTION: list_items
ARGUMENTS: {}
OBSERVATION: Apple, Banana, Orange

[轮次 2]
THOUGHT: 已了解现有物品，创建 Grape
ACTION: create_item
ARGUMENTS: {"name": "Grape", "price": 3.0, "quantity": 30}
OBSERVATION: 成功创建 ID=4

[轮次 3]
ANSWER: 已查看物品列表并成功创建 Grape
```

## 日志系统

### REST API 日志

```
[15:30:45] INFO: [API] list_items() -> 返回 3 个物品
[15:30:46] INFO: [API] create_item(name=Grape, price=3.0, quantity=30)
[15:30:46] INFO: [API] create_item() -> 创建成功, id=4
```

### MCP Server 日志

```
[15:30:45] [MCP] >>> list_items() 被调用
[15:30:45] [MCP] <<< list_items() -> 返回 3 个物品
```

## 扩展指南

### 添加新的 REST API 端点

1. 在 `apps/rest/app.py` 添加路由
2. 在 `servers/rest_mcp_server.py` 添加对应工具

### 添加新的 MCP Server

1. 创建 `servers/my_mcp_server.py`
2. 使用 FastMCP 定义工具
3. 通过 STDIO 模式运行

## 相关文件

| 文件 | 描述 |
|------|------|
| `apps/rest/app.py` | REST API 应用 |
| `servers/rest_mcp_server.py` | MCP Server |
| `core/react_agent.py` | ReAct Agent |
| `experiments/07_rest_mcp_llm.py` | 完整演示 |
| `notebooks/03_rest_mcp_llm.ipynb` | 学习 notebook |
