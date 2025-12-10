"""
硅基流动API客户端
SiliconFlow API Client

支持BGE-M3等向量模型和千问系列大语言模型
"""

import os
import requests
from typing import List, Dict, Any, Optional
import json
import time
from .base import BaseEmbeddingModel, BaseLLMClient


class SiliconFlowClient(BaseEmbeddingModel, BaseLLMClient):
    """硅基流动API客户端"""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        初始化硅基流动客户端

        Args:
            api_key: API密钥，如果不提供则从环境变量获取
            base_url: API基础URL，如果不提供则使用默认值
        """
        self.api_key = api_key or os.getenv("SILICONFLOW_API_KEY")
        self.base_url = base_url or os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")

        if not self.api_key:
            raise ValueError("SiliconFlow API key is required. Please set SILICONFLOW_API_KEY environment variable.")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        批量生成文档嵌入向量

        Args:
            texts: 文本列表

        Returns:
            向量列表
        """
        embeddings = []

        for text in texts:
            embedding = self.embed_query(text)
            embeddings.append(embedding)

        return embeddings

    def embed_query(self, text: str, model: str = "BAAI/bge-m3") -> List[float]:
        """
        生成单个文本的嵌入向量

        Args:
            text: 输入文本
            model: 模型名称，默认使用BGE-M3

        Returns:
            向量数组
        """
        url = f"{self.base_url}/embeddings"

        payload = {
            "model": model,
            "input": text,
            "encoding_format": "float"
        }

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()

            data = response.json()
            return data["data"][0]["embedding"]

        except requests.exceptions.RequestException as e:
            print(f"API请求失败: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"错误详情: {e.response.text}")
            raise
        except Exception as e:
            print(f"生成嵌入向量时出错: {e}")
            raise

    def get_embedding_dimension(self, model: str = "BAAI/bge-m3") -> int:
        """
        获取向量维度

        Args:
            model: 模型名称

        Returns:
            向量维度
        """
        # 常见模型的向量维度
        model_dimensions = {
            "BAAI/bge-m3": 1024,
            "BAAI/bge-large-zh-v1.5": 1024,
            "qwen/Qwen2.5-embedding-7b-instruct": 3072,
        }

        # 从模型名称中提取最后的部分
        model_name = model.split("/")[-1]

        for key, dim in model_dimensions.items():
            if model_name in key or key in model_name:
                return dim

        # 默认返回1024（BGE-M3的维度）
        return 1024

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "Qwen/Qwen2.5-7B-Instruct",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """
        聊天补全

        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数

        Returns:
            生成的回复文本
        """
        url = f"{self.base_url}/chat/completions"

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()

            data = response.json()
            return data["choices"][0]["message"]["content"]

        except requests.exceptions.RequestException as e:
            print(f"API请求失败: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"错误详情: {e.response.text}")
            raise
        except Exception as e:
            print(f"聊天补全时出错: {e}")
            raise

    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息

        Returns:
            模型信息字典
        """
        return {
            "provider": "SiliconFlow",
            "base_url": self.base_url,
            "embedding_models": [
                "BAAI/bge-m3",
                "BAAI/bge-large-zh-v1.5",
                "qwen/Qwen2.5-embedding-7b-instruct"
            ],
            "chat_models": [
                "Qwen/Qwen2.5-7B-Instruct",
                "Qwen/Qwen2.5-14B-Instruct",
                "Qwen/Qwen2.5-32B-Instruct",
                "Qwen/Qwen2.5-72B-Instruct",
                "Qwen/Qwen2.5-Coder-7B-Instruct"
            ]
        }

    def test_connection(self) -> bool:
        """
        测试API连接

        Returns:
            连接是否成功
        """
        try:
            # 测试嵌入向量生成
            test_embedding = self.embed_query("测试文本", "BAAI/bge-m3")
            if len(test_embedding) != 1024:
                return False

            # 测试聊天补全
            test_messages = [{"role": "user", "content": "你好"}]
            test_response = self.chat_completion(test_messages, max_tokens=10)

            return bool(test_response)

        except Exception as e:
            print(f"连接测试失败: {e}")
            return False


def create_siliconflow_client() -> SiliconFlowClient:
    """
    创建硅基流动客户端的工厂函数

    Returns:
        SiliconFlowClient实例
    """
    return SiliconFlowClient()


# 示例用法
if __name__ == "__main__":
    # 创建客户端
    client = create_siliconflow_client()

    # 测试连接
    if client.test_connection():
        print("✅ 硅基流动API连接成功")

        # 获取模型信息
        model_info = client.get_model_info()
        print("📋 可用模型:", json.dumps(model_info, ensure_ascii=False, indent=2))

        # 测试嵌入向量
        test_text = "这是一段测试文本，用于验证BGE-M3向量模型的性能。"
        embedding = client.embed_query(test_text)
        print(f"🔢 向量维度: {len(embedding)}")
        print(f"🎯 向量前5维: {embedding[:5]}")

    else:
        print("❌ 硅基流动API连接失败")