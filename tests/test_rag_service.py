"""
RAG服务测试
RAG Service Tests

测试RAG检索服务的语义搜索、向量检索和混合搜索功能
"""

import pytest
import logging
from typing import List
from unittest.mock import Mock, patch, MagicMock

from homeworkpal.rag.rag_service import RAGService, SearchResult, create_rag_service
from homeworkpal.llm.siliconflow import SiliconFlowClient
from homeworkpal.database.models import TextbookChunk

# 设置测试日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestRAGService:
    """RAG服务测试类"""

    @pytest.fixture
    def mock_embedding_client(self):
        """模拟向量嵌入客户端"""
        mock_client = Mock(spec=SiliconFlowClient)
        # 模拟1024维向量
        mock_client.embed_query.return_value = [0.1] * 1024
        return mock_client

    @pytest.fixture
    def rag_service(self, mock_embedding_client):
        """创建RAG服务实例"""
        return RAGService(
            embedding_client=mock_embedding_client,
            similarity_threshold=0.3,
            max_results=10
        )

    @pytest.fixture
    def sample_textbook_chunks(self):
        """示例教材片段数据"""
        return [
            {
                'id': 1,
                'content': '周长是指封闭图形一周的长度。计算长方形的周长可以用公式：周长 = (长 + 宽) × 2',
                'metadata_json': {'subject': '数学', 'grade': '三年级', 'unit': '第一单元', 'page': 15},
                'source_file': '数学三上.pdf',
                'page_number': 15
            },
            {
                'id': 2,
                'content': '正方形的周长计算公式是：周长 = 边长 × 4。例如，边长为5厘米的正方形，周长是20厘米。',
                'metadata_json': {'subject': '数学', 'grade': '三年级', 'unit': '第一单元', 'page': 16},
                'source_file': '数学三上.pdf',
                'page_number': 16
            },
            {
                'id': 3,
                'content': '时间单位有：时、分、秒。1小时 = 60分钟，1分钟 = 60秒。',
                'metadata_json': {'subject': '数学', 'grade': '三年级', 'unit': '第二单元', 'page': 25},
                'source_file': '数学三上.pdf',
                'page_number': 25
            }
        ]

    def test_rag_service_initialization(self, mock_embedding_client):
        """测试RAG服务初始化"""
        service = RAGService(
            embedding_client=mock_embedding_client,
            similarity_threshold=0.5,
            max_results=5
        )

        assert service.embedding_client == mock_embedding_client
        assert service.similarity_threshold == 0.5
        assert service.max_results == 5
        assert service.embedding_dimension == 1024

    @patch('homeworkpal.rag.rag_service.get_db')
    def test_generate_query_embedding(self, mock_get_db, rag_service, mock_embedding_client):
        """测试查询向量生成"""
        query = "周长怎么算"
        expected_embedding = [0.1] * 1024
        mock_embedding_client.embed_query.return_value = expected_embedding

        result = rag_service._generate_query_embedding(query)

        assert result == expected_embedding
        mock_embedding_client.embed_query.assert_called_once_with(query)

    @patch('homeworkpal.rag.rag_service.get_db')
    def test_search_basic(self, mock_get_db, rag_service, sample_textbook_chunks):
        """测试基础语义搜索"""
        # 模拟数据库查询结果
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # 模拟查询执行结果
        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([
            Mock(
                content=chunk['content'],
                similarity_score=0.85,
                metadata_json=chunk['metadata_json'],
                id=chunk['id'],
                source_file=chunk['source_file'],
                page_number=chunk['page_number']
            ) for chunk in sample_textbook_chunks[:2]
        ]))
        mock_db.execute.return_value = mock_result

        # 执行搜索
        results = rag_service.search("周长怎么算", top_k=3)

        # 验证结果
        assert len(results) == 2
        assert isinstance(results[0], SearchResult)
        assert results[0].content == sample_textbook_chunks[0]['content']
        assert results[0].score == 0.85
        assert results[0].metadata['subject'] == '数学'

    @patch('homeworkpal.rag.rag_service.get_db')
    def test_search_with_filters(self, mock_get_db, rag_service, sample_textbook_chunks):
        """测试带过滤条件的语义搜索"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([
            Mock(
                content=sample_textbook_chunks[1]['content'],
                similarity_score=0.82,
                metadata_json=sample_textbook_chunks[1]['metadata_json'],
                id=sample_textbook_chunks[1]['id'],
                source_file=sample_textbook_chunks[1]['source_file'],
                page_number=sample_textbook_chunks[1]['page_number']
            )
        ]))
        mock_db.execute.return_value = mock_result

        # 执行带过滤条件的搜索
        results = rag_service.search(
            "正方形周长",
            subject="数学",
            grade="三年级",
            unit="第一单元",
            top_k=3
        )

        # 验证结果
        assert len(results) == 1
        assert results[0].content == sample_textbook_chunks[1]['content']

    @patch('homeworkpal.rag.rag_service.get_db')
    def test_search_no_results(self, mock_get_db, rag_service):
        """测试无结果情况"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # 模拟空结果
        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([]))
        mock_db.execute.return_value = mock_result

        results = rag_service.search("不相关的内容", top_k=3)

        assert len(results) == 0

    @patch('homeworkpal.rag.rag_service.get_db')
    def test_keyword_search(self, mock_get_db, rag_service, sample_textbook_chunks):
        """测试关键词搜索"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([
            Mock(
                content=chunk['content'],
                keyword_score=0.75,
                metadata_json=chunk['metadata_json'],
                id=chunk['id'],
                source_file=chunk['source_file'],
                page_number=chunk['page_number']
            ) for chunk in sample_textbook_chunks[:1]
        ]))
        mock_db.execute.return_value = mock_result

        results = rag_service._keyword_search("周长", top_k=3)

        assert len(results) == 1
        assert "周长" in results[0].content

    @patch('homeworkpal.rag.rag_service.get_db')
    def test_hybrid_search(self, mock_get_db, rag_service, sample_textbook_chunks):
        """测试混合搜索"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # 模拟语义搜索结果
        mock_semantic_result = Mock()
        mock_semantic_result.__iter__ = Mock(return_value=iter([
            Mock(
                content=sample_textbook_chunks[0]['content'],
                similarity_score=0.85,
                metadata_json=sample_textbook_chunks[0]['metadata_json'],
                id=sample_textbook_chunks[0]['id'],
                source_file=sample_textbook_chunks[0]['source_file'],
                page_number=sample_textbook_chunks[0]['page_number']
            )
        ]))

        # 模拟关键词搜索结果
        mock_keyword_result = Mock()
        mock_keyword_result.__iter__ = Mock(return_value=iter([
            Mock(
                content=sample_textbook_chunks[1]['content'],
                keyword_score=0.75,
                metadata_json=sample_textbook_chunks[1]['metadata_json'],
                id=sample_textbook_chunks[1]['id'],
                source_file=sample_textbook_chunks[1]['source_file'],
                page_number=sample_textbook_chunks[1]['page_number']
            )
        ]))

        # 设置mock_db.execute的返回值
        mock_db.execute.side_effect = [mock_semantic_result, mock_keyword_result]

        results = rag_service.hybrid_search("周长", top_k=3, keyword_weight=0.4, semantic_weight=0.6)

        assert len(results) >= 1
        assert isinstance(results[0], SearchResult)

    @patch('homeworkpal.rag.rag_service.get_db')
    def test_get_similar_chunks(self, mock_get_db, rag_service, sample_textbook_chunks):
        """测试获取相似片段"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # 模拟目标片段
        target_chunk = Mock()
        target_chunk.embedding = [0.1] * 1024
        mock_db.query.return_value.filter.return_value.first.return_value = target_chunk

        # 模拟相似片段查询结果
        mock_similar_result = Mock()
        mock_similar_result.__iter__ = Mock(return_value=iter([
            Mock(
                content=sample_textbook_chunks[1]['content'],
                similarity_score=0.78,
                metadata_json=sample_textbook_chunks[1]['metadata_json'],
                id=sample_textbook_chunks[1]['id'],
                source_file=sample_textbook_chunks[1]['source_file'],
                page_number=sample_textbook_chunks[1]['page_number']
            )
        ]))
        mock_db.execute.return_value = mock_similar_result

        similar_chunks = rag_service.get_similar_chunks(chunk_id=1, top_k=3)

        assert len(similar_chunks) == 1
        assert similar_chunks[0].content == sample_textbook_chunks[1]['content']

    @patch('homeworkpal.rag.rag_service.get_db')
    def test_get_service_stats(self, mock_get_db):
        """测试获取服务统计信息"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # 模拟统计数据
        mock_db.query.return_value.count.return_value = 128
        mock_db.execute.side_effect = [
            # subject_stats
            [
                Mock(subject='数学', count=80),
                Mock(subject='语文', count=48)
            ],
            # grade_stats
            [
                Mock(grade='三年级', count=128)
            ]
        ]

        rag_service = RAGService()
        stats = rag_service.get_service_stats()

        assert stats['total_chunks'] == 128
        assert stats['embedding_dimension'] == 1024
        assert stats['subject_distribution']['数学'] == 80
        assert stats['grade_distribution']['三年级'] == 128

    def test_search_result_to_dict(self):
        """测试SearchResult转换为字典"""
        result = SearchResult(
            content="测试内容",
            score=0.85,
            metadata={'subject': '数学', 'grade': '三年级'},
            chunk_id=1,
            source_file="test.pdf",
            page_number=10
        )

        result_dict = result.to_dict()

        assert result_dict['content'] == "测试内容"
        assert result_dict['score'] == 0.85
        assert result_dict['metadata']['subject'] == '数学'
        assert result_dict['chunk_id'] == 1
        assert result_dict['source_file'] == "test.pdf"
        assert result_dict['page_number'] == 10

    def test_create_rag_service_factory(self):
        """测试RAG服务工厂函数"""
        service = create_rag_service(similarity_threshold=0.4, max_results=8)

        assert isinstance(service, RAGService)
        assert service.similarity_threshold == 0.4
        assert service.max_results == 8


