# backend/routers/analyze.py
# 역할:
# - 텍스트 분석과 파일 분석 API 엔드포인트를 정의합니다.
# - 실제 분석 로직은 services 계층에 위임합니다.

from fastapi import APIRouter, File, UploadFile

from schemas.analysis import AnalyzeTextRequest, AnalysisResult
from services.ai_service import analyze_text
from services.file_parser import parse_uploaded_file

router = APIRouter(tags=["analyze"])

# 이 함수는 사용자가 입력한 텍스트를 분석하는 API입니다.
# React 프론트의 텍스트 입력 탭에서 호출합니다.
@router.post("/analyze-text", response_model=AnalysisResult)
async def analyze_text_endpoint(request: AnalyzeTextRequest) -> AnalysisResult:
    try:
        return await analyze_text(request.text)
    except Exception as exc:
        return AnalysisResult(
            summary=f"분석 중 오류가 발생했습니다: {exc}",
            decisions=[],
            action_items=[],
            risks=[],
            missing_info=[
                "OpenAI API Key, 모델명, .env 설정을 확인해 주세요."
            ],
        )


# 이 함수는 업로드된 파일을 텍스트로 추출한 뒤 분석하는 API입니다.
# 파일 입력도 최종적으로 analyze_text 흐름을 재사용합니다.
@router.post("/analyze-file", response_model=AnalysisResult)
async def analyze_file_endpoint(file: UploadFile = File(...)) -> AnalysisResult:
    try:
        extracted_text = await parse_uploaded_file(file)
        return await analyze_text(extracted_text)

    except Exception as exc:
        return AnalysisResult(
            summary=f"파일 분석 중 오류가 발생했습니다: {exc}",
            decisions=[],
            action_items=[],
            risks=[],
            missing_info=[
                "파일 형식, 텍스트 추출 가능 여부, 파일 내용을 확인해 주세요."
            ],
        )