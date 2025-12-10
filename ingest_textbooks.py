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
from sqlalchemy.orm import sessionmaker

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import TextLoader

def print_status(message: str, status: str):
    """打印状态信息"""
    icons = {"✅": "✅", "❌": "❌", "⚠️": "⚠️", "🔧": "🔧", "📚": "📚", "🔍": "🔍", "💾": "💾"}
    print(f"{icons.get(status, 'ℹ️')} {message}")


def load_textbook_documents(data_dir: str) -> List[Dict[str, Any]]:
    """
    加载教材文档

    Args:
        data_dir: 教材文档目录路径

    Returns:
        文档列表
    """
    print_status(f"加载教材文档: {data_dir}", "📚")

    documents = []
    data_path = Path(data_dir)

    if not data_path.exists():
        print_status(f"教材目录不存在: {data_dir}", "❌")
        return documents

    # 支持的文件扩展名
    supported_extensions = ['.md', '.txt']

    for file_path in data_path.rglob('*'):
        if file_path.suffix.lower() in supported_extensions:
            try:
                # 使用LangChain加载文档
                loader = TextLoader(str(file_path), encoding='utf-8')
                docs = loader.load()

                for doc in docs:
                    documents.append({
                        'content': doc.page_content,
                        'source': str(file_path),
                        'file_name': file_path.name,
                        'file_type': file_path.suffix.lower()
                    })

                print(f"  ✅ 已加载: {file_path.name}")

            except Exception as e:
                print(f"  ❌ 加载失败 {file_path.name}: {e}")

    print_status(f"共加载 {len(documents)} 个文档", "📚")
    return documents


def split_documents(documents: List[Dict[str, Any]],
                   chunk_size: int = 1000,
                   chunk_overlap: int = 200) -> List[Dict[str, Any]]:
    """
    分割文档为小片段

    Args:
        documents: 文档列表
        chunk_size: 片段大小
        chunk_overlap: 片段重叠大小

    Returns:
        分割后的文档片段列表
    """
    print_status(f"分割文档 (片段大小: {chunk_size}, 重叠: {chunk_overlap})", "🔍")

    # 创建文本分割器
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""]
    )

    chunks = []

    for doc in documents:
        try:
            # 分割文档
            split_docs = text_splitter.create_documents([doc['content']])

            for i, chunk in enumerate(split_docs):
                # 提取元数据
                metadata = extract_metadata(chunk.page_content, doc)

                chunks.append({
                    'content': chunk.page_content,
                    'metadata': metadata,
                    'source_file': doc['source'],
                    'file_name': doc['file_name'],
                    'chunk_index': i,
                    'total_chunks': len(split_docs)
                })

            print(f"  ✅ {doc['file_name']}: {len(split_docs)} 个片段")

        except Exception as e:
            print(f"  ❌ 分割失败 {doc['file_name']}: {e}")

    print_status(f"共生成 {len(chunks)} 个文档片段", "🔍")
    return chunks


