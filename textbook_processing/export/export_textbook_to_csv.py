#!/usr/bin/env python3
"""
PDF教材数据导出到CSV脚本
Export Textbook PDF Data to CSV Script

将人教版语文教材的PDF内容按结构化方式导出到CSV文件
"""

import sys
import os
from pathlib import Path
import pandas as pd
import re
from typing import List, Dict, Any
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from homeworkpal.document import create_pdf_processor, create_pdf_splitter
from homeworkpal.document.chinese_text_processor import ChineseTextProcessor
from homeworkpal.document.chinese_textbook_analyzer import ChineseTextbookAnalyzer
from homeworkpal.llm.siliconflow import SiliconFlowEmbeddingModel


def print_status(message: str, status: str):
    """打印状态信息"""
    icons = {"✅": "✅", "❌": "❌", "⚠️": "⚠️", "🔧": "🔧", "📚": "📚", "🔍": "🔍", "💾": "💾", "🚀": "🚀", "📖": "📖"}
    print(f"{icons.get(status, 'ℹ️')} {message}")


def extract_textbook_content_to_csv(pdf_path: str, output_csv: str = "textbook_content.csv"):
    """
    将PDF教材内容提取到CSV文件

    Args:
        pdf_path: PDF文件路径
        output_csv: 输出CSV文件路径
    """
    print_status(f"开始处理教材PDF: {pdf_path}", "📚")

    # 1. 提取PDF基本内容
    pdf_processor = create_pdf_processor()
    pdf_result = pdf_processor.extract_text_from_pdf(pdf_path)

    print(f"📄 PDF信息:")
    print(f"  总页数: {pdf_result.get('total_pages', 0)}")
    print(f"  文件大小: {pdf_result.get('file_size', 0)} bytes")

    # 2. 按页提取文本内容
    pages_content = []
    for i, page in enumerate(pdf_result.get('pages', []), 1):
        page_text = page.get('text', '').strip()
        if page_text:
            pages_content.append({
                'page_number': i,
                'content': page_text,
                'content_length': len(page_text)
            })

    print(f"📝 提取了 {len(pages_content)} 页有效内容")

    # 3. 创建文本分段器
    text_splitter = create_pdf_splitter(chunk_size=1500, chunk_overlap=200)
    chunks = text_splitter.split_pdf_content(pdf_result)

    # 4. 应用中文文本处理（不进行向量化）
    print_status("应用中文文本处理和质量评估", "🔧")

    # 使用简化版本的处理器（不需要API密钥）
    processed_chunks = []
    for chunk in chunks:
        content = chunk['content']

        # 基础文本清理
        content = re.sub(r'\s+', ' ', content)  # 合并空白
        content = re.sub(r'\n+', ' ', content)  # 合并换行符

        # 移除明显的噪音
        content = re.sub(r'[^\u4e00-\u9fff\u3000-\u303f\uff00-\uffef\s，。！？；：""''（）【】《》0-9一二三四五六七八九十]', '', content)
        content = content.strip()

        if len(content) > 10:  # 只保留有意义的内容
            processed_chunks.append({
                'chunk_id': chunk['id'],
                'page_number': chunk.get('page_number', 0),
                'chunk_index': chunk.get('chunk_index', 0),
                'content': content,
                'content_length': len(content),
                'source_file': pdf_path
            })

    print(f"🔍 处理后得到 {len(processed_chunks)} 个有效片段")

    # 5. 使用智能分析器识别课文结构
    print_status("开始智能课文结构分析", "🧠")

    # 创建临时的嵌入模型用于文本处理器（不调用API）
    class DummyEmbeddingModel:
        def embed_query(self, text):
            return [0.0] * 1024  # 返回假向量

    dummy_embedding = DummyEmbeddingModel()
    chinese_processor = ChineseTextProcessor(dummy_embedding)

    # 更新处理器以不调用API
    def simple_preprocess(text):
        if not text:
            return text
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'[^\u4e00-\u9fff\u3000-\u303f\uff00-\uffef\s，。！？；：""''（）【】《》0-9一二三四五六七八九十]', '', text)
        text = text.strip()
        return text

    # 分析器也需要修改以避免API调用
    analyzer = ChineseTextbookAnalyzer()

    try:
        # 使用分析器进行结构分析
        structure = analyzer.analyze_textbook_structure(processed_chunks)

        print(f"📊 分析结果:")
        print(f"  年级: {structure.grade}")
        print(f"  科目: {structure.subject}")
        print(f"  单元数: {len(set(lesson.unit_number for lesson in structure.units))}")
        print(f"  课文数: {structure.total_lessons}")

        # 6. 将片段与课文结构关联
        chunk_with_structure = []
        for chunk in processed_chunks:
            # 查找对应的课文
            matched_lesson = None
            for lesson in structure.units:
                if (lesson.start_page <= chunk['page_number'] <= (lesson.end_page or 999)):
                    matched_lesson = lesson
                    break

            chunk_info = chunk.copy()
            if matched_lesson:
                chunk_info.update({
                    'unit_number': matched_lesson.unit_number,
                    'unit_title': matched_lesson.unit_title,
                    'lesson_number': matched_lesson.lesson_number,
                    'lesson_title': matched_lesson.lesson_title,
                    'lesson_start_page': matched_lesson.start_page,
                    'lesson_end_page': matched_lesson.end_page
                })
            else:
                chunk_info.update({
                    'unit_number': None,
                    'unit_title': None,
                    'lesson_number': None,
                    'lesson_title': None,
                    'lesson_start_page': None,
                    'lesson_end_page': None
                })

            # 添加文本质量评估
            chunk_info['text_quality'] = assess_text_quality(chunk_info['content'])

            chunk_with_structure.append(chunk_info)

    except Exception as e:
        print_status(f"结构分析失败，使用基础数据: {e}", "⚠️")
        chunk_with_structure = []
        for chunk in processed_chunks:
            chunk_info = chunk.copy()
            chunk_info.update({
                'unit_number': None,
                'unit_title': None,
                'lesson_number': None,
                'lesson_title': None,
                'lesson_start_page': None,
                'lesson_end_page': None,
                'text_quality': assess_text_quality(chunk_info['content'])
            })
            chunk_with_structure.append(chunk_info)

    # 7. 转换为DataFrame并保存
    print_status("创建CSV数据文件", "💾")

    df = pd.DataFrame(chunk_with_structure)

    # 重新排列列顺序
    column_order = [
        'chunk_id', 'page_number', 'chunk_index', 'unit_number', 'unit_title',
        'lesson_number', 'lesson_title', 'lesson_start_page', 'lesson_end_page',
        'content_length', 'text_quality', 'content', 'source_file'
    ]

    # 确保所有列都存在
    for col in column_order:
        if col not in df.columns:
            df[col] = None

    df = df[column_order]

    # 保存到CSV
    df.to_csv(output_csv, index=False, encoding='utf-8-sig')

    print_status(f"成功导出到CSV: {output_csv}", "✅")
    print(f"📊 CSV统计:")
    print(f"  总行数: {len(df)}")
    print(f"  有课文信息的: {df['lesson_title'].notna().sum()}")
    print(f"  平均内容长度: {df['content_length'].mean():.1f}")

    # 8. 生成统计报告
    generate_summary_report(df, output_csv.replace('.csv', '_summary.txt'))

    return df


