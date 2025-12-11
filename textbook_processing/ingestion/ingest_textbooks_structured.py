#!/usr/bin/env python3
"""
结构化课文知识库入库脚本
Structured Textbook Knowledge Ingestion Script

专门处理人教版语文教材，按单元-课文结构进行智能分析和存储
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
from homeworkpal.document.chinese_textbook_analyzer import ChineseTextbookAnalyzer, LessonInfo, TextbookStructure
from sqlalchemy.orm import sessionmaker

def print_status(message: str, status: str):
    """打印状态信息"""
    icons = {"✅": "✅", "❌": "❌", "⚠️": "⚠️", "🔧": "🔧", "📚": "📚", "🔍": "🔍", "💾": "💾", "🚀": "🚀", "📖": "📖", "🏗️": "🏗️"}
    print(f"{icons.get(status, 'ℹ️')} {message}")


def process_textbook_structured(data_dir: str) -> TextbookStructure:
    """
    结构化处理教材文档，按单元-课文进行分析

    Args:
        data_dir: 教材文档目录路径

    Returns:
        结构化的教材信息
    """
    print_status(f"结构化处理教材文档: {data_dir}", "📖")

    all_chunks = []
    data_path = Path(data_dir)

    if not data_path.exists():
        print_status(f"教材目录不存在: {data_dir}", "❌")
        return None

    # 创建处理器
    pdf_processor = create_pdf_processor()
    text_splitter = create_pdf_splitter(chunk_size=2000, chunk_overlap=300)  # 更大的段落便于课文识别

    # 创建中文文本处理器
    embedding_model = SiliconFlowEmbeddingModel(
        api_key=os.getenv('SILICONFLOW_API_KEY'),
        base_url=os.getenv('SILICONFLOW_BASE_URL'),
        model_name='BAAI/bge-m3'
    )
    chinese_processor = ChineseTextProcessor(embedding_model)

    # 创建课文分析器
    textbook_analyzer = ChineseTextbookAnalyzer()

    pdf_files = [f for f in data_path.glob("*.pdf") if "语文" in f.name]
    if not pdf_files:
        print_status("未找到语文教材PDF文件", "❌")
        return None

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
            return None

    print(f"📚 共生成 {len(all_chunks)} 个高质量文档片段")

    # 使用智能分析器分析教材结构
    print_status("开始智能课文结构分析", "🧠")
    structure = textbook_analyzer.analyze_textbook_structure(all_chunks)

    if structure and structure.units:
        print_status(f"分析完成: {structure.total_lessons} 篇课文, {len(set(l.unit_number for l in structure.units))} 个单元", "🎉")

        # 显示统计信息
        stats = textbook_analyzer.get_lesson_statistics(structure)
        print(f"📊 教材统计:")
        print(f"  年级: {structure.grade} {structure.subject}")
        print(f"  总单元数: {stats['total_units']}")
        print(f"  总课文数: {stats['total_lessons']}")

        for unit_key, unit_info in stats['units'].items():
            print(f"  {unit_key} - {unit_info['unit_title']}: {len(unit_info['lessons'])} 篇课文")
    else:
        print_status("课文结构分析失败", "❌")
        return None

    return structure


def generate_structured_embeddings(structure: TextbookStructure, embedding_client) -> List[Dict[str, Any]]:
    """
    为结构化的课文生成向量嵌入

    Args:
        structure: 教材结构信息
        embedding_client: 嵌入模型客户端

    Returns:
        包含嵌入向量的课文数据列表
    """
    print_status(f"为 {structure.total_lessons} 篇课文生成向量嵌入", "🔍")

    if not structure or not structure.units:
        return []

    # 创建中文文本处理器
    chinese_processor = ChineseTextProcessor(embedding_client)

    all_lesson_embeddings = []
    total_chunks = 0

    for lesson in structure.units:
        if not lesson.content_chunks:
            continue

        print(f"  📖 处理课文: 第{lesson.unit_number}单元 第{lesson.lesson_number}课 - {lesson.lesson_title}")

        # 提取课文内容
        lesson_texts = [chunk['content'] for chunk in lesson.content_chunks]
        total_chunks += len(lesson_texts)

        try:
            # 批量生成向量嵌入
            embeddings, quality_results = chinese_processor.batch_vectorize_with_quality_control(
                lesson_texts,
                batch_size=3,  # 课文内容较长，使用更小的批处理
                max_retries=3,
                quality_threshold=0.6  # 课文内容质量要求更高
            )

            # 创建课文的完整元数据
            lesson_metadata = {
                'grade': structure.grade,
                'subject': structure.subject,
                'unit_number': lesson.unit_number,
                'unit_title': lesson.unit_title,
                'lesson_number': lesson.lesson_number,
                'lesson_title': lesson.lesson_title,
                'start_page': lesson.start_page,
                'end_page': lesson.end_page,
                'total_chunks': len(lesson.content_chunks),
                'text_processor': 'structured_chinese_processor',
                'analysis_timestamp': datetime.now().isoformat()
            }

            # 为每个内容片段创建完整记录
            for i, (chunk, embedding, quality) in enumerate(zip(lesson.content_chunks, embeddings, quality_results)):
                chunk_record = {
                    'content': chunk['content'],
                    'original_content': chunk['original_content'],
                    'embedding': embedding,
                    'content_hash': hashlib.md5(chunk['content'].encode('utf-8')).hexdigest(),
                    'metadata_json': {
                        **chunk['metadata'],
                        **lesson_metadata,
                        'chunk_index_in_lesson': i,
                        'quality_details': quality
                    },
                    'source_file': chunk['source'],
                    'chunk_index': chunk['chunk_index'],
                    'page_number': chunk['page_number'],
                    'quality_score': quality['score']
                }

                all_lesson_embeddings.append(chunk_record)

            print(f"    ✅ 成功生成 {len(embeddings)} 个嵌入向量")

        except Exception as e:
            print(f"    ❌ 课文处理失败: {e}")
            # 为失败的课文添加占位记录
            for chunk in lesson.content_chunks:
                chunk_record = {
                    'content': chunk['content'],
                    'embedding': [0.0] * 1024,  # 零向量占位
                    'content_hash': hashlib.md5(chunk['content'].encode('utf-8')).hexdigest(),
                    'metadata_json': {
                        **chunk['metadata'],
                        **{
                            'grade': structure.grade,
                            'subject': structure.subject,
                            'unit_number': lesson.unit_number,
                            'unit_title': lesson.unit_title,
                            'lesson_number': lesson.lesson_number,
                            'lesson_title': lesson.lesson_title,
                            'start_page': lesson.start_page,
                            'end_page': lesson.end_page,
                            'processing_error': str(e)
                        }
                    },
                    'source_file': chunk['source'],
                    'chunk_index': chunk['chunk_index'],
                    'page_number': chunk['page_number'],
                    'quality_score': 0.0
                }

                all_lesson_embeddings.append(chunk_record)

    print_status(f"成功为 {total_chunks} 个内容片段生成向量嵌入", "✅")
    return all_lesson_embeddings


def save_structured_to_database(lesson_data: List[Dict[str, Any]], batch_size: int = 10) -> bool:
    """
    将结构化的课文数据保存到数据库

    Args:
        lesson_data: 课文数据列表
        batch_size: 批处理大小

    Returns:
        是否保存成功
    """
    print_status(f"保存 {len(lesson_data)} 个结构化课文片段到数据库", "💾")

    try:
        # 创建数据库会话
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        # 去重：检查内容哈希是否已存在
        existing_hashes = set()
        existing_records = session.query(TextbookChunk.content_hash).filter(
            TextbookChunk.content_hash.in_([data.get('content_hash', '') for data in lesson_data])
        ).all()
        existing_hashes = set(record[0] for record in existing_records)

        # 过滤新片段
        new_chunks = [data for data in lesson_data if data.get('content_hash', '') not in existing_hashes]

        if not new_chunks:
            print_status("所有课文片段都已存在于数据库中", "✅")
            session.close()
            return True

        print(f"  📊 过滤重复后新增 {len(new_chunks)} 个片段")

        # 统计质量分布
        quality_scores = [chunk.get('quality_score', 0) for chunk in new_chunks]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        high_quality_count = sum(1 for score in quality_scores if score >= 0.8)

        print(f"  📈 平均质量评分: {avg_quality:.3f}")
        print(f"  🌟 高质量片段: {high_quality_count}/{len(new_chunks)} ({high_quality_count/len(new_chunks)*100:.1f}%)")

        # 按单元分组统计
        unit_stats = {}
        for chunk in new_chunks:
            metadata = chunk.get('metadata_json', {})
            unit_key = f"第{metadata.get('unit_number', 0)}单元"
            unit_stats[unit_key] = unit_stats.get(unit_key, 0) + 1

        print(f"  📚 按单元分布:")
        for unit_key, count in unit_stats.items():
            print(f"    {unit_key}: {count} 个片段")

        # 批量保存
        saved_count = 0
        for i in range(0, len(new_chunks), batch_size):
            batch = new_chunks[i:i + batch_size]

            for chunk in batch:
                # 创建TextbookChunk对象
                textbook_chunk = TextbookChunk(
                    content=chunk['content'],
                    embedding=chunk['embedding'],
                    metadata_json=chunk['metadata_json'],
                    source_file=chunk['source_file'],
                    chunk_index=chunk['chunk_index'],
                    content_hash=chunk['content_hash'],
                    page_number=chunk['page_number'],
                    quality_score=chunk['quality_score']
                )

                session.add(textbook_chunk)
                saved_count += 1

            # 提交批次
            session.commit()
            print(f"  ✅ 已保存 {min(i + batch_size, len(new_chunks))}/{len(new_chunks)} 个片段")

        session.close()

        print_status(f"成功保存 {saved_count} 个结构化课文片段到数据库", "✅")
        return True

    except Exception as e:
        print_status(f"保存到数据库失败: {e}", "❌")
        if 'session' in locals():
            session.rollback()
            session.close()
        return False


def verify_structured_ingestion():
    """验证结构化入库结果"""
    print_status("验证结构化入库结果", "🔍")

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

            # 显示结构化元数据
            metadata = sample_chunk.metadata_json or {}
            if metadata.get('unit_number'):
                print(f"  📖 单元课文信息:")
                print(f"    单元: 第{metadata.get('unit_number')}单元 {metadata.get('unit_title', '')}")
                print(f"    课文: 第{metadata.get('lesson_number')}课 {metadata.get('lesson_title', '')}")
                print(f"    页面: {metadata.get('start_page')}-{metadata.get('end_page')}")
                print(f"    处理器: {metadata.get('text_processor', 'unknown')}")

            # 按单元统计
            from sqlalchemy import func
            unit_stats = session.query(
                func.count(TextbookChunk.id).label('count')
            ).filter(
                TextbookChunk.metadata_json['unit_number'].astext != ''
            ).all()

            print(f"  📚 按单元统计: {unit_stats[0].count} 个结构化片段")

        session.close()
        print_status("结构化入库验证完成", "✅")
        return True

    except Exception as e:
        print_status(f"验证失败: {e}", "❌")
        return False


def main():
    """主函数"""
    print("🏗️ 作业搭子 RAG 系统 - 结构化课文知识库入库脚本")
    print("=" * 60)
    print()

    # 配置参数
    data_dir = os.getenv("TEXTBOOK_DIR", "data/textbooks")
    print(f"📂 教材目录: {data_dir}")
    print("📖 启用智能课文结构分析和单元-课文元数据存储")
    print()

    # 执行处理流程
    try:
        # 步骤1: 结构化文档分析
        structure = process_textbook_structured(data_dir)
        if not structure:
            print("❌ 结构化文档分析 - 失败")
            return 1
        print("✅ 结构化文档分析 - 通过")

        # 步骤2: 初始化嵌入模型
        if not initialize_embedding_model():
            print("❌ 初始化嵌入模型 - 失败")
            return 1
        print("✅ 初始化嵌入模型 - 通过")

        # 步骤3: 生成结构化向量嵌入
        embedding_client = create_siliconflow_client()
        lesson_embeddings = generate_structured_embeddings(structure, embedding_client)
        if not lesson_embeddings:
            print("❌ 生成结构化向量嵌入 - 失败")
            return 1
        print("✅ 生成结构化向量嵌入 - 通过")

        # 步骤4: 保存结构化数据到数据库
        if not save_structured_to_database(lesson_embeddings):
            print("❌ 保存结构化数据到数据库 - 失败")
            return 1
        print("✅ 保存结构化数据到数据库 - 通过")

        # 步骤5: 验证入库结果
        if not verify_structured_ingestion():
            print("❌ 验证结构化入库结果 - 失败")
            return 1
        print("✅ 验证结构化入库结果 - 通过")

        passed = 5
        total = 5

    except Exception as e:
        print(f"❌ 处理流程失败: {e}")
        return 1

    print("\n" + "=" * 60)
    print(f"📊 结构化入库结果: {passed}/{total} 步骤完成")

    if passed == total:
        print("🎉 结构化课文知识库入库完成!")
        print("✅ 人教版语文教材已按单元-课文结构化存储")
        print("🧖️ 使用了智能课文分析和结构化元数据技术")
        print("🔍 现在可以进行基于课文结构的精准语义检索和问答")
        return 0
    else:
        print("⚠️ 结构化课文知识库入库未完成，请检查错误信息")
        return 1


def initialize_embedding_model():
    """初始化嵌入模型"""
    try:
        client = create_siliconflow_client()

        # 测试连接
        test_text = "这是一篇关于春天的课文"
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