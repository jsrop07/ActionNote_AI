# backend/services/google_docs_service.py
# 역할:
# - ActionNote AI 분석 결과를 Google Docs 문서로 저장합니다.
# - Google OAuth 인증을 처리합니다.
# - 생성된 문서를 지정한 Google Drive 회의록 폴더로 이동합니다.
# - 문서 이름이 비어 있으면 날짜 기반 기본 이름을 만들고, 중복 시 _1, _2 형식으로 저장합니다.

import os
from datetime import datetime
from pathlib import Path
from typing import Any, List

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from schemas.analysis import AnalysisResult

load_dotenv()


# Google Docs 문서 생성/수정과 Drive 파일 이동에 필요한 권한 범위입니다.
# documents: Google Docs 문서 생성/수정
# drive.file: 이 앱이 만든 Drive 파일 접근 및 폴더 이동
SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive.file",
]


# 이 함수는 Google API 인증 정보를 가져옵니다.
# token.json이 있으면 재사용하고, 없거나 만료되었으면 브라우저 OAuth 인증을 진행합니다.
def get_google_credentials() -> Credentials:
    token_path = Path("token.json")
    credentials_path = Path("credentials.json")

    creds = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    if not creds or not creds.valid:
        if not credentials_path.exists():
            raise FileNotFoundError(
                "credentials.json 파일이 없습니다. backend 폴더에 credentials.json을 넣어주세요."
            )

        flow = InstalledAppFlow.from_client_secrets_file(
            str(credentials_path),
            SCOPES,
        )
        creds = flow.run_local_server(port=0)

        with open(token_path, "w", encoding="utf-8") as token_file:
            token_file.write(creds.to_json())

    return creds


# 이 함수는 사용자가 문서 이름을 입력하지 않았을 때 사용할 기본 문서명을 생성합니다.
# 형식은 YYYY-MM-DD_회의록 입니다.
def build_default_doc_title() -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    return f"{today}_회의록"


# 이 함수는 Google Drive 폴더 안에서 특정 이름과 관련된 기존 파일명을 조회합니다.
# 같은 이름이 있으면 _1, _2를 붙이기 위해 사용합니다.
def find_existing_file_names_in_folder(
    drive_service: Any,
    folder_id: str,
    base_title: str,
) -> List[str]:
    if not folder_id:
        return []

    safe_title = base_title.replace("'", "\\'")

    query = (
        f"'{folder_id}' in parents "
        f"and trashed = false "
        f"and name contains '{safe_title}'"
    )

    response = drive_service.files().list(
        q=query,
        fields="files(id, name)",
        spaces="drive",
    ).execute()

    files = response.get("files", [])
    return [file.get("name", "") for file in files]


# 이 함수는 Google Drive 폴더 안에서 중복되지 않는 문서명을 생성합니다.
# 예: 2026-06-01_회의록, 2026-06-01_회의록_1, 2026-06-01_회의록_2
def build_unique_doc_title(
    drive_service: Any,
    folder_id: str,
    requested_title: str | None = None,
) -> str:
    base_title = (
        requested_title.strip()
        if requested_title and requested_title.strip()
        else build_default_doc_title()
    )

    if not folder_id:
        return base_title

    existing_names = find_existing_file_names_in_folder(
        drive_service=drive_service,
        folder_id=folder_id,
        base_title=base_title,
    )

    if base_title not in existing_names:
        return base_title

    index = 1

    while True:
        candidate_title = f"{base_title}_{index}"

        if candidate_title not in existing_names:
            return candidate_title

        index += 1


# 이 함수는 Google Drive에서 파일의 현재 부모 폴더 ID를 조회합니다.
# 파일을 특정 폴더로 이동할 때 기존 부모 폴더를 제거하기 위해 사용합니다.
def get_current_parent_ids(drive_service: Any, file_id: str) -> str:
    file_info = drive_service.files().get(
        fileId=file_id,
        fields="parents",
    ).execute()

    parents = file_info.get("parents", [])
    return ",".join(parents)


