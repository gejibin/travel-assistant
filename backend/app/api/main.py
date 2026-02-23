"""优化的FastAPI主应用"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ..config import get_settings, validate_config, print_config
from .routes import trip, poi, map as map_routes

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动
    print(f"\n{'='*50}")
    print(f"🚀 {settings.app_name} v{settings.app_version}")
    print(f"{'='*50}")
    
    print_config()
    
    try:
        validate_config()
        print("\n✅ 配置验证通过")
    except ValueError as e:
        print(f"\n❌ 配置验证失败: {e}")
        raise
    
    print(f"\n📚 文档: http://localhost:{settings.port}/docs")
    print(f"{'='*50}\n")
    
    yield
    
    # 关闭
    print(f"\n{'='*50}")
    print("👋 应用关闭")
    print(f"{'='*50}\n")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="基于HelloAgents框架的智能旅行规划助手API",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
for router in [trip.router, poi.router, map_routes.router]:
    app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running"
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.api.main_new:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )