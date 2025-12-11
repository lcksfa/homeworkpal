"""
PDF文档处理器
PDF Document Processor for Homework Pal

针对人教版教材PDF的智能解析和内容提取
"""

import os
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
    print(f"✅ PyMuPDF available, version: {fitz.version}")
except ImportError as e:
    PYMUPDF_AVAILABLE = False
    print(f"❌ PyMuPDF not available: {e}")

try:
    from unstructured.partition.auto import partition
    from unstructured.partition.pdf import partition_pdf
    UNSTRUCTURED_AVAILABLE = True
except ImportError:
    UNSTRUCTURED_AVAILABLE = False

logger = logging.getLogger(__name__)


class PDFProcessor:
    """PDF文档处理器"""

    def __init__(self,
                 use_unstructured: bool = True,
                 extract_images: bool = True,
                 preserve_layout: bool = True):
        """
        初始化PDF处理器

        Args:
            use_unstructured: 是否使用unstructured库
            extract_images: 是否提取图片信息
            preserve_layout: 是否保持文档布局
        """
        self.use_unstructured = use_unstructured and UNSTRUCTURED_AVAILABLE
        self.extract_images = extract_images
        self.preserve_layout = preserve_layout

        if not PYMUPDF_AVAILABLE and not self.use_unstructured:
            raise ImportError("需要安装PyMuPDF或unstructured库来处理PDF文件")

    def extract_text_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        从PDF文件提取文本和元数据

        Args:
            pdf_path: PDF文件路径

        Returns:
            包含提取结果的字典
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

        try:
            logger.info(f"开始处理PDF: {pdf_path}")

            # 获取文件信息
            file_name = os.path.basename(pdf_path)
            file_size = os.path.getsize(pdf_path)

            # 提取教育元数据
            education_metadata = self._extract_education_metadata(file_name)

            if self.use_unstructured:
                result = self._extract_with_unstructured(pdf_path)
            else:
                result = self._extract_with_pymupdf(pdf_path)

            # 添加文件信息
            result.update({
                'file_name': file_name,
                'file_path': pdf_path,
                'file_size': file_size,
                'processed_date': datetime.now().isoformat(),
                'education_metadata': education_metadata,
                'processor_type': 'unstructured' if self.use_unstructured else 'pymupdf'
            })

            logger.info(f"PDF处理完成: {len(result.get('pages', []))} 页")
            return result

        except Exception as e:
            logger.error(f"PDF处理失败: {e}")
            raise

    def _extract_with_unstructured(self, pdf_path: str) -> Dict[str, Any]:
        """使用unstructured库提取PDF内容"""
        try:
            # 使用unstructured进行高级解析
            elements = partition_pdf(
                pdf_path,
                infer_table_structure=True,
                include_page_breaks=True,
                strategy="hi_res" if self.preserve_layout else "fast"
            )

            pages = []
            current_page = []
            current_page_num = 1

            for element in elements:
                # 获取页面信息
                page_num = getattr(element, 'page_number', 1)

                # 如果是新页面，保存前一页内容
                if page_num != current_page_num:
                    if current_page:
                        pages.append({
                            'page_number': current_page_num,
                            'text': '\n'.join(current_page),
                            'elements': len(current_page)
                        })
                    current_page = []
                    current_page_num = page_num

                # 添加元素内容
                if hasattr(element, 'text') and element.text.strip():
                    current_page.append(element.text.strip())

            # 添加最后一页
            if current_page:
                pages.append({
                    'page_number': current_page_num,
                    'text': '\n'.join(current_page),
                    'elements': len(current_page)
                })

            return {
                'pages': pages,
                'total_pages': len(pages),
                'element_count': len(elements),
                'method': 'unstructured'
            }

        except Exception as e:
            logger.warning(f"unstructured解析失败，回退到PyMuPDF: {e}")
            return self._extract_with_pymupdf(pdf_path)

    def _extract_with_pymupdf(self, pdf_path: str) -> Dict[str, Any]:
        """使用PyMuPDF提取PDF内容"""
        try:
            doc = fitz.open(pdf_path)
            pages = []

            for page_num in range(len(doc)):
                page = doc[page_num]

                # 提取文本
                text = page.get_text()

                # 如果需要，提取图片信息
                images = []
                if self.extract_images:
                    image_list = page.get_images()
                    for img_index, img in enumerate(image_list):
                        try:
                            # 获取图片信息
                            xref = img[0]
                            pix = fitz.Pixmap(doc, xref)

                            if pix.width > 50 and pix.height > 50:  # 过滤小图片
                                images.append({
                                    'index': img_index,
                                    'width': pix.width,
                                    'height': pix.height,
                                    'xref': xref
                                })

                            pix = None  # 释放内存
                        except Exception as e:
                            logger.debug(f"提取图片信息失败: {e}")

                # 预处理文本
                cleaned_text = self._preprocess_page_text(text)

                if cleaned_text.strip():
                    pages.append({
                        'page_number': page_num + 1,
                        'text': cleaned_text,
                        'images': images,
                        'raw_text_length': len(text),
                        'cleaned_text_length': len(cleaned_text)
                    })

            doc.close()

            return {
                'pages': pages,
                'total_pages': len(pages),
                'method': 'pymupdf'
            }

        except Exception as e:
            logger.error(f"PyMuPDF解析失败: {e}")
            raise

    def _extract_education_metadata(self, file_name: str) -> Dict[str, str]:
        """
        从文件名提取教育元数据

        Args:
            file_name: 文件名

        Returns:
            教育元数据字典
        """
        metadata = {
            'subject': '未识别',
            'grade': '未识别',
            'semester': '未识别',
            'publisher': '人教版'
        }

        file_name_lower = file_name.lower()

        # 识别学科
        if '数学' in file_name or 'math' in file_name_lower:
            metadata['subject'] = '数学'
        elif '语文' in file_name or 'chinese' in file_name_lower:
            metadata['subject'] = '语文'
        elif '英语' in file_name or 'english' in file_name_lower:
            metadata['subject'] = '英语'
        elif '科学' in file_name or 'science' in file_name_lower:
            metadata['subject'] = '科学'

        # 识别年级
        if any(grade in file_name for grade in ['一年级', 'grade1', '1年级']):
            metadata['grade'] = '一年级'
        elif any(grade in file_name for grade in ['二年级', 'grade2', '2年级']):
            metadata['grade'] = '二年级'
        elif any(grade in file_name for grade in ['三年级', 'grade3', '3年级', '三上']):
            metadata['grade'] = '三年级'
        elif any(grade in file_name for grade in ['四年级', 'grade4', '4年级']):
            metadata['grade'] = '四年级'
        elif any(grade in file_name for grade in ['五年级', 'grade5', '5年级']):
            metadata['grade'] = '五年级'
        elif any(grade in file_name for grade in ['六年级', 'grade6', '6年级']):
            metadata['grade'] = '六年级'

        # 识别学期
        if '上' in file_name or 'first' in file_name_lower:
            metadata['semester'] = '上学期'
        elif '下' in file_name or 'second' in file_name_lower:
            metadata['semester'] = '下学期'

        # 识别版本
        if '人教' in file_name or 'pep' in file_name_lower:
            metadata['publisher'] = '人教版'
        elif '苏教' in file_name:
            metadata['publisher'] = '苏教版'
        elif '北师' in file_name:
            metadata['publisher'] = '北师大版'

        return metadata

    def _preprocess_page_text(self, text: str) -> str:
        """
        预处理页面文本

        Args:
            text: 原始文本

        Returns:
            清理后的文本
        """
        if not text:
            return text

        # 移除多余空白
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            line = line.strip()

            # 跳过明显无意义的行
            if not line:
                continue

            # 跳过纯数字行（可能是页码）
            if line.isdigit():
                continue

            # 跳过非常短的行（可能是页面标识）
            if len(line) < 2:
                continue

            cleaned_lines.append(line)

        # 重新组合文本
        cleaned_text = '\n'.join(cleaned_lines)

        # 规范化空白字符
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text)

        return cleaned_text.strip()

    def get_processor_info(self) -> Dict[str, Any]:
        """获取处理器信息"""
        return {
            'use_unstructured': self.use_unstructured,
            'extract_images': self.extract_images,
            'preserve_layout': self.preserve_layout,
            'pymupdf_available': PYMUPDF_AVAILABLE,
            'unstructured_available': UNSTRUCTURED_AVAILABLE
        }


