"""
实验 14: 知识检测 - 测试你对 v0.1-v0.5 的掌握程度
==================================================

这是一个交互式知识检测工具，帮助你评估对 RogueRabbit 项目的理解程度。

覆盖版本:
- v0.1: LLM 交互基础（消息模型、LLM 客户端、系统提示词）
- v0.2: MCP 工具调用（MCP 协议、ReAct Agent、传输方式）
- v0.3: Skill 知识管理（Skill 协议、SkillManager、上下文注入）
- v0.4: Session 会话管理（会话状态、存储后端、上下文窗口）
- v0.5: Memory 长期记忆（记忆结构、检索策略、Session 集成）

运行方式:
--------
    python -m rogue_rabbit.experiments.14_knowledge_check
"""

import logging

logging.basicConfig(level=logging.INFO, format="%(name)s - %(message)s")
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# ============================================================
# 题库定义
# ============================================================

QUESTIONS = [
    # ========================
    # v0.1 LLM 交互基础
    # ========================
    {
        "version": "v0.1",
        "question": "Message 消息由哪两个核心属性组成？",
        "options": [
            "A. type 和 data",
            "B. role 和 content",
            "C. sender 和 text",
            "D. category 和 value",
        ],
        "answer": "B",
        "explanation": "Message(role=Role.USER, content='你好') — 由 role（角色）和 content（内容）组成，定义在 contracts/messages.py 中。",
    },
    {
        "version": "v0.1",
        "question": "为什么 Message 使用 frozen=True（不可变数据类）？",
        "options": [
            "A. 提高运行速度",
            "B. 减少内存占用",
            "C. 避免意外修改，保证数据安全",
            "D. 支持多线程并发",
        ],
        "answer": "C",
        "explanation": "frozen=True 使消息一旦创建就不能被修改，避免意外的数据污染，安全地在多处共享消息对象。",
    },
    {
        "version": "v0.1",
        "question": "System Prompt（系统提示词）的主要作用是什么？",
        "options": [
            "A. 存储用户的个人信息",
            "B. 定义 AI 的行为准则和角色",
            "C. 记录对话历史",
            "D. 管理 API 调用频率",
        ],
        "answer": "B",
        "explanation": "System Prompt 通过 SYSTEM 角色消息定义 AI 的行为准则，如'你是一个有帮助的助手'。它在消息列表开头，影响整个对话的风格。",
    },
    {
        "version": "v0.1",
        "question": "LLM 是'有状态'还是'无状态'的？这意味着什么？",
        "options": [
            "A. 有状态 — LLM 会自动记住之前的对话",
            "B. 无状态 — 每次调用需要发送完整对话历史",
            "C. 有状态 — 只需要发送最新的消息",
            "D. 无状态 — LLM 不需要任何上下文",
        ],
        "answer": "B",
        "explanation": "LLM 是无状态的，每次调用都需要发送完整的消息历史。维护消息列表是调用方（如 Conversation 类）的责任。",
    },
    # ========================
    # v0.2 MCP 工具调用
    # ========================
    {
        "version": "v0.2",
        "question": "MCP 协议定义了哪三种核心资源类型？",
        "options": [
            "A. Input、Output、Error",
            "B. Tool、Resource、Prompt",
            "C. Function、Variable、Template",
            "D. Action、Data、Config",
        ],
        "answer": "B",
        "explanation": "MCP 定义了 Tool（可调用的工具函数）、Resource（可读取的资源数据）、Prompt（可复用的提示模板）三种原语。",
    },
    {
        "version": "v0.2",
        "question": "ReAct Agent 的核心循环是什么？",
        "options": [
            "A. 接收 → 编码 → 传输",
            "B. 训练 → 验证 → 测试",
            "C. 推理(Reason) → 行动(Act) → 观察(Observe)",
            "D. 输入 → 处理 → 输出",
        ],
        "answer": "C",
        "explanation": "ReAct = Reasoning + Acting。Agent 先推理分析问题，再调用工具执行行动，然后观察结果，循环直到得出最终答案。",
    },
    {
        "version": "v0.2",
        "question": "MCP 支持哪两种传输方式？",
        "options": [
            "A. TCP 和 UDP",
            "B. STDIO 和 HTTP",
            "C. WebSocket 和 gRPC",
            "D. FTP 和 SMTP",
        ],
        "answer": "B",
        "explanation": "MCP 支持 STDIO（标准输入输出，适合本地进程间通信）和 HTTP（适合远程服务和分布式部署）两种传输方式。",
    },
    {
        "version": "v0.2",
        "question": "项目中 LLMClient 使用 Protocol（协议）而不是抽象基类的好处是什么？",
        "options": [
            "A. 运行速度更快",
            "B. 不需要继承，只需实现相同方法即可（鸭子类型）",
            "C. 支持更多数据类型",
            "D. 自动生成文档",
        ],
        "answer": "B",
        "explanation": "Protocol 是 Python 的结构化子类型（鸭子类型），不需要显式继承，只要实现了 complete() 方法就满足 LLMClient 协议。",
    },
    # ========================
    # v0.3 Skill 知识管理
    # ========================
    {
        "version": "v0.3",
        "question": "Skill 和 MCP 的本质区别是什么？",
        "options": [
            "A. Skill 是函数调用，MCP 是提示词扩展",
            "B. Skill 是提示词扩展（上下文注入），MCP 是工具/函数调用",
            "C. Skill 只能用于本地，MCP 只能用于远程",
            "D. 没有区别，只是名称不同",
        ],
        "answer": "B",
        "explanation": "Skill 是可执行知识包，通过上下文注入扩展 LLM 的知识；MCP 是结构化的工具调用，有明确的输入输出。Skill 指导'如何做'，MCP 提供'执行工具'。",
    },
    {
        "version": "v0.3",
        "question": "Skill 的 SKILL.md 文件中 YAML frontmatter 必须包含哪两个字段？",
        "options": [
            "A. name 和 version",
            "B. name 和 description",
            "C. title 和 author",
            "D. type 和 content",
        ],
        "answer": "B",
        "explanation": "SKILL.md 的 YAML frontmatter 必须包含 name（Skill 名称）和 description（描述，告诉 LLM 何时使用此 Skill）。",
    },
    {
        "version": "v0.3",
        "question": "SkillManager 的 discover() 方法返回什么？",
        "options": [
            "A. 一个 Skill 对象",
            "B. 一个字符串列表",
            "C. 一个 SkillDiscoveryResult 对象（包含 skills 和 errors）",
            "D. 一个字典",
        ],
        "answer": "C",
        "explanation": "discover() 返回 SkillDiscoveryResult，包含 skills（成功加载的 SkillMeta 列表）和 errors（加载失败的错误信息列表）。",
    },
    {
        "version": "v0.3",
        "question": "Skill 是如何与 LLM 集成的？",
        "options": [
            "A. 通过 MCP 工具调用",
            "B. 通过文件系统读取",
            "C. 通过将 Skill 内容注入到 System Prompt 中",
            "D. 通过数据库查询",
        ],
        "answer": "C",
        "explanation": "Skill 通过上下文注入方式集成：将 Skill 的完整提示词内容注入到 System Prompt 中，让 LLM 根据 Skill 指导执行任务。",
    },
    # ========================
    # v0.4 Session 会话管理
    # ========================
    {
        "version": "v0.4",
        "question": "Session 的三种状态及其转换关系是什么？",
        "options": [
            "A. OPEN → RUNNING → STOPPED",
            "B. ACTIVE <-> IDLE -> CLOSED",
            "C. START -> PAUSE -> END",
            "D. CREATE -> USE -> DESTROY",
        ],
        "answer": "B",
        "explanation": "Session 三种状态：ACTIVE（活跃，可对话）<-> IDLE（暂停，可恢复）-> CLOSED（关闭，不可恢复但数据保留）。",
    },
    {
        "version": "v0.4",
        "question": "Session 和之前实验02中的 Conversation 类有什么核心区别？",
        "options": [
            "A. Session 支持多语言",
            "B. Session 有元数据、生命周期管理和持久化能力",
            "C. Session 使用不同的 API",
            "D. Session 只能用于生产环境",
        ],
        "answer": "B",
        "explanation": "Conversation 是简单的消息列表封装；Session 增加了元数据（ID、时间、状态）、完整的生命周期管理（创建/暂停/恢复/关闭）和持久化支持。",
    },
    {
        "version": "v0.4",
        "question": "ContextWindowManager 的 KEEP_FIRST_LAST 截断策略会保留什么？",
        "options": [
            "A. 只保留最后 N 条消息",
            "B. 只保留前 N 条消息",
            "C. 保留前 N 条和后 M 条消息",
            "D. 随机保留部分消息",
        ],
        "answer": "C",
        "explanation": "KEEP_FIRST_LAST 保留前 keep_first 条消息（通常是系统提示词+首轮对话）和后 keep_last 条消息（最近的对话），兼顾历史背景和最新上下文。",
    },
    {
        "version": "v0.4",
        "question": "SessionStore 使用 Protocol 接口的好处是什么？",
        "options": [
            "A. 代码运行更快",
            "B. 支持多种存储后端（内存/文件），且可以灵活切换",
            "C. 自动备份数据",
            "D. 支持多用户并发",
        ],
        "answer": "B",
        "explanation": "SessionStore Protocol 定义了存储接口，MemorySessionStore 和 FileSessionStore 分别实现。SessionManager 不关心具体后端，可以灵活切换。",
    },
    # ========================
    # v0.5 Memory 长期记忆
    # ========================
    {
        "version": "v0.5",
        "question": "Session 和 Memory 的核心区别是什么？",
        "options": [
            "A. Session 存文件，Memory 存数据库",
            "B. Session 是短期对话历史，Memory 是跨会话的长期知识",
            "C. Session 用内存，Memory 用硬盘",
            "D. Session 给用户用，Memory 给开发者用",
        ],
        "answer": "B",
        "explanation": "Session 负责当前对话的消息历史（短期），随会话关闭而停止；Memory 负责跨会话的关键知识（长期），持久保存。",
    },
    {
        "version": "v0.5",
        "question": "MemoryItem 的 importance（重要性）评分 0.9-1.0 通常用于什么？",
        "options": [
            "A. 普通对话内容",
            "B. 可遗忘的低价值信息",
            "C. 核心信息，如用户名和关键偏好",
            "D. 系统配置信息",
        ],
        "answer": "C",
        "explanation": "0.9-1.0 代表核心信息（用户名、关键偏好），0.7-0.8 是重要信息，0.4-0.6 是一般信息，0.0-0.3 是可遗忘的低价值信息。",
    },
    {
        "version": "v0.5",
        "question": "Memory 如何与 Session 集成来增强对话质量？",
        "options": [
            "A. 直接替换 Session 的消息历史",
            "B. 检索相关记忆注入到 Session 的 System Prompt 中",
            "C. 通过 MCP 工具调用传递记忆",
            "D. 使用 Skill 间接传递",
        ],
        "answer": "B",
        "explanation": "通过 get_context_for_session() 检索与当前对话相关的记忆，格式化后注入到 System Prompt 中，让 LLM 在对话时可以引用历史知识。",
    },
    {
        "version": "v0.5",
        "question": "MemoryManager 的 search() 方法支持哪些过滤条件？",
        "options": [
            "A. 只支持关键词搜索",
            "B. 关键词搜索 + 分类过滤 + 重要性阈值过滤",
            "C. 只支持时间范围过滤",
            "D. 只支持分类过滤",
        ],
        "answer": "B",
        "explanation": "search() 方法先按关键词匹配，再按 category 过滤，最后按 min_importance 过滤，返回按重要性排序的结果。",
    },
]


