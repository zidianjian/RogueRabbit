"""
实验 21: 基础钩子
================

学习目标:
--------
1. 理解钩子机制：在特定事件点注册和触发回调
2. 掌握 HookContext：钩子之间传递数据的载体
3. 学会注册和卸载：运行时动态管理钩子

核心概念:
--------
- HookEvent: 钩子事件类型（生命周期节点）
- HookContext: 钩子上下文（事件 + 数据 + 短路标志）
- HookCallback: 钩子回调函数
- HookManager: 钩子管理器（注册/触发/卸载）

运行方式:
--------
    python -m rogue_rabbit.experiments.21_hook_basic
"""

from rogue_rabbit.contracts.hook import HookContext, HookEvent
from rogue_rabbit.core.hook_manager import HookManager


def demo_basic_register_trigger() -> None:
    """Demo 1: 注册和触发单个钩子"""
    print("\n" + "=" * 60)
    print("Demo 1: 注册和触发单个钩子")
    print("-" * 60)

    manager = HookManager()

    # 定义一个简单的钩子
    def on_before_llm(ctx: HookContext) -> HookContext:
        print(f"  [钩子] 事件: {ctx.event.value}, 数据: {ctx.data}")
        return ctx

    # 注册钩子
    hook_id = manager.register(HookEvent.BEFORE_LLM_CALL, on_before_llm)
    print(f"[注册] hook_id = {hook_id}")
    print(f"[查询] BEFORE_LLM_CALL 上的钩子: {manager.get_hooks(HookEvent.BEFORE_LLM_CALL)}")

    # 触发事件
    ctx = HookContext(event=HookEvent.BEFORE_LLM_CALL, data={"prompt": "你好"})
    print(f"\n[触发] BEFORE_LLM_CALL")
    result = manager.trigger(HookEvent.BEFORE_LLM_CALL, ctx)
    print(f"[结果] data = {result.data}, stopped = {result.stopped}")

    print("\n[要点] register() 注册回调，trigger() 按优先级执行所有回调")


def demo_modify_context() -> None:
    """Demo 2: 钩子修改 context.data"""
    print("\n" + "=" * 60)
    print("Demo 2: 钩子修改 context.data")
    print("-" * 60)

    manager = HookManager()

    # 钩子 1: 添加默认 model
    def set_default_model(ctx: HookContext) -> HookContext:
        if "model" not in ctx.data:
            ctx.data["model"] = "glm-4"
            print(f"  [钩子] 设置默认 model: glm-4")
        return ctx

    # 钩子 2: 添加 timestamp
    def add_timestamp(ctx: HookContext) -> HookContext:
        from datetime import datetime
        ctx.data["timestamp"] = datetime.now().isoformat()
        print(f"  [钩子] 添加 timestamp")
        return ctx

    manager.register(HookEvent.BEFORE_LLM_CALL, set_default_model)
    manager.register(HookEvent.BEFORE_LLM_CALL, add_timestamp)

    # 触发 - 初始数据没有 model，钩子会添加
    ctx = HookContext(event=HookEvent.BEFORE_LLM_CALL, data={"prompt": "hello"})
    print(f"[触发前] data = {ctx.data}")
    result = manager.trigger(HookEvent.BEFORE_LLM_CALL, ctx)
    print(f"[触发后] data = {result.data}")

    # 触发 - 初始数据已有 model，钩子不会覆盖
    ctx2 = HookContext(event=HookEvent.BEFORE_LLM_CALL, data={"prompt": "hi", "model": "gpt-4"})
    print(f"\n[触发前] data = {ctx2.data}")
    result2 = manager.trigger(HookEvent.BEFORE_LLM_CALL, ctx2)
    print(f"[触发后] data = {result2.data}")

    print("\n[要点] 钩子通过修改 ctx.data 影响后续处理流程")


def demo_unregister() -> None:
    """Demo 3: 卸载钩子"""
    print("\n" + "=" * 60)
    print("Demo 3: 卸载钩子")
    print("-" * 60)

    manager = HookManager()
    call_log: list[str] = []

    def hook_a(ctx: HookContext) -> HookContext:
        call_log.append("A")
        return ctx

    def hook_b(ctx: HookContext) -> HookContext:
        call_log.append("B")
        return ctx

    id_a = manager.register(HookEvent.ON_START, hook_a)
    id_b = manager.register(HookEvent.ON_START, hook_b)

    # 触发 - 两个钩子都执行
    manager.trigger(HookEvent.ON_START, HookContext(event=HookEvent.ON_START))
    print(f"[触发] 两个钩子执行: {call_log}")

    # 卸载 A
    success = manager.unregister(id_a)
    print(f"\n[卸载] hook_id={id_a}, 成功={success}")
    print(f"[查询] 剩余钩子: {manager.get_hooks(HookEvent.ON_START)}")

    # 再次触发 - 只有 B 执行
    call_log.clear()
    manager.trigger(HookEvent.ON_START, HookContext(event=HookEvent.ON_START))
    print(f"[触发] 只剩 B 执行: {call_log}")

    # 卸载不存在的 ID
    success2 = manager.unregister("hook_999")
    print(f"\n[卸载] hook_id=hook_999, 成功={success2}")

    print("\n[要点] unregister() 通过 hook_id 动态移除钩子")


def demo_multiple_events() -> None:
    """Demo 4: 监听多个事件"""
    print("\n" + "=" * 60)
    print("Demo 4: 监听多个事件")
    print("-" * 60)

    manager = HookManager()
    event_log: list[str] = []

    def logger_hook(ctx: HookContext) -> HookContext:
        event_log.append(ctx.event.value)
        return ctx

    # 同一个回调注册到多个事件
    manager.register(HookEvent.ON_START, logger_hook)
    manager.register(HookEvent.BEFORE_LLM_CALL, logger_hook)
    manager.register(HookEvent.AFTER_LLM_CALL, logger_hook)
    manager.register(HookEvent.ON_FINISH, logger_hook)

    # 模拟 Agent 循环
    print("[模拟] Agent 执行流程:")
    for event in [HookEvent.ON_START, HookEvent.BEFORE_LLM_CALL,
                  HookEvent.AFTER_LLM_CALL, HookEvent.ON_FINISH]:
        print(f"  → {event.value}")
        manager.trigger(event, HookContext(event=event))

    print(f"\n[记录] 事件流: {' → '.join(event_log)}")
    print("[要点] 同一个钩子可以注册到多个事件，实现统一日志")


def main() -> None:
    """主函数"""
    print("=" * 60)
    print("实验 21: 基础钩子")
    print("=" * 60)

    demo_basic_register_trigger()
    demo_modify_context()
    demo_unregister()
    demo_multiple_events()

    # 总结
    print("\n" + "=" * 60)
    print("学习总结")
    print("-" * 60)
    print("1. HookEvent: 定义 Agent 生命周期中的拦截点")
    print("2. HookContext: 钩子上下文，承载事件数据，支持短路")
    print("3. HookCallback: 接收 HookContext，返回 None 或修改后的 context")
    print("4. HookManager: 管理钩子的注册、触发和卸载")
    print("5. 同一回调可注册到多个事件，实现横切关注点")
    print("=" * 60)


if __name__ == "__main__":
    main()
