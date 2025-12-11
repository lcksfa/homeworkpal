#!/usr/bin/env python3
"""
语文教材向量化处理脚本
Chinese Textbook Vectorization Script
"""

import sys
import os
from pathlib import Path
import hashlib
from datetime import datetime
import logging

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

# 导入项目模块
from homeworkpal.database.connection import engine, get_db
from homeworkpal.database.models import TextbookChunk
from homeworkpal.llm.siliconflow import create_siliconflow_client
from homeworkpal.document import (
    create_pdf_processor,
    create_pdf_splitter,
    create_chinese_text_processor
)
from sqlalchemy.orm import sessionmaker

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def print_status(message: str, status: str):
    """打印状态信息"""
    icons = {"✅": "✅", "❌": "❌", "⚠️": "⚠️", "🔧": "🔧", "📚": "📚", "🔍": "🔍", "💾": "💾"}
    print(f"{icons.get(status, 'ℹ️')} {message}")


def process_chinese_textbook():
    """处理语文教材PDF并生成向量嵌入"""
    pdf_path = "data/textbooks/语文三上.pdf"

    print_status("开始处理语文教材向量化", "📚")
    print("=" * 60)

    try:
        # 1. 创建处理组件
        print_status("创建处理器组件", "🔧")
        processor = create_pdf_processor(subject='语文')
        splitter = create_pdf_splitter(subject='语文')
        embedding_client = create_siliconflow_client()
        text_processor = create_chinese_text_processor(embedding_client)

        print(f"✅ 所有组件创建成功")

        # 2. 处理PDF（只处理前3页用于测试）
        print_status("处理PDF文档", "📄")
        pdf_result = processor.extract_text_from_pdf(pdf_path)

        # 限制处理页数
        test_pages = pdf_result['pages'][:3]
        test_result = pdf_result.copy()
        test_result['pages'] = test_pages

        print(f"✅ PDF处理完成: {len(test_pages)} 页")

        # 3. 分割文档
        print_status("分割文档内容", "✂️")
        chunks = splitter.split_pdf_content(test_result)
        print(f"✅ 生成 {len(chunks)} 个文档片段")

        # 4. 准备文本内容
        text_contents = [chunk['content'] for chunk in chunks]

        # 显示片段信息
        for i, chunk in enumerate(chunks[:3]):
            print(f"片段 {i+1}: 类型={chunk.get('content_type', '未知')}, 长度={chunk.get('text_length', 0)}")

        # 5. 质量评估和预处理
        print_status("评估文本质量", "🔍")
        for i, content in enumerate(text_contents[:3]):
            quality = text_processor.assess_embedding_quality(content)
            processed = text_processor.preprocess_chinese_text_for_embedding(content)
            print(f"  片段 {i+1}: 评分={quality['score']:.2f}, 处理后长度={len(processed)}")

        # 6. 批量向量化
        print_status("开始批量向量化", "⚡")
        start_time = datetime.now()

        embeddings, quality_results = text_processor.batch_vectorize_with_quality_control(
            text_contents,
            batch_size=2,  # 小批次测试
            max_retries=2
        )

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        print(f"✅ 向量化完成:")
        print(f"  - 处理时间: {processing_time:.1f}秒")
        print(f"  - 向量数量: {len(embeddings)}")
        print(f"  - 向量维度: {len(embeddings[0]) if embeddings else 0}")

        # 7. 保存到数据库
        print_status("保存到数据库", "💾")
        save_chunks_to_database(chunks, embeddings, test_result)

        print_status("语文教材向量化处理完成!", "🎉")
        return True

    except Exception as e:
        print_status(f"处理失败: {e}", "❌")
        import traceback
        traceback.print_exc()
        return False


def save_chunks_to_database(chunks, embeddings, pdf_result):
    """保存文档片段到数据库"""
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        saved_count = 0

        for i, chunk in enumerate(chunks):
            # 生成内容哈希
            content_hash = hashlib.md5(chunk['content'].encode('utf-8')).hexdigest()

            # 检查是否已存在
            existing = session.query(TextbookChunk).filter_by(
                content_hash=content_hash
            ).first()

            if existing:
                print(f"跳过重复内容: {content_hash[:8]}...")
                continue

            # 创建数据库记录
            db_chunk = TextbookChunk(
                content=chunk['content'],
                embedding=embeddings[i] if i < len(embeddings) else [0.0] * 1024,
                content_hash=content_hash,
                metadata_json={
                    'pdf_file': pdf_result['file_name'],
                    'subject': pdf_result['education_metadata']['subject'],
                    'grade': pdf_result['education_metadata']['grade'],
                    'content_type': chunk.get('content_type', '未知'),
                    'page_number': chunk['page_number'],
                    'quality_score': chunk['quality_score']
                },
                source_file=pdf_result['file_path'],
                chunk_index=chunk['chunk_index'],
                page_number=chunk['page_number'],
                quality_score=chunk['quality_score']
            )

            session.add(db_chunk)
            saved_count += 1

        session.commit()
        print(f"✅ 保存了 {saved_count} 个新片段到数据库")

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def main():
    """主函数"""
    print("🔧 语文教材向量化处理脚本")
    print("=" * 60)

    # 检查环境
    if not Path("data/textbooks/语文三上.pdf").exists():
        print_status("PDF文件不存在", "❌")
        return False

    if not os.getenv("SILICONFLOW_API_KEY"):
        print_status("未设置SILICONFLOW_API_KEY", "❌")
        return False

    # 执行处理
    return process_chinese_textbook()


if __name__ == "__main__":
    main()