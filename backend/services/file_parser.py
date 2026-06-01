# =====================================================================
# backend/services/file_parser.py
# 역할: 업로드된 파일에서 텍스트를 추출하는 서비스 레이어
# - 지원 형식: TXT, DOCX, PDF, XLSX
# - 추출된 텍스트는 ai_service.analyze_text()에 전달됨
# =====================================================================

from fastapi import UploadFile


async def extract_text(file: UploadFile) -> str:
    """
    역할: 업로드된 파일 형식을 감지하고 적절한 파서를 호출해 텍스트를 반환한다.
    - 매개변수 file: FastAPI UploadFile 객체
    - 반환값: 파일에서 추출된 순수 텍스트 문자열
    - 지원: .txt / .docx / .pdf / .xlsx
    """
    filename = file.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext == "txt":
        return await _parse_txt(file)
    elif ext == "docx":
        return await _parse_docx(file)
    elif ext == "pdf":
        return await _parse_pdf(file)
    elif ext == "xlsx":
        return await _parse_xlsx(file)
    else:
        raise ValueError(f"지원하지 않는 파일 형식입니다: .{ext}")


async def _parse_txt(file: UploadFile) -> str:
    """
    역할: .txt 파일에서 텍스트를 읽어 반환한다.
    - UTF-8 인코딩 우선 시도, 실패 시 CP949(한국어 Windows 인코딩) 시도
    """
    content = await file.read()
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return content.decode("cp949", errors="ignore")


async def _parse_docx(file: UploadFile) -> str:
    """
    역할: .docx 파일에서 단락 텍스트를 추출해 반환한다.
    - TODO: python-docx 라이브러리 설치 후 구현
    - requirements.txt 에서 python-docx 주석 해제 필요
    """
    # TODO: python-docx 로 구현
    # import io
    # from docx import Document
    # content = await file.read()
    # doc = Document(io.BytesIO(content))
    # return "\n".join(para.text for para in doc.paragraphs if para.text.strip())
    raise NotImplementedError("DOCX 파싱은 아직 구현되지 않았습니다. TODO를 참고하세요.")


async def _parse_pdf(file: UploadFile) -> str:
    """
    역할: .pdf 파일에서 페이지별 텍스트를 추출해 반환한다.
    - TODO: PyPDF2 또는 pdfminer 라이브러리 설치 후 구현
    - 표가 포함된 PDF는 순서가 섞일 수 있으므로 사용자 검토 필요
    """
    # TODO: PyPDF2 로 구현
    # import io
    # from PyPDF2 import PdfReader
    # content = await file.read()
    # reader = PdfReader(io.BytesIO(content))
    # return "\n".join(page.extract_text() or "" for page in reader.pages)
    raise NotImplementedError("PDF 파싱은 아직 구현되지 않았습니다. TODO를 참고하세요.")


async def _parse_xlsx(file: UploadFile) -> str:
    """
    역할: .xlsx 파일의 각 시트를 읽어 셀 값을 텍스트로 변환해 반환한다.
    - TODO: openpyxl 라이브러리 설치 후 구현
    - 각 행을 탭으로 구분된 텍스트로 변환
    """
    # TODO: openpyxl 로 구현
    # import io
    # import openpyxl
    # content = await file.read()
    # wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True)
    # lines = []
    # for ws in wb.worksheets:
    #     for row in ws.iter_rows(values_only=True):
    #         lines.append("\t".join(str(c) for c in row if c is not None))
    # return "\n".join(lines)
    raise NotImplementedError("XLSX 파싱은 아직 구현되지 않았습니다. TODO를 참고하세요.")