def extract_metadata(content: str, doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    从文档内容中提取元数据

    Args:
        content: 文档内容
        doc: 文档信息

    Returns:
        元数据字典
    """
    metadata = {
        'file_name': doc['file_name'],
        'file_type': doc['file_type'],
        'source': doc['source'],
        'subject': '数学',  # 默认学科
        'grade': '三年级',  # 默认年级
        'processed_date': datetime.now().isoformat(),
        'content_length': len(content),
        'content_hash': hashlib.md5(content.encode('utf-8')).hexdigest()
    }

    # 从文件名推断信息
    file_name = doc['file_name'].lower()

    if '数学' in file_name or 'math' in file_name:
        metadata['subject'] = '数学'
    elif '语文' in file_name or 'chinese' in file_name:
        metadata['subject'] = '语文'
    elif '英语' in file_name or 'english' in file_name:
        metadata['subject'] = '英语'

    if '三年级' in file_name or 'grade3' in file_name or '3' in file_name:
        metadata['grade'] = '三年级'
    elif '二年级' in file_name or 'grade2' in file_name or '2' in file_name:
        metadata['grade'] = '二年级'
    elif '四年级' in file_name or 'grade4' in file_name or '4' in file_name:
        metadata['grade'] = '四年级'

    # 从内容中提取单元信息
    content_lower = content.lower()
    if '第' in content and '单元' in content:
        import re
        unit_pattern = r'第[一二三四五六七八九十百千万\d]+单元'
        matches = re.findall(unit_pattern, content)
        if matches:
            metadata['unit'] = matches[0]

    # 从内容中提取主题信息
    themes = []
    theme_keywords = {
        '加法': ['加法', '求和', '相加'],
        '减法': ['减法', '求差', '相减'],
        '乘法': ['乘法', '求积', '相乘'],
        '除法': ['除法', '求商', '相除'],
        '时间': ['时间', '小时', '分钟', '秒'],
        '质量': ['千克', '克', '重量', '质量'],
        '长度': ['米', '厘米', '毫米', '长度'],
        '几何': '图形 正方形 长方形 圆形 三角形'.split()
    }

    for theme, keywords in theme_keywords.items():
        for keyword in keywords:
            if keyword in content:
                themes.append(theme)
                break

    if themes:
        metadata['themes'] = list(set(themes))

    return metadata


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

    # 提取文本内容
    texts = [chunk['content'] for chunk in chunks]

    try:
        # 批量生成嵌入向量
        embeddings = embedding_client.embed_documents(texts)

        # 验证嵌入向量数量和维度
        if len(embeddings) != len(chunks):
            raise ValueError(f"嵌入向量数量({len(embeddings)})与片段数量({len(chunks)})不匹配")

        expected_dim = 1024  # BGE-M3的维度
        for i, embedding in enumerate(embeddings):
            if len(embedding) != expected_dim:
                print(f"  ⚠️ 片段 {i} 向量维度不正确: {len(embedding)} (期望: {expected_dim})")

        # 将嵌入向量添加到片段中
        for i, chunk in enumerate(chunks):
            chunk['embedding'] = embeddings[i]

        print_status(f"成功生成 {len(embeddings)} 个向量嵌入", "✅")
        return chunks

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

        # 批量保存
        saved_count = 0
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]

            for chunk in batch:
                # 创建TextbookChunk对象
                textbook_chunk = TextbookChunk(
                    content=chunk['content'],
                    embedding=chunk['embedding'],
                    metadata_json=chunk['metadata'],
                    source_file=chunk['source_file'],
                    chunk_index=chunk['chunk_index']
                )

                session.add(textbook_chunk)
                saved_count += 1

            # 提交批次
            session.commit()
            print(f"  ✅ 已保存 {min(i + batch_size, len(chunks))}/{len(chunks)} 个片段")

        session.close()

        print_status(f"成功保存 {saved_count} 个文档片段到数据库", "✅")
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
            print(f"  🔢 向量维度: {len(sample_chunk.embedding) if sample_chunk.embedding else 0}")
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

    # 步骤检查
    steps = [
        ("加载教材文档", lambda: load_textbook_documents(data_dir)),
        ("分割文档片段", lambda: split_documents(load_textbook_documents(data_dir), chunk_size, chunk_overlap)),
        ("初始化嵌入模型", lambda: initialize_embedding_model()),
        ("生成向量嵌入", lambda: generate_embeddings(
            split_documents(load_textbook_documents(data_dir), chunk_size, chunk_overlap),
            create_siliconflow_client()
        )),
        ("保存到数据库", lambda: save_to_database(
            generate_embeddings(
                split_documents(load_textbook_documents(data_dir), chunk_size, chunk_overlap),
                create_siliconflow_client()
            )
        )),
        ("验证入库结果", verify_ingestion)
    ]

    passed = 0
    total = len(steps)

    for name, step_func in steps:
        try:
            result = step_func()
            if result or result is None:  # None也表示成功
                passed += 1
                print(f"✅ {name} - 通过")
            else:
                print(f"❌ {name} - 失败")
                break
        except Exception as e:
            print(f"❌ {name} - 失败: {e}")
            break

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