class ChineseTextbookProcessor(PDFProcessor):
    """语文教材专用PDF处理器"""

    def __init__(self,
                 use_unstructured: bool = True,
                 extract_images: bool = True,
                 preserve_layout: bool = True):
        """
        初始化语文教材PDF处理器

        Args:
            use_unstructured: 是否使用unstructured库
            extract_images: 是否提取图片信息
            preserve_layout: 是否保持文档布局
        """
        super().__init__(
            use_unstructured=use_unstructured,
            extract_images=extract_images,
            preserve_layout=preserve_layout
        )

        # 语文教材结构识别模式
        self.chinese_patterns = {
            'lesson_title': r'^第?\s*[一二三四五六七八九十\d]+\s*课\s*[：《].*[》\s]*',
            'vocabulary': r'生字\s*词|生字\s*表|词语\s*盘点',
            'exercise': r'课后练习|练习\s*[一二三四五六七八九十\d]+|基础\s*练习',
            'unit_review': r'单元\s*复习|语文\s*园地|口语\s*交际',
            'writing': r'习作\s*[一二三四五六七八九十\d]+|写作\s*指导|看图\s*写话',
            'reading': r'阅读\s*提示|精读\s*指导',
            'ancient_poem': r'古诗\s*[一二三四五六七八九十\d]+|日积月累',
            'pinyin': r'拼音乐园|拼音\s*复习',
            'character': r'识字\s*[一二三四五六七八九十\d]+|写字\s*指导'
        }

    def detect_chinese_textbook_structure(self, text: str) -> Dict[str, Any]:
        """
        识别语文教材结构

        Args:
            text: 文本内容

        Returns:
            结构识别结果
        """
        structure_info = {
            'content_type': '未识别',
            'lesson_number': None,
            'unit_number': None,
            'section_type': None,
            'language_focus': None,
            'difficulty_level': 1,
            'has_images': False
        }

        # 检测课文标题
        lesson_match = re.search(self.chinese_patterns['lesson_title'], text, re.MULTILINE)
        if lesson_match:
            structure_info['content_type'] = '课文'
            structure_info['section_type'] = 'lesson_title'

            # 提取课号
            lesson_number = re.search(r'第?\s*([一二三四五六七八九十\d]+)\s*课', lesson_match.group())
            if lesson_number:
                structure_info['lesson_number'] = lesson_number.group(1)

            structure_info['language_focus'] = '阅读理解'
            structure_info['difficulty_level'] = 2

        # 检测生字词
        elif re.search(self.chinese_patterns['vocabulary'], text):
            structure_info['content_type'] = '生字词'
            structure_info['section_type'] = 'vocabulary'
            structure_info['language_focus'] = '识字'
            structure_info['difficulty_level'] = 1

        # 检测课后练习
        elif re.search(self.chinese_patterns['exercise'], text):
            structure_info['content_type'] = '练习题'
            structure_info['section_type'] = 'exercise'
            structure_info['language_focus'] = '理解应用'
            structure_info['difficulty_level'] = 3

        # 检测单元复习
        elif re.search(self.chinese_patterns['unit_review'], text):
            structure_info['content_type'] = '单元复习'
            structure_info['section_type'] = 'unit_review'
            structure_info['language_focus'] = '综合复习'
            structure_info['difficulty_level'] = 2

        # 检测习作
        elif re.search(self.chinese_patterns['writing'], text):
            structure_info['content_type'] = '写作指导'
            structure_info['section_type'] = 'writing'
            structure_info['language_focus'] = '写作'
            structure_info['difficulty_level'] = 3

        # 检测古诗
        elif re.search(self.chinese_patterns['ancient_poem'], text):
            structure_info['content_type'] = '古诗词'
            structure_info['section_type'] = 'ancient_poem'
            structure_info['language_focus'] = '古诗欣赏'
            structure_info['difficulty_level'] = 2

        # 检测识字内容
        elif re.search(self.chinese_patterns['character'], text):
            structure_info['content_type'] = '识字'
            structure_info['section_type'] = 'character'
            structure_info['language_focus'] = '识字'
            structure_info['difficulty_level'] = 1

        return structure_info

    def _preprocess_chinese_text(self, text: str) -> str:
        """
        中文文本专用预处理

        Args:
            text: 原始文本

        Returns:
            预处理后的文本
        """
        if not text:
            return text

        # 清理PDF解析产生的噪音
        text = re.sub(r'\s+', ' ', text)  # 合并多余空白

        # 保留中文字符、标点符号和常用符号
        text = re.sub(r'[^\u4e00-\u9fff\u3000-\u303f\uff00-\uffef\s，。！？；：""''（）【】《》\\d一二三四五六七八九十]', '', text)

        # 确保标点符号格式统一
        text = text.replace(',', '，').replace('.', '。').replace('!', '！').replace('?', '？')
        text = text.replace(':', '：').replace(';', '；').replace('"', '"').replace('"', '"')

        # 清理页码等噪音
        text = re.sub(r'\b\d+\s*页\b', '', text)  # 移除"X页"
        text = re.sub(r'\b页\s*\d+\b', '', text)  # 移除"页X"

        return text.strip()

    def _extract_with_pymupdf_chinese(self, pdf_path: str) -> Dict[str, Any]:
        """使用PyMuPDF专门处理语文教材PDF"""
        try:
            doc = fitz.open(pdf_path)
            pages = []

            for page_num in range(len(doc)):
                page = doc[page_num]

                # 获取页面文本
                text = page.get_text()

                # 语文教材专用预处理
                cleaned_text = self._preprocess_chinese_text(text)

                if cleaned_text.strip():
                    # 识别页面结构
                    structure_info = self.detect_chinese_textbook_structure(cleaned_text)

                    # 获取图片信息
                    images = []
                    if self.extract_images:
                        image_list = page.get_images()
                        for img_index, img in enumerate(image_list):
                            try:
                                xref = img[0]
                                pix = fitz.Pixmap(doc, xref)

                                if pix.width > 50 and pix.height > 50:
                                    images.append({
                                        'index': img_index,
                                        'width': pix.width,
                                        'height': pix.height,
                                        'xref': xref
                                    })
                                pix = None
                            except Exception as e:
                                logger.debug(f"提取图片信息失败: {e}")

                    # 如果有图片，更新结构信息
                    if images:
                        structure_info['has_images'] = True

                    pages.append({
                        'page_number': page_num + 1,
                        'text': cleaned_text,
                        'images': images,
                        'structure_info': structure_info,
                        'raw_text_length': len(text),
                        'cleaned_text_length': len(cleaned_text)
                    })

            doc.close()

            return {
                'pages': pages,
                'total_pages': len(pages),
                'method': 'pymupdf_chinese'
            }

        except Exception as e:
            logger.error(f"语文教材PyMuPDF解析失败: {e}")
            # 回退到普通处理
            return self._extract_with_pymupdf(pdf_path)

    def extract_text_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        重写PDF提取方法，优先使用语文教材专用处理

        Args:
            pdf_path: PDF文件路径

        Returns:
            包含提取结果的字典
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

        try:
            logger.info(f"开始处理语文教材PDF: {pdf_path}")

            # 获取文件信息
            file_name = os.path.basename(pdf_path)
            file_size = os.path.getsize(pdf_path)

            # 提取教育元数据
            education_metadata = self._extract_education_metadata(file_name)

            # 如果是语文教材，使用专用处理
            if education_metadata.get('subject') == '语文':
                logger.info("检测到语文教材，使用专用处理器")
                if self.use_unstructured:
                    # 尝试使用unstructured处理
                    try:
                        result = self._extract_with_unstructured(pdf_path)
                        # 对结果进行结构识别
                        for page in result['pages']:
                            text = page.get('text', '')
                            if text:
                                page['structure_info'] = self.detect_chinese_textbook_structure(text)
                    except Exception as e:
                        logger.warning(f"unstructured处理语文教材失败，回退到专用PyMuPDF: {e}")
                        result = self._extract_with_pymupdf_chinese(pdf_path)
                else:
                    result = self._extract_with_pymupdf_chinese(pdf_path)
            else:
                # 使用标准处理
                if self.use_unstructured:
                    result = self._extract_with_unstructured(pdf_path)
                else:
                    result = self._extract_with_pymupdf(pdf_path)

            # 添加文件信息
            result.update({
                'file_name': file_name,
                'file_path': pdf_path,
                'file_size': file_size,
                'processed_date': datetime.now().isoformat(),
                'education_metadata': education_metadata,
                'processor_type': 'chinese_textbook' if education_metadata.get('subject') == '语文' else 'standard'
            })

            logger.info(f"语文教材PDF处理完成: {len(result.get('pages', []))} 页")
            return result

        except Exception as e:
            logger.error(f"语文教材PDF处理失败: {e}")
            raise


