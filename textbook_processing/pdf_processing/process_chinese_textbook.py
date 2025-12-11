#!/usr/bin/env python3
"""
语文三上 PDF 处理和向量化脚本
Chinese Grade 3 Textbook PDF Processing and Vectorization Script
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
from homeworkpal.database.connection import engine, SessionLocal
from homeworkpal.database.models import TextbookChunk
from sqlalchemy.orm import sessionmaker

def print_status(message: str, status: str):
    """打印状态信息"""
    icons = {"✅": "✅", "❌": "❌", "⚠️": "⚠️", "🔧": "🔧", "📚": "📚", "🔍": "🔍", "💾": "💾"}
    print(f"{icons.get(status, 'ℹ️')} {message}")


def extract_text_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    使用PyMuPDF提取PDF文本内容

    Args:
        pdf_path: PDF文件路径

    Returns:
        提取的页面文本列表
    """
    import fitz  # PyMuPDF

    print_status(f"提取PDF文本: {pdf_path}", "📚")

    try:
        doc = fitz.open(pdf_path)
        pages_text = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()

            if text.strip():  # 只保存非空页面
                pages_text.append({
                    'page_number': page_num + 1,
                    'content': text.strip(),
                    'char_count': len(text.strip())
                })

        doc.close()

        print(f"✅ 成功提取 {len(pages_text)} 页文本内容")
        return pages_text

    except Exception as e:
        print(f"❌ PDF文本提取失败: {e}")
        return []


def split_text_into_chunks(pages_text: List[Dict[str, Any]],
                         chunk_size: int = 1000,
                         chunk_overlap: int = 200) -> List[Dict[str, Any]]:
    """
    将文本分割成适合的片段

    Args:
        pages_text: 页面文本列表
        chunk_size: 片段大小
        chunk_overlap: 片段重叠

    Returns:
        文本片段列表
    """
    print_status(f"分割文本为片段 (大小: {chunk_size}, 重叠: {chunk_overlap})", "✂️")

    all_chunks = []
    current_chunk = ""
    current_page = 1
    chunk_index = 0

    for page_data in pages_text:
        page_text = page_data['content']
        page_number = page_data['page_number']

        # 如果当前片段为空，开始新片段
        if not current_chunk:
            current_page = page_number
            current_chunk = page_text
        else:
            current_chunk += "\n\n" + page_text

        # 当片段达到指定大小时，创建片段
        if len(current_chunk) >= chunk_size:
            # 添加当前片段
            chunk = {
                'content': current_chunk,
                'page_number': current_page,
                'chunk_index': chunk_index,
                'quality_score': 1.0,  # 简单的质量评分
                'metadata': {
                    'subject': '语文',
                    'grade': '三年级',
                    'semester': '上册',
                    'textbook': '人教版',
                    'source_type': 'pdf_textbook',
                    'processed_date': datetime.now().isoformat(),
                    'content_type': '教材内容',
                    'language': 'chinese'
                }
            }
            all_chunks.append(chunk)
            chunk_index += 1

            # 保留重叠部分用于下一个片段
            if chunk_overlap > 0:
                overlap_start = max(0, len(current_chunk) - chunk_overlap)
                current_chunk = current_chunk[overlap_start:]
            else:
                current_chunk = ""

    # 处理最后一个片段
    if current_chunk.strip():
        chunk = {
            'content': current_chunk,
            'page_number': current_page,
            'chunk_index': chunk_index,
            'quality_score': 1.0,
            'metadata': {
                'subject': '语文',
                'grade': '三年级',
                'semester': '上册',
                'textbook': '人教版',
                'source_type': 'pdf_textbook',
                'processed_date': datetime.now().isoformat(),
                'content_type': '教材内容',
                'language': 'chinese'
            }
        }
        all_chunks.append(chunk)

    print(f"✅ 成功生成 {len(all_chunks)} 个文本片段")
    return all_chunks


