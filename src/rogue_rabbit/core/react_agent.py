"""
ReAct Agent - 基于 Reasoning + Acting 模式的智能代理

ReAct = Reasoning + Acting
- LLM 分析问题，决定使用什么工具
- 执行工具调用
- 根据结果继续推理
- 直到得出最终答案
"""

import json
import re

from rogue_rabbit.contracts import Message, Role
from rogue_rabbit.contracts.mcp import MCPTool


class ReActAgent:
    """
    ReAct Agent - 使用 LLM 进行推理和工具调用

    使用方式:
        agent = ReActAgent(llm_client, mcp_client)
        answer = await agent.run("你的问题")
    """

    def __init__(
        self,
        llm_client,
        mcp_client,
        max_iterations: int = 10,
        verbose: bool = True,
    ):
        """
        初始化 ReAct Agent

        参数:
            llm_client: LLM 客户端（需实现 complete 方法）
            mcp_client: MCP 客户端（需实现 list_tools, call_tool 方法）
            max_iterations: 最大迭代次数
            verbose: 是否打印详细日志
        """
        self._llm = llm_client
        self._mcp = mcp_client
        self._max_iterations = max_iterations
        self._verbose = verbose

    def _log(self, message: str):
        """打印日志"""
        if self._verbose:
            print(message)

    async def run(self, question: str) -> str:
        """
        运行 Agent 回答问题

        参数:
            question: 用户问题

        返回:
            最终答案字符串
        """
        # 获取可用工具
        tools = await self._mcp.list_tools()
        tool_descriptions = self._format_tools(tools)

        # 构建系统提示
        system_prompt = f"""你是一个智能助手，可以使用工具来回答问题。

可用工具:
{tool_descriptions}

使用规则:
1. 当需要使用工具时，按以下格式回复：
   THOUGHT: 你的分析
   ACTION: 工具名称
   ARGUMENTS: {{"参数名": "参数值"}}

2. 当可以给出最终答案时，按以下格式回复：
   THOUGHT: 你的分析
   ANSWER: 最终答案

3. 如果工具返回错误，尝试其他方法或告诉用户无法完成。

请始终用中文回复。"""

        messages: list[Message] = [
            Message(role=Role.SYSTEM, content=system_prompt),
            Message(role=Role.USER, content=question),
        ]

        # ReAct 循环
        for i in range(self._max_iterations):
            self._log(f"\n{'='*50}")
            self._log(f"[轮次 {i + 1}]")

            # 调用 LLM
            response = self._llm.complete(messages)
            self._log(f"\n[LLM 回复]\n{response}")

            # 检查是否需要调用工具
            action, arguments = self._parse_action(response)

            if action and "ANSWER:" not in response:
                # 有工具调用
                self._log(f"\n[调用工具] {action}({arguments})")

                # 执行工具
                try:
                    result = await self._mcp.call_tool(action, arguments)
                    result_text = result.text if hasattr(result, "text") else str(result)
                    self._log(f"[工具结果] {result_text[:200]}{'...' if len(result_text) > 200 else ''}")

                    # 添加到消息历史
                    messages.append(Message(role=Role.ASSISTANT, content=response))
                    messages.append(
                        Message(
                            role=Role.USER,
                            content=f"工具执行结果:\n{result_text}",
                        )
                    )
                except Exception as e:
                    error_msg = f"工具调用失败: {str(e)}"
                    self._log(f"[错误] {error_msg}")
                    messages.append(Message(role=Role.ASSISTANT, content=response))
                    messages.append(
                        Message(role=Role.USER, content=f"工具执行出错:\n{error_msg}")
                    )

            elif "ANSWER:" in response:
                # 提取最终答案
                answer = self._extract_answer(response)
                return answer

            else:
                # LLM 直接回答了问题
                return response

        return "达到最大轮次限制，未能完成任务"

    def _format_tools(self, tools: list[MCPTool]) -> str:
        """格式化工具描述"""
        lines = []
        for tool in tools:
            params_desc = []
            for name, prop in tool.input_schema.properties.items():
                param_type = prop.get("type", "any")
                desc = prop.get("description", "")
                required = name in tool.input_schema.required
                req_mark = "必需" if required else "可选"
                params_desc.append(f"    - {name} ({param_type}, {req_mark}): {desc}")

            lines.append(f"- {tool.name}: {tool.description}")
            if params_desc:
                lines.extend(params_desc)

        return "\n".join(lines)

    def _parse_action(self, response: str) -> tuple[str, dict]:
        """解析工具调用 - 支持多种格式"""
        action = ""
        arguments = {}

        # 格式 1: 标准 ReAct 格式 (ACTION: xxx ARGUMENTS: {...})
        action_match = re.search(r"ACTION:\s*(\w+)", response)
        if action_match:
            action = action_match.group(1)
            args_match = re.search(r"ARGUMENTS:\s*(\{.*?\})", response, re.DOTALL)
            if args_match:
                try:
                    arguments = json.loads(args_match.group(1))
                except json.JSONDecodeError:
                    self._log("[警告] 无法解析参数，使用空参数")
            return action, arguments

        # 格式 2: 直接返回工具名和参数 (tool_name {"arg": "value"})
        # GLM 有时会直接输出这种格式
        direct_match = re.search(r"^(\w+)\s*(\{.*?\})\s*$", response.strip(), re.DOTALL)
        if direct_match:
            action = direct_match.group(1)
            try:
                arguments = json.loads(direct_match.group(2))
            except json.JSONDecodeError:
                pass
            return action, arguments

        # 格式 3: 只有工具名
        simple_match = re.search(r"^(\w+)\s*$", response.strip())
        if simple_match:
            return simple_match.group(1), {}

        # 格式 4: JSON 格式的函数调用
        json_match = re.search(r'\{[^{}]*"name"\s*:\s*"(\w+)"[^{}]*\}', response)
        if json_match:
            try:
                data = json.loads(json_match.group(0))
                action = data.get("name", "")
                arguments = data.get("arguments", {})
                return action, arguments
            except json.JSONDecodeError:
                pass

        return action, arguments

    def _extract_answer(self, response: str) -> str:
        """提取最终答案"""
        answer_match = re.search(r"ANSWER:\s*(.+)", response, re.DOTALL)
        return answer_match.group(1).strip() if answer_match else response
