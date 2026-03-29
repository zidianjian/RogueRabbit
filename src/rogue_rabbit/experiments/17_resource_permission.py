"""
实验 17: 资源访问控制
====================

学习目标:
--------
1. 理解资源级别的访问控制
2. 掌握基于角色的资源保护
3. 学会保护 Memory、Session、文件等资源
4. 理解多策略组合的权限效果

核心概念:
--------
- 资源保护：控制谁可以访问哪些数据
- RBAC（基于角色的访问控制）：通过角色分配权限
- 最小权限原则：只授予完成任务所需的最小权限
- 资源命名空间：通过前缀组织资源（memory:, file:, session:）

运行方式:
--------
    python -m rogue_rabbit.experiments.17_resource_permission
"""

import logging
from pathlib import Path

from rogue_rabbit.contracts.permission import (
    AccessRequest,
    Effect,
    Permission,
    Policy,
)
from rogue_rabbit.core.authorizer import Authorizer
from rogue_rabbit.runtime.policy_store import InMemoryPolicyStore, FilePolicyStore

logging.basicConfig(level=logging.INFO, format="%(name)s - %(message)s")


def demo_memory_protection() -> None:
    """Demo 1: 记忆资源保护"""
    print("\n" + "=" * 60)
    print("Demo 1: 记忆（Memory）资源保护")
    print("-" * 60)

    store = InMemoryPolicyStore()
    authorizer = Authorizer(store=store)

    # 用户只能读写自己的记忆，管理员可以访问所有
    policies = [
        Policy(
            name="memory-owner",
            role="user",
            priority=5,
            permissions=[
                Permission(action="read", resource="memory:user1", effect=Effect.ALLOW),
                Permission(action="write", resource="memory:user1", effect=Effect.ALLOW),
                Permission(action="delete", resource="memory:*", effect=Effect.DENY),
            ],
        ),
        Policy(
            name="memory-admin",
            role="admin",
            priority=10,
            permissions=[
                Permission(action="*", resource="memory:*", effect=Effect.ALLOW),
            ],
        ),
    ]
    for p in policies:
        authorizer.add_policy(p)

    print("[策略] user: 可读写自己的记忆(user1)，不能删除")
    print("[策略] admin: 完全控制所有记忆")

    # 测试 user
    print(f"\n[测试] user 角色访问记忆:")
    test_cases = [
        ("user", "read", "memory:user1"),
        ("user", "write", "memory:user1"),
        ("user", "delete", "memory:user1"),
        ("user", "read", "memory:user2"),
    ]
    for role, action, resource in test_cases:
        request = AccessRequest(action=action, resource=resource, role=role)
        result = authorizer.check(request)
        status = "允许" if result.allowed else "拒绝"
        print(f"  {status:4s} | {action:8s} | {resource}")

    # 测试 admin
    print(f"\n[测试] admin 角色访问记忆:")
    admin_cases = [
        ("admin", "read", "memory:user1"),
        ("admin", "write", "memory:user2"),
        ("admin", "delete", "memory:user1"),
    ]
    for role, action, resource in admin_cases:
        request = AccessRequest(action=action, resource=resource, role=role)
        result = authorizer.check(request)
        status = "允许" if result.allowed else "拒绝"
        print(f"  {status:4s} | {action:8s} | {resource}")

    print("\n[要点] 用户只能访问自己的记忆，管理员拥有完全控制权")


def demo_file_protection() -> None:
    """Demo 2: 文件资源保护"""
    print("\n" + "=" * 60)
    print("Demo 2: 文件资源保护")
    print("-" * 60)

    store = InMemoryPolicyStore()
    authorizer = Authorizer(store=store)

    # 基于目录的文件保护
    policies = [
        Policy(
            name="public-files",
            role="user",
            priority=1,
            permissions=[
                Permission(action="read", resource="file:///public/*", effect=Effect.ALLOW),
                Permission(action="write", resource="file:///public/user_*", effect=Effect.ALLOW),
            ],
        ),
        Policy(
            name="protect-private",
            role="user",
            priority=5,
            permissions=[
                Permission(action="*", resource="file:///private/*", effect=Effect.DENY),
            ],
        ),
        Policy(
            name="protect-system",
            role="user",
            priority=10,
            permissions=[
                Permission(action="*", resource="file:///system/*", effect=Effect.DENY),
            ],
        ),
    ]
    for p in policies:
        authorizer.add_policy(p)

    print("[策略] user 可读 public/*, 可写 public/user_*")
    print("[策略] user 不能访问 private/* 和 system/*")

    test_cases = [
        ("user", "read", "file:///public/report.txt", "读公共文件"),
        ("user", "write", "file:///public/user_data.txt", "写用户文件"),
        ("user", "write", "file:///public/system.cfg", "写公共系统配置"),
        ("user", "read", "file:///private/user1.txt", "读私有文件"),
        ("user", "read", "file:///system/config.ini", "读系统文件"),
        ("user", "delete", "file:///public/old.txt", "删除公共文件"),
    ]

    print(f"\n[测试] 文件访问:")
    for role, action, resource, desc in test_cases:
        request = AccessRequest(action=action, resource=resource, role=role)
        result = authorizer.check(request)
        status = "允许" if result.allowed else "拒绝"
        print(f"  {status:4s} | {desc}")
        print(f"       {action}:{resource}")

    print("\n[要点] 通过文件路径前缀实现目录级别的保护")


