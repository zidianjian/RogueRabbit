"""
钩子管理器

学习要点:
=========
1. 注册/卸载机制：运行时动态管理钩子
2. 优先级排序：priority 越大越先执行
3. 短路机制：context.stopped = True 跳过后续钩子
4. 钩子链：多个钩子按顺序处理同一事件

设计思路:
========
HookManager 维护一个 event → [(hook_id, priority, callback)] 的映射。
- register: 注册回调，返回 hook_id 用于后续卸载
- trigger: 按 priority 降序执行回调，支持短路
- unregister: 通过 hook_id 卸载
"""

from collections import defaultdict

from rogue_rabbit.contracts.hook import HookCallback, HookContext, HookEvent


class HookManager:
    """
    钩子管理器

    使用示例:
    --------
    >>> manager = HookManager()
    >>>
    >>> def logging_hook(ctx: HookContext) -> HookContext:
    ...     print(f"[LOG] {ctx.event.value}: {ctx.data}")
    ...     return ctx
    ...
    >>> hook_id = manager.register(HookEvent.BEFORE_LLM_CALL, logging_hook)
    >>> ctx = manager.trigger(HookEvent.BEFORE_LLM_CALL, HookContext(event=HookEvent.BEFORE_LLM_CALL))
    >>> manager.unregister(hook_id)
    """

    def __init__(self) -> None:
        self._hooks: dict[HookEvent, list[tuple[str, int, HookCallback]]] = defaultdict(list)
        self._counter = 0

    def register(
        self, event: HookEvent, callback: HookCallback, priority: int = 0
    ) -> str:
        """
        注册钩子

        参数:
        -----
        - event: 监听的事件类型
        - callback: 钩子回调函数
        - priority: 优先级（越大越先执行，默认 0）

        返回:
        -----
        - hook_id: 用于后续卸载
        """
        hook_id = f"hook_{self._counter}"
        self._counter += 1
        self._hooks[event].append((hook_id, priority, callback))
        # 按 priority 降序排序（越大越先执行）
        self._hooks[event].sort(key=lambda x: -x[1])
        return hook_id

    def unregister(self, hook_id: str) -> bool:
        """
        卸载钩子

        参数:
        -----
        - hook_id: 注册时返回的 ID

        返回:
        -----
        - True: 成功卸载
        - False: 未找到该钩子
        """
        for event in self._hooks:
            for i, (hid, _, _) in enumerate(self._hooks[event]):
                if hid == hook_id:
                    self._hooks[event].pop(i)
                    return True
        return False

    def trigger(self, event: HookEvent, context: HookContext) -> HookContext:
        """
        触发事件的所有钩子

        按 priority 降序执行，支持短路：
        - 如果回调返回新的 HookContext，替换当前 context
        - 如果 context.stopped 为 True，停止执行

        参数:
        -----
        - event: 触发的事件
        - context: 钩子上下文

        返回:
        -----
        - 经过钩子链处理后的 HookContext
        """
        for _hook_id, _priority, callback in self._hooks.get(event, []):
            result = callback(context)
            if result is not None:
                context = result
            if context.stopped:
                break
        return context

    def get_hooks(self, event: HookEvent) -> list[tuple[str, int]]:
        """
        查询事件上已注册的钩子

        返回:
        -----
        - [(hook_id, priority), ...] 按优先级降序
        """
        return [(hid, pri) for hid, pri, _ in self._hooks.get(event, [])]

    def clear(self) -> None:
        """清空所有钩子"""
        self._hooks.clear()
