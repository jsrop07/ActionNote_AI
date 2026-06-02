# =====================================================================
# backend/schemas/analysis.py
# 역할: API 요청/응답에서 사용하는 Pydantic 데이터 모델 정의
# - 프론트엔드의 src/types/analysis.ts 와 구조가 일치해야 함
# - 모든 Optional 필드는 AI가 원문에서 찾지 못할 때 None으로 반환
# =====================================================================

from pydantic import BaseModel
from typing import Optional


# ── 결정사항 ─────────────────────────────────────────────────────────
class Decision(BaseModel):
    """회의에서 내려진 결정사항 항목"""
    content: str                 # 결정 내용
    evidence_text: str           # 원문 근거 (AI가 발췌한 원본 텍스트)


# ── 실행 항목 ───────────────────────────────────────────────────────
class ActionItem(BaseModel):
    """회의에서 도출된 할 일 항목"""
    task: str                    # 해야 할 일
    owner: Optional[str]         # 담당자 (원문에 없으면 None → 프론트에서 '미정' 표시)
    due_date: Optional[str]      # 마감일 (원문에 없으면 None → 프론트에서 '미정' 표시)
    priority: Optional[str]      # 우선순위: "높음" | "보통" | "낮음" | None
    evidence_text: str           # 원문 근거


# ── 리스크 ────────────────────────────────────────────────────────────
class Risk(BaseModel):
    """회의에서 언급된 리스크 항목"""
    risk: str                    # 리스크 내용
    response: Optional[str]      # 대응 방향 (원문에 없으면 None)
    evidence_text: str           # 원문 근거


# ── 분석 결과 전체 ────────────────────────────────────────────────────
class AnalysisResult(BaseModel):
    """AI 분석의 최종 결과 구조 — 프론트의 AnalysisResult 타입과 동일"""
    summary: str                      # 전체 요약
    decisions: list[Decision]         # 결정사항 목록
    action_items: list[ActionItem]    # 실행 항목 목록
    risks: list[Risk]                 # 리스크 목록
    missing_info: list[str]           # 누락 정보 (문자열 목록)


# ── API 요청 모델 ─────────────────────────────────────────────────────
class AnalyzeTextRequest(BaseModel):
    """POST /api/analyze-text 요청 바디"""
    text: str                    # 분석할 회의록 또는 업무 메모 원문


class SaveGoogleDocRequest(BaseModel):
    """POST /api/save-google-doc 요청 바디"""
    title: str                   # 저장할 문서 이름 (빈 문자열이면 자동 생성)
    result: AnalysisResult       # 저장할 분석 결과


# ── API 응답 모델 ─────────────────────────────────────────────────────
class SaveGoogleDocResponse(BaseModel):
    """POST /api/save-google-doc 응답"""
    title: str                   # 실제로 저장된 문서명
    url: str                     # 생성된 Google Docs 문서 URL
