"""
权限协议定义

学习要点:
=========
1. 权限模型：谁能(who) 对 什么资源(what) 做什么操作(how)
2. 策略（Policy）：一组权限规则的集合，绑定到角色
3. 授权检查：根据策略决定请求是否被允许

为什么需要权限控制?
==================
1. 安全边界：Agent 不能随意执行危险操作（如删除文件、发送邮件）
2. 用户授权：敏感操作需要用户确认或预授权
3. 最小权限：Agent 只拥有完成任务所需的最小权限
4. 可审计：所有权限决策都有记录，便于追踪

Permission vs Policy:
--------------------
- Permission: 单条权限规则（允许/拒绝 某操作 在 某资源）
- Policy: 一组权限规则的集合，绑定到某个角色

资源标识格式:
------------
- 工具: tool:<tool_name>  (如 tool:calculator, tool:file_reader)
- 文件: file:<path>       (如 file:///home/user/data)
- 记忆: memory:<user_id>  (如 memory:user1)
- 通配: *                 (匹配所有资源)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable
from uuid import uuid4


class Effect(str, Enum):
    """
    权限效果

    ALLOW: 允许操作
    DENY: 拒绝操作

    规则:
    -----
    - DENY 优先：如果同时存在 ALLOW 和 DENY 规则，DENY 生效
    - 默认拒绝：没有匹配规则时，默认 DENY
    """

    ALLOW = "allow"
    DENY = "deny"


@dataclass(frozen=True)
class Permission:
    """
    单条权限规则

    属性:
    -----
    - action: 操作类型（read, write, execute, delete, *）
    - resource: 资源标识（tool:xxx, file:xxx, memory:xxx, *）
    - effect: 允许或拒绝

    通配符:
    -------
    - action="*" 表示匹配所有操作
    - resource="*" 表示匹配所有资源
    - resource="tool:*" 表示匹配所有工具

    使用示例:
    --------
    >>> # 允许读取所有文件
    >>> Permission(action="read", resource="file:*", effect=Effect.ALLOW)
    >>> # 拒绝删除操作
    >>> Permission(action="delete", resource="*", effect=Effect.DENY)
    >>> # 允许使用计算器工具
    >>> Permission(action="execute", resource="tool:calculator", effect=Effect.ALLOW)
    """

    action: str
    resource: str
    effect: Effect

    def matches(self, action: str, resource: str) -> bool:
        """
        检查此权限是否匹配给定的操作和资源

        参数:
        -----
        action: 请求的操作
        resource: 请求的资源

        返回:
        -----
        是否匹配
        """
        return self._match_action(action) and self._match_resource(resource)

    def _match_action(self, action: str) -> bool:
        """匹配操作（支持通配符）"""
        if self.action == "*":
            return True
        return self.action == action

    def _match_resource(self, resource: str) -> bool:
        """
        匹配资源（支持通配符和前缀匹配）

        示例:
        -----
        - resource="*" 匹配所有
        - resource="tool:*" 匹配 "tool:calculator", "tool:file_reader" 等
        - resource="file:///secret/*" 匹配 "file:///secret/keys.pem" 等
        - resource="tool:calculator" 精确匹配
        """
        if self.resource == "*":
            return True
        if self.resource.endswith("*"):
            prefix = self.resource[:-1]  # "tool:*" -> "tool:", "file:///secret/*" -> "file:///secret/"
            return resource.startswith(prefix)
        return self.resource == resource

    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            "action": self.action,
            "resource": self.resource,
            "effect": self.effect.value,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Permission":
        """从字典反序列化"""
        return cls(
            action=data["action"],
            resource=data["resource"],
            effect=Effect(data["effect"]),
        )


@dataclass
class Policy:
    """
    权限策略

    一组权限规则的集合，绑定到某个角色

    属性:
    -----
    - name: 策略名称
    - role: 绑定的角色（如 "admin", "user", "guest"）
    - permissions: 权限规则列表
    - priority: 优先级（数值越高越优先，默认 0）
    - description: 策略描述

    使用示例:
    --------
    >>> admin_policy = Policy(
    ...     name="admin-full-access",
    ...     role="admin",
    ...     permissions=[
    ...         Permission(action="*", resource="*", effect=Effect.ALLOW),
    ...     ],
    ...     priority=10,
    ... )
    >>>
    >>> user_policy = Policy(
    ...     name="user-read-only",
    ...     role="user",
    ...     permissions=[
    ...         Permission(action="read", resource="*", effect=Effect.ALLOW),
    ...         Permission(action="execute", resource="tool:*", effect=Effect.ALLOW),
    ...         Permission(action="delete", resource="*", effect=Effect.DENY),
    ...     ],
    ... )
    """

    name: str
    role: str
    permissions: list[Permission] = field(default_factory=list)
    priority: int = 0
    description: str = ""

    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            "name": self.name,
            "role": self.role,
            "permissions": [p.to_dict() for p in self.permissions],
            "priority": self.priority,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Policy":
        """从字典反序列化"""
        return cls(
            name=data["name"],
            role=data["role"],
            permissions=[Permission.from_dict(p) for p in data.get("permissions", [])],
            priority=data.get("priority", 0),
            description=data.get("description", ""),
        )


@dataclass(frozen=True)
class AccessRequest:
    """
    访问请求

    描述一次权限检查的完整信息

    属性:
    -----
    - action: 请求的操作
    - resource: 请求的资源
    - role: 请求者的角色
    - context: 附加上下文（user_id, session_id 等）

    使用示例:
    --------
    >>> request = AccessRequest(
    ...     action="execute",
    ...     resource="tool:calculator",
    ...     role="user",
    ...     context={"user_id": "user1"},
    ... )
    """

    action: str
    resource: str
    role: str
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class AccessResult:
    """
    授权检查结果

    属性:
    -----
    - allowed: 是否允许
    - reason: 决策原因
    - matched_policy: 匹配的策略名称（可选）
    - matched_permission: 匹配的权限规则（可选）

    使用示例:
    --------
    >>> result = AccessResult(allowed=True, reason="匹配 admin-full-access 策略")
    >>> if not result.allowed:
    ...     print(f"拒绝原因: {result.reason}")
    """

    allowed: bool
    reason: str = ""
    matched_policy: str | None = None
    matched_permission: Permission | None = None


@runtime_checkable
class PolicyStore(Protocol):
    """
    策略存储协议

    方法说明:
    --------
    - save: 保存或更新策略
    - load: 加载策略，不存在返回 None
    - delete: 删除策略，返回是否成功
    - list_policies: 列出所有策略
    - find_by_role: 按角色查找策略
    """

    def save(self, policy: Policy) -> None:
        """保存策略"""
        ...

    def load(self, name: str) -> Policy | None:
        """加载策略，按名称查找"""
        ...

    def delete(self, name: str) -> bool:
        """删除策略"""
        ...

    def list_policies(self) -> list[Policy]:
        """列出所有策略"""
        ...

    def find_by_role(self, role: str) -> list[Policy]:
        """按角色查找策略"""
        ...
