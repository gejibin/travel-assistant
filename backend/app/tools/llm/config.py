"""配置管理 - 优化版"""

import os
from typing import Optional
from pydantic import BaseModel, Field

class Config(BaseModel):
    """HelloAgents配置类"""
    
    # LLM配置
    default_model: str = "gpt-3.5-turbo"
    default_provider: str = "openai"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, gt=0)
    
    # 系统配置
    debug: bool = False
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    
    # 其他配置
    max_history_length: int = Field(default=100, gt=0)
    
    @classmethod
    def from_env(cls) -> "Config":
        """从环境变量创建配置"""
        return cls(
            debug=os.getenv("DEBUG", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            temperature=float(os.getenv("TEMPERATURE", "0.7")),
            max_tokens=int(max_tokens) if (max_tokens := os.getenv("MAX_TOKENS")) else None,
        )
