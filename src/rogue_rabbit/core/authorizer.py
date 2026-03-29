"""
授权管理器

学习要点:
=========
1. 授权检查流程：收集策略 → 匹配规则 → DENY 优先 → 返回结果
2. 策略优先级：高优先级策略覆盖低优先级
3. 默认拒绝：没有匹配规则时默认 DENY
4. 审计日志：记录所有权限决策

设计模式:
=========
Authorizer 是权限系统的"决策者"：
- 委托 PolicyStore 处理策略持久化
- 按 priority 排序策略
- DENY 优先于 ALLOW
- 默认拒绝（fail-safe）

权限检查流程:
============
1. 根据请求的 role 查找所有匹配策略
2. 按 priority 降序排列
3. 遍历策略中的每条 Permission
4. 如果匹配到 DENY，立即返回拒绝
5. 如果匹配到 ALLOW，记录允许
6. 最终：有 ALLOW 且无 DENY → 允许；否则 → 拒绝
"""

import logging

from rogue_rabbit.contracts.permission import (
    AccessRequest,
    AccessResult,
    Effect,
    Permission,
    Policy,
    PolicyStore,
)

logger = logging.getLogger("authorizer")


class Authorizer:
    """
    授权管理器

    职责:
    ----
    1. 管理权限策略（增删查）
    2. 执行授权检查
    3. 记录审计日志

    使用示例:
    --------
    >>> from rogue_rabbit.runtime import InMemoryPolicyStore
    >>> from rogue_rabbit.contracts.permission import Permission, Policy, Effect
    >>>
    >>> store = InMemoryPolicyStore()
    >>> authorizer = Authorizer(store=store)
    >>>
    >>> # 添加策略
    >>> policy = Policy(
    ...     name="user-basic",
    ...     role="user",
    ...     permissions=[
    ...         Permission(action="read", resource="*", effect=Effect.ALLOW),
    ...         Permission(action="delete", resource="*", effect=Effect.DENY),
    ...     ],
    ... )
    >>> authorizer.add_policy(policy)
    >>>
    >>> # 检查权限
    >>> request = AccessRequest(action="read", resource="file:data", role="user")
    >>> result = authorizer.check(request)
    >>> print(result.allowed)  # True
    """

    def __init__(self, store: PolicyStore):
        """
        初始化授权管理器

        参数:
        -----
        store: 策略存储后端
        """
        self._store = store

    def add_policy(self, policy: Policy) -> None:
        """
        添加或更新策略

        参数:
        -----
        policy: 权限策略
        """
        self._store.save(policy)
        logger.info(
            f"[Authorizer] 添加策略: {policy.name} (role={policy.role}, "
            f"permissions={len(policy.permissions)}, priority={policy.priority})"
        )

    def remove_policy(self, name: str) -> bool:
        """
        删除策略

        参数:
        -----
        name: 策略名称

        返回:
        -----
        是否删除成功
        """
        result = self._store.delete(name)
        if result:
            logger.info(f"[Authorizer] 删除策略: {name}")
        return result

    def get_policy(self, name: str) -> Policy | None:
        """
        获取策略

        参数:
        -----
        name: 策略名称

        返回:
        -----
        策略对象或 None
        """
        return self._store.load(name)

    def list_policies(self) -> list[Policy]:
        """列出所有策略"""
        return self._store.list_policies()

    def check(self, request: AccessRequest) -> AccessResult:
        """
        执行授权检查

        核心流程:
        --------
        1. 按 role 查找策略
        2. 按 priority 降序排列
        3. 遍历规则，DENY 优先
        4. 无匹配 → 默认拒绝

        参数:
        -----
        request: 访问请求

        返回:
        -----
        授权结果
        """
        # 1. 查找匹配角色的策略
        policies = self._store.find_by_role(request.role)
        if not policies:
            reason = f"无匹配策略: role={request.role}"
            logger.warning(f"[Authorizer] 拒绝: {reason} | {request.action}:{request.resource}")
            return AccessResult(allowed=False, reason=reason)

        # 2. 按优先级降序排列
        policies.sort(key=lambda p: p.priority, reverse=True)

        # 3. 遍历策略检查权限
        allow_match: AccessResult | None = None

        for policy in policies:
            for perm in policy.permissions:
                if perm.matches(request.action, request.resource):
                    if perm.effect == Effect.DENY:
                        # DENY 立即生效
                        reason = (
                            f"DENY by policy={policy.name}: "
                            f"{perm.action}:{perm.resource}"
                        )
                        logger.warning(
                            f"[Authorizer] 拒绝: {reason} | "
                            f"role={request.role} {request.action}:{request.resource}"
                        )
                        return AccessResult(
                            allowed=False,
                            reason=reason,
                            matched_policy=policy.name,
                            matched_permission=perm,
                        )
                    elif perm.effect == Effect.ALLOW:
                        # 记录 ALLOW，但不立即返回（可能被 DENY 覆盖）
                        if allow_match is None:
                            allow_match = AccessResult(
                                allowed=True,
                                reason=f"ALLOW by policy={policy.name}",
                                matched_policy=policy.name,
                                matched_permission=perm,
                            )

        # 4. 返回结果
        if allow_match:
            logger.info(
                f"[Authorizer] 允许: role={request.role} "
                f"{request.action}:{request.resource} via {allow_match.matched_policy}"
            )
            return allow_match

        # 5. 默认拒绝
        reason = f"无匹配权限: role={request.role} {request.action}:{request.resource}"
        logger.warning(f"[Authorizer] 拒绝: {reason}")
        return AccessResult(allowed=False, reason=reason)

    def check_all(self, requests: list[AccessRequest]) -> list[AccessResult]:
        """
        批量检查权限

        参数:
        -----
        requests: 访问请求列表

        返回:
        -----
        对应的授权结果列表
        """
        return [self.check(req) for req in requests]

    def get_permissions_for_role(self, role: str) -> list[Permission]:
        """
        获取角色的所有权限

        参数:
        -----
        role: 角色名称

        返回:
        -----
        权限列表（按策略优先级排序）
        """
        policies = self._store.find_by_role(role)
        policies.sort(key=lambda p: p.priority, reverse=True)
        permissions = []
        for policy in policies:
            permissions.extend(policy.permissions)
        return permissions
