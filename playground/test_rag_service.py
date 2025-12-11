#!/usr/bin/env python3
"""
RAG服务功能测试脚本
RAG Service Functional Test Script

用于测试和验证RAG检索服务的基本功能
"""

import os
import sys
import logging
from typing import List

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from homeworkpal.rag.rag_service import RAGService, create_rag_service
from homeworkpal.llm.siliconflow import SiliconFlowClient

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_embedding_client():
    """测试向量嵌入客户端"""
    print("🔧 测试向量嵌入客户端...")
    print("=" * 50)

    try:
        client = SiliconFlowClient()
        print("✅ SiliconFlow客户端初始化成功")

        # 测试查询向量生成
        test_query = "周长怎么算"
        embedding = client.embed_query(test_query)
        print(f"✅ 查询向量生成成功: {len(embedding)}维")
        print(f"📊 向量前5位: {embedding[:5]}")

        return client

    except Exception as e:
        print(f"❌ 向量嵌入客户端测试失败: {e}")
        return None


def test_rag_service_basic(rag_service):
    """测试RAG服务基础功能"""
    print("\n🔍 测试RAG服务基础功能...")
    print("=" * 50)

    try:
        # 测试基础搜索
        print("\n📝 测试查询: '周长怎么算'")
        results = rag_service.search("周长怎么算", top_k=3)

        print(f"✅ 搜索完成，返回 {len(results)} 个结果")
        for i, result in enumerate(results, 1):
            print(f"\n📄 结果 {i}:")
            print(f"   内容: {result.content[:100]}...")
            print(f"   相似度: {result.score:.3f}")
            print(f"   元数据: {result.metadata}")
            print(f"   页码: {result.page_number}")

        return len(results) > 0

    except Exception as e:
        print(f"❌ RAG服务基础功能测试失败: {e}")
        return False


def test_rag_service_with_filters(rag_service):
    """测试带过滤条件的RAG服务"""
    print("\n🎯 测试带过滤条件的搜索...")
    print("=" * 50)

    try:
        # 测试学科过滤
        print("\n📚 测试数学学科过滤")
        results = rag_service.search(
            "加减法运算",
            top_k=3,
            subject="数学",
            grade="三年级"
        )

        print(f"✅ 过滤搜索完成，返回 {len(results)} 个结果")
        for i, result in enumerate(results, 1):
            print(f"\n📄 结果 {i}:")
            print(f"   内容: {result.content[:80]}...")
            print(f"   相似度: {result.score:.3f}")
            print(f"   学科: {result.metadata.get('subject', '未知')}")

        return len(results) > 0

    except Exception as e:
        print(f"❌ 过滤搜索测试失败: {e}")
        return False


def test_rag_service_stats(rag_service):
    """测试RAG服务统计功能"""
    print("\n📊 测试RAG服务统计功能...")
    print("=" * 50)

    try:
        stats = rag_service.get_service_stats()

        print("📈 服务统计信息:")
        print(f"   总文档片段数: {stats.get('total_chunks', 0)}")
        print(f"   向量维度: {stats.get('embedding_dimension', 0)}")
        print(f"   相似度阈值: {stats.get('similarity_threshold', 0)}")
        print(f"   最大结果数: {stats.get('max_results', 0)}")

        if 'subject_distribution' in stats:
            print("   学科分布:")
            for subject, count in stats['subject_distribution'].items():
                print(f"     {subject}: {count}")

        if 'grade_distribution' in stats:
            print("   年级分布:")
            for grade, count in stats['grade_distribution'].items():
                print(f"     {grade}: {count}")

        return True

    except Exception as e:
        print(f"❌ 统计功能测试失败: {e}")
        return False


def test_hybrid_search(rag_service):
    """测试混合搜索功能"""
    print("\n🔀 测试混合搜索功能...")
    print("=" * 50)

    try:
        print("\n📝 测试混合查询: '时间单位换算'")
        results = rag_service.hybrid_search(
            "时间单位换算",
            top_k=3,
            keyword_weight=0.3,
            semantic_weight=0.7
        )

        print(f"✅ 混合搜索完成，返回 {len(results)} 个结果")
        for i, result in enumerate(results, 1):
            print(f"\n📄 结果 {i}:")
            print(f"   内容: {result.content[:80]}...")
            print(f"   混合分数: {result.score:.3f}")
            print(f"   学科: {result.metadata.get('subject', '未知')}")

        return len(results) > 0

    except Exception as e:
        print(f"❌ 混合搜索测试失败: {e}")
        return False


def test_service_factory():
    """测试服务工厂函数"""
    print("\n🏭 测试RAG服务工厂函数...")
    print("=" * 50)

    try:
        # 使用工厂函数创建服务
        service = create_rag_service(
            similarity_threshold=0.4,
            max_results=8
        )

        print("✅ 工厂函数创建服务成功")
        print(f"   相似度阈值: {service.similarity_threshold}")
        print(f"   最大结果数: {service.max_results}")

        return True

    except Exception as e:
        print(f"❌ 工厂函数测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 RAG服务功能测试开始")
    print("=" * 60)

    test_results = {}

    # 1. 测试向量嵌入客户端
    embedding_client = test_embedding_client()
    test_results['embedding_client'] = embedding_client is not None

    if not embedding_client:
        print("\n❌ 向量嵌入客户端测试失败，无法继续测试")
        return False

    # 2. 创建RAG服务实例
    try:
        rag_service = RAGService(
            embedding_client=embedding_client,
            similarity_threshold=0.3,
            max_results=5
        )
        print("✅ RAG服务初始化成功")
        test_results['service_init'] = True
    except Exception as e:
        print(f"❌ RAG服务初始化失败: {e}")
        test_results['service_init'] = False
        return False

    # 3. 测试基础搜索功能
    test_results['basic_search'] = test_rag_service_basic(rag_service)

    # 4. 测试过滤搜索功能
    test_results['filtered_search'] = test_rag_service_with_filters(rag_service)

    # 5. 测试混合搜索功能
    test_results['hybrid_search'] = test_hybrid_search(rag_service)

    # 6. 测试统计功能
    test_results['service_stats'] = test_rag_service_stats(rag_service)

    # 7. 测试工厂函数
    test_results['service_factory'] = test_service_factory()

    # 输出测试结果总结
    print("\n" + "=" * 60)
    print("📋 测试结果总结:")
    print("=" * 60)

    passed = 0
    total = len(test_results)

    for test_name, result in test_results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1

    print(f"\n📊 总体结果: {passed}/{total} 测试通过")

    if passed == total:
        print("🎉 所有测试通过！RAG服务功能正常")
        return True
    else:
        print("⚠️  部分测试失败，请检查相关功能")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)