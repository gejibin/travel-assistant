"""优化后的协议工具集合 - 专注于MCP Tool"""

from typing import Any, Optional
from ..base import Tool, ToolParameter
import os
import asyncio
import concurrent.futures
from .client import MCPClient


# MCP服务器环境变量映射
MCP_SERVER_ENV_MAP = {
    "server-github": ["GITHUB_PERSONAL_ACCESS_TOKEN"],
    "server-slack": ["SLACK_BOT_TOKEN", "SLACK_TEAM_ID"],
    "server-google-drive": ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REFRESH_TOKEN"],
    "server-postgres": ["POSTGRES_CONNECTION_STRING"],
    "server-sqlite": [],
    "server-filesystem": [],
}


class MCPTool(Tool):
    """MCP (Model Context Protocol) 工具
    
    连接到MCP服务器并调用其提供的工具、资源和提示词。
    
    功能：
    - 列出服务器提供的工具
    - 调用服务器工具
    - 读取服务器资源
    - 获取提示词模板

    使用示例:
        >>>
        >>> # 方式1: 使用内置演示服务器
        >>> tool = MCPTool()  # 自动创建内置服务器
        >>> result = tool.run({"action": "list_tools"})
        >>>
        >>> # 方式2: 连接到外部 MCP 服务器
        >>> tool = MCPTool(server_command=["python", "examples/mcp_example.py"])
        >>> result = tool.run({"action": "list_tools"})
        >>>
        >>> # 方式3: 使用自定义 FastMCP 服务器
        >>> from fastmcp import FastMCP
        >>> server = FastMCP("MyServer")
        >>> tool = MCPTool(server=server)

    注意：使用 fastmcp 库，已包含在依赖中
    """
    
    def __init__(
        self,
        name: str = "mcp",
        description: Optional[str] = None,
        server_command: Optional[list[str]] = None,
        server_args: Optional[list[str]] = None,
        server: Optional[Any] = None,
        auto_expand: bool = True,
        env: Optional[dict[str, str]] = None,
        env_keys: Optional[list[str]] = None
    ):
        """
        初始化 MCP 工具

        Args:
            name: 工具名称（默认为"mcp"，建议为不同服务器指定不同名称）
            description: 工具描述（可选，默认为通用描述）
            server_command: 服务器启动命令（如 ["python", "server.py"]）
            server_args: 服务器参数列表
            server: FastMCP 服务器实例（可选，用于内存传输）
            auto_expand: 是否自动展开为独立工具（默认True）
            env: 环境变量字典（优先级最高，直接传递给MCP服务器）
            env_keys: 要从系统环境变量加载的key列表（优先级中等）

        环境变量优先级（从高到低）：
            1. 直接传递的env参数
            2. env_keys指定的环境变量
            3. 自动检测的环境变量（根据server_command）

        注意：如果所有参数都为空，将创建内置演示服务器

        示例：
            >>> # 方式1：直接传递环境变量（优先级最高）
            >>> github_tool = MCPTool(
            ...     name="github",
            ...     server_command=["npx", "-y", "@modelcontextprotocol/server-github"],
            ...     env={"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_xxx"}
            ... )
            >>>
            >>> # 方式2：从.env文件加载指定的环境变量
            >>> github_tool = MCPTool(
            ...     name="github",
            ...     server_command=["npx", "-y", "@modelcontextprotocol/server-github"],
            ...     env_keys=["GITHUB_PERSONAL_ACCESS_TOKEN"]
            ... )
            >>>
            >>> # 方式3：自动检测（最简单，推荐）
            >>> github_tool = MCPTool(
            ...     name="github",
            ...     server_command=["npx", "-y", "@modelcontextprotocol/server-github"]
            ...     # 自动从环境变量加载GITHUB_PERSONAL_ACCESS_TOKEN
            ... )
        """
        self.server_command = server_command
        self.server_args = server_args or []
        self.server = server
        self._client = None
        self._available_tools = []
        self.auto_expand = auto_expand
        self.prefix = f"{name}_" if auto_expand else ""

        # 环境变量处理
        self.env = self._prepare_env(env, env_keys, server_command)

        # 创建内置服务器（如果未指定）
        if not server_command and not server:
            self.server = self._create_builtin_server()

        # 发现工具
        self._discover_tools()

        # 设置描述
        if description is None:
            description = self._generate_description()

        super().__init__(name=name, description=description, expandable=auto_expand)

    def _prepare_env(
        self,
        env: Optional[dict[str, str]],
        env_keys: Optional[list[str]],
        server_command: Optional[list[str]]
    ) -> dict[str, str]:
        """
        准备环境变量

        优先级：env > env_keys > 自动检测

        Args:
            env: 直接传递的环境变量字典
            env_keys: 要从系统环境变量加载的key列表
            server_command: 服务器命令（用于自动检测）

        Returns:
            合并后的环境变量字典
        """
        result_env = {}

        # 1. 自动检测
        if server_command:
            server_name = next(
                (part.split("/")[-1] for part in server_command if "server-" in part),
                None
            )
            if server_name and server_name in MCP_SERVER_ENV_MAP:
                for key in MCP_SERVER_ENV_MAP[server_name]:
                    if value := os.getenv(key):
                        result_env[key] = value
                        print(f"🔑 自动加载环境变量: {key}")

        # 2. env_keys指定
        if env_keys:
            for key in env_keys:
                if value := os.getenv(key):
                    result_env[key] = value
                    print(f"🔑 从env_keys加载环境变量: {key}")
                else:
                    print(f"⚠️  警告: 环境变量 {key} 未设置")

        # 3. 直接传递（优先级最高）
        if env:
            result_env.update(env)
            for key in env.keys():
                print(f"🔑 使用直接传递的环境变量: {key}")

        return result_env

    def _create_builtin_server(self):
        """创建内置演示服务器"""
        try:
            from fastmcp import FastMCP
            server = FastMCP("BuiltinServer")

            @server.tool()
            def add(a: float, b: float) -> float:
                """加法计算器"""
                return a + b

            @server.tool()
            def subtract(a: float, b: float) -> float:
                """减法计算器"""
                return a - b

            @server.tool()
            def multiply(a: float, b: float) -> float:
                """乘法计算器"""
                return a * b

            @server.tool()
            def divide(a: float, b: float) -> float:
                """除法计算器"""
                if b == 0:
                    raise ValueError("除数不能为零")
                return a / b

            @server.tool()
            def greet(name: str = "World") -> str:
                """友好问候"""
                return f"Hello, {name}! 欢迎使用 Agents MCP 工具！"

            return server
        except ImportError:
            raise ImportError("创建内置MCP服务器需要fastmcp库。请安装: pip install fastmcp")

    def _discover_tools(self):
        """发现MCP服务器提供的所有工具"""
        try:
            async def discover():
                client_source = self.server if self.server else self.server_command
                async with MCPClient(client_source, server_args=self.server_args, env=self.env) as client:
                    return await client.list_tools()

            self._available_tools = self._run_async(discover())
        except Exception as e:
            print(f"⚠️  工具发现失败: {e}")
            self._available_tools = []

    def _run_async(self, coro):
        """运行异步操作（处理事件循环）"""
        try:
            loop = asyncio.get_running_loop()
            # 已有循环，在新线程中运行
            def run_in_thread():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(coro)
                finally:
                    new_loop.close()

            with concurrent.futures.ThreadPoolExecutor() as executor:
                return executor.submit(run_in_thread).result()
        except RuntimeError:
            # 没有运行中的循环
            return asyncio.run(coro)

    def _generate_description(self) -> str:
        """生成增强的工具描述"""
        if not self._available_tools:
            return "连接到MCP服务器，调用工具、读取资源和获取提示词。"

        if self.auto_expand:
            return f"MCP工具服务器，包含{len(self._available_tools)}个工具。"
        
        desc_parts = [f"MCP工具服务器，提供{len(self._available_tools)}个工具："]
        for tool in self._available_tools:
            tool_name = tool.get('name', 'unknown')
            tool_desc = tool.get('description', '无描述').split('.')[0]
            desc_parts.append(f"  • {tool_name}: {tool_desc}")
        
        desc_parts.append('\n调用格式：{"action": "call_tool", "tool_name": "工具名", "arguments": {...}}')
        return "\n".join(desc_parts)

    def get_expanded_tools(self) -> list['Tool']:
        """
        获取展开的工具列表

        将MCP服务器的每个工具包装成独立的Tool对象

        Returns:
            Tool对象列表
        """
        if not self.auto_expand:
            return []

        from .mcp_wrapper_tool import MCPWrappedTool
        return [
            MCPWrappedTool(mcp_tool=self, tool_info=tool_info, prefix=self.prefix)
            for tool_info in self._available_tools
        ]

    def run(self, parameters: dict[str, Any]) -> str:
        """
        执行 MCP 操作

        Args:
            parameters: 包含以下参数的字典
                - action: 操作类型 (list_tools, call_tool, list_resources, read_resource)
                  如果不指定action但指定了tool_name，会自动推断为call_tool
                - tool_name: 工具名称（call_tool 需要）
                - arguments: 工具参数（call_tool 需要）
                - uri: 资源 URI（read_resource 需要）

        Returns:
            操作结果
        """
        # 智能推断action
        action = parameters.get("action", "").lower()
        if not action and "tool_name" in parameters:
            action = "call_tool"
            parameters["action"] = action

        if not action:
            return "错误：必须指定action参数或tool_name参数"

        async def run_mcp_operation():
            client_source = self.server if self.server else self.server_command
            async with MCPClient(client_source, server_args=self.server_args, env=self.env) as client:
                if action == "list_tools":
                    tools = await client.list_tools()
                    if not tools:
                        return "没有找到可用的工具"
                    result = f"找到 {len(tools)} 个工具:\n"
                    for tool in tools:
                        result += f"- {tool['name']}: {tool['description']}\n"
                    return result

                elif action == "call_tool":
                    tool_name = parameters.get("tool_name")
                    arguments = parameters.get("arguments", {})
                    if not tool_name:
                        return "错误：必须指定tool_name参数"
                    result = await client.call_tool(tool_name, arguments)
                    return f"工具 '{tool_name}' 执行结果:\n{result}"

                elif action == "list_resources":
                    resources = await client.list_resources()
                    if not resources:
                        return "没有找到可用的资源"
                    result = f"找到 {len(resources)} 个资源:\n"
                    for resource in resources:
                        result += f"- {resource['uri']}: {resource['name']}\n"
                    return result

                elif action == "read_resource":
                    uri = parameters.get("uri")
                    if not uri:
                        return "错误：必须指定uri参数"
                    content = await client.read_resource(uri)
                    return f"资源 '{uri}' 内容:\n{content}"

                else:
                    return f"错误：不支持的操作 '{action}'"

        try:
            return self._run_async(run_mcp_operation())
        except Exception as e:
            return f"MCP操作失败: {e}"

    def get_parameters(self) -> list[ToolParameter]:
        """获取工具参数定义"""
        return [
            ToolParameter(
                name="action",
                type="string",
                description="操作类型: list_tools, call_tool, list_resources, read_resource",
                required=True
            ),
            ToolParameter(
                name="tool_name",
                type="string",
                description="工具名称（call_tool操作需要）",
                required=False
            ),
            ToolParameter(
                name="arguments",
                type="object",
                description="工具参数（call_tool操作需要）",
                required=False
            ),
            ToolParameter(
                name="uri",
                type="string",
                description="资源URI（read_resource操作需要）",
                required=False
            )
        ]
                
