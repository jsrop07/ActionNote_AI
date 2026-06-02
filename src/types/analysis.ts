// =====================================================================
// src/types/analysis.ts
// 역할: 백엔드 API 응답과 프론트엔드 컴포넌트 사이에서 공유하는 타입 정의
// - backend/schemas/analysis.py 의 Pydantic 모델과 구조가 일치해야 함
// - 미정 판단이 필요한 경우 isUnspecified() 유틸 함수 사용
// =====================================================================

// ── 결정사항 ─────────────────────────────────────────────────────────
export interface Decision {
  content: string;        // 결정 내용
  evidence_text: string;  // 원문 근거
}

// ── 실행 항목 ───────────────────────────────────────────────────────
export interface ActionItem {
  task: string;               // 해야 할 일
  owner: string | null;       // 담당자 (null 이면 미정)
  due_date: string | null;    // 마감일 (null 이면 미정)
  priority: string | null;    // 우선순위: "높음" | "보통" | "낮음" | null
  evidence_text: string;      // 원문 근거
}

// ── 리스크 ────────────────────────────────────────────────────────────
export interface Risk {
  risk: string;               // 리스크 내용
  response: string | null;    // 대응 방향 (null 이면 미정)
  evidence_text: string;      // 원문 근거
}

// ── 분석 결과 전체 ────────────────────────────────────────────────────
export interface AnalysisResult {
  summary: string;
  decisions: Decision[];
  action_items: ActionItem[];
  risks: Risk[];
  missing_info: string[];
}

// ── 저장 API 요청/응답 ───────────────────────────────────────────────
export interface SaveGoogleDocRequest {
  title: string;           // 빈 문자열이면 백엔드에서 자동 생성
  result: AnalysisResult;
}

export interface SaveGoogleDocResponse {
  title: string;           // 실제로 저장된 문서명
  url: string;             // Google Docs URL
}

// ── 미정 판단 유틸 ────────────────────────────────────────────────────
/**
 * 역할: 값이 "미정"으로 간주되는지 판단한다.
 * - null, undefined, 빈 문자열, 또는 아래 키워드는 모두 미정으로 처리
 * - UI에서 담당자/마감일 등을 '미정' 뱃지로 표시할 때 사용
 */
const UNSPECIFIED_VALUES = new Set([
  "미정",
  "",
  "추후 결정",
  "미확정",
  "불명확",
  "없음",
]);

export function isUnspecified(value: string | null | undefined): boolean {
  if (value === null || value === undefined) return true;
  return UNSPECIFIED_VALUES.has(value.trim());
}

// ── 메트릭 계산 유틸 ─────────────────────────────────────────────────
/**
 * 역할: 분석 결과에서 대시보드용 통계 수치를 계산한다.
 * - App.tsx 의 Stats Cards 섹션에서 사용
 */
export interface AnalysisMetrics {
  totalActionItems: number;   // 실행 항목 수
  unassignedCount: number;    // 담당자 미정 수
  noDueDateCount: number;     // 마감일 미정 수
  riskCount: number;          // 리스크 수
}

export function calcMetrics(result: AnalysisResult): AnalysisMetrics {
  return {
    totalActionItems: result.action_items.length,
    unassignedCount: result.action_items.filter((a) => isUnspecified(a.owner)).length,
    noDueDateCount: result.action_items.filter((a) => isUnspecified(a.due_date)).length,
    riskCount: result.risks.length,
  };
}
