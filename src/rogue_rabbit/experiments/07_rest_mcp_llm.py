"""
实验 07: REST API + MCP Server + LLM 完整演示
==============================================

学习目标:
1. 理解三层架构: REST API -> MCP Server -> LLM Agent
2. 掌握进程间通信和异步协调
3. 体验 AI Agent 调用自定义 API 的完整流程

架构:
    用户 -> LLM Agent -> MCP Client -> MCP Server -> REST API

运行方式:
    python -m rogue_rabbit.experiments.07_rest_mcp_llm
"""

import asyncio
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

from rogue_rabbit.core import ReActAgent

# ========================================
# 配置检查
# ========================================


def check_api_key() -> bool:
    """检查 API key 是否配置"""
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
# REST 服务启动器
# ========================================


class RestServiceRunner:
    """REST 服务运行器 - 在后台线程运行 FastAPI"""

    def __init__(self, host: str = "127.0.0.1", port: int = 8000):
        self.host = host
        self.port = port
        self._thread = None

    def start(self):
        """启动 REST 服务"""
        import threading

        import uvicorn

        print(f"\n{'='*50}")
        print(f"[REST] 启动 REST API 服务...")
        print(f"[REST] 地址: http://{self.host}:{self.port}")
        print(f"[REST] 文档: http://{self.host}:{self.port}/docs")
        print(f"{'='*50}\n")

        def run_server():
            from rogue_rabbit.apps.rest.app import app

            # 使用 info 级别显示更多日志
            uvicorn.run(app, host=self.host, port=self.port, log_level="info")

        self._thread = threading.Thread(target=run_server, daemon=True)
        self._thread.start()
        time.sleep(2)  # 等待服务启动

    def stop(self):
        """停止服务（daemon 线程会自动停止）"""
        print(f"\n[REST] 服务已停止")


# ========================================
# 完整演示流程
# ========================================


async def run_demo():
    """运行完整演示"""
    print("=" * 60)
    print("实验 07: REST API + MCP Server + LLM")
    print("=" * 60)

    if not check_api_key():
        return

    # 1. 启动 REST 服务
    print("\n[步骤 1] 启动 REST 服务...")
    rest_service = RestServiceRunner()
    rest_service.start()

    # 2. 配置 MCP Server（STDIO 模式）
    print("\n[步骤 2] 配置 MCP Server...")
    from rogue_rabbit.adapters import create_mcp_client
    from rogue_rabbit.contracts.mcp import MCPServerConfig, MCPTransportType

    server_path = Path(__file__).parent.parent / "servers" / "rest_mcp_server.py"
    config = MCPServerConfig(
        name="rest-api-server",
        transport=MCPTransportType.STDIO,
        command=sys.executable,
        args=[str(server_path)],
        env={"REST_API_URL": "http://127.0.0.1:8000"},
    )
    print(f"  Server 路径: {server_path}")

    try:
        # 3. 连接 MCP Server
        print("\n[步骤 3] 连接 MCP Server...")
        async with create_mcp_client(config) as mcp_client:
            tools = await mcp_client.list_tools()
            print(f"[OK] 连接成功！发现 {len(tools)} 个工具:")
            for tool in tools:
                desc = tool.description[:50] + "..." if len(tool.description) > 50 else tool.description
                print(f"  - {tool.name}: {desc}")

            # 4. 测试直接调用工具
            print("\n[步骤 4] 测试直接调用工具...")
            result = await mcp_client.call_tool("list_items", {})
            result_text = result.text if hasattr(result, "text") else str(result)
            print(f"[工具结果]\n{result_text}")

            # 5. 创建 LLM Agent
            print("\n[步骤 5] 使用 LLM Agent 进行交互...")
            from rogue_rabbit.adapters import GLMClient

            llm_client = GLMClient()
            agent = ReActAgent(llm_client, mcp_client, max_iterations=8)

            # 6. 让 LLM 完成任务
            question = "请帮我查看有哪些物品，然后创建一个新物品叫 Grape，价格 5.0 元，库存 30 个"
            print(f"\n问题: {question}")

            answer = await agent.run(question)
            print(f"\n{'='*50}")
            print(f"最终答案: {answer}")

    except Exception as e:
        print(f"\n[错误] {e}")
        import traceback

        traceback.print_exc()

    finally:
        rest_service.stop()

    # 总结
    print("\n" + "=" * 60)
    print("学习总结")
    print("=" * 60)
    print("""
1. 三层架构:
   - REST API: 提供标准 HTTP 接口 (FastAPI)
   - MCP Server: 将 HTTP 接口封装为 AI 可调用的工具
   - LLM Agent: 通过自然语言理解和调用工具 (GLM + ReAct)

2. 关键技术:
   - FastAPI: 轻量级异步 REST 框架
   - FastMCP: 快速创建 MCP Server
   - STDIO 传输: 进程间通信
   - 后台线程: 运行 REST 服务

3. 扩展方向:
   - 添加更多 REST API 端点
   - 支持数据库持久化
   - 添加认证和授权
""")


async def main():
    """主入口"""
    await run_demo()


if __name__ == "__main__":
    asyncio.run(main())
