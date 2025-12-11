#!/usr/bin/env python3
"""
语文教材向量化导入脚本
Chinese Textbook Vectorization Import Script

从CSV文件导入语文教材内容到向量数据库
"""

import os
import sys
import pandas as pd
import hashlib
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from homeworkpal.database.connection import engine
from sqlalchemy.orm import sessionmaker
from homeworkpal.database.models import TextbookChunk
from homeworkpal.llm.base import BaseEmbeddingModel
from homeworkpal.llm.siliconflow import SiliconFlowEmbeddingModel

def print_status(message: str, status: str):
    """打印状态信息"""
    icons = {"✅": "✅", "❌": "❌", "⚠️": "⚠️", "🔧": "🔧", "📚": "📚", "🔍": "🔍", "💾": "💾", "📖": "📖"}
    print(f"{icons.get(status, 'ℹ️')} {message}")


def load_csv_data(csv_path: str) -> List[Dict[str, Any]]:
    """加载CSV数据"""
    print_status(f"加载CSV文件: {csv_path}", "📚")

    try:
        # 读取CSV文件
        df = pd.read_csv(csv_path)

        # 过滤高质量内容
        df = df[df['text_quality'].str.contains("'is_suitable': True", na=False)]

        # 转换为字典列表
        chunks = []
        for _, row in df.iterrows():
            # 解析文本质量信息
            try:
                text_quality = eval(row['text_quality']) if isinstance(row['text_quality'], str) else {}
                quality_score = text_quality.get('score', 0.8)
            except:
                quality_score = 0.8

            # 创建元数据
            metadata = {
                'pdf_file': '语文三上.pdf',
                'subject': '语文',
                'grade': '三年级',
                'page_number': int(row['page_number']),
                'unit_number': row['unit_number'] if pd.notna(row['unit_number']) else None,
                'unit_title': row['unit_title'] if pd.notna(row['unit_title']) else None,
                'lesson_number': row['lesson_number'] if pd.notna(row['lesson_number']) else None,
                'lesson_title': row['lesson_title'] if pd.notna(row['lesson_title']) else None,
                'lesson_start_page': row['lesson_start_page'] if pd.notna(row['lesson_start_page']) else None,
                'lesson_end_page': row['lesson_end_page'] if pd.notna(row['lesson_end_page']) else None,
                'content_length': int(row['content_length']) if pd.notna(row['content_length']) else 0,
                'processed_date': datetime.now().isoformat(),
                'content_type': '课文内容',
                'source_file': row['source_file']
            }

            # 添加内容分类信息（如果存在）
            if 'content_category' in row and pd.notna(row['content_category']):
                metadata['content_category'] = row['content_category']
                # 更新content_type以匹配分类
                if row['content_category'] == '课文':
                    metadata['content_type'] = '课文主体'
                elif row['content_category'] == '习作':
                    metadata['content_type'] = '习作指导'
                elif row['content_category'] == '交流':
                    metadata['content_type'] = '口语交际'
                elif row['content_category'] == '练习':
                    metadata['content_type'] = '课后练习'
                elif row['content_category'] == '日积月累':
                    metadata['content_type'] = '日积月累'
                elif row['content_category'] == '阅读':
                    metadata['content_type'] = '阅读材料'
                else:
                    metadata['content_type'] = '其他内容'

            chunk = {
                'content': row['content'],
                'page_number': int(row['page_number']),
                'chunk_index': int(row['chunk_index']),
                'metadata_json': metadata,
                'quality_score': quality_score,
                'source_file': row['source_file']
            }
            chunks.append(chunk)

        print_status(f"成功加载 {len(chunks)} 个高质量片段", "✅")
        return chunks

    except Exception as e:
        print_status(f"加载CSV文件失败: {e}", "❌")
        return []


def generate_content_hash(content: str) -> str:
    """生成内容哈希"""
    return hashlib.md5(content.encode('utf-8')).hexdigest()


def get_embedding_llm():
    """获取嵌入模型"""
    try:
        import os
        api_key = os.getenv("SILICONFLOW_API_KEY")
        base_url = os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")

        if not api_key:
            print_status("未设置SILICONFLOW_API_KEY环境变量", "⚠️")
            return None

        embedding_model = SiliconFlowEmbeddingModel(
            api_key=api_key,
            base_url=base_url
        )
        print_status("成功加载SiliconFlow嵌入模型", "✅")
        return embedding_model
    except Exception as e:
        print_status(f"加载嵌入模型失败: {e}", "⚠️")
        return None


def import_chunks_to_database(chunks: List[Dict[str, Any]], llm = None):
    """导入片段到数据库"""
    print_status("开始导入片段到数据库", "💾")

    try:
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        # 清除现有的语文教材数据
        existing_count = session.query(TextbookChunk).filter(
            TextbookChunk.source_file.like('%语文%')
        ).count()

        if existing_count > 0:
            print_status(f"清除现有 {existing_count} 个语文教材片段", "🔧")
            session.query(TextbookChunk).filter(
                TextbookChunk.source_file.like('%语文%')
            ).delete()
            session.commit()

        imported_count = 0
        skipped_count = 0

        for chunk_data in chunks:
            # 检查内容是否已存在
            content_hash = generate_content_hash(chunk_data['content'])
            existing = session.query(TextbookChunk).filter(
                TextbookChunk.content_hash == content_hash
            ).first()

            if existing:
                skipped_count += 1
                continue

            # 生成嵌入向量
            embedding = None
            if llm:
                try:
                    embedding = llm.embed_query(chunk_data['content'])
                except Exception as e:
                    print_status(f"生成嵌入向量失败: {e}", "⚠️")
                    embedding = None

            # 创建数据库记录
            db_chunk = TextbookChunk(
                content=chunk_data['content'],
                embedding=embedding,
                content_hash=content_hash,
                metadata_json=chunk_data['metadata_json'],
                source_file=chunk_data['source_file'],
                chunk_index=chunk_data['chunk_index'],
                page_number=chunk_data['page_number'],
                quality_score=chunk_data['quality_score']
            )

            session.add(db_chunk)
            imported_count += 1

            # 每10个片段提交一次
            if imported_count % 10 == 0:
                session.commit()
                print_status(f"已导入 {imported_count} 个片段", "💾")

        # 最终提交
        session.commit()
        session.close()

        print_status(f"成功导入 {imported_count} 个片段，跳过 {skipped_count} 个重复片段", "✅")
        return True

    except Exception as e:
        print_status(f"导入数据库失败: {e}", "❌")
        return False


def main():
    """主函数"""
    print("🎯 语文教材向量化导入脚本")
    print("=" * 50)

    # CSV文件路径
    csv_path = "/Users/lizhao/workspace/hulus/homeworkpal/exports/语文三上_content_cleaned.csv"

    if not os.path.exists(csv_path):
        print_status(f"CSV文件不存在: {csv_path}", "❌")
        return 1

    # 加载CSV数据
    chunks = load_csv_data(csv_path)
    if not chunks:
        print_status("没有可导入的数据", "❌")
        return 1

    # 获取嵌入模型
    llm = get_embedding_llm()

    # 导入到数据库
    if import_chunks_to_database(chunks, llm):
        print("\n🎉 语文教材向量化导入完成！")
        print("💡 可以开始进行智能检索测试")
        return 0
    else:
        print("\n⚠️ 导入失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())