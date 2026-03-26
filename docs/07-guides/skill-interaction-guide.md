# Skill 交互指南

本指南介绍如何使用 RogueRabbit 的 Skill 系统。

## 什么是 Skill？

Skill 是**可执行知识包**，用于扩展 LLM 的能力。与 MCP 不同，Skill 不是工具或函数，而是提示词扩展。

### Skill vs MCP

| 特性 | MCP | Skill |
|------|-----|-------|
| 类型 | 工具/函数 | 提示词扩展 |
| 输入 | 结构化参数 (JSON) | 自然语言 |
| 输出 | 结构化结果 | 指导性内容 |
| 调用方式 | Tool Call | 上下文注入 |
| 适合场景 | 明确的输入输出操作 | 需要灵活处理的任务 |

## SKILL.md 格式

每个 Skill 是一个文件夹，包含 `SKILL.md` 文件：

```markdown
---
name: skill-name
description: 单行描述，告诉 LLM 何时使用此 skill
---

# Skill 标题

详细的指令内容...
```

### YAML Frontmatter

- `name`: Skill 名称（必需），用于调用
- `description`: 单行描述（必需），告诉 LLM 何时使用

### Markdown 内容

- 详细的指令
- 使用示例
- 注意事项

## 内置 Skills

| Skill | 描述 |
|-------|------|
| `calculator` | 数学计算，支持基本运算和常用函数 |
| `file-reader` | 读取和分析文本文件内容 |
| `code-review` | 代码审查，检查代码质量和潜在问题 |

## 使用方式

### 1. 发现 Skills

```python
from rogue_rabbit.skills import get_skill_dirs
from rogue_rabbit.core.skill_manager import SkillManager

# 获取 skill 搜索目录
skill_dirs = get_skill_dirs()

# 创建管理器
manager = SkillManager(skill_dirs)

# 发现所有 skills
result = manager.discover()
for meta in result.skills:
    print(f"- {meta.name}: {meta.description}")
```

### 2. 加载 Skill

```python
# 加载指定 skill
skill = manager.load("calculator")

# 获取完整提示词
full_prompt = skill.get_full_prompt()
print(full_prompt)
```

### 3. 与 LLM 集成

```python
from rogue_rabbit.adapters import GLMClient

llm = GLMClient()

# 构建 system prompt
system_prompt = f"""你正在使用 {skill.meta.name} Skill。

{skill.get_full_prompt()}

请根据以上指导完成任务。
"""

# 调用 LLM
response = llm.complete([
    Message(role=Role.SYSTEM, content=system_prompt),
    Message(role=Role.USER, content="计算 2^20"),
])
```

## 创建自定义 Skill

### 1. 创建目录结构

```
skills/
└── my-skill/
    ├── SKILL.md
    └── helpers/          # 可选
        └── script.py
```

### 2. 编写 SKILL.md

```markdown
---
name: my-skill
description: 简短描述，告诉 LLM 何时使用此 skill
---

# My Skill

详细说明如何使用这个 skill...

## 使用方式

1. 步骤一
2. 步骤二

## 示例

- 输入: xxx
- 输出: xxx

## 注意事项

- 注意点1
- 注意点2
```

### 3. 测试 Skill

```python
manager = SkillManager([Path("skills/")])
result = manager.discover()

if manager.has_skill("my-skill"):
    skill = manager.load("my-skill")
    print(skill.get_full_prompt())
```

## 最佳实践

1. **描述要精确**: description 决定 LLM 何时选择此 skill
2. **指令要清晰**: 详细说明使用方式和示例
3. **保持单一职责**: 每个 skill 专注一个任务
4. **提供示例**: 帮助 LLM 理解预期行为

## 相关文件

- `contracts/skill.py`: Skill 数据结构定义
- `core/skill_manager.py`: Skill 管理器
- `skills/`: 内置 Skills 目录
- `experiments/08_skill_basic.py`: 基础实验
- `experiments/09_skill_with_llm.py`: LLM 集成实验
