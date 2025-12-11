#!/usr/bin/env python3
"""
知识库入库脚本
Textbook Knowledge Ingestion Script for Homework Pal RAG System

用于处理人教版教材文档，生成向量嵌入并存储到数据库
"""

import sys
import os
from pathlib import Path
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

# 导入项目模块
from homeworkpal.database.connection import engine, get_db
from homeworkpal.database.models import TextbookChunk
from homeworkpal.llm.siliconflow import create_siliconflow_client
from homeworkpal.document import create_pdf_processor, create_pdf_splitter
from sqlalchemy.orm import sessionmaker

def print_status(message: str, status: str):
    """打印状态信息"""
    icons = {"✅": "✅", "❌": "❌", "⚠️": "⚠️", "🔧": "🔧", "📚": "📚", "🔍": "🔍", "💾": "💾"}
    print(f"{icons.get(status, 'ℹ️')} {message}")


def process_textbook_documents(data_dir: str) -> List[Dict[str, Any]]:
    """
    处理教材文档（包括PDF和其他格式）

    Args:
        data_dir: 教材文档目录路径

    Returns:
        处理后的文档片段列表
    """
    print_status(f"处理教材文档: {data_dir}", "📚")

    all_chunks = []
    data_path = Path(data_dir)

    if not data_path.exists():
        print_status(f"教材目录不存在: {data_dir}", "❌")
        return all_chunks

    # 创建处理器
    pdf_processor = create_pdf_processor()
    text_splitter = create_pdf_splitter(chunk_size=1500, chunk_overlap=200)

    # 优先处理PDF文件
    pdf_files = list(data_path.glob("*.pdf"))
    print(f"📄 发现 {len(pdf_files)} 个PDF文件")

    for pdf_file in pdf_files:
        try:
            print(f"  🔄 正在处理: {pdf_file.name}")

            # 使用PDF处理器提取内容
            pdf_result = pdf_processor.extract_text_from_pdf(str(pdf_file))

            # 使用智能分段器处理内容
            chunks = text_splitter.split_pdf_content(pdf_result)

            # 转换为统一格式
            for chunk in chunks:
                all_chunks.append({
                    'content': chunk['content'],
                    'source': str(pdf_file),
                    'file_name': pdf_file.name,
                    'file_type': 'pdf',
                    'chunk_id': chunk['id'],
                    'page_number': chunk['page_number'],
                    'chunk_index': chunk['chunk_index'],
                    'quality_score': chunk['quality_score'],
                    'metadata': chunk['metadata']
                })

            print(f"  ✅ {pdf_file.name}: 生成 {len(chunks)} 个片段")

        except Exception as e:
            print(f"  ❌ 处理失败 {pdf_file.name}: {e}")

    # 处理其他格式文件（如果有）
    other_extensions = ['.md', '.txt']
    for ext in other_extensions:
        for file_path in data_path.glob(f"*{ext}"):
            try:
                print(f"  🔄 正在处理: {file_path.name}")

                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 简单分段
                from langchain.text_splitter import RecursiveCharacterTextSplitter
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1500,
                    chunk_overlap=200,
                    separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""]
                )

                docs = splitter.create_documents([content])

                for i, doc in enumerate(docs):
                    metadata = {
                        'file_name': file_path.name,
                        'file_type': ext,
                        'source': str(file_path),
                        'subject': '未知',
                        'grade': '三年级',
                        'processed_date': datetime.now().isoformat(),
                        'content_type': '正文内容'
                    }

                    all_chunks.append({
                        'content': doc.page_content,
                        'source': str(file_path),
                        'file_name': file_path.name,
                        'file_type': ext,
                        'chunk_index': i,
                        'quality_score': 1.0,
                        'metadata': metadata
                    })

                print(f"  ✅ {file_path.name}: 生成 {len(docs)} 个片段")

            except Exception as e:
                print(f"  ❌ 处理失败 {file_path.name}: {e}")

    print_status(f"共生成 {len(all_chunks)} 个文档片段", "📚")
    return all_chunks






