"""优化后的数据模型定义"""

from typing import Generic, TypeVar, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import date


# ============ 基础模型 ============

T = TypeVar('T')


class BaseResponse(BaseModel, Generic[T]):
    """统一响应基类"""
    success: bool
    message: str = ""
    data: Optional[T] = None


class Location(BaseModel):
    """地理位置"""
    longitude: float
    latitude: float


# ============ 请求模型 ============

class TripRequest(BaseModel):
    """旅行规划请求"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "city": "北京",
            "start_date": "2025-06-01",
            "end_date": "2025-06-03",
            "travel_days": 3,
            "transportation": "公共交通",
            "accommodation": "经济型酒店",
            "preferences": ["历史文化", "美食"],
            "free_text_input": "希望多安排一些博物馆"
        }
    })
    
    city: str = Field(description="目的地城市")
    start_date: str = Field(description="开始日期 YYYY-MM-DD")
    end_date: str = Field(description="结束日期 YYYY-MM-DD")
    travel_days: int = Field(ge=1, le=30, description="旅行天数")
    transportation: str = Field(description="交通方式")
    accommodation: str = Field(description="住宿偏好")
    preferences: list[str] = Field(default_factory=list, description="旅行偏好标签")
    free_text_input: str = Field(default="", description="额外要求")


class POISearchRequest(BaseModel):
    """POI搜索请求"""
    keywords: str = Field(description="搜索关键词")
    city: str = Field(description="城市")
    citylimit: bool = Field(default=True, description="是否限制在城市范围内")


class RouteRequest(BaseModel):
    """路线规划请求"""
    origin_address: str = Field(description="起点地址")
    destination_address: str = Field(description="终点地址")
    origin_city: Optional[str] = None
    destination_city: Optional[str] = None
    route_type: str = Field(default="walking", description="路线类型: walking/driving/transit")


# ============ 业务模型 ============

class Attraction(BaseModel):
    """景点信息"""
    name: str
    address: str
    location: Location
    visit_duration: int = Field(description="建议游览时间(分钟)")
    description: str
    category: str = "景点"
    rating: Optional[float] = Field(default=None, description="景点评分")
    photos: list[str] = Field(default_factory=list)
    poi_id: str = ""
    image_url: Optional[str] = None
    ticket_price: int = 0


class Meal(BaseModel):
    """餐饮信息"""
    type: str = Field(description="餐饮类型: breakfast/lunch/dinner/snack")
    name: str
    address: Optional[str] = None
    location: Optional[Location] = None
    description: Optional[str] = None
    estimated_cost: int = 0


class Hotel(BaseModel):
    """酒店信息"""
    name: str
    address: str = ""
    location: Optional[Location] = None
    price_range: str = ""
    rating: str = ""
    distance: str = ""
    type: str = ""
    estimated_cost: int = 0


class WeatherInfo(BaseModel):
    """天气信息"""
    date: str
    day_weather: str = ""
    night_weather: str = ""
    day_temp: int | str = 0
    night_temp: int | str = 0
    wind_direction: str = ""
    wind_power: str = ""

    @field_validator('day_temp', 'night_temp', mode='before')
    @classmethod
    def parse_temperature(cls, v):
        """解析温度，移除单位符号"""
        if isinstance(v, str):
            v = v.replace('°C', '').replace('℃', '').replace('°', '').strip()
            try:
                return int(v)
            except ValueError:
                return 0
        return v


class Budget(BaseModel):
    """预算信息"""
    total_attractions: int = 0
    total_hotels: int = 0
    total_meals: int = 0
    total_transportation: int = 0
    total: int = 0


class DayPlan(BaseModel):
    """单日行程"""
    date: str
    day_index: int
    description: str
    transportation: str
    accommodation: str = Field(description="住宿安排")
    hotel: Optional[Hotel] = Field(default=None, description="推荐酒店")
    attractions: list[Attraction] = Field(default_factory=list, description="景点列表")
    meals: list[Meal] = Field(default_factory=list, description="餐饮列表")


class TripPlan(BaseModel):
    """旅行计划"""
    city: str
    start_date: str
    end_date: str
    days: list[DayPlan]
    weather_info: list[WeatherInfo] = Field(default_factory=list)
    overall_suggestions: str
    budget: Optional[Budget] = None


class POIInfo(BaseModel):
    """POI信息"""
    id: str = Field(description="POI ID")
    name: str = Field(description="名称")
    type: str = Field(description="类型")
    address: str = Field(description="地址")
    location: Location = Field(description="经纬度坐标")
    tel: Optional[str] = Field(default=None, description="电话")


class RouteInfo(BaseModel):
    """路线信息"""
    distance: float = Field(description="距离(米)")
    duration: int = Field(description="时间(秒)")
    route_type: str
    description: str


# ============ 响应模型 ============

class TripPlanResponse(BaseResponse[TripPlan]):
    """旅行计划响应"""
    pass


class POISearchResponse(BaseResponse[list[POIInfo]]):
    """POI搜索响应"""
    pdata: list[POIInfo] = Field(default=[], description="POI列表")


class RouteResponse(BaseResponse[RouteInfo]):
    """路线规划响应"""
    pass


class WeatherResponse(BaseResponse[list[WeatherInfo]]):
    """天气查询响应"""
    data: list[WeatherInfo] = Field(default_factory=list, description="天气信息")


class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = False
    message: str
    error_code: Optional[str] = None
