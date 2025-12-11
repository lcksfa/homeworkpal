"""
文档分段器
Document Splitter for Homework Pal

针对PDF文档内容的智能分段策略
"""

import re
from typing import List, Dict, Any, Optional
# 简化的Document类
class Document:
    """简化的文档类，替代LangChain的Document"""
    def __init__(self, page_content: str, metadata: Dict[str, Any] = None):
        self.page_content = page_content
        self.metadata = metadata or {}

# 简化的文本分割器
class SimpleRecursiveTextSplitter:
    """简化的递归文本分割器"""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200,
                 length_function=len, separators: List[str] = None):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.length_function = length_function
        self.separators = separators or ["\n\n", "\n", " ", ""]

    def create_documents(self, texts: List[str]) -> List[Document]:
        """创建文档列表"""
        documents = []
        for text in texts:
            chunks = self._split_text(text)
            for chunk in chunks:
                documents.append(Document(page_content=chunk))
        return documents

    def _split_text(self, text: str) -> List[str]:
        """分割文本"""
        if self.length_function(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            # 找到最佳分割点
            end = start + self.chunk_size
            if end > len(text):
                end = len(text)

            # 如果不是最后一段，尝试在分隔符处分割
            if end < len(text):
                best_split = end
                for separator in self.separators:
                    split_pos = text.rfind(separator, start, end)
                    if split_pos > start:
                        best_split = split_pos + len(separator)
                        break

                end = best_split

            chunk = text[start:end]
            if chunk.strip():
                chunks.append(chunk.strip())

            # 计算下一个起始位置（考虑重叠）
            start = max(start + 1, end - self.chunk_overlap)

        return chunks
import logging

logger = logging.getLogger(__name__)


class PDFTextSplitter:
    """PDF文档智能分段器"""

    def __init__(self,
                 chunk_size: int = 1500,
                 chunk_overlap: int = 200,
                 respect_sentence_endings: bool = True,
                 respect_paragraph_breaks: bool = True):
        """
        初始化PDF文档分段器

        Args:
            chunk_size: 分段大小（字符数）
            chunk_overlap: 分段重叠大小（字符数）
            respect_sentence_endings: 是否尊重句子结尾
            respect_paragraph_breaks: 是否尊重段落分隔
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.respect_sentence_endings = respect_sentence_endings
        self.respect_paragraph_breaks = respect_paragraph_breaks

        # 创建简化的文本分割器
        self.text_splitter = SimpleRecursiveTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=self._get_pdf_separators()
        )

    def _get_pdf_separators(self) -> List[str]:
        """获取PDF文档的分隔符列表"""
        separators = []

        if self.respect_paragraph_breaks:
            # 段落分隔符（双换行以上）
            separators.append("\n\n\n")

        if self.respect_sentence_endings:
            # 句子分隔符
            separators.extend([
                "。\n",    # 句号+换行
                "！\n",    # 感叹号+换行
                "？\n",    # 问号+换行
                "；\n",    # 分号+换行
                "：\n",    # 冒号+换行
            ])

        # 常规分隔符
        separators.extend([
            "\n",         # 单个换行
            "。",         # 句号
            "！",         # 感叹号
            "？",         # 问号
            "；",         # 分号
            "：",         # 冒号
            "，",         # 逗号
            " ",          # 空格
        ])

        return separators

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

            # 获取PDF的页面信息
            pages = pdf_result.get('pages', [])

            if not pages:
                logger.warning("PDF没有可处理的页面")
                return []

            chunks = []

            for page in pages:
                page_chunks = self._split_page_content(page, pdf_result)
                chunks.extend(page_chunks)

            logger.info(f"PDF分割完成，共生成 {len(chunks)} 个片段")
            return chunks

        except Exception as e:
            logger.error(f"分割PDF内容时出错: {e}")
            raise

    def _split_page_content(self, page: Dict[str, Any], pdf_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """分割单个页面的内容"""
        page_text = page.get('text', '')
        page_number = page.get('page_number', 0)

        if not page_text.strip():
            return []

        # 预处理页面文本
        cleaned_text = self._preprocess_page_text(page_text)

        # 使用LangChain进行文本分割
        documents = self.text_splitter.create_documents([cleaned_text])

        chunks = []
        for i, doc in enumerate(documents):
            # 生成唯一标识符
            chunk_id = f"{pdf_result['file_name']}_page_{page_number}_chunk_{i+1}"

            # 检查片段质量
            text_quality = self._assess_text_quality(doc.page_content)

            if text_quality['is_meaningful']:
                chunk = {
                    'id': chunk_id,
                    'content': doc.page_content.strip(),
                    'page_number': page_number,
                    'chunk_index': i,
                    'total_chunks': len(documents),
                    'text_length': len(doc.page_content),
                    'word_count': len(doc.page_content.split()),
                    'quality_score': text_quality['score'],
                    'content_type': self._identify_content_type(doc.page_content),
                    'metadata': {
                        'pdf_file': pdf_result['file_name'],
                        'subject': pdf_result['education_metadata'].get('subject', '未识别'),
                        'grade': pdf_result['education_metadata'].get('grade', '未识别'),
                        'page_number': page_number,
                        'total_pages': pdf_result.get('total_pages', 0),
                        'processed_date': pdf_result.get('processed_date', ''),
                        'content_type': self._identify_content_type(doc.page_content),
                        'has_images': len(page.get('images', [])) > 0
                    }
                }

                chunks.append(chunk)

        return chunks

    def _preprocess_page_text(self, text: str) -> str:
        """预处理页面文本"""
        if not text:
            return text

        # 移除页面头部和尾部的页码等
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            line = line.strip()

            # 跳过页码行
            if self._is_page_number_line(line):
                continue

            # 跳过空行（保留结构）
            if line or cleaned_lines:  # 如果是第一行或者已经有内容，保留空行
                cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)

    def _is_page_number_line(self, line: str) -> bool:
        """判断是否为页码行"""
        line = line.strip()

        # 常见的页码模式
        page_patterns = [
            r'^\d+$',                      # 纯数字
            r'^第\d+页$',                   # 第X页
            r'^Page\s*\d+$',               # Page X
            r'^\d+\s*/\s*\d+$',            # 1/50
            r'^-\s*\d+\s*-$',               # - 5 -
            r'^\[\s*\d+\s*\]$',              # [1]
            r'^\(\s*\d+\s*\)$',              # (1)
        ]

        for pattern in page_patterns:
            if re.match(pattern, line):
                return True

        return False

    def _assess_text_quality(self, text: str) -> Dict[str, Any]:
        """评估文本质量"""
        text = text.strip()

        if not text:
            return {'is_meaningful': False, 'score': 0.0}

        score = 1.0  # 基础分数

        # 文本长度评分（太短或太长都扣分）
        length = len(text)
        if length < 50:
            score -= 0.5
        elif length > 2000:
            score -= 0.3

        # 包含中文内容的评分
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

        # 结构化内容评分（包含标题、列表等）
        if re.search(r'^(第.*[：:])', text):
            score += 0.2
        if re.search(r'^\d+[、.]', text):
            score += 0.2
        if re.search(r'^\*|^-', text):
            score += 0.1

        # 最终评分
        score = max(0.0, min(1.0, score))

        return {
            'is_meaningful': score > 0.3,  # 最低0.3分才认为有意义
            'score': score,
            'length': length,
            'chinese_chars': chinese_chars,
            'keyword_count': keyword_count
        }

    def _identify_content_type(self, text: str) -> str:
        """识别内容类型"""
        text_lower = text.lower()

        # 教学内容类型
        if re.search(r'例题|练习|测试|作业|考试', text_lower):
            return '练习题'
        elif re.search(r'概念|定义|解释|说明', text_lower):
            return '概念讲解'
        elif re.search(r'步骤|过程|方法', text_lower):
            return '方法步骤'
        elif re.search(r'公式|定理|定律', text_lower):
            return '公式定理'
        elif re.search(r'图片|插图|图表', text_lower):
            return '图示说明'
        elif re.search(r'总结|小结|回顾', text_lower):
            return '总结复习'
        else:
            return '正文内容'

    def get_splitting_stats(self) -> Dict[str, Any]:
        """获取分段统计信息"""
        return {
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap,
            'respect_sentence_endings': self.respect_sentence_endings,
            'respect_paragraph_breaks': self.respect_paragraph_breaks,
            'separators_count': len(self._get_pdf_separators())
        }


class ChineseTextbookSplitter(PDFTextSplitter):
    """语文教材专用文本分割器"""

    def __init__(self,
                 chunk_size: int = 1200,          # 语文内容稍小，保持语义完整
                 chunk_overlap: int = 150,
                 respect_sentence_endings: bool = True,
                 respect_paragraph_breaks: bool = True):
        """
        初始化语文教材文本分割器

        Args:
            chunk_size: 分段大小（字符数）
            chunk_overlap: 分段重叠大小（字符数）
            respect_sentence_endings: 是否尊重句子结尾
            respect_paragraph_breaks: 是否尊重段落分隔
        """
        super().__init__(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            respect_sentence_endings=respect_sentence_endings,
            respect_paragraph_breaks=respect_paragraph_breaks
        )

        # 创建语文教材专用的文本分割器
        self.text_splitter = SimpleRecursiveTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=self._get_chinese_separators()
        )

    def _get_chinese_separators(self) -> List[str]:
        """获取语文教材专用分隔符列表"""
        separators = []

        # 语文教材结构分隔符（优先级从高到低）
        separators.extend([
            r'\n第[一二三四五六七八九十\d]+课',        # 课文分隔
            r'\n第[一二三四五六七八九十\d]+单元',      # 单元分隔
            r'\n\s*[一二三四五六七八九十\d]+\s*、',     # 编号列表
            r'\n\s*（[一二三四五六七八九十\d]+）',     # 括号编号
            r'\n\s*[1-9]\d*\s*[、\.]',             # 数字编号
            r'\n\s*[①②③④⑤⑥⑦⑧⑨⑩]',             # 圆圈数字
            r'\n\s*[①②③④⑤⑥⑦⑧⑨⑩]',               # 圆圈数字（另一种格式）
            r'\n\s*[①②③④⑤⑥⑦⑧⑨⑩]',               # 圆圈数字（重复确保匹配）
            r'\n\s*[①②③④⑤⑥⑦⑧⑨⑩]',               # 圆圈数字（最后一次）
        ])

        # 段落分隔符
        if self.respect_paragraph_breaks:
            separators.append("\n\n\n")
            separators.append("\n\n")

        # 句子分隔符（语文教材常用）
        if self.respect_sentence_endings:
            separators.extend([
                "。\n",    # 句号+换行
                "！\n",    # 感叹号+换行
                "？\n",    # 问号+换行
                "；\n",    # 分号+换行
                "：\n",    # 冒号+换行
            ])

        # 标点符号分隔符
        separators.extend([
            "。",         # 句号
            "！",         # 感叹号
            "？",         # 问号
            "；",         # 分号
            "：",         # 冒号
            "，",         # 逗号
            "、",         # 顿号
            "\n",         # 单个换行
            " ",          # 空格
        ])

        return separators

    def _identify_chinese_content_type(self, text: str, structure_info: Dict[str, Any] = None) -> str:
        """
        识别语文教材内容类型

        Args:
            text: 文本内容
            structure_info: 结构识别信息

        Returns:
            内容类型字符串
        """
        # 如果有结构信息，优先使用
        if structure_info and structure_info.get('content_type') != '未识别':
            return structure_info['content_type']

        text_lower = text.lower()

        # 语文教材特有内容类型
        if re.search(r'生字\s*词|生字\s*表|词语\s*盘点|拼音乐园', text_lower):
            return '生字词'
        elif re.search(r'课后练习|练习\s*[一二三四五六七八九十\d]+|基础\s*练习', text_lower):
            return '练习题'
        elif re.search(r'第[一二三四五六七八九十\d]+课.*[《].*[》]', text):
            return '课文'
        elif re.search(r'单元\s*复习|语文\s*园地|口语\s*交际', text_lower):
            return '单元复习'
        elif re.search(r'习作|写作|看图\s*写话', text_lower):
            return '写作指导'
        elif re.search(r'古诗|日积月累|古诗词', text_lower):
            return '古诗词'
        elif re.search(r'识字|写字', text_lower):
            return '识字'
        elif re.search(r'阅读\s*提示|精读\s*指导', text_lower):
            return '阅读指导'
        elif re.search(r'拼音|声母|韵母', text_lower):
            return '拼音学习'
        elif re.search(r'词语\s*解释|近义词|反义词', text_lower):
            return '词语学习'
        elif re.search(r'句子\s*练习|句式|造句', text_lower):
            return '句子练习'
        else:
            return '语文内容'

    def _assess_chinese_text_quality(self, text: str) -> Dict[str, Any]:
        """
        评估语文教材文本质量

        Args:
            text: 文本内容

        Returns:
            质量评估结果
        """
        text = text.strip()

        if not text:
            return {'is_meaningful': False, 'score': 0.0}

        score = 1.0  # 基础分数

        # 文本长度评分（语文内容特点）
        length = len(text)
        if length < 30:
            score -= 0.6
        elif length > 1500:
            score -= 0.2

        # 中文内容评分
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        if chinese_chars == 0:
            score -= 0.8
        else:
            chinese_ratio = chinese_chars / length
            score += chinese_ratio * 0.4

        # 语文教材关键词评分
        chinese_keywords = [
            '课文', '生字', '词语', '练习', '阅读', '写作', '口语', '交际',
            '拼音', '识字', '写字', '古诗', '日积月累', '语文园地',
            '近义词', '反义词', '造句', '理解', '背诵', '朗读',
            '第课', '单元', '复习', '习作', '看图写话'
        ]

        keyword_count = sum(1 for keyword in chinese_keywords if keyword in text)
        score += min(keyword_count * 0.08, 0.6)

        # 教育结构评分
        if re.search(r'第[一二三四五六七八九十\d]+课', text):
            score += 0.3
        if re.search(r'^\d+[、.]', text, re.MULTILINE):
            score += 0.2
        if re.search(r'[《].*[》]', text):  # 书名号
            score += 0.2

        # 内容类型评分
        content_type = self._identify_chinese_content_type(text)
        if content_type in ['课文', '古诗', '生字词', '练习题']:
            score += 0.2
        elif content_type in ['写作指导', '阅读指导', '单元复习']:
            score += 0.1

        # 排除噪音内容
        noise_patterns = [
            r'^\d+$',                      # 纯数字
            r'^第\d+页$',                   # 页码
            r'^page\s*\d+$',               # 英文页码
            r'^-*$',                       # 纯横线
            r'^\s*$',                      # 空白
            r'^[^\u4e00-\u9fff]*$',        # 无中文
        ]

        for pattern in noise_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                score -= 0.5

        # 最终评分
        score = max(0.0, min(1.0, score))

        return {
            'is_meaningful': score > 0.4,  # 语文内容阈值稍高
            'score': score,
            'length': length,
            'chinese_chars': chinese_chars,
            'chinese_ratio': chinese_chars / length if length > 0 else 0,
            'keyword_count': keyword_count,
            'content_type': content_type
        }

    def split_page_content(self, page: Dict[str, Any], pdf_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        分割语文教材单个页面的内容

        Args:
            page: 页面信息
            pdf_result: PDF处理结果

        Returns:
            分割后的文档片段列表
        """
        page_text = page.get('text', '')
        page_number = page.get('page_number', 0)
        structure_info = page.get('structure_info', {})

        if not page_text.strip():
            return []

        # 预处理页面文本
        cleaned_text = self._preprocess_page_text(page_text)

        # 使用语文教材专用分割器
        documents = self.text_splitter.create_documents([cleaned_text])

        chunks = []
        for i, doc in enumerate(documents):
            # 生成唯一标识符
            chunk_id = f"{pdf_result['file_name']}_page_{page_number}_chunk_{i+1}"

            # 语文教材专用质量评估
            text_quality = self._assess_chinese_text_quality(doc.page_content)

            if text_quality['is_meaningful']:
                # 识别内容类型
                content_type = self._identify_chinese_content_type(doc.page_content, structure_info)

                chunk = {
                    'id': chunk_id,
                    'content': doc.page_content.strip(),
                    'page_number': page_number,
                    'chunk_index': i,
                    'total_chunks': len(documents),
                    'text_length': len(doc.page_content),
                    'word_count': len(doc.page_content.split()),
                    'quality_score': text_quality['score'],
                    'content_type': content_type,
                    'metadata': {
                        'pdf_file': pdf_result['file_name'],
                        'subject': pdf_result['education_metadata'].get('subject', '语文'),
                        'grade': pdf_result['education_metadata'].get('grade', '三年级'),
                        'page_number': page_number,
                        'total_pages': pdf_result.get('total_pages', 0),
                        'processed_date': pdf_result.get('processed_date', ''),
                        'content_type': content_type,
                        'has_images': len(page.get('images', [])) > 0,
                        'language_focus': structure_info.get('language_focus', '综合学习'),
                        'difficulty_level': structure_info.get('difficulty_level', 1),
                        'section_type': structure_info.get('section_type', content_type),
                        'chinese_ratio': text_quality.get('chinese_ratio', 0),
                        'is_lesson_content': content_type in ['课文', '古诗', '阅读指导'],
                        'is_exercise': content_type in ['练习题', '造句', '句子练习'],
                        'is_vocabulary': content_type in ['生字词', '词语学习'],
                        'is_writing': content_type in ['写作指导', '看图写话']
                    }
                }

                chunks.append(chunk)

        return chunks


def create_pdf_splitter(chunk_size: int = 1500,
                      chunk_overlap: int = 200,
                      subject: str = None) -> PDFTextSplitter:
    """
    创建PDF分段器的工厂函数

    Args:
        chunk_size: 分段大小（字符数）
        chunk_overlap: 分段重叠大小（字符数）
        subject: 学科类型，如果是'语文'则使用语文教材专用分割器

    Returns:
        PDF分割器实例
    """
    if subject == '语文':
        return ChineseTextbookSplitter(
            chunk_size=1200,    # 语文内容使用较小片段
            chunk_overlap=150,
            respect_sentence_endings=True,
            respect_paragraph_breaks=True
        )
    else:
        return PDFTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            respect_sentence_endings=True,
            respect_paragraph_breaks=True
        )


