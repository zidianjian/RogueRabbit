@echo off
chcp 65001 >nul
echo ==================================================
echo RogueRabbit REST API Server
echo ==================================================
echo.
echo 启动 REST API 服务...
echo 地址: http://127.0.0.1:8000
echo 文档: http://127.0.0.1:8000/docs
echo.
echo 按 Ctrl+C 停止服务
echo ==================================================
echo.

python -m rogue_rabbit.apps.rest.app
