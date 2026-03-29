# Permission 权限控制交互指南

## 概念

权限控制决定 Agent 可以执行哪些操作、访问哪些资源。

### 核心对象

| 对象 | 说明 |
|------|------|
| `Permission` | 单条权限规则：允许/拒绝 某操作 在 某资源 |
| `Policy` | 策略：一组权限规则，绑定到角色 |
| `AccessRequest` | 访问请求：谁要对什么资源做什么操作 |
| `AccessResult` | 授权结果：允许/拒绝 + 原因 |
| `Authorizer` | 授权管理器：执行权限检查 |

### 资源命名

```
tool:calculator      # 工具
tool:file_reader     # 工具
tool:*               # 所有工具
file:///public/*     # 公共文件
file:///secret/*     # 机密文件
memory:user1         # 用户记忆
memory:*             # 所有记忆
*                    # 所有资源
```

## 使用流程

### 1. 创建策略

```python
from rogue_rabbit.contracts.permission import Permission, Policy, Effect

policy = Policy(
    name="user-basic",
    role="user",
    permissions=[
        Permission(action="read", resource="*", effect=Effect.ALLOW),
        Permission(action="execute", resource="tool:*", effect=Effect.ALLOW),
        Permission(action="delete", resource="*", effect=Effect.DENY),
    ],
)
```

### 2. 添加到 Authorizer

```python
from rogue_rabbit.core import Authorizer
from rogue_rabbit.runtime import InMemoryPolicyStore

authorizer = Authorizer(store=InMemoryPolicyStore())
authorizer.add_policy(policy)
```

### 3. 检查权限

```python
from rogue_rabbit.contracts.permission import AccessRequest

request = AccessRequest(action="execute", resource="tool:calculator", role="user")
result = authorizer.check(request)

if result.allowed:
    # 执行操作
else:
    print(f"拒绝: {result.reason}")
```

## 核心原则

1. **DENY 优先**：同时有 ALLOW 和 DENY 时，DENY 生效
2. **默认拒绝**：没有匹配规则时自动 DENY
3. **策略优先级**：priority 高的策略优先检查
4. **最小权限**：只授予完成任务所需的最小权限

## 相关实验

- `15_permission_basic`: 基础权限检查
- `16_tool_permission`: 工具调用权限
- `17_resource_permission`: 资源访问控制
