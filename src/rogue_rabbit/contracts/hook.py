"""
钩子（Hooks）协议定义

学习要点:
=========
1. 生命周期钩子：在 Agent 执行的关键节点拦截
2. 前置/后置拦截：在操作前后插入自定义逻辑
3. 洋葱模型：请求穿过多层钩子，每层可拦截或修改

为什么需要钩子?
==============
1. 正交扩展：不修改核心逻辑即可添加行为（如日志、计时、权限检查）
2. 解耦：将横切关注点从业务逻辑中分离
3. 灵活组合：按需注册不同钩子，实现不同的行为组合

钩子 vs 继承 vs 装饰器:
----------------------
- 继承: 修改父类行为，耦合度高
- 装饰器: 包装函数，但难以动态组合和移除
- 钩子: 注册/卸载机制，运行时可动态调整，适合 Agent 生命周期

参考设计:
--------
- Claude Code Hooks: 用户定义的 shell 命令，在特定生命周期点自动执行
- FastAPI Middleware: 洋葱模型，请求穿过多层中间件
- Django Signals: 事件驱动，解耦发送者和接收者
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


# ========================================
# 枚举
# ========================================


class HookEvent(str, Enum):
    """
    钩子事件类型

    生命周期顺序:
    ON_START → BEFORE_LLM_CALL → AFTER_LLM_CALL
            → BEFORE_TOOL_CALL → AFTER_TOOL_CALL
            → ON_ERROR (异常时)
            → ON_FINISH
    """

    ON_START = "on_start"
    ON_FINISH = "on_finish"
    BEFORE_LLM_CALL = "before_llm_call"
    AFTER_LLM_CALL = "after_llm_call"
    BEFORE_TOOL_CALL = "before_tool_call"
    AFTER_TOOL_CALL = "after_tool_call"
    ON_ERROR = "on_error"


# ========================================
# 数据模型
# ========================================


@dataclass
class HookContext:
    """
    钩子上下文

    每个钩子回调接收并返回 HookContext，实现数据在钩子链中传递。

    属性:
    -----
    - event: 触发的事件类型
    - data: 事件相关数据（钩子可读取和修改）
    - stopped: 是否短路（停止后续钩子执行）

    使用示例:
    --------
    >>> ctx = HookContext(event=HookEvent.BEFORE_LLM_CALL, data={"prompt": "hello"})
    >>> ctx.data["model"] = "gpt-4"   # 钩子修改数据
    >>> ctx.stopped = True             # 钩子短路
    """

    event: HookEvent
    data: dict[str, Any] = field(default_factory=dict)
    stopped: bool = False


# ========================================
# 类型别名
# ========================================


HookCallback = Callable[[HookContext], HookContext | None]
"""
钩子回调函数类型

接收 HookContext，返回:
- None: 不修改 context，继续传递
- HookContext: 替换 context（通常修改 data 或设置 stopped）
"""
