# backend/services/ai_service.py
# 역할:
# - 회의록/업무 메모 텍스트를 OpenAI API로 분석합니다.
# - AI 응답을 JSON으로 파싱한 뒤 AnalysisResult 형태로 반환합니다.
# - 원문에 없는 담당자/마감일은 추측하지 않고 "미정"으로 처리하도록 프롬프트를 구성합니다.

import json
import os
from typing import Any, Dict

from dotenv import load_dotenv
from openai import AsyncOpenAI

from schemas.analysis import AnalysisResult, Decision, ActionItem, Risk

load_dotenv()


# 이 함수는 OpenAI 클라이언트를 생성합니다.
# OPENAI_API_KEY가 없으면 명확한 오류를 발생시켜 설정 문제를 바로 알 수 있게 합니다.
def get_openai_client() -> AsyncOpenAI:
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다. backend/.env 파일을 확인하세요.")

    return AsyncOpenAI(api_key=api_key)


# 이 함수는 AI에게 전달할 시스템 프롬프트를 반환합니다.
# 자유 형식 회의록/업무 메모를 업무 후속 조치 중심 JSON으로 구조화하도록 지시합니다.
def build_system_prompt() -> str:
    return """
당신은 회의록, 업무 메모, 메신저 대화, 문서 텍스트를 분석해 업무 후속 조치 정보를 정리하는 도우미입니다.

입력 텍스트는 정해진 양식이 아닐 수 있습니다.
회의록, 업무 메모, 메신저 대화, 보고서 일부, 표에서 추출한 텍스트가 들어올 수 있습니다.

목표는 단순 요약이 아니라, 실제 업무 후속 조치에 필요한 정보를 구조화하는 것입니다.

반드시 아래 규칙을 지키세요.

1. 원문에 명확히 있는 정보만 사용하세요.
2. 담당자, 마감일, 우선순위가 명확하지 않으면 추측하지 말고 "미정"으로 표시하세요.
3. 각 결정사항, 액션 아이템, 리스크에는 사용자가 검증할 수 있도록 원문 근거 evidence_text를 포함하세요.
4. 출력은 반드시 JSON 형식으로만 반환하세요.
5. JSON 외의 설명 문장, markdown 코드블록, 주석은 출력하지 마세요.
6. action_items가 없으면 빈 배열 []로 반환하세요.
7. risks가 없으면 빈 배열 []로 반환하세요.
8. missing_info에는 담당자/마감일/우선순위 등 업무 진행에 필요한데 불명확한 정보를 적으세요.
9. owner, due_date, priority 필드는 반드시 짧은 값으로 반환하세요.
10. due_date가 명확하지 않으면 설명 문장을 넣지 말고 반드시 "미정"으로 반환하세요.
11. owner가 명확하지 않으면 설명 문장을 넣지 말고 반드시 "미정"으로 반환하세요.
12. priority가 명확하지 않으면 설명 문장을 넣지 말고 반드시 "미정"으로 반환하세요.
13. "마감일도 애매함", "담당자 불명확", "추후 논의" 같은 설명형 문장은 due_date나 owner 필드에 넣지 말고 missing_info에 넣으세요.

반환 JSON 구조는 반드시 아래와 같아야 합니다.

{
  "summary": "전체 내용 요약",
  "decisions": [
    {
      "content": "결정사항",
      "evidence_text": "원문 근거"
    }
  ],
  "action_items": [
    {
      "task": "해야 할 일",
      "owner": "담당자 또는 미정",
      "due_date": "마감일 또는 미정",
      "priority": "높음/보통/낮음/미정",
      "evidence_text": "원문 근거"
    }
  ],
  "risks": [
    {
      "risk": "리스크",
      "response": "대응 방향 또는 미정",
      "evidence_text": "원문 근거"
    }
  ],
  "missing_info": [
    "누락되거나 불명확한 정보"
  ]
}
""".strip()


# 이 함수는 사용자가 입력한 텍스트를 AI 분석용 프롬프트로 감쌉니다.
# 분석 대상 텍스트를 명확히 구분해 LLM이 불필요한 설명을 만들지 않도록 합니다.
def build_user_prompt(text: str) -> str:
    return f"""
아래 텍스트를 분석해 업무 후속 조치 정보를 JSON으로 정리하세요.

[분석 대상 텍스트]
{text}
""".strip()


