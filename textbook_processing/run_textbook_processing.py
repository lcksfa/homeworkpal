#!/usr/bin/env python3
"""
Textbook Processing Main Entry Point
教材处理主入口脚本

提供统一的命令行界面来运行各种教材处理任务
"""

import os
import sys
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

def print_status(message: str, status: str):
    """打印状态信息"""
    icons = {"✅": "✅", "❌": "❌", "⚠️": "⚠️", "🔧": "🔧", "📚": "📚", "🔍": "🔍", "💾": "💾", "📖": "📖"}
    print(f"{icons.get(status, 'ℹ️')} {message}")


def run_basic_ingestion():
    """运行基础教材导入"""
    print_status("运行基础教材导入", "🚀")
    try:
        os.system(f"cd {project_root} && python textbook_processing/ingestion/ingest_textbooks.py")
        return True
    except Exception as e:
        print_status(f"基础导入失败: {e}", "❌")
        return False


def run_enhanced_ingestion():
    """运行增强教材导入"""
    print_status("运行增强教材导入", "🚀")
    try:
        os.system(f"cd {project_root} && python textbook_processing/ingestion/ingest_textbooks_enhanced.py")
        return True
    except Exception as e:
        print_status(f"增强导入失败: {e}", "❌")
        return False


def run_structured_ingestion():
    """运行结构化教材导入"""
    print_status("运行结构化教材导入", "🚀")
    try:
        os.system(f"cd {project_root} && python textbook_processing/ingestion/ingest_textbooks_structured.py")
        return True
    except Exception as e:
        print_status(f"结构化导入失败: {e}", "❌")
        return False


def run_chinese_processing():
    """运行中文教材处理流程"""
    print_status("运行中文教材处理流程", "🚀")
    try:
        # 1. PDF处理
        print_status("步骤1: PDF处理", "📖")
        os.system(f"cd {project_root} && python textbook_processing/pdf_processing/process_chinese_textbook.py")

        # 2. 导出CSV
        print_status("步骤2: 导出CSV", "📊")
        os.system(f"cd {project_root} && python textbook_processing/export/export_textbook_to_csv.py")

        # 3. 向量化导入
        print_status("步骤3: 向量化导入", "🔮")
        os.system(f"cd {project_root} && python textbook_processing/ingestion/import_chinese_textbook.py")

        return True
    except Exception as e:
        print_status(f"中文处理流程失败: {e}", "❌")
        return False


def run_tests():
    """运行测试"""
    print_status("运行教材处理测试", "🧪")
    try:
        # 向量化测试
        print_status("运行向量化测试", "🔍")
        os.system(f"cd {project_root} && python textbook_processing/tests/test_chinese_vectorize.py")

        # 检索测试
        print_status("运行检索测试", "🔍")
        os.system(f"cd {project_root} && python textbook_processing/tests/test_chinese_search.py")

        return True
    except Exception as e:
        print_status(f"测试失败: {e}", "❌")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="教材处理工具")
    parser.add_argument(
        "command",
        choices=["basic", "enhanced", "structured", "chinese", "test"],
        help="要执行的命令"
    )

    args = parser.parse_args()

    print("🎯 教材处理工具")
    print("=" * 50)

    success = False
    if args.command == "basic":
        success = run_basic_ingestion()
    elif args.command == "enhanced":
        success = run_enhanced_ingestion()
    elif args.command == "structured":
        success = run_structured_ingestion()
    elif args.command == "chinese":
        success = run_chinese_processing()
    elif args.command == "test":
        success = run_tests()

    if success:
        print("\n✅ 任务执行完成！")
        return 0
    else:
        print("\n❌ 任务执行失败！")
        return 1


if __name__ == "__main__":
    sys.exit(main())