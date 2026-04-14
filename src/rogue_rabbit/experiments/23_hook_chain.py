"""
实验 23: 钩子链与优先级
=======================

学习目标:
--------
1. 理解优先级排序: priority 越大越先执行
2. 掌握短路机制: context.stopped = True 跳过后续钩子
3. 学会组合多个钩子实现实用场景

核心概念:
--------
- 优先级: 钩子按 priority 降序执行，实现顺序控制
- 短路: stopped=True 时停止传播，实现拦截/守卫
- 钩子组合: 日志 + 计时 + 权限检查等多钩子协同

运行方式:
--------
    python -m rogue_rabbit.experiments.23_hook_chain
"""

import time

from rogue_rabbit.contracts.hook import HookContext, HookEvent
from rogue_rabbit.core.hook_manager import HookManager


def demo_priority_order() -> None:
    """Demo 1: 优先级排序"""
    print("\n" + "=" * 60)
    print("Demo 1: 优先级排序")
    print("-" * 60)

    manager = HookManager()
    order: list[str] = []

    def make_hook(name: str):
        def hook(ctx: HookContext) -> HookContext:
            order.append(name)
            print(f"  [执行] {name}")
            return ctx
        return hook

    # 注册时 priority 不同
    manager.register(HookEvent.BEFORE_LLM_CALL, make_hook("日志钩子(priority=0)"), priority=0)
    manager.register(HookEvent.BEFORE_LLM_CALL, make_hook("权限钩子(priority=10)"), priority=10)
    manager.register(HookEvent.BEFORE_LLM_CALL, make_hook("限流钩子(priority=5)"), priority=5)

    print(f"[注册顺序] 日志(0) → 权限(10) → 限流(5)")
    print(f"[查询] 执行顺序: {manager.get_hooks(HookEvent.BEFORE_LLM_CALL)}")
    print(f"\n[触发]")

    manager.trigger(HookEvent.BEFORE_LLM_CALL, HookContext(event=HookEvent.BEFORE_LLM_CALL))
    print(f"\n[实际] {' → '.join(order)}")

    print("\n[要点] priority 越大越先执行: 权限(10) → 限流(5) → 日志(0)")


def demo_short_circuit() -> None:
    """Demo 2: 短路机制"""
    print("\n" + "=" * 60)
    print("Demo 2: 短路机制")
    print("-" * 60)

    manager = HookManager()
    order: list[str] = []

    def make_hook(name: str):
        def hook(ctx: HookContext) -> HookContext:
            order.append(name)
            print(f"  [执行] {name}")
            return ctx
        return hook

    # 守卫钩子: 如果没有 token，短路
    def auth_guard(ctx: HookContext) -> HookContext:
        order.append("auth_guard")
        print(f"  [执行] auth_guard")
        if not ctx.data.get("token"):
            print(f"  [拦截] 无 token，设置 stopped=True")
            ctx.stopped = True
            ctx.data["blocked"] = True
        return ctx

    # 注册: 守卫优先级最高
    manager.register(HookEvent.BEFORE_TOOL_CALL, auth_guard, priority=10)
    manager.register(HookEvent.BEFORE_TOOL_CALL, make_hook("tool_executor"), priority=5)
    manager.register(HookEvent.BEFORE_TOOL_CALL, make_hook("tool_logger"), priority=0)

    # 场景 1: 无 token - 短路
    print("[场景 1] 无 token")
    order.clear()
    ctx = HookContext(event=HookEvent.BEFORE_TOOL_CALL, data={})
    result = manager.trigger(HookEvent.BEFORE_TOOL_CALL, ctx)
    print(f"  执行顺序: {' → '.join(order)}")
    print(f"  结果: stopped={result.stopped}, blocked={result.data.get('blocked')}")

    # 场景 2: 有 token - 正常执行
    print(f"\n[场景 2] 有 token")
    order.clear()
    ctx2 = HookContext(event=HookEvent.BEFORE_TOOL_CALL, data={"token": "valid_token"})
    result2 = manager.trigger(HookEvent.BEFORE_TOOL_CALL, ctx2)
    print(f"  执行顺序: {' → '.join(order)}")
    print(f"  结果: stopped={result2.stopped}")

    print("\n[要点] 高优先级钩子通过 stopped=True 短路，跳过低优先级钩子")


