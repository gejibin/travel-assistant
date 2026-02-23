"""
中文到英文翻译工具
使用百度翻译API和大语言模型进行高质量翻译
"""

from typing import List
import time
import requests
from urllib.parse import urlencode
import hashlib
import random
from ..agents.simple_agent import SimpleAgent
from ..llm.llm import HelloAgentsLLM  # 使用正确的导入路径
from ...config import get_settings


class ChineseToEnglishTranslator:
    """中文到英文翻译器"""
    
    def __init__(self):
        """初始化翻译器"""
        self.settings = get_settings()
        try:
            # 使用正确的HelloAgents类
            self.translation_agent = SimpleAgent(
                name="ChineseToEnglishTranslator",
                llm=HelloAgentsLLM(),
                system_prompt=self._get_translation_prompt()
            )
        except Exception as e:
            print(f"⚠️ 初始化LLM翻译器失败: {e}")
            self.translation_agent = None
    
    def _get_translation_prompt(self) -> str:
        """获取翻译代理的系统提示"""
        return """你是一个专业的中英翻译专家。你的任务是将中文文本准确翻译成英文，同时保留原文的含义和语境。

要求：
1. 只输出翻译结果，不要添加任何解释
2. 保持专有名词的准确性（如地名、人名、机构名等）
3. 对于景点名称、地标等，使用国际通用的标准译名
4. 语法要符合英文习惯
5. 不要添加标点符号或额外字符，除非原文本就有

例如：
- 输入："故宫" → 输出："Forbidden City"
- 输入："北京长城" → 输出："Great Wall of China"
- 输入："西湖" → 输出："West Lake"

现在请翻译用户提供的中文文本。"""
    
    def translate(self, text: str) -> str:
        """翻译中文文本到英文，优先使用百度翻译API"""
        if not text or not text.strip():
            return text
        
        # 优先尝试百度翻译API
        try:
            result = self._baidu_translate(text)
            if result and result != text:
                print(f"✅ 使用百度翻译成功: {text} -> {result}")
                return result
        except Exception as e:
            print(f"⚠️ 百度翻译失败: {e}")
        
        # 如果百度翻译失败，尝试LLM
        try:
            result = self._llm_translate(text)
            if result and result != text:
                print(f"✅ 使用LLM翻译成功: {text} -> {result}")
                return result
        except Exception as e:
            print(f"⚠️ LLM翻译失败: {e}")
        
        # 所有服务都失败，返回原文
        print(f"⚠️ 所有翻译服务都失败，返回原文: {text}")
        return text
    
    def _baidu_translate(self, text: str) -> str:
        """使用百度翻译API"""
        if not self.settings.baidu_trans_app_id or not self.settings.baidu_trans_secret_key:
            raise Exception("百度翻译API凭据未配置")
        
        url = 'https://fanyi-api.baidu.com/api/trans/vip/translate'
        app_id = self.settings.baidu_trans_app_id
        secret_key = self.settings.baidu_trans_secret_key
        
        salt = random.randint(32768, 65536)
        sign_str = app_id + text + str(salt) + secret_key
        sign = hashlib.md5(sign_str.encode()).hexdigest()
        
        params = {
            'q': text,
            'from': 'zh',
            'to': 'en',
            'appid': app_id,
            'salt': salt,
            'sign': sign
        }
        
        response = requests.get(url, params=params)
        result = response.json()
        
        if 'trans_result' in result:
            return result['trans_result'][0]['dst']
        else:
            raise Exception(f"百度翻译API错误: {result}")
    
    def _llm_translate(self, text: str) -> str:
        """使用LLM翻译"""
        if self.translation_agent is None:
            raise Exception("LLM翻译器未初始化")
        
        response = self.translation_agent.run(text.strip())
        return response.strip()
    
    def batch_translate(self, texts: List[str]) -> List[str]:
        """批量翻译多个文本"""
        translated_texts = []
        for text in texts:
            # 添加延时以避免API限制
            time.sleep(0.1)
            translated_text = self.translate(text)
            translated_texts.append(translated_text)
        return translated_texts


# 创建全局翻译器实例
try:
    _translator = ChineseToEnglishTranslator()
except Exception as e:
    print(f"⚠️ 创建翻译器实例失败: {e}")
    _translator = None


def get_translator() -> ChineseToEnglishTranslator:
    """获取翻译器实例"""
    global _translator
    if _translator is None:
        _translator = ChineseToEnglishTranslator()
    return _translator


def translate_chinese_to_english(text: str) -> str:
    """便捷函数：将中文文本翻译为英文"""
    try:
        return get_translator().translate(text)
    except Exception as e:
        print(f"⚠️ 翻译函数调用失败: {e}，返回原文")
        return text