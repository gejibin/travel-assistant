"""优化后的旅行规划API路由"""

from fastapi import APIRouter, HTTPException
from ...models.model import TripRequest, TripPlanResponse
from ...agents.trip_planner_agent import get_trip_planner_agent

router = APIRouter(prefix="/trip", tags=["旅行规划"])


def log_request(request: TripRequest):
    """记录请求信息"""
    print(f"\n{'='*60}")
    print(f"📥 收到旅行规划请求:")
    print(f"   城市: {request.city}")
    print(f"   日期: {request.start_date} - {request.end_date}")
    print(f"   天数: {request.travel_days}")
    print(f"{'='*60}\n")


@router.post("/plan", response_model=TripPlanResponse, summary="生成旅行计划")
async def plan_trip(request: TripRequest):
    """根据用户输入的旅行需求，生成详细的旅行计划"""
    try:
        log_request(request)
        
        print("🔄 获取多智能体系统实例...")
        agent = get_trip_planner_agent()
        
        print("🚀 开始生成旅行计划...")
        trip_plan = agent.plan_trip(request)
        
        print("✅ 旅行计划生成成功，准备返回响应\n")
        
        return TripPlanResponse(
            success=True,
            message="旅行计划生成成功",
            data=trip_plan
        )
    except Exception as e:
        print(f"❌ 生成旅行计划失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"生成旅行计划失败: {e}")


@router.get("/health", summary="健康检查")
async def health_check():
    """检查旅行规划服务是否正常"""
    try:
        agent = get_trip_planner_agent()
        return {
            "status": "healthy",
            "service": "trip-planner",
            "agent_name": agent.agent.name,
            "tools_count": len(agent.agent.list_tools())
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"服务不可用: {e}")
