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
        elif any(grade in file_name for grade in ['三年级', 'grade3', '3年级']):
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


def create_pdf_processor(use_unstructured: bool = True,
                        extract_images: bool = True,
                        preserve_layout: bool = True) -> PDFProcessor:
    """
    创建PDF处理器的工厂函数

    Args:
        use_unstructured: 是否使用unstructured库
        extract_images: 是否提取图片信息
        preserve_layout: 是否保持文档布局

    Returns:
        PDF处理器实例
    """
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