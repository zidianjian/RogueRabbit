"""
实验 08: Skill 基础调用
========================

学习目标:
1. 理解 Skill 的概念和结构
2. 学会使用 SkillManager 发现和加载 Skills
3. 理解 Skill 与 MCP 的区别

Skill 是"可执行知识包"：
- 包含提示词扩展（SKILL.md）
- 可选包含辅助脚本和资源
- 按需加载，注入到上下文

运行方式:
    python -m rogue_rabbit.experiments.08_skill_basic
"""

import asyncio
from pathlib import Path

from rogue_rabbit.contracts import Skill, SkillDiscoveryResult
from rogue_rabbit.core.skill_manager import SkillManager
from rogue_rabbit.skills import get_skill_dirs


# ========================================
# Demo 1: 发现 Skills
# ========================================


async def demo_discover_skills():
    """Demo 1: 发现所有可用的 Skills"""
    print("\n" + "=" * 60)
    print("Demo 1: 发现 Skills")
    print("=" * 60)

    # 获取 skill 搜索目录
    skill_dirs = get_skill_dirs()
    print(f"\nSkill 搜索目录:")
    for d in skill_dirs:
        print(f"  - {d}")

    # 创建 Skill 管理器
    manager = SkillManager(skill_dirs)

    # 发现 skills
    result = manager.discover()

    print(f"\n发现 {len(result.skills)} 个 Skill:")
    for meta in result.skills:
        print(f"  - {meta.name}: {meta.description}")

    if result.errors:
        print(f"\n加载失败的 Skills:")
        for error in result.errors:
            print(f"  - {error}")

    return manager


# ========================================
# Demo 2: 加载 Skill 内容
# ========================================


async def demo_load_skill(manager: SkillManager):
    """Demo 2: 加载指定 Skill 的完整内容"""
    print("\n" + "=" * 60)
    print("Demo 2: 加载 Skill 内容")
    print("=" * 60)

    # 加载 calculator skill
    skill_name = "calculator"
    print(f"\n加载 Skill: {skill_name}")

    skill = manager.load(skill_name)
    if skill:
        print(f"\n[Skill 元数据]")
        print(f"  名称: {skill.meta.name}")
        print(f"  描述: {skill.meta.description}")
        print(f"  路径: {skill.base_path}")

        print(f"\n[Skill 内容预览]")
        lines = skill.content.split("\n")[:15]
        print("  " + "\n  ".join(lines))
        if len(skill.content.split("\n")) > 15:
            print("  ...")

        print(f"\n[完整 Prompt（用于注入上下文）]")
        full_prompt = skill.get_full_prompt()
        print(f"  长度: {len(full_prompt)} 字符")
    else:
        print(f"[错误] 未找到 Skill: {skill_name}")

    return skill


# ========================================
# Demo 3: Skill 与 LLM 集成
# ========================================


async def demo_skill_with_llm(manager: SkillManager, skill: Skill):
    """Demo 3: 展示 Skill 如何与 LLM 集成"""
    print("\n" + "=" * 60)
    print("Demo 3: Skill 与 LLM 集成")
    print("=" * 60)

    print("""
Skill 与 LLM 集成的流程:

1. 用户提问: "帮我计算 2^20 是多少"

2. LLM 检查可用 Skills:
   - calculator: 执行数学计算
   - file-reader: 读取文件
   - code-review: 代码审查

3. LLM 选择 calculator Skill

4. 系统注入 Skill 内容到上下文:
   - Base Path: .../skills/calculator/
   - SKILL.md 内容（指导 LLM 如何处理）

5. LLM 根据 Skill 指导执行计算:
   - 表达式: 2 ** 20
   - 结果: 1048576

6. 返回答案: "2^20 = 1,048,576"
""")

    print("\n[Skill 注入示例]")
    print("-" * 40)
    print(skill.get_full_prompt()[:500] + "...")


# ========================================
# Demo 4: Skill vs MCP 对比
# ========================================


async def demo_skill_vs_mcp():
    """Demo 4: Skill 与 MCP 的区别"""
    print("\n" + "=" * 60)
    print("Demo 4: Skill vs MCP")
    print("=" * 60)

    print("""
┌─────────────────────────────────────────────────────────────┐
│                    Skill vs MCP 对比                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  MCP (Model Context Protocol)                               │
│  ├── 类型: 工具/函数                                        │
│  ├── 输入: 结构化参数 (JSON Schema)                         │
│  ├── 输出: 结构化结果                                       │
│  ├── 调用: Tool Call                                        │
│  └── 适合: 明确的输入输出操作                               │
│                                                             │
│  Skill                                                      │
│  ├── 类型: 提示词扩展                                       │
│  ├── 输入: 自然语言                                         │
│  ├── 输出: 指导性内容                                       │
│  ├── 调用: 上下文注入                                       │
│  └── 适合: 需要灵活处理的任务                               │
│                                                             │
│  示例对比:                                                   │
│                                                             │
│  MCP Tool: calculator                                       │
│  ├── 输入: {"expression": "2**10"}                         │
│  └── 输出: {"result": 1024}                                │
│                                                             │
│  Skill: calculator                                          │
│  ├── 注入: SKILL.md 内容（计算指南）                        │
│  └── LLM: 自行决定如何计算并回答                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
""")


# ========================================
# Main
# ========================================


async def main():
    """主函数"""
    print("=" * 60)
    print("实验 08: Skill 基础调用")
    print("=" * 60)

    print("\n本实验介绍 Skill 的基本概念和使用方式。")

    # Demo 1: 发现 Skills
    manager = await demo_discover_skills()

    # Demo 2: 加载 Skill
    skill = await demo_load_skill(manager)

    # Demo 3: Skill 与 LLM 集成
    if skill:
        await demo_skill_with_llm(manager, skill)

    # Demo 4: Skill vs MCP
    await demo_skill_vs_mcp()

    # 总结
    print("\n" + "=" * 60)
    print("学习总结")
    print("=" * 60)
    print("""
1. Skill 是"可执行知识包"，包含 SKILL.md 和可选资源
2. SkillManager 负责 Skill 的发现和加载
3. Skill 通过上下文注入方式扩展 LLM 能力
4. Skill 适合需要灵活处理的任务，MCP 适合结构化操作

关键文件:
- contracts/skill.py: Skill 数据结构定义
- core/skill_manager.py: Skill 管理器
- skills/: 内置 Skills 目录

下一步:
- 运行 09_skill_with_llm.py 体验完整的 LLM + Skill 集成
- 创建自己的 Skill 并测试
""")


if __name__ == "__main__":
    asyncio.run(main())
