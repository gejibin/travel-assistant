"""优化后的地图服务API路由"""

from fastapi import APIRouter, HTTPException, Query
from ...models.model import (
    POISearchResponse,
    RouteRequest,
    RouteResponse,
    WeatherResponse
)
from ...services.amap_service import get_amap_service

router = APIRouter(prefix="/map", tags=["地图服务"])


def handle_error(operation: str, error: Exception):
    """统一错误处理"""
    error_msg = f"{operation}失败: {error}"
    print(f"❌ {error_msg}")
    raise HTTPException(status_code=500, detail=error_msg)


@router.get("/poi", response_model=POISearchResponse, summary="搜索POI")
async def search_poi(
    keywords: str = Query(..., description="搜索关键词"),
    city: str = Query(..., description="城市"),
    citylimit: bool = Query(True, description="是否限制在城市范围内")
):
    """根据关键词搜索POI（兴趣点）"""
    try:
        pois = get_amap_service().search_poi(keywords, city, citylimit)
        return POISearchResponse(success=True, message="POI搜索成功", data=pois)
    except Exception as e:
        handle_error("POI搜索", e)


@router.get("/weather", response_model=WeatherResponse, summary="查询天气")
async def get_weather(city: str = Query(..., description="城市名称")):
    """查询指定城市的天气信息"""
    try:
        weather_info = get_amap_service().get_weather(city)
        return WeatherResponse(success=True, message="天气查询成功", data=weather_info)
    except Exception as e:
        handle_error("天气查询", e)


@router.post("/route", response_model=RouteResponse, summary="规划路线")
async def plan_route(request: RouteRequest):
    """规划两点之间的路线"""
    try:
        route_info = get_amap_service().plan_route(
            origin_address=request.origin_address,
            destination_address=request.destination_address,
            origin_city=request.origin_city,
            destination_city=request.destination_city,
            route_type=request.route_type
        )
        return RouteResponse(success=True, message="路线规划成功", data=route_info)
    except Exception as e:
        handle_error("路线规划", e)


@router.get("/health", summary="健康检查")
async def health_check():
    """检查地图服务是否正常"""
    try:
        service = get_amap_service()
        return {
            "status": "healthy",
            "service": "map-service",
            "mcp_tools_count": len(service.mcp_tool._available_tools)
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"服务不可用: {e}")
