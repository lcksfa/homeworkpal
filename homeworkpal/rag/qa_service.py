"""
RAG问答服务
RAG Question-Answering Service for Homework Pal

实现端到端的问答流程：问题→向量化→检索→生成→答案
基于人教版教材内容为三年级学生提供教育导向的答案
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import json
import time

from sqlalchemy.orm import Session
from ..database.connection import get_db
from ..database.models import TextbookChunk
from ..rag.rag_service import RAGService, SearchResult
from ..llm.siliconflow import SiliconFlowClient

logger = logging.getLogger(__name__)


@dataclass
class QARequest:
    """问答请求数据类"""
    question: str
    subject: Optional[str] = None  # 学科过滤，如"语文"、"数学"
    grade: Optional[str] = None    # 年级过滤，如"三年级"
    unit: Optional[str] = None     # 单元过滤
    max_context_length: int = 3000 # 上下文最大长度
    temperature: float = 0.7       # 生成温度
    max_tokens: int = 800          # 最大生成token数


@dataclass
class QAResponse:
    """问答响应数据类"""
    answer: str                    # 生成的答案
    sources: List[Dict[str, Any]] # 参考来源
    question: str                 # 原始问题
    response_time: float          # 响应时间（秒）
    context_used: bool           # 是否使用了教材上下文
    metadata: Dict[str, Any]     # 额外元数据

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'answer': self.answer,
            'sources': self.sources,
            'question': self.question,
            'response_time': self.response_time,
            'context_used': self.context_used,
            'metadata': self.metadata
        }


class QAService:
    """RAG问答服务类

    实现完整的问答流程：问题理解 → 向量检索 → 上下文构建 → LLM生成答案 → 结果后处理
    专门针对三年级学生的教育场景优化，使用教师语形和鼓励性语言
    """

    def __init__(self,
                 rag_service: Optional[RAGService] = None,
                 llm_client: Optional[SiliconFlowClient] = None):
        """
        初始化问答服务

        Args:
            rag_service: RAG检索服务实例
            llm_client: LLM客户端实例
        """
        self.rag_service = rag_service or RAGService()
        self.llm_client = llm_client or SiliconFlowClient()

        # 教师语形Prompt模板
        self.teacher_prompt_template = """
你是一位经验丰富的小学三年级语文老师，正在耐心回答学生的问题。

## 学生的问题：
{question}

## 相关教材内容：
{context}

## 回答要求：
1. 使用温柔、鼓励的语气，像老师和学生说话一样亲切
2. 用简单易懂的语言解释，避免复杂词汇
3. 如果有定义，先给出明确的定义，然后用生活中的例子帮助理解
4. 回答要准确基于提供的教材内容，不要编造信息
5. 结尾要鼓励学生继续学习，保护学生的学习兴趣
6. 回答长度控制在200-400字之间，适合三年级学生阅读

## 请回答：
"""

        # 无上下文时的回答模板
        self.no_context_prompt = """
你是一位经验丰富的小学三年级语文老师，正在回答学生的问题。

## 学生的问题：
{question}

## 回答要求：
1. 使用温柔、鼓励的语气，像老师和学生说话一样亲切
2. 用简单易懂的语言解释，避免复杂词汇
3. 如果是学科概念问题，给出基础定义和生活中的例子
4. 承认教材中没有找到完全对应的内容，但仍提供有用的指导
5. 建议学生可以查阅相关教材或询问老师
6. 回答长度控制在150-300字之间
7. 结尾要鼓励学生的学习热情

