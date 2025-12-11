#!/usr/bin/env python3
"""
测试语文教材向量化
Test Chinese Textbook Vectorization
"""

import sys
from pathlib import Path
import hashlib

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

# 导入项目模块
from homeworkpal.document import create_pdf_processor, create_pdf_splitter


def test_chinese_processing():
    """测试语文教材处理"""
    print("🔧 测试语文教材处理")
    print("=" * 40)

    # 1. 测试PDF处理
    processor = create_pdf_processor(subject='语文')
    print(f"✅ 处理器创建: {type(processor).__name__}")

    pdf_path = "data/textbooks/语文三上.pdf"
    if not Path(pdf_path).exists():
        print(f"❌ PDF文件不存在: {pdf_path}")
        return False

    try:
        # 处理前2页
        result = processor.extract_text_from_pdf(pdf_path)
        test_pages = result['pages'][:2]

        print(f"✅ PDF处理成功:")
        print(f"  - 文件名: {result['file_name']}")
        print(f"  - 学科: {result['education_metadata']['subject']}")
        print(f"  - 年级: {result['education_metadata']['grade']}")
        print(f"  - 测试页数: {len(test_pages)}")

        # 2. 测试分割
        splitter = create_pdf_splitter(subject='语文')
        print(f"✅ 分割器创建: {type(splitter).__name__}")

        test_result = result.copy()
        test_result['pages'] = test_pages
        chunks = splitter.split_pdf_content(test_result)

        print(f"✅ 分割完成: {len(chunks)} 个片段")

        # 显示片段信息
        for i, chunk in enumerate(chunks[:3]):
            content_hash = hashlib.md5(chunk['content'].encode('utf-8')).hexdigest()
            print(f"\\n--- 片段 {i+1} ---")
            print(f"  ID: {chunk['id']}")
            print(f"  类型: {chunk.get('content_type', '未知')}")
            print(f"  页面: {chunk['page_number']}")
            print(f"  长度: {chunk['text_length']} 字符")
            print(f"  质量: {chunk['quality_score']:.2f}")
            print(f"  哈希: {content_hash[:8]}...")
            print(f"  预览: {chunk['content'][:100]}...")

        print(f"\\n✅ 处理测试成功完成!")
        return True

    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    return test_chinese_processing()


if __name__ == "__main__":
    success = main()
    if success:
        print("\\n🎉 语文教材处理测试成功!")
    else:
        print("\\n❌ 语文教材处理测试失败!")