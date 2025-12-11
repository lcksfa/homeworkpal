"""
文档处理模块
Document Processing Module for Homework Pal

支持多种文档格式的处理：
- PDF文档处理
- Markdown文档处理
- 文本文档处理
"""

from .pdf_processor import PDFProcessor, ChineseTextbookProcessor, create_pdf_processor

from .text_splitter import PDFTextSplitter, ChineseTextbookSplitter, create_pdf_splitter

# Temporarily comment out problematic import
# from .chinese_text_processor import ChineseTextProcessor, create_chinese_text_processor

__all__ = [
    'PDFProcessor',
    'ChineseTextbookProcessor',
    'create_pdf_processor',
    'PDFTextSplitter',
    'ChineseTextbookSplitter',
    'create_pdf_splitter',
    # 'ChineseTextProcessor',
    # 'create_chinese_text_processor'
]