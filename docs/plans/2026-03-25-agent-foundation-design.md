# Agent Foundation Design

**背景**

本仓库用于从零开发一个 Python agent 项目。项目分为三个阶段推进，当前优先建设阶段一的 0.x 学习型版本，目标是用尽量少的代码逐步掌握 agent 常见能力，并为后续可用化与生产化保留清晰演进路径。

**目标**

- 建立一个符合 Harness Engineering 思路的仓库骨架
- 优先定义稳定的目录边界与文档结构，而不是一次性堆满功能
- 让每个 0.x 小版本只扩展一个能力主题，便于学习、验证与回归
- 让仓库同时适合人类维护与 agent 执行

**非目标**

- 本轮不实现完整的生产级 agent 能力
- 本轮不引入外部服务依赖、数据库或复杂部署方案
- 本轮不绑定具体模型供应商与 MCP 服务商实现

**设计原则**

- 人类掌舵，agent 执行
- 规则进入仓库，而不是停留在对话中
- 先定义边界，再填充能力
- 先保证可验证，再扩展复杂度
- 文档既要给人读，也要给 agent 取用

**阶段划分**

1. 阶段一：0.x 学习型版本
   - 每个小版本只引入一个主题能力
   - 目标是形成最小闭环与清晰接口
   - 主题包括 LLM、MCP、Skill、Session、权限、记忆、日志、Planning、Agent Team
2. 阶段二：可用化
   - 将阶段一已有模块补齐为可持续使用的实现
   - 增加持久化、恢复、基础审计、可观察性与集成验证
3. 阶段三：生产化
   - 增加强约束、测试矩阵、故障恢复、性能与运维文档

**版本路线**

- 0.1：LLM 交互闭环
- 0.2：MCP 调用闭环
- 0.3：Skill 调用闭环
- 0.4：Session 管理
- 0.5：权限管理
- 0.6：记忆系统
- 0.7：日志系统
- 0.8：Checkpoint & Restore
- 0.9：Planning
- 0.10：Agent Team
- 0.11：端到端整合

**仓库结构**

```text
RogueRabbit/
├─ AGENTS.md
├─ README.md
├─ pyproject.toml
├─ docs/
├─ src/
│  └─ rogue_rabbit/
│     ├─ contracts/
│     ├─ config/
│     ├─ core/
│     ├─ adapters/
│     ├─ runtime/
│     ├─ apps/
│     └─ experiments/
├─ tests/
├─ examples/
└─ scripts/
```

**分层职责**

- contracts：协议、数据模型、错误边界
- config：配置模型与能力开关
- core：Session、权限、记忆、日志等核心域能力
- adapters：LLM、MCP、Skill 与外部接口适配
- runtime：agent loop、任务执行与 team 编排
- apps：CLI 与演示入口
- experiments：阶段一探索性样例

**文档结构**

```text
docs/
├─ index.md
├─ plans/
├─ 01-overview/
├─ 02-architecture/
├─ 03-harness/
├─ 04-phases/
├─ 05-capabilities/
├─ 06-specs/
├─ 07-guides/
└─ templates/
```

**文档职责**

- 01-overview：项目愿景、路线图、术语
- 02-architecture：原则、分层、模块映射
- 03-harness：agent 规则、上下文策略、验证策略、约束
- 04-phases：三个阶段的验收边界
- 05-capabilities：能力清单与演进目标
- 06-specs：后续具体特性方案
- 07-guides：开发与扩展操作指南
- templates：规格、ADR 与迭代模板

**Harness Engineering 落地方式**

- 使用 AGENTS.md 作为仓库入口规则
- 使用 docs/index.md 作为统一导航
- 将阶段目标、架构边界、验证要求固化到文档
- 用最小测试验证目录、导入路径与基础 CLI 可用
- 后续逐步加入结构约束检查、文档一致性检查与能力回归测试

**本轮交付**

- 设计文档
- 实施计划
- 最小项目骨架
- 最小 docs 管理结构
- 可运行的基础测试

**后续演进建议**

- 在 0.1 版本先完成模型抽象与 CLI 演示
- 在每个小版本完成后补一份 capability spec 与 iteration checklist
- 在阶段二开始前增加持久化与错误处理统一规范
