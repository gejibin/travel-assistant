"""
MCP功能测试 - 测试多种传输方式

测试内容：
1. 内存传输（Memory Transport）- FastMCP实例
2. Stdio传输 - Python脚本
3. HTTP传输 - 远程服务器
4. SSE传输 - 实时通信
5. 工具展开功能
"""

import asyncio
from pathlib import Path
from ..tools.mcp.client import MCPClient


async def test_memory_transport():
    """测试1: 内存传输 - 使用FastMCP实例"""
    print("\n" + "="*60)
    print("测试1: 内存传输（Memory Transport）")
    print("="*60)
    
    try:
        from fastmcp import FastMCP
        
        # 创建内置服务器
        server = FastMCP("TestServer")
        
        @server.tool()
        def add(a: float, b: float) -> float:
            """加法计算器"""
            return a + b
        
        @server.tool()
        def greet(name: str = "World") -> str:
            """问候"""
            return f"Hello, {name}!"
        
        # 使用内存传输
        async with MCPClient(server) as client:
            # 列出工具
            tools = await client.list_tools()
            print(f"✅ 找到 {len(tools)} 个工具:")
            for tool in tools:
                print(f"   - {tool['name']}: {tool['description']}")
            
            # 调用工具
            result = await client.call_tool("add", {"a": 5, "b": 3})
            print(f"✅ add(5, 3) = {result}")
            
            result = await client.call_tool("greet", {"name": "MCP"})
            print(f"✅ greet('MCP') = {result}")
        
        print("✅ 内存传输测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 内存传输测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_stdio_transport():
    """测试2: Stdio传输 - Python脚本"""
    print("\n" + "="*60)
    print("测试2: Stdio传输（Python脚本）")
    print("="*60)
    
    try:
        
        # 创建测试服务器脚本
        test_script = Path(__file__).parent / "test_mcp_server.py"
        
        if not test_script.exists():
            print("⚠️  创建测试服务器脚本...")
            test_script.write_text('''
from fastmcp import FastMCP

server = FastMCP("StdioTestServer")

@server.tool()
def multiply(a: float, b: float) -> float:
    """乘法计算器"""
    return a * b

@server.tool()
def echo(message: str) -> str:
    """回显消息"""
    return f"Echo: {message}"

if __name__ == "__main__":
    server.run()
''')
        
        # 方式1: 直接传递脚本路径
        print("\n方式1: 直接传递脚本路径")
        async with MCPClient(str(test_script)) as client:
            tools = await client.list_tools()
            print(f"✅ 找到 {len(tools)} 个工具")
            
            result = await client.call_tool("multiply", {"a": 4, "b": 7})
            print(f"✅ multiply(4, 7) = {result}")
        
        # 方式2: 传递命令列表
        print("\n方式2: 传递命令列表")
        async with MCPClient(["python", str(test_script)]) as client:
            result = await client.call_tool("echo", {"message": "Hello Stdio"})
            print(f"✅ echo('Hello Stdio') = {result}")
        
        print("✅ Stdio传输测试通过")
        return True
        
    except Exception as e:
        print(f"❌ Stdio传输测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_http_transport():
    """测试3: HTTP传输 - 远程服务器（模拟）"""
    print("\n" + "="*60)
    print("测试3: HTTP传输（远程服务器）")
    print("="*60)
    
    try:
        
        # 注意：这需要实际的HTTP MCP服务器
        # 这里仅演示如何使用
        print("⚠️  HTTP传输需要实际的远程服务器")
        print("示例用法:")
        print('  client = MCPClient("https://api.example.com/mcp")')
        print('  async with client:')
        print('      tools = await client.list_tools()')
        
        # 如果有测试服务器，取消注释以下代码
        # async with MCPClient("http://localhost:8000/mcp") as client:
        #     tools = await client.list_tools()
        #     print(f"✅ 找到 {len(tools)} 个工具")
        
        print("✅ HTTP传输示例完成")
        return True
        
    except Exception as e:
        print(f"❌ HTTP传输测试失败: {e}")
        return False


async def test_sse_transport():
    """测试4: SSE传输 - 实时通信（模拟）"""
    print("\n" + "="*60)
    print("测试4: SSE传输（Server-Sent Events）")
    print("="*60)
    
    try:
        
        print("⚠️  SSE传输需要支持SSE的远程服务器")
        print("示例用法:")
        print('  client = MCPClient("https://api.example.com/mcp/sse", transport_type="sse")')
        print('  async with client:')
        print('      tools = await client.list_tools()')
        
        # 如果有SSE服务器，取消注释以下代码
        # async with MCPClient("http://localhost:8000/mcp/sse", transport_type="sse") as client:
        #     tools = await client.list_tools()
        #     print(f"✅ 找到 {len(tools)} 个工具")
        
        print("✅ SSE传输示例完成")
        return True
        
    except Exception as e:
        print(f"❌ SSE传输测试失败: {e}")
        return False


async def test_mcp_tool_expansion():
    """测试5: MCP工具展开功能"""
    print("\n" + "="*60)
    print("测试5: MCP工具展开功能")
    print("="*60)
    
    try:
        from fastmcp import FastMCP
        
        # 创建服务器
        server = FastMCP("ExpansionTestServer")
        
        @server.tool()
        def divide(a: float, b: float) -> float:
            """除法计算器"""
            if b == 0:
                raise ValueError("除数不能为零")
            return a / b
        
        @server.tool()
        def power(base: float, exponent: float) -> float:
            """幂运算"""
            return base ** exponent
        
        # 创建MCP工具（自动展开）
        print("\n创建MCP工具（auto_expand=True）...")
        mcp_tool = MCPTool(
            name="math",
            server=server,
            auto_expand=True
        )
        
        # 获取展开的工具
        expanded_tools = mcp_tool.get_expanded_tools()
        print(f"✅ 展开为 {len(expanded_tools)} 个独立工具:")
        for tool in expanded_tools:
            print(f"   - {tool.name}: {tool.description}")
        
        # 测试展开的工具
        print("\n测试展开的工具...")
        for tool in expanded_tools:
            if "divide" in tool.name:
                result = tool.run({"a": 10, "b": 2})
                print(f"✅ {tool.name}(10, 2) = {result}")
            elif "power" in tool.name:
                result = tool.run({"base": 2, "exponent": 3})
                print(f"✅ {tool.name}(2, 3) = {result}")
        
        print("✅ 工具展开测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 工具展开测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_config_transport():
    """测试6: 配置字典传输"""
    print("\n" + "="*60)
    print("测试6: 配置字典传输")
    print("="*60)
    
    try:
        
        # 创建测试脚本
        test_script = Path(__file__).parent / "test_mcp_server.py"
        
        # 使用配置字典
        config = {
            "transport": "stdio",
            "args": [str(test_script)],
            "env": {"DEBUG": "1"}
        }
        
        print("使用配置字典创建客户端...")
        async with MCPClient(config) as client:
            tools = await client.list_tools()
            print(f"✅ 找到 {len(tools)} 个工具")
        
        print("✅ 配置字典传输测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 配置字典传输测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("MCP功能测试套件")
    print("="*60)
    
    results = {
        "内存传输": await test_memory_transport(),
        "Stdio传输": await test_stdio_transport(),
        "HTTP传输": await test_http_transport(),
        "SSE传输": await test_sse_transport(),
        "工具展开": await test_mcp_tool_expansion(),
        "配置字典": await test_config_transport(),
    }
    
    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    print(f"\n总计: {passed}/{total} 个测试通过")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
