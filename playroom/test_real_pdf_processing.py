#!/usr/bin/env python3
"""
真实PDF处理测试
Real PDF Processing Test

使用PyMuPDF处理真实的教材PDF文件
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

# 直接导入模块，避免__init__.py的langchain依赖
sys.path.insert(0, str(project_root / "homeworkpal" / "document"))
from pdf_processor import create_pdf_processor

# 使用简化的文本分割器，避免langchain依赖
sys.path.append(str(Path(__file__).parent))
from simple_text_splitter import create_simple_splitter

def test_real_pdf_processing():
    """测试真实PDF处理功能"""
    print("🎯 真实PDF处理测试")
    print("=" * 50)

    # 创建处理器
    pdf_processor = create_pdf_processor()
    text_splitter = create_simple_splitter(chunk_size=1500, chunk_overlap=200)

    # 查找PDF文件
    data_dir = Path("../data/textbooks")
    if not data_dir.exists():
        print(f"❌ 教材目录不存在: {data_dir}")
        return False

    pdf_files = list(data_dir.glob("*.pdf"))
    print(f"📄 发现 {len(pdf_files)} 个PDF文件")

    if not pdf_files:
        print("❌ 没有找到PDF文件")
        return False

    # 处理第一个PDF文件（数学教材）
    pdf_file = pdf_files[0]
    print(f"\n🔄 正在处理: {pdf_file.name}")
    print(f"📁 文件大小: {pdf_file.stat().st_size / 1024 / 1024:.1f} MB")

    try:
        # 提取PDF内容
        print("📖 开始提取PDF内容...")
        pdf_result = pdf_processor.extract_text_from_pdf(str(pdf_file))
        print(f"✅ PDF提取成功")
        print(f"  - 总页数: {len(pdf_result.get('pages', []))}")
        print(f"  - 学科: {pdf_result['education_metadata'].get('subject', '未识别')}")
        print(f"  - 年级: {pdf_result['education_metadata'].get('grade', '未识别')}")
        print(f"  - 处理器: {pdf_result.get('processor_type', 'unknown')}")
        print(f"  - 文件名: {pdf_result['file_name']}")

        # 分割内容
        print("🔪 开始分割文本...")
        chunks = text_splitter.split_pdf_content(pdf_result)
        print(f"✅ 文档分割成功，生成 {len(chunks)} 个片段")

        # 显示统计信息
        if chunks:
            high_quality = [c for c in chunks if c['quality_score'] > 0.5]
            avg_length = sum(c['text_length'] for c in chunks) / len(chunks)
            print(f"  - 高质量片段: {len(high_quality)}")
            print(f"  - 平均片段长度: {avg_length:.1f}")

            # 按页面分布统计
            pages = {}
            for chunk in chunks:
                page = chunk['page_number']
                pages[page] = pages.get(page, 0) + 1
            print(f"  - 页面分布: {pages}")

            # 显示前3个片段的预览
            for i, chunk in enumerate(chunks[:3]):
                print(f"\n--- 片段 {i+1} 预览 ---")
                print(f"ID: {chunk['id']}")
                print(f"页面: {chunk['page_number']}")
                print(f"长度: {chunk['text_length']} 字符")
                print(f"质量评分: {chunk['quality_score']:.2f}")
                print(f"内容类型: {chunk['metadata']['content_type']}")
                preview = chunk['content'][:300] + '...' if len(chunk['content']) > 300 else chunk['content']
                print(f"内容: {preview}")

        else:
            print("⚠️ 没有生成任何片段")

        return True

    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_math_vs_chinese_pdfs():
    """测试数学和语文PDF的处理差异"""
    print("\n\n📚 数学 vs 语文 PDF处理对比")
    print("=" * 50)

    # 创建处理器
    pdf_processor = create_pdf_processor()
    text_splitter = create_simple_splitter(chunk_size=1500, chunk_overlap=200)

    data_dir = Path("../data/textbooks")
    pdf_files = list(data_dir.glob("*.pdf"))

    results = {}

    for pdf_file in pdf_files:
        try:
            print(f"\n📖 处理: {pdf_file.name}")
            print(f"📁 大小: {pdf_file.stat().st_size / 1024 / 1024:.1f} MB")

            # 提取内容
            pdf_result = pdf_processor.extract_text_from_pdf(str(pdf_file))
            chunks = text_splitter.split_pdf_content(pdf_result)

            # 统计信息
            stats = {
                'pages': len(pdf_result.get('pages', [])),
                'chunks': len(chunks),
                'high_quality': len([c for c in chunks if c['quality_score'] > 0.5]),
                'avg_length': sum(c['text_length'] for c in chunks) / len(chunks) if chunks else 0,
                'subject': pdf_result['education_metadata'].get('subject', '未识别'),
                'grade': pdf_result['education_metadata'].get('grade', '未识别')
            }

            results[pdf_file.name] = stats

            print(f"  ✅ 页数: {stats['pages']}")
            print(f"  ✅ 片段数: {stats['chunks']}")
            print(f"  ✅ 高质量片段: {stats['high_quality']}")
            print(f"  ✅ 平均长度: {stats['avg_length']:.1f}")

        except Exception as e:
            print(f"  ❌ 处理失败: {e}")
            results[pdf_file.name] = {'error': str(e)}

    # 显示对比结果
    print(f"\n📊 处理结果对比:")
    print(f"{'文件名':<20} {'学科':<6} {'页数':<4} {'片段数':<6} {'高质量':<6} {'平均长度':<8}")
    print("-" * 60)

    for filename, stats in results.items():
        if 'error' not in stats:
            print(f"{filename:<20} {stats['subject']:<6} {stats['pages']:<4} {stats['chunks']:<6} {stats['high_quality']:<6} {stats['avg_length']:<8.1f}")
        else:
            print(f"{filename:<20} {'错误':<6} {'-':<4} {'-':<6} {'-':<6} {'-':<8}")

    return len(results) > 0


if __name__ == "__main__":
    print("🎯 作业搭子 - 真实PDF处理测试")
    print("=" * 60)

    success1 = test_real_pdf_processing()
    success2 = test_math_vs_chinese_pdfs()

    if success1 and success2:
        print("\n🎉 所有PDF处理测试通过！")
        print("✅ PyMuPDF安装成功，可以处理真实PDF文件")
        print("💡 现在可以使用完整的ingest_textbooks.py处理真实教材")
    else:
        print("\n❌ 部分测试失败")
        sys.exit(1)