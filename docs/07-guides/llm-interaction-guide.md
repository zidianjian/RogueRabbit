# LLM 交互学习指南

本指南帮助你理解 LLM 交互的核心原理和设计思想。

## 目录

1. [LLM 交互的本质](#llm-交互的本质)
2. [为什么需要 contracts 层](#为什么需要-contracts-层)
3. [为什么需要 adapters 层](#为什么需要-adapters-层)
4. [设计决策的思考过程](#设计决策的思考过程)
5. [常见问题](#常见问题)

---

## LLM 交互的本质

### 最简单的理解

LLM 交互就是**发送消息，接收回复**。

```python
# 伪代码
response = llm.send("你好")
print(response)  # "你好！有什么可以帮助你的？"
```

### 稍微复杂一点

实际上，你需要发送**消息列表**，而不是单条消息：

```python
messages = [
    {"role": "user", "content": "你好"}
]
response = llm.chat(messages)
```

### 真正的复杂性

多轮对话时，需要发送**完整的对话历史**：

```python
messages = [
    {"role": "user", "content": "我叫小明"},
    {"role": "assistant", "content": "你好小明！"},
    {"role": "user", "content": "我叫什么？"},  # AI 需要历史才能回答
]
response = llm.chat(messages)  # "你叫小明"
```

### 核心理解

```
┌─────────────────────────────────────────────────┐
│                  LLM 交互本质                    │
├─────────────────────────────────────────────────┤
│ 输入: 消息列表 [msg1, msg2, msg3, ...]          │
│ 输出: AI 的回复文本                              │
│ 特点: 无状态，每次需要完整历史                   │
└─────────────────────────────────────────────────┘
```

---

## 为什么需要 contracts 层

### 问题场景

假设你直接使用 OpenAI SDK：

```python
from openai import OpenAI

client = OpenAI()

def ask(question: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": question}]
    )
    return response.choices[0].message.content
```

**问题 1**: 如果想换成 Claude，需要改所有调用代码

**问题 2**: 测试时不想真的调用 API

**问题 3**: 代码里到处是 OpenAI 特有的格式

### 解决方案：定义协议

```python
# contracts/llm.py
from typing import Protocol

class LLMClient(Protocol):
    """LLM 客户端协议 - 统一的接口"""
    def complete(self, messages: list[Message]) -> str: ...
```

现在业务代码只依赖协议：

```python
def ask(client: LLMClient, question: str) -> str:
    messages = [Message(role=Role.USER, content=question)]
    return client.complete(messages)
```

### contracts 层的价值

```
┌─────────────────────────────────────────────────┐
│              contracts 层的价值                  │
├─────────────────────────────────────────────────┤
│ 1. 定义"做什么"而不是"怎么做"                    │
│ 2. 业务代码不依赖具体实现                        │
│ 3. 可以轻松替换实现（OpenAI → Claude）           │
│ 4. 方便测试（用 Mock 替换真实 API）              │
└─────────────────────────────────────────────────┘
```

---

## 为什么需要 adapters 层

### 问题场景

不同 LLM 的 API 格式不同：

```python
# OpenAI 格式
{"role": "user", "content": "你好"}

# Anthropic 格式
{"role": "user", "content": [{"type": "text", "text": "你好"}]}
```

如果没有适配层，业务代码需要处理这些差异。

### 解决方案：适配器模式

```python
# adapters/openai_client.py
class OpenAIClient:
    def complete(self, messages: list[Message]) -> str:
        # 1. 转换格式：内部 → OpenAI
        openai_messages = [
            {"role": msg.role.value, "content": msg.content}
            for msg in messages
        ]
        # 2. 调用 API
        response = self._client.chat.completions.create(...)
        # 3. 返回结果
        return response.choices[0].message.content
```

业务代码只需要：

```python
client = OpenAIClient()
response = client.complete(messages)  # 统一接口
```

### adapters 层的价值

```
┌─────────────────────────────────────────────────┐
│              adapters 层的价值                   │
├─────────────────────────────────────────────────┤
│ 1. 封装外部 API 的复杂性                         │
│ 2. 转换数据格式（内部 ↔ 外部）                   │
│ 3. 隔离外部变化（API 变化只影响适配器）          │
│ 4. 统一接口（所有 LLM 都用同样的方式调用）       │
└─────────────────────────────────────────────────┘
```

---

## 设计决策的思考过程

### 决策 1：为什么用 Protocol 而不是 ABC？

| 方面 | Protocol | ABC |
|------|----------|-----|
| 继承 | 不需要显式继承 | 需要显式继承 |
| 第三方库 | 容易适配 | 需要包装 |
| 类型检查 | 结构化子类型 | 名义子类型 |

**选择 Protocol**：更灵活，第三方库不需要修改就能适配。

### 决策 2：为什么 Message 用 dataclass？

```python
@dataclass(frozen=True)
class Message:
    role: Role
    content: str
```

- **简洁**：5 行代码 vs 手写 20+ 行
- **不可变**：`frozen=True` 防止意外修改
- **可读**：`Message(role=Role.USER, content="hi")` 很清晰

### 决策 3：为什么 complete() 返回 str 而不是对象？

```python
def complete(self, messages: list[Message]) -> str:
    ...
```

**阶段一原则**：保持简单，够用就好。

后续可以扩展：

```python
@dataclass
class LLMResponse:
    content: str
    usage: Usage
    model: str
    # ... 更多字段
```

### 决策 4：为什么没有异步版本？

**阶段一原则**：先跑通，再优化。

同步代码更容易理解和调试。后续版本可以添加：

```python
async def complete_async(self, messages: list[Message]) -> str:
    ...
```

---

## 常见问题

### Q1: 如何处理 API 错误？

阶段一暂时不处理，让错误抛出。后续可以添加：

```python
class LLMError(Exception):
    """LLM 调用错误"""

class RateLimitError(LLMError):
    """速率限制"""
```

### Q2: 如何控制生成参数（temperature 等）？

阶段一使用默认值。后续可以添加：

```python
@dataclass
class GenerateConfig:
    temperature: float = 1.0
    max_tokens: int = 1024

def complete(
    self,
    messages: list[Message],
    config: GenerateConfig | None = None
) -> str:
    ...
```

### Q3: 如何实现流式输出？

阶段一不支持。后续可以添加：

```python
def stream(
    self,
    messages: list[Message]
) -> Iterator[str]:
    """流式返回生成的文本"""
    ...
```

### Q4: 为什么不用 LangChain/LlamaIndex？

**学习目的**：先理解底层原理，再使用框架。

框架封装了很多细节，不利于学习。理解原理后，使用框架会更得心应手。

---

## 学习建议

1. **先跑通** `experiments/01_hello_llm.py`
2. **理解** Message 和 Role 的设计
3. **对比** contracts 和 adapters 的代码
4. **尝试** 添加一个新的适配器（如 Claude）
5. **阅读** 源码中的详细注释

---

## 下一步

- [ ] 运行 `python -m rogue_rabbit.experiments.01_hello_llm`
- [ ] 运行 `notebooks/01_llm_basics.ipynb`
- [ ] 阅读 `src/rogue_rabbit/contracts/messages.py`
- [ ] 阅读 `src/rogue_rabbit/adapters/openai_client.py`
- [ ] 尝试实现一个 MockLLMClient
