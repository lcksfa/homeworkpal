#!/usr/bin/env python3
"""
语文教材RAG搜索测试
Chinese Textbook RAG Search Test

测试语文教材的智能检索和问答功能
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
    icons = {"✅": "✅", "❌": "❌", "⚠️": "⚠️", "🔧": "🔧", "📚": "📚", "🔍": "🔍", "💾": "💾", "📖": "📖"}
    print(f"{icons.get(status, 'ℹ️')} {message}")


def test_chinese_textbook_search():
    """测试语文教材搜索功能"""
    print_status("测试语文教材内容搜索", "🔍")

    try:
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        # 测试查询列表
        test_queries = [
            "花的学校 泰戈尔",
            "孙中山 不懂就要问",
            "古诗三首 山行",
            "秋天的雨",
            "大青树下的小学",
            "口语交际",
            "语文园地",
            "习作 猜猜他是谁"
        ]

        for query in test_queries:
            print(f"\n🔍 搜索查询: {query}")
            print("-" * 50)

            # 获取所有知识片段
            chunks = session.query(TextbookChunk).all()

            # 关键词匹配搜索
            relevant_chunks = []
            query_keywords = query.split()

            for chunk in chunks:
                content_lower = chunk.content.lower()
                metadata = chunk.metadata_json or {}

                # 计算相关性得分
                relevance_score = 0
                for keyword in query_keywords:
                    keyword_lower = keyword.lower()
                    if keyword_lower in content_lower:
                        relevance_score += 1
                    # 检查元数据
                    if metadata.get('lesson_title') and keyword_lower in metadata['lesson_title'].lower():
                        relevance_score += 2  # 课文标题匹配权重更高
                    if metadata.get('unit_title') and keyword_lower in metadata['unit_title'].lower():
                        relevance_score += 1.5  # 单元标题匹配

                if relevance_score > 0:
                    relevant_chunks.append((chunk, relevance_score))

            # 按相关性排序
            relevant_chunks.sort(key=lambda x: x[1], reverse=True)

            if relevant_chunks:
                print(f"📊 找到 {len(relevant_chunks)} 个相关片段")
                for i, (chunk, score) in enumerate(relevant_chunks[:3]):  # 显示前3个最相关的
                    print(f"\n--- 相关片段 {i+1} (相关度: {score:.1f}) ---")
                    metadata = chunk.metadata_json or {}
                    print(f"📖 课文: {metadata.get('lesson_title', '未知')}")
                    print(f"📚 单元: {metadata.get('unit_title', '未知')}")
                    print(f"📄 页码: {chunk.page_number}")
                    print(f"⭐ 质量评分: {chunk.quality_score:.3f}")
                    print(f"📝 内容预览: {chunk.content[:150]}...")
            else:
                print("❌ 未找到相关内容")

        session.close()
        print_status("语文教材搜索测试完成", "✅")
        return True

    except Exception as e:
        print_status(f"语文教材搜索测试失败: {e}", "❌")
        return False


def test_lesson_structure():
    """测试课文结构化信息"""
    print_status("测试课文结构化信息", "📖")

    try:
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        # 获取所有语文教材内容
        chunks = session.query(TextbookChunk).filter(
            TextbookChunk.source_file.like('%语文%')
        ).all()

        print(f"📊 语文教材总片段数: {len(chunks)}")

        # 统计单元和课文分布
        units = {}
        lessons = {}

        for chunk in chunks:
            metadata = chunk.metadata_json or {}
            unit_title = metadata.get('unit_title', '未知单元')
            lesson_title = metadata.get('lesson_title', '未知课文')

            if unit_title not in units:
                units[unit_title] = 0
            units[unit_title] += 1

            if lesson_title not in lessons:
                lessons[lesson_title] = 0
            lessons[lesson_title] += 1

        print(f"\n📚 单元分布 ({len(units)} 个单元):")
        for unit, count in sorted(units.items()):
            print(f"  {unit}: {count} 个片段")

        print(f"\n📖 课文分布 ({len(lessons)} 篇课文):")
        for lesson, count in sorted(lessons.items()):
            if lesson != '未知课文':
                print(f"  {lesson}: {count} 个片段")

        # 显示一些详细的课文示例
        print(f"\n🔍 课文内容示例:")
        sample_chunks = chunks[:3]
        for i, chunk in enumerate(sample_chunks):
            metadata = chunk.metadata_json or {}
            print(f"\n--- 示例 {i+1} ---")
            print(f"📖 课文: {metadata.get('lesson_title', '未知')}")
            print(f"📚 单元: {metadata.get('unit_title', '未知')}")
            print(f"📄 页码: {chunk.page_number}")
            print(f"⭐ 质量评分: {chunk.quality_score:.3f}")
            print(f"📝 内容: {chunk.content}")

        session.close()
        print_status("课文结构化信息测试完成", "✅")
        return True

    except Exception as e:
        print_status(f"课文结构化信息测试失败: {e}", "❌")
        return False


def main():
    """主测试函数"""
    print("🎯 作业搭子 语文教材 RAG 系统 - 专项测试")
    print("=" * 60)

    tests = [
        ("语文教材搜索", test_chinese_textbook_search),
        ("课文结构化信息", test_lesson_structure)
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
        print("🎉 语文教材RAG功能测试全部通过！")
        print("💡 语文教材知识库已经可以支持智能问答")
        print("\n🚀 下一步建议:")
        print("  1. 集成Chainlit界面进行学生交互测试")
        print("  2. 添加问答生成功能")
        print("  3. 实现课文内容的智能推荐")
        return 0
    else:
        print("⚠️ 部分测试失败，请检查问题")
        return 1


if __name__ == "__main__":
    sys.exit(main())