"""
测试RAG问答服务
Test cases for RAG Question-Answering Service
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import time

from homeworkpal.rag.qa_service import QAService, QARequest, QAResponse
from homeworkpal.rag.rag_service import SearchResult


class TestQAService:
    """问答服务测试类"""

    @pytest.fixture
    def mock_rag_service(self):
        """模拟RAG检索服务"""
        mock_rag = Mock()
        mock_rag.search = Mock(return_value=[
            SearchResult(
                content="周长是围成一个图形边缘的总长度。我们可以用绳子沿着图形的边缘围一圈，绳子的长度就是这个图形的周长。",
                score=0.85,
                metadata={"subject": "数学", "grade": "三年级"},
                chunk_id=1,
                source_file="数学教材.pdf",
                page_number=45
            ),
            SearchResult(
                content="测量周长时，我们可以用尺子测量正方形的每条边，然后把四条边的长度加起来。",
                score=0.78,
                metadata={"subject": "数学", "grade": "三年级"},
                chunk_id=2,
                source_file="数学教材.pdf",
                page_number=46
            )
        ])
        return mock_rag

    @pytest.fixture
    def mock_llm_client(self):
        """模拟LLM客户端"""
        mock_llm = Mock()
        mock_llm.chat_completion = Mock(return_value={
            "choices": [{
                "message": {
                    "content": "嗨，小朋友！周长就是围成一个图形边缘的总长度哦！比如我们可以用绳子沿着图形的边缘围一圈，绳子的长度就是周长。你学会了吗？继续加油！💪"
                }
            }],
            "usage": {"total_tokens": 150}
        })
        mock_llm.get_response_text = Mock(return_value="嗨，小朋友！周长就是围成一个图形边缘的总长度哦！比如我们可以用绳子沿着图形的边缘围一圈，绳子的长度就是周长。你学会了吗？继续加油！💪")
        mock_llm.get_model_info = Mock(return_value={
            "model_name": "Qwen/Qwen2.5-7B-Instruct",
            "provider": "SiliconFlow",
            "type": "chat_completion"
        })
        return mock_llm

    @pytest.fixture
    def qa_service(self, mock_rag_service, mock_llm_client):
        """创建问答服务实例"""
        mock_siliconflow = Mock()
        mock_siliconflow.llm_client = mock_llm_client
        mock_siliconflow.embed_query = Mock(return_value=[0.1] * 1024)

        with patch('homeworkpal.rag.qa_service.SiliconFlowClient', return_value=mock_siliconflow):
            with patch('homeworkpal.rag.qa_service.RAGService', return_value=mock_rag_service):
                service = QAService()
                service.llm_client = mock_siliconflow
                service.rag_service = mock_rag_service
                return service

    @pytest.mark.asyncio
    async def test_ask_question_with_context(self, qa_service, mock_rag_service):
        """测试有上下文的问答"""
        request = QARequest(
            question="周长是什么",
            subject="数学",
            grade="三年级",
            temperature=0.7,
            max_tokens=800
        )

        response = await qa_service.ask_question(request)

        # 验证响应结构
        assert isinstance(response, QAResponse)
        assert response.question == "周长是什么"
        assert response.context_used is True
        assert response.response_time > 0
        assert len(response.answer) > 0
        assert len(response.sources) == 2

        # 验证调用次数
        mock_rag_service.search.assert_called_once_with(
            query="周长是什么",
            top_k=5,
            subject="数学",
            grade="三年级",
            unit=None
        )

        # 验证答案质量
        assert "小朋友" in response.answer  # 教师语形
        assert "周长" in response.answer
        assert len(response.answer) < 500  # 适合三年级学生阅读长度

    @pytest.mark.asyncio
    async def test_ask_question_no_context(self, qa_service, mock_rag_service):
        """测试无上下文的问答"""
        # 设置检索无结果
        mock_rag_service.search.return_value = []

        request = QARequest(
            question="什么是量子力学",
            subject="物理",
            grade="三年级"
        )

        response = await qa_service.ask_question(request)

        # 验证响应
        assert response.context_used is False
        assert len(response.sources) == 0
        assert len(response.answer) > 0

        # 验证答案包含适当的指导
        answer_text = response.answer.lower()
        assert any(word in answer_text for word in ["教材", "老师", "学习", "继续", "加油"])

    @pytest.mark.asyncio
    async def test_ask_question_with_filters(self, qa_service, mock_rag_service):
        """测试带过滤条件的问答"""
        request = QARequest(
            question="作文怎么写",
            subject="语文",
            grade="三年级",
            unit="第1单元"
        )

        response = await qa_service.ask_question(request)

        # 验证调用了正确的过滤参数
        mock_rag_service.search.assert_called_once_with(
            query="作文怎么写",
            top_k=5,
            subject="语文",
            grade="三年级",
            unit="第1单元"
        )

        assert isinstance(response, QAResponse)

    @pytest.mark.asyncio
    async def test_ask_question_error_handling(self, qa_service, mock_rag_service):
        """测试错误处理"""
        # 模拟RAG服务异常
        mock_rag_service.search.side_effect = Exception("检索服务不可用")

        request = QARequest(
            question="测试问题",
            subject="语文",
            grade="三年级"
        )

        response = await qa_service.ask_question_with_error_handling(request)

        # 验证错误响应
        assert response.context_used is False
        # 检查是否包含错误处理相关的词汇
        assert any(word in response.answer for word in ["抱歉", "知识库", "休息一下", "老师"])
        assert response.metadata.get("error") is not None

    def test_build_context_with_results(self, qa_service):
        """测试上下文构建"""
        search_results = [
            SearchResult(
                content="这是第一个教材片段",
                score=0.9,
                metadata={"subject": "语文"},
                chunk_id=1,
                source_file="语文教材.pdf",
                page_number=10
            ),
            SearchResult(
                content="这是第二个教材片段",
                score=0.8,
                metadata={"subject": "语文"},
                chunk_id=2,
                source_file="语文教材.pdf",
                page_number=11
            )
        ]

        request = QARequest(question="测试问题", max_context_length=1000)
        context, prompt = qa_service._build_context_and_prompt(request, search_results)

        # 验证上下文
        assert "教材片段1" in context
        assert "教材片段2" in context
        assert "来源: 语文教材.pdf" in context
        assert "第10页" in context

        # 验证Prompt
        assert "测试问题" in prompt
        assert "三年级语文老师" in prompt
        assert context in prompt

    def test_build_context_no_results(self, qa_service):
        """测试无检索结果时的上下文构建"""
        request = QARequest(question="测试问题")
        context, prompt = qa_service._build_context_and_prompt(request, [])

        assert "没有找到与问题直接相关的教材内容" in context
        assert "测试问题" in prompt
        assert prompt == qa_service.no_context_prompt.format(question="测试问题")

    def test_clean_answer(self, qa_service):
        """测试答案清理"""
        dirty_answer = """```json
这是一个测试答案
```"""

        cleaned = qa_service._clean_answer(dirty_answer)
        assert cleaned == "这是一个测试答案"

        # 测试多余空行清理
        multiline_answer = "第一行\n\n\n第二行\n\n第三行"
        cleaned = qa_service._clean_answer(multiline_answer)
        assert cleaned == "第一行\n第二行\n第三行"

    def test_get_service_status(self, qa_service, mock_rag_service):
        """测试服务状态获取"""
        status = qa_service.get_service_status()

        # 验证状态结构
        assert "status" in status
        assert "components" in status
        assert "rag_service" in status["components"]
        assert "llm_service" in status["components"]

        # 验证RAG服务状态
        rag_status = status["components"]["rag_service"]
        assert rag_status["status"] == "working"

        # 验证LLM服务状态
        llm_status = status["components"]["llm_service"]
        assert llm_status["status"] == "working"
        assert "model_info" in llm_status

    @pytest.mark.asyncio
    async def test_generate_answer(self, qa_service):
        """测试答案生成"""
        prompt = "测试Prompt"

        answer = await qa_service._generate_answer(prompt)

        # 验证LLM被调用
        qa_service.llm_client.llm_client.chat_completion.assert_called_once()

        # 验证返回的答案
        assert isinstance(answer, str)
        assert len(answer) > 0

    @pytest.mark.asyncio
    async def test_filter_low_quality_results(self, qa_service):
        """测试低质量结果过滤"""
        # 模拟低质量结果
        mock_rag_service = Mock()
        mock_rag_service.search.return_value = [
            SearchResult(content="高质量内容", score=0.8, metadata={}, chunk_id=1),
            SearchResult(content="低质量内容", score=0.2, metadata={}, chunk_id=2),  # 低于阈值
            SearchResult(content="中等质量内容", score=0.4, metadata={}, chunk_id=3)
        ]

        qa_service.rag_service = mock_rag_service

        request = QARequest(question="测试问题")
        results = await qa_service._retrieve_relevant_content(request)

        # 验证过滤结果
        assert len(results) == 2  # 只有score > 0.3的结果被保留
        assert all(result.score > 0.3 for result in results)

    def test_response_serialization(self, qa_service):
        """测试响应序列化"""
        response = QAResponse(
            answer="测试答案",
            sources=[{"content": "测试来源", "score": 0.8}],
            question="测试问题",
            response_time=1.5,
            context_used=True,
            metadata={"test": "value"}
        )

        response_dict = response.to_dict()

        # 验证序列化结果
        assert response_dict["answer"] == "测试答案"
        assert response_dict["question"] == "测试问题"
        assert response_dict["response_time"] == 1.5
        assert response_dict["context_used"] is True
        assert len(response_dict["sources"]) == 1
        assert response_dict["metadata"]["test"] == "value"


class TestQAIntegration:
    """集成测试类"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_end_to_end_qa_flow(self):
        """端到端问答流程测试（需要真实的API密钥和数据库）"""
        # 这个测试需要真实的API密钥和数据库连接
        # 在CI/CD环境中可能需要skip
        pytest.skip("需要真实的API密钥和数据库连接")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_qa_performance_benchmarks(self):
        """性能基准测试"""
        # 测试响应时间、并发性能等
        pytest.skip("性能基准测试，需要特殊环境设置")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])