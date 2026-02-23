"""优化后的LLM服务模块"""

from functools import lru_cache
from ..tools.llm.llm import HelloAgentsLLM
#from ..config import get_settings


@lru_cache
def get_llm() -> HelloAgentsLLM:
    """获取LLM实例（单例模式）"""
    #settings = get_settings()
    
    # HelloAgentsLLM会自动从环境变量读取配置
    # 包括OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL等
    llm = HelloAgentsLLM()
    
    print(f"✅ LLM服务初始化成功")
    print(f"   提供商: {llm.provider}")
    print(f"   模型: {llm.model}")
    
    return llm


def reset_llm():
    """重置LLM实例（用于测试或重新配置）"""
    get_llm.cache_clear()
