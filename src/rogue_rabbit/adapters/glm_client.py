"""
GLM (智谱 AI) 客户端适配器

学习要点:
=========
1. 如何复用已有适配器
2. 通过配置 base_url 接入兼容 API
3. 使用 .env 文件管理敏感配置

GLM API 与 OpenAI 兼容:
=====================
- 相同的请求/响应格式
- 只需要配置 base_url 指向 GLM 的 API 地址
- 使用 GLM 的 API key

GLM 模型列表:
===========
- glm-4-flash: 快速版，性价比高
- glm-4: 标准版
- glm-4-plus: 增强版

使用示例:
========
>>> from rogue_rabbit.adapters import GLMClient
>>> client = GLMClient()  # 自动从 .env 读取 ZHIPU_API_KEY
>>> response = client.complete([Message(role=Role.USER, content="Hello")])
"""

import os
from pathlib import Path

from dotenv import load_dotenv

from rogue_rabbit.adapters.openai_client import OpenAIClient

# GLM API 地址
GLM_BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"

# 自动加载项目根目录的 .env 文件
_env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(_env_path)


class GLMClient(OpenAIClient):
    """
    GLM (智谱 AI) 客户端 - 继承自 OpenAIClient

    为什么可以继承?
    --------------
    GLM 的 API 完全兼容 OpenAI 格式：
    - 相同的消息结构
    - 相同的调用方式
    - 只需要改 base_url

    这样做的好处:
    ------------
    1. 复用代码，不需要重复实现
    2. 保持接口一致
    3. 方便切换不同的 LLM 提供商
    """

    def __init__(
        self,
        model: str = "glm-4-flash",
        api_key: str | None = None,
    ):
        """
        初始化 GLM 客户端

        参数:
        -----
        model: GLM 模型名称，默认 glm-4-flash（性价比高）
        api_key: 智谱 AI 的 API key。如果不传，会自动读取

        配置方式（按优先级）:
        -------------------
        1. 直接传入 api_key 参数
        2. 从 .env 文件读取 ZHIPU_API_KEY
        3. 从环境变量读取 ZHIPU_API_KEY

        使用示例:
        --------
        >>> # 方式 1: 使用 .env 文件（推荐）
        >>> # 在项目根目录创建 .env 文件:
        >>> # ZHIPU_API_KEY=your-api-key
        >>> client = GLMClient()
        >>>
        >>> # 方式 2: 直接传入
        >>> client = GLMClient(api_key="your-api-key")
        """
        # 如果没有传入 api_key，尝试从环境变量读取
        # load_dotenv 已经加载了 .env 文件到 os.environ
        if api_key is None:
            api_key = os.environ.get("ZHIPU_API_KEY")

        # 调用父类构造函数，固定使用 GLM 的 base_url
        super().__init__(
            model=model,
            api_key=api_key,
            base_url=GLM_BASE_URL,
        )