# ============================================================
# 测试引擎
# ============================================================


def run_quiz() -> dict[str, list[bool]]:
    """
    运行知识检测

    返回:
    -----
    按版本分组的结果 {version: [True/False, ...]}
    """
    results: dict[str, list[bool]] = {}

    print("\n" + "=" * 60)
    print("RogueRabbit 知识检测 (v0.1 - v0.5)")
    print("=" * 60)
    print(f"\n共 {len(QUESTIONS)} 道题，覆盖 v0.1 - v0.5 所有核心概念")
    print("每题 4 个选项，输入 A/B/C/D 作答\n")

    current_version = ""

    for i, q in enumerate(QUESTIONS, 1):
        # 版本标题
        if q["version"] != current_version:
            current_version = q["version"]
            version_names = {
                "v0.1": "LLM 交互基础",
                "v0.2": "MCP 工具调用",
                "v0.3": "Skill 知识管理",
                "v0.4": "Session 会话管理",
                "v0.5": "Memory 长期记忆",
            }
            print(f"\n{'─' * 60}")
            print(f"  {current_version} - {version_names[current_version]}")
            print(f"{'─' * 60}")

        # 题目
        print(f"\n[{i}/{len(QUESTIONS)}] {q['question']}")
        for opt in q["options"]:
            print(f"    {opt}")

        # 获取答案
        while True:
            answer = input("\n  你的答案: ").strip().upper()
            if answer in ("A", "B", "C", "D"):
                break
            if answer == "QUIT":
                print("\n  已退出测试。")
                return results
            print("  请输入 A/B/C/D（输入 QUIT 退出）")

        # 判断对错
        correct = answer == q["answer"]
        results.setdefault(q["version"], []).append(correct)

        if correct:
            print(f"  [正确] {q['explanation']}")
        else:
            print(f"  [错误] 正确答案是 {q['answer']}")
            print(f"  {q['explanation']}")

    return results


