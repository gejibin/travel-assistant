"""
测试Pexels图片搜索结果并保存到本地文件
"""

import json
from datetime import datetime
from ..services.pexels_service import get_pexels_service
from ..tools.utils.chinese_to_english_translator import translate_chinese_to_english

def test_image_search():
    """测试图片搜索功能"""
    print("🔍 开始测试Pexels图片搜索功能...")
    
    # 获取Pexels服务实例
    pexels_service = get_pexels_service()
    
    # 测试景点列表 - 只包含中文名称
    chinese_attractions = [
        "故宫",
        "长城", 
        "天安门广场",
        "正阳门箭楼",
        "北京古观象台",
        "中国国家博物馆",
        "北京湖广会馆",
        "什刹海",
        "烟袋斜街",
        "北京石刻艺术博物馆"
    ]
    
    # 存储搜索结果
    results = {
        "test_time": datetime.now().isoformat(),
        "city": "Beijing",
        "attractions": []
    }
    
    for chinese_name in chinese_attractions:
        # 实时翻译中文名称为英文
        english_name = translate_chinese_to_english(chinese_name)
        print(f"\n🔍 搜索: {chinese_name} (翻译为: {english_name})")
        
        # 测试不同搜索策略 - 包括翻译后的英文名称
        queries = [
            f"{english_name} Beijing China",      # 英文名称+城市+国家
            f"{chinese_name} Beijing China",      # 中文名称+城市+国家
            f"{english_name} China",              # 英文名称+国家
            f"{english_name} landmark",           # 英文名称+地标
            f"{chinese_name} landmark",           # 中文名称+地标
            f"{english_name}",                    # 仅英文名称
            f"{chinese_name}"                     # 仅中文名称
        ]
        
        found = False
        for query in queries:
            print(f"  尝试查询: {query}")
            photo_url = pexels_service.get_photo_url(query)
            
            if photo_url:
                print(f"  ✅ 找到图片: {photo_url[:80]}...")
                results["attractions"].append({
                    "chinese_name": chinese_name,
                    "english_name": english_name,
                    "query_used": query,
                    "photo_url": photo_url
                })
                found = True
                break
            else:
                print(f"  ❌ 未找到图片")
        
        if not found:
            print(f"  ❌ 所有查询均未找到 {chinese_name} 的图片")
            results["attractions"].append({
                "chinese_name": chinese_name,
                "english_name": english_name,
                "query_used": "None",
                "photo_url": None
            })
    
    # 保存结果到本地文件
    filename = f"image_search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 测试完成，结果已保存到 {filename}")
    
    # 输出摘要
    print("\n📊 测试结果摘要:")
    successful = 0
    for item in results["attractions"]:
        if item["photo_url"]:
            successful += 1
            print(f"  ✅ {item['chinese_name']} ({item['english_name']}) - 使用查询: {item['query_used']}")
        else:
            print(f"  ❌ {item['chinese_name']} ({item['english_name']}) - 未找到图片")
    
    print(f"\n📈 成功率: {successful}/{len(chinese_attractions)} ({successful/len(chinese_attractions)*100:.1f}%)")
    
    return results

if __name__ == "__main__":
    test_image_search()