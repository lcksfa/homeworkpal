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


class TextbookKnowledge(Base):
    """教材知识表"""
    __tablename__ = 'textbook_knowledge'

    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False, comment="教材内容")
    embedding = Column(Vector(1536), comment="向量嵌入")
    meta_data = Column(JSON, nullable=False, comment="元数据")
    subject = Column(String(50), nullable=False, comment="学科")
    grade = Column(String(10), nullable=False, comment="年级")
    unit = Column(String(100), comment="单元")
    page = Column(Integer, comment="页码")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # 关联关系
    mistake_records = relationship("MistakeRecord", back_populates="textbook_ref")


class HomeworkSession(Base):
    """作业会话表"""
    __tablename__ = 'homework_sessions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), nullable=False, comment="用户ID")
    date = Column(Date, nullable=False, comment="作业日期")
    summary = Column(Text, comment="会话总结")
    status = Column(String(20), default='active', comment="状态")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # 关联关系
    mistake_records = relationship("MistakeRecord", back_populates="session")


class MistakeRecord(Base):
    """错题记录表"""
    __tablename__ = 'mistake_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('homework_sessions.id'), comment="会话ID")
    subject = Column(String(50), nullable=False, comment="学科")
    image_path = Column(Text, comment="图片路径")
    student_answer = Column(Text, comment="学生答案")
    correct_hint = Column(Text, comment="正确提示")
    ai_analysis = Column(Text, comment="AI分析")
    textbook_ref_id = Column(Integer, ForeignKey('textbook_knowledge.id'), comment="教材参考ID")
    status = Column(Integer, default=0, comment="掌握状态: 0-未掌握, 1-已掌握")
    difficulty_level = Column(Integer, default=1, comment="难度等级")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # 关联关系
    session = relationship("HomeworkSession", back_populates="mistake_records")
    textbook_ref = relationship("TextbookKnowledge", back_populates="mistake_records")