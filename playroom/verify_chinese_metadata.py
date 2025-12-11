#!/usr/bin/env python3
"""
验证语文教材元数据结构
Verify Chinese Textbook Metadata Structure
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
import json

def print_status(message: str, status: str):
    """打印状态信息"""
    icons = {"✅": "✅", "❌": "❌", "⚠️": "⚠️", "🔧": "🔧", "📚": "📚", "🔍": "🔍", "💾": "💾", "📖": "📖"}
    print(f"{icons.get(status, 'ℹ️')} {message}")


def verify_metadata_structure():
    """验证元数据结构"""
    print_status("验证语文教材元数据结构", "📊")

    try:
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        # 获取语文教材内容
        chunks = session.query(TextbookChunk).filter(
            TextbookChunk.source_file.like('%语文%')
        ).order_by(TextbookChunk.page_number).all()

        print(f"📊 总片段数: {len(chunks)}")

        # 统计正确的单元和课文信息
        units = {}
        lessons = {}

        for chunk in chunks:
            metadata = chunk.metadata_json or {}

            unit_title = metadata.get('unit_title', '未知单元')
            lesson_title = metadata.get('lesson_title', '未知课文')

            # 只统计有意义的单元和课文标题
            if unit_title and unit_title != '未知单元' and '第' in unit_title and '单元' in unit_title:
                if unit_title not in units:
                    units[unit_title] = 0
                units[unit_title] += 1

            if lesson_title and lesson_title != '未知课文' and len(lesson_title) < 20:  # 过滤掉过长的标题
                if lesson_title not in lessons:
                    lessons[lesson_title] = 0
                lessons[lesson_title] += 1

        print(f"\n📚 单元分布 ({len(units)} 个单元):")
        for unit, count in sorted(units.items()):
            print(f"  {unit}: {count} 个片段")

        print(f"\n📖 课文分布 ({len(lessons)} 篇课文):")
        for lesson, count in sorted(lessons.items()):
            print(f"  {lesson}: {count} 个片段")

        # 显示几个具体的元数据示例
        print(f"\n🔍 元数据示例:")
        sample_chunks = [c for c in chunks if c.metadata_json.get('lesson_title')][:5]

        for i, chunk in enumerate(sample_chunks):
            metadata = chunk.metadata_json or {}
            print(f"\n--- 示例 {i+1} ---")
            print(f"📄 页码: {chunk.page_number}")
            print(f"📚 单元: {metadata.get('unit_title', '未知')}")
            print(f"📖 课文: {metadata.get('lesson_title', '未知')}")
            print(f"📝 内容类型: {metadata.get('content_type', '未知')}")
            print(f"⭐ 质量评分: {metadata.get('quality_details', {}).get('score', 0):.3f}")
            print(f"📋 内容预览: {chunk.content[:100]}...")

        session.close()
        print_status("元数据结构验证完成", "✅")
        return True

    except Exception as e:
        print_status(f"元数据结构验证失败: {e}", "❌")
        return False


def main():
    """主函数"""
    print("🎯 语文教材元数据结构验证")
    print("=" * 50)

    if verify_metadata_structure():
        print("\n🎉 元数据结构验证通过！")
        print("💡 语文教材数据结构完整，可以进行智能检索")
        return 0
    else:
        print("\n⚠️ 元数据结构验证失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())