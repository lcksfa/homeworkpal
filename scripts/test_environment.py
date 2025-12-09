#!/usr/bin/env python3
"""
环境测试脚本 - 验证数据库连接和依赖
Environment test script - Verify database connection and dependencies
"""

import sys
import os
from dotenv import load_dotenv

def test_imports():
    """测试必需的包导入"""
    try:
        import sqlalchemy
        print("✅ SQLAlchemy imported successfully")

        from pgvector.sqlalchemy import Vector
        print("✅ PGVector imported successfully")

        import chainlit
        print("✅ Chainlit imported successfully")

        from fastapi import FastAPI
        print("✅ FastAPI imported successfully")

        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_database():
    """测试数据库连接"""
    try:
        from src.homeworkpal.database.connection import test_connection, init_database

        # 测试基本连接
        if test_connection():
            print("✅ Database connection successful")

            # 尝试初始化数据库（如果需要）
            try:
                init_database()
                print("✅ Database initialization successful")
            except Exception as e:
                print(f"⚠️ Database initialization warning: {e}")

            return True
        else:
            print("❌ Database connection failed")
            return False

    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_models():
    """测试数据模型"""
    try:
        from src.homeworkpal.database.models import Base, TextbookKnowledge, HomeworkSession, MistakeRecord
        print("✅ Database models imported successfully")

        # 测试模型创建
        print("✅ Models available:")
        print(f"   - TextbookKnowledge: {TextbookKnowledge.__tablename__}")
        print(f"   - HomeworkSession: {HomeworkSession.__tablename__}")
        print(f"   - MistakeRecord: {MistakeRecord.__tablename__}")

        return True
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 Testing Homework Pal Environment")
    print("=" * 50)

    # 加载环境变量
    load_dotenv()

    tests = [
        ("Package Imports", test_imports),
        ("Database Models", test_models),
        ("Database Connection", test_database)
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        result = test_func()
        results.append(result)

    print("\n" + "=" * 50)
    print("📊 Test Results:")

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("🎉 All tests passed! Environment is ready.")
        return 0
    else:
        print("⚠️ Some tests failed. Check the logs above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())