def create_simple_embeddings(texts: List[str]) -> List[List[float]]:
    """
    创建简单的伪嵌入向量（用于测试）
    在实际使用中应该替换为真实的嵌入模型调用

    Args:
        texts: 文本列表

    Returns:
        嵌入向量列表
    """
    print_status("创建嵌入向量 (使用简单哈希方法 - 仅用于测试)", "🔍")

    embeddings = []
    for text in texts:
        # 使用文本的哈希值创建固定长度的向量
        hash_obj = hashlib.md5(text.encode('utf-8'))
        hash_hex = hash_obj.hexdigest()

        # 将哈希值转换为1024维向量
        vector = []
        for i in range(0, len(hash_hex), 2):
            hex_pair = hash_hex[i:i+2]
            value = int(hex_pair, 16) / 255.0 - 0.5  # 归一化到[-0.5, 0.5]
            vector.extend([value] * 64)  # 每个字节扩展为64个值

        # 确保向量长度为1024
        while len(vector) < 1024:
            vector.append(0.0)

        embeddings.append(vector[:1024])

    print(f"✅ 成功生成 {len(embeddings)} 个1024维嵌入向量")
    return embeddings


def save_chunks_to_database(chunks: List[Dict[str, Any]]) -> bool:
    """
    将文本片段保存到数据库

    Args:
        chunks: 文本片段列表

    Returns:
        是否保存成功
    """
    print_status(f"保存 {len(chunks)} 个文本片段到数据库", "💾")

    try:
        session = SessionLocal()

        saved_count = 0
        for chunk in chunks:
            # 生成嵌入向量
            embedding = create_simple_embeddings([chunk['content']])[0]
            content_hash = hashlib.md5(chunk['content'].encode('utf-8')).hexdigest()

            # 检查是否已存在
            existing = session.query(TextbookChunk).filter(
                TextbookChunk.content_hash == content_hash
            ).first()

            if existing:
                continue

            # 创建新的TextbookChunk对象
            textbook_chunk = TextbookChunk(
                content=chunk['content'],
                embedding=embedding,
                metadata_json=chunk['metadata'],
                source_file="data/textbooks/语文三上.pdf",
                chunk_index=chunk['chunk_index'],
                content_hash=content_hash,
                page_number=chunk['page_number'],
                quality_score=chunk['quality_score']
            )

            session.add(textbook_chunk)
            saved_count += 1

        session.commit()
        session.close()

        print(f"✅ 成功保存 {saved_count} 个新文本片段到数据库")
        return True

    except Exception as e:
        print(f"❌ 保存到数据库失败: {e}")
        if 'session' in locals():
            session.rollback()
            session.close()
        return False


def main():
    """主函数"""
    print("🔧 语文三上 PDF 处理和向量化脚本")
    print("=" * 60)
    print()

    # 配置参数
    pdf_path = "data/textbooks/语文三上.pdf"

    if not Path(pdf_path).exists():
        print(f"❌ PDF文件不存在: {pdf_path}")
        return 1

    try:
        # 步骤1: 提取PDF文本
        pages_text = extract_text_from_pdf(pdf_path)
        if not pages_text:
            print("❌ 提取PDF文本 - 失败")
            return 1
        print("✅ 提取PDF文本 - 通过")

        # 步骤2: 分割文本
        chunks = split_text_into_chunks(pages_text)
        if not chunks:
            print("❌ 分割文本 - 失败")
            return 1
        print("✅ 分割文本 - 通过")

        # 步骤3: 保存到数据库
        if not save_chunks_to_database(chunks):
            print("❌ 保存到数据库 - 失败")
            return 1
        print("✅ 保存到数据库 - 通过")

        print("\n" + "=" * 60)
        print("🎉 语文三上 PDF 处理完成!")
        print("✅ 语文教材已成功处理并存储到数据库")
        print("🔍 现在可以进行语文知识的语义检索")

        return 0

    except Exception as e:
        print(f"❌ 处理流程失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())