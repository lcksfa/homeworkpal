#!/usr/bin/env python3
"""
Homework Pal Chainlit Application (Simplified Version)
基础的交互界面，暂时忽略数据库连接
"""

import chainlit as cl
from typing import Optional
import os
from dotenv import load_dotenv

from homeworkpal.utils.logger import get_simple_logger

# Load environment variables
load_dotenv()

# Initialize logger
logger = get_simple_logger()

@cl.on_chat_start
async def on_chat_start():
    """Initialize chat session"""
    # Send welcome message
    welcome_message = """
👋 嗨！我是你的作业搭子小栗子！🌰
今天我们也要一起消灭作业怪兽哦！

👇 你可以：
📸 检查作业 - 上传作业照片，我来帮你检查
📅 整理清单 - 告诉我今天的作业内容
📕 复习错题 - 查看你的错题本
"""

    await cl.Message(
        content=welcome_message,
        author="小栗子"
    ).send()

    # Add action buttons (Chainlit 2.x compatible)
    actions = [
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
        content="选择一个功能开始吧：",
        actions=actions
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
    """Handle chat messages"""
    user_input = message.content

    # Simple response logic for now
    if "你好" in user_input or "hi" in user_input.lower():
        response = "你好呀！我是小栗子，有什么可以帮你的吗？🌰"
    elif "帮助" in user_input or "help" in user_input.lower():
        response = """我可以帮你：
📸 检查作业 - 上传照片我来检查
📅 整理清单 - 告诉我作业内容
📕 复习错题 - 查看错题本
还有什么问题吗？"""
    else:
        response = f"我收到了你的消息：「{user_input}」这个功能正在开发中，敬请期待！"

    await cl.Message(
        content=response,
        author="小栗子"
    ).send()

if __name__ == "__main__":
    print("Starting Homework Pal Chainlit Application...")