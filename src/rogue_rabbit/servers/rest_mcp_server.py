"""
REST API MCP Server - 将 REST API 封装为 MCP 工具

这个 MCP Server 连接到 RogueRabbit REST API，提供以下工具：
- list_items: 获取所有物品列表
- get_item: 获取单个物品详情
- create_item: 创建新物品
- update_item: 更新物品信息
- delete_item: 删除物品

运行方式:
    python -m rogue_rabbit.servers.rest_mcp_server

或作为 STDIO MCP 服务器被其他程序调用。
"""

import logging
import os
import sys

# 配置日志输出到 stderr（避免干扰 STDIO 通信）
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [MCP] %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stderr,
)
logger = logging.getLogger("mcp-server")

# 配置 REST API 地址
REST_API_BASE_URL = os.environ.get("REST_API_URL", "http://127.0.0.1:8000")

# 使用 FastMCP 创建 MCP Server
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("rogue-rabbit-rest")


# ========================================
# 工具定义
# ========================================


@mcp.tool()
async def list_items() -> str:
    """
    获取所有物品列表。

    返回所有可用物品的 ID、名称、价格和库存信息。
    """
    import httpx

    logger.info(">>> list_items() 被调用")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{REST_API_BASE_URL}/items/", timeout=5.0)
            if response.status_code == 200:
                items = response.json()
                logger.info(f"<<< list_items() -> 返回 {len(items)} 个物品")
                if not items:
                    return "当前没有物品"
                result = "物品列表:\n"
                for item in items:
                    result += f"- ID: {item['id']}, 名称: {item['name']}, 价格: {item['price']}, 库存: {item['quantity']}\n"
                return result
            logger.warning(f"<<< list_items() -> HTTP {response.status_code}")
            return f"获取物品列表失败: HTTP {response.status_code}"
        except httpx.ConnectError:
            logger.error(f"<<< list_items() -> 无法连接到 {REST_API_BASE_URL}")
            return f"无法连接到 REST API 服务 ({REST_API_BASE_URL})，请确保服务已启动"
        except Exception as e:
            logger.error(f"<<< list_items() -> 错误: {str(e)}")
            return f"获取物品列表出错: {str(e)}"


@mcp.tool()
async def get_item(item_id: int) -> str:
    """
    根据 ID 获取单个物品的详细信息。

    参数:
        item_id: 物品的唯一标识符（整数）
    """
    import httpx

    logger.info(f">>> get_item(item_id={item_id}) 被调用")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{REST_API_BASE_URL}/items/{item_id}", timeout=5.0
            )
            if response.status_code == 200:
                item = response.json()
                logger.info(f"<<< get_item(item_id={item_id}) -> 找到 '{item['name']}'")
                return f"物品详情: ID={item['id']}, 名称={item['name']}, 价格={item['price']}, 库存={item['quantity']}"
            elif response.status_code == 404:
                logger.warning(f"<<< get_item(item_id={item_id}) -> 404 未找到")
                return f"未找到 ID 为 {item_id} 的物品"
            logger.warning(f"<<< get_item(item_id={item_id}) -> HTTP {response.status_code}")
            return f"获取物品失败: HTTP {response.status_code}"
        except httpx.ConnectError:
            logger.error(f"<<< get_item(item_id={item_id}) -> 无法连接")
            return f"无法连接到 REST API 服务 ({REST_API_BASE_URL})"
        except Exception as e:
            logger.error(f"<<< get_item(item_id={item_id}) -> 错误: {str(e)}")
            return f"获取物品出错: {str(e)}"


@mcp.tool()
async def create_item(name: str, price: float, quantity: int = 0) -> str:
    """
    创建一个新物品。

    参数:
        name: 物品名称
        price: 物品价格（浮点数）
        quantity: 库存数量（整数，默认为0）
    """
    import httpx

    logger.info(f">>> create_item(name='{name}', price={price}, quantity={quantity}) 被调用")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{REST_API_BASE_URL}/items/",
                json={"name": name, "price": price, "quantity": quantity},
                timeout=5.0,
            )
            if response.status_code == 200:
                item = response.json()
                logger.info(f"<<< create_item(name='{name}') -> 成功创建 id={item['id']}")
                return f"成功创建物品: ID={item['id']}, 名称={item['name']}, 价格={item['price']}, 库存={item['quantity']}"
            logger.warning(f"<<< create_item(name='{name}') -> HTTP {response.status_code}")
            return f"创建物品失败: HTTP {response.status_code}"
        except httpx.ConnectError:
            logger.error(f"<<< create_item(name='{name}') -> 无法连接")
            return f"无法连接到 REST API 服务 ({REST_API_BASE_URL})"
        except Exception as e:
            logger.error(f"<<< create_item(name='{name}') -> 错误: {str(e)}")
            return f"创建物品出错: {str(e)}"


