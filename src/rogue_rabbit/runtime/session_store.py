"""
会话存储后端实现

学习要点:
=========
1. 存储抽象：通过 SessionStore 协议定义接口
2. 多种实现：内存存储 vs 文件存储
3. 依赖注入：SessionManager 不关心具体实现

实现对比:
=========
MemorySessionStore:
- 优点：速度快，实现简单
- 缺点：进程重启后数据丢失
- 适用：测试、开发、短期会话

FileSessionStore:
- 优点：数据持久化，跨进程可用
- 缺点：IO 开销，不适合高并发
- 适用：单机部署、长期会话

扩展方向:
=========
- RedisSessionStore: 分布式场景
- SQLiteSessionStore: 结构化查询
- EncryptedSessionStore: 安全存储
"""

import json
import logging
from pathlib import Path

from rogue_rabbit.contracts.session import Session, SessionMeta

logger = logging.getLogger("session-store")


class MemorySessionStore:
    """
    内存会话存储

    特点:
    -----
    - 数据存储在内存中
    - 进程重启后数据丢失
    - 适合测试和开发

    使用示例:
    --------
    >>> store = MemorySessionStore()
    >>> session = Session(meta=SessionMeta())
    >>> store.save(session)
    >>> loaded = store.load(session.meta.session_id)
    >>> print(loaded.meta.session_id)
    """

    def __init__(self):
        """初始化内存存储"""
        self._sessions: dict[str, Session] = {}

    def save(self, session: Session) -> None:
        """保存会话到内存"""
        self._sessions[session.meta.session_id] = session
        logger.debug(f"[MemoryStore] 保存会话: {session.meta.session_id}")

    def load(self, session_id: str) -> Session | None:
        """从内存加载会话"""
        return self._sessions.get(session_id)

    def delete(self, session_id: str) -> bool:
        """从内存删除会话"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.debug(f"[MemoryStore] 删除会话: {session_id}")
            return True
        return False

    def list_sessions(self) -> list[SessionMeta]:
        """列出所有会话元数据"""
        return [s.meta for s in self._sessions.values()]

    def clear(self) -> None:
        """清空所有会话（仅用于测试）"""
        self._sessions.clear()
        logger.debug("[MemoryStore] 清空所有会话")


class FileSessionStore:
    """
    文件会话存储

    特点:
    -----
    - 数据持久化到文件系统
    - 进程重启后数据保留
    - 适合单机部署

    文件结构:
    --------
    sessions/
    ├── abc12345.json
    ├── def67890.json
    └── ...

    文件格式:
    --------
    使用 JSON 格式，UTF-8 编码，便于查看和调试

    使用示例:
    --------
    >>> from pathlib import Path
    >>> store = FileSessionStore(Path("./sessions"))
    >>> session = Session(meta=SessionMeta())
    >>> store.save(session)
    >>> loaded = store.load(session.meta.session_id)
    """

    def __init__(self, base_path: Path):
        """
        初始化文件存储

        参数:
        -----
        base_path: 会话文件存储目录
        """
        self._base_path = base_path
        self._base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"[FileStore] 初始化存储目录: {base_path}")

    def _get_file_path(self, session_id: str) -> Path:
        """获取会话文件路径"""
        return self._base_path / f"{session_id}.json"

    def save(self, session: Session) -> None:
        """保存会话到文件"""
        file_path = self._get_file_path(session.meta.session_id)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)
        logger.debug(f"[FileStore] 保存会话: {session.meta.session_id}")

    def load(self, session_id: str) -> Session | None:
        """从文件加载会话"""
        file_path = self._get_file_path(session_id)
        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Session.from_dict(data)
        except Exception as e:
            logger.error(f"[FileStore] 加载会话失败 {session_id}: {e}")
            return None

    def delete(self, session_id: str) -> bool:
        """删除会话文件"""
        file_path = self._get_file_path(session_id)
        if file_path.exists():
            file_path.unlink()
            logger.debug(f"[FileStore] 删除会话: {session_id}")
            return True
        return False

    def list_sessions(self) -> list[SessionMeta]:
        """列出所有会话元数据"""
        sessions = []
        for file_path in self._base_path.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                session = Session.from_dict(data)
                sessions.append(session.meta)
            except Exception as e:
                logger.warning(
                    f"[FileStore] 加载会话元数据失败 {file_path}: {e}"
                )
        return sessions

    def clear(self) -> None:
        """清空所有会话文件（仅用于测试）"""
        for file_path in self._base_path.glob("*.json"):
            file_path.unlink()
        logger.debug("[FileStore] 清空所有会话文件")
