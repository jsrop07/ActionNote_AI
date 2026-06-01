# =====================================================================
# backend/main.py
# 역할: FastAPI 애플리케이션 진입점
# - CORS 설정 (프론트엔드 개발 서버 허용)
# - /api/health 헬스체크 엔드포인트
# - analyze, export 라우터 등록
# 실행: uvicorn main:app --reload --port 8000
# =====================================================================

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from routers.analyze import router as analyze_router
from routers.export import router as export_router

# .env 파일 로드
load_dotenv()

# ── 허용할 프론트엔드 출처 ───────────────────────────────────────────
# 개발 환경: Vite 기본 포트 5173
# 배포 환경: .env의 ALLOWED_ORIGINS에 실제 도메인 추가
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

# ── FastAPI 앱 생성 ──────────────────────────────────────────────────
app = FastAPI(
    title="ActionNote AI API",
    description="회의록/업무 메모 분석 및 구조화 서비스",
    version="0.1.0",
)

# ── CORS 미들웨어 ────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 라우터 등록 ─────────────────────────────────────────────────────
# prefix="/api" 로 모든 엔드포인트가 /api/... 로 시작
app.include_router(analyze_router, prefix="/api", tags=["analyze"])
app.include_router(export_router, prefix="/api", tags=["export"])


# ── 헬스체크 엔드포인트 ─────────────────────────────────────────────
@app.get("/api/health", tags=["health"])
async def health_check():
    """
    역할: 서버가 정상적으로 동작 중인지 확인하는 엔드포인트.
    - 프론트엔드에서 서버 연결 상태를 확인할 때 사용
    - 응답: { "status": "ok" }
    """
    return {"status": "ok"}