@mcp.tool()
async def update_item(item_id: int, name: str, price: float, quantity: int) -> str:
    """
    更新指定物品的信息。

    参数:
        item_id: 要更新的物品 ID（整数）
        name: 新的物品名称
        price: 新的价格（浮点数）
        quantity: 新的库存数量（整数）
    """
    import httpx

    logger.info(f">>> update_item(id={item_id}, name='{name}', price={price}, quantity={quantity}) 被调用")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.put(
                f"{REST_API_BASE_URL}/items/{item_id}",
                json={"name": name, "price": price, "quantity": quantity},
                timeout=5.0,
            )
            if response.status_code == 200:
                item = response.json()
                logger.info(f"<<< update_item(id={item_id}) -> 更新成功")
                return f"成功更新物品: ID={item['id']}, 名称={item['name']}, 价格={item['price']}, 库存={item['quantity']}"
            elif response.status_code == 404:
                logger.warning(f"<<< update_item(id={item_id}) -> 404 未找到")
                return f"未找到 ID 为 {item_id} 的物品"
            logger.warning(f"<<< update_item(id={item_id}) -> HTTP {response.status_code}")
            return f"更新物品失败: HTTP {response.status_code}"
        except httpx.ConnectError:
            logger.error(f"<<< update_item(id={item_id}) -> 无法连接")
            return f"无法连接到 REST API 服务 ({REST_API_BASE_URL})"
        except Exception as e:
            logger.error(f"<<< update_item(id={item_id}) -> 错误: {str(e)}")
            return f"更新物品出错: {str(e)}"


@mcp.tool()
async def delete_item(item_id: int) -> str:
    """
    删除指定物品。

    参数:
        item_id: 要删除的物品 ID（整数）
    """
    import httpx

    logger.info(f">>> delete_item(id={item_id}) 被调用")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.delete(
                f"{REST_API_BASE_URL}/items/{item_id}", timeout=5.0
            )
            if response.status_code == 200:
                logger.info(f"<<< delete_item(id={item_id}) -> 删除成功")
                return f"成功删除 ID 为 {item_id} 的物品"
            elif response.status_code == 404:
                logger.warning(f"<<< delete_item(id={item_id}) -> 404 未找到")
                return f"未找到 ID 为 {item_id} 的物品"
            logger.warning(f"<<< delete_item(id={item_id}) -> HTTP {response.status_code}")
            return f"删除物品失败: HTTP {response.status_code}"
        except httpx.ConnectError:
            logger.error(f"<<< delete_item(id={item_id}) -> 无法连接")
            return f"无法连接到 REST API 服务 ({REST_API_BASE_URL})"
        except Exception as e:
            logger.error(f"<<< delete_item(id={item_id}) -> 错误: {str(e)}")
            return f"删除物品出错: {str(e)}"


# ========================================
# 入口
# ========================================

if __name__ == "__main__":
    import sys

    # 启动日志输出到 stderr（不干扰 STDIO 协议）
    print("\n" + "=" * 50, file=sys.stderr)
    print("RogueRabbit MCP Server", file=sys.stderr)
    print("=" * 50, file=sys.stderr)
    print(f"REST API 地址: {REST_API_BASE_URL}", file=sys.stderr)
    print(f"可用工具:", file=sys.stderr)
    print(f"  - list_items: 获取所有物品列表", file=sys.stderr)
    print(f"  - get_item: 获取单个物品详情", file=sys.stderr)
    print(f"  - create_item: 创建新物品", file=sys.stderr)
    print(f"  - update_item: 更新物品信息", file=sys.stderr)
    print(f"  - delete_item: 删除物品", file=sys.stderr)
    print("", file=sys.stderr)
    print("运行方式:", file=sys.stderr)
    print("  python -m rogue_rabbit.servers.rest_mcp_server", file=sys.stderr)
    print("", file=sys.stderr)
    print("注意: 此服务使用 STDIO 协议，需要由 MCP 客户端调用", file=sys.stderr)
    print("=" * 50 + "\n", file=sys.stderr)

    # 以 STDIO 模式运行 MCP Server
    mcp.run()
