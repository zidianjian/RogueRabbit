"""
实验 15: 基础权限检查
====================

学习目标:
--------
1. 理解权限模型：Permission（权限规则）和 Policy（策略）
2. 掌握通配符匹配：* 和 prefix:*
3. 理解 DENY 优先原则
4. 学会策略优先级（priority）

核心概念:
--------
- Permission: 单条权限规则（action + resource + effect）
- Policy: 一组权限规则的集合，绑定到角色
- AccessRequest: 访问请求（谁要做什么）
- AccessResult: 授权结果（允许/拒绝 + 原因）

运行方式:
--------
    python -m rogue_rabbit.experiments.15_permission_basic
"""

import logging

from rogue_rabbit.contracts.permission import (
    AccessRequest,
    AccessResult,
    Effect,
    Permission,
    Policy,
)
from rogue_rabbit.core.authorizer import Authorizer
from rogue_rabbit.runtime.policy_store import InMemoryPolicyStore

logging.basicConfig(level=logging.INFO, format="%(name)s - %(message)s")


def demo_basic_permission() -> None:
    """Demo 1: 基础权限规则"""
    print("\n" + "=" * 60)
    print("Demo 1: 基础权限规则")
    print("-" * 60)

    store = InMemoryPolicyStore()
    authorizer = Authorizer(store=store)

    # 创建用户策略
    user_policy = Policy(
        name="user-basic",
        role="user",
        description="普通用户基本权限",
        permissions=[
            Permission(action="read", resource="*", effect=Effect.ALLOW),
            Permission(action="execute", resource="tool:*", effect=Effect.ALLOW),
            Permission(action="write", resource="memory:*", effect=Effect.ALLOW),
            Permission(action="delete", resource="*", effect=Effect.DENY),
        ],
    )
    authorizer.add_policy(user_policy)
    print(f"[策略] 添加: {user_policy.name} (role={user_policy.role})")
    print(f"  权限规则数: {len(user_policy.permissions)}")
    for p in user_policy.permissions:
        print(f"  - {p.effect.value:5s} | {p.action:8s} | {p.resource}")

    # 测试各种请求
    test_cases = [
        ("user", "read", "file:///data/report.txt"),
        ("user", "execute", "tool:calculator"),
        ("user", "write", "memory:user1"),
        ("user", "delete", "file:///data/report.txt"),
        ("user", "write", "file:///data/report.txt"),
    ]

    print(f"\n[测试] 权限检查:")
    for role, action, resource in test_cases:
        request = AccessRequest(action=action, resource=resource, role=role)
        result = authorizer.check(request)
        status = "允许" if result.allowed else "拒绝"
        print(f"  {status:4s} | {role:5s} | {action:8s} | {resource}")
        print(f"       原因: {result.reason}")

    print("\n[完成] 基础权限规则演示结束")


def demo_deny_priority() -> None:
    """Demo 2: DENY 优先原则"""
    print("\n" + "=" * 60)
    print("Demo 2: DENY 优先原则")
    print("-" * 60)

    store = InMemoryPolicyStore()
    authorizer = Authorizer(store=store)

    # 创建一个同时有 ALLOW 和 DENY 的策略
    policy = Policy(
        name="conflicting-policy",
        role="editor",
        description="演示 DENY 优先原则",
        permissions=[
            Permission(action="*", resource="*", effect=Effect.ALLOW),
            Permission(action="delete", resource="file:*", effect=Effect.DENY),
        ],
    )
    authorizer.add_policy(policy)

    # 虽然有 ALLOW *:* 规则，但 delete file: 应该被 DENY
    print("[策略] 同时有 ALLOW *:* 和 DENY delete file:*")

    test_cases = [
        ("editor", "read", "file:data"),
        ("editor", "write", "file:data"),
        ("editor", "delete", "file:data"),
        ("editor", "execute", "tool:calculator"),
    ]

    print(f"\n[测试] DENY 优先:")
    for role, action, resource in test_cases:
        request = AccessRequest(action=action, resource=resource, role=role)
        result = authorizer.check(request)
        status = "允许" if result.allowed else "拒绝"
        print(f"  {status:4s} | {action:8s} | {resource}")
        if not result.allowed:
            print(f"       原因: {result.reason}")

    print("\n[要点] 即使有 ALLOW 规则，DENY 规则总是优先")