def create_pdf_processor(use_unstructured: bool = True,
                        extract_images: bool = True,
                        preserve_layout: bool = True,
                        subject: str = None) -> PDFProcessor:
    """
    创建PDF处理器的工厂函数

    Args:
        use_unstructured: 是否使用unstructured库
        extract_images: 是否提取图片信息
        preserve_layout: 是否保持文档布局
        subject: 学科类型，如果是'语文'则使用专用处理器

    Returns:
        PDF处理器实例
    """
    if subject == '语文':
        return ChineseTextbookProcessor(
            use_unstructured=use_unstructured,
            extract_images=extract_images,
            preserve_layout=preserve_layout
        )
    else:
        return PDFProcessor(
            use_unstructured=use_unstructured,
            extract_images=extract_images,
            preserve_layout=preserve_layout
        )


if __name__ == "__main__":
    # 测试PDF处理器
    print("🔧 测试PDF文档处理器")
    print("=" * 40)

    # 检查依赖
    print(f"PyMuPDF可用: {PYMUPDF_AVAILABLE}")
    print(f"unstructured可用: {UNSTRUCTURED_AVAILABLE}")

    # 创建处理器
    processor = create_pdf_processor()
    print(f"处理器信息: {processor.get_processor_info()}")

    # 查找PDF文件进行测试
    test_dir = Path("data/textbooks")
    if test_dir.exists():
        pdf_files = list(test_dir.glob("*.pdf"))
        if pdf_files:
            test_file = pdf_files[0]
            print(f"\n📄 测试文件: {test_file}")

            try:
                result = processor.extract_text_from_pdf(str(test_file))
                print(f"✅ 处理成功")
                print(f"  - 文件名: {result['file_name']}")
                print(f"  - 文件大小: {result['file_size'] / 1024 / 1024:.1f} MB")
                print(f"  - 页数: {result['total_pages']}")
                print(f"  - 处理器: {result['processor_type']}")
                print(f"  - 学科: {result['education_metadata']['subject']}")
                print(f"  - 年级: {result['education_metadata']['grade']}")

            except Exception as e:
                print(f"❌ 处理失败: {e}")
        else:
            print("❌ 没有找到PDF测试文件")
    else:
        print(f"❌ 测试目录不存在: {test_dir}")

    print("\n🔧 测试完成")