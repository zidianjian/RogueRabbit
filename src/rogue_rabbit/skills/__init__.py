"""
skills 包 - 内置 Skills

每个 skill 是一个文件夹，包含：
- SKILL.md: skill 定义文件（YAML frontmatter + Markdown）
- 可选的辅助脚本和资源文件

可用 Skills:
- calculator: 数学计算
- file-reader: 文件读取分析
- code-review: 代码审查
"""

import sys
from pathlib import Path

# 内置 skills 目录
BUILTIN_SKILLS_DIR = Path(__file__).parent

# 用户 skills 目录（可扩展）
USER_SKILLS_DIR = Path.home() / ".rogue_rabbit" / "skills"


def get_skill_dirs() -> list[Path]:
    """
    获取所有 skill 搜索目录

    Returns:
        目录列表，优先级：用户目录 > 内置目录
    """
    dirs = []
    if USER_SKILLS_DIR.exists():
        dirs.append(USER_SKILLS_DIR)
    dirs.append(BUILTIN_SKILLS_DIR)
    return dirs