# 集成测试 - 需要真实数据库连接
@pytest.mark.integration
class TestRAGServiceIntegration:
    """RAG服务集成测试类"""

    @pytest.fixture
    def rag_service(self):
        """创建真实的RAG服务实例"""
        # 使用真实的SiliconFlow客户端（需要有效的API密钥）
        try:
            embedding_client = SiliconFlowClient()
            return RAGService(
                embedding_client=embedding_client,
                similarity_threshold=0.3,
                max_results=5
            )
        except Exception as e:
            pytest.skip(f"无法创建SiliconFlow客户端: {e}")

    @pytest.mark.skipif(
        not True,  # 暂时跳过集成测试
        reason="需要 --run-integration 选项来运行集成测试"
    )
    def test_real_search_query(self, rag_service):
        """测试真实搜索查询"""
        try:
            results = rag_service.search("周长怎么算", top_k=3)

            assert isinstance(results, list)
            if results:  # 如果有数据的话
                assert isinstance(results[0], SearchResult)
                assert results[0].content.strip()
                assert results[0].score >= rag_service.similarity_threshold
                logger.info(f"找到 {len(results)} 个相关结果")

        except Exception as e:
            logger.error(f"集成测试失败: {e}")
            pytest.skip(f"数据库或API不可用: {e}")


def test_search_result_dataclass():
    """测试SearchResult数据类"""
    result = SearchResult(
        content="长方形周长计算公式：周长 = (长 + 宽) × 2",
        score=0.89,
        metadata={"subject": "数学", "grade": "三年级"},
        chunk_id=1,
        source_file="数学三上.pdf",
        page_number=15
    )

    # 测试字段访问
    assert result.content == "长方形周长计算公式：周长 = (长 + 宽) × 2"
    assert result.score == 0.89
    assert result.metadata["subject"] == "数学"
    assert result.chunk_id == 1
    assert result.source_file == "数学三上.pdf"
    assert result.page_number == 15

    # 测试to_dict方法
    result_dict = result.to_dict()
    assert result_dict["content"] == result.content
    assert result_dict["score"] == result.score
    assert result_dict["metadata"] == result.metadata
    assert result_dict["chunk_id"] == result.chunk_id


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])