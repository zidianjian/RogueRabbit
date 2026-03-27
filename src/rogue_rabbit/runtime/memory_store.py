"""
记忆存储后端实现

学习要点:
=========
1. 存储抽象：通过 MemoryStore 协议定义接口
2. 多种实现：内存存储 vs 文件存储
3. 与 SessionStore 类似的设计模式

实现对比:
=========
InMemoryStore:
- 优点：速度快，实现简单
- 缺点：进程重启后数据丢失
- 适用：测试、开发

FileMemoryStore:
- 优点：数据持久化，跨进程可用
- 缺点：IO 开销，不适合高并发
- 适用：单机部署、长期记忆
"""

import json
import logging
from pathlib import Path

from rogue_rabbit.contracts.memory import Memory, MemoryMeta

logger = logging.getLogger("memory-store")


class InMemoryStore:
    """
    内存记忆存储

    特点:
    -----
    - 数据存储在内存中
    - 进程重启后数据丢失
    - 适合测试和开发

    使用示例:
    --------
    >>> store = InMemoryStore()
    >>> memory = Memory(meta=MemoryMeta(user_id="user1"))
    >>> store.save(memory)
    >>> loaded = store.load("user1")
    """

    def __init__(self):
        self._memories: dict[str, Memory] = {}

    def save(self, memory: Memory) -> None:
        """保存记忆空间"""
        self._memories[memory.meta.user_id] = memory
        logger.debug(f"[InMemoryStore] 保存记忆: {memory.meta.user_id}")

    def load(self, user_id: str) -> Memory | None:
        """加载记忆空间"""
        return self._memories.get(user_id)

    def delete(self, user_id: str) -> bool:
        """删除记忆空间"""
        if user_id in self._memories:
            del self._memories[user_id]
            logger.debug(f"[InMemoryStore] 删除记忆: {user_id}")
            return True
        return False

    def list_memories(self) -> list[MemoryMeta]:
        """列出所有记忆空间元数据"""
        return [m.meta for m in self._memories.values()]

    def clear(self) -> None:
        """清空所有记忆（仅用于测试）"""
        self._memories.clear()


class FileMemoryStore:
    """
    文件记忆存储

    特点:
    -----
    - 数据持久化到文件系统
    - 进程重启后数据保留
    - 适合单机部署

    文件结构:
    --------
    memories/
    ├── user1.json
    ├── user2.json
    └── ...

    使用示例:
    --------
    >>> from pathlib import Path
    >>> store = FileMemoryStore(Path("./memories"))
    >>> memory = Memory(meta=MemoryMeta(user_id="user1"))
    >>> store.save(memory)
    """

    def __init__(self, base_path: Path):
        """
        初始化文件存储

        参数:
        -----
        base_path: 记忆文件存储目录
        """
        self._base_path = base_path
        self._base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"[FileMemoryStore] 初始化存储目录: {base_path}")

    def _get_file_path(self, user_id: str) -> Path:
        """获取记忆文件路径"""
        return self._base_path / f"{user_id}.json"

    def save(self, memory: Memory) -> None:
        """保存记忆空间到文件"""
        file_path = self._get_file_path(memory.meta.user_id)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(memory.to_dict(), f, ensure_ascii=False, indent=2)
        logger.debug(f"[FileMemoryStore] 保存记忆: {memory.meta.user_id}")

    def load(self, user_id: str) -> Memory | None:
        """从文件加载记忆空间"""
        file_path = self._get_file_path(user_id)
        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Memory.from_dict(data)
        except Exception as e:
            logger.error(f"[FileMemoryStore] 加载记忆失败 {user_id}: {e}")
            return None

    def delete(self, user_id: str) -> bool:
        """删除记忆文件"""
        file_path = self._get_file_path(user_id)
        if file_path.exists():
            file_path.unlink()
            logger.debug(f"[FileMemoryStore] 删除记忆: {user_id}")
            return True
        return False

    def list_memories(self) -> list[MemoryMeta]:
        """列出所有记忆空间元数据"""
        memories = []
        for file_path in self._base_path.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                memory = Memory.from_dict(data)
                memories.append(memory.meta)
            except Exception as e:
                logger.warning(
                    f"[FileMemoryStore] 加载记忆元数据失败 {file_path}: {e}"
                )
        return memories

    def clear(self) -> None:
        """清空所有记忆文件（仅用于测试）"""
        for file_path in self._base_path.glob("*.json"):
            file_path.unlink()
        logger.debug("[FileMemoryStore] 清空所有记忆文件")