def demo_rbac() -> None:
    """Demo 3: 基于角色的访问控制（RBAC）"""
    print("\n" + "=" * 60)
    print("Demo 3: 基于角色的访问控制（RBAC）")
    print("-" * 60)

    store = InMemoryPolicyStore()
    authorizer = Authorizer(store=store)

    # 定义三种角色：guest < user < admin
    roles_config = [
        ("guest", [
            Permission(action="read", resource="file:///public/*", effect=Effect.ALLOW),
            Permission(action="execute", resource="tool:calculator", effect=Effect.ALLOW),
        ]),
        ("user", [
            Permission(action="read", resource="*", effect=Effect.ALLOW),
            Permission(action="write", resource="memory:*", effect=Effect.ALLOW),
            Permission(action="write", resource="file:///public/*", effect=Effect.ALLOW),
            Permission(action="execute", resource="tool:*", effect=Effect.ALLOW),
            Permission(action="delete", resource="*", effect=Effect.DENY),
        ]),
        ("admin", [
            Permission(action="*", resource="*", effect=Effect.ALLOW),
        ]),
    ]

    for role_name, permissions in roles_config:
        authorizer.add_policy(Policy(
            name=f"rbac-{role_name}",
            role=role_name,
            priority={"guest": 1, "user": 5, "admin": 10}[role_name],
            permissions=permissions,
        ))

    # 对比不同角色的权限
    operations = [
        ("read", "file:///public/readme.txt"),
        ("execute", "tool:calculator"),
        ("write", "memory:user1"),
        ("execute", "tool:file_writer"),
        ("delete", "file:///public/old.txt"),
        ("read", "file:///system/config"),
    ]

    print(f"\n{'操作':8s} {'资源':32s} {'guest':6s} {'user':6s} {'admin':6s}")
    print("-" * 70)

    for action, resource in operations:
        results = []
        for role_name, _ in roles_config:
            request = AccessRequest(action=action, resource=resource, role=role_name)
            result = authorizer.check(request)
            results.append("允许" if result.allowed else "拒绝")
        print(f"{action:8s} {resource:32s} {results[0]:6s} {results[1]:6s} {results[2]:6s}")

    print("\n[要点] RBAC 通过角色分层，实现递增的权限控制")


def demo_policy_persistence() -> None:
    """Demo 4: 策略文件持久化"""
    print("\n" + "=" * 60)
    print("Demo 4: 策略文件持久化")
    print("-" * 60)

    import json

    store_path = Path(__file__).parent.parent.parent.parent / "tmp_policies"
    file_store = FilePolicyStore(store_path)

    # 创建并保存策略
    policy = Policy(
        name="demo-policy",
        role="user",
        priority=5,
        description="演示策略持久化",
        permissions=[
            Permission(action="read", resource="*", effect=Effect.ALLOW),
            Permission(action="write", resource="memory:*", effect=Effect.ALLOW),
            Permission(action="delete", resource="*", effect=Effect.DENY),
        ],
    )
    file_store.save(policy)
    print(f"[保存] 策略: {policy.name}")

    # 查看文件
    files = list(store_path.glob("*.json"))
    print(f"[文件] 创建了 {len(files)} 个文件: {[f.name for f in files]}")

    # 读取文件内容
    if files:
        content = files[0].read_text(encoding="utf-8")
        data = json.loads(content)
        print(f"[内容] 名称: {data['name']}, 角色: {data['role']}, 权限数: {len(data['permissions'])}")

    # 从文件重新加载
    loaded = file_store.load("demo-policy")
    print(f"[加载] 名称: {loaded.name}, 角色: {loaded.role}, 权限数: {len(loaded.permissions)}")
    for p in loaded.permissions:
        print(f"  - {p.effect.value:5s} {p.action:8s} {p.resource}")

    # 按角色查找
    found = file_store.find_by_role("user")
    print(f"[查找] 角色=user 的策略数: {len(found)}")

    # 清理
    file_store.clear()
    store_path.rmdir()
    print(f"[清理] 已删除临时目录")

    print("\n[完成] 策略文件持久化演示结束")


def main() -> None:
    """主函数"""
    print("=" * 60)
    print("实验 17: 资源访问控制")
    print("=" * 60)

    demo_memory_protection()
    demo_file_protection()
    demo_rbac()
    demo_policy_persistence()

    # 总结
    print("\n" + "=" * 60)
    print("学习总结")
    print("-" * 60)
    print("1. 资源保护：通过 resource 路径控制数据访问")
    print("2. RBAC：通过角色分层，guest < user < admin 递增权限")
    print("3. 最小权限：只授予完成任务所需的最小权限")
    print("4. 命名空间：memory:, file:, tool: 等前缀组织资源")
    print("5. 持久化：FilePolicyStore 支持策略文件持久化")
    print("=" * 60)


if __name__ == "__main__":
    main()
