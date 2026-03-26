"""
Skill 管理器

负责：
1. 发现：扫描目录，找到所有 SKILL.md 文件
2. 加载：解析 SKILL.md（YAML frontmatter + Markdown）
3. 管理：维护 skill 注册表，提供查询接口
"""

import logging
import re
from pathlib import Path

from rogue_rabbit.contracts.skill import Skill, SkillDiscoveryResult, SkillMeta

logger = logging.getLogger("skill-manager")

# YAML frontmatter 正则模式
# 匹配 --- 开头和结尾的块
FRONTMATTER_PATTERN = re.compile(
    r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL
)


def parse_skill_md(content: str, file_path: Path) -> tuple[SkillMeta, str] | None:
    """
    解析 SKILL.md 文件

    Args:
        content: SKILL.md 文件内容
        file_path: 文件路径（用于错误报告）

    Returns:
        (SkillMeta, markdown_content) 或 None（解析失败）
    """
    match = FRONTMATTER_PATTERN.match(content)
    if not match:
        logger.warning(f"[Skill] {file_path}: 缺少 YAML frontmatter")
        return None

    frontmatter_str, markdown_content = match.groups()

    # 解析 YAML frontmatter（简单实现，不引入 pyyaml）
    meta = {}
    for line in frontmatter_str.strip().split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip().strip('"').strip("'")

    # 验证必需字段
    if "name" not in meta:
        logger.warning(f"[Skill] {file_path}: 缺少 'name' 字段")
        return None
    if "description" not in meta:
        logger.warning(f"[Skill] {file_path}: 缺少 'description' 字段")
        return None

    skill_meta = SkillMeta(name=meta["name"], description=meta["description"])
    return skill_meta, markdown_content.strip()


class SkillManager:
    """
    Skill 管理器

    使用方式：
        manager = SkillManager([Path("skills/")])
        skills = manager.discover()
        skill = manager.load("calculator")
    """

    def __init__(self, skill_dirs: list[Path]):
        """
        初始化 Skill 管理器

        Args:
            skill_dirs: skill 搜索目录列表
        """
        self._skill_dirs = skill_dirs
        self._registry: dict[str, Path] = {}  # name -> SKILL.md path

    def discover(self) -> SkillDiscoveryResult:
        """
        发现所有可用的 skills

        扫描 skill_dirs 下的所有子目录，查找 SKILL.md 文件

        Returns:
            SkillDiscoveryResult 包含发现的 skills 和错误信息
        """
        result = SkillDiscoveryResult()
        self._registry.clear()

        for skill_dir in self._skill_dirs:
            if not skill_dir.exists():
                logger.debug(f"[Skill] 目录不存在: {skill_dir}")
                continue

            # 扫描子目录
            for subdir in skill_dir.iterdir():
                if not subdir.is_dir():
                    continue

                skill_md_path = subdir / "SKILL.md"
                if not skill_md_path.exists():
                    continue

                # 解析 frontmatter 获取元数据
                try:
                    content = skill_md_path.read_text(encoding="utf-8")
                    parsed = parse_skill_md(content, skill_md_path)
                    if parsed:
                        meta, _ = parsed
                        self._registry[meta.name] = skill_md_path
                        result.skills.append(meta)
                        logger.info(f"[Skill] 发现 skill: {meta.name} -> {skill_md_path}")
                except Exception as e:
                    error_msg = f"[Skill] 加载失败 {skill_md_path}: {e}"
                    logger.error(error_msg)
                    result.errors.append(error_msg)

        logger.info(f"[Skill] 发现完成: {len(result.skills)} 个 skill")
        return result

    def load(self, name: str) -> Skill | None:
        """
        加载指定 skill 的完整内容

        Args:
            name: skill 名称

        Returns:
            Skill 对象或 None（未找到）
        """
        if name not in self._registry:
            logger.warning(f"[Skill] 未找到 skill: {name}")
            return None

        skill_md_path = self._registry[name]
        try:
            content = skill_md_path.read_text(encoding="utf-8")
            parsed = parse_skill_md(content, skill_md_path)
            if not parsed:
                return None

            meta, markdown_content = parsed
            skill = Skill(
                meta=meta,
                base_path=skill_md_path.parent,
                content=markdown_content,
            )
            logger.info(f"[Skill] 加载成功: {name}")
            return skill
        except Exception as e:
            logger.error(f"[Skill] 加载失败 {name}: {e}")
            return None

    def list_skills(self) -> list[SkillMeta]:
        """
        获取所有已发现的 skill 元数据

        Returns:
            SkillMeta 列表
        """
        return [
            SkillMeta(name=name, description="")
            for name in self._registry.keys()
        ]

    def get_skill_descriptions(self) -> str:
        """
        获取所有 skill 的描述列表

        用于 LLM prompt，告诉 LLM 有哪些 skill 可用

        Returns:
            格式化的 skill 描述字符串
        """
        if not self._registry:
            return "没有可用的 skill"

        lines = ["可用 Skills:", ""]
        for name, path in self._registry.items():
            # 重新读取获取 description
            try:
                content = path.read_text(encoding="utf-8")
                parsed = parse_skill_md(content, path)
                if parsed:
                    meta, _ = parsed
                    lines.append(f"- {meta.name}: {meta.description}")
                else:
                    lines.append(f"- {name}")
            except Exception:
                lines.append(f"- {name}")

        return "\n".join(lines)

    def has_skill(self, name: str) -> bool:
        """检查 skill 是否存在"""
        return name in self._registry
