# =====================================================================
# backend/routers/export.py
# 역할: 분석 결과를 외부 서비스로 내보내는 API 엔드포인트를 정의한다.
# - POST /api/save-google-doc : Google Docs로 저장
# =====================================================================

from fastapi import APIRouter, HTTPException
from schemas.analysis import SaveGoogleDocRequest, SaveGoogleDocResponse
from services.google_docs_service import save_to_google_docs

router = APIRouter()


@router.post("/save-google-doc", response_model=SaveGoogleDocResponse)
async def save_google_doc_endpoint(request: SaveGoogleDocRequest):
    """
    역할: 분석 결과를 Google Docs에 저장하고 생성된 문서 URL을 반환한다.
    - 요청 바디: { "title": "문서명 (빈 문자열이면 자동 생성)", "result": AnalysisResult }
    - 응답: { "title": "실제 문서명", "url": "Google Docs URL" }
    - TODO: google_docs_service 구현 후 실제 동작
    """
    try:
        response = await save_to_google_docs(request.title, request.result)
        return SaveGoogleDocResponse(**response)
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google Docs 저장 중 오류: {e}")
