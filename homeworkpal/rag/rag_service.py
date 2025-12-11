"""
RAG检索服务
RAG Retrieval Service for Homework Pal

实现基于向量相似性的语义搜索功能，支持人教版教材内容检索
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np

from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_, desc

from ..database.connection import get_db
from ..database.models import TextbookChunk
from ..llm.siliconflow import SiliconFlowClient

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """检索结果数据类"""
    content: str
    score: float
    metadata: Dict[str, Any]
    chunk_id: int
    source_file: Optional[str] = None
    page_number: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'content': self.content,
            'score': float(self.score),
            'metadata': self.metadata,
            'chunk_id': self.chunk_id,
            'source_file': self.source_file,
            'page_number': self.page_number
        }


class RAGService:
    """RAG检索服务类

    提供语义搜索、向量相似性检索和知识获取功能。
    基于BGE-M3向量模型和PostgreSQL pgvector数据库实现。
    """

    def __init__(self,
                 embedding_client: Optional[SiliconFlowClient] = None,
                 similarity_threshold: float = 0.3,
                 max_results: int = 10):
        """
        初始化RAG服务

        Args:
            embedding_client: 向量嵌入客户端，默认使用SiliconFlow
            similarity_threshold: 相似度阈值，低于此值的结果将被过滤
            max_results: 最大返回结果数量
        """
        self.embedding_client = embedding_client or SiliconFlowClient()
        self.similarity_threshold = similarity_threshold
        self.max_results = max_results
        self.embedding_dimension = 1024  # BGE-M3向量维度

        logger.info(f"RAG服务初始化完成，相似度阈值: {similarity_threshold}, 最大结果数: {max_results}")

    def search(self,
               query: str,
               top_k: int = 3,
               subject: Optional[str] = None,
               grade: Optional[str] = None,
               unit: Optional[str] = None,
               filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """
        执行语义搜索

        Args:
            query: 查询文本
            top_k: 返回结果数量
            subject: 学科过滤 (如: 数学, 语文, 英语)
            grade: 年级过滤 (如: 三年级)
            unit: 单元过滤
            filters: 其他过滤条件

        Returns:
            检索结果列表，按相似度降序排列
        """
        try:
            logger.info(f"执行语义搜索: query='{query}', top_k={top_k}, filters={filters}")

            # 生成查询向量
            query_embedding = self._generate_query_embedding(query)

            # 执行向量相似性搜索
            results = self._vector_similarity_search(
                query_embedding=query_embedding,
                limit=min(top_k, self.max_results),
                subject=subject,
                grade=grade,
                unit=unit,
                additional_filters=filters
            )

            # 记录搜索结果统计
            logger.info(f"搜索完成，返回 {len(results)} 个结果")
            if results:
                avg_score = np.mean([r.score for r in results])
                logger.info(f"平均相似度分数: {avg_score:.3f}")

            return results

        except Exception as e:
            logger.error(f"语义搜索失败: {e}")
            raise

    def _generate_query_embedding(self, query: str) -> List[float]:
        """
        生成查询文本的向量嵌入

        Args:
            query: 查询文本

        Returns:
            向量嵌入列表
        """
        try:
            logger.debug(f"生成查询向量: {query}")
            embedding = self.embedding_client.embed_query(query)

            if len(embedding) != self.embedding_dimension:
                raise ValueError(f"向量维度不匹配: 期望{self.embedding_dimension}, 实际{len(embedding)}")

            return embedding

        except Exception as e:
            logger.error(f"生成查询向量失败: {e}")
            raise

    def _vector_similarity_search(self,
                                  query_embedding: List[float],
                                  limit: int,
                                  subject: Optional[str] = None,
                                  grade: Optional[str] = None,
                                  unit: Optional[str] = None,
                                  additional_filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """
        执行向量相似性搜索

        Args:
            query_embedding: 查询向量
            limit: 返回结果数量限制
            subject: 学科过滤
            grade: 年级过滤
            unit: 单元过滤
            additional_filters: 其他过滤条件

        Returns:
            检索结果列表
        """
        try:
            # 获取数据库会话
            db = next(get_db())

            # 构建向量相似性查询
            query_vector_str = f"[{','.join(map(str, query_embedding))}]"

            # 基础SQL查询
            base_sql = """
            SELECT
                id, content, embedding, metadata_json, source_file,
                chunk_index, page_number, quality_score,
                1 - (embedding <=> :query_vector) as similarity_score
            FROM textbook_chunks
            WHERE 1 - (embedding <=> :query_vector) >= :threshold
            """

            # 添加过滤条件
            params = {
                'query_vector': query_vector_str,
                'threshold': self.similarity_threshold
            }

            # 构建过滤条件
            if subject or grade or unit or additional_filters:
                filter_conditions = []

                if subject:
                    filter_conditions.append("metadata_json->>'subject' = :subject")
                    params['subject'] = subject

                if grade:
                    filter_conditions.append("metadata_json->>'grade' = :grade")
                    params['grade'] = grade

                if unit:
                    filter_conditions.append("metadata_json->>'unit' = :unit")
                    params['unit'] = unit

                # 添加其他过滤条件
                if additional_filters:
                    for key, value in additional_filters.items():
                        if isinstance(value, str):
                            filter_conditions.append(f"metadata_json->>'{key}' = :filter_{key}")
                            params[f'filter_{key}'] = value
                        elif isinstance(value, list):
                            # 支持列表值过滤 (IN操作)
                            placeholders = ','.join([f":filter_{key}_{i}" for i in range(len(value))])
                            filter_conditions.append(f"metadata_json->>'{key}' IN ({placeholders})")
                            for i, v in enumerate(value):
                                params[f'filter_{key}_{i}'] = v

                if filter_conditions:
                    base_sql += " AND " + " AND ".join(filter_conditions)

            # 添加排序和限制
            base_sql += " ORDER BY similarity_score DESC LIMIT :limit"
            params['limit'] = limit

            # 执行查询
            logger.debug(f"执行向量相似性查询: {base_sql}")
            result = db.execute(text(base_sql), params)

            # 转换结果
            search_results = []
            for row in result:
                search_result = SearchResult(
                    content=row.content,
                    score=float(row.similarity_score),
                    metadata=dict(row.metadata_json) if row.metadata_json else {},
                    chunk_id=row.id,
                    source_file=row.source_file,
                    page_number=row.page_number
                )
                search_results.append(search_result)

            db.close()

            return search_results

        except Exception as e:
            logger.error(f"向量相似性搜索失败: {e}")
            if 'db' in locals():
                db.close()
            raise

    def hybrid_search(self,
                      query: str,
                      top_k: int = 3,
                      keyword_weight: float = 0.3,
                      semantic_weight: float = 0.7,
                      **filters) -> List[SearchResult]:
        """
        混合搜索：结合关键词匹配和语义相似性

        Args:
            query: 查询文本
            top_k: 返回结果数量
            keyword_weight: 关键词匹配权重
            semantic_weight: 语义相似性权重
            **filters: 过滤条件

        Returns:
            检索结果列表
        """
        try:
            logger.info(f"执行混合搜索: query='{query}', keyword_weight={keyword_weight}")

            # 获取语义搜索结果
            semantic_results = self.search(query, top_k=top_k * 2, **filters)

            # 获取关键词搜索结果
            keyword_results = self._keyword_search(query, top_k=top_k * 2, **filters)

            # 合并和重排序结果
            combined_results = self._combine_search_results(
                semantic_results, keyword_results,
                semantic_weight, keyword_weight, top_k
            )

            return combined_results

        except Exception as e:
            logger.error(f"混合搜索失败: {e}")
            # 降级到纯语义搜索
            logger.info("降级到纯语义搜索")
            return self.search(query, top_k=top_k, **filters)

    def _keyword_search(self,
                        query: str,
                        top_k: int,
                        **filters) -> List[SearchResult]:
        """
        关键词搜索

        Args:
            query: 查询文本
            top_k: 返回结果数量
            **filters: 过滤条件

        Returns:
            检索结果列表
        """
        try:
            # 获取数据库会话
            db = next(get_db())

            # 构建关键词搜索查询
            base_sql = """
            SELECT
                id, content, metadata_json, source_file,
                chunk_index, page_number, quality_score,
                ts_rank_cd(to_tsvector('chinese', content), plainto_tsquery('chinese', :query)) as keyword_score
            FROM textbook_chunks
            WHERE to_tsvector('chinese', content) @@ plainto_tsquery('chinese', :query)
            """

            params = {'query': query}

            # 添加过滤条件 (与向量搜索相同的逻辑)
            if any(filters.values()):
                filter_conditions = []
                for key, value in filters.items():
                    if value and key in ['subject', 'grade', 'unit']:
                        filter_conditions.append(f"metadata_json->>'{key}' = :{key}")
                        params[key] = value

                if filter_conditions:
                    base_sql += " AND " + " AND ".join(filter_conditions)

            # 添加排序和限制
            base_sql += " ORDER BY keyword_score DESC LIMIT :limit"
            params['limit'] = top_k

            # 执行查询
            result = db.execute(text(base_sql), params)

            # 转换结果
            keyword_results = []
            for row in result:
                search_result = SearchResult(
                    content=row.content,
                    score=float(row.keyword_score),  # 使用关键词分数
                    metadata=dict(row.metadata_json) if row.metadata_json else {},
                    chunk_id=row.id,
                    source_file=row.source_file,
                    page_number=row.page_number
                )
                keyword_results.append(search_result)

            db.close()
            return keyword_results

        except Exception as e:
            logger.error(f"关键词搜索失败: {e}")
            return []

    def _combine_search_results(self,
                               semantic_results: List[SearchResult],
                               keyword_results: List[SearchResult],
                               semantic_weight: float,
                               keyword_weight: float,
                               top_k: int) -> List[SearchResult]:
        """
        合并语义搜索和关键词搜索结果

        Args:
            semantic_results: 语义搜索结果
            keyword_results: 关键词搜索结果
            semantic_weight: 语义搜索权重
            keyword_weight: 关键词搜索权重
            top_k: 最终返回结果数量

        Returns:
            合并后的检索结果列表
        """
        # 使用chunk_id作为键合并结果
        combined_scores = {}
        chunk_data = {}

        # 处理语义搜索结果
        for result in semantic_results:
            chunk_id = result.chunk_id
            combined_scores[chunk_id] = result.score * semantic_weight
            chunk_data[chunk_id] = result

        # 处理关键词搜索结果
        for result in keyword_results:
            chunk_id = result.chunk_id
            if chunk_id in combined_scores:
                combined_scores[chunk_id] += result.score * keyword_weight
            else:
                combined_scores[chunk_id] = result.score * keyword_weight
                chunk_data[chunk_id] = result

        # 按合并分数排序并返回top_k结果
        sorted_results = sorted(
            combined_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]

        final_results = []
        for chunk_id, combined_score in sorted_results:
            result = chunk_data[chunk_id]
            result.score = combined_score  # 更新为合并后的分数
            final_results.append(result)

        return final_results

    def get_similar_chunks(self, chunk_id: int, top_k: int = 5) -> List[SearchResult]:
        """
        获取与指定文档片段相似的其他片段

        Args:
            chunk_id: 文档片段ID
            top_k: 返回结果数量

        Returns:
            相似文档片段列表
        """
        try:
            # 获取数据库会话
            db = next(get_db())

            # 获取目标片段的向量
            target_chunk = db.query(TextbookChunk).filter(TextbookChunk.id == chunk_id).first()
            if not target_chunk:
                raise ValueError(f"未找到ID为{chunk_id}的文档片段")

            target_embedding = target_chunk.embedding.tolist()

            # 搜索相似片段
            similar_sql = """
            SELECT
                id, content, metadata_json, source_file,
                chunk_index, page_number, quality_score,
                1 - (embedding <=> :query_vector) as similarity_score
            FROM textbook_chunks
            WHERE id != :exclude_id
            AND 1 - (embedding <=> :query_vector) >= :threshold
            ORDER BY similarity_score DESC
            LIMIT :limit
            """

            params = {
                'query_vector': f"[{','.join(map(str, target_embedding))}]",
                'exclude_id': chunk_id,
                'threshold': 0.2,  # 对于相似片段搜索，使用较低的阈值
                'limit': top_k
            }

            result = db.execute(text(similar_sql), params)

            similar_chunks = []
            for row in result:
                similar_chunk = SearchResult(
                    content=row.content,
                    score=float(row.similarity_score),
                    metadata=dict(row.metadata_json) if row.metadata_json else {},
                    chunk_id=row.id,
                    source_file=row.source_file,
                    page_number=row.page_number
                )
                similar_chunks.append(similar_chunk)

            db.close()
            return similar_chunks

        except Exception as e:
            logger.error(f"获取相似片段失败: {e}")
            raise

    def get_service_stats(self) -> Dict[str, Any]:
        """
        获取RAG服务统计信息

        Returns:
            服务统计信息字典
        """
        try:
            db = next(get_db())

            # 获取文档片段总数
            total_chunks = db.query(TextbookChunk).count()

            # 按学科统计
            subject_stats = db.execute(text("""
                SELECT
                    metadata_json->>'subject' as subject,
                    COUNT(*) as count
                FROM textbook_chunks
                WHERE metadata_json->>'subject' IS NOT NULL
                GROUP BY metadata_json->>'subject'
                ORDER BY count DESC
            """)).fetchall()

            # 按年级统计
            grade_stats = db.execute(text("""
                SELECT
                    metadata_json->>'grade' as grade,
                    COUNT(*) as count
                FROM textbook_chunks
                WHERE metadata_json->>'grade' IS NOT NULL
                GROUP BY metadata_json->>'grade'
                ORDER BY count DESC
            """)).fetchall()

            db.close()

            return {
                'total_chunks': total_chunks,
                'embedding_dimension': self.embedding_dimension,
                'similarity_threshold': self.similarity_threshold,
                'max_results': self.max_results,
                'subject_distribution': {row.subject: row.count for row in subject_stats},
                'grade_distribution': {row.grade: row.count for row in grade_stats}
            }

        except Exception as e:
            logger.error(f"获取服务统计失败: {e}")
            return {}


def create_rag_service(**kwargs) -> RAGService:
    """
    创建RAG服务实例的工厂函数

    Args:
        **kwargs: RAGService初始化参数

    Returns:
        RAG服务实例
    """
    return RAGService(**kwargs)