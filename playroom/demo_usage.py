#!/usr/bin/env python3
"""
作业搭子问答功能演示脚本
展示完整的前后端集成效果
"""

import asyncio
import aiohttp
import json
import time

async def demo_qa_functionality():
    """演示问答功能的完整流程"""

    print("🎓 作业搭子 - AI问答功能演示")
    print("=" * 50)
    print("📍 前端地址: http://localhost:8000")
    print("📍 后端API: http://localhost:8001")
    print("=" * 50)

    base_url = "http://localhost:8001"

    demo_questions = [
        {
            "category": "数学问题",
            "questions": [
                "什么是加法？",
                "数学中的减法是什么？",
                "怎么计算乘法？"
            ]
        },
        {
            "category": "语文问题",
            "questions": [
                "怎么写好作文？",
                "语文学习要注意什么？",
                "怎么提高阅读能力？"
            ]
        },
        {
            "category": "综合问题",
            "questions": [
                "学习习惯怎么培养？",
                "遇到难题怎么办？"
            ]
        }
    ]

    async with aiohttp.ClientSession() as session:
        # 检查系统状态
        try:
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    health = await response.json()
                    print(f"✅ 系统状态: {health['status']}")
                else:
                    print(f"❌ 系统状态异常: {response.status}")
                    return

            async with session.get(f"{base_url}/api/qa/status") as response:
                if response.status == 200:
                    status = await response.json()
                    llm_info = status['components']['llm_service']['model_info']
                    print(f"🤖 AI模型: {llm_info['model_name']}")
                    print(f"🔗 服务商: {llm_info['provider']}")
                else:
                    print("❌ 问答服务状态异常")
                    return

        except Exception as e:
            print(f"❌ 无法连接到后端服务: {e}")
            return

        print("\n" + "=" * 50)
        print("🚀 开始问答演示")
        print("=" * 50)

        for category_group in demo_questions:
            category = category_group["category"]
            questions = category_group["questions"]

            print(f"\n📚 {category}")
            print("-" * 30)

            for i, question in enumerate(questions, 1):
                print(f"\n问题 {i}: {question}")
                print("⏳ 正在处理...")

                start_time = time.time()

                try:
                    # 检测学科类型
                    math_keywords = ["加法", "减法", "乘法", "除法", "计算", "数学"]
                    chinese_keywords = ["语文", "作文", "阅读", "学习", "习惯"]

                    subject = None
                    if any(keyword in question for keyword in math_keywords):
                        subject = "数学"
                    elif any(keyword in question for keyword in chinese_keywords):
                        subject = "语文"

                    # 调用问答API
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

                            print(f"✅ 回答成功 (耗时: {response_time:.1f}秒)")
                            print(f"📖 使用教材: {'是' if context_used else '否'}")
                            print(f"📚 来源数量: {len(sources)}")

                            # 显示答案预览
                            answer_preview = answer.replace('\n', ' ')[:150] + "..."
                            print(f"💬 答案预览: {answer_preview}")

                            # 显示教材来源（如果有）
                            if sources:
                                print("📄 教材来源:")
                                for j, source in enumerate(sources[:2], 1):
                                    metadata = source.get("metadata", {})
                                    page = metadata.get("page", "未知")
                                    subject = metadata.get("subject", "未知")
                                    print(f"   {j}. {subject} 第{page}页")

                        else:
                            print(f"❌ 请求失败: {response.status}")
                            error_text = await response.text()
                            print(f"   错误: {error_text}")

                except asyncio.TimeoutError:
                    print(f"⏰ 请求超时")
                except Exception as e:
                    print(f"❌ 处理异常: {e}")

                # 间隔时间，避免请求过快
                await asyncio.sleep(1)

        print("\n" + "=" * 50)
        print("🎉 演示完成！")
        print("\n🌟 功能亮点:")
        print("✅ 基于人教版教材的智能问答")
        print("✅ 学科自动识别和过滤")
        print("✅ 三年级学生友好的回答风格")
        print("✅ 教材来源溯源和标注")
        print("✅ 鼓励性和教育性语言")
        print("✅ 完整的错误处理机制")

        print("\n📱 前端使用指南:")
        print("1. 打开 http://localhost:8000")
        print("2. 在聊天框直接输入学习问题")
        print("3. 观察小栗子老师的'正在思考'提示")
        print("4. 获得基于教材的详细答案和鼓励")
        print("5. 查看教材来源和学习建议")

if __name__ == "__main__":
    asyncio.run(demo_qa_functionality())