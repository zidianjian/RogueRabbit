# RogueRabbit Agent Rules

## Mission

- 优先构建阶段一学习型 agent
- 用最小代码形成单一能力闭环
- 将规则、约束与验证写入仓库

## Structure

- `docs/index.md` 是文档导航入口
- `docs/03-harness/` 定义 agent 工作规则
- `src/rogue_rabbit/contracts/` 只放稳定边界
- `src/rogue_rabbit/adapters/` 负责外部集成
- `src/rogue_rabbit/runtime/` 负责 agent 运行编排

## Delivery

- 每个 0.x 版本只扩一个主题能力
- 先补文档与测试，再补最小实现
- 未进入当前版本范围的能力不提前实现

## Verification

- 新增结构必须有自动化验证
- 优先使用标准库与轻依赖
- CLI 入口必须保持可运行

## Docs

- 新能力先补 `docs/05-capabilities/`
- 新方案先补 `docs/06-specs/`
- 新决策优先记录到 ADR 模板
