#!/usr/bin/env python3
"""
增强版知识库入库脚本
Enhanced Textbook Knowledge Ingestion Script for Homework Pal RAG System

集成了中文文本处理器，支持拼音修复和文本质量优化
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
from homeworkpal.llm.siliconflow import create_siliconflow_client, SiliconFlowEmbeddingModel
from homeworkpal.document import create_pdf_processor, create_pdf_splitter
from homeworkpal.document.chinese_text_processor import ChineseTextProcessor
from sqlalchemy.orm import sessionmaker

def print_status(message: str, status: str):
    """打印状态信息"""
    icons = {"✅": "✅", "❌": "❌", "⚠️": "⚠️", "🔧": "🔧", "📚": "📚", "🔍": "🔍", "💾": "💾", "🚀": "🚀"}
    print(f"{icons.get(status, 'ℹ️')} {message}")


def process_textbook_documents_enhanced(data_dir: str) -> List[Dict[str, Any]]:
    """
    使用增强的文本处理器处理教材文档

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

    # 创建中文文本处理器
    embedding_model = SiliconFlowEmbeddingModel(
        api_key=os.getenv('SILICONFLOW_API_KEY'),
        base_url=os.getenv('SILICONFLOW_BASE_URL'),
        model_name='BAAI/bge-m3'
    )
    chinese_processor = ChineseTextProcessor(embedding_model)

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

            # 应用中文文本处理和质量评估
            processed_count = 0
            for chunk in chunks:
                # 使用中文文本处理器预处理
                original_content = chunk['content']
                processed_content = chinese_processor.preprocess_chinese_text_for_embedding(original_content)

                if not processed_content.strip():
                    continue  # 跳过空内容

                # 质量评估
                quality_assessment = chinese_processor.assess_embedding_quality(processed_content)

                # 只保留高质量内容
                if quality_assessment['is_suitable']:
                    processed_chunk = {
                        'content': processed_content,
                        'original_content': original_content,
                        'source': str(pdf_file),
                        'file_name': pdf_file.name,
                        'file_type': 'pdf',
                        'chunk_id': chunk['id'],
                        'page_number': chunk['page_number'],
                        'chunk_index': chunk['chunk_index'],
                        'quality_score': quality_assessment['score'],
                        'quality_details': quality_assessment,
                        'metadata': chunk['metadata']
                    }

                    all_chunks.append(processed_chunk)
                    processed_count += 1

            print(f"  ✅ {pdf_file.name}: 原始 {len(chunks)} 片段 → 高质量 {processed_count} 片段")

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

                # 使用中文文本处理器预处理
                processed_content = chinese_processor.preprocess_chinese_text_for_embedding(content)

                if not processed_content.strip():
                    continue

                # 质量评估
                quality_assessment = chinese_processor.assess_embedding_quality(processed_content)

                if quality_assessment['is_suitable']:
                    # 简单分段
                    from langchain.text_splitter import RecursiveCharacterTextSplitter
                    splitter = RecursiveCharacterTextSplitter(
                        chunk_size=1500,
                        chunk_overlap=200,
                        separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""]
                    )

                    docs = splitter.create_documents([processed_content])

                    for i, doc in enumerate(docs):
                        metadata = {
                            'file_name': file_path.name,
                            'file_type': ext,
                            'source': str(file_path),
                            'subject': '未知',
                            'grade': '三年级',
                            'processed_date': datetime.now().isoformat(),
                            'content_type': '正文内容',
                            'quality_score': quality_assessment['score']
                        }

                        all_chunks.append({
                            'content': doc.page_content,
                            'original_content': content,
                            'source': str(file_path),
                            'file_name': file_path.name,
                            'file_type': ext,
                            'chunk_index': i,
                            'quality_score': quality_assessment['score'],
                            'quality_details': quality_assessment,
                            'metadata': metadata
                        })

                    print(f"  ✅ {file_path.name}: 生成 {len(docs)} 个片段")

                else:
                    print(f"  ⚠️ {file_path.name}: 质量不符合要求")

            except Exception as e:
                print(f"  ❌ 处理失败 {file_path.name}: {e}")

    print_status(f"共生成 {len(all_chunks)} 个高质量文档片段", "🚀")
    return all_chunks


def generate_embeddings_enhanced(chunks: List[Dict[str, Any]],
                                embedding_client) -> List[Dict[str, Any]]:
    """
    使用增强的批处理生成文档片段的向量嵌入

    Args:
        chunks: 文档片段列表
        embedding_client: 嵌入模型客户端

    Returns:
        包含嵌入向量的文档片段列表
    """
    print_status(f"生成 {len(chunks)} 个片段的向量嵌入", "🔍")

    if not chunks:
        print_status("没有文档片段可供处理", "❌")
        return []

    # 提取文本内容
    texts = [chunk['content'] for chunk in chunks]

    try:
        # 使用中文文本处理器的批量向量化功能
        chinese_processor = ChineseTextProcessor(embedding_client)
        embeddings, quality_results = chinese_processor.batch_vectorize_with_quality_control(
            texts,
            batch_size=5,  # 使用较小的批处理确保稳定性
            max_retries=3,
            quality_threshold=0.4
        )

        # 验证嵌入向量数量和维度
        if len(embeddings) != len(chunks):
            raise ValueError(f"嵌入向量数量({len(embeddings)})与片段数量({len(chunks)})不匹配")

        expected_dim = 1024  # BGE-M3的维度
        valid_count = 0
        for i, embedding in enumerate(embeddings):
            if len(embedding) == expected_dim and embedding != [0.0] * expected_dim:
                valid_count += 1

        print(f"  📊 有效向量: {valid_count}/{len(embeddings)}")

        # 将嵌入向量添加到片段中
        for i, chunk in enumerate(chunks):
            chunk['embedding'] = embeddings[i]
            # 添加内容哈希用于去重（使用处理后的内容）
            chunk['content_hash'] = hashlib.md5(chunk['content'].encode('utf-8')).hexdigest()
            # 添加质量评估结果
            if i < len(quality_results):
                chunk['quality_details'] = quality_results[i]

        print_status(f"成功生成 {len(embeddings)} 个向量嵌入", "✅")
        return chunks

    except Exception as e:
        print_status(f"生成嵌入向量失败: {e}", "❌")
        return []


