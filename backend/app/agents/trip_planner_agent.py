"""优化后的多智能体旅行规划系统"""

import json
from datetime import datetime, timedelta
from functools import lru_cache
from ..tools.agents.simple_agent import SimpleAgent
from ..tools.mcp.protocol import MCPTool
from ..services.llm_service import get_llm
from ..models.model import TripRequest, TripPlan, DayPlan, Attraction, Meal, Location
from ..config import get_settings

# ============ Agent提示词 ============

ATTRACTION_AGENT_PROMPT = """你是景点搜索专家。你的任务是根据城市和用户偏好搜索合适的景点。

**重要提示:**
你必须使用工具来搜索景点!不要自己编造景点信息!

**工具调用格式:**
使用maps_text_search工具时,必须严格按照以下格式:
`[TOOL_CALL:amap_maps_text_search:keywords=景点关键词,city=城市名]`

**示例:**
用户: "搜索北京的历史文化景点"
你的回复: [TOOL_CALL:amap_maps_text_search:keywords=历史文化,city=北京]

**注意:**
1. 必须使用工具,不要直接回答
2. 格式必须完全正确,包括方括号和冒号
3. 参数用逗号分隔
"""

WEATHER_AGENT_PROMPT = """你是天气查询专家。你的任务是查询指定城市的天气信息。

**重要提示:**
你必须使用工具来查询天气!不要自己编造天气信息!

**工具调用格式:**
使用maps_weather工具时,必须严格按照以下格式:
`[TOOL_CALL:amap_maps_weather:city=城市名]`

**示例:**
用户: "查询北京天气"
你的回复: [TOOL_CALL:amap_maps_weather:city=北京]

**注意:**
1. 必须使用工具,不要直接回答
2. 格式必须完全正确,包括方括号和冒号
"""

HOTEL_AGENT_PROMPT = """你是酒店推荐专家。你的任务是根据城市和景点位置推荐合适的酒店。

**重要提示:**
你必须使用工具来搜索酒店!不要自己编造酒店信息!

**工具调用格式:**
使用maps_text_search工具搜索酒店时,必须严格按照以下格式:
`[TOOL_CALL:amap_maps_text_search:keywords=酒店,city=城市名]`

**示例:**
用户: "搜索北京的酒店"
你的回复: [TOOL_CALL:amap_maps_text_search:keywords=酒店,city=北京]

**注意:**
1. 必须使用工具,不要直接回答
2. 格式必须完全正确,包括方括号和冒号
3. 关键词使用"酒店"或"宾馆"
"""

PLANNER_AGENT_PROMPT = """你是行程规划专家。你的任务是根据景点信息和天气信息,生成详细的旅行计划。

请严格按照以下JSON格式返回旅行计划:
```json
{
  "city": "城市名称",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "days": [
    {
      "date": "YYYY-MM-DD",
      "day_index": 0,
      "description": "第1天行程概述",
      "transportation": "交通方式",
      "accommodation": "住宿类型",
      "hotel": {
        "name": "酒店名称",
        "address": "酒店地址",
        "location": {"longitude": 116.397128, "latitude": 39.916527},
        "price_range": "300-500元",
        "rating": "4.5",
        "distance": "距离景点2公里",
        "type": "经济型酒店",
        "estimated_cost": 400
      },
      "attractions": [
        {
          "name": "景点名称",
          "address": "详细地址",
          "location": {"longitude": 116.397128, "latitude": 39.916527},
          "visit_duration": 120,
          "description": "景点详细描述",
          "category": "景点类别",
          "ticket_price": 60
        }
      ],
      "meals": [
        {"type": "breakfast", "name": "早餐推荐", "description": "早餐描述", "estimated_cost": 30},
        {"type": "lunch", "name": "午餐推荐", "description": "午餐描述", "estimated_cost": 50},
        {"type": "dinner", "name": "晚餐推荐", "description": "晚餐描述", "estimated_cost": 80}
      ]
    }
  ],
  "weather_info": [
    {
      "date": "YYYY-MM-DD",
      "day_weather": "晴",
      "night_weather": "多云",
      "day_temp": 25,
      "night_temp": 15,
      "wind_direction": "南风",
      "wind_power": "1-3级"
    }
  ],
  "overall_suggestions": "总体建议",
  "budget": {
    "total_attractions": 180,
    "total_hotels": 1200,
    "total_meals": 480,
    "total_transportation": 200,
    "total": 2060
  }
}
```

**重要提示:**
1. weather_info数组必须包含每一天的天气信息
2. 温度必须是纯数字(不要带°C等单位)
3. 每天安排2-3个景点
4. 考虑景点之间的距离和游览时间
5. 每天必须包含早中晚三餐
6. 提供实用的旅行建议
7. **必须包含预算信息**
"""


