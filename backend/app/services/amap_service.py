"""优化后的高德地图MCP服务封装"""

from typing import Optional
from functools import lru_cache
from ..tools.mcp.protocol import MCPTool
from ..config import get_settings
from ..models.model import Location, POIInfo, WeatherInfo


@lru_cache
def get_amap_mcp_tool() -> MCPTool:
    """获取高德地图MCP工具实例（单例模式）"""
    settings = get_settings()
    
    if not settings.amap_api_key:
        raise ValueError("高德地图API Key未配置，请在.env文件中设置AMAP_API_KEY")
    
    tool = MCPTool(
        name="amap",
        description="高德地图服务，支持POI搜索、路线规划、天气查询等功能",
        server_command=["uvx", "amap-mcp-server"],
        env={"AMAP_MAPS_API_KEY": settings.amap_api_key},
        auto_expand=True
    )
    
    print(f"✅ 高德地图MCP工具初始化成功")
    print(f"   工具数量: {len(tool._available_tools)}")
    
    if tool._available_tools:
        print("   可用工具:")
        for t in tool._available_tools[:5]:
            print(f"     - {t.get('name', 'unknown')}")
        if len(tool._available_tools) > 5:
            print(f"     ... 还有 {len(tool._available_tools) - 5} 个工具")
    
    return tool


class AmapService:
    """高德地图服务封装类"""
    
    def __init__(self):
        self.mcp_tool = get_amap_mcp_tool()
    
    def _call_tool(self, tool_name: str, arguments: dict) -> str:
        """调用MCP工具的通用方法"""
        try:
            return self.mcp_tool.run({
                "action": "call_tool",
                "tool_name": tool_name,
                "arguments": arguments
            })
        except Exception as e:
            print(f"❌ {tool_name} 调用失败: {e}")
            raise
    
    def search_poi(self, keywords: str, city: str, citylimit: bool = True) -> list[POIInfo]:
        """搜索POI"""
        try:
            result = self._call_tool("maps_text_search", {
                "keywords": keywords,
                "city": city,
                "citylimit": str(citylimit).lower()
            })
            print(f"POI搜索结果: {result[:200]}...")
            # TODO: 解析实际的POI数据
            return []
        except Exception as e:
            print(f"❌ POI搜索失败: {e}")
            return []
    
    def get_weather(self, city: str) -> list[WeatherInfo]:
        """查询天气"""
        try:
            result = self._call_tool("maps_weather", {"city": city})
            print(f"天气查询结果: {result[:200]}...")
            # TODO: 解析实际的天气数据
            return []
        except Exception as e:
            print(f"❌ 天气查询失败: {e}")
            return []
    
    def plan_route(
        self,
        origin_address: str,
        destination_address: str,
        origin_city: Optional[str] = None,
        destination_city: Optional[str] = None,
        route_type: str = "walking"
    ) -> dict:
        """规划路线"""
        tool_map = {
            "walking": "maps_direction_walking_by_address",
            "driving": "maps_direction_driving_by_address",
            "transit": "maps_direction_transit_integrated_by_address"
        }
        
        tool_name = tool_map.get(route_type, "maps_direction_walking_by_address")
        
        arguments = {
            "origin_address": origin_address,
            "destination_address": destination_address
        }
        
        if origin_city:
            arguments["origin_city"] = origin_city
        if destination_city:
            arguments["destination_city"] = destination_city
        
        try:
            result = self._call_tool(tool_name, arguments)
            print(f"路线规划结果: {result[:200]}...")
            # TODO: 解析实际的路线数据
            return {}
        except Exception as e:
            print(f"❌ 路线规划失败: {e}")
            return {}
    
    def geocode(self, address: str, city: Optional[str] = None) -> Optional[Location]:
        """地理编码（地址转坐标）"""
        arguments = {"address": address}
        if city:
            arguments["city"] = city
        
        try:
            result = self._call_tool("maps_geo", arguments)
            print(f"地理编码结果: {result[:200]}...")
            # TODO: 解析实际的坐标数据
            return None
        except Exception as e:
            print(f"❌ 地理编码失败: {e}")
            return None
    
    def get_poi_detail(self, poi_id: str) -> dict:
        """获取POI详情"""
        try:
            result = self._call_tool("maps_search_detail", {"id": poi_id})
            print(f"POI详情结果: {result[:200]}...")
            
            import json
            import re
            
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            return {"raw": result}
        except Exception as e:
            print(f"❌ 获取POI详情失败: {e}")
            return {}


@lru_cache
def get_amap_service() -> AmapService:
    """获取高德地图服务实例（单例模式）"""
    return AmapService()
