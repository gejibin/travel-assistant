"""消息系统 - 优化版"""

from typing import Optional, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field

MessageRole = Literal["user", "assistant", "system", "tool"]

class Message(BaseModel):
    """消息类"""
    
    content: str
    role: MessageRole
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def __init__(self, content: str, role: MessageRole, **kwargs):
        super().__init__(
            content=content,
            role=role,
            timestamp=kwargs.get('timestamp', datetime.now()),
            metadata=kwargs.get('metadata', {})
        )

    def to_dict(self) -> Dict[str, str]:
        """转换为字典格式（OpenAI API格式）"""
        return {"role": self.role, "content": self.content}
    
    def __str__(self) -> str:
        return f"[{self.role}] {self.content}"
