"""优化后的Unsplash图片服务"""

import requests
from functools import lru_cache
from typing import Optional
from ..config import get_settings


class UnsplashService:
    """Unsplash图片服务类"""
    
    BASE_URL = "https://api.unsplash.com"
    TIMEOUT = 10
    
    def __init__(self):
        self.access_key = get_settings().unsplash_access_key
    
    def search_photos(self, query: str, per_page: int = 5) -> list[dict]:
        """搜索图片"""
        if not self.access_key:
            print("⚠️  Unsplash Access Key未配置")
            return []
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/search/photos",
                params={
                    "query": query,
                    "per_page": per_page,
                    "client_id": self.access_key
                },
                timeout=self.TIMEOUT
            )
            response.raise_for_status()
            
            results = response.json().get("results", [])
            
            return [
                {
                    "id": photo.get("id"),
                    "url": photo.get("urls", {}).get("regular"),
                    "thumb": photo.get("urls", {}).get("thumb"),
                    "description": photo.get("description") or photo.get("alt_description"),
                    "photographer": photo.get("user", {}).get("name")
                }
                for photo in results
            ]
        except Exception as e:
            print(f"❌ Unsplash搜索失败: {e}")
            return []
    
    def get_photo_url(self, query: str) -> Optional[str]:
        """获取单张图片URL"""
        photos = self.search_photos(query, per_page=1)
        return photos[0].get("url") if photos else None


@lru_cache
def get_unsplash_service() -> UnsplashService:
    """获取Unsplash服务实例（单例模式）"""
    return UnsplashService()
