#!/usr/bin/env python3
"""
浏览器自动化测试：验证前端问答功能的用户体验
"""

import asyncio
import time
from playwright.async_api import async_playwright

async def test_browser_qa():
    """使用Playwright进行浏览器测试"""

    test_cases = [
        {
            "name": "基本问候测试",
            "input": "你好",
            "expected_type": "simple_response",
            "description": "应该返回简单的问候回复，不调用API"
        },
        {
            "name": "帮助功能测试",
            "input": "帮助",
            "expected_type": "help_response",
            "description": "应该显示帮助信息，不调用API"
        },
        {
            "name": "数学问题测试",
            "input": "什么是加法？",
            "expected_type": "qa_response",
            "description": "应该调用API并返回基于教材的答案"
        },
        {
            "name": "语文问题测试",
            "input": "怎么写好作文？",
            "expected_type": "qa_response",
            "description": "应该调用API并返回基于教材的答案"
        }
    ]

    print("🌐 开始浏览器自动化测试...")
    print("📍 测试地址: http://localhost:8000")
    print("=" * 60)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # 设置为True可以无头模式运行
        page = await browser.new_page()

        try:
            # 访问前端页面
            await page.goto("http://localhost:8000")
            await page.wait_for_selector('[data-testid="input"]', timeout=10000)
            print("✅ 前端页面加载成功")

            # 等待页面完全加载
            await page.wait_for_timeout(2000)

            for i, test_case in enumerate(test_cases, 1):
                print(f"\n📝 测试 {i}/{len(test_cases)}: {test_case['name']}")
                print(f"   输入: {test_case['input']}")
                print(f"   期望: {test_case['description']}")

                try:
                    # 查找输入框（可能的选择器）
                    input_selectors = [
                        'textarea[placeholder*="消息"]',
                        'textarea[placeholder*="输入"]',
                        'textarea',
                        'input[type="text"]',
                        '[data-testid="input"]',
                        '.chat-input textarea'
                    ]

                    input_element = None
                    for selector in input_selectors:
                        try:
                            input_element = await page.wait_for_selector(selector, timeout=2000)
                            if input_element:
                                break
                        except:
                            continue

                    if not input_element:
                        print("   ❌ 找不到输入框")
                        continue

                    # 输入测试问题
                    await input_element.fill(test_case['input'])
                    await page.wait_for_timeout(500)

                    # 查找发送按钮
                    send_selectors = [
                        'button[type="submit"]',
                        'button[aria-label*="发送"]',
                        'button[title*="发送"]',
                        '.send-button',
                        '[data-testid="send"]'
                    ]

                    send_button = None
                    for selector in send_selectors:
                        try:
                            send_button = await page.wait_for_selector(selector, timeout=2000)
                            if send_button:
                                break
                        except:
                            continue

                    if send_button:
                        await send_button.click()
                    else:
                        # 如果找不到发送按钮，尝试按Enter键
                        await input_element.press("Enter")

                    # 等待响应
                    await page.wait_for_timeout(3000)

                    # 检查是否出现了"正在思考"的提示（对于问答）
                    if test_case['expected_type'] == 'qa_response':
                        thinking_indicators = [
                            "正在思考",
                            "正在处理",
                            "请稍等",
                            "思考中"
                        ]

                        page_content = await page.content()
                        has_thinking = any(indicator in page_content for indicator in thinking_indicators)

                        if has_thinking:
                            print("   ✅ 检测到'正在思考'提示")

                        # 等待更长时间让API调用完成
                        await page.wait_for_timeout(8000)

                    # 检查响应内容
                    messages = await page.query_selector_all('.message, [data-message-id], .chat-message')

                    if len(messages) >= 2:  # 至少有用户消息和AI回复
                        print(f"   ✅ 检测到 {len(messages)} 条消息")

                        # 获取最后一条AI回复
                        last_message = messages[-1]
                        message_text = await last_message.text_content()

                        if message_text:
                            print(f"   📄 回复预览: {message_text[:100]}...")

                            # 根据测试类型验证回复内容
                            if test_case['expected_type'] == 'simple_response':
                                if "小栗子" in message_text and "有什么可以帮你的吗" in message_text:
                                    print("   ✅ 简单回复验证通过")
                                else:
                                    print("   ⚠️  简单回复格式可能需要调整")

                            elif test_case['expected_type'] == 'help_response':
                                if "帮助" in message_text and "可以帮你" in message_text:
                                    print("   ✅ 帮助回复验证通过")
                                else:
                                    print("   ⚠️  帮助回复格式可能需要调整")

                            elif test_case['expected_type'] == 'qa_response':
                                if ("答案" in message_text or "💡" in message_text) and len(message_text) > 100:
                                    print("   ✅ 问答回复验证通过")
                                else:
                                    print("   ⚠️  问答回复格式可能需要调整")
                        else:
                            print("   ❌ 无法获取回复内容")
                    else:
                        print("   ❌ 未检测到预期的回复消息")

                    # 清空输入框，准备下一个测试
                    await input_element.fill("")
                    await page.wait_for_timeout(1000)

                except Exception as e:
                    print(f"   ❌ 测试执行失败: {e}")

            print(f"\n{'='*60}")
            print("🎉 浏览器测试完成！")
            print("\n📋 测试总结:")
            print("1. 基本问候和帮助功能应该在前端处理")
            print("2. 问答功能应该调用后端API")
            print("3. 应该显示'正在思考'的加载提示")
            print("4. 答案格式应该包含教材来源和鼓励话语")

        except Exception as e:
            print(f"❌ 浏览器测试失败: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_browser_qa())