def demo_hook_chain_realistic() -> None:
    """Demo 3: 实用场景——日志 + 计时 + 权限组合"""
    print("\n" + "=" * 60)
    print("Demo 3: 实用场景——日志 + 计时 + 权限组合")
    print("-" * 60)

    manager = HookManager()
    timings: dict[str, float] = {}

    # 权限检查钩子（最高优先级，先执行）
    def permission_check(ctx: HookContext) -> HookContext:
        user_role = ctx.data.get("user_role", "guest")
        if user_role == "guest":
            print(f"  [权限] 拒绝 guest 用户，短路!")
            ctx.stopped = True
            ctx.data["error"] = "Permission denied"
            return ctx
        print(f"  [权限] 用户角色={user_role}, 允许通过")
        return ctx

    # 计时钩子
    def timing_start(ctx: HookContext) -> HookContext:
        timings["start"] = time.time()
        return ctx

    def timing_end(ctx: HookContext) -> HookContext:
        elapsed = (time.time() - timings.get("start", time.time())) * 1000
        print(f"  [计时] 耗时 {elapsed:.1f}ms")
        return ctx

    # 日志钩子（最低优先级，最后执行）
    def log_before(ctx: HookContext) -> HookContext:
        print(f"  [日志] 开始处理: action={ctx.data.get('action')}, role={ctx.data.get('user_role')}")
        return ctx

    def log_after(ctx: HookContext) -> HookContext:
        print(f"  [日志] 处理完成: result={ctx.data.get('result', ctx.data.get('error', 'N/A'))}")
        return ctx

    # 注册前置钩子（权限 > 计时 > 日志）
    manager.register(HookEvent.BEFORE_TOOL_CALL, permission_check, priority=20)
    manager.register(HookEvent.BEFORE_TOOL_CALL, timing_start, priority=10)
    manager.register(HookEvent.BEFORE_TOOL_CALL, log_before, priority=0)

    # 注册后置钩子
    manager.register(HookEvent.AFTER_TOOL_CALL, log_after, priority=10)
    manager.register(HookEvent.AFTER_TOOL_CALL, timing_end, priority=0)

    # 场景 1: admin 用户 - 全部通过
    print("[场景 1] admin 用户")
    ctx = HookContext(event=HookEvent.BEFORE_TOOL_CALL, data={"action": "delete_file", "user_role": "admin"})
    result = manager.trigger(HookEvent.BEFORE_TOOL_CALL, ctx)
    if not result.stopped:
        # 模拟工具执行
        result.data["result"] = "文件已删除"
        manager.trigger(HookEvent.AFTER_TOOL_CALL, result)

    # 场景 2: guest 用户 - 被拦截
    print(f"\n[场景 2] guest 用户")
    ctx2 = HookContext(event=HookEvent.BEFORE_TOOL_CALL, data={"action": "delete_file", "user_role": "guest"})
    result2 = manager.trigger(HookEvent.BEFORE_TOOL_CALL, ctx2)
    if not result2.stopped:
        result2.data["result"] = "文件已删除"
        manager.trigger(HookEvent.AFTER_TOOL_CALL, result2)
    else:
        print(f"  [拦截] 请求被阻止，未执行工具")

    print("\n[要点] 多钩子按优先级协同: 权限守卫 → 计时 → 日志，短路避免无谓执行")


def demo_callback_return_none() -> None:
    """Demo 4: 回调返回 None vs 返回 Context"""
    print("\n" + "=" * 60)
    print("Demo 4: 回调返回 None vs 返回 Context")
    print("-" * 60)

    manager = HookManager()

    # 返回 None: 不修改 context
    def passive_hook(ctx: HookContext) -> HookContext | None:
        print(f"  [被动钩子] 只是观察，不修改")
        return None

    # 返回 context: 修改数据
    def active_hook(ctx: HookContext) -> HookContext:
        ctx.data["modified"] = True
        print(f"  [主动钩子] 修改了 data")
        return ctx

    manager.register(HookEvent.ON_START, passive_hook)
    manager.register(HookEvent.ON_START, active_hook)

    ctx = HookContext(event=HookEvent.ON_START, data={"original": True})
    result = manager.trigger(HookEvent.ON_START, ctx)

    print(f"\n[原始] data = {{'original': True}}")
    print(f"[结果] data = {result.data}")
    print("[要点] 返回 None 不影响 context，返回修改后的 context 才生效")


def main() -> None:
    """主函数"""
    print("=" * 60)
    print("实验 23: 钩子链与优先级")
    print("=" * 60)

    demo_priority_order()
    demo_short_circuit()
    demo_hook_chain_realistic()
    demo_callback_return_none()

    # 总结
    print("\n" + "=" * 60)
    print("学习总结")
    print("-" * 60)
    print("1. priority 越大越先执行，实现顺序控制")
    print("2. stopped=True 短路，高优先级钩子可拦截后续执行")
    print("3. 返回 None 不修改 context，返回 context 才生效")
    print("4. 实用组合: 权限守卫(高优先级) + 计时(中) + 日志(低)")
    print("5. 短路机制避免无谓执行，提升效率和安全")
    print("=" * 60)


if __name__ == "__main__":
    main()
