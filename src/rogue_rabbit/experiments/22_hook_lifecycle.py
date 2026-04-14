"""
实验 22: Agent 生命周期钩子
===========================

学习目标:
--------
1. 理解 Agent 执行循环中的生命周期事件
2. 掌握在各节点注册钩子并观察触发顺序
3. 学会 ON_ERROR 钩子拦截异常

核心概念:
--------
- Agent 生命周期: ON_START → BEFORE/AFTER_LLM → BEFORE/AFTER_TOOL → ON_FINISH
- 洋葱模型: 前置钩子从外到内，后置钩子从内到外
- ON_ERROR: 异常处理钩子，用于错误恢复或记录

运行方式:
--------
    python -m rogue_rabbit.experiments.22_hook_lifecycle
"""

from rogue_rabbit.contracts.hook import HookContext, HookEvent
from rogue_rabbit.core.hook_manager import HookManager


class SimpleAgent:
    """
    简化版 Agent，模拟 ReAct 循环

    用于演示钩子在 Agent 生命周期中的触发。
    不依赖真实的 LLM 和 MCP 客户端。
    """

    def __init__(self, hook_manager: HookManager | None = None) -> None:
        self.hooks = hook_manager or HookManager()
        self.tools = {"calculator": lambda x: str(eval(x)), "search": lambda q: f"搜索结果: {q}"}

    def run(self, question: str, fail_tool: bool = False) -> str:
        """
        模拟 Agent 执行循环

        参数:
        -----
        - question: 用户问题
        - fail_tool: 是否模拟工具调用失败
        """
        # ON_START
        ctx = HookContext(event=HookEvent.ON_START, data={"question": question})
        ctx = self.hooks.trigger(HookEvent.ON_START, ctx)

        # BEFORE_LLM_CALL
        ctx = HookContext(event=HookEvent.BEFORE_LLM_CALL, data={"question": question})
        ctx = self.hooks.trigger(HookEvent.BEFORE_LLM_CALL, ctx)

        # 模拟 LLM 响应（决定调用工具）
        llm_response = f"思考: 需要使用工具来回答 '{question}'"
        action = "calculator"
        action_input = "2 + 3"

        # AFTER_LLM_CALL
        ctx = HookContext(
            event=HookEvent.AFTER_LLM_CALL,
            data={"response": llm_response, "action": action, "action_input": action_input},
        )
        ctx = self.hooks.trigger(HookEvent.AFTER_LLM_CALL, ctx)

        # BEFORE_TOOL_CALL
        ctx = HookContext(
            event=HookEvent.BEFORE_TOOL_CALL,
            data={"tool": action, "arguments": action_input},
        )
        ctx = self.hooks.trigger(HookEvent.BEFORE_TOOL_CALL, ctx)

        # 模拟工具执行
        try:
            if fail_tool:
                raise PermissionError(f"工具 '{action}' 无权限")
            tool_result = self.tools.get(action, lambda x: "未知工具")(action_input)
        except Exception as e:
            # ON_ERROR
            err_ctx = HookContext(
                event=HookEvent.ON_ERROR,
                data={"error": str(e), "tool": action},
            )
            self.hooks.trigger(HookEvent.ON_ERROR, err_ctx)
            tool_result = f"错误: {e}"

        # AFTER_TOOL_CALL
        ctx = HookContext(
            event=HookEvent.AFTER_TOOL_CALL,
            data={"tool": action, "result": tool_result},
        )
        ctx = self.hooks.trigger(HookEvent.AFTER_TOOL_CALL, ctx)

        # ON_FINISH
        answer = f"答案: {tool_result}"
        ctx = HookContext(event=HookEvent.ON_FINISH, data={"answer": answer})
        ctx = self.hooks.trigger(HookEvent.ON_FINISH, ctx)

        return answer


def demo_lifecycle_flow() -> None:
    """Demo 1: 观察完整生命周期"""
    print("\n" + "=" * 60)
    print("Demo 1: 观察完整生命周期")
    print("-" * 60)

    manager = HookManager()
    flow: list[str] = []

    def trace_hook(ctx: HookContext) -> HookContext:
        summary = f"{ctx.event.value}"
        if ctx.data:
            key = list(ctx.data.keys())[0]
            summary += f" ({key}={ctx.data[key]})"
        flow.append(ctx.event.value)
        print(f"  [钩子] {summary}")
        return ctx

    # 为每个生命周期事件注册追踪钩子
    for event in HookEvent:
        manager.register(event, trace_hook)

    # 运行 Agent
    agent = SimpleAgent(manager)
    print("[开始] 运行 Agent...")
    answer = agent.run("计算 2+3")
    print(f"\n[结果] {answer}")
    print(f"[流序] {' → '.join(flow)}")

    print("\n[要点] Agent 循环: START → LLM前后 → TOOL前后 → FINISH")