# 이 함수는 생성된 Google Docs 파일을 지정한 Google Drive 폴더로 이동합니다.
# addParents로 새 폴더를 추가하고 removeParents로 기존 위치를 제거합니다.
def move_file_to_folder(drive_service: Any, file_id: str, folder_id: str) -> None:
    if not folder_id:
        return

    previous_parents = get_current_parent_ids(drive_service, file_id)

    drive_service.files().update(
        fileId=file_id,
        addParents=folder_id,
        removeParents=previous_parents,
        fields="id, parents",
    ).execute()


# 이 함수는 분석 결과를 Google Docs에 넣기 좋은 텍스트 보고서로 변환합니다.
# Google Docs API에는 먼저 단순 텍스트로 삽입하고, 형식보다 공유 가능한 내용 구성을 우선합니다.
def build_google_docs_text(result: AnalysisResult) -> str:
    lines = []

    lines.append("ActionNote AI 분석 결과")
    lines.append("=" * 30)
    lines.append("")

    lines.append("[요약]")
    lines.append(result.summary or "요약 정보가 없습니다.")
    lines.append("")

    lines.append("[결정사항]")
    if not result.decisions:
        lines.append("- 결정사항이 없습니다.")
    else:
        for index, item in enumerate(result.decisions, start=1):
            lines.append(f"{index}. {item.content}")
            lines.append(f"   - 원문 근거: {item.evidence_text}")
    lines.append("")

    lines.append("[실행 항목]")
    if not result.action_items:
        lines.append("- 실행 항목이 없습니다.")
    else:
        for index, item in enumerate(result.action_items, start=1):
            lines.append(f"{index}. {item.task}")
            lines.append(f"   - 담당자: {item.owner}")
            lines.append(f"   - 마감일: {item.due_date}")
            lines.append(f"   - 우선순위: {item.priority}")
            lines.append(f"   - 원문 근거: {item.evidence_text}")
    lines.append("")

    lines.append("[리스크]")
    if not result.risks:
        lines.append("- 리스크가 없습니다.")
    else:
        for index, item in enumerate(result.risks, start=1):
            lines.append(f"{index}. {item.risk}")
            lines.append(f"   - 대응 방향: {item.response}")
            lines.append(f"   - 원문 근거: {item.evidence_text}")
    lines.append("")

    lines.append("[누락 정보]")
    if not result.missing_info:
        lines.append("- 누락 정보가 없습니다.")
    else:
        for item in result.missing_info:
            lines.append(f"- {item}")
    lines.append("")

    lines.append("[검증 메모]")
    lines.append("- 담당자, 마감일, 우선순위가 명확하지 않은 항목은 '미정'으로 표시했습니다.")
    lines.append("- 각 항목에는 원문과 비교할 수 있도록 evidence_text를 함께 남겼습니다.")
    lines.append("- 파일 입력은 텍스트로 추출한 뒤 동일한 AI 분석 흐름으로 처리했습니다.")

    return "\n".join(lines)


# 이 함수는 Google Docs 문서를 새로 만들고 분석 결과를 삽입한 뒤,
# 지정한 Google Drive 폴더로 이동합니다.
# 반환값은 실제 저장된 문서명과 문서 URL입니다.
async def save_to_google_docs(
    title: str | None,
    result: AnalysisResult,
) -> dict:
    creds = get_google_credentials()

    docs_service = build("docs", "v1", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)

    target_folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "")

    final_title = build_unique_doc_title(
        drive_service=drive_service,
        folder_id=target_folder_id,
        requested_title=title,
    )

    document = docs_service.documents().create(
        body={
            "title": final_title,
        }
    ).execute()

    document_id = document["documentId"]
    report_text = build_google_docs_text(result)

    docs_service.documents().batchUpdate(
        documentId=document_id,
        body={
            "requests": [
                {
                    "insertText": {
                        "location": {
                            "index": 1,
                        },
                        "text": report_text,
                    }
                }
            ]
        },
    ).execute()

    if target_folder_id:
        move_file_to_folder(
            drive_service=drive_service,
            file_id=document_id,
            folder_id=target_folder_id,
        )

    return {
        "title": final_title,
        "url": f"https://docs.google.com/document/d/{document_id}/edit",
    }