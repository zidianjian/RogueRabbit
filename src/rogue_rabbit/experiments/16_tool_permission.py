"""
实验 16: 工具调用权限
====================

学习目标:
--------
1. 理解如何为 MCP 工具调用添加权限控制
2. 掌握工具级别的权限策略设计
3. 学会将权限系统集成到 Agent 流程中

核心概念:
--------
- 工具权限：控制 Agent 可以调用哪些工具
- 资源权限：控制工具可以访问哪些资源
- 权限包装器：在工具调用前检查权限

运行方式:
--------
    python -m rogue_rabbit.experiments.16_tool_permission
"""

import logging

from rogue_rabbit.contracts.permission import (
    AccessRequest,
    Effect,
    Permission,
    Policy,
)
from rogue_rabbit.contracts.mcp import MCPTool, MCPToolResult
from rogue_rabbit.core.authorizer import Authorizer
from rogue_rabbit.runtime.policy_store import InMemoryPolicyStore

logging.basicConfig(level=logging.INFO, format="%(name)s - %(message)s")


# ============================================================
# 模拟工具
# ============================================================

def mock_calculator(expression: str) -> str:
    """模拟计算器工具"""
    try:
        result = eval(expression)  # 仅用于演示
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算错误: {e}"


def mock_file_reader(path: str) -> str:
    """模拟文件读取工具"""
    return f"[文件内容] {path}: 这是模拟的文件内容..."


def mock_file_writer(path: str, content: str) -> str:
    """模拟文件写入工具"""
    return f"[写入成功] {path}: 已写入 {len(content)} 字符"


def mock_network_request(url: str) -> str:
    """模拟网络请求工具"""
    return f"[HTTP 200] {url}: 响应内容..."


# ============================================================
# 权限感知的工具执行器
# ============================================================

class PermissionAwareExecutor:
    """
    权限感知的工具执行器

    在执行工具前检查权限，拒绝未授权的工具调用
    """

    def __init__(self, authorizer: Authorizer):
        self._authorizer = authorizer
        self._tools: dict[str, callable] = {}

    def register(self, name: str, func: callable) -> None:
        """注册工具"""
        self._tools[name] = func
        print(f"  [注册] 工具: {name}")

    def execute(self, tool_name: str, role: str, **kwargs) -> tuple[bool, str]:
        """
        执行工具（带权限检查）

        参数:
        -----
        tool_name: 工具名称
        role: 调用者角色
        **kwargs: 工具参数

        返回:
        -----
        (是否成功, 结果或错误信息)
        """
        # 权限检查
        request = AccessRequest(
            action="execute",
            resource=f"tool:{tool_name}",
            role=role,
            context={"tool_name": tool_name, "args": kwargs},
        )
        result = self._authorizer.check(request)

        if not result.allowed:
            return False, f"权限拒绝: {result.reason}"

        # 执行工具
        if tool_name not in self._tools:
            return False, f"工具不存在: {tool_name}"

        try:
            output = self._tools[tool_name](**kwargs)
            return True, output
        except Exception as e:
            return False, f"工具执行失败: {e}"


def demo_tool_permission() -> None:
    """Demo 1: 工具级别权限控制"""
    print("\n" + "=" * 60)
    print("Demo 1: 工具级别权限控制")
    print("-" * 60)

    store = InMemoryPolicyStore()
    authorizer = Authorizer(store=store)

    # 创建不同角色的策略
    policies = [
        Policy(
            name="admin-tools",
            role="admin",
            priority=10,
            permissions=[
                Permission(action="execute", resource="tool:*", effect=Effect.ALLOW),
            ],
        ),
        Policy(
            name="user-tools",
            role="user",
            priority=5,
            permissions=[
                Permission(action="execute", resource="tool:calculator", effect=Effect.ALLOW),
                Permission(action="execute", resource="tool:file_reader", effect=Effect.ALLOW),
                Permission(action="execute", resource="tool:file_writer", effect=Effect.DENY),
                Permission(action="execute", resource="tool:network_request", effect=Effect.DENY),
            ],
        ),
        Policy(
            name="guest-tools",
            role="guest",
            priority=1,
            permissions=[
                Permission(action="execute", resource="tool:calculator", effect=Effect.ALLOW),
            ],
        ),
    ]

    for policy in policies:
        authorizer.add_policy(policy)

    # 创建执行器并注册工具
    executor = PermissionAwareExecutor(authorizer)
    print("[工具注册]")
    executor.register("calculator", mock_calculator)
    executor.register("file_reader", mock_file_reader)
    executor.register("file_writer", mock_file_writer)
    executor.register("network_request", mock_network_request)

    # 测试不同角色的工具调用
    roles = ["admin", "user", "guest"]
    tools = [
        ("calculator", {"expression": "2 + 3"}),
        ("file_reader", {"path": "/data/report.txt"}),
        ("file_writer", {"path": "/data/output.txt", "content": "hello"}),
        ("network_request", {"url": "https://example.com"}),
    ]

    for role in roles:
        print(f"\n[角色] {role}:")
        for tool_name, kwargs in tools:
            success, output = executor.execute(tool_name, role, **kwargs)
            status = "成功" if success else "拒绝"
            print(f"  {status:4s} | {tool_name:16s} | {output[:50]}")

    print("\n[完成] 工具级别权限控制演示结束")


