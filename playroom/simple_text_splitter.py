"""
简化的文本分段器
Simple Text Splitter for PDF Processing
"""

import re
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class SimpleTextSplitter:
    """简单的文本分段器，不依赖langchain"""

    def __init__(self, chunk_size: int = 1500, chunk_overlap: int = 200):
        """
        初始化文本分段器

        Args:
            chunk_size: 分段大小（字符数）
            chunk_overlap: 分段重叠大小（字符数）
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> List[str]:
        """
        分割文本为小片段

        Args:
            text: 待分割的文本

        Returns:
            文本片段列表
        """
        if not text or len(text) <= self.chunk_size:
            return [text] if text else []

        chunks = []
        separators = ["\n\n", "\n", "。", "！", "？", "；", "，", " "]

        # 递归分割
        def recursive_split(content: str, separators: List[str]) -> List[str]:
            if len(content) <= self.chunk_size:
                return [content]

            if not separators:
                # 最后的分割：按字符分割
                return [
                    content[i:i + self.chunk_size]
                    for i in range(0, len(content), self.chunk_size - self.chunk_overlap)
                ]

            separator = separators[0]
            parts = content.split(separator)

            if len(parts) == 1:
                return recursive_split(content, separators[1:])

            chunks = []
            current_chunk = ""

            for part in parts:
                test_chunk = current_chunk + (separator if current_chunk else "") + part

                if len(test_chunk) <= self.chunk_size:
                    current_chunk = test_chunk
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = part

            if current_chunk:
                chunks.append(current_chunk)

            # 如果还有太长的片段，继续分割
            final_chunks = []
            for chunk in chunks:
                if len(chunk) > self.chunk_size:
                    final_chunks.extend(recursive_split(chunk, separators[1:]))
                else:
                    final_chunks.append(chunk)

            return final_chunks

        return recursive_split(text, separators)

    def split_pdf_content(self, pdf_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        分割PDF文档内容

        Args:
            pdf_result: PDF处理结果

        Returns:
            分割后的文档片段列表
        """
        try:
            logger.info(f"开始分割PDF文档: {pdf_result['file_name']}")

            pages = pdf_result.get('pages', [])
            if not pages:
                logger.warning("PDF没有可处理的页面")
                return []

            chunks = []

            for page in pages:
                page_text = page.get('text', '')
                page_number = page.get('page_number', 0)

                if not page_text.strip():
                    continue

                # 分割文本
                text_chunks = self.split_text(page_text)

                for i, chunk_text in enumerate(text_chunks):
                    chunk_text = chunk_text.strip()
                    if not chunk_text:
                        continue

                    # 评估文本质量
                    quality_score = self._assess_text_quality(chunk_text)

                    if quality_score > 0.3:
                        chunk_id = f"{pdf_result['file_name']}_page_{page_number}_chunk_{i+1}"

                        chunk = {
                            'id': chunk_id,
                            'content': chunk_text,
                            'page_number': page_number,
                            'chunk_index': i,
                            'total_chunks': len(text_chunks),
                            'text_length': len(chunk_text),
                            'word_count': len(chunk_text.split()),
                            'quality_score': quality_score,
                            'metadata': {
                                'pdf_file': pdf_result['file_name'],
                                'subject': pdf_result['education_metadata'].get('subject', '未识别'),
                                'grade': pdf_result['education_metadata'].get('grade', '未识别'),
                                'page_number': page_number,
                                'total_pages': pdf_result.get('total_pages', 0),
                                'processed_date': pdf_result.get('processed_date', ''),
                                'content_type': self._identify_content_type(chunk_text),
                                'has_images': len(page.get('images', [])) > 0
                            }
                        }

                        chunks.append(chunk)

            logger.info(f"PDF分割完成，共生成 {len(chunks)} 个片段")
            return chunks

        except Exception as e:
            logger.error(f"分割PDF内容时出错: {e}")
            raise

    def _assess_text_quality(self, text: str) -> float:
        """评估文本质量"""
        if not text:
            return 0.0

        score = 1.0
        length = len(text)

        # 文本长度评分
        if length < 50:
            score -= 0.5
        elif length > 2000:
            score -= 0.3

        # 中文内容评分
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        if chinese_chars == 0:
            score -= 0.5
        else:
            chinese_ratio = chinese_chars / length
            score += chinese_ratio * 0.3

        # 教育内容关键词评分
        education_keywords = [
            '练习', '例题', '答案', '知识点', '学习', '思考', '讨论',
            '数学', '语文', '英语', '运算', '概念', '方法', '技巧',
            '乘法表', '加法', '减法', '应用题', '综合题'
        ]

        keyword_count = sum(1 for keyword in education_keywords if keyword in text)
        score += min(keyword_count * 0.1, 0.5)

        return max(0.0, min(1.0, score))

    def _identify_content_type(self, text: str) -> str:
        """识别内容类型"""
        text_lower = text.lower()

        if re.search(r'例题|练习|测试|作业|考试', text_lower):
            return '练习题'
        elif re.search(r'概念|定义|解释|说明', text_lower):
            return '概念讲解'
        elif re.search(r'步骤|过程|方法', text_lower):
            return '方法步骤'
        elif re.search(r'公式|定理|定律', text_lower):
            return '公式定理'
        else:
            return '正文内容'


def create_simple_splitter(chunk_size: int = 1500, chunk_overlap: int = 200) -> SimpleTextSplitter:
    """创建简单文本分段器的工厂函数"""
    return SimpleTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)