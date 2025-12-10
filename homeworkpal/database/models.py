"""
数据库模型定义
Database models for Homework Pal RAG System
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON, ForeignKey, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
import datetime

Base = declarative_base()


class TextbookChunk(Base):
    """教材知识片段表"""
    __tablename__ = 'textbook_chunks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False, comment="教材内容片段")
    embedding = Column(Vector(1024), comment="向量嵌入 (BGE-M3 1024维)")
    content_hash = Column(String(64), unique=True, comment="内容MD5哈希值，用于去重")
    metadata_json = Column(JSON, nullable=False, comment="元数据 (学科、年级、单元、页码等)")
    source_file = Column(String(255), comment="源文件路径")
    chunk_index = Column(Integer, comment="在源文档中的片段索引")
    page_number = Column(Integer, comment="页码")
    quality_score = Column(Float, default=1.0, comment="文本质量评分")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # 关联关系
    mistake_records = relationship("MistakeRecord", back_populates="textbook_chunk")


class MistakeRecord(Base):
    """错题记录表"""
    __tablename__ = 'mistake_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_name = Column(String(100), comment="学生姓名")
    subject = Column(String(50), nullable=False, comment="学科")
    grade = Column(String(10), nullable=False, comment="年级")
    image_path = Column(Text, comment="作业图片路径")
    student_answer = Column(Text, nullable=False, comment="学生答案")
    question_text = Column(Text, comment="题目文字描述")
    ai_analysis = Column(Text, comment="AI分析结果")
    correct_answer = Column(Text, comment="正确答案或提示")
    knowledge_points = Column(JSON, comment="相关知识点列表")
    difficulty_level = Column(Integer, default=1, comment="难度等级 1-5")
    mastery_status = Column(Integer, default=0, comment="掌握状态: 0-未掌握, 1-部分掌握, 2-已掌握")
    reviewed = Column(Boolean, default=False, comment="是否已复习")
    textbook_chunk_id = Column(Integer, ForeignKey('textbook_chunks.id'), comment="关联的教材知识片段ID")
    session_id = Column(String(100), comment="会话ID")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # 关联关系
    textbook_chunk = relationship("TextbookChunk", back_populates="mistake_records")