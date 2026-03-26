"""
实验 09: LLM + Skill 集成
==========================

学习目标:
1. 理解 LLM 如何选择合适的 Skill
2. 实现 Skill 选择和注入流程
3. 体验完整的 LLM + Skill 交互

架构:
    用户 -> SkillAgent -> 选择 Skill -> 注入内容 -> LLM 执行 -> 返回结果

运行方式:
    python -m rogue_rabbit.experiments.09_skill_with_llm
"""

import asyncio
import os
import re
from pathlib import Path

from dotenv import load_dotenv

from rogue_rabbit.contracts import Message, Role, Skill
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
# Skill Agent
# ========================================


class SkillAgent:
    """
    Skill Agent - 集成 Skill 的智能代理

    职责:
    1. 根据问题关键词自动匹配 Skill
    2. 将 Skill 内容注入 LLM 上下文
    3. 执行并返回结果
    """

    def __init__(self, manager: SkillManager, llm_client, verbose: bool = True):
        self._manager = manager
        self._llm = llm_client
        self._verbose = verbose

    def _log(self, message: str):
        """打印日志"""
        if self._verbose:
            print(message)

    def _match_skill_by_keywords(self, question: str) -> str | None:
        """
        根据关键词匹配 Skill

        简单的关键词匹配，实际应用中可以用 LLM 或向量相似度
        使用列表保持优先级顺序
        """
        question_lower = question.lower()

        # 关键词映射（按优先级排序：先检查更具体的）
        keyword_map = [
            ("code-review", ["审查", "代码审查", "code review", "检查代码", "代码质量", "代码"]),
            ("file-reader", ["读取", "文件", "file", "read", "读取文件", "打开文件", "readme"]),
            ("calculator", ["计算", "数学", "加减乘除", "乘方", "次方", "求和", "多少"]),
        ]

        for skill_name, keywords in keyword_map:
            for kw in keywords:
                if kw in question_lower:
                    if self._manager.has_skill(skill_name):
                        self._log(f"[关键词匹配] 命中关键词 '{kw}' -> Skill: {skill_name}")
                        return skill_name
                    break

        self._log("[关键词匹配] 未匹配到任何 Skill")
        return None

    def _select_skill_via_llm(self, question: str) -> str | None:
        """
        让 LLM 选择 Skill（可选的高级方法）

        返回: skill 名称或 None
        """
        skill_descriptions = self._manager.get_skill_descriptions()

        system_prompt = f"""你是一个 Skill 选择器。根据用户问题，选择最合适的 Skill。

{skill_descriptions}

规则:
1. 如果需要使用 Skill，只回复 Skill 名称（如: calculator）
2. 如果不需要任何 Skill，回复: none

只回复 Skill 名称或 none，不要有其他内容。"""

        messages = [
            Message(role=Role.SYSTEM, content=system_prompt),
            Message(role=Role.USER, content=question),
        ]

        response = self._llm.complete(messages).strip().lower()
        self._log(f"[LLM 选择] 原始回复: {response}")

        # 清理响应，提取 skill 名称
        response = response.replace("skill:", "").strip()

        if response == "none" or not response:
            return None

        # 检查是否是有效的 skill
        if self._manager.has_skill(response):
            return response

        return None

    def _execute_with_skill(self, question: str, skill: Skill) -> str:
        """
        使用 Skill 执行任务

        将 Skill 内容注入 System Prompt
        """
        skill_prompt = f"""你正在使用 "{skill.meta.name}" Skill。

Skill 说明: {skill.meta.description}

{skill.get_full_prompt()}

---

请根据以上 Skill 指导完成用户的任务。严格按照 Skill 中的说明操作。"""

        messages = [
            Message(role=Role.SYSTEM, content=skill_prompt),
            Message(role=Role.USER, content=question),
        ]

        return self._llm.complete(messages)

    def _execute_without_skill(self, question: str) -> str:
        """
        不使用 Skill 直接执行
        """
        messages = [
            Message(role=Role.USER, content=question),
        ]
        return self._llm.complete(messages)

    def run(
        self,
        question: str,
        use_llm_selection: bool = False,
    ) -> str:
        """
        运行 Agent

        Args:
            question: 用户问题
            use_llm_selection: 是否使用 LLM 选择 Skill（默认用关键词匹配）

        Returns:
            最终答案
        """
        self._log(f"\n{'='*50}")
        self._log(f"问题: {question}")
        self._log("=" * 50)

        # Step 1: 选择 Skill
        self._log("\n[步骤 1] 选择 Skill...")

        if use_llm_selection:
            skill_name = self._select_skill_via_llm(question)
        else:
            skill_name = self._match_skill_by_keywords(question)

        # Step 2: 执行
        if skill_name:
            self._log(f"[选择结果] 使用 Skill: {skill_name}")

            # 加载 Skill
            skill = self._manager.load(skill_name)
            if not skill:
                self._log(f"[错误] 无法加载 Skill: {skill_name}")
                return self._execute_without_skill(question)

            # 显示 Skill 内容
            self._log(f"\n[Skill 内容预览]")
            lines = skill.content.split("\n")[:8]
            self._log("  " + "\n  ".join(lines))

            # 使用 Skill 执行
            self._log(f"\n[步骤 2] 使用 Skill 执行...")
            answer = self._execute_with_skill(question, skill)
        else:
            self._log("[选择结果] 不需要 Skill，直接回答")
            self._log(f"\n[步骤 2] 直接执行...")
            answer = self._execute_without_skill(question)

        return answer


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

    # 创建 Skill Agent
    agent = SkillAgent(manager, llm_client, verbose=True)

    # 测试用例
    test_questions = [
        "帮我计算 2 的 20 次方是多少",
        "读取 README.md 文件并告诉我里面有什么",
        "审查这段代码: def add(a, b): return a + b",
        "今天天气怎么样？",  # 不需要 Skill
    ]

    for question in test_questions:
        answer = agent.run(question)
        print(f"\n{'='*50}")
        # 安全打印，处理 Unicode 字符
        safe_answer = answer.encode('gbk', errors='replace').decode('gbk')
        print(f"[最终答案]\n{safe_answer}")

    # 总结
    print("\n" + "=" * 60)
    print("学习总结")
    print("=" * 60)
    print("""
Skill Agent 工作流程:
1. 问题分析 -> 关键词匹配或 LLM 选择
2. Skill 加载 -> 获取完整内容
3. 上下文注入 -> Skill 内容作为 System Prompt
4. LLM 执行 -> 根据 Skill 指导完成任务

关键设计:
- SkillAgent: 统一的 Agent 接口
- 关键词匹配: 简单高效的 Skill 选择
- LLM 选择: 更智能但更慢的备选方案
- 职责分离: 选择、加载、执行各自独立

与 MCP 的配合:
- Skill: 指导 LLM "如何" 做某事
- MCP: 提供 "工具" 让 LLM 执行具体操作
- 可以组合: Skill 指导 + MCP 工具执行
""")


async def main():
    await run_demo()


if __name__ == "__main__":
    asyncio.run(main())