# 이 함수는 모델이 ```json 코드블록 형태로 응답했을 때 코드블록 문자를 제거합니다.
# JSON 파싱 실패를 줄이기 위한 방어 로직입니다.
def clean_json_text(raw_text: str) -> str:
    text = raw_text.strip()

    if text.startswith("```json"):
        text = text.replace("```json", "", 1).strip()

    if text.startswith("```"):
        text = text.replace("```", "", 1).strip()

    if text.endswith("```"):
        text = text[:-3].strip()

    return text


# 이 함수는 AI 분석 실패 시에도 프론트 화면이 깨지지 않도록 기본 결과를 반환합니다.
# summary에 실패 이유를 넣고 나머지는 빈 배열로 유지합니다.
def build_empty_result(message: str) -> AnalysisResult:
    return AnalysisResult(
        summary=message,
        decisions=[],
        action_items=[],
        risks=[],
        missing_info=[],
    )

# 이 함수는 담당자, 마감일, 우선순위 필드에 설명형 문장이 들어왔을 때 "미정"으로 정규화합니다.
# LLM이 "마감일도 애매함", "담당자 불명확" 같은 표현을 필드 값으로 넣는 경우를 방지합니다.
def normalize_short_field(value: Any) -> str:
    if value is None:
        return "미정"

    text = str(value).strip()

    if not text:
        return "미정"

    unknown_markers = [
        "미정",
        "불명확",
        "애매",
        "정하지",
        "정해지지",
        "없음",
        "추후",
        "미확정",
        "담당자 불명확",
        "마감일도 애매함",
    ]

    if any(marker in text for marker in unknown_markers):
        return "미정"

    if len(text) > 20:
        return "미정"

    return text
    
# 이 함수는 dict 형태의 AI 응답을 AnalysisResult Pydantic 모델로 정규화합니다.
# 일부 필드가 누락되어도 기본값을 채워 API 응답 구조를 안정화합니다.
def normalize_result(data: Dict[str, Any]) -> AnalysisResult:
    decisions = []
    for item in data.get("decisions") or []:
        if isinstance(item, dict):
            decisions.append(
                Decision(
                    content=item.get("content") or "내용 없음",
                    evidence_text=item.get("evidence_text") or "근거 없음",
                )
            )

    action_items = []
    for item in data.get("action_items") or []:
        if isinstance(item, dict):
            action_items.append(
                ActionItem(
                    task=item.get("task") or "작업 없음",
                    owner=normalize_short_field(item.get("owner")),
                    due_date=normalize_short_field(item.get("due_date")),
                    priority=normalize_short_field(item.get("priority")),
                    evidence_text=item.get("evidence_text") or "근거 없음",
                )
            )

    risks = []
    for item in data.get("risks") or []:
        if isinstance(item, dict):
            risks.append(
                Risk(
                    risk=item.get("risk") or "리스크 없음",
                    response=item.get("response") or "미정",
                    evidence_text=item.get("evidence_text") or "근거 없음",
                )
            )

    missing_info = []
    for item in data.get("missing_info") or []:
        missing_info.append(str(item))

    return AnalysisResult(
        summary=data.get("summary") or "요약 정보가 없습니다.",
        decisions=decisions,
        action_items=action_items,
        risks=risks,
        missing_info=missing_info,
    )


# 이 함수는 회의록/업무 메모 텍스트를 OpenAI API로 분석합니다.
# 1차 구현에서는 텍스트 분석만 담당하고, 파일 업로드는 file_parser에서 텍스트를 추출한 뒤 이 함수를 재사용합니다.
async def analyze_text(text: str) -> AnalysisResult:
    if not text or not text.strip():
        return build_empty_result("입력된 텍스트가 없습니다.")

    if len(text.strip()) < 20:
        return build_empty_result("입력 텍스트가 너무 짧아 분석하기 어렵습니다.")

    client = get_openai_client()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    response = await client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": build_user_prompt(text)},
        ],
    )

    raw_content = response.choices[0].message.content or ""
    cleaned_content = clean_json_text(raw_content)

    try:
        parsed = json.loads(cleaned_content)
    except json.JSONDecodeError:
        return build_empty_result(
            "AI 응답을 JSON으로 변환하지 못했습니다. 입력 내용을 조금 더 명확하게 작성해 주세요."
        )

    return normalize_result(parsed)