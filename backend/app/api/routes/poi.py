"""优化后的POI相关API路由"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ...services.amap_service import get_amap_service
from ...services.unsplash_service import get_unsplash_service
from ...services.pexels_service import get_pexels_service
from ...tools.utils.chinese_to_english_translator import translate_chinese_to_english

router = APIRouter(prefix="/poi", tags=["POI"])


class POIDetailResponse(BaseModel):
    """POI详情响应"""
    success: bool
    message: str
    data: dict | None = None


def handle_error(operation: str, error: Exception):
    """统一错误处理"""
    error_msg = f"{operation}失败: {error}"
    print(f"❌ {error_msg}")
    raise HTTPException(status_code=500, detail=error_msg)


@router.get("/detail/{poi_id}", response_model=POIDetailResponse, summary="获取POI详情")
async def get_poi_detail(poi_id: str):
    """根据POI ID获取详细信息，包括图片"""
    try:
        result = get_amap_service().get_poi_detail(poi_id)
        return POIDetailResponse(success=True, message="获取POI详情成功", data=result)
    except Exception as e:
        handle_error("获取POI详情", e)


@router.get("/search", summary="搜索POI")
async def search_poi(keywords: str, city: str = "北京"):
    """根据关键词搜索POI"""
    try:
        result = get_amap_service().search_poi(keywords, city)
        return {"success": True, "message": "搜索成功", "data": result}
    except Exception as e:
        handle_error("搜索POI", e)


@router.get("/photo", summary="获取景点图片")
async def get_attraction_photo(name: str, city: str = ""):
    """根据景点名称从Pexels获取图片，可指定城市"""
    try:
        pexels = get_pexels_service()
        
        # 将中文景点名称和城市翻译为英文
        english_name = translate_chinese_to_english(name)
        english_city = translate_chinese_to_english(city) if city else ""
        
        print(f"🔍 搜索图片: {name} (翻译为: {english_name})")
        if city:
            print(f"🏙️  城市: {city} (翻译为: {english_city})")
        
        # 构建搜索查询，优先使用翻译后的英文
        search_queries = []
        
        if english_city:
            # 按优先级构建搜索查询 - 英文优先
            search_queries.extend([
                f"{english_name} {english_city} China landmark",  # 最具体: 英文景点+英文城市+国家
                f"{name} {city} China landmark",                 # 中文景点+中文城市+国家
                f"{english_name} {english_city} China",          # 英文景点+英文城市
                f"{name} {city} China",                          # 中文景点+中文城市
                f"{english_name} {english_city}",                # 英文景点+英文城市（无国家限制）
                f"{english_city} {english_name} China",          # 英文城市+英文景点+国家
                f"{english_name} China",                         # 英文景点+国家
                f"{name} China",                                 # 中文景点+国家
                f"{english_name} landmark",                      # 英文景点+地标
                f"{name} landmark",                              # 中文景点+地标
                f"{english_name}",                               # 仅英文景点名称
                f"{name}"                                        # 仅中文景点名称
            ])
        else:
            # 仅使用景点名称的搜索 - 英文优先
            search_queries.extend([
                f"{english_name} China landmark",
                f"{name} China landmark",
                f"{english_name} China",
                f"{name} China",
                f"{english_name} landmark",
                f"{name} landmark",
                f"{english_name}"
            ])
        
        # 按优先级尝试搜索
        photo_url = None
        for query in search_queries:
            print(f"🔍 尝试搜索: {query}")
            photo_url = pexels.get_photo_url(query)
            if photo_url:
                print(f"✅ 找到图片: {query}")
                break
        
        return {
            "success": True,
            "message": "获取图片成功" if photo_url else "未找到匹配的图片",
            "data": {
                "name": name, 
                "english_name": english_name,
                "city": city, 
                "english_city": english_city,
                "photo_url": photo_url
            }
        }
    except Exception as e:
        handle_error("获取景点图片", e)