if __name__ == "__main__":
    # 测试PDF分段器
    from homeworkpal.document.pdf_processor import create_pdf_processor
    import os

    print("🔧 测试PDF文档分段器")
    print("=" * 40)

    # 创建处理器
    processor = create_pdf_processor()
    splitter = create_pdf_splitter()

    # 测试数学PDF
    math_pdf = 'data/textbooks/数学 3 上.pdf'
    if not os.path.exists(math_pdf):
        print(f"❌ PDF文件不存在: {math_pdf}")
        exit(1)

    print(f"正在测试: {math_pdf}")

    # 处理PDF
    try:
        pdf_result = processor.extract_text_from_pdf(math_pdf)

        # 分割内容
        chunks = splitter.split_pdf_content(pdf_result)

        print(f"✅ PDF分割成功")
        print(f"  - 总片段数: {len(chunks)}")
        print(f"  - 平均片段长度: {sum(c['text_length'] for c in chunks) / len(chunks):.1f}")
        print(f"  - 高质量片段数: {sum(1 for c in chunks if c['quality_score'] > 0.5)}")

        # 显示前3个片段的预览
        for i, chunk in enumerate(chunks[:3]):
            print(f"\n--- 片段 {i+1} 预览 ---")
            print(f"ID: {chunk['id']}")
            print(f"页面: {chunk['page_number']}")
            print(f"长度: {chunk['text_length']} 字符")
            print(f"质量评分: {chunk['quality_score']:.2f}")
            preview = chunk['content'][:200] + '...' if len(chunk['content']) > 200 else chunk['content']
            print(f"内容: {preview}")

    except Exception as e:
        print(f"❌ 处理失败: {e}")