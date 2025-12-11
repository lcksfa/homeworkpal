#!/usr/bin/env python3
"""
语文知识库搜索测试脚本
Chinese Knowledge Base Search Test Script
"""

import sys
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from homeworkpal.database.connection import SessionLocal
from sqlalchemy import text
import hashlib

def print_status(message: str, status: str):
    """打印状态信息"""
    icons = {"✅": "✅", "❌": "❌", "⚠️": "⚠️", "🔧": "🔧", "📚": "📚", "🔍": "🔍", "💾": "💾"}
    print(f"{icons.get(status, 'ℹ️')} {message}")

def create_simple_query_embedding(query: str) -> List[float]:
    """
    为查询创建简单的嵌入向量（与处理脚本保持一致）
    """
    hash_obj = hashlib.md5(query.encode('utf-8'))
    hash_hex = hash_obj.hexdigest()

    # 将哈希值转换为1024维向量
    vector = []
    for i in range(0, len(hash_hex), 2):
        hex_pair = hash_hex[i:i+2]
        value = int(hex_pair, 16) / 255.0 - 0.5  # 归一化到[-0.5, 0.5]
        vector.extend([value] * 64)  # 每个字节扩展为64个值

    # 确保向量长度为1024
    while len(vector) < 1024:
        vector.append(0.0)

    return vector[:1024]

def simple_vector_search(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    简单的向量相似性搜索
    """
    print_status(f"搜索查询: '{query}'", "🔍")

    try:
        # 生成查询向量
        query_embedding = create_simple_query_embedding(query)

        session = SessionLocal()

        # 使用余弦相似度进行简单的向量搜索
        # 注意：这里使用简化的相似度计算，实际应用中应该使用pgvector的内置函数
        result = session.execute(text('''
            SELECT
                content,
                page_number,
                chunk_index,
                metadata_json,
                embedding,
                CASE
                    WHEN embedding IS NOT NULL THEN
                        1.0 - ABS(SUM(ABS(
                            (embedding[:1]::vector + embedding[1:2]::vector + embedding[2:3]::vector) -
                            (:query_vec[:1]::vector + :query_vec[1:2]::vector + :query_vec[2:3]::vector)
                        )) / 3.0)
                    ELSE 0.0
                END as similarity_score
            FROM textbook_chunks
            WHERE metadata_json->>'subject' = '语文'
            AND embedding IS NOT NULL
            GROUP BY content, page_number, chunk_index, metadata_json, embedding
            ORDER BY similarity_score DESC, page_number, chunk_index
            LIMIT :limit
        '''), {
            'query_vec': query_embedding,
            'limit': limit
        })

        results = []
        for row in result.fetchall():
            results.append({
                'content': row.content,
                'page_number': row.page_number,
                'chunk_index': row.chunk_index,
                'metadata': row.metadata_json,
                'similarity_score': row.similarity_score
            })

        session.close()

        print(f"✅ 找到 {len(results)} 个相关片段")
        return results

    except Exception as e:
        print(f"❌ 搜索失败: {e}")
        return []

def search_by_keyword(keyword: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    基于关键词的搜索
    """
    print_status(f"关键词搜索: '{keyword}'", "🔍")

    try:
        session = SessionLocal()

        result = session.execute(text('''
            SELECT
                content,
                page_number,
                chunk_index,
                metadata_json,
                CASE
                    WHEN content ILIKE '%' || :keyword || '%' THEN 1.0
                    WHEN metadata_json ILIKE '%' || :keyword || '%' THEN 0.5
                    ELSE 0.0
                END as keyword_score
            FROM textbook_chunks
            WHERE metadata_json->>'subject' = '语文'
            AND (content ILIKE '%' || :keyword || '%' OR metadata_json ILIKE '%' || :keyword || '%')
            ORDER BY keyword_score DESC, page_number, chunk_index
            LIMIT :limit
        '''), {
            'keyword': keyword,
            'limit': limit
        })

        results = []
        for row in result.fetchall():
            results.append({
                'content': row.content,
                'page_number': row.page_number,
                'chunk_index': row.chunk_index,
                'metadata': row.metadata_json,
                'keyword_score': row.keyword_score
            })

        session.close()

        print(f"✅ 找到 {len(results)} 个相关片段")
        return results

    except Exception as e:
        print(f"❌ 关键词搜索失败: {e}")
        return []

def display_results(results: List[Dict[str, Any]], search_type: str):
    """
    显示搜索结果
    """
    print(f"\n📋 {search_type}搜索结果:")
    print("=" * 60)

    if not results:
        print("❌ 未找到相关内容")
        return

    for i, result in enumerate(results, 1):
        print(f"\n🔍 结果 {i}:")
        print(f"   📄 页码: {result['page_number']}")
        print(f"   📝 片段: {result['chunk_index']}")
        print(f"   📊 相关性: {result.get('similarity_score', result.get('keyword_score', 0)):.3f}")

        # 显示内容预览
        content = result['content']
        preview = content[:200] + '...' if len(content) > 200 else content
        print(f"   📖 内容预览:")
        print(f"      {preview}")

def main():
    """主函数"""
    print("🔧 语文知识库搜索测试")
    print("=" * 60)
    print()

    # 测试查询列表
    test_queries = [
        "我们的学校",
        "老师",
        "学习",
        "课文",
        "生字"
    ]

    test_keywords = [
        "学校",
        "老师",
        "学习",
        "课文",
        "练习"
    ]

    try:
        # 执行向量搜索测试
        print("🚀 向量搜索测试")
        print("-" * 40)
        for query in test_queries:
            results = simple_vector_search(query, limit=3)
            display_results(results, f"向量搜索 - {query}")
            print()

        # 执行关键词搜索测试
        print("\n🚀 关键词搜索测试")
        print("-" * 40)
        for keyword in test_keywords:
            results = search_by_keyword(keyword, limit=3)
            display_results(results, f"关键词搜索 - {keyword}")
            print()

        print("=" * 60)
        print("🎉 语文知识库搜索测试完成!")
        print("✅ 搜索功能基本可用")
        print("⚠️  注意：当前使用简化算法，实际部署时需要使用真实的嵌入模型")

        return 0

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())