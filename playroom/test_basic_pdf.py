#!/usr/bin/env python3
"""
基础PDF处理测试（不依赖PyMuPDF）
Basic PDF Processing Test (PyMuPDF-free)
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

def test_pdf_files():
    """测试PDF文件存在性和基本信息"""
    print("🔧 测试PDF文件基本信息")
    print("=" * 40)

    # 查找PDF文件
    data_dir = Path("data/textbooks")
    if not data_dir.exists():
        print(f"❌ 教材目录不存在: {data_dir}")
        return False

    pdf_files = list(data_dir.glob("*.pdf"))
    print(f"📄 发现 {len(pdf_files)} 个PDF文件")

    if not pdf_files:
        print("❌ 没有找到PDF文件")
        return False

    for pdf_file in pdf_files:
        print(f"\n📁 文件: {pdf_file.name}")
        print(f"  - 路径: {pdf_file}")
        print(f"  - 大小: {pdf_file.stat().st_size / 1024 / 1024:.1f} MB")
        print(f"  - 修改时间: {pdf_file.stat().st_mtime}")

        # 从文件名推断信息
        file_name = pdf_file.name
        subject = '未识别'
        grade = '未识别'

        if '数学' in file_name:
            subject = '数学'
        elif '语文' in file_name:
            subject = '语文'

        if '三年级' in file_name or '3' in file_name:
            grade = '三年级'

        print(f"  - 学科: {subject}")
        print(f"  - 年级: {grade}")

    return True


def test_simple_text_splitting():
    """测试简单文本分割功能"""
    print("\n🔪 测试文本分割功能")
    print("=" * 40)

    # 模拟PDF文本内容
    sample_text = """
    三年级数学上册

    第一单元：时、分、秒

    1. 认识钟表

    钟表是用来计时的工具。我们常见的钟表有时针、分针和秒针。

    时针最短，走得最慢；分针比时针长，走得比时针快；秒针最长，走得最快。

    例题1：看图填空

    图中钟表显示的时间是3时15分。

    练习：

    1. 说出下面钟表显示的时间：
       (1) 7时30分
       (2) 12时45分
       (3) 9时整

    2. 小明早上7时起床，8时到学校，他路上用了多长时间？
    """

    print(f"原始文本长度: {len(sample_text)} 字符")
    print(f"原始文本预览: {sample_text[:100]}...")

    # 简单的文本分割
    chunk_size = 200
    chunks = []

    # 按段落分割
    paragraphs = [p.strip() for p in sample_text.split('\n\n') if p.strip()]

    current_chunk = ""
    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) <= chunk_size:
            current_chunk += paragraph + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = paragraph + "\n\n"

    if current_chunk:
        chunks.append(current_chunk.strip())

    print(f"\n✅ 分割结果:")
    print(f"  - 总片段数: {len(chunks)}")
    print(f"  - 平均长度: {sum(len(c) for c in chunks) / len(chunks):.1f}")

    for i, chunk in enumerate(chunks):
        print(f"\n--- 片段 {i+1} ---")
        print(f"长度: {len(chunk)} 字符")
        print(f"内容: {chunk[:100]}{'...' if len(chunk) > 100 else ''}")

    return len(chunks) > 0


def test_embedding_simulation():
    """测试向量化模拟"""
    print("\n🔍 测试向量化模拟")
    print("=" * 40)

    # 模拟文本片段
    texts = [
        "三年级数学上册第一单元：时、分、秒",
        "钟表是用来计时的工具。我们常见的钟表有时针、分针和秒针。",
        "时针最短，走得最慢；分针比时针长，走得比时针快；秒针最长，走得最快。"
    ]

    print(f"模拟文本数量: {len(texts)}")

    # 模拟向量生成（用随机数）
    import random
    dimension = 1024  # BGE-M3的维度

    for i, text in enumerate(texts):
        # 生成模拟向量
        vector = [random.uniform(-1, 1) for _ in range(dimension)]
        print(f"\n文本 {i+1}:")
        print(f"  长度: {len(text)} 字符")
        print(f"  向量维度: {len(vector)}")
        print(f"  向量前5位: {[round(x, 3) for x in vector[:5]]}")

    return True


def main():
    """主测试函数"""
    print("🎯 作业搭子 - PDF处理基础测试")
    print("=" * 60)

    tests = [
        ("PDF文件检查", test_pdf_files),
        ("文本分割测试", test_simple_text_splitting),
        ("向量化模拟", test_embedding_simulation)
    ]

    passed = 0
    total = len(tests)

    for name, test_func in tests:
        try:
            print(f"\n🧪 运行测试: {name}")
            if test_func():
                print(f"✅ {name} - 通过")
                passed += 1
            else:
                print(f"❌ {name} - 失败")
        except Exception as e:
            print(f"❌ {name} - 异常: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 基础功能测试全部通过！")
        print("💡 下一步：安装PyMuPDF并测试真实PDF处理")
        return 0
    else:
        print("⚠️ 部分测试失败，请检查问题")
        return 1


if __name__ == "__main__":
    sys.exit(main())