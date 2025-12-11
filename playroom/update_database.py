#!/usr/bin/env python3
"""
数据库更新脚本
Database Update Script

添加新的字段到textbook_chunks表
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
from sqlalchemy import text

def update_database():
    """更新数据库结构"""
    print("🔧 更新数据库结构")
    print("=" * 40)

    try:
        with engine.connect() as conn:
            # 检查是否已存在content_hash字段
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'textbook_chunks' AND column_name = 'content_hash'
            """))

            has_content_hash = result.fetchone() is not None

            if not has_content_hash:
                print("📝 添加content_hash字段...")
                conn.execute(text("""
                    ALTER TABLE textbook_chunks
                    ADD COLUMN content_hash VARCHAR(64)
                """))
                print("✅ content_hash字段添加成功")
            else:
                print("✅ content_hash字段已存在")

            # 检查是否已存在page_number字段
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'textbook_chunks' AND column_name = 'page_number'
            """))

            has_page_number = result.fetchone() is not None

            if not has_page_number:
                print("📝 添加page_number字段...")
                conn.execute(text("""
                    ALTER TABLE textbook_chunks
                    ADD COLUMN page_number INTEGER
                """))
                print("✅ page_number字段添加成功")
            else:
                print("✅ page_number字段已存在")

            # 检查是否已存在quality_score字段
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'textbook_chunks' AND column_name = 'quality_score'
            """))

            has_quality_score = result.fetchone() is not None

            if not has_quality_score:
                print("📝 添加quality_score字段...")
                conn.execute(text("""
                    ALTER TABLE textbook_chunks
                    ADD COLUMN quality_score FLOAT DEFAULT 1.0
                """))
                print("✅ quality_score字段添加成功")
            else:
                print("✅ quality_score字段已存在")

            # 创建content_hash唯一索引（如果不存在）
            result = conn.execute(text("""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = 'textbook_chunks' AND indexname = 'ix_textbook_chunks_content_hash'
            """))

            has_index = result.fetchone() is not None

            if not has_index:
                print("📝 创建content_hash唯一索引...")
                conn.execute(text("""
                    CREATE UNIQUE INDEX ix_textbook_chunks_content_hash
                    ON textbook_chunks (content_hash)
                """))
                print("✅ 索引创建成功")
            else:
                print("✅ content_hash索引已存在")

            conn.commit()
            print("🎉 数据库更新完成！")
            return True

    except Exception as e:
        print(f"❌ 数据库更新失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = update_database()
    if success:
        print("\n✅ 数据库结构已更新，现在可以运行入库脚本")
    else:
        print("\n❌ 数据库更新失败")
        sys.exit(1)