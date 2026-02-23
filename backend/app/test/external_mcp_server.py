#!/usr/bin/env python3
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
