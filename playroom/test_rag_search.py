#!/usr/bin/env python3
"""
RAG检索测试
RAG Search Test

测试向量检索和知识库查询功能
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from homeworkpal.database.connection import engine
from sqlalchemy.orm import sessionmaker
from homeworkpal.database.models import TextbookChunk
import numpy as np
import json

def print_status(message: str, status: str):
    """打印状态信息"""
    icons = {"✅": "✅", "❌": "❌", "⚠️": "⚠️", "🔧": "🔧", "📚": "📚", "🔍": "🔍", "💾": "💾"}
    print(f"{icons.get(status, 'ℹ️')} {message}")


def test_database_connection():
    """测试数据库连接"""
    print_status("测试数据库连接", "🔧")

    try:
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        # 简单查询
        count = session.query(TextbookChunk).count()
        print(f"📊 数据库中知识片段数量: {count}")

        session.close()
        print_status("数据库连接成功", "✅")
        return True

    except Exception as e:
        print_status(f"数据库连接失败: {e}", "❌")
        return False


def test_vector_similarity():
    """测试向量相似度计算"""
    print_status("测试向量相似度计算", "🔍")

    try:
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        # 获取所有知识片段
        chunks = session.query(TextbookChunk).all()

        if len(chunks) < 2:
            print("⚠️ 需要至少2个知识片段来测试相似度")
            session.close()
            return False

        print(f"📊 找到 {len(chunks)} 个知识片段")

        # 显示前几个片段的信息
        for i, chunk in enumerate(chunks[:2]):
            print(f"\n--- 知识片段 {i+1} ---")
            print(f"文件: {chunk.source_file}")
            print(f"学科: {chunk.metadata_json.get('subject', '未知')}")
            print(f"年级: {chunk.metadata_json.get('grade', '未知')}")
            print(f"内容长度: {len(chunk.content)} 字符")
            print(f"内容预览: {chunk.content[:100]}...")

            if chunk.embedding is not None:
                print(f"向量维度: {len(chunk.embedding)}")

        # 计算两个向量之间的余弦相似度
        if chunks[0].embedding is not None and chunks[1].embedding is not None:
            vec1 = np.array(chunks[0].embedding)
            vec2 = np.array(chunks[1].embedding)

            # 余弦相似度
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            if norm1 > 0 and norm2 > 0:
                cosine_similarity = dot_product / (norm1 * norm2)
                print(f"\n🔗 向量相似度: {cosine_similarity:.4f}")
            else:
                print(f"\n⚠️ 无法计算相似度（向量为零）")

        session.close()
        print_status("向量相似度测试完成", "✅")
        return True

    except Exception as e:
        print_status(f"向量相似度测试失败: {e}", "❌")
        return False


def test_mock_query():
    """测试模拟查询"""
    print_status("测试模拟查询功能", "🔍")

    try:
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        # 模拟查询："三年级数学时间"
        query_text = "三年级数学时间"
        print(f"🔍 模拟查询: {query_text}")

        # 获取所有知识片段
        chunks = session.query(TextbookChunk).all()

        if not chunks:
            print("❌ 数据库中没有知识片段")
            session.close()
            return False

        # 简单的关键词匹配（在实际应用中会使用向量相似度）
        relevant_chunks = []
        for chunk in chunks:
            content_lower = chunk.content.lower()
            if any(keyword in content_lower for keyword in ['时间', '数学', '钟表']):
                relevant_chunks.append(chunk)

        print(f"📊 找到 {len(relevant_chunks)} 个相关片段")

        # 显示相关片段
        for i, chunk in enumerate(relevant_chunks):
            print(f"\n--- 相关片段 {i+1} ---")
            print(f"文件: {chunk.source_file}")
            print(f"学科: {chunk.metadata_json.get('subject', '未知')}")
            print(f"年级: {chunk.metadata_json.get('grade', '未知')}")
            print(f"质量评分: {chunk.quality_score}")
            print(f"内容: {chunk.content}")

        session.close()
        print_status("模拟查询测试完成", "✅")
        return True

    except Exception as e:
        print_status(f"模拟查询测试失败: {e}", "❌")
        return False


def main():
    """主测试函数"""
    print("🎯 作业搭子 RAG 系统 - 检索功能测试")
    print("=" * 60)

    tests = [
        ("数据库连接", test_database_connection),
        ("向量相似度", test_vector_similarity),
        ("模拟查询", test_mock_query)
    ]

    passed = 0
    total = len(tests)

    for name, test_func in tests:
        try:
            print(f"\n🧪 运行测试: {name}")
            if test_func():
                print(f"✅ {name} - 通过")
                passed += 1
            else:
                print(f"❌ {name} - 失败")
        except Exception as e:
            print(f"❌ {name} - 异常: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 RAG检索功能测试全部通过！")
        print("💡 知识库已经准备好进行问答测试")
        print("\n🚀 下一步:")
        print("  1. 配置SiliconFlow API以进行真实向量嵌入")
        print("  2. 实现完整的向量相似度搜索")
        print("  3. 集成LLM进行问答生成")
        return 0
    else:
        print("⚠️ 部分测试失败，请检查问题")
        return 1


if __name__ == "__main__":
    sys.exit(main())