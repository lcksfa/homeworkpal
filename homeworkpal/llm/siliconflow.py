"""
SiliconFlow API客户端
SiliconFlow Client for BGE-M3 Embedding and Qwen LLM

支持BGE-M3向量嵌入模型和Qwen系列大语言模型
"""

import os
import requests
import logging
from typing import List, Dict, Any, Optional
import json

from .base import EmbeddingModel, LLMClient

logger = logging.getLogger(__name__)


class SiliconFlowEmbeddingModel(EmbeddingModel):
    """SiliconFlow BGE-M3嵌入模型客户端"""

    def __init__(self, api_key: str, base_url: str, model_name: str = "BAAI/bge-m3"):
        """
        初始化SiliconFlow嵌入模型

        Args:
            api_key: SiliconFlow API密钥
            base_url: API基础URL
            model_name: 模型名称，默认使用BAAI/bge-m3
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.model_name = model_name
        self.embedding_url = f"{self.base_url}/v1/embeddings"

        # 设置请求头
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def embed_query(self, text: str) -> List[float]:
        """
        为单个查询文本生成向量嵌入

        Args:
            text: 查询文本

        Returns:
            向量嵌入列表
        """
        return self.embed_documents([text])[0]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        为文档列表批量生成向量嵌入

        Args:
            texts: 文档文本列表

        Returns:
            向量嵌入列表的列表
        """
        try:
            # 准备请求数据
            payload = {
                "model": self.model_name,
                "input": texts,
                "encoding_format": "float"
            }

            logger.debug(f"发送嵌入请求: {len(texts)} 个文本")

            # 发送POST请求
            response = requests.post(
                self.embedding_url,
                headers=self.headers,
                json=payload,
                timeout=30.0
            )

            response.raise_for_status()
            result = response.json()

            # 提取嵌入向量
            embeddings = [item['embedding'] for item in result['data']]

            logger.debug(f"成功生成 {len(embeddings)} 个嵌入向量，维度: {len(embeddings[0])}")

            return embeddings

        except Exception as e:
            logger.error(f"生成嵌入向量失败: {e}")
            raise


class SiliconFlowLLMClient(LLMClient):
    """SiliconFlow Qwen大语言模型客户端"""

    def __init__(self, api_key: str, base_url: str, model_name: str = "Qwen/Qwen2.5-7B-Instruct"):
        """
        初始化SiliconFlow LLM客户端

        Args:
            api_key: SiliconFlow API密钥
            base_url: API基础URL
            model_name: 模型名称，默认使用Qwen2.5-7B-Instruct
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.model_name = model_name
        self.chat_url = f"{self.base_url}/v1/chat/completions"

        # 设置请求头
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def chat_completion(self,
                      messages: List[Dict[str, str]],
                      max_tokens: int = 1000,
                      temperature: float = 0.7,
                      stream: bool = False) -> Dict[str, Any]:
        """
        调用聊天补全API

        Args:
            messages: 对话消息列表
            max_tokens: 最大token数量
            temperature: 温度参数
            stream: 是否使用流式响应

        Returns:
            API响应结果
        """
        try:
            # 准备请求数据
            payload = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": stream
            }

            logger.debug(f"发送聊天请求: {len(messages)} 条消息")

            # 发送POST请求
            response = requests.post(
                self.chat_url,
                headers=self.headers,
                json=payload,
                timeout=30.0
            )

            response.raise_for_status()
            result = response.json()

            logger.debug(f"聊天响应成功，token使用: {result.get('usage', {})}")

            return result

        except Exception as e:
            logger.error(f"聊天补全失败: {e}")
            raise

    def get_response_text(self, response: Dict[str, Any]) -> str:
        """
        从响应中提取回复文本

        Args:
            response: API响应

        Returns:
            回复文本
        """
        try:
            return response['choices'][0]['message']['content']
        except (KeyError, IndexError) as e:
            logger.error(f"提取回复文本失败: {e}")
            return ""


class SiliconFlowClient:
    """SiliconFlow API统一客户端"""

    def __init__(self,
                 api_key: Optional[str] = None,
                 base_url: Optional[str] = None):
        """
        初始化SiliconFlow客户端

        Args:
            api_key: API密钥，从环境变量SILICONFLOW_API_KEY获取
            base_url: API基础URL，从环境变量SILICONFLOW_BASE_URL获取
        """
        self.api_key = api_key or os.getenv("SILICONFLOW_API_KEY")
        self.base_url = base_url or os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")

        if not self.api_key:
            raise ValueError("缺少SiliconFlow API密钥，请设置SILICONFLOW_API_KEY环境变量")

        # 初始化嵌入模型和LLM客户端
        self.embedding_model = SiliconFlowEmbeddingModel(
            api_key=self.api_key,
            base_url=self.base_url,
            model_name=os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
        )

        self.llm_client = SiliconFlowLLMClient(
            api_key=self.api_key,
            base_url=self.base_url,
            model_name=os.getenv("LLM_MODEL", "Qwen/Qwen2.5-7B-Instruct")
        )

    def embed_query(self, text: str) -> List[float]:
        """为单个查询文本生成向量嵌入"""
        return self.embedding_model.embed_query(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """为文档列表批量生成向量嵌入"""
        return self.embedding_model.embed_documents(texts)

    def chat_completion(self,
                      messages: List[Dict[str, str]],
                      max_tokens: int = 1000,
                      temperature: float = 0.7) -> str:
        """
        调用聊天补全API并返回回复文本

        Args:
            messages: 对话消息列表
            max_tokens: 最大token数量
            temperature: 温度参数

        Returns:
            回复文本
        """
        response = self.llm_client.chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        return self.llm_client.get_response_text(response)


def create_siliconflow_client(api_key: Optional[str] = None,
                            base_url: Optional[str] = None) -> SiliconFlowClient:
    """
    创建SiliconFlow客户端的工厂函数

    Args:
        api_key: API密钥
        base_url: API基础URL

    Returns:
        SiliconFlow客户端实例
    """
    return SiliconFlowClient(api_key=api_key, base_url=base_url)


if __name__ == "__main__":
    # 测试SiliconFlow客户端
    print("🔧 测试SiliconFlow API客户端")
    print("=" * 40)

    try:
        # 创建客户端
        client = create_siliconflow_client()
        print("✅ 客户端初始化成功")

        # 测试BGE-M3嵌入
        test_text = "三年级数学上册第一单元：时、分、秒"
        print(f"\n📝 测试文本: {test_text}")

        embedding = client.embed_query(test_text)
        print(f"✅ BGE-M3嵌入向量维度: {len(embedding)}")
        print(f"📊 向量前5位: {embedding[:5]}")

        # 测试Qwen聊天
        messages = [
            {"role": "user", "content": "你好，我是一个三年级学生，你能帮我学习数学吗？"}
        ]

        response = client.chat_completion(messages)
        print(f"\n💬 Qwen回复: {response}")

        print("\n🎉 所有测试通过！")

    except Exception as e:
        print(f"❌ 测试失败: {e}")