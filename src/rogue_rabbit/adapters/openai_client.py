"""
OpenAI 客户端适配器 - 将 OpenAI API 封装成统一接口

学习要点:
=========
1. 什么是适配器模式？为什么需要它？
2. 如何封装第三方 API？
3. 如何将外部格式转换为内部格式

适配器模式:
==========
适配器的作用是"转换接口"：
- 外部：OpenAI SDK 的 API 格式
- 内部：我们定义的 Message/LLMClient 协议

这样做的价值:
-----------
1. **隔离变化**: OpenAI API 变化只影响这个文件
2. **统一接口**: 业务代码不需要关心是 OpenAI 还是 Claude
3. **便于测试**: 可以轻松替换成 Mock 客户端

代码结构:
========
1. __init__: 初始化 OpenAI 客户端
2. complete: 实现 LLMClient 协议
   - 转换消息格式（内部 → OpenAI）
   - 调用 OpenAI API
   - 返回结果
"""

from openai import OpenAI

from rogue_rabbit.contracts import LLMClient, Message


class OpenAIClient:
    """
    OpenAI 适配器 - 实现 LLMClient 协议

    这个类把 OpenAI 的 API 封装成我们定义的统一接口。
    业务代码只需要知道 LLMClient 协议，不需要知道 OpenAI 的细节。

    属性:
    -----
    _client: OpenAI SDK 的客户端实例（延迟初始化）
    _model: 使用的模型名称
    _api_key: API 密钥（可选）

    使用示例:
    --------
    >>> client = OpenAIClient(model="gpt-4o-mini")
    >>> messages = [Message(role=Role.USER, content="你好")]
    >>> response = client.complete(messages)
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        """
        初始化 OpenAI 客户端

        参数:
        -----
        model: 模型名称，默认使用 gpt-4o-mini（性价比高）
        api_key: API 密钥（可选）。如果不传，会从 OPENAI_API_KEY 环境变量读取
        base_url: API 地址（可选）。用于配置兼容 OpenAI 格式的其他服务

        配置 GLM (智谱 AI):
        ------------------
        >>> client = OpenAIClient(
        ...     model="glm-4-flash",
        ...     api_key="your-zhipu-api-key",
        ...     base_url="https://open.bigmodel.cn/api/paas/v4/"
        ... )

        注意:
        -----
        - 延迟初始化：创建对象时不立即连接，调用 complete 时才初始化客户端
        - 这样可以在没有 API key 的情况下导入和检查代码
        """
        self._client: OpenAI | None = None
        self._model = model
        self._api_key = api_key
        self._base_url = base_url

    def _get_client(self) -> OpenAI:
        """
        获取或创建 OpenAI 客户端（延迟初始化）

        为什么延迟初始化?
        ----------------
        1. 允许在没有 API key 时导入模块
        2. 方便单元测试时 mock
        3. 只有真正需要时才连接
        """
        if self._client is None:
            self._client = OpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
            )
        return self._client

    def complete(self, messages: list[Message]) -> str:
        """
        发送消息给 OpenAI，获取回复

        实现步骤:
        --------
        1. 将内部 Message 格式转换为 OpenAI 需要的格式
        2. 调用 OpenAI Chat Completions API
        3. 提取并返回回复文本

        参数:
        -----
        messages: 内部格式的消息列表

        返回:
        -----
        str: LLM 的回复文本

        OpenAI API 调用说明:
        -------------------
        client.chat.completions.create() 是核心方法:
        - model: 模型名称
        - messages: 消息列表，格式为 [{"role": "user", "content": "..."}]

        响应结构:
        - response.choices[0].message.content 是回复内容
        - choices 是因为有多个可能的回复（n 参数）
        """
        # Step 1: 转换消息格式
        # 内部格式: Message(role=Role.USER, content="你好")
        # OpenAI 格式: {"role": "user", "content": "你好"}
        openai_messages = [
            {"role": msg.role.value, "content": msg.content}
            for msg in messages
        ]

        # Step 2: 调用 OpenAI API
        response = self._get_client().chat.completions.create(
            model=self._model,
            messages=openai_messages,
        )

        # Step 3: 提取并返回回复
        return response.choices[0].message.content or ""
