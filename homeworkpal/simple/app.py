#!/usr/bin/env python3
"""
Homework Pal Chainlit Application (Simplified Version)
基础的交互界面，集成RAG问答功能
"""

import chainlit as cl
from typing import Optional
import os
import asyncio
import aiohttp
import json
from datetime import datetime
from dotenv import load_dotenv

from homeworkpal.utils.logger import get_simple_logger

# Load environment variables
load_dotenv()

# Initialize logger
logger = get_simple_logger()

# Backend API configuration
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8001")

async def call_backend_api(question: str, subject: str = None, grade: str = "三年级") -> dict:
    """
    调用后端RAG问答API

    Args:
        question: 学生的问题
        subject: 学科（数学、语文等）
        grade: 年级（默认三年级）

    Returns:
        API响应数据
    """
    api_url = f"{BACKEND_API_URL}/api/ask"
    payload = {
        "question": question,
        "grade": grade,
        "subject": subject,
        "max_context_length": 3000,
        "temperature": 0.7,
        "max_tokens": 800
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                api_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_data = await response.text()
                    logger.error(f"API请求失败: {response.status} - {error_data}")
                    return None
    except asyncio.TimeoutError:
        logger.error("API请求超时")
        return None
    except Exception as e:
        logger.error(f"API请求异常: {e}")
        return None


def format_answer_display(answer_data: dict) -> str:
    """
    格式化答案显示，包含来源信息和教学风格

    Args:
        answer_data: API返回的答案数据

    Returns:
        格式化后的显示文本
    """
    if not answer_data:
        return "抱歉，我现在无法回答这个问题。请稍后再试或换个问题问问吧！"

    answer = answer_data.get("answer", "")
    sources = answer_data.get("sources", [])
    response_time = answer_data.get("response_time", 0)
    context_used = answer_data.get("context_used", False)
    metadata = answer_data.get("metadata", {})

    # 构建答案显示
    display_parts = []

    # 主要答案
    if answer:
        display_parts.append(f"💡 **答案**\n{answer}")

    # 教材来源信息
    if sources and context_used:
        display_parts.append("\n📚 **教材来源**")
        for i, source in enumerate(sources[:3], 1):  # 最多显示3个来源
            source_text = source.get("text", "")[:100] + "..." if len(source.get("text", "")) > 100 else source.get("text", "")
            page_info = source.get("metadata", {}).get("page", "")
            subject_info = source.get("metadata", {}).get("subject", "")

            if page_info:
                source_info = f"第{page_info}页"
            else:
                source_info = "相关内容"

            if subject_info:
                source_info = f"{subject_info} {source_info}"

            display_parts.append(f"{i}. {source_info}")

    # 添加鼓励话语
    display_parts.append(f"\n✨ **小栗子说**\n希望这个答案对你有帮助！如果还有不明白的地方，可以继续问我哦！学习就是这样，一点一滴积累，你会越来越棒的！🌟")

    # 添加响应时间（调试用，可选显示）
    if response_time > 0:
        logger.info(f"问答响应时间: {response_time:.2f}秒")

    return "\n".join(display_parts)


def detect_subject_from_question(question: str) -> Optional[str]:
    """
    从问题中检测学科类型

    Args:
        question: 学生的问题

    Returns:
        检测到的学科（数学、语文等）
    """
    question_lower = question.lower()

    # 数学关键词
    math_keywords = ["加法", "减法", "乘法", "除法", "计算", "等于", "数字", "算术", "几何", "图形", "面积", "周长"]
    # 语文关键词
    chinese_keywords = ["汉字", "拼音", "造句", "作文", "阅读", "古诗", "词语", "近义词", "反义词", "标点", "句子"]
    # 英语关键词
    english_keywords = ["english", "单词", "翻译", "hello", "apple", "banana", "英语"]

    if any(keyword in question for keyword in math_keywords):
        return "数学"
    elif any(keyword in question for keyword in chinese_keywords):
        return "语文"
    elif any(keyword in question for keyword in english_keywords):
        return "英语"

    return None


@cl.on_chat_start
async def on_chat_start():
    """Initialize chat session"""
    # Send welcome message
    welcome_message = """
👋 嗨！我是你的作业搭子小栗子！🌰
今天我们也要一起消灭作业怪兽哦！

👇 你可以：
🤔 **提问学习** - 直接问我学习上的问题，我会帮你找答案！
📸 检查作业 - 上传作业照片，我来帮你检查
📅 整理清单 - 告诉我今天的作业内容
📕 复习错题 - 查看你的错题本

💡 **试试问我这些**：
- "什么是加法？"
- "怎么写好作文？"
- "这个字怎么读？"
"""

    await cl.Message(
        content=welcome_message,
        author="小栗子"
    ).send()

    # Add action buttons (Chainlit 2.x compatible)
    actions = [
        cl.Action(
            name="ask_question",
            payload={"action": "ask"},
            label="🤔 提问学习"
        ),
        cl.Action(
            name="check_homework",
            payload={"action": "check"},
            label="📸 检查作业"
        ),
        cl.Action(
            name="create_planner",
            payload={"action": "planner"},
            label="📅 整理清单"
        ),
        cl.Action(
            name="view_mistakes",
            payload={"action": "mistakes"},
            label="📕 复习错题"
        ),
    ]

    await cl.Message(
        content="选择一个功能开始吧，或者直接在聊天框里问我问题哦！",
        actions=actions
    ).send()

@cl.action_callback("ask_question")
async def on_ask_question(action: cl.Action):
    """Handle ask question action"""
    await cl.Message(
        content="🤔 好呀！有什么学习问题想问我吗？可以直接在聊天框里输入你的问题哦！\n\n比如：\n- 什么是加法？\n- 怎么写好作文？\n- 这个字怎么读？\n\n我会帮你从教材里找答案的！",
        author="小栗子"
    ).send()


@cl.action_callback("check_homework")
async def on_check_homework(action: cl.Action):
    """Handle homework checking action"""
    await cl.Message(
        content="📸 请上传你的作业照片，我来帮你检查！",
        author="小栗子"
    ).send()

    # Request file upload
    files = await cl.AskFileMessage(
        content="请选择要检查的作业照片：",
        accept=["image/jpeg", "image/png", "image/webp"],
        max_size_mb=10,
        max_files=5
    ).send()

    if files:
        await cl.Message(
            content=f"收到了 {len(files)} 张照片，正在检查中...请稍等 ⏳",
            author="小栗子"
        ).send()

        # 简化的处理逻辑
        await cl.Message(
            content="🔍 正在分析你的作业...这个功能正在开发中，敬请期待！",
            author="小栗子"
        ).send()

@cl.action_callback("create_planner")
async def on_create_planner(action: cl.Action):
    """Handle planner creation action"""
    await cl.Message(
        content="📅 请告诉我今天的作业内容，我来帮你整理成清单！",
        author="小栗子"
    ).send()

@cl.action_callback("view_mistakes")
async def on_view_mistakes(action: cl.Action):
    """Handle mistake viewing action"""
    await cl.Message(
        content="📕 正在查看你的错题本...让我想想你最近遇到了哪些难题 🤔",
        author="小栗子"
    ).send()

    # 简化的错题本显示
    await cl.Message(
        content="📚 错题本功能正在开发中，敬请期待！",
        author="小栗子"
    ).send()

@cl.on_message
async def on_message(message: cl.Message):
    """Handle chat messages with RAG Q&A integration"""
    user_input = message.content.strip()

    # 基本问候和帮助
    if "你好" in user_input or "hi" in user_input.lower():
        response = "你好呀！我是小栗子，有什么学习问题想问我吗？🌰\n\n你可以直接问我作业相关的问题，比如：\n- '什么是加法？'\n- '怎么写好作文？'\n- '这个字怎么读？'"
        await cl.Message(content=response, author="小栗子").send()
        return

    if "帮助" in user_input or "help" in user_input.lower():
        response = """🌟 我是你的作业搭子小栗子，我可以帮你：

🤔 **学习问答** - 直接问学习问题，我从教材里找答案
📸 检查作业 - 上传作业照片我来检查
📅 整理清单 - 告诉我今天的作业内容
📕 复习错题 - 查看你的错题本

💡 **试试这些问题**：
- "什么是加法？"
- "怎么写好作文？"
- "古诗《静夜思》怎么背？"
- "这个字怎么读？"

直接在聊天框里输入问题就行！"""
        await cl.Message(content=response, author="小栗子").send()
        return

    # 检查是否是问题（包含问号，或者长度合适且不是简单指令）
    is_question = (
        ("？" in user_input or "?" in user_input) and
        not any(cmd in user_input for cmd in ["你好", "帮助", "help", "hi", "再见", "bye"]) and
        len(user_input) >= 2
    )

    if is_question:
        # 发送"正在思考"的消息
        thinking_msg = cl.Message(
            content="🤔 小栗子正在认真思考你的问题...让我从教材里找找答案！⏳",
            author="小栗子"
        )
        await thinking_msg.send()

        try:
            # 检测学科类型
            detected_subject = detect_subject_from_question(user_input)

            # 调用后端API
            logger.info(f"调用问答API: 问题='{user_input}', 检测学科='{detected_subject}'")
            answer_data = await call_backend_api(
                question=user_input,
                subject=detected_subject,
                grade="三年级"
            )

            # 删除"正在思考"的消息
            await thinking_msg.remove()

            if answer_data:
                # 格式化并显示答案
                formatted_answer = format_answer_display(answer_data)
                await cl.Message(
                    content=formatted_answer,
                    author="小栗子"
                ).send()

                # 记录问答日志
                response_time = answer_data.get("response_time", 0)
                context_used = answer_data.get("context_used", False)
                logger.info(f"问答完成: 响应时间={response_time:.2f}秒, 使用上下文={context_used}")

            else:
                # API调用失败
                error_msg = """😅 抱歉，我现在有点头晕，暂时找不到答案。

可能的原因：
- 网络连接有点问题
- 问题太复杂了
- 教材里暂时没有相关内容

你可以：
1. 换个简单点的问题试试
2. 检查一下网络连接
3. 稍后再问我

别灰心，学习路上有我陪你！💪"""
                await cl.Message(content=error_msg, author="小栗子").send()

        except Exception as e:
            # 删除"正在思考"的消息
            await thinking_msg.remove()
            logger.error(f"问答处理异常: {e}")

            error_msg = """😱 哎呀，出现了一点小问题！

别担心，这不是你的错。让我先休息一下，你可以：
- 稍后再试试
- 换个问题问问
- 重新开始对话

学习就像闯关，偶尔遇到小困难很正常，我们一起加油！🌟"""
            await cl.Message(content=error_msg, author="小栗子").send()

    else:
        # 不是问题的输入，给出友好提示
        response = f"""我收到了你的消息：「{user_input}」

🤔 这个问题我可能不太明白。你可以试试：
1. 用问号结尾，比如："什么是加法？"
2. 问我学习上的具体问题
3. 输入"帮助"看看我能做什么

或者点击上面的"🤔 提问学习"按钮，我会给你更多提示！"""

        await cl.Message(
            content=response,
            author="小栗子"
        ).send()

if __name__ == "__main__":
    print("Starting Homework Pal Chainlit Application...")