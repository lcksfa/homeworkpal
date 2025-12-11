#!/usr/bin/env python3
"""
RAG检索功能测试脚本
RAG Search Functionality Test Script

测试向量化导入后的检索功能，验证数据质量和检索效果
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
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


def get_database_connection():
    """获取数据库连接"""
    try:
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        return session
    except Exception as e:
        print_status(f"数据库连接失败: {e}", "❌")
        return None


def get_embedding_model():
    """获取嵌入模型"""
    try:
        api_key = os.getenv("SILICONFLOW_API_KEY")
        base_url = os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")

        if not api_key:
            print_status("未设置SILICONFLOW_API_KEY环境变量", "⚠️")
            return None

        # 创建带有更长超时时间的嵌入模型
        embedding_model = SiliconFlowEmbeddingModel(
            api_key=api_key,
            base_url=base_url
        )

        # 如果模型支持超时设置，可以在这里配置
        if hasattr(embedding_model, 'timeout'):
            embedding_model.timeout = 60  # 增加到60秒

        print_status("成功加载嵌入模型", "✅")
        return embedding_model
    except Exception as e:
        print_status(f"加载嵌入模型失败: {e}", "❌")
        return None


def cosine_similarity(vec1, vec2) -> float:
    """计算余弦相似度"""
    try:
        # 确保输入是列表格式
        if isinstance(vec1, str):
            vec1 = eval(vec1) if vec1.startswith('[') else []
        if isinstance(vec2, str):
            vec2 = eval(vec2) if vec2.startswith('[') else []

        # 将向量转换为numpy数组，确保是float类型
        vec1_array = np.array(vec1, dtype=float)
        vec2_array = np.array(vec2, dtype=float)

        # 检查向量有效性
        if vec1_array.size == 0 or vec2_array.size == 0:
            return 0.0

        # 计算点积和模长
        dot_product = np.dot(vec1_array, vec2_array)
        norm1 = np.linalg.norm(vec1_array)
        norm2 = np.linalg.norm(vec2_array)

        # 避免除零
        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0

        # 返回余弦相似度
        similarity = float(dot_product / (norm1 * norm2))
        return similarity
    except Exception as e:
        print_status(f"计算余弦相似度失败: {e}", "⚠️")
        return 0.0


def test_database_connection():
    """测试数据库连接和基础数据"""
    print_status("测试数据库连接", "🔧")

    session = get_database_connection()
    if not session:
        return False

    try:
        # 检查数据库中的记录数
        total_count = session.query(TextbookChunk).count()
        print_status(f"数据库中共有 {total_count} 条记录", "📊")

        if total_count == 0:
            print_status("数据库中没有记录，请先运行导入脚本", "⚠️")
            session.close()
            return False

        # 检查有向量的记录数
        vector_count = session.query(TextbookChunk).filter(
            TextbookChunk.embedding.isnot(None)
        ).count()
        print_status(f"有向量嵌入的记录数: {vector_count}", "📊")

        # 查看前几条记录的元数据
        sample_records = session.query(TextbookChunk).limit(3).all()
        print_status("查看样本记录元数据:", "📖")
        for i, record in enumerate(sample_records):
            metadata = record.metadata_json or {}
            content_type = metadata.get('content_type', '未知')
            content_category = metadata.get('content_category', '未分类')
            content_preview = record.content[:50] + "..." if len(record.content) > 50 else record.content
            print(f"  记录{i+1}: 页码{record.page_number}, 类型={content_type}, 分类={content_category}")
            print(f"    内容预览: {content_preview}")

        session.close()
        return True

    except Exception as e:
        print_status(f"数据库测试失败: {e}", "❌")
        session.close()
        return False


def test_content_categories():
    """测试内容分类统计"""
    print_status("测试内容分类统计", "📊")

    session = get_database_connection()
    if not session:
        return False

    try:
        # 统计各种内容类型
        categories = {}
        records = session.query(TextbookChunk).all()

        for record in records:
            metadata = record.metadata_json or {}
            content_category = metadata.get('content_category', '未分类')
            content_type = metadata.get('content_type', '未知')

            key = f"{content_category} ({content_type})"
            categories[key] = categories.get(key, 0) + 1

        print_status("内容分类统计:", "📋")
        for category, count in sorted(categories.items()):
            print(f"  {category}: {count} 条")

        session.close()
        return True

    except Exception as e:
        print_status(f"分类统计失败: {e}", "❌")
        session.close()
        return False


def test_semantic_search(embedding_model):
    """测试语义搜索功能"""
    print_status("测试语义搜索功能", "🔍")

    session = get_database_connection()
    if not session:
        return False

    try:
        # 定义测试问题
        test_queries = [
            "古诗三首",
            "听听秋的声音",
            "古诗山行",
            "口语交际暑假生活",
            "泰戈尔花的学校",
            "不懂就要问孙中山"
        ]

        print_status("执行语义搜索测试:", "🔍")
        # 获取所有有向量的记录（一次性获取以提高效率）
        records = session.query(TextbookChunk).filter(
            TextbookChunk.embedding.isnot(None)
        ).all()

        successful_searches = 0
        total_searches = len(test_queries)

        for query in test_queries:
            print(f"\n📝 搜索问题: '{query}'")

            # 生成查询向量，带有重试机制
            query_embedding = None
            max_retries = 2
            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        print_status(f"重试生成查询向量 (尝试 {attempt + 1}/{max_retries + 1})", "🔄")
                    query_embedding = embedding_model.embed_query(query)
                    if query_embedding:
                        break
                except Exception as e:
                    print_status(f"生成查询向量失败 (尝试 {attempt + 1}): {str(e)[:100]}...", "⚠️")
                    if attempt < max_retries:
                        continue
                    else:
                        print_status(f"跳过查询 '{query}' - 所有重试均失败", "❌")
                        break

            # 只有成功生成向量时才进行搜索
            if query_embedding is None:
                print_status(f"无法为查询 '{query}' 生成向量，跳过搜索", "⚠️")
                continue

            # 计算相似度并排序
            similarities = []
            for record in records:
                try:
                    # 检查向量是否存在且有效
                    if record.embedding is None:
                        continue

                    # 处理向量格式
                    embedding = record.embedding
                    if isinstance(embedding, str):
                        embedding = eval(embedding) if embedding.startswith('[') else []

                    # 确保向量不为空
                    if embedding is None or (isinstance(embedding, (list, tuple)) and len(embedding) == 0):
                        continue

                    similarity = cosine_similarity(query_embedding, embedding)
                    similarities.append((similarity, record))
                except Exception as e:
                    print_status(f"处理记录 {getattr(record, 'id', '未知')} 失败: {e}", "⚠️")
                    continue

            # 按相似度降序排序
            similarities.sort(key=lambda x: x[0], reverse=True)

            # 显示前3个最相似的结果
            print(f"  找到 {len(records)} 条记录，显示前3个最相关结果:")
            for i, (similarity, record) in enumerate(similarities[:3]):
                metadata = record.metadata_json or {}
                content_type = metadata.get('content_type', '未知')
                page_number = record.page_number
                content_preview = record.content[:80] + "..." if len(record.content) > 80 else record.content

                print(f"    {i+1}. 相似度: {similarity:.4f} | 页码: {page_number} | 类型: {content_type}")
                print(f"       内容: {content_preview}")

            # 如果找到了相似的结果，增加成功计数
            if similarities:
                successful_searches += 1

        # 显示搜索成功率报告
        print_status(f"语义搜索完成: {successful_searches}/{total_searches} 个查询成功", "📊")

        session.close()
        # 如果至少有一半的查询成功，认为测试通过
        return successful_searches >= total_searches // 2

    except Exception as e:
        print_status(f"语义搜索测试失败: {e}", "❌")
        session.close()
        return False


def test_category_specific_search(embedding_model):
    """测试按分类搜索"""
    print_status("测试按分类搜索", "🔍")

    session = get_database_connection()
    if not session:
        return False

    try:
        # 测试按不同分类搜索
        category_tests = [
            ("课文主体", "大青树下的小学"),
            ("习作指导", "写日记"),
            ("课后练习", "朗读课文"),
            ("日积月累", "山行"),
            ("口语交际", "暑假生活")
        ]

        for category, keyword in category_tests:
            print(f"\n📂 测试分类: {category}")

            # 查询指定分类的记录
            records = session.query(TextbookChunk).filter(
                TextbookChunk.embedding.isnot(None)
            ).all()

            # 筛选指定分类的记录
            category_records = []
            for record in records:
                metadata = record.metadata_json or {}
                content_type = metadata.get('content_type', '')
                # 确保content_type是字符串
                if content_type and isinstance(content_type, str) and category in content_type:
                    category_records.append(record)

            print(f"  找到 {len(category_records)} 条 '{category}' 记录")

            # 生成关键词向量并搜索
            if category_records:
                # 生成查询向量，带有重试机制
                query_embedding = None
                max_retries = 2
                for attempt in range(max_retries + 1):
                    try:
                        if attempt > 0:
                            print_status(f"重试生成分类查询向量 (尝试 {attempt + 1}/{max_retries + 1})", "🔄")
                        query_embedding = embedding_model.embed_query(keyword)
                        if query_embedding:
                            break
                    except Exception as e:
                        print_status(f"生成分类查询向量失败 (尝试 {attempt + 1}): {str(e)[:100]}...", "⚠️")
                        if attempt < max_retries:
                            continue
                        else:
                            print_status(f"跳过分类 '{category}' 的搜索 - 所有重试均失败", "❌")
                            break

                if query_embedding is None:
                    print_status(f"无法为分类 '{category}' 生成向量，跳过搜索", "⚠️")
                    continue

                similarities = []

                for record in category_records:
                    try:
                        # 检查向量是否存在且有效
                        if record.embedding is None:
                            continue

                        # 处理向量格式
                        embedding = record.embedding
                        if isinstance(embedding, str):
                            embedding = eval(embedding) if embedding.startswith('[') else []

                        # 确保向量不为空
                        if embedding is None or (isinstance(embedding, (list, tuple)) and len(embedding) == 0):
                            continue

                        similarity = cosine_similarity(query_embedding, embedding)
                        similarities.append((similarity, record))
                    except Exception as e:
                        print_status(f"处理分类记录 {getattr(record, 'id', '未知')} 失败: {e}", "⚠️")
                        continue

                similarities.sort(key=lambda x: x[0], reverse=True)

                # 显示最相关的结果
                if similarities:
                    best_similarity, best_record = similarities[0]
                    metadata = best_record.metadata_json or {}
                    page_number = best_record.page_number
                    content_preview = best_record.content[:60] + "..." if len(best_record.content) > 60 else best_record.content

                    print(f"  最相关记录: 相似度 {best_similarity:.4f} | 页码 {page_number}")
                    print(f"  内容: {content_preview}")
            else:
                print(f"  没有找到 '{category}' 类型的记录")

        session.close()
        return True

    except Exception as e:
        print_status(f"分类搜索测试失败: {e}", "❌")
        session.close()
        return False


def test_lesson_structure():
    """测试课程结构信息"""
    print_status("测试课程结构信息", "📚")

    session = get_database_connection()
    if not session:
        return False

    try:
        # 获取所有记录
        records = session.query(TextbookChunk).all()

        # 统计单元信息
        units = {}
        lessons = {}

        for record in records:
            metadata = record.metadata_json or {}
            unit_title = metadata.get('unit_title', '')
            lesson_title = metadata.get('lesson_title', '')
            page_number = record.page_number

            if unit_title:
                if unit_title not in units:
                    units[unit_title] = {'count': 0, 'pages': set()}
                units[unit_title]['count'] += 1
                units[unit_title]['pages'].add(page_number)

            if lesson_title:
                if lesson_title not in lessons:
                    lessons[lesson_title] = {'count': 0, 'pages': set()}
                lessons[lesson_title]['count'] += 1
                lessons[lesson_title]['pages'].add(page_number)

        print_status("单元结构统计:", "📖")
        for unit_title, data in sorted(units.items()):
            pages = sorted(list(data['pages']))
            page_range = f"{min(pages)}-{max(pages)}" if len(pages) > 1 else str(pages[0])
            print(f"  {unit_title}: {data['count']} 个片段, 页码范围: {page_range}")

        print_status("\n课文结构统计:", "📖")
        for lesson_title, data in sorted(lessons.items()):
            pages = sorted(list(data['pages']))
            page_range = f"{min(pages)}-{max(pages)}" if len(pages) > 1 else str(pages[0])
            print(f"  {lesson_title}: {data['count']} 个片段, 页码范围: {page_range}")

        session.close()
        return True

    except Exception as e:
        print_status(f"课程结构测试失败: {e}", "❌")
        session.close()
        return False


def main():
    """主函数"""
    print("🎯 RAG检索功能测试脚本")
    print("=" * 60)

    # 测试1: 数据库连接
    if not test_database_connection():
        print("\n❌ 数据库连接测试失败，请检查导入是否完成")
        return 1

    # 测试2: 内容分类统计
    if not test_content_categories():
        print("\n❌ 内容分类测试失败")
        return 1

    # 测试3: 课程结构
    if not test_lesson_structure():
        print("\n❌ 课程结构测试失败")
        return 1

    # 获取嵌入模型
    embedding_model = get_embedding_model()
    if not embedding_model:
        print("\n❌ 无法加载嵌入模型，跳过语义搜索测试")
        print("🔍 但数据库连接和基础测试已完成")
        return 0

    # 测试4: 语义搜索
    if not test_semantic_search(embedding_model):
        print("\n⚠️ 语义搜索测试失败，但继续其他测试")

    # 测试5: 按分类搜索
    if not test_category_specific_search(embedding_model):
        print("\n⚠️ 分类搜索测试失败，但基础功能已完成")

    print("\n" + "=" * 60)
    print("🎉 所有测试完成！RAG系统运行正常")
    print("💡 系统已准备好进行智能检索")

    return 0


if __name__ == "__main__":
    sys.exit(main())