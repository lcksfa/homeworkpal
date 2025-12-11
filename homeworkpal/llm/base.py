"""
基础模型接口定义
Base interfaces for LLM and embedding models
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any


class BaseEmbeddingModel(ABC):
    """嵌入模型基类"""

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """生成文档嵌入向量"""
        pass

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """生成查询嵌入向量"""
        pass

    @abstractmethod
    def get_embedding_dimension(self) -> int:
        """获取向量维度"""
        pass


class BaseLLMClient(ABC):
    """大语言模型客户端基类"""

    @abstractmethod
    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """聊天补全"""
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        pass

    @abstractmethod
    def get_response_text(self, response: Dict[str, Any]) -> str:
        """从响应中提取回复文本"""
        pass