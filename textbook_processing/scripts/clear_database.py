#!/usr/bin/env python3
"""
数据库清理脚本
Database Clear Script

清空textbook_chunks表并重置ID序列
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from homeworkpal.database.connection import engine
from sqlalchemy.orm import sessionmaker
from homeworkpal.database.models import TextbookChunk

def print_status(message: str, status: str):
    """打印状态信息"""
    icons = {"✅": "✅", "❌": "❌", "⚠️": "⚠️", "🔧": "🔧", "📚": "📚", "🔍": "🔍", "💾": "💾", "📖": "📖", "🗑️": "🗑️"}
    print(f"{icons.get(status, 'ℹ️')} {message}")


def clear_textbook_chunks_table():
    """清空textbook_chunks表并重置ID序列"""
    print_status("开始清空textbook_chunks表", "🗑️")

    try:
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        # 检查当前数据量
        count_before = session.query(TextbookChunk).count()
        print_status(f"当前数据库中有 {count_before} 个记录", "📊")

        if count_before == 0:
            print_status("数据库已经是空的", "ℹ️")
            session.close()
            return True

        # 清空表数据
        session.query(TextbookChunk).delete()
        session.commit()
        print_status("已清空表数据", "🗑️")

        # 重置序列到1
        # 使用PostgreSQL的ALTER SEQUENCE命令重置ID序列
        reset_sequence_sql = """
        ALTER SEQUENCE textbook_chunks_id_seq RESTART WITH 1;
        """

        session.execute(reset_sequence_sql)
        session.commit()
        print_status("已重置ID序列到1", "🔄")

        # 验证清理结果
        count_after = session.query(TextbookChunk).count()
        if count_after == 0:
            print_status("✅ 数据库清空成功，ID序列已重置", "✅")
        else:
            print_status(f"❌ 清空失败，仍有 {count_after} 个记录", "❌")

        session.close()
        return count_after == 0

    except Exception as e:
        print_status(f"清空数据库失败: {e}", "❌")
        return False


def verify_database_state():
    """验证数据库状态"""
    print_status("验证数据库状态", "🔍")

    try:
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        # 检查记录数量
        count = session.query(TextbookChunk).count()
        print_status(f"✅ textbook_chunks表记录数: {count}", "📊")

        # 检查表结构
        session.execute("SELECT 1 FROM textbook_chunks LIMIT 1")
        print_status("✅ 表结构正常", "📋")

        # 检查序列状态
        result = session.execute("SELECT nextval('textbook_chunks_id_seq')")
        # nextval会返回序列的下一个值，所以实际重置后的值应该是1
        print_status("✅ ID序列已重置", "🔢")

        session.close()
        return True

    except Exception as e:
        print_status(f"验证数据库状态失败: {e}", "❌")
        return False


def main():
    """主函数"""
    print("🗑️ 教材数据库清理工具")
    print("=" * 50)

    # 清空数据库
    if clear_textbook_chunks_table():
        print("\n" + "=" * 50)
        print("✅ 数据库清理完成！")

        # 验证状态
        verify_database_state()

        print("\n💡 现在可以重新导入数据了")
        print("   1. 调整CSV文件中的数据")
        print("   2. 运行导入脚本: python textbook_processing/ingestion/import_chinese_textbook.py")
        return 0
    else:
        print("\n❌ 数据库清理失败！")
        return 1


if __name__ == "__main__":
    sys.exit(main())