def generate_embeddings(chunks: List[Dict[str, Any]],
                       embedding_client) -> List[Dict[str, Any]]:
    """
    生成文档片段的向量嵌入

    Args:
        chunks: 文档片段列表
        embedding_client: 嵌入模型客户端

    Returns:
        包含嵌入向量的文档片段列表
    """
    print_status(f"生成 {len(chunks)} 个片段的向量嵌入", "🔍")

    # 过滤高质量片段
    high_quality_chunks = [chunk for chunk in chunks if chunk.get('quality_score', 1.0) > 0.3]
    print(f"  📊 从 {len(chunks)} 个片段中筛选出 {len(high_quality_chunks)} 个高质量片段")

    if not high_quality_chunks:
        print_status("没有高质量的文档片段可供处理", "❌")
        return []

    # 提取文本内容
    texts = [chunk['content'] for chunk in high_quality_chunks]

    try:
        # 批量生成嵌入向量
        embeddings = embedding_client.embed_documents(texts)

        # 验证嵌入向量数量和维度
        if len(embeddings) != len(high_quality_chunks):
            raise ValueError(f"嵌入向量数量({len(embeddings)})与片段数量({len(high_quality_chunks)})不匹配")

        expected_dim = 1024  # BGE-M3的维度
        for i, embedding in enumerate(embeddings):
            if len(embedding) != expected_dim:
                print(f"  ⚠️ 片段 {i} 向量维度不正确: {len(embedding)} (期望: {expected_dim})")

        # 将嵌入向量添加到片段中
        for i, chunk in enumerate(high_quality_chunks):
            chunk['embedding'] = embeddings[i]
            # 添加内容哈希用于去重
            chunk['content_hash'] = hashlib.md5(chunk['content'].encode('utf-8')).hexdigest()

        print_status(f"成功生成 {len(embeddings)} 个向量嵌入", "✅")
        return high_quality_chunks

    except Exception as e:
        print_status(f"生成嵌入向量失败: {e}", "❌")
        return []


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
            embedding_dim = len(sample_chunk.embedding) if hasattr(sample_chunk.embedding, '__len__') else 0
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
    print("🔧 作业搭子 RAG 系统 - 知识库入库脚本")
    print("=" * 60)
    print()

    # 配置参数
    data_dir = os.getenv("TEXTBOOK_DIR", "data/textbooks")
    chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))
    chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "200"))

    print(f"📂 教材目录: {data_dir}")
    print(f"📏 片段大小: {chunk_size}")
    print(f"🔄 片段重叠: {chunk_overlap}")
    print()

    # 执行处理流程
    try:
        # 步骤1: 处理教材文档
        chunks = process_textbook_documents(data_dir)
        if not chunks:
            print("❌ 处理教材文档 - 失败")
            return 1
        print("✅ 处理教材文档 - 通过")

        # 步骤2: 初始化嵌入模型
        if not initialize_embedding_model():
            print("❌ 初始化嵌入模型 - 失败")
            return 1
        print("✅ 初始化嵌入模型 - 通过")

        # 步骤3: 生成向量嵌入
        embedding_client = create_siliconflow_client()
        embedded_chunks = generate_embeddings(chunks, embedding_client)
        if not embedded_chunks:
            print("❌ 生成向量嵌入 - 失败")
            return 1
        print("✅ 生成向量嵌入 - 通过")

        # 步骤4: 保存到数据库
        if not save_to_database(embedded_chunks):
            print("❌ 保存到数据库 - 失败")
            return 1
        print("✅ 保存到数据库 - 通过")

        # 步骤5: 验证入库结果
        if not verify_ingestion():
            print("❌ 验证入库结果 - 失败")
            return 1
        print("✅ 验证入库结果 - 通过")

        passed = 5
        total = 5

    except Exception as e:
        print(f"❌ 处理流程失败: {e}")
        return 1

    print("\n" + "=" * 60)
    print(f"📊 入库结果: {passed}/{total} 步骤完成")

    if passed == total:
        print("🎉 知识库入库完成!")
        print("✅ 人教版教材已成功向量化并存储到数据库")
        print("🔍 现在可以进行语义检索和问答")
        return 0
    else:
        print("⚠️ 知识库入库未完成，请检查错误信息")
        return 1


def initialize_embedding_model():
    """初始化嵌入模型"""
    try:
        client = create_siliconflow_client()

        # 测试连接
        test_text = "这是一个测试文本"
        embedding = client.embed_query(test_text)

        if len(embedding) != 1024:
            raise ValueError(f"向量维度错误: {len(embedding)} (期望: 1024)")

        print_status("嵌入模型初始化成功", "✅")
        return True

    except Exception as e:
        print_status(f"嵌入模型初始化失败: {e}", "❌")
        return False


if __name__ == "__main__":
    sys.exit(main())