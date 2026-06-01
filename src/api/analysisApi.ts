// =====================================================================
// src/api/analysisApi.ts
// 역할: ActionNote AI 백엔드 API 호출 함수 모음
// - analyzeText()  : 텍스트 입력 분석 → POST /api/analyze-text
// - analyzeFile()  : 파일 업로드 분석 → POST /api/analyze-file
// - saveGoogleDoc(): Google Docs 저장  → POST /api/save-google-doc
// - App.tsx 에서 이 파일의 함수만 import해서 사용하면 됨
// =====================================================================

import { apiFetch, apiFetchForm } from "./client";
import type {
  AnalysisResult,
  SaveGoogleDocRequest,
  SaveGoogleDocResponse,
} from "../types/analysis";

/**
 * 역할: 텍스트 입력을 백엔드로 전송해 AI 분석 결과를 받아온다.
 * - 매개변수 text: 사용자가 입력한 회의록/업무 메모 원문
 * - 반환값: Promise<AnalysisResult>
 * - 에러 시: ApiError를 throw (App.tsx에서 catch 처리 필요)
 */
export async function analyzeText(text: string): Promise<AnalysisResult> {
  return apiFetch<AnalysisResult>("/api/analyze-text", {
    method: "POST",
    body: JSON.stringify({ text }),
  });
}

/**
 * 역할: 파일을 업로드해 백엔드에서 텍스트를 추출 후 AI 분석 결과를 받아온다.
 * - 매개변수 file: 사용자가 선택한 File 객체 (PDF, DOCX, XLSX, TXT)
 * - 반환값: Promise<AnalysisResult>
 * - 에러 시: ApiError를 throw (App.tsx에서 catch 처리 필요)
 */
export async function analyzeFile(file: File): Promise<AnalysisResult> {
  const formData = new FormData();
  // 백엔드 routers/analyze.py 의 File(...) field name 과 일치해야 함
  formData.append("file", file);
  return apiFetchForm<AnalysisResult>("/api/analyze-file", formData);
}

/**
 * 역할: 분석 결과를 Google Docs에 저장하고 생성된 문서 URL을 반환한다.
 * - 매개변수 title: 저장할 문서 이름 (빈 문자열이면 백엔드에서 자동 생성)
 * - 매개변수 result: 저장할 AnalysisResult
 * - 반환값: Promise<SaveGoogleDocResponse> { title, url }
 * - 에러 시: ApiError를 throw (App.tsx에서 catch 처리 필요)
 */
export async function saveGoogleDoc(
  title: string,
  result: AnalysisResult,
): Promise<SaveGoogleDocResponse> {
  const body: SaveGoogleDocRequest = { title, result };
  return apiFetch<SaveGoogleDocResponse>("/api/save-google-doc", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

/**
 * 역할: 백엔드 서버가 정상 동작 중인지 확인한다.
 * - 반환값: true(서버 정상) / false(서버 미응답)
 * - 앱 시작 시 또는 연결 상태 확인이 필요할 때 사용
 */
export async function checkHealth(): Promise<boolean> {
  try {
    const res = await apiFetch<{ status: string }>("/api/health");
    return res.status === "ok";
  } catch {
    return false;
  }
}
