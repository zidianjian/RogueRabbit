"""
Skill 协议定义

Skill 是可执行知识包，包含：
- 元数据（name, description）
- 指令内容（Markdown 格式）
- 可选的辅助脚本和资源

Skill 与 MCP 的区别：
- MCP：工具/函数，结构化输入输出
- Skill：提示词扩展，自然语言交互

参考：Claude Code Skills 设计
"""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class SkillMeta:
    """
    Skill 元数据

    来自 SKILL.md 的 YAML frontmatter
    """

    name: str  # skill 名称，如 "calculator"，用于调用
    description: str  # 单行描述，告诉 LLM 何时使用此 skill


@dataclass
class Skill:
    """
    完整的 Skill 定义

    包含元数据、内容和资源路径
    """

    meta: SkillMeta
    base_path: Path  # skill 文件夹路径，用于定位辅助脚本
    content: str  # SKILL.md 的 Markdown 内容（不含 frontmatter）

    def get_full_prompt(self) -> str:
        """
        获取完整的 skill 提示词

        包含 base_path 信息和内容
        """
        return f"Base Path: {self.base_path}/\n\n{self.content}"


@dataclass
class SkillDiscoveryResult:
    """
    Skill 发现结果
    """

    skills: list[SkillMeta] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)  # 加载失败的 skill
