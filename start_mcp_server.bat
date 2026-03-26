@echo off
chcp 65001 >nul
echo ==================================================
echo RogueRabbit MCP Server
echo ==================================================
echo.
echo 启动 MCP Server (STDIO 模式)...
echo.
echo 注意:
echo   1. 请先启动 REST API 服务 (start_rest.bat)
echo   2. 此服务使用 STDIO 协议
echo   3. 需要由 MCP 客户端调用，或运行实验 07
echo.
echo 运行完整演示:
echo   python -m rogue_rabbit.experiments.07_rest_mcp_llm
echo.
echo ==================================================
echo.

python -m rogue_rabbit.servers.rest_mcp_server