## 请回答：
"""

    async def ask_question(self, request: QARequest) -> QAResponse:
        """
        处理问答请求的完整流程

        Args:
            request: 问答请求对象

        Returns:
            问答响应对象
        """
        start_time = time.time()

        try:
            logger.info(f"开始处理问题: {request.question}")

            # 步骤1: 向量检索相关教材内容
            search_results = await self._retrieve_relevant_content(request)

            # 步骤2: 构建上下文和Prompt
            context, prompt = self._build_context_and_prompt(request, search_results)

            # 步骤3: LLM生成答案
            answer = await self._generate_answer(prompt, request.temperature, request.max_tokens)

            # 步骤4: 准备响应数据
            response_time = time.time() - start_time

            sources = []
            for result in search_results:
                source_info = {
                    'content': result.content[:200] + "..." if len(result.content) > 200 else result.content,
                    'score': result.score,
                    'source_file': result.source_file,
                    'page_number': result.page_number,
                    'metadata': result.metadata
                }
                sources.append(source_info)

            metadata = {
                'subject_filter': request.subject,
                'grade_filter': request.grade,
                'unit_filter': request.unit,
                'search_results_count': len(search_results),
                'context_length': len(context),
                'model_info': self.llm_client.llm_client.get_model_info()
            }

            response = QAResponse(
                answer=answer,
                sources=sources,
                question=request.question,
                response_time=response_time,
                context_used=len(search_results) > 0,
                metadata=metadata
            )

            logger.info(f"问答完成，耗时: {response_time:.2f}秒，检索到{len(search_results)}个相关片段")
            return response

        except Exception as e:
            logger.error(f"问答处理失败: {e}")
            # 返回错误响应
            error_response_time = time.time() - start_time
            return QAResponse(
                answer=f"抱歉，老师现在遇到了一些技术问题，无法回答你的问题。请稍后再试，或者直接询问你的语文老师哦！继续加油学习！💪",
                sources=[],
                question=request.question,
                response_time=error_response_time,
                context_used=False,
                metadata={'error': str(e)}
            )

    async def ask_question_with_error_handling(self, request: QARequest) -> QAResponse:
        """
        处理问答请求，带有详细的错误处理逻辑（用于测试）

        Args:
            request: 问答请求对象

        Returns:
            问答响应对象
        """
        start_time = time.time()
        retrieval_failed = False

        try:
            logger.info(f"开始处理问题: {request.question}")

            # 步骤1: 向量检索相关教材内容
            try:
                search_results = await self._retrieve_relevant_content(request)
            except Exception as retrieval_error:
                logger.error(f"内容检索失败: {retrieval_error}")
                retrieval_failed = True
                # 直接返回错误响应，因为我们无法获取任何上下文
                error_response_time = time.time() - start_time
                return QAResponse(
                    answer=f"抱歉，老师的知识库现在需要休息一下。你可以把这个问题记下来，明天问学校的老师哦！继续努力！🌟",
                    sources=[],
                    question=request.question,
                    response_time=error_response_time,
                    context_used=False,
                    metadata={'error': '检索服务不可用'}
                )

            # 步骤2: 构建上下文和Prompt
            context, prompt = self._build_context_and_prompt(request, search_results)

            # 步骤3: LLM生成答案
            try:
                answer = await self._generate_answer(prompt, request.temperature, request.max_tokens)
            except Exception as generation_error:
                logger.error(f"答案生成失败: {generation_error}")
                error_response_time = time.time() - start_time
                return QAResponse(
                    answer=f"抱歉，老师现在需要休息一下，没能很好地回答你的问题。你可以把这个问题记下来，明天问学校的老师哦！继续努力！🌟",
                    sources=[],
                    question=request.question,
                    response_time=error_response_time,
                    context_used=False,
                    metadata={'error': '生成服务不可用'}
                )

            # 步骤4: 准备响应数据
            response_time = time.time() - start_time

            sources = []
            for result in search_results:
                source_info = {
                    'content': result.content[:200] + "..." if len(result.content) > 200 else result.content,
                    'score': result.score,
                    'source_file': result.source_file,
                    'page_number': result.page_number,
                    'metadata': result.metadata
                }
                sources.append(source_info)

            metadata = {
                'subject_filter': request.subject,
                'grade_filter': request.grade,
                'unit_filter': request.unit,
                'search_results_count': len(search_results),
                'context_length': len(context),
                'model_info': self.llm_client.llm_client.get_model_info(),
                'retrieval_failed': retrieval_failed
            }

            response = QAResponse(
                answer=answer,
                sources=sources,
                question=request.question,
                response_time=response_time,
                context_used=len(search_results) > 0,
                metadata=metadata
            )

            logger.info(f"问答完成，耗时: {response_time:.2f}秒，检索到{len(search_results)}个相关片段")
            return response

        except Exception as e:
            logger.error(f"问答处理完全失败: {e}")
            # 返回错误响应
            error_response_time = time.time() - start_time
            return QAResponse(
                answer=f"抱歉，老师现在遇到了一些技术问题，无法回答你的问题。请稍后再试，或者直接询问你的语文老师哦！继续加油学习！💪",
                sources=[],
                question=request.question,
                response_time=error_response_time,
                context_used=False,
                metadata={'error': str(e)}
            )

    async def _retrieve_relevant_content(self, request: QARequest) -> List[SearchResult]:
        """
        检索相关的教材内容

        Args:
            request: 问答请求对象

        Returns:
            检索结果列表
        """
        # 使用RAG服务进行语义搜索
        results = self.rag_service.search(
            query=request.question,
            top_k=5,  # 检索5个最相关的片段
            subject=request.subject,
            grade=request.grade,
            unit=request.unit
        )

        # 过滤低质量结果
        filtered_results = []
        for result in results:
            if result.score > 0.3:  # 相似度阈值
                filtered_results.append(result)

        logger.info(f"检索到 {len(filtered_results)} 个高质量相关片段（阈值>0.3）")
        return filtered_results

    def _build_context_and_prompt(self,
                                 request: QARequest,
                                 search_results: List[SearchResult]) -> Tuple[str, str]:
        """
        构建上下文和Prompt

        Args:
            request: 问答请求对象
            search_results: 检索结果列表

        Returns:
            上下文文本和完整Prompt
        """
        context_parts = []
        current_length = 0
        max_context_length = request.max_context_length

        # 构建上下文
        for i, result in enumerate(search_results):
            # 格式化片段
            source_info = []
            if result.source_file:
                source_info.append(f"来源: {result.source_file}")
            if result.page_number:
                source_info.append(f"第{result.page_number}页")

            source_text = " | ".join(source_info) if source_info else "教材内容"

            formatted_chunk = f"【教材片段{i+1}】{source_text}\n{result.content}\n"

            # 检查长度限制
            if current_length + len(formatted_chunk) > max_context_length:
                break

            context_parts.append(formatted_chunk)
            current_length += len(formatted_chunk)

        context = "\n".join(context_parts)

        # 选择合适的Prompt模板
        if context.strip():
            prompt = self.teacher_prompt_template.format(
                question=request.question,
                context=context
            )
        else:
            # 没有找到相关内容
            context = "没有找到与问题直接相关的教材内容。"
            prompt = self.no_context_prompt.format(question=request.question)

        return context, prompt

    async def _generate_answer(self,
                             prompt: str,
                             temperature: float = 0.7,
                             max_tokens: int = 800) -> str:
        """
        使用LLM生成答案

        Args:
            prompt: 完整的Prompt
            temperature: 生成温度
            max_tokens: 最大token数

        Returns:
            生成的答案文本
        """
        try:
            # 准备消息
            messages = [
                {"role": "system", "content": "你是一位专业的小学语文老师，擅长用简单易懂的语言教三年级学生。"},
                {"role": "user", "content": prompt}
            ]

            logger.debug(f"生成答案，Prompt长度: {len(prompt)}")

            # 调用LLM
            response = self.llm_client.llm_client.chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            # 提取回复文本
            answer = self.llm_client.llm_client.get_response_text(response)

            # 清理答案格式
            answer = self._clean_answer(answer)

            logger.debug(f"生成答案成功，长度: {len(answer)}")
            return answer

        except Exception as e:
            logger.error(f"答案生成失败: {e}")
            # 返回默认答案
            return "抱歉，老师现在需要休息一下，没能很好地回答你的问题。你可以把这个问题记下来，明天问学校的老师哦！继续努力！🌟"

    def _clean_answer(self, answer: str) -> str:
        """
        清理答案文本

        Args:
            answer: 原始答案

        Returns:
            清理后的答案
        """
        # 移除可能的JSON格式标记
        answer = answer.strip()
        if answer.startswith('```json'):
            answer = answer[7:]
        if answer.startswith('```'):
            answer = answer[3:]
        if answer.endswith('```'):
            answer = answer[:-3]

        # 移除可能的引号
        answer = answer.strip('"\'')

        # 清理多余的空行
        lines = answer.split('\n')
        cleaned_lines = [line.strip() for line in lines if line.strip()]
        answer = '\n'.join(cleaned_lines)

        return answer

    def get_service_status(self) -> Dict[str, Any]:
        """
        获取服务状态

        Returns:
            服务状态信息
        """
        try:
            # 测试RAG服务
            rag_status = "connected"
            rag_error = None
            try:
                test_results = self.rag_service.search("测试", top_k=1)
                rag_status = "working" if len(test_results) >= 0 else "error"
            except Exception as e:
                rag_status = "error"
                rag_error = str(e)

            # 测试LLM服务
            llm_status = "connected"
            llm_error = None
            try:
                llm_info = self.llm_client.llm_client.get_model_info()
                llm_status = "working"
            except Exception as e:
                llm_status = "error"
                llm_error = str(e)

            return {
                "status": "operational" if rag_status == "working" and llm_status == "working" else "degraded",
                "components": {
                    "rag_service": {
                        "status": rag_status,
                        "error": rag_error
                    },
                    "llm_service": {
                        "status": llm_status,
                        "error": llm_error,
                        "model_info": llm_info if 'llm_info' in locals() else None
                    }
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }


# 单例实例
qa_service = QAService()