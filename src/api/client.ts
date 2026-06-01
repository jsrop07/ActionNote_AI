// =====================================================================
// src/api/client.ts
// 역할: 백엔드 API와 통신하는 기본 fetch 클라이언트
// - baseURL 관리 (개발: http://localhost:8000, 배포: 환경변수로 주입)
// - 공통 에러 처리 및 JSON 파싱을 담당
// - 모든 API 함수(analysisApi.ts)는 이 클라이언트를 통해 요청
// =====================================================================

// Vite 환경변수: .env 에 VITE_API_BASE_URL=http://localhost:8000 설정 가능
// 설정하지 않으면 기본값 사용
const BASE_URL =
  (import.meta as { env?: Record<string, string> }).env?.VITE_API_BASE_URL ??
  "http://localhost:8000";

/**
 * 역할: API 요청 중 발생한 HTTP 에러를 표현하는 커스텀 에러 클래스.
 * - status: HTTP 상태 코드
 * - detail: 백엔드가 반환한 에러 메시지
 */
export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

/**
 * 역할: 공통 fetch 래퍼 — JSON 요청/응답 처리 및 에러를 ApiError로 변환한다.
 * - 매개변수 path: "/api/analyze-text" 같은 경로 (BASE_URL에 붙임)
 * - 매개변수 options: RequestInit (method, body, headers 등)
 * - 반환값: 파싱된 JSON 응답 (제네릭 T)
 * - 에러: HTTP 오류 시 ApiError를 throw
 */
export async function apiFetch<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {}),
    },
    ...options,
  });

  if (!response.ok) {
    // 백엔드 FastAPI 에러 응답은 { "detail": "..." } 형식
    let detail = `HTTP ${response.status}`;
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      // JSON 파싱 실패 시 기본 메시지 유지
    }
    throw new ApiError(response.status, detail);
  }

  return response.json() as Promise<T>;
}

/**
 * 역할: multipart/form-data 파일 업로드 전용 fetch 래퍼.
 * - Content-Type 헤더를 설정하지 않아야 브라우저가 boundary를 자동으로 추가함
 * - 매개변수 path: API 경로
 * - 매개변수 formData: 업로드할 FormData 객체
 * - 반환값: 파싱된 JSON 응답 (제네릭 T)
 */
export async function apiFetchForm<T>(
  path: string,
  formData: FormData,
): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    body: formData,
    // Content-Type 헤더 의도적으로 생략 (브라우저 자동 설정)
  });

  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      // JSON 파싱 실패 시 기본 메시지 유지
    }
    throw new ApiError(response.status, detail);
  }

  return response.json() as Promise<T>;
}
