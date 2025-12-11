#!/usr/bin/env python3
"""
测试前端问答功能的集成
"""

import asyncio
import aiohttp
import json
import time

async def test_qa_integration():
    """测试问答功能集成"""

    # 测试问题列表
    test_questions = [
        "什么是加法？",
        "怎么写好作文？",
        "语文学习要注意什么？",
        "数学中的减法是什么？",
        "你好",
        "帮助"
    ]

    base_url = "http://localhost:8001"

    print("🧪 开始测试前端问答功能集成...")
    print(f"后端API地址: {base_url}")
    print(f"前端地址: http://localhost:8000")
    print("-" * 50)

    async with aiohttp.ClientSession() as session:
        # 首先检查后端健康状态
        try:
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"✅ 后端健康检查: {health_data['status']}")
                else:
                    print(f"❌ 后端健康检查失败: {response.status}")
                    return
        except Exception as e:
            print(f"❌ 无法连接到后端: {e}")
            return

        # 测试每个问题
        for i, question in enumerate(test_questions, 1):
            print(f"\n📝 测试问题 {i}: {question}")

            # 检测学科类型（模拟前端逻辑）
            math_keywords = ["加法", "减法", "乘法", "除法", "计算", "等于", "数字", "算术"]
            chinese_keywords = ["汉字", "拼音", "造句", "作文", "阅读", "古诗", "词语", "语文"]

            subject = None
            if any(keyword in question for keyword in math_keywords):
                subject = "数学"
            elif any(keyword in question for keyword in chinese_keywords):
                subject = "语文"

            print(f"   检测学科: {subject or '未检测到'}")

            # 调用API
            start_time = time.time()
            try:
                payload = {
                    "question": question,
                    "grade": "三年级",
                    "subject": subject,
                    "max_context_length": 3000,
                    "temperature": 0.7,
                    "max_tokens": 800
                }

                async with session.post(
                    f"{base_url}/api/ask",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:

                    response_time = time.time() - start_time

                    if response.status == 200:
                        data = await response.json()
                        answer = data.get("answer", "")
                        sources = data.get("sources", [])
                        context_used = data.get("context_used", False)
                        api_response_time = data.get("response_time", 0)

                        print(f"   ✅ 请求成功")
                        print(f"   🕐 API响应时间: {api_response_time:.2f}秒")
                        print(f"   🕐 总耗时: {response_time:.2f}秒")
                        print(f"   📚 使用上下文: {context_used}")
                        print(f"   📖 来源数量: {len(sources)}")
                        print(f"   💬 答案长度: {len(answer)}字符")

                        # 显示答案预览（前100字符）
                        answer_preview = answer[:100] + "..." if len(answer) > 100 else answer
                        print(f"   📄 答案预览: {answer_preview}")

                    else:
                        error_data = await response.text()
                        print(f"   ❌ 请求失败: {response.status}")
                        print(f"   📄 错误信息: {error_data}")

            except asyncio.TimeoutError:
                print(f"   ⏰ 请求超时")
            except Exception as e:
                print(f"   ❌ 请求异常: {e}")

    print(f"\n{'='*50}")
    print("🎉 测试完成！")
    print("\n📋 接下来请进行浏览器测试:")
    print("1. 打开 http://localhost:8000")
    print("2. 在聊天框中输入测试问题")
    print("3. 观察前端界面和响应效果")
    print("4. 检查'正在思考'加载提示是否正常")
    print("5. 验证答案格式和鼓励话语")

if __name__ == "__main__":
    asyncio.run(test_qa_integration())