"""优化后的配置管理模块"""

import os
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv


def load_env_files():
    """加载环境变量文件"""
    load_dotenv()  # 加载当前目录的.env


load_env_files()

print(os.getenv("CORS_ORIGINS"))


class Settings(BaseSettings):
    """应用配置"""
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )

    # 应用配置
    app_name: str = "智能旅行助手"
    app_version: str = "1.0.0"
    debug: bool = False

    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS配置
    cors_origins: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"

    # API配置
    amap_api_key: str = ""
    unsplash_access_key: str = ""
    unsplash_secret_key: str = ""

    pexels_api_key: str = ""

    # 翻译API配置
    baidu_trans_app_id: str = ""
    baidu_trans_secret_key: str = ""

    # LLM配置
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4"

    # 日志配置
    log_level: str = "INFO"

    @property
    def cors_origins_list(self) -> list[str]:
        """获取CORS origins列表"""
        return [origin.strip() for origin in self.cors_origins.split(',')]

    @property
    def llm_api_key(self) -> str:
        """获取LLM API Key"""
        return os.getenv("LLM_API_KEY") or self.openai_api_key

    @property
    def llm_base_url(self) -> str:
        """获取LLM Base URL"""
        return os.getenv("LLM_BASE_URL") or self.openai_base_url

    @property
    def llm_model(self) -> str:
        """获取LLM Model"""
        return os.getenv("LLM_MODEL_ID") or self.openai_model

    def validate(self) -> bool:
        """验证配置完整性"""
        errors = []
        warnings = []

        if not self.amap_api_key:
            errors.append("AMAP_API_KEY未配置")

        if not self.llm_api_key:
            warnings.append("LLM_API_KEY或OPENAI_API_KEY未配置，LLM功能可能无法使用")

        if errors:
            raise ValueError("配置错误:\n" + "\n".join(f"  - {e}" for e in errors))

        if warnings:
            print("\n⚠️  配置警告:")
            for w in warnings:
                print(f"  - {w}")

        return True

    def print_info(self):
        """打印配置信息（隐藏敏感信息）"""
        print(f"应用名称: {self.app_name}")
        print(f"版本: {self.app_version}")
        print(f"服务器: {self.host}:{self.port}")
        print(f"高德地图API Key: {'已配置' if self.amap_api_key else '未配置'}")
        print(f"百度翻译API: {'已配置' if self.baidu_trans_app_id else '未配置'}")
        
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """获取配置实例（单例模式）"""
    return Settings()


def validate_config():
    """验证配置"""
    settings = get_settings()
    settings.validate()


def print_config():
    """打印配置信息"""
    settings = get_settings()
    settings.print_info()