def show_results(results: dict[str, list[bool]]) -> None:
    """显示测试结果"""
    version_names = {
        "v0.1": "LLM 交互基础",
        "v0.2": "MCP 工具调用",
        "v0.3": "Skill 知识管理",
        "v0.4": "Session 会话管理",
        "v0.5": "Memory 长期记忆",
    }

    total_correct = sum(sum(v) for v in results.values())
    total_count = sum(len(v) for v in results.values())
    score = int(total_correct / total_count * 100) if total_count > 0 else 0

    print("\n" + "=" * 60)
    print("测试结果")
    print("=" * 60)
    print(f"\n  总分: {total_correct}/{total_count} ({score}分)")

    # 各版本得分
    print(f"\n  {'版本':<10} {'主题':<20} {'正确率':<10}")
    print(f"  {'─' * 40}")

    weak_versions = []
    for version in ["v0.1", "v0.2", "v0.3", "v0.4", "v0.5"]:
        if version in results:
            correct = sum(results[version])
            total = len(results[version])
            pct = int(correct / total * 100) if total > 0 else 0
            name = version_names.get(version, "")
            bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
            print(f"  {version:<10} {name:<20} {correct}/{total} {bar} {pct}%")
            if pct < 70:
                weak_versions.append((version, name, pct))

    # 薄弱环节提示
    if weak_versions:
        print(f"\n  薄弱环节:")
        for version, name, pct in weak_versions:
            print(f"    - {version} {name} ({pct}%)")
            if version == "v0.1":
                print(f"      建议: 重做实验 01-03，理解 Message/Role/LLMClient 基础")
            elif version == "v0.2":
                print(f"      建议: 重做实验 04-07，理解 MCP 协议和 ReAct Agent")
            elif version == "v0.3":
                print(f"      建议: 重做实验 08-09，理解 Skill 和上下文注入")
            elif version == "v0.4":
                print(f"      建议: 重做实验 10-11，理解 Session 生命周期和持久化")
            elif version == "v0.5":
                print(f"      建议: 重做实验 12-13，理解 Memory 和 Session 集成")
    else:
        print(f"\n  所有版本掌握良好!")

    # 评价
    print(f"\n  评价: ", end="")
    if score >= 90:
        print("优秀! 你已经完全掌握了 RogueRabbit 的核心概念。")
    elif score >= 70:
        print("良好! 大部分概念已经理解，可以针对性复习薄弱环节。")
    elif score >= 50:
        print("一般。建议重新运行相关实验，加深理解。")
    else:
        print("需要加强。建议按顺序重新学习 v0.1 到 v0.5 的所有实验。")

    print("\n" + "=" * 60)


def main() -> None:
    """主函数"""
    results = run_quiz()
    if results:
        show_results(results)


if __name__ == "__main__":
    main()
