"""
策略存储后端实现

学习要点:
=========
1. 存储抽象：通过 PolicyStore 协议定义接口
2. 多种实现：内存存储 vs 文件存储
3. 与 SessionStore/MemoryStore 类似的设计模式

实现对比:
=========
InMemoryPolicyStore:
- 优点：速度快，实现简单
- 缺点：进程重启后数据丢失
- 适用：测试、开发

FilePolicyStore:
- 优点：数据持久化，跨进程可用
- 缺点：IO 开销，不适合高并发
- 适用：单机部署、长期运行
"""

import json
import logging
from pathlib import Path

from rogue_rabbit.contracts.permission import Policy

logger = logging.getLogger("policy-store")


class InMemoryPolicyStore:
    """
    内存策略存储

    特点:
    -----
    - 数据存储在内存中
    - 进程重启后数据丢失
    - 适合测试和开发

    使用示例:
    --------
    >>> store = InMemoryPolicyStore()
    >>> policy = Policy(name="test", role="user", permissions=[])
    >>> store.save(policy)
    >>> loaded = store.load("test")
    """

    def __init__(self):
        self._policies: dict[str, Policy] = {}

    def save(self, policy: Policy) -> None:
        """保存策略"""
        self._policies[policy.name] = policy
        logger.debug(f"[InMemoryPolicyStore] 保存策略: {policy.name}")

    def load(self, name: str) -> Policy | None:
        """加载策略"""
        return self._policies.get(name)

    def delete(self, name: str) -> bool:
        """删除策略"""
        if name in self._policies:
            del self._policies[name]
            logger.debug(f"[InMemoryPolicyStore] 删除策略: {name}")
            return True
        return False

    def list_policies(self) -> list[Policy]:
        """列出所有策略"""
        return list(self._policies.values())

    def find_by_role(self, role: str) -> list[Policy]:
        """按角色查找策略"""
        return [p for p in self._policies.values() if p.role == role]

    def clear(self) -> None:
        """清空所有策略（仅用于测试）"""
        self._policies.clear()


class FilePolicyStore:
    """
    文件策略存储

    特点:
    -----
    - 数据持久化到文件系统
    - 进程重启后数据保留
    - 适合单机部署

    文件结构:
    --------
    policies/
    ├── admin-full-access.json
    ├── user-basic.json
    └── ...

    使用示例:
    --------
    >>> from pathlib import Path
    >>> store = FilePolicyStore(Path("./policies"))
    >>> policy = Policy(name="test", role="user", permissions=[])
    >>> store.save(policy)
    """

    def __init__(self, base_path: Path):
        """
        初始化文件存储

        参数:
        -----
        base_path: 策略文件存储目录
        """
        self._base_path = base_path
        self._base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"[FilePolicyStore] 初始化存储目录: {base_path}")

    def _get_file_path(self, name: str) -> Path:
        """获取策略文件路径"""
        return self._base_path / f"{name}.json"

    def save(self, policy: Policy) -> None:
        """保存策略到文件"""
        file_path = self._get_file_path(policy.name)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(policy.to_dict(), f, ensure_ascii=False, indent=2)
        logger.debug(f"[FilePolicyStore] 保存策略: {policy.name}")

    def load(self, name: str) -> Policy | None:
        """从文件加载策略"""
        file_path = self._get_file_path(name)
        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Policy.from_dict(data)
        except Exception as e:
            logger.error(f"[FilePolicyStore] 加载策略失败 {name}: {e}")
            return None

    def delete(self, name: str) -> bool:
        """删除策略文件"""
        file_path = self._get_file_path(name)
        if file_path.exists():
            file_path.unlink()
            logger.debug(f"[FilePolicyStore] 删除策略: {name}")
            return True
        return False

    def list_policies(self) -> list[Policy]:
        """列出所有策略"""
        policies = []
        for file_path in self._base_path.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                policies.append(Policy.from_dict(data))
            except Exception as e:
                logger.warning(
                    f"[FilePolicyStore] 加载策略失败 {file_path}: {e}"
                )
        return policies

    def find_by_role(self, role: str) -> list[Policy]:
        """按角色查找策略"""
        return [p for p in self.list_policies() if p.role == role]

    def clear(self) -> None:
        """清空所有策略文件（仅用于测试）"""
        for file_path in self._base_path.glob("*.json"):
            file_path.unlink()
        logger.debug("[FilePolicyStore] 清空所有策略文件")
