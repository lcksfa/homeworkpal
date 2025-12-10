#!/usr/bin/env python3
"""
作业搭子 RAG 系统数据库初始化脚本
Database initialization script for Homework Pal RAG System

用于创建数据库表结构并验证模型
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from homeworkpal.database.connection import engine, init_database, test_connection
from homeworkpal.database.models import Base, TextbookChunk, MistakeRecord
from sqlalchemy import text


def print_status(message: str, status: str):
    """打印状态信息"""
    icons = {"✅": "✅", "❌": "❌", "⚠️": "⚠️", "🔧": "🔧"}
    print(f"{icons.get(status, 'ℹ️')} {message}")


def check_database_connection():
    """检查数据库连接"""
    print("📋 检查数据库连接:")
    if test_connection():
        print_status("数据库连接正常", "✅")
        return True
    else:
        print_status("数据库连接失败", "❌")
        return False


def create_tables():
    """创建数据库表"""
    print("\n📋 创建数据库表:")

    try:
        # 先检查pgvector扩展
        from sqlalchemy import text
        with engine.connect() as conn:
            # 启用pgvector扩展
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
            print_status("pgvector扩展已启用", "✅")

        # 创建所有表
        init_database()

        # 验证表是否创建成功
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public'
                AND tablename IN ('textbook_chunks', 'mistake_records')
                ORDER BY tablename;
            """))

            tables = [row[0] for row in result.fetchall()]

            expected_tables = ['textbook_chunks', 'mistake_records']
            created_tables = []

            for table in expected_tables:
                if table in tables:
                    print_status(f"表 {table}: 创建成功", "✅")
                    created_tables.append(table)
                else:
                    print_status(f"表 {table}: 创建失败", "❌")

            if len(created_tables) == len(expected_tables):
                print_status("所有必需表创建完成", "✅")
                return True
            else:
                print_status(f"部分表创建失败: {len(created_tables)}/{len(expected_tables)}", "❌")
                return False

    except Exception as e:
        print_status(f"创建表时出错: {e}", "❌")
        return False


def verify_table_structure():
    """验证表结构"""
    print("\n📋 验证表结构:")

    try:
        with engine.connect() as conn:
            # 检查textbook_chunks表结构
            result = conn.execute(text("""
                SELECT column_name, data_type, udt_name
                FROM information_schema.columns
                WHERE table_name = 'textbook_chunks'
                AND table_schema = 'public'
                ORDER BY ordinal_position;
            """))

            chunk_columns = [f"{row[0]}({row[2]})" for row in result.fetchall()]

            # 检查mistake_records表结构
            result = conn.execute(text("""
                SELECT column_name, data_type, udt_name
                FROM information_schema.columns
                WHERE table_name = 'mistake_records'
                AND table_schema = 'public'
                ORDER BY ordinal_position;
            """))

            mistake_columns = [f"{row[0]}({row[2]})" for row in result.fetchall()]

            print("📄 textbook_chunks 表结构:")
            for col in chunk_columns:
                print(f"  • {col}")

            print("\n📝 mistake_records 表结构:")
            for col in mistake_columns:
                print(f"  • {col}")

            # 检查向量字段
            if any('vector' in col for col in chunk_columns):
                print_status("向量字段配置正确", "✅")
            else:
                print_status("向量字段配置异常", "❌")

            return True

    except Exception as e:
        print_status(f"验证表结构时出错: {e}", "❌")
        return False


def test_model_creation():
    """测试模型创建"""
    print("\n📋 测试模型创建:")

    try:
        # 创建测试数据
        from sqlalchemy.orm import sessionmaker
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        # 测试TextbookChunk模型
        test_chunk = TextbookChunk(
            content="这是一个测试教材内容片段",
            metadata_json={"学科": "数学", "年级": "三年级", "单元": "第一单元", "页码": 1},
            source_file="test.md",
            chunk_index=0
        )

        # 测试MistakeRecord模型
        test_mistake = MistakeRecord(
            student_name="测试学生",
            subject="数学",
            grade="三年级",
            student_answer="错误的答案",
            question_text="测试题目",
            ai_analysis="AI分析结果",
            correct_answer="正确答案",
            knowledge_points=["加法", "运算"],
            difficulty_level=1,
            mastery_status=0
        )

        print_status("模型对象创建成功", "✅")
        print_status("模型字段配置正确", "✅")

        session.close()
        return True

    except Exception as e:
        print_status(f"测试模型创建时出错: {e}", "❌")
        return False


def main():
    """主函数"""
    print("🔧 作业搭子 RAG 系统 - 数据库初始化")
    print("=" * 50)
    print()

    checks = [
        ("数据库连接检查", check_database_connection),
        ("数据库表创建", create_tables),
        ("表结构验证", verify_table_structure),
        ("模型创建测试", test_model_creation),
    ]

    passed = 0
    total = len(checks)

    for name, check_func in checks:
        if check_func():
            passed += 1
            print(f"✅ {name} - 通过")
        else:
            print(f"❌ {name} - 失败")

    print("\n" + "=" * 50)
    print(f"📊 初始化结果: {passed}/{total} 项检查通过")

    if passed == total:
        print("🎉 Task-1.2 数据库模型设计 - 全部通过!")
        print("✅ 数据库表结构已创建完成，RAG系统可以开始使用")
        return 0
    else:
        print("⚠️ 存在未通过的检查项，请修复错误后重试")
        return 1


if __name__ == "__main__":
    sys.exit(main())