def demo_tool_resource_permission() -> None:
    """Demo 2: 工具 + 资源双重权限"""
    print("\n" + "=" * 60)
    print("Demo 2: 工具 + 资源双重权限")
    print("-" * 60)

    store = InMemoryPolicyStore()
    authorizer = Authorizer(store=store)

    # 可以使用 file_reader，但只能读 public 目录
    authorizer.add_policy(Policy(
        name="restricted-reader",
        role="restricted_user",
        permissions=[
            Permission(action="execute", resource="tool:file_reader", effect=Effect.ALLOW),
            Permission(action="read", resource="file:///public/*", effect=Effect.ALLOW),
            Permission(action="read", resource="file:///secret/*", effect=Effect.DENY),
        ],
    ))

    # 测试
    print("[策略] restricted_user 可以:")
    print("  - 执行 file_reader 工具")
    print("  - 读取 file:///public/* 下的文件")
    print("  - 不能读取 file:///secret/* 下的文件")

    test_cases = [
        ("execute", "tool:file_reader", "调用工具"),
        ("read", "file:///public/report.txt", "读公共文件"),
        ("read", "file:///secret/keys.pem", "读机密文件"),
        ("execute", "tool:file_writer", "调用写入工具"),
    ]

    print(f"\n[测试] 双重权限:")
    for action, resource, desc in test_cases:
        request = AccessRequest(action=action, resource=resource, role="restricted_user")
        result = authorizer.check(request)
        status = "允许" if result.allowed else "拒绝"
        print(f"  {status:4s} | {desc} ({action}:{resource})")

    print("\n[要点] 可以同时对工具调用和资源访问进行权限控制")


def demo_agent_flow() -> None:
    """Demo 3: 模拟 Agent 工具调用流程"""
    print("\n" + "=" * 60)
    print("Demo 3: 模拟 Agent 工具调用流程")
    print("-" * 60)

    store = InMemoryPolicyStore()
    authorizer = Authorizer(store=store)

    # Agent 角色策略
    authorizer.add_policy(Policy(
        name="agent-policy",
        role="agent",
        permissions=[
            Permission(action="execute", resource="tool:calculator", effect=Effect.ALLOW),
            Permission(action="execute", resource="tool:file_reader", effect=Effect.ALLOW),
            Permission(action="execute", resource="tool:file_writer", effect=Effect.ALLOW),
            Permission(action="execute", resource="tool:network_request", effect=Effect.DENY),
        ],
    ))

    executor = PermissionAwareExecutor(authorizer)
    executor.register("calculator", mock_calculator)
    executor.register("file_reader", mock_file_reader)
    executor.register("file_writer", mock_file_writer)
    executor.register("network_request", mock_network_request)

    # 模拟 Agent 执行任务
    print("[模拟] Agent 收到任务: '读取 data.txt 并计算文件长度'")
    print()

    # Step 1: 读取文件
    print("[Step 1] Agent 调用 file_reader")
    success, output = executor.execute("file_reader", "agent", path="/data/data.txt")
    print(f"  结果: {output}")
    if not success:
        print(f"  任务失败!")
        return

    # Step 2: 计算
    print("\n[Step 2] Agent 调用 calculator 计算长度")
    success, output = executor.execute("calculator", "agent", expression="len('模拟的文件内容')")
    print(f"  结果: {output}")

    # Step 3: 尝试写入（模拟一个需要确认的场景）
    print("\n[Step 3] Agent 尝试写入结果")
    success, output = executor.execute(
        "file_writer", "agent", path="/data/result.txt", content="计算结果: 7"
    )
    print(f"  结果: {output}")

    # Step 4: 尝试网络请求（应该被拒绝）
    print("\n[Step 4] Agent 尝试发送网络请求")
    success, output = executor.execute("network_request", "agent", url="https://external.com/api")
    print(f"  结果: {output}")

    print("\n[完成] Agent 工具调用流程演示结束")


def main() -> None:
    """主函数"""
    print("=" * 60)
    print("实验 16: 工具调用权限")
    print("=" * 60)

    demo_tool_permission()
    demo_tool_resource_permission()
    demo_agent_flow()

    # 总结
    print("\n" + "=" * 60)
    print("学习总结")
    print("-" * 60)
    print("1. 工具权限：通过 resource='tool:<name>' 控制工具调用")
    print("2. 角色分级：不同角色有不同的工具使用权限")
    print("3. 双重检查：可以同时对工具和资源进行权限控制")
    print("4. 权限包装器：在工具执行前检查权限，解耦权限与业务逻辑")
    print("5. Agent 流程：Agent 调用工具时自动进行权限检查")
    print("=" * 60)


if __name__ == "__main__":
    main()
