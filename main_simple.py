"""
Homework Pal FastAPI Backend (Simplified Version)
提供基础的后端服务，暂时忽略数据库连接
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
from dotenv import load_dotenv

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

if __name__ == "__main__":
    uvicorn.run(
        "main_simple:app",
        host="0.0.0.0",
        port=8001,
        reload=os.getenv("RELOAD", "false").lower() == "true"
    )