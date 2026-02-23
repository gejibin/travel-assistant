"""简单Agent实现 - 优化版"""

from typing import Optional, Iterator, TYPE_CHECKING
import re
import json

from ..llm.agent import Agent
from ..llm.llm import HelloAgentsLLM
from ..llm.config import Config
from ..llm.message import Message

if TYPE_CHECKING:
    from ..registry import ToolRegistry

# 工具调用正则模式
TOOL_CALL_PATTERN = re.compile(r'\[TOOL_CALL:([^:]+):([^\]]+)\]')

# 工具特定的action推断规则
TOOL_ACTION_RULES = {
    'memory': {
        'recall': ('search', 'query'),
        'store': ('add', 'content'),
        'query': ('search', None),
        'content': ('add', None)
    },
    'rag': {
        'search': ('search', 'query'),
        'query': ('search', None),
        'text': ('add_text', None)
    }
}

# 简单参数推断规则
SIMPLE_PARAM_RULES = {
    'rag': {'action': 'search', 'query': None},
    'memory': {'action': 'search', 'query': None}
}

class SimpleAgent(Agent):
    """简单的对话Agent，支持可选的工具调用"""
    
    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None,
        tool_registry: Optional['ToolRegistry'] = None,
        enable_tool_calling: bool = True
    ):
        super().__init__(name, llm, system_prompt, config)
        self.tool_registry = tool_registry
        self.enable_tool_calling = enable_tool_calling and tool_registry is not None
    
    def _get_enhanced_system_prompt(self) -> str:
        """构建增强的系统提示词，包含工具信息"""
        base_prompt = self.system_prompt or "你是一个有用的AI助手。"
        
        if not self.enable_tool_calling or not self.tool_registry:
            return base_prompt
        
        tools_description = self.tool_registry.get_tools_description()
        if not tools_description or tools_description == "暂无可用工具":
            return base_prompt
        
        tools_section = (
            "\n\n## 可用工具\n"
            "你可以使用以下工具来帮助回答问题：\n"
            f"{tools_description}\n"
            "\n## 工具调用格式\n"
            "当需要使用工具时，请使用以下格式：\n"
            "`[TOOL_CALL:{tool_name}:{parameters}]`\n\n"
            "### 参数格式说明\n"
            "1. **多个参数**：使用 `key=value` 格式，用逗号分隔\n"
            "   示例：`[TOOL_CALL:calculator_multiply:a=12,b=8]`\n"
            "2. **单个参数**：直接使用 `key=value`\n"
            "   示例：`[TOOL_CALL:search:query=Python编程]`\n"
            "3. **简单查询**：可以直接传入文本\n"
            "   示例：`[TOOL_CALL:search:Python编程]`\n\n"
            "### 重要提示\n"
            "- 参数名必须与工具定义的参数名完全匹配\n"
            "- 数字参数直接写数字，不需要引号：`a=12` 而不是 `a=\"12\"`\n"
            "- 工具调用结果会自动插入到对话中，然后你可以基于结果继续回答\n"
        )
        
        return base_prompt + tools_section
    
    def _parse_tool_calls(self, text: str) -> list[dict]:
        """解析文本中的工具调用"""
        return [
            {
                'tool_name': tool_name.strip(),
                'parameters': parameters.strip(),
                'original': f'[TOOL_CALL:{tool_name}:{parameters}]'
            }
            for tool_name, parameters in TOOL_CALL_PATTERN.findall(text)
        ]
    
    def _execute_tool_call(self, tool_name: str, parameters: str) -> str:
        """执行工具调用"""
        if not self.tool_registry:
            return "❌ 错误：未配置工具注册表"

        try:
            tool = self.tool_registry.get_tool(tool_name)
            if not tool:
                return f"❌ 错误：未找到工具 '{tool_name}'"

            param_dict = self._parse_tool_parameters(tool_name, parameters)
            result = tool.run(param_dict)
            return f"🔧 工具 {tool_name} 执行结果：\n{result}"

        except Exception as e:
            return f"❌ 工具调用失败：{str(e)}"

    def _parse_tool_parameters(self, tool_name: str, parameters: str) -> dict:
        """智能解析工具参数"""
        # 尝试JSON格式
        if parameters.strip().startswith('{'):
            try:
                param_dict = json.loads(parameters)
                return self._convert_parameter_types(tool_name, param_dict)
            except json.JSONDecodeError:
                pass

        # key=value格式
        if '=' in parameters:
            param_dict = dict(
                pair.split('=', 1) if '=' in pair else (pair, '')
                for pair in (p.strip() for p in parameters.split(','))
            )
            param_dict = {k.strip(): v.strip() for k, v in param_dict.items()}
            param_dict = self._convert_parameter_types(tool_name, param_dict)
            
            if 'action' not in param_dict:
                param_dict = self._infer_action(tool_name, param_dict)
            
            return param_dict

        # 简单参数
        return self._infer_simple_parameters(tool_name, parameters)

    def _convert_parameter_types(self, tool_name: str, param_dict: dict) -> dict:
        """根据工具的参数定义转换参数类型"""
        if not self.tool_registry:
            return param_dict

        tool = self.tool_registry.get_tool(tool_name)
        if not tool:
            return param_dict

        try:
            tool_params = tool.get_parameters()
            param_types = {param.name: param.type for param in tool_params}
        except:
            return param_dict

        converted_dict = {}
        for key, value in param_dict.items():
            if key not in param_types:
                converted_dict[key] = value
                continue
            
            param_type = param_types[key]
            try:
                if param_type in ('number', 'integer') and isinstance(value, str):
                    converted_dict[key] = float(value) if param_type == 'number' else int(value)
                elif param_type == 'boolean':
                    converted_dict[key] = value.lower() in ('true', '1', 'yes') if isinstance(value, str) else bool(value)
                else:
                    converted_dict[key] = value
            except (ValueError, TypeError):
                converted_dict[key] = value

        return converted_dict

    def _infer_action(self, tool_name: str, param_dict: dict) -> dict:
        """根据工具类型和参数推断action"""
        if tool_name not in TOOL_ACTION_RULES:
            return param_dict
        
        rules = TOOL_ACTION_RULES[tool_name]
        for key, (action, target_key) in rules.items():
            if key in param_dict:
                param_dict['action'] = action
                if target_key and key != target_key:
                    param_dict[target_key] = param_dict.pop(key)
                break
        
        return param_dict

    def _infer_simple_parameters(self, tool_name: str, parameters: str) -> dict:
        """为简单参数推断完整的参数字典"""
        if tool_name in SIMPLE_PARAM_RULES:
            result = SIMPLE_PARAM_RULES[tool_name].copy()
            result['query'] = parameters
            return result
        return {'input': parameters}

    def run(self, input_text: str, max_tool_iterations: int = 3, **kwargs) -> str:
        """运行SimpleAgent，支持可选的工具调用"""
        messages = self._build_messages(input_text)
        
        if not self.enable_tool_calling:
            response = self.llm.invoke(messages, **kwargs)
            self._save_conversation(input_text, response)
            return response
        
        # 迭代处理工具调用
        final_response = self._run_with_tools(messages, max_tool_iterations, **kwargs)
        self._save_conversation(input_text, final_response)
        return final_response

    def _build_messages(self, input_text: str) -> list[dict]:
        """构建消息列表"""
        messages = [{"role": "system", "content": self._get_enhanced_system_prompt()}]
        messages.extend({"role": msg.role, "content": msg.content} for msg in self._history)
        messages.append({"role": "user", "content": input_text})
        return messages

    def _run_with_tools(self, messages: list[dict], max_iterations: int, **kwargs) -> str:
        """运行带工具调用的对话"""
        for _ in range(max_iterations):
            response = self.llm.invoke(messages, **kwargs)
            tool_calls = self._parse_tool_calls(response)
            
            if not tool_calls:
                return response
            
            # 执行工具并更新消息
            tool_results = [self._execute_tool_call(call['tool_name'], call['parameters']) for call in tool_calls]
            clean_response = response
            for call in tool_calls:
                clean_response = clean_response.replace(call['original'], "")
            
            messages.append({"role": "assistant", "content": clean_response})
            messages.append({
                "role": "user",
                "content": f"工具执行结果：\n{chr(10).join(tool_results)}\n\n请基于这些结果给出完整的回答。"
            })
        
        return self.llm.invoke(messages, **kwargs)

    def _save_conversation(self, input_text: str, response: str) -> None:
        """保存对话到历史记录"""
        self.add_message(Message(input_text, "user"))
        self.add_message(Message(response, "assistant"))

    def add_tool(self, tool, auto_expand: bool = True) -> None:
        """添加工具到Agent"""
        if not self.tool_registry:
            from ..registry import ToolRegistry
            self.tool_registry = ToolRegistry()
            self.enable_tool_calling = True

        self.tool_registry.register_tool(tool, auto_expand=auto_expand)

    def remove_tool(self, tool_name: str) -> bool:
        """移除工具"""
        return self.tool_registry.unregister(tool_name) if self.tool_registry else False

    def list_tools(self) -> list:
        """列出所有可用工具"""
        return self.tool_registry.list_tools() if self.tool_registry else []

    def has_tools(self) -> bool:
        """检查是否有可用工具"""
        return self.enable_tool_calling and self.tool_registry is not None

    def stream_run(self, input_text: str, **kwargs) -> Iterator[str]:
        """流式运行Agent"""
        messages = [{"role": "system", "content": self.system_prompt}] if self.system_prompt else []
        messages.extend({"role": msg.role, "content": msg.content} for msg in self._history)
        messages.append({"role": "user", "content": input_text})
        
        full_response = ""
        for chunk in self.llm.stream_invoke(messages, **kwargs):
            full_response += chunk
            yield chunk
        
        self._save_conversation(input_text, full_response)