def assess_text_quality(text: str) -> Dict[str, Any]:
    """
    评估文本质量（不调用API的简化版本）

    Args:
        text: 文本内容

    Returns:
        质量评估结果
    """
    if not text:
        return {'score': 0.0, 'is_suitable': False, 'reason': '文本为空'}

    score = 0.5  # 基础分数
    reasons = []

    # 长度评分
    length = len(text)
    if 50 <= length <= 500:
        score += 0.3
        reasons.append('长度适中')
    elif length < 20:
        score -= 0.3
        reasons.append('文本过短')
    elif length > 1000:
        score -= 0.1
        reasons.append('文本较长')

    # 中文字符比例
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    if length > 0:
        chinese_ratio = chinese_chars / length
        score += chinese_ratio * 0.2
        if chinese_ratio > 0.7:
            reasons.append('中文为主')

    # 教育关键词
    edu_keywords = ['课文', '生字', '词语', '练习', '阅读', '学习', '理解']
    keyword_count = sum(1 for keyword in edu_keywords if keyword in text)
    if keyword_count > 0:
        score += min(keyword_count * 0.05, 0.2)
        reasons.append('教育相关')

    score = max(0.0, min(1.0, score))

    return {
        'score': score,
        'is_suitable': score > 0.4,
        'reason': ', '.join(reasons) if reasons else '基础质量'
    }


