# =====================================================================
# backend/services/google_docs_service.py
# 역할: Google Docs API를 통해 분석 결과를 문서로 저장하는 서비스
# - credentials.json 은 Google Cloud Console에서 다운로드 필요
# =====================================================================

import os
from datetime import datetime
from schemas.analysis import AnalysisResult

GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
GOOGLE_TOKEN_PATH = os.getenv("GOOGLE_TOKEN_PATH", "token.json")


def _resolve_doc_title(title: str) -> str:
    """
    역할: 문서 이름을 결정한다.
    - 빈 문자열이면 오늘 날짜 기반으로 자동 생성 (YYYY-MM-DD_회의록)
    - 이미 같은 이름이 있으면 _1, _2 ... 를 붙임 (TODO: 중복 체크 구현)
    """
    if not title.strip():
        today = datetime.now().strftime("%Y-%m-%d")
        return f"{today}_회의록"
    return title.strip()


def _result_to_markdown(title: str, result: AnalysisResult) -> str:
    """
    역할: AnalysisResult를 Google Docs에 쓸 마크다운 형식 텍스트로 변환한다.
    - Google Docs API의 batchUpdate 요청 전에 텍스트를 준비하는 단계
    """
    lines = [f"# {title}\n"]

    lines.append("## 요약\n")
    lines.append(result.summary + "\n")

    lines.append("\n## 결정사항\n")
    for d in result.decisions:
        lines.append(f"- {d.content}")
        lines.append(f"  > 근거: {d.evidence_text}\n")

    lines.append("\n## 액션 아이템\n")
    for a in result.action_items:
        owner = a.owner or "미정"
        due = a.due_date or "미정"
        priority = a.priority or "미정"
        lines.append(f"- [{priority}] {a.task} — 담당: {owner} / 마감: {due}")
        lines.append(f"  > 근거: {a.evidence_text}\n")

    lines.append("\n## 리스크\n")
    for r in result.risks:
        response = r.response or "미정"
        lines.append(f"- {r.risk} → 대응: {response}")
        lines.append(f"  > 근거: {r.evidence_text}\n")

    lines.append("\n## 누락 정보\n")
    for m in result.missing_info:
        lines.append(f"- {m}")

    return "\n".join(lines)


async def save_to_google_docs(title: str, result: AnalysisResult) -> dict:
    """
    역할: 분석 결과를 Google Docs에 새 문서로 저장하고 URL을 반환한다.
    - 매개변수 title: 저장할 문서 이름 (빈 문자열이면 자동 생성)
    - 매개변수 result: 저장할 AnalysisResult
    - 반환값: { "title": 실제_문서명, "url": Google_Docs_URL }
    - TODO: 실제 Google Docs API 연동 구현
    """
    resolved_title = _resolve_doc_title(title)
    content_text = _result_to_markdown(resolved_title, result)

    # TODO: Google Docs API 연동 구현
    # 1. credentials.json으로 OAuth 인증 (google-auth-oauthlib)
    # 2. Docs API로 빈 문서 생성 (documents.create)
    # 3. batchUpdate로 텍스트/서식 삽입
    # 예시:
    # from googleapiclient.discovery import build
    # from google.oauth2.credentials import Credentials
    # from google_auth_oauthlib.flow import InstalledAppFlow
    #
    # SCOPES = ["https://www.googleapis.com/auth/documents"]
    # creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN_PATH, SCOPES)
    # service = build("docs", "v1", credentials=creds)
    # doc = service.documents().create(body={"title": resolved_title}).execute()
    # doc_id = doc["documentId"]
    # doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
    # ... batchUpdate 로 content_text 삽입 ...
    # return {"title": resolved_title, "url": doc_url}

    # ── 임시 더미 반환값 ────────────────────────────────────────────
    dummy_doc_id = "TODO_REAL_DOC_ID"
    return {
        "title": resolved_title,
        "url": f"https://docs.google.com/document/d/{dummy_doc_id}/edit",
    }
