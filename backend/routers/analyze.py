# =====================================================================
# backend/routers/analyze.py
# 역할: 텍스트/파일 분석 API 엔드포인트를 정의한다.
# - POST /api/analyze-text : 텍스트 직접 입력 분석
# - POST /api/analyze-file : 파일 업로드 분석
# =====================================================================

from fastapi import APIRouter, HTTPException, UploadFile, File
from schemas.analysis import AnalysisResult, AnalyzeTextRequest
from services.ai_service import analyze_text
from services.file_parser import extract_text

router = APIRouter()

# 허용 파일 형식
ALLOWED_EXTENSIONS = {"txt", "docx", "pdf", "xlsx"}


@router.post("/analyze-text", response_model=AnalysisResult)
async def analyze_text_endpoint(request: AnalyzeTextRequest):
    """
    역할: 텍스트를 받아 AI 분석 결과를 반환한다.
    - 요청 바디: { "text": "회의록 원문" }
    - 응답: AnalysisResult (summary, decisions, action_items, risks, missing_info)
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="분석할 텍스트를 입력해 주세요.")

    result = await analyze_text(request.text)
    return result


@router.post("/analyze-file", response_model=AnalysisResult)
async def analyze_file_endpoint(file: UploadFile = File(...)):
    """
    역할: 업로드된 파일에서 텍스트를 추출한 뒤 AI 분석 결과를 반환한다.
    - 요청: multipart/form-data, field name = "file"
    - 지원 형식: .txt / .docx / .pdf / .xlsx
    - 응답: AnalysisResult
    """
    # 파일 형식 검증
    filename = file.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 파일 형식입니다. 허용: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # 텍스트 추출
    try:
        text = await extract_text(file)
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 파싱 중 오류: {e}")

    if not text.strip():
        raise HTTPException(status_code=400, detail="파일에서 텍스트를 추출할 수 없습니다.")

    result = await analyze_text(text)
    return result
