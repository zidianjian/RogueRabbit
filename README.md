# RogueRabbit

RogueRabbit 是一个用 Python 构建的 agent 学习与工程化项目。

当前仓库采用三阶段路线：

- 阶段一：以 0.x 版本逐项学习 agent 常见能力
- 阶段二：将已有能力扩展到可用程度
- 阶段三：将已有能力优化到生产可用程度

当前骨架优先服务于阶段一，并参考 Harness Engineering 的思路组织仓库结构、文档结构与验证方式。

## 当前目录

- `docs/`：设计、架构、阶段路线、能力说明与模板
- `src/rogue_rabbit/`：Python 包骨架
- `tests/`：最小验证

## 下一步

- 0.1：完成 LLM 交互最小闭环
- 0.2：完成 MCP 调用最小闭环
- 0.3：完成 Skill 调用最小闭环
