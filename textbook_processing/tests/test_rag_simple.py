#!/usr/bin/env python3
"""
简化的RAG测试脚本
Simple RAG Test Script

测试基本的语义搜索功能
"""

import os
import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from homeworkpal.database.connection import engine
from sqlalchemy.orm import sessionmaker
from homeworkpal.database.models import TextbookChunk
from homeworkpal.llm.base import BaseEmbeddingModel
from homeworkpal.llm.siliconflow import SiliconFlowEmbeddingModel
import numpy as np

def print_status(message: str, status: str):
    """打印状态信息"""
    icons = {"✅": "✅", "❌": "❌", "⚠️": "⚠️", "🔧": "🔧", "📚": "📚", "🔍": "🔍", "💾": "💾", "📖": "📖"}
    print(f"{icons.get(status, 'ℹ️')} {message}")

def get_embedding_model():
    """获取嵌入模型"""
    try:
        api_key = os.getenv("SILICONFLOW_API_KEY")
        base_url = os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")

        if not api_key:
            print_status("未设置SILICONFLOW_API_KEY环境变量", "⚠️")
            return None

        embedding_model = SiliconFlowEmbeddingModel(
            api_key=api_key,
            base_url=base_url
        )
        print_status("成功加载嵌入模型", "✅")
        return embedding_model
    except Exception as e:
        print_status(f"加载嵌入模型失败: {e}", "❌")
        return None

def cosine_similarity(vec1, vec2) -> float:
    """计算余弦相似度"""
    try:
        # 转换为numpy数组
        vec1_array = np.array(vec1, dtype=float)
        vec2_array = np.array(vec2, dtype=float)

        # 检查向量大小
        if vec1_array.size == 0 or vec2_array.size == 0:
            return 0.0

        # 计算相似度
        dot_product = np.dot(vec1_array, vec2_array)
        norm1 = np.linalg.norm(vec1_array)
        norm2 = np.linalg.norm(vec2_array)

        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0

        return float(dot_product / (norm1 * norm2))
    except Exception as e:
        print_status(f"计算余弦相似度失败: {e}", "⚠️")
        return 0.0

def test_simple_search():
    """简单搜索测试"""
    print_status("开始简单语义搜索测试", "🔍")

    # 获取数据库连接
    try:
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
    except Exception as e:
        print_status(f"数据库连接失败: {e}", "❌")
        return False

    # 获取嵌入模型
    embedding_model = get_embedding_model()
    if not embedding_model:
        session.close()
        return False

    try:
        # 测试查询
        query = "大青树下的小学"
        print_status(f"查询: {query}", "📝")

        # 生成查询向量
        query_embedding = embedding_model.embed_query(query)
        print_status(f"查询向量维度: {len(query_embedding)}", "📊")

        # 获取有向量的记录
        records = session.query(TextbookChunk).filter(
            TextbookChunk.embedding.isnot(None)
        ).limit(10).all()  # 限制为10条记录进行测试

        print_status(f"找到 {len(records)} 条有向量的记录", "📊")

        # 计算相似度
        results = []
        for i, record in enumerate(records):
            try:
                print_status(f"处理记录 {i+1}: 页码 {record.page_number}", "🔄")

                # 检查向量格式
                embedding = record.embedding
                if isinstance(embedding, str):
                    print_status("向量是字符串格式，尝试转换", "🔧")
                    embedding = eval(embedding)

                similarity = cosine_similarity(query_embedding, embedding)
                results.append((similarity, record))
                print_status(f"相似度: {similarity:.4f}", "✅")

            except Exception as e:
                print_status(f"处理记录 {i+1} 失败: {e}", "⚠️")
                continue

        # 排序并显示结果
        results.sort(key=lambda x: x[0], reverse=True)

        print_status("\n搜索结果:", "📋")
        for i, (similarity, record) in enumerate(results[:3]):
            content_preview = record.content[:50] + "..." if len(record.content) > 50 else record.content
            print(f"  {i+1}. 相似度: {similarity:.4f} | 页码: {record.page_number}")
            print(f"     内容: {content_preview}")

        session.close()
        return True

    except Exception as e:
        print_status(f"搜索测试失败: {e}", "❌")
        session.close()
        return False

def main():
    """主函数"""
    print("🎯 简化RAG测试脚本")
    print("=" * 40)

    if test_simple_search():
        print("\n🎉 简化搜索测试完成！")
        return 0
    else:
        print("\n❌ 简化搜索测试失败！")
        return 1

if __name__ == "__main__":
    sys.exit(main())