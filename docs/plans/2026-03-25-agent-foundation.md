# Agent Foundation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 创建一个以阶段一优先、符合 Harness Engineering 思路的 Python agent 项目最小骨架与 docs 管理结构。

**Architecture:** 先建立稳定的仓库入口、分层目录、文档导航与最小可运行入口，再通过测试验证目录存在、模块可导入和 CLI 可执行。代码保持极简，为后续 0.x 迭代留出明确扩展位。

**Tech Stack:** Python 3、pyproject.toml、src 布局、unittest、Markdown 文档

---

### Task 1: 编写骨架测试

**Files:**
- Create: `tests/test_project_layout.py`

**Step 1: Write the failing test**

```python
import unittest
from pathlib import Path


class ProjectLayoutTestCase(unittest.TestCase):
    def test_expected_paths_exist(self) -> None:
        root = Path(__file__).resolve().parents[1]
        expected = [
            root / "README.md",
            root / "AGENTS.md",
            root / "pyproject.toml",
            root / "docs" / "index.md",
            root / "src" / "rogue_rabbit" / "__init__.py",
            root / "src" / "rogue_rabbit" / "apps" / "cli.py",
        ]
        for path in expected:
            self.assertTrue(path.exists(), path)
```

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_project_layout -v`
Expected: FAIL，因为项目文件尚未创建

**Step 3: Write minimal implementation**

创建 README、AGENTS、pyproject、docs/index、src 包与 CLI 文件。

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_project_layout -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_project_layout.py README.md AGENTS.md pyproject.toml docs/index.md src/rogue_rabbit
git commit -m "feat: add agent foundation skeleton"
```

### Task 2: 创建 docs 管理结构

**Files:**
- Create: `docs/index.md`
- Create: `docs/01-overview/vision.md`
- Create: `docs/01-overview/roadmap.md`
- Create: `docs/02-architecture/principles.md`
- Create: `docs/02-architecture/layers.md`
- Create: `docs/02-architecture/module-map.md`
- Create: `docs/03-harness/agent-rules.md`
- Create: `docs/03-harness/verification-policy.md`
- Create: `docs/04-phases/phase-1-learning.md`
- Create: `docs/04-phases/phase-2-usable.md`
- Create: `docs/04-phases/phase-3-production.md`
- Create: `docs/05-capabilities/index.md`
- Create: `docs/06-specs/README.md`
- Create: `docs/07-guides/local-dev.md`
- Create: `docs/07-guides/add-capability.md`
- Create: `docs/templates/capability-spec.md`
- Create: `docs/templates/adr.md`
- Create: `docs/templates/iteration-checklist.md`

**Step 1: Write the failing test**

在 `tests/test_project_layout.py` 增加对 docs 关键文件与目录的断言。

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_project_layout -v`
Expected: FAIL，因为 docs 结构尚未补齐

**Step 3: Write minimal implementation**

为每个目录创建最小说明文档，统一字段与导航方式。

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_project_layout -v`
Expected: PASS

**Step 5: Commit**

```bash
git add docs tests/test_project_layout.py
git commit -m "docs: add harness-oriented documentation structure"
```

### Task 3: 创建最小 Python 包骨架

**Files:**
- Create: `src/rogue_rabbit/__init__.py`
- Create: `src/rogue_rabbit/contracts/__init__.py`
- Create: `src/rogue_rabbit/config/__init__.py`
- Create: `src/rogue_rabbit/core/__init__.py`
- Create: `src/rogue_rabbit/adapters/__init__.py`
- Create: `src/rogue_rabbit/runtime/__init__.py`
- Create: `src/rogue_rabbit/apps/__init__.py`
- Create: `src/rogue_rabbit/apps/cli.py`
- Create: `src/rogue_rabbit/experiments/__init__.py`

**Step 1: Write the failing test**

在 `tests/test_project_layout.py` 增加对包导入与 CLI 输出的断言。

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_project_layout -v`
Expected: FAIL，因为模块或入口尚未完整

**Step 3: Write minimal implementation**

补齐包目录与极简 CLI，输出项目名称、阶段与版本。

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_project_layout -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src tests/test_project_layout.py
git commit -m "feat: add minimal python package layout"
```

### Task 4: 验证基础可用性

**Files:**
- Modify: `tests/test_project_layout.py`

**Step 1: Write the failing test**

增加对 `python -m rogue_rabbit.apps.cli` 可执行性的校验思路，并确认测试可覆盖导入路径。

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_project_layout -v`
Expected: FAIL，如果入口路径或输出不符合预期

**Step 3: Write minimal implementation**

调整 CLI 与测试路径处理，确保基础入口可执行。

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_project_layout -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src tests/test_project_layout.py
git commit -m "test: verify minimal agent foundation entrypoint"
```