def demo_policy_priority() -> None:
    """Demo 3: 策略优先级"""
    print("\n" + "=" * 60)
    print("Demo 3: 策略优先级（priority）")
    print("-" * 60)

    store = InMemoryPolicyStore()
    authorizer = Authorizer(store=store)

    # 低优先级策略：允许读取
    low_policy = Policy(
        name="low-access",
        role="user",
        priority=1,
        permissions=[
            Permission(action="read", resource="*", effect=Effect.ALLOW),
        ],
    )

    # 高优先级策略：拒绝读取敏感文件
    high_policy = Policy(
        name="restrict-sensitive",
        role="user",
        priority=10,
        description="高优先级策略覆盖低优先级",
        permissions=[
            Permission(action="read", resource="file:///secret/*", effect=Effect.DENY),
        ],
    )

    authorizer.add_policy(low_policy)
    authorizer.add_policy(high_policy)

    print(f"[策略] 低优先级(1): read * ALLOW")
    print(f"[策略] 高优先级(10): read file:///secret/* DENY")

    test_cases = [
        ("user", "read", "file:///data/report.txt"),
        ("user", "read", "file:///secret/keys.pem"),
        ("user", "read", "memory:user1"),
    ]

    print(f"\n[测试] 优先级检查:")
    for role, action, resource in test_cases:
        request = AccessRequest(action=action, resource=resource, role=role)
        result = authorizer.check(request)
        status = "允许" if result.allowed else "拒绝"
        print(f"  {status:4s} | {action:8s} | {resource}")
        if result.matched_policy:
            print(f"       匹配策略: {result.matched_policy}")

    print("\n[要点] 高优先级策略的 DENY 可以覆盖低优先级策略的 ALLOW")


def demo_default_deny() -> None:
    """Demo 4: 默认拒绝"""
    print("\n" + "=" * 60)
    print("Demo 4: 默认拒绝（fail-safe）")
    print("-" * 60)

    store = InMemoryPolicyStore()
    authorizer = Authorizer(store=store)

    # 没有任何策略
    print("[策略] 无任何策略")

    request = AccessRequest(action="read", resource="file:data", role="unknown")
    result = authorizer.check(request)

    status = "允许" if result.allowed else "拒绝"
    print(f"\n[测试] 未知角色访问: {status}")
    print(f"  原因: {result.reason}")

    # 添加只读策略，但测试未覆盖的操作
    authorizer.add_policy(Policy(
        name="read-only",
        role="guest",
        permissions=[
            Permission(action="read", resource="*", effect=Effect.ALLOW),
        ],
    ))

    write_request = AccessRequest(action="write", resource="file:data", role="guest")
    write_result = authorizer.check(write_request)
    status = "允许" if write_result.allowed else "拒绝"
    print(f"\n[测试] guest 写文件: {status}")
    print(f"  原因: {write_result.reason}")

    print("\n[要点] 没有明确 ALLOW 的操作，默认拒绝（安全优先）")


def demo_wildcard_matching() -> None:
    """Demo 5: 通配符匹配"""
    print("\n" + "=" * 60)
    print("Demo 5: 通配符匹配")
    print("-" * 60)

    store = InMemoryPolicyStore()
    authorizer = Authorizer(store=store)

    authorizer.add_policy(Policy(
        name="tool-user",
        role="agent",
        permissions=[
            Permission(action="execute", resource="tool:*", effect=Effect.ALLOW),
            Permission(action="execute", resource="tool:network_*", effect=Effect.DENY),
        ],
    ))

    print("[规则] ALLOW execute tool:* (通配允许所有工具)")
    print("[规则] DENY  execute tool:network_* (拒绝网络工具)")

    test_cases = [
        ("agent", "execute", "tool:calculator"),
        ("agent", "execute", "tool:file_reader"),
        ("agent", "execute", "tool:code_review"),
        ("agent", "execute", "tool:network_client"),
        ("agent", "read", "tool:calculator"),
    ]

    print(f"\n[测试] 通配符匹配:")
    for role, action, resource in test_cases:
        request = AccessRequest(action=action, resource=resource, role=role)
        result = authorizer.check(request)
        status = "允许" if result.allowed else "拒绝"
        print(f"  {status:4s} | {action:8s} | {resource}")

    print("\n[要点] DENY 优先于 ALLOW，即使 ALLOW 范围更大")


def main() -> None:
    """主函数"""
    print("=" * 60)
    print("实验 15: 基础权限检查")
    print("=" * 60)

    demo_basic_permission()
    demo_deny_priority()
    demo_policy_priority()
    demo_default_deny()
    demo_wildcard_matching()

    # 总结
    print("\n" + "=" * 60)
    print("学习总结")
    print("-" * 60)
    print("1. Permission = action + resource + effect（操作 + 资源 + 效果）")
    print("2. Policy = 一组 Permission 的集合，绑定到 role")
    print("3. DENY 优先：同时有 ALLOW 和 DENY 时，DENY 生效")
    print("4. 策略优先级：priority 高的策略优先检查")
    print("5. 默认拒绝：没有匹配规则时自动 DENY（fail-safe）")
    print("6. 通配符：* 匹配所有，prefix:* 匹配前缀")
    print("=" * 60)


if __name__ == "__main__":
    main()