def save_to_database_enhanced(chunks: List[Dict[str, Any]],
                             batch_size: int = 10) -> bool:
    """
    将增强处理的文档片段保存到数据库

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

        # 统计质量分布
        quality_scores = [chunk.get('quality_score', 0) for chunk in new_chunks]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        high_quality_count = sum(1 for score in quality_scores if score >= 0.8)

        print(f"  📈 平均质量评分: {avg_quality:.3f}")
        print(f"  📊 高质量片段: {high_quality_count}/{len(new_chunks)} ({high_quality_count/len(new_chunks)*100:.1f}%)")

        # 批量保存
        saved_count = 0
        for i in range(0, len(new_chunks), batch_size):
            batch = new_chunks[i:i + batch_size]

            for chunk in batch:
                # 增强元数据
                enhanced_metadata = chunk.get('metadata', {})
                enhanced_metadata.update({
                    'processed_date': datetime.now().isoformat(),
                    'quality_score': chunk.get('quality_score', 0),
                    'has_original': 'original_content' in chunk,
                    'text_processor': 'enhanced_chinese_processor'
                })

                # 创建TextbookChunk对象
                textbook_chunk = TextbookChunk(
                    content=chunk['content'],
                    embedding=chunk['embedding'],
                    metadata_json=enhanced_metadata,
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


def verify_ingestion_enhanced():
    """
    验证增强版入库结果
    """
    print_status("验证增强版入库结果", "🔍")

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
            print(f"  🎯 质量评分: {sample_chunk.quality_score}")
            print(f"  📋 元数据: {json.dumps(sample_chunk.metadata_json, ensure_ascii=False, indent=2)}")

            # 质量分布统计
            from sqlalchemy import func
            quality_stats = session.query(
                func.avg(TextbookChunk.quality_score).label('avg_quality'),
                func.min(TextbookChunk.quality_score).label('min_quality'),
                func.max(TextbookChunk.quality_score).label('max_quality')
            ).first()

            print(f"  📈 质量分布:")
            print(f"    平均: {quality_stats.avg_quality:.3f}")
            print(f"    最低: {quality_stats.min_quality:.3f}")
            print(f"    最高: {quality_stats.max_quality:.3f}")

        session.close()
        print_status("增强版入库验证完成", "✅")
        return True

    except Exception as e:
        print_status(f"验证失败: {e}", "❌")
        return False


def main():
    """主函数"""
    print("🚀 作业搭子 RAG 系统 - 增强版知识库入库脚本")
    print("=" * 60)
    print()

    # 配置参数
    data_dir = os.getenv("TEXTBOOK_DIR", "data/textbooks")
    chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))
    chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "200"))

    print(f"📂 教材目录: {data_dir}")
    print(f"📏 片段大小: {chunk_size}")
    print(f"🔄 片段重叠: {chunk_overlap}")
    print("🚀 启用增强版中文文本处理和拼音修复")
    print()

    # 执行处理流程
    try:
        # 步骤1: 增强版文档处理
        chunks = process_textbook_documents_enhanced(data_dir)
        if not chunks:
            print("❌ 处理教材文档 - 失败")
            return 1
        print("✅ 处理教材文档 - 通过")

        # 步骤2: 初始化嵌入模型
        if not initialize_embedding_model():
            print("❌ 初始化嵌入模型 - 失败")
            return 1
        print("✅ 初始化嵌入模型 - 通过")

        # 步骤3: 增强版向量嵌入
        embedding_client = create_siliconflow_client()
        embedded_chunks = generate_embeddings_enhanced(chunks, embedding_client)
        if not embedded_chunks:
            print("❌ 生成向量嵌入 - 失败")
            return 1
        print("✅ 生成向量嵌入 - 通过")

        # 步骤4: 增强版数据库保存
        if not save_to_database_enhanced(embedded_chunks):
            print("❌ 保存到数据库 - 失败")
            return 1
        print("✅ 保存到数据库 - 通过")

        # 步骤5: 验证入库结果
        if not verify_ingestion_enhanced():
            print("❌ 验证入库结果 - 失败")
            return 1
        print("✅ 验证入库结果 - 通过")

        passed = 5
        total = 5

    except Exception as e:
        print(f"❌ 处理流程失败: {e}")
        return 1

    print("\n" + "=" * 60)
    print(f"📊 增强版入库结果: {passed}/{total} 步骤完成")

    if passed == total:
        print("🎉 增强版知识库入库完成!")
        print("✅ 人教版教材已成功向量化并存储到数据库")
        print("🚀 使用了中文拼音修复和质量优化技术")
        print("🔍 现在可以进行高质量的语义检索和问答")
        return 0
    else:
        print("⚠️ 增强版知识库入库未完成，请检查错误信息")
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