class MultiAgentTripPlanner:
    """多智能体旅行规划系统"""

    def __init__(self):
        """初始化多智能体系统"""
        print("🔄 开始初始化多智能体旅行规划系统...")

        try:
            settings = get_settings()
            self.llm = get_llm()

            # 创建共享的MCP工具
            print("  - 创建共享MCP工具...")
            self.amap_tool = MCPTool(
                name="amap",
                description="高德地图服务",
                server_command=["uvx", "amap-mcp-server"],
                env={"AMAP_MAPS_API_KEY": settings.amap_api_key},
                auto_expand=True
            )

            # 创建各个专家Agent
            self._create_agents()

            print(f"✅ 多智能体系统初始化成功")
            self._print_agent_info()

        except Exception as e:
            print(f"❌ 多智能体系统初始化失败: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _create_agents(self):
        """创建所有Agent"""
        agents_config = [
            ("attraction_agent", "景点搜索专家", ATTRACTION_AGENT_PROMPT, True),
            ("weather_agent", "天气查询专家", WEATHER_AGENT_PROMPT, True),
            ("hotel_agent", "酒店推荐专家", HOTEL_AGENT_PROMPT, True),
            ("planner_agent", "行程规划专家", PLANNER_AGENT_PROMPT, False),
        ]

        for attr_name, name, prompt, needs_tool in agents_config:
            print(f"  - 创建{name}...")
            agent = SimpleAgent(name=name, llm=self.llm, system_prompt=prompt)
            if needs_tool:
                agent.add_tool(self.amap_tool)
            setattr(self, attr_name, agent)

    def _print_agent_info(self):
        """打印Agent信息"""
        for agent_name in ["attraction_agent", "weather_agent", "hotel_agent"]:
            agent = getattr(self, agent_name)
            print(f"   {agent.name}: {len(agent.list_tools())} 个工具")

    def plan_trip(self, request: TripRequest) -> TripPlan:
        """使用多智能体协作生成旅行计划"""
        try:
            self._log_request(request)

            # 多智能体协作
            attraction_response = self._search_attractions(request)
            weather_response = self._query_weather(request)
            hotel_response = self._search_hotels(request)
            planner_response = self._generate_plan(request, attraction_response, weather_response, hotel_response)

            # 解析最终计划
            trip_plan = self._parse_response(planner_response, request)

            print(f"{'='*60}")
            print(f"✅ 旅行计划生成完成!")
            print(f"{'='*60}\n")

            return trip_plan

        except Exception as e:
            print(f"❌ 生成旅行计划失败: {e}")
            import traceback
            traceback.print_exc()
            return self._create_fallback_plan(request)

    def _log_request(self, request: TripRequest):
        """记录请求信息"""
        print(f"\n{'='*60}")
        print(f"🚀 开始多智能体协作规划旅行...")
        print(f"目的地: {request.city}")
        print(f"日期: {request.start_date} 至 {request.end_date}")
        print(f"天数: {request.travel_days}天")
        print(f"偏好: {', '.join(request.preferences) if request.preferences else '无'}")
        print(f"{'='*60}\n")

    def _search_attractions(self, request: TripRequest) -> str:
        """搜索景点"""
        print("📍 步骤1: 搜索景点...")
        keywords = request.preferences[0] if request.preferences else "景点"
        query = f"请使用amap_maps_text_search工具搜索{request.city}的{keywords}相关景点。\n[TOOL_CALL:amap_maps_text_search:keywords={keywords},city={request.city}]"
        response = self.attraction_agent.run(query)
        print(f"景点搜索结果: {response[:500]}...\n")
        return response

    def _query_weather(self, request: TripRequest) -> str:
        """查询天气"""
        print("🌤️  步骤2: 查询天气...")
        query = f"请查询{request.city}的天气信息"
        response = self.weather_agent.run(query)
        print(f"天气查询结果: {response[:200]}...\n")
        return response

    def _search_hotels(self, request: TripRequest) -> str:
        """搜索酒店"""
        print("🏨 步骤3: 搜索酒店...")
        query = f"请搜索{request.city}的{request.accommodation}酒店"
        response = self.hotel_agent.run(query)
        print(f"酒店搜索结果: {response[:200]}...\n")
        return response

    def _generate_plan(self, request: TripRequest, attractions: str, weather: str, hotels: str) -> str:
        """生成行程计划"""
        print("📋 步骤4: 生成行程计划...")
        query = f"""请根据以下信息生成{request.city}的{request.travel_days}天旅行计划:

**基本信息:**
- 城市: {request.city}
- 日期: {request.start_date} 至 {request.end_date}
- 天数: {request.travel_days}天
- 交通方式: {request.transportation}
- 住宿: {request.accommodation}
- 偏好: {', '.join(request.preferences) if request.preferences else '无'}

**景点信息:**
{attractions}

**天气信息:**
{weather}

**酒店信息:**
{hotels}

**要求:**
1. 每天安排2-3个景点
2. 每天必须包含早中晚三餐
3. 每天推荐一个具体的酒店(从酒店信息中选择)
4. 考虑景点之间的距离和交通方式
5. 返回完整的JSON格式数据
6. 景点的经纬度坐标要真实准确
"""
        if request.free_text_input:
            query += f"\n**额外要求:** {request.free_text_input}"

        response = self.planner_agent.run(query)
        print(f"行程规划结果: {response}...\n")
        return response

    def _parse_response(self, response: str, request: TripRequest) -> TripPlan:
        """解析Agent响应"""
        try:
            # 提取JSON
            json_str = self._extract_json(response)
            data = json.loads(json_str)
            return TripPlan(**data)
        except Exception as e:
            print(f"⚠️  解析响应失败: {e}")
            print(f"   将使用备用方案生成计划")
            return self._create_fallback_plan(request)

    def _extract_json(self, response: str) -> str:
        """从响应中提取JSON字符串"""
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            return response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            return response[start:end].strip()
        elif "{" in response and "}" in response:
            start = response.find("{")
            end = response.rfind("}") + 1
            return response[start:end]
        else:
            raise ValueError("响应中未找到JSON数据")

    def _create_fallback_plan(self, request: TripRequest) -> TripPlan:
        """创建备用计划（当Agent失败时）"""
        start_date = datetime.strptime(request.start_date, "%Y-%m-%d")

        days = [
            DayPlan(
                date=(start_date + timedelta(days=i)).strftime("%Y-%m-%d"),
                day_index=i,
                description=f"第{i+1}天行程",
                transportation=request.transportation,
                accommodation=request.accommodation,
                attractions=[
                    Attraction(
                        name=f"{request.city}景点{j+1}",
                        address=f"{request.city}市",
                        location=Location(
                            longitude=116.4 + i*0.01 + j*0.005,
                            latitude=39.9 + i*0.01 + j*0.005
                        ),
                        visit_duration=120,
                        description=f"这是{request.city}的著名景点",
                        category="景点"
                    )
                    for j in range(2)
                ],
                meals=[
                    Meal(type="breakfast", name=f"第{i+1}天早餐", description="当地特色早餐"),
                    Meal(type="lunch", name=f"第{i+1}天午餐", description="午餐推荐"),
                    Meal(type="dinner", name=f"第{i+1}天晚餐", description="晚餐推荐")
                ]
            )
            for i in range(request.travel_days)
        ]

        return TripPlan(
            city=request.city,
            start_date=request.start_date,
            end_date=request.end_date,
            days=days,
            weather_info=[],
            overall_suggestions=f"这是为您规划的{request.city}{request.travel_days}日游行程,建议提前查看各景点的开放时间。"
        )


@lru_cache
def get_trip_planner_agent() -> MultiAgentTripPlanner:
    """获取多智能体旅行规划系统实例（单例模式）"""
    return MultiAgentTripPlanner()
