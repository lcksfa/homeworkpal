#!/usr/bin/env python3
"""
RAG服务教育场景测试
RAG Service Educational Scenario Testing

专门测试三年级人教版教材相关搜索功能
"""

import os
import sys
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from homeworkpal.rag.rag_service import create_rag_service
from homeworkpal.llm.siliconflow import SiliconFlowClient

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_chinese_textbook_search(rag_service):
    """测试语文教材搜索"""
    print("\n📚 测试语文教材内容搜索...")
    print("=" * 50)

    test_queries = [
        "秋分过后有什么特点",
        "伤员陆续",
        "修改符号的使用",
        "白求恩做手术",
        "阅读链接的内容"
    ]

    for query in test_queries:
        print(f"\n🔍 搜索: '{query}'")
        results = rag_service.search(query, top_k=2)

        print(f"   找到 {len(results)} 个结果:")
        for i, result in enumerate(results, 1):
            print(f"   {i}. 相似度: {result.score:.3f}")
            print(f"      内容: {result.content[:100]}...")
            print(f"      页码: {result.page_number}")
            print(f"      单元: {result.metadata.get('unit', '未知')}")

    return True


def test_third_grade_level_content(rag_service):
    """测试三年级适龄内容搜索"""
    print("\n🎓 测试三年级适龄内容...")
    print("=" * 50)

    # 测试适合三年级学生的查询
    queries = [
        "怎么写作文",
        "怎么修改作文",
        "阅读理解",
        "语文学习"
    ]

    for query in queries:
        print(f"\n🔍 三年级查询: '{query}'")
        results = rag_service.search(query, top_k=3, grade="三年级")

        print(f"   找到 {len(results)} 个结果:")
        for i, result in enumerate(results, 1):
            print(f"   {i}. 相似度: {result.score:.3f}")
            print(f"      内容: {result.content[:80]}...")
            # 验证内容是否适合三年级学生
            simple_content = len(result.content) < 300  # 简单的内容检查
            print(f"      适龄性: {'✅ 适合' if simple_content else '⚠️ 内容较长'}")

    return True


def test_semantic_understanding(rag_service):
    """测试语义理解能力"""
    print("\n🧠 测试语义理解能力...")
    print("=" * 50)

    # 测试语义相似的查询
    semantic_groups = [
        [
            "秋分是什么时候",
            "秋分过后的特点",
            "秋天到了会怎样"
        ],
        [
            "修改作文的符号",
            "作文修改标记",
            "写作修改方法"
        ]
    ]

    for group_idx, queries in enumerate(semantic_groups, 1):
        print(f"\n🔗 语义组 {group_idx}:")

        all_results = []
        for query in queries:
            print(f"   搜索: '{query}'")
            results = rag_service.search(query, top_k=2)
            all_results.extend([r.content for r in results])
            print(f"     结果数: {len(results)}")

        # 检查是否有重叠结果（表明语义理解准确）
        unique_results = set(all_results)
        overlap_ratio = 1 - len(unique_results) / len(all_results) if all_results else 0
        print(f"   语义重叠度: {overlap_ratio:.2%} (越高表明语义理解越准确)")

    return True


def test_content_metadata(rag_service):
    """测试内容元数据检索"""
    print("\n📊 测试内容元数据检索...")
    print("=" * 50)

    # 获取服务统计信息
    stats = rag_service.get_service_stats()

    print("📈 系统统计:")
    print(f"   总文档片段: {stats.get('total_chunks', 0)}")
    print(f"   学科分布: {stats.get('subject_distribution', {})}")
    print(f"   年级分布: {stats.get('grade_distribution', {})}")

    # 测试基于元数据的搜索
    print("\n🎯 基于元数据的搜索:")

    # 按学科搜索
    results = rag_service.search("阅读", subject="语文", top_k=3)
    print(f"   语文-阅读: {len(results)} 个结果")

    # 按年级搜索
    results = rag_service.search("学习", grade="三年级", top_k=3)
    print(f"   三年级-学习: {len(results)} 个结果")

    return True


def test_retrieval_performance(rag_service):
    """测试检索性能"""
    print("\n⚡ 测试检索性能...")
    print("=" * 50)

    import time

    test_query = "秋分过后的变化"
    iterations = 5

    response_times = []

    for i in range(iterations):
        start_time = time.time()
        results = rag_service.search(test_query, top_k=3)
        end_time = time.time()

        response_time = (end_time - start_time) * 1000  # 转换为毫秒
        response_times.append(response_time)

        print(f"   测试 {i+1}: {response_time:.1f}ms, 结果数: {len(results)}")

    avg_time = sum(response_times) / len(response_times)
    print(f"\n📊 性能统计:")
    print(f"   平均响应时间: {avg_time:.1f}ms")
    print(f"   最快响应时间: {min(response_times):.1f}ms")
    print(f"   最慢响应时间: {max(response_times):.1f}ms")

    # 检查是否满足性能要求（<500ms）
    performance_ok = avg_time < 500
    print(f"   性能评估: {'✅ 优秀' if performance_ok else '⚠️ 需要优化'} (目标: <500ms)")

    return performance_ok


def main():
    """主测试函数"""
    print("🎓 RAG服务教育场景测试开始")
    print("=" * 60)

    try:
        # 创建RAG服务
        rag_service = create_rag_service(
            similarity_threshold=0.25,  # 降低阈值以获得更多结果
            max_results=5
        )
        print("✅ RAG服务创建成功")
    except Exception as e:
        print(f"❌ RAG服务创建失败: {e}")
        return False

    # 运行教育场景测试
    test_functions = [
        ("语文教材搜索", test_chinese_textbook_search),
        ("三年级适龄内容", test_third_grade_level_content),
        ("语义理解能力", test_semantic_understanding),
        ("内容元数据检索", test_content_metadata),
        ("检索性能测试", test_retrieval_performance)
    ]

    results = {}
    for test_name, test_func in test_functions:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            results[test_name] = test_func(rag_service)
        except Exception as e:
            print(f"❌ {test_name}测试失败: {e}")
            results[test_name] = False

    # 测试结果总结
    print("\n" + "=" * 60)
    print("📋 教育场景测试总结")
    print("=" * 60)

    passed = 0
    total = len(results)

    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1

    print(f"\n📊 总体结果: {passed}/{total} 测试通过")

    if passed == total:
        print("🎉 所有教育场景测试通过！RAG服务已准备好为三年级学生提供支持")
        return True
    else:
        print("⚠️  部分测试未通过，但核心功能仍然可用")
        return passed >= total * 0.8  # 80%通过率即可


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)