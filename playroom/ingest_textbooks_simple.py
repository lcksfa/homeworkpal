#!/usr/bin/env python3
"""
简化的知识库入库脚本
Simplified Textbook Knowledge Ingestion Script

使用简化的PDF处理和文本分段功能
"""

import sys
import os
from pathlib import Path
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

# 导入项目模块
from homeworkpal.database.connection import engine, get_db
from homeworkpal.database.models import TextbookChunk
from sqlalchemy.orm import sessionmaker
from simple_text_splitter import create_simple_splitter

def print_status(message: str, status: str):
    """打印状态信息"""
    icons = {"✅": "✅", "❌": "❌", "⚠️": "⚠️", "🔧": "🔧", "📚": "📚", "🔍": "🔍", "💾": "💾"}
    print(f"{icons.get(status, 'ℹ️')} {message}")


def process_textbook_documents_simple(data_dir: str) -> List[Dict[str, Any]]:
    """
    简化版的教材文档处理（暂时不处理真实PDF，使用示例文本）

    Args:
        data_dir: 教材文档目录路径

    Returns:
        处理后的文档片段列表
    """
    print_status(f"处理教材文档（简化模式）: {data_dir}", "📚")

    # 示例教材内容
    sample_documents = [
        {
            "file_name": "数学 3 上.pdf",
            "subject": "数学",
            "grade": "三年级",
            "content": """
            三年级数学上册第一单元：时、分、秒

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
        },
        {
            "file_name": "语文三上.pdf",
            "subject": "语文",
            "grade": "三年级",
            "content": """
            三年级语文上册第一单元：我们的学校

            1. 我们的学校

            我们的学校很美丽。校园里有高大的教学楼，宽阔的操场，还有绿油油的小草。

            教学楼有五层高，每一层都有明亮的教室。教室里有整齐的课桌椅，干净的黑板。

            操场上有篮球架、足球门。下课的时候，同学们都喜欢到操场上玩。

            校园的周围种着许多树。春天，树木发芽；夏天，树木长得郁郁葱葱。

            我爱我们的学校，爱这里的一草一木。

            生字：校园 操场 教学 整齐 干净 周围 树木 发芽
            """
        }
    ]

    all_chunks = []
    text_splitter = create_simple_splitter(chunk_size=1500, chunk_overlap=200)

    for doc in sample_documents:
        print(f"  🔄 正在处理: {doc['file_name']}")

        # 分割文本
        chunks = text_splitter.split_text(doc['content'])

        for i, chunk_text in enumerate(chunks):
            chunk_text = chunk_text.strip()
            if not chunk_text:
                continue

            chunk_id = f"{doc['file_name']}_chunk_{i+1}"

            chunk = {
                'content': chunk_text,
                'source': f"data/textbooks/{doc['file_name']}",
                'file_name': doc['file_name'],
                'file_type': 'pdf',
                'chunk_id': chunk_id,
                'page_number': 1,  # 示例文档
                'chunk_index': i,
                'quality_score': 1.0,  # 示例质量分数
                'metadata': {
                    'pdf_file': doc['file_name'],
                    'subject': doc['subject'],
                    'grade': doc['grade'],
                    'page_number': 1,
                    'total_pages': 1,
                    'processed_date': datetime.now().isoformat(),
                    'content_type': '正文内容',
                    'has_images': False
                }
            }

            all_chunks.append(chunk)

        print(f"  ✅ {doc['file_name']}: 生成 {len(chunks)} 个片段")

    print_status(f"共生成 {len(all_chunks)} 个文档片段", "📚")
    return all_chunks


def generate_mock_embeddings(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    生成模拟的向量嵌入（用于测试）

    Args:
        chunks: 文档片段列表

    Returns:
        包含模拟嵌入向量的文档片段列表
    """
    print_status(f"生成 {len(chunks)} 个片段的模拟向量嵌入", "🔍")

    import random

    # BGE-M3的向量维度是1024
    dimension = 1024

    for i, chunk in enumerate(chunks):
        # 生成模拟向量（在实际应用中会使用真实的嵌入模型）
        embedding = [random.uniform(-1, 1) for _ in range(dimension)]
        chunk['embedding'] = embedding
        chunk['content_hash'] = hashlib.md5(chunk['content'].encode('utf-8')).hexdigest()

    print_status(f"成功生成 {len(chunks)} 个模拟向量嵌入", "✅")
    return chunks


def save_to_database(chunks: List[Dict[str, Any]],
                     batch_size: int = 10) -> bool:
    """
    将文档片段保存到数据库

    Args:
        chunks: 文档片段列表
        batch_size: 批处理大小

    Returns:
        是否保存成功
    """
    print_status(f"保存 {len(chunks)} 个文档片段到数据库", "💾")

    try:
        # 创建数据库会话
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        # 去重：检查内容哈希是否已存在
        existing_hashes = set()
        existing_records = session.query(TextbookChunk.content_hash).filter(
            TextbookChunk.content_hash.in_([chunk.get('content_hash', '') for chunk in chunks])
        ).all()
        existing_hashes = set(record[0] for record in existing_records)

        # 过滤新片段
        new_chunks = [chunk for chunk in chunks if chunk.get('content_hash', '') not in existing_hashes]

        if not new_chunks:
            print_status("所有片段都已存在于数据库中", "✅")
            session.close()
            return True

        print(f"  📊 过滤重复后新增 {len(new_chunks)} 个片段")

        # 批量保存
        saved_count = 0
        for i in range(0, len(new_chunks), batch_size):
            batch = new_chunks[i:i + batch_size]

            for chunk in batch:
                # 创建TextbookChunk对象
                textbook_chunk = TextbookChunk(
                    content=chunk['content'],
                    embedding=chunk['embedding'],
                    metadata_json=chunk['metadata'],
                    source_file=chunk['source'],
                    chunk_index=chunk['chunk_index'],
                    content_hash=chunk.get('content_hash', hashlib.md5(chunk['content'].encode('utf-8')).hexdigest()),
                    page_number=chunk.get('page_number'),
                    quality_score=chunk.get('quality_score', 1.0)
                )

                session.add(textbook_chunk)
                saved_count += 1

            # 提交批次
            session.commit()
            print(f"  ✅ 已保存 {min(i + batch_size, len(new_chunks))}/{len(new_chunks)} 个片段")

        session.close()

        print_status(f"成功保存 {saved_count} 个新文档片段到数据库", "✅")
        return True

    except Exception as e:
        print_status(f"保存到数据库失败: {e}", "❌")
        if 'session' in locals():
            session.rollback()
            session.close()
        return False


def verify_ingestion():
    """
    验证入库结果
    """
    print_status("验证入库结果", "🔍")

    try:
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        # 查询总记录数
        total_count = session.query(TextbookChunk).count()
        print(f"  📊 数据库中总记录数: {total_count}")

        if total_count > 0:
            # 查询示例记录
            sample_chunk = session.query(TextbookChunk).first()
            print(f"  📝 示例内容长度: {len(sample_chunk.content)} 字符")
            embedding_dim = len(sample_chunk.embedding) if sample_chunk.embedding is not None else 0
            print(f"  🔢 向量维度: {embedding_dim}")
            print(f"  📄 源文件: {sample_chunk.source_file}")
            print(f"  📋 元数据: {json.dumps(sample_chunk.metadata_json, ensure_ascii=False, indent=2)}")

        session.close()
        print_status("入库验证完成", "✅")
        return True

    except Exception as e:
        print_status(f"验证失败: {e}", "❌")
        return False


def main():
    """主函数"""
    print("🔧 作业搭子 RAG 系统 - 简化知识库入库脚本")
    print("=" * 60)
    print()

    # 配置参数
    data_dir = os.getenv("TEXTBOOK_DIR", "data/textbooks")

    print(f"📂 教材目录: {data_dir}")
    print(f"🔧 模式: 简化测试模式（使用示例文本）")
    print()

    try:
        # 步骤1: 处理教材文档
        chunks = process_textbook_documents_simple(data_dir)
        if not chunks:
            print("❌ 处理教材文档 - 失败")
            return 1
        print("✅ 处理教材文档 - 通过")

        # 步骤2: 生成模拟向量嵌入
        embedded_chunks = generate_mock_embeddings(chunks)
        if not embedded_chunks:
            print("❌ 生成向量嵌入 - 失败")
            return 1
        print("✅ 生成向量嵌入 - 通过")

        # 步骤3: 保存到数据库
        if not save_to_database(embedded_chunks):
            print("❌ 保存到数据库 - 失败")
            return 1
        print("✅ 保存到数据库 - 通过")

        # 步骤4: 验证入库结果
        if not verify_ingestion():
            print("❌ 验证入库结果 - 失败")
            return 1
        print("✅ 验证入库结果 - 通过")

        passed = 4
        total = 4

    except Exception as e:
        print(f"❌ 处理流程失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print("\n" + "=" * 60)
    print(f"📊 入库结果: {passed}/{total} 步骤完成")

    if passed == total:
        print("🎉 知识库入库完成!")
        print("✅ 示例教材内容已成功向量化并存储到数据库")
        print("🔍 现在可以进行语义检索和问答测试")
        print("\n💡 下一步:")
        print("  1. 安装PyMuPDF以处理真实PDF文件")
        print("  2. 配置SiliconFlow API以使用真实向量嵌入")
        print("  3. 测试检索和问答功能")
        return 0
    else:
        print("⚠️ 知识库入库未完成，请检查错误信息")
        return 1


if __name__ == "__main__":
    sys.exit(main())