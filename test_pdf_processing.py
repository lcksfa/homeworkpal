#!/usr/bin/env python3
"""
测试PDF处理功能
Test PDF Processing Functionality
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from homeworkpal.document import create_pdf_processor, create_pdf_splitter

def test_pdf_processing():
    """测试PDF处理功能"""
    print("🔧 测试PDF处理功能")
    print("=" * 40)

    # 创建处理器
    pdf_processor = create_pdf_processor()
    text_splitter = create_pdf_splitter(chunk_size=1500, chunk_overlap=200)

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

    # 处理第一个PDF文件
    pdf_file = pdf_files[0]
    print(f"🔄 正在处理: {pdf_file.name}")

    try:
        # 提取PDF内容
        pdf_result = pdf_processor.extract_text_from_pdf(str(pdf_file))
        print(f"✅ PDF提取成功")
        print(f"  - 总页数: {len(pdf_result.get('pages', []))}")
        print(f"  - 学科: {pdf_result['education_metadata'].get('subject', '未识别')}")
        print(f"  - 年级: {pdf_result['education_metadata'].get('grade', '未识别')}")

        # 分割内容
        chunks = text_splitter.split_pdf_content(pdf_result)
        print(f"✅ 文档分割成功，生成 {len(chunks)} 个片段")

        # 显示统计信息
        high_quality = [c for c in chunks if c['quality_score'] > 0.5]
        print(f"  - 高质量片段: {len(high_quality)}")
        print(f"  - 平均片段长度: {sum(c['text_length'] for c in chunks) / len(chunks):.1f}")

        # 显示前3个片段的预览
        for i, chunk in enumerate(chunks[:3]):
            print(f"\n--- 片段 {i+1} 预览 ---")
            print(f"ID: {chunk['id']}")
            print(f"页面: {chunk['page_number']}")
            print(f"长度: {chunk['text_length']} 字符")
            print(f"质量评分: {chunk['quality_score']:.2f}")
            print(f"内容类型: {chunk['metadata']['content_type']}")
            preview = chunk['content'][:200] + '...' if len(chunk['content']) > 200 else chunk['content']
            print(f"内容: {preview}")

        return True

    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_pdf_processing()
    if success:
        print("\n🎉 PDF处理测试通过！")
    else:
        print("\n❌ PDF处理测试失败！")
        sys.exit(1)