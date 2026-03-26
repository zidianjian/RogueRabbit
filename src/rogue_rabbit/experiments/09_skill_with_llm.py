"""
实验 09: LLM + Skill 集成
==========================

学习目标:
1. 理解 LLM 如何选择合适的 Skill
2. 实现 Skill 选择和注入流程
3. 体验完整的 LLM + Skill 交互

架构:
    用户 -> LLM -> 选择 Skill -> 注入内容 -> LLM 执行 -> 返回结果

运行方式:
    python -m rogue_rabbit.experiments.09_skill_with_llm
"""

import asyncio
import os
import re
from pathlib import Path

from dotenv import load_dotenv

from rogue_rabbit.contracts import Message, Role, Skill, SkillMeta
from rogue_rabbit.core.skill_manager import SkillManager
from rogue_rabbit.skills import get_skill_dirs


# ========================================
# 配置检查
# ========================================


def check_api_key() -> bool:
    """检查 API key 是否配置"""
    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    load_dotenv(env_path)

    api_key = os.environ.get("ZHIPU_API_KEY")
    if not api_key:
        print("[!] 未配置 ZHIPU_API_KEY")
        print("\n请在项目根目录创建 .env 文件:")
        print("  ZHIPU_API_KEY=your-api-key")
        return False

    print("[OK] ZHIPU_API_KEY 已配置")
    return True


# ========================================
# Skill 选择器
# ========================================


class SkillSelector:
    """
    Skill 选择器

    让 LLM 选择合适的 Skill 并注入上下文
    """

    def __init__(self, manager: SkillManager, llm_client):
        self._manager = manager
        self._llm = llm_client

    def _build_skill_selection_prompt(self) -> str:
        """构建 Skill 选择提示"""
        skill_list = self._manager.get_skill_descriptions()
        return f"""你是一个智能助手，可以使用 Skills 来帮助完成任务。

{skill_list}

使用规则:
1. 当需要使用 Skill 时，按以下格式回复：
   SKILL: skill名称

2. 如果不需要任何 Skill，直接回答问题。

请始终用中文回复。"""

    def select_skill(self, question: str) -> str | None:
        """
        让 LLM 选择合适的 Skill

        Args:
            question: 用户问题

        Returns:
            Skill 名称或 None
        """
        system_prompt = self._build_skill_selection_prompt()

        messages = [
            Message(role=Role.SYSTEM, content=system_prompt),
            Message(role=Role.USER, content=question),
        ]

        response = self._llm.complete(messages)
        print(f"\n[LLM 回复]\n{response}")

        # 解析 Skill 选择
        match = re.search(r"SKILL:\s*(\S+)", response)
        if match:
            skill_name = match.group(1).strip()
            if self._manager.has_skill(skill_name):
                return skill_name
            print(f"[警告] 未找到 Skill: {skill_name}")

        return None

    def execute_with_skill(self, question: str, skill: Skill) -> str:
        """
        使用 Skill 执行任务

        Args:
            question: 用户问题
            skill: 选中的 Skill

        Returns:
            最终答案
        """
        # 构建包含 Skill 内容的 prompt
        skill_prompt = f"""你正在使用 "{skill.meta.name}" Skill 来完成任务。

{skill.get_full_prompt()}

---

请根据以上 Skill 指导，完成用户的任务。"""

        messages = [
            Message(role=Role.SYSTEM, content=skill_prompt),
            Message(role=Role.USER, content=question),
        ]

        response = self._llm.complete(messages)
        return response


# ========================================
# Demo
# ========================================


async def run_demo():
    """运行完整演示"""
    print("=" * 60)
    print("实验 09: LLM + Skill 集成")
    print("=" * 60)

    if not check_api_key():
        return

    # 初始化 Skill 管理器
    skill_dirs = get_skill_dirs()
    manager = SkillManager(skill_dirs)
    result = manager.discover()

    print(f"\n[Skill 发现] 找到 {len(result.skills)} 个 Skill:")
    for meta in result.skills:
        print(f"  - {meta.name}: {meta.description}")

    # 初始化 LLM 客户端
    from rogue_rabbit.adapters import GLMClient

    llm_client = GLMClient()

    # 创建 Skill 选择器
    selector = SkillSelector(manager, llm_client)

    # 测试用例
    test_questions = [
        "帮我计算 2 的 20 次方是多少",
        # "读取 README.md 文件并总结内容",
        # "审查这段代码: def add(a, b): return a + b",
    ]

    for question in test_questions:
        print("\n" + "=" * 60)
        print(f"问题: {question}")
        print("=" * 60)

        # Step 1: LLM 选择 Skill
        print("\n[步骤 1] LLM 选择 Skill...")
        skill_name = selector.select_skill(question)

        if skill_name:
            print(f"\n[选择结果] Skill: {skill_name}")

            # Step 2: 加载 Skill
            print("\n[步骤 2] 加载 Skill 内容...")
            skill = manager.load(skill_name)
            if skill:
                print(f"[Skill 内容预览]")
                lines = skill.content.split("\n")[:10]
                print("  " + "\n  ".join(lines))

                # Step 3: 使用 Skill 执行
                print("\n[步骤 3] 使用 Skill 执行任务...")
                answer = selector.execute_with_skill(question, skill)
                print(f"\n[最终答案]\n{answer}")
        else:
            print("\n[结果] 不需要 Skill，直接回答")
            messages = [Message(role=Role.USER, content=question)]
            answer = llm_client.complete(messages)
            print(f"\n[答案]\n{answer}")

    # 总结
    print("\n" + "=" * 60)
    print("学习总结")
    print("=" * 60)
    print("""
1. Skill 选择: LLM 根据问题描述选择合适的 Skill
2. Skill 加载: SkillManager 加载 Skill 的完整内容
3. Skill 注入: Skill 内容作为 System Prompt 注入
4. 任务执行: LLM 根据 Skill 指导完成任务

关键流程:
  用户问题 -> LLM 选择 Skill -> 加载 Skill -> 注入上下文 -> 执行任务

与 MCP 的配合:
  - Skill: 指导 LLM "如何" 做某事
  - MCP: 提供 "工具" 让 LLM 执行具体操作
  - 可以组合使用: Skill 指导 + MCP 工具执行
""")


async def main():
    await run_demo()


if __name__ == "__main__":
    asyncio.run(main())
