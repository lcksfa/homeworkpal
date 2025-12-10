"""
文档处理模块
Document Processing Module for Homework Pal

支持多种文档格式的处理：
- PDF文档处理
- Markdown文档处理
- 文本文档处理
"""

from .pdf_processor import PDFProcessor, create_pdf_processor

from .text_splitter import PDFTextSplitter, create_pdf_splitter

__all__ = [
    'PDFProcessor',
    'create_pdf_processor',
    'PDFTextSplitter',
    'create_pdf_splitter'
]