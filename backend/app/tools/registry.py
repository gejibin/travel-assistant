"""工具注册表 - 优化版"""

from typing import Optional, Callable
from .base import Tool

class ToolRegistry:
    """HelloAgents工具注册表，支持Tool对象和函数注册"""

    def __init__(self, verbose: bool = True):
        self._tools: dict[str, Tool] = {}
        self._functions: dict[str, dict[str, Callable]] = {}
        self.verbose = verbose

    def _log(self, message: str) -> None:
        """内部日志方法"""
        if self.verbose:
            print(message)

    def register_tool(self, tool: Tool, auto_expand: bool = True) -> None:
        """注册Tool对象，支持自动展开"""
        if auto_expand and getattr(tool, 'expandable', False):
            if expanded_tools := tool.get_expanded_tools():
                for sub_tool in expanded_tools:
                    if sub_tool.name in self._tools:
                        self._log(f"⚠️ 警告：工具 '{sub_tool.name}' 已存在，将被覆盖。")
                    self._tools[sub_tool.name] = sub_tool
                self._log(f"✅ 工具 '{tool.name}' 已展开为 {len(expanded_tools)} 个独立工具")
                return

        if tool.name in self._tools:
            self._log(f"⚠️ 警告：工具 '{tool.name}' 已存在，将被覆盖。")

        self._tools[tool.name] = tool
        self._log(f"✅ 工具 '{tool.name}' 已注册。")

    def register_function(self, name: str, description: str, func: Callable[[str], str]) -> None:
        """直接注册函数作为工具"""
        if name in self._functions:
            self._log(f"⚠️ 警告：工具 '{name}' 已存在，将被覆盖。")

        self._functions[name] = {"description": description, "func": func}
        self._log(f"✅ 工具 '{name}' 已注册。")

    def unregister(self, name: str) -> bool:
        """注销工具，返回是否成功"""
        if name in self._tools:
            del self._tools[name]
            self._log(f"🗑️ 工具 '{name}' 已注销。")
            return True
        elif name in self._functions:
            del self._functions[name]
            self._log(f"🗑️ 工具 '{name}' 已注销。")
            return True
        else:
            self._log(f"⚠️ 工具 '{name}' 不存在。")
            return False

    def get_tool(self, name: str) -> Optional[Tool]:
        """获取Tool对象"""
        return self._tools.get(name)

    def get_function(self, name: str) -> Optional[Callable]:
        """获取工具函数"""
        return self._functions[name]["func"] if name in self._functions else None

    def execute_tool(self, name: str, input_text: str) -> str:
        """执行工具并返回结果"""
        try:
            if name in self._tools:
                return self._tools[name].run({"input": input_text})
            elif name in self._functions:
                return self._functions[name]["func"](input_text)
            else:
                return f"错误：未找到名为 '{name}' 的工具。"
        except Exception as e:
            return f"错误：执行工具 '{name}' 时发生异常: {str(e)}"

    def get_tools_description(self) -> str:
        """获取所有可用工具的格式化描述字符串"""
        descriptions = [
            f"- {tool.name}: {tool.description}" for tool in self._tools.values()
        ] + [
            f"- {name}: {info['description']}" for name, info in self._functions.items()
        ]
        return "\n".join(descriptions) if descriptions else "暂无可用工具"

    def list_tools(self) -> list[str]:
        """列出所有工具名称"""
        return [*self._tools.keys(), *self._functions.keys()]

    def get_all_tools(self) -> list[Tool]:
        """获取所有Tool对象"""
        return list(self._tools.values())

    def clear(self) -> None:
        """清空所有工具"""
        self._tools.clear()
        self._functions.clear()
        self._log("🧹 所有工具已清空。")

    def __len__(self) -> int:
        """返回工具总数"""
        return len(self._tools) + len(self._functions)

    def __contains__(self, name: str) -> bool:
        """检查工具是否存在"""
        return name in self._tools or name in self._functions

# 全局工具注册表
global_registry = ToolRegistry()
