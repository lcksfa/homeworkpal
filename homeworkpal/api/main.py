"""
Homework Pal FastAPI Backend
Provides API endpoints for the frontend application
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
import asyncio
from dotenv import load_dotenv
from sqlalchemy import text

# 导入数据库连接
from homeworkpal.database.connection import init_database, test_connection, get_db
from homeworkpal.database.models import TextbookKnowledge, HomeworkSession, MistakeRecord

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Homework Pal API",
    description="AI-powered homework assistant backend",
    version="1.0.0"
)

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

class DatabaseStatus(BaseModel):
    connected: bool
    tables_created: bool
    pgvector_enabled: bool


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    try:
        print("Initializing database...")
        init_database()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization failed: {e}")
        # 不阻止应用启动，但记录错误


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


@app.get("/health/database")
async def database_health():
    """数据库健康检查"""
    try:
        # 测试基本连接
        connected = test_connection()

        # 测试表是否存在
        tables_ok = False
        pgvector_ok = False

        if connected:
            from homeworkpal.database.connection import engine
            with engine.connect() as conn:
                # 检查表是否存在
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM information_schema.tables
                    WHERE table_name IN ('textbook_knowledge', 'homework_sessions', 'mistake_records')
                """))
                table_count = result.fetchone()[0]
                tables_ok = table_count >= 3

                # 检查pgvector扩展
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM pg_extension WHERE extname = 'vector'
                """))
                pgvector_count = result.fetchone()[0]
                pgvector_ok = pgvector_count > 0

        return DatabaseStatus(
            connected=connected,
            tables_created=tables_ok,
            pgvector_enabled=pgvector_ok
        )

    except Exception as e:
        return DatabaseStatus(
            connected=False,
            tables_created=False,
            pgvector_enabled=False
        )


@app.get("/api/v1/status")
async def get_status():
    """Get API status"""
    return {
        "status": "operational",
        "version": "1.0.0",
        "features": {
            "rag": False,
            "vision": False,
            "mistake_notebook": False,
            "planner": False
        }
    }


@app.get("/api/v1/database/init")
async def init_database_endpoint():
    """手动初始化数据库端点"""
    try:
        init_database()
        return {"message": "Database initialized successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database initialization failed: {e}")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=os.getenv("RELOAD", "false").lower() == "true"
    )
