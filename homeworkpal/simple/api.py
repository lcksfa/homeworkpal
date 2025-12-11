"""
Homework Pal FastAPI Backend (Simplified Version)
提供基础的后端服务，暂时忽略数据库连接
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uvicorn
import os

from homeworkpal.core.config import settings
from homeworkpal.utils.logger import get_simple_logger
from homeworkpal.rag.qa_service import QAService, QARequest, QAResponse

# Initialize logger
logger = get_simple_logger()

# Initialize QA service
qa_service = QAService()

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered homework assistant backend",
    version=settings.VERSION,
    debug=settings.DEBUG
)

@app.on_event("startup")
async def startup_event():
    """Log application startup."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION} on port {settings.PORT}")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HealthResponse(BaseModel):
    status: str
    message: str


class AskRequest(BaseModel):
    """问答请求模型"""
    question: str = Field(..., description="学生提出的问题", min_length=1, max_length=500)
    subject: Optional[str] = Field(None, description="学科过滤，如'语文'、'数学'")
    grade: Optional[str] = Field(None, description="年级过滤，如'三年级'")
    unit: Optional[str] = Field(None, description="单元过滤")
    max_context_length: int = Field(3000, description="上下文最大长度", ge=500, le=5000)
    temperature: float = Field(0.7, description="生成温度", ge=0.1, le=1.0)
    max_tokens: int = Field(800, description="最大生成token数", ge=100, le=2000)


class AskResponse(BaseModel):
    """问答响应模型"""
    answer: str
    sources: List[Dict[str, Any]]
    question: str
    response_time: float
    context_used: bool
    metadata: Dict[str, Any]

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Homework Pal API is running"}

@app.get("/health")
async def health_check() -> HealthResponse:
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        message="Homework Pal API is running properly"
    )

@app.get("/api/v1/status")
async def get_status():
    """Get API status"""
    qa_status = qa_service.get_service_status()

    return {
        "status": qa_status.get("status", "operational"),
        "version": "1.0.0",
        "features": {
            "rag": True,
            "qa": qa_status.get("status") == "operational",
            "vision": False,
            "mistake_notebook": False,
            "planner": False
        },
        "components": qa_status.get("components", {})
    }


@app.post("/api/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """
    端到端RAG问答端点

    接收学生的问题，基于人教版教材内容生成适合三年级学生的答案

    Args:
        request: 问答请求对象

    Returns:
        问答响应对象，包含答案、来源和元数据

    Raises:
        HTTPException: 当问答处理失败时
    """
    try:
        logger.info(f"收到问答请求: {request.question}")

        # 转换为内部请求格式
        qa_request = QARequest(
            question=request.question,
            subject=request.subject,
            grade=request.grade,
            unit=request.unit,
            max_context_length=request.max_context_length,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )

        # 调用问答服务
        qa_response = await qa_service.ask_question(qa_request)

        logger.info(f"问答完成，耗时: {qa_response.response_time:.2f}秒")

        return AskResponse(
            answer=qa_response.answer,
            sources=qa_response.sources,
            question=qa_response.question,
            response_time=qa_response.response_time,
            context_used=qa_response.context_used,
            metadata=qa_response.metadata
        )

    except Exception as e:
        logger.error(f"问答处理失败: {e}")
        raise HTTPException(
            status_code=500,
            detail="问答服务暂时不可用，请稍后再试"
        )


@app.get("/api/qa/status")
async def get_qa_status():
    """获取问答服务详细状态"""
    return qa_service.get_service_status()

if __name__ == "__main__":
    uvicorn.run(
        "homeworkpal.simple.api:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )