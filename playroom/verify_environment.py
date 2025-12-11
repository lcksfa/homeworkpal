#!/usr/bin/env python3
"""
作业搭子 RAG 系统环境验证脚本
Environment Verification Script for Homework Pal RAG System

用于验证 Task-1.1 项目初始化与环境配置的完成情况
"""

import sys
import os
import subprocess
import importlib
from pathlib import Path


def print_status(message: str, status: str):
    """打印状态信息"""
    icons = {"✅": "✅", "❌": "❌", "⚠️": "⚠️", "🔧": "🔧"}
    print(f"{icons.get(status, 'ℹ️')} {message}")


def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        print_status(f"Python版本: {version.major}.{version.minor}.{version.micro} (符合要求 >=3.11)", "✅")
        return True
    else:
        print_status(f"Python版本: {version.major}.{version.minor}.{version.micro} (不符合要求，需要 >=3.11)", "❌")
        return False


def check_uv_package_manager():
    """检查uv包管理器"""
    try:
        result = subprocess.run(['uv', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print_status(f"uv包管理器: {result.stdout.strip()}", "✅")
            return True
        else:
            print_status("uv包管理器未安装或不可用", "❌")
            return False
    except FileNotFoundError:
        print_status("uv包管理器未找到", "❌")
        return False


def check_dependencies():
    """检查关键依赖包"""
    critical_deps = [
        'chainlit', 'fastapi', 'uvicorn', 'psycopg', 'pgvector',
        'sqlalchemy', 'langchain', 'openai', 'dashscope'
    ]

    failed_deps = []
    for dep in critical_deps:
        try:
            importlib.import_module(dep)
            print_status(f"依赖包 {dep}: 已安装", "✅")
        except ImportError:
            failed_deps.append(dep)
            print_status(f"依赖包 {dep}: 未安装", "❌")

    return len(failed_deps) == 0


def check_database_connection():
    """检查PostgreSQL数据库连接"""
    try:
        import psycopg

        # 测试连接
        conn_str = 'postgresql://homeworkpal:password@localhost:5432/homeworkpal'
        conn = psycopg.connect(conn_str)

        # 检查pgvector扩展
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
            if cur.fetchone():
                print_status("PostgreSQL + pgvector扩展: 连接成功", "✅")
            else:
                print_status("PostgreSQL连接成功，但缺少pgvector扩展", "⚠️")

        conn.close()
        return True

    except Exception as e:
        print_status(f"数据库连接失败: {e}", "❌")
        return False


def check_environment_file():
    """检查.env配置文件"""
    env_file = Path('.env')
    if not env_file.exists():
        print_status(".env文件不存在", "❌")
        return False

    print_status(".env文件存在", "✅")

    # 检查关键配置
    required_vars = ['DATABASE_URL', 'DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    configured_vars = []
    missing_vars = []

    # 加载环境变量
    from dotenv import load_dotenv
    load_dotenv('.env')

    for var in required_vars:
        value = os.getenv(var)
        if value:
            configured_vars.append(var)
        else:
            missing_vars.append(var)

    if missing_vars:
        print_status(f"缺少环境变量: {', '.join(missing_vars)}", "❌")
        return False
    else:
        print_status(f"关键环境变量已配置: {', '.join(configured_vars)}", "✅")

    # 检查API密钥
    api_keys = ['DASHSCOPE_API_KEY', 'DEEPSEEK_API_KEY', 'OPENAI_API_KEY']
    configured_apis = []

    for key in api_keys:
        value = os.getenv(key, '')
        if value and 'your_' not in value:
            configured_apis.append(key)

    if configured_apis:
        print_status(f"已配置API密钥: {', '.join(configured_apis)}", "✅")
    else:
        print_status("未配置任何API密钥（占位符值）", "⚠️")

    return True


def check_project_structure():
    """检查项目结构"""
    required_files = [
        'pyproject.toml', '.env', 'init.sh', 'verify_environment.py',
        'homeworkpal/__init__.py', 'homeworkpal/database/__init__.py',
        'homeworkpal/api/main.py', 'homeworkpal/frontend/app.py'
    ]

    missing_files = []
    for file in required_files:
        if Path(file).exists():
            print_status(f"文件 {file}: 存在", "✅")
        else:
            missing_files.append(file)
            print_status(f"文件 {file}: 不存在", "❌")

    return len(missing_files) == 0


def check_postgres_container():
    """检查PostgreSQL Docker容器状态"""
    try:
        result = subprocess.run(
            ['docker', 'ps', '--filter', 'name=homework-pal-postgres', '--format', '{{.Status}}'],
            capture_output=True, text=True
        )

        if result.returncode == 0 and result.stdout.strip():
            print_status(f"PostgreSQL Docker容器: {result.stdout.strip()}", "✅")
            return True
        else:
            print_status("PostgreSQL Docker容器未运行", "❌")
            return False

    except FileNotFoundError:
        print_status("Docker未安装或不可用", "❌")
        return False


def main():
    """主验证函数"""
    print("🔧 作业搭子 RAG 系统 - 环境验证")
    print("=" * 50)
    print()

    checks = [
        ("Python版本检查", check_python_version),
        ("uv包管理器检查", check_uv_package_manager),
        ("依赖包检查", check_dependencies),
        ("项目结构检查", check_project_structure),
        ("环境配置检查", check_environment_file),
        ("PostgreSQL容器检查", check_postgres_container),
        ("数据库连接检查", check_database_connection),
    ]

    passed = 0
    total = len(checks)

    for name, check_func in checks:
        print(f"\n📋 {name}:")
        if check_func():
            passed += 1
            print(f"✅ {name} - 通过")
        else:
            print(f"❌ {name} - 失败")

    print("\n" + "=" * 50)
    print(f"📊 验证结果: {passed}/{total} 项检查通过")

    if passed == total:
        print("🎉 Task-1.1 项目初始化与环境配置 - 全部通过!")
        print("✅ 环境已准备好进入下一个开发阶段")
        return 0
    else:
        print("⚠️ 存在未通过的检查项，请完成配置后再继续")
        return 1


if __name__ == "__main__":
    sys.exit(main())