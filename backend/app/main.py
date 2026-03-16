"""
Manufacturing AX Agent — FastAPI 메인 앱
실행: uvicorn app.main:app --reload --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router

app = FastAPI(
    title="Manufacturing AX Agent API",
    description="CNC 예지보전 + 온톨로지 + LLM 자율 판단 관제 시스템",
    version="0.1.0",
)

# CORS 설정 (프론트엔드 연동용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite, Next.js
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(router)


@app.get("/")
async def root():
    return {
        "name": "Manufacturing AX Agent",
        "version": "0.1.0",
        "docs": "/docs",
        "endpoints": 13,
    }
