# backend/routers/export.py
# 역할:
# - 분석 결과를 외부 서비스로 저장하는 API 엔드포인트를 정의합니다.
# - 현재는 Google Docs 저장 기능을 제공합니다.

from fastapi import APIRouter
from services.google_docs_service import save_to_google_docs
from schemas.analysis import SaveGoogleDocRequest, SaveGoogleDocResponse

router = APIRouter(tags=["export"])


# 이 함수는 분석 결과를 Google Docs 문서로 저장합니다.
# title이 비어 있으면 서비스 계층에서 날짜 기반 기본 이름을 생성합니다.
@router.post("/save-google-doc", response_model=SaveGoogleDocResponse)
async def save_google_doc_endpoint(
    request: SaveGoogleDocRequest,
) -> SaveGoogleDocResponse:
    saved_doc = await save_to_google_docs(
        title=request.title,
        result=request.result,
    )

    return SaveGoogleDocResponse(
        title=saved_doc["title"],
        url=saved_doc["url"],
    )