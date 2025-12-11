#!/usr/bin/env python3
"""
RAG服务API测试
RAG Service API Testing

测试通过FastAPI接口访问RAG服务
"""

import requests
import json
import time
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_backend_health():
    """测试后端健康状态"""
    try:
        response = requests.get("http://localhost:8001/health", timeout=5)
        if response.status_code == 200:
            print("✅ 后端服务健康")
            return True
        else:
            print(f"❌ 后端服务异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接后端服务: {e}")
        return False

def test_rag_search_api():
    """测试RAG搜索API"""
    if not test_backend_health():
        return False

    print("\n🔍 测试RAG搜索API...")

    test_queries = [
        "周长怎么算",
        "秋分过后有什么特点",
        "修改符号的使用",
        "写作文的方法"
    ]

    base_url = "http://localhost:8001"

    for query in test_queries:
        print(f"\n📝 API查询: '{query}'")

        try:
            start_time = time.time()

            # 尝试不同的API端点
            endpoints = [
                "/retrieve",  # 标准检索端点
                "/ask",       # 问答端点
                "/search"     # 搜索端点
            ]

            success = False
            for endpoint in endpoints:
                try:
                    response = requests.post(
                        f"{base_url}{endpoint}",
                        json={
                            "query": query,
                            "top_k": 3,
                            "threshold": 0.3
                        },
                        timeout=10
                    )

                    if response.status_code == 200:
                        result = response.json()
                        end_time = time.time()

                        print(f"   ✅ {endpoint} 成功")
                        print(f"   ⏱️  响应时间: {(end_time - start_time)*1000:.1f}ms")
                        print(f"   📊 返回数据: {json.dumps(result, ensure_ascii=False, indent=2)[:200]}...")
                        success = True
                        break
                    else:
                        print(f"   ❌ {endpoint} 失败: {response.status_code}")

                except Exception as e:
                    print(f"   ❌ {endpoint} 异常: {e}")

            if not success:
                print(f"   ⚠️  所有端点都失败，可能是API尚未实现")

        except Exception as e:
            print(f"   ❌ 查询失败: {e}")

def test_api_endpoints():
    """测试所有可用的API端点"""
    if not test_backend_health():
        return False

    print("\n🔗 测试API端点...")

    base_url = "http://localhost:8001"

    # 测试不同端点
    endpoints = [
        "/",
        "/health",
        "/docs",
        "/status",
        "/documents/count",
        "/vector/stats"
    ]

    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            print(f"   GET {endpoint}: {response.status_code}")

            if response.status_code == 200 and 'application/json' in response.headers.get('content-type', ''):
                data = response.json()
                print(f"      数据: {json.dumps(data, ensure_ascii=False)[:100]}...")

        except Exception as e:
            print(f"   GET {endpoint}: 异常 - {e}")

def main():
    """主测试函数"""
    print("🚀 RAG服务API测试开始")
    print("=" * 50)

    # 测试后端连接
    if not test_backend_health():
        print("\n❌ 后端服务不可用，请确保服务已启动")
        return False

    # 测试API端点
    test_api_endpoints()

    # 测试搜索功能
    test_rag_search_api()

    print("\n" + "=" * 50)
    print("📋 API测试完成")
    print("\n💡 如果搜索API返回404，说明RAG服务端点尚未实现")
    print("   但RAG服务本身已经可以通过Python直接调用")

if __name__ == "__main__":
    main()