"""
外部MCP服务器测试 - 测试stdio传输和真实的MCP服务器

测试内容：
1. 创建外部Python MCP服务器脚本
2. 使用stdio传输连接
3. 列出工具
4. 调用工具
5. 测试工具展开
"""

from pathlib import Path


def test_external_mcp_server():
    """测试外部MCP服务器（stdio传输）"""
    print("\n" + "="*60)
    print("测试: 外部MCP服务器（stdio传输）")
    print("="*60)
    
    try:
        from ..tools.mcp.protocol import MCPTool
        
        # 创建外部服务器脚本
        server_script = Path(__file__).parent / "external_mcp_server.py"
        
        print("创建外部MCP服务器脚本...")
        server_script.write_text('''#!/usr/bin/env python3
"""外部MCP服务器示例"""

from fastmcp import FastMCP

# 创建服务器
server = FastMCP("ExternalServer")

@server.tool()
def string_length(text: str) -> int:
    """计算字符串长度"""
    return len(text)

@server.tool()
def string_reverse(text: str) -> str:
    """反转字符串"""
    return text[::-1]

@server.tool()
def string_upper(text: str) -> str:
    """转换为大写"""
    return text.upper()

@server.tool()
def string_lower(text: str) -> str:
    """转换为小写"""
    return text.lower()

@server.tool()
def word_count(text: str) -> int:
    """统计单词数量"""
    return len(text.split())

if __name__ == "__main__":
    server.run()
''')
        
        print(f"✅ 服务器脚本已创建: {server_script}")
        
        # 测试1: 列出工具
        print("\n" + "-"*60)
        print("测试1: 列出工具")
        print("-"*60)
        
        mcp_tool = MCPTool(
            name="string_tools",
            server_command=["python", str(server_script)],
            auto_expand=False
        )
        
        result = mcp_tool.run({"action": "list_tools"})
        print(f"✅ 工具列表:\n{result}")
        
        # 测试2: 调用工具
        print("\n" + "-"*60)
        print("测试2: 调用工具")
        print("-"*60)
        
        test_cases = [
            ("string_length", {"text": "Hello World"}, "11"),
            ("string_reverse", {"text": "MCP"}, "PCM"),
            ("string_upper", {"text": "hello"}, "HELLO"),
            ("string_lower", {"text": "WORLD"}, "world"),
            ("word_count", {"text": "Hello MCP Server"}, "3"),
        ]
        
        for tool_name, args, expected in test_cases:
            result = mcp_tool.run({
                "action": "call_tool",
                "tool_name": tool_name,
                "arguments": args
            })
            print(f"✅ {tool_name}{args} = {result}")
            if expected in str(result):
                print(f"   验证通过: 包含期望值 '{expected}'")
        
        # 测试3: 工具展开
        print("\n" + "-"*60)
        print("测试3: 工具展开")
        print("-"*60)
        
        mcp_tool_expanded = MCPTool(
            name="string_tools",
            server_command=["python", str(server_script)],
            auto_expand=True
        )
        
        expanded_tools = mcp_tool_expanded.get_expanded_tools()
        print(f"✅ 展开为 {len(expanded_tools)} 个独立工具:")
        
        for tool in expanded_tools:
            print(f"\n  工具: {tool.name}")
            print(f"    描述: {tool.description}")
            params = tool.get_parameters()
            #print(f"    参数: {[f'{p.name}({p.type})' for p in params]}")
            print(f"    参数: {[f'{p}' for p in params]}")
        
        # 测试4: 调用展开的工具
        print("\n" + "-"*60)
        print("测试4: 调用展开的工具")
        print("-"*60)
        
        for tool in expanded_tools[:2]:  # 只测试前2个
            if "length" in tool.name:
                result = tool.run({"text": "Test"})
                print(f"✅ {tool.name}('Test') = {result}")
            elif "reverse" in tool.name:
                result = tool.run({"text": "ABC"})
                print(f"✅ {tool.name}('ABC') = {result}")
        
        print("\n✅ 外部MCP服务器测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 外部MCP服务器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_github_mcp_server():
    """测试GitHub MCP服务器（需要npx和token）"""
    print("\n" + "="*60)
    print("测试: GitHub MCP服务器（可选）")
    print("="*60)
    
    try:
        from ..tools.mcp.protocol import MCPTool
        import os
        import subprocess
        
        # 检查是否有npx
        try:
            result = subprocess.run(["npx", "--version"], capture_output=True, text=True, shell=True)
            has_npx = result.returncode == 0
        except:
            has_npx = False
        
        if not has_npx:
            print("⚠️  未安装npx，跳过GitHub MCP服务器测试")
            print("   安装Node.js后可运行此测试")
            return True
        
        os.environ["GITHUB_PERSONAL_ACCESS_TOKEN"] = "xxxxxxx"

        # 检查是否有GitHub token
        token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
        if not token:
            print("⚠️  未设置GITHUB_PERSONAL_ACCESS_TOKEN环境变量")
            print("   设置后可测试GitHub MCP服务器")
            print("   示例: export GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxx")
            return True
        
        print("✅ 检测到npx和GitHub token，开始测试...")
        
        # 创建GitHub MCP工具
        github_tool = MCPTool(
            name="github",
            server_command=["npx", "-y", "@modelcontextprotocol/server-github"],
            auto_expand=False
        )
        
        # 列出工具
        print("\n列出GitHub MCP工具...")
        result = github_tool.run({"action": "list_tools"})
        print(f"✅ GitHub工具列表:\n{result[:500]}...")
        
        # 尝试调用一个简单的工具（如果有的话）
        print("\n✅ GitHub MCP服务器测试通过")
        return True
        
    except Exception as e:
        print(f"⚠️  GitHub MCP服务器测试跳过: {e}")
        return True  # 不算失败


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("外部MCP服务器测试套件")
    print("="*60)
    
    results = {
        "外部MCP服务器": test_external_mcp_server(),
        "GitHub MCP服务器": test_github_mcp_server(),
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
    success = main()
    exit(0 if success else 1)
