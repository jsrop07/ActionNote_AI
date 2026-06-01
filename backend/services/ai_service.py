# =====================================================================
# backend/services/ai_service.py
# 역할: AI 모델을 호출해 회의록 텍스트를 분석하는 서비스 레이어
# - 실제 AI API 호출 로직은 TODO로 표시되어 있음
# - analyze_text() 함수가 유일한 공개 인터페이스
# =====================================================================

import os
from dotenv import load_dotenv
from schemas.analysis import AnalysisResult, Decision, ActionItem, Risk

load_dotenv()

# AI 모델 설정 (환경변수에서 읽기)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")


def _build_prompt(text: str) -> str:
    """
    역할: AI에게 보낼 프롬프트를 구성한다.
    - 반환값: AI API에 전달할 시스템+유저 프롬프트 문자열
    - TODO: 실제 프롬프트 내용 작성 (한국어 회의록 분석 지시사항 포함)
    """
    # TODO: 실제 프롬프트 작성
    # 예시: summary, decisions, action_items, risks, missing_info 를
    #       JSON 형식으로 반환하도록 지시하는 프롬프트
    return f"""
다음 회의록을 분석하여 아래 JSON 형식으로 결과를 반환하세요.

[회의록]
{text}

[반환 형식]
TODO: 실제 JSON 스키마 프롬프트 작성
"""


async def analyze_text(text: str) -> AnalysisResult:
    """
    역할: 텍스트를 받아 AI 분석을 수행하고 AnalysisResult를 반환한다.
    - 매개변수 text: 분석할 원본 텍스트 (회의록, 업무 메모 등)
    - 반환값: AnalysisResult (구조화된 분석 결과)
    - TODO: 실제 AI API 호출 구현
    """
    # TODO: 실제 OpenAI / Gemini API 호출 구현
    # 예시 구조:
    # client = OpenAI(api_key=OPENAI_API_KEY)
    # response = await client.chat.completions.create(
    #     model=OPENAI_MODEL,
    #     messages=[{"role": "user", "content": _build_prompt(text)}],
    #     response_format={"type": "json_object"},
    # )
    # raw = json.loads(response.choices[0].message.content)
    # return AnalysisResult(**raw)

    # ── 임시 더미 반환값 (API 연결 전 테스트용) ──────────────────────
    return AnalysisResult(
        summary="[TODO] AI 분석 결과가 여기에 표시됩니다.",
        decisions=[
            Decision(
                content="[TODO] 결정사항 예시",
                evidence_text="[TODO] 원문 근거",
            )
        ],
        action_items=[
            ActionItem(
                task="[TODO] 액션 아이템 예시",
                owner=None,
                due_date=None,
                priority=None,
                evidence_text="[TODO] 원문 근거",
            )
        ],
        risks=[
            Risk(
                risk="[TODO] 리스크 예시",
                response=None,
                evidence_text="[TODO] 원문 근거",
            )
        ],
        missing_info=["[TODO] 누락 정보 예시"],
    )