def demo_lifecycle_hooks_with_data() -> None:
    """Demo 2: 钩子在各节点修改数据"""
    print("\n" + "=" * 60)
    print("Demo 2: 钩子在各节点修改数据")
    print("-" * 60)

    manager = HookManager()

    # 前置钩子: 注入 system prompt
    def inject_system_prompt(ctx: HookContext) -> HookContext:
        ctx.data["system_prompt"] = "你是一个数学助手"
        print(f"  [注入] system_prompt → {ctx.data['system_prompt']}")
        return ctx

    # 后置钩子: 记录 LLM 响应
    def log_llm_response(ctx: HookContext) -> HookContext:
        print(f"  [记录] LLM 决定使用工具: {ctx.data.get('action')}")
        return ctx

    # 工具后置: 校验结果
    def validate_tool_result(ctx: HookContext) -> HookContext:
        result = ctx.data.get("result", "")
        if "错误" in str(result):
            print(f"  [警告] 工具调用出错: {result}")
        else:
            print(f"  [校验] 工具结果正常: {result}")
        return ctx

    manager.register(HookEvent.BEFORE_LLM_CALL, inject_system_prompt)
    manager.register(HookEvent.AFTER_LLM_CALL, log_llm_response)
    manager.register(HookEvent.AFTER_TOOL_CALL, validate_tool_result)

    agent = SimpleAgent(manager)
    agent.run("计算 2+3")

    print("\n[要点] 钩子在各生命周期节点读取/修改数据，实现横切逻辑")


def demo_error_hook() -> None:
    """Demo 3: ON_ERROR 钩子拦截异常"""
    print("\n" + "=" * 60)
    print("Demo 3: ON_ERROR 钩子拦截异常")
    print("-" * 60)

    manager = HookManager()
    errors: list[str] = []

    def error_handler(ctx: HookContext) -> HookContext:
        error_msg = ctx.data.get("error", "unknown")
        tool = ctx.data.get("tool", "unknown")
        errors.append(f"{tool}: {error_msg}")
        print(f"  [错误处理] 工具={tool}, 错误={error_msg}")
        # 可以在这里实现重试、降级、通知等逻辑
        return ctx

    def finish_logger(ctx: HookContext) -> HookContext:
        print(f"  [结束] answer={ctx.data.get('answer')}")
        return ctx

    manager.register(HookEvent.ON_ERROR, error_handler)
    manager.register(HookEvent.ON_FINISH, finish_logger)

    agent = SimpleAgent(manager)
    print("[开始] 模拟工具调用失败...")
    answer = agent.run("计算 2+3", fail_tool=True)
    print(f"\n[结果] {answer}")
    print(f"[错误记录] {errors}")

    print("\n[要点] ON_ERROR 钩子统一处理异常，不侵入 Agent 核心逻辑")


def demo_tear_down() -> None:
    """Demo 4: 清理钩子"""
    print("\n" + "=" * 60)
    print("Demo 4: 完整流程后清理")
    print("-" * 60)

    manager = HookManager()

    counter = {"value": 0}

    def counting_hook(ctx: HookContext) -> HookContext:
        counter["value"] += 1
        return ctx

    manager.register(HookEvent.ON_START, counting_hook)
    manager.register(HookEvent.ON_FINISH, counting_hook)

    agent = SimpleAgent(manager)
    agent.run("第一次")
    print(f"[第一次] 钩子被调用 {counter['value']} 次")

    # 清理
    manager.clear()
    counter["value"] = 0

    agent2 = SimpleAgent(manager)
    agent2.run("第二次（清理后）")
    print(f"[第二次] 钩子被调用 {counter['value']} 次（应为 0，因为已清理）")

    print("\n[要点] clear() 清空所有钩子，适用于测试重置或会话切换")


def main() -> None:
    """主函数"""
    print("=" * 60)
    print("实验 22: Agent 生命周期钩子")
    print("=" * 60)

    demo_lifecycle_flow()
    demo_lifecycle_hooks_with_data()
    demo_error_hook()
    demo_tear_down()

    # 总结
    print("\n" + "=" * 60)
    print("学习总结")
    print("-" * 60)
    print("1. Agent 生命周期: START → LLM前后 → TOOL前后 → FINISH")
    print("2. 洋葱模型: 前置钩子准备数据，后置钩子处理结果")
    print("3. ON_ERROR: 统一的异常处理入口，不侵入核心逻辑")
    print("4. 钩子让横切关注点（日志、计时、权限）与业务逻辑解耦")
    print("5. clear() 用于测试重置或会话切换场景")
    print("=" * 60)


if __name__ == "__main__":
    main()
