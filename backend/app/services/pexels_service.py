"""优化后的Pexels图片服务"""

import requests
from functools import lru_cache
from typing import Optional
from ..config import get_settings


class PexelsService:
    """Pexels图片服务类"""
    
    BASE_URL = "https://api.pexels.com/v1"
    TIMEOUT = 10
    
    def __init__(self):
        self.api_key = get_settings().pexels_api_key
    
    def search_photos(self, query: str, per_page: int = 5) -> list[dict]:
        """搜索图片"""
        if not self.api_key:
            print("⚠️  Pexels API Key未配置")
            return []
        
        try:
            headers = {
                "Authorization": self.api_key
            }
            
            response = requests.get(
                f"{self.BASE_URL}/search",
                params={
                    "query": query,
                    "per_page": per_page
                },
                headers=headers,
                timeout=self.TIMEOUT
            )
            response.raise_for_status()
            
            results = response.json().get("photos", [])
            
            return [
                {
                    "id": photo.get("id"),
                    "url": photo.get("src", {}).get("large"),
                    "thumb": photo.get("src", {}).get("tiny"),
                    "description": photo.get("alt") or query,
                    "photographer": photo.get("photographer"),
                    "photographer_url": photo.get("photographer_url")
                }
                for photo in results
            ]
        except Exception as e:
            print(f"❌ Pexels搜索失败: {e}")
            return []
    
    def get_photo_url(self, query: str) -> Optional[str]:
        """获取单张图片URL"""
        photos = self.search_photos(query, per_page=1)
        return photos[0].get("url") if photos else None


@lru_cache
def get_pexels_service() -> PexelsService:
    """获取Pexels服务实例（单例模式）"""
    return PexelsService()