def generate_summary_report(df: pd.DataFrame, report_path: str):
    """
    生成数据统计报告

    Args:
        df: 数据DataFrame
        report_path: 报告文件路径
    """
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("人教版语文教材数据统计报告\n")
        f.write("=" * 50 + "\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("基本统计:\n")
        f.write(f"  总片段数: {len(df)}\n")
        f.write(f"  总页数: {df['page_number'].nunique()}\n")
        f.write(f"  平均片段长度: {df['content_length'].mean():.1f} 字符\n")
        f.write(f"  中位数片段长度: {df['content_length'].median():.1f} 字符\n\n")

        # 单元统计
        if df['unit_number'].notna().any():
            unit_stats = df[df['unit_number'].notna()].groupby('unit_number').agg({
                'chunk_id': 'count',
                'content_length': 'mean'
            }).round(1)

            f.write("单元分布:\n")
            for unit_num, row in unit_stats.iterrows():
                f.write(f"  第{unit_num}单元: {row['chunk_id']}个片段, 平均长度{row['content_length']:.1f}字符\n")
            f.write("\n")

        # 课文统计
        if df['lesson_title'].notna().any():
            lesson_stats = df[df['lesson_title'].notna()].groupby('lesson_title').agg({
                'chunk_id': 'count',
                'content_length': 'mean'
            }).round(1)

            f.write("课文分布 (前10篇):\n")
            for lesson_title, row in lesson_stats.head(10).iterrows():
                f.write(f"  {lesson_title}: {row['chunk_id']}个片段, 平均长度{row['content_length']:.1f}字符\n")
            f.write("\n")

        # 质量分布
        quality_stats = df['text_quality'].apply(lambda x: x.get('score', 0) if isinstance(x, dict) else 0)
        f.write("质量分布:\n")
        f.write(f"  平均质量分数: {quality_stats.mean():.3f}\n")
        f.write(f"  高质量片段(>0.7): {(quality_stats > 0.7).sum()}个\n")
        f.write(f"  中等质量片段(0.4-0.7): {((quality_stats >= 0.4) & (quality_stats <= 0.7)).sum()}个\n")
        f.write(f"  低质量片段(<0.4): {(quality_stats < 0.4).sum()}个\n")

    print_status(f"统计报告已保存: {report_path}", "📊")


def main():
    """主函数"""
    print("🏗️ 作业搭子 RAG 系统 - PDF教材数据导出到CSV")
    print("=" * 60)
    print()

    # 配置参数
    data_dir = os.getenv("TEXTBOOK_DIR", "data/textbooks")
    output_dir = Path("exports")
    output_dir.mkdir(exist_ok=True)

    print(f"📂 教材目录: {data_dir}")
    print(f"📁 输出目录: {output_dir}")
    print()

    # 查找语文教材PDF
    data_path = Path(data_dir)
    if not data_path.exists():
        print_status(f"教材目录不存在: {data_dir}", "❌")
        return 1

    pdf_files = [f for f in data_path.glob("*.pdf") if "语文" in f.name]
    if not pdf_files:
        print_status("未找到语文教材PDF文件", "❌")
        return 1

    # 处理每个PDF文件
    for pdf_file in pdf_files:
        try:
            output_csv = output_dir / f"{pdf_file.stem}_content.csv"
            df = extract_textbook_content_to_csv(str(pdf_file), str(output_csv))

            print(f"✅ 完成处理: {pdf_file.name} -> {output_csv.name}")

        except Exception as e:
            print(f"❌ 处理失败 {pdf_file.name}: {e}")
            continue

    print()
    print("🎉 PDF数据导出完成!")
    print("📋 下一步:")
    print("  1. 检查CSV文件中的数据结构")
    print("  2. 验证单元和课文信息的准确性")
    print("  3. 根据需要调整和清理数据")
    print("  4. 准备进行向量化处理")

    return 0


if __name__ == "__main__":
    sys.exit(main())