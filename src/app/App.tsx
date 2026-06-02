// =====================================================================
// src/app/App.tsx
// 역할: ActionNote AI 메인 화면 컴포넌트
// - 입력 섹션 (텍스트 입력 / 파일 업로드)
// - 분석 결과 섹션 (요약, 통계, 결정사항, 실행 항목, 리스크, 누락 정보)
// - 저장 섹션 (Google Docs 저장)
//   API 연결 상태 관리 틀만 추가함
// =====================================================================

import { useRef, useState } from 'react';
import {
  FileText, Upload, AlertCircle, CheckCircle2,
  Clock, Users, ArrowRight, Download, FileDown,
  Target, TrendingUp, Shield, Info
} from 'lucide-react';
import type { AnalysisResult } from '../types/analysis';
import { calcMetrics, isUnspecified } from '../types/analysis';
import { analyzeText, analyzeFile, saveGoogleDoc } from '../api/analysisApi';
import type { ApiError } from '../api/client';

export default function App() {
  // ── 탭 상태 (기존 유지) ──────────────────────────────────────────
  const [activeInputTab, setActiveInputTab] = useState<'text' | 'file'>('text');
  const [activeResultTab, setActiveResultTab] = useState<'decisions' | 'actions' | 'risks' | 'missing'>('actions');

  // ── 입력 상태 ────────────────────────────────────────────────────
  const [inputText, setInputText] = useState<string>('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragActive, setIsDragActive] = useState<boolean>(false);

  // ── API 연동 상태 ─────────────────────────────────────────────────
  /** 분석 결과 (null이면 아직 분석 전 → mock 데이터 fallback 표시) */
  const [result, setResult] = useState<AnalysisResult | null>(null);
  /** 분석 요청 중 로딩 여부 */
  const [isLoading, setIsLoading] = useState<boolean>(false);
  /** 분석 또는 저장 중 에러 메시지 (null이면 에러 없음) */
  const [error, setError] = useState<string | null>(null);

  // ── 저장 상태 ────────────────────────────────────────────────────
  /** Google Docs 저장 시 사용할 문서 이름 */
  const [docTitle, setDocTitle] = useState<string>('');
  /** 저장 완료된 Google Docs URL (null이면 아직 저장 안 함) */
  const [savedDocUrl, setSavedDocUrl] = useState<string | null>(null);

  // ── 메트릭 계산 ─────────────────────────────────────────────────
  /**
   * 역할: 현재 result 또는 mock 데이터 기준으로 대시보드 통계를 계산한다.
   * - result가 있으면 실제 API 응답 기준으로 계산
   * - result가 없으면 mock 데이터 기준 고정값 반환 (UI 미리보기용)
   */
  const metrics = result
    ? calcMetrics(result)
    : { totalActionItems: 0, unassignedCount: 0, noDueDateCount: 0, riskCount: 0 };

  function isSupportedFile(file: File) {
    const fileName = file.name.toLowerCase();
    return (
      fileName.endsWith('.txt') ||
      fileName.endsWith('.docx') ||
      fileName.endsWith('.pdf') ||
      fileName.endsWith('.xlsx')
    );
  }

  function selectFile(file: File) {
    if (!isSupportedFile(file)) {
      setError('지원하지 않는 파일 형식입니다. TXT, DOCX, PDF, XLSX 파일만 업로드해 주세요.');
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
    setError(null);
    setSavedDocUrl(null);
    setDocTitle('');
  }

  function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    selectFile(file);
  }

  function handleDragOver(event: React.DragEvent<HTMLDivElement>) {
    event.preventDefault();
    event.stopPropagation();
    setIsDragActive(true);
  }

  function handleDragLeave(event: React.DragEvent<HTMLDivElement>) {
    event.preventDefault();
    event.stopPropagation();
    setIsDragActive(false);
  }

  function handleDrop(event: React.DragEvent<HTMLDivElement>) {
    event.preventDefault();
    event.stopPropagation();
    setIsDragActive(false);

    const file = event.dataTransfer.files?.[0];

    if (!file) {
      return;
    }

    selectFile(file);
  }
  // ── 분석 핸들러 ──────────────────────────────────────────────────
  /**
   * 역할: "분석하기" 버튼 클릭 시 호출된다.
   * - 현재 활성 탭(텍스트/파일)에 따라 analyzeText 또는 analyzeFile을 호출
   */
  async function handleAnalyze() {
    setError(null);
    setIsLoading(true);

    try {
      let data: AnalysisResult;

      setSavedDocUrl(null);
      setDocTitle('');
      setActiveResultTab('actions');

      if (activeInputTab === 'text') {
        if (!inputText.trim()) {
          setError('분석할 텍스트를 입력해 주세요.');
          return;
        }

        // 새 텍스트 분석을 시작하면 이전 Google Docs 저장 결과를 초기화합니다.
        setSavedDocUrl(null);
        setDocTitle('');
        setActiveResultTab('actions');

        data = await analyzeText(inputText);
      } else {
        if (!selectedFile) {
          setError('분석할 파일을 선택해 주세요.');
          return;
        }

        // 새 파일 분석을 시작하면 이전 Google Docs 저장 결과를 초기화합니다.
        setSavedDocUrl(null);
        setDocTitle('');
        setActiveResultTab('actions');

        data = await analyzeFile(selectedFile);
      }

      setResult(data);
    } catch (err) {
      const apiErr = err as ApiError;
      setError(apiErr.detail ?? '분석 중 오류가 발생했습니다. 백엔드 서버가 실행 중인지 확인해 주세요.');
    } finally {
      setIsLoading(false);
    }
  }

  // ── Google Docs 저장 핸들러 ───────────────────────────────────────
  /**
   * 역할: "Google Docs로 저장" 버튼 클릭 시 호출된다.
   * - result가 없으면 저장 불가 안내 표시
   * - TODO: 실제 API 연결 후 savedDocUrl에 반환된 URL 저장
   */
  async function handleSaveGoogleDoc() {
    if (!result) {
      setError('먼저 회의록을 분석해 주세요.');
      return;
    }
    setError(null);
    setIsLoading(true);
    try {
      // TODO: 백엔드 Google Docs 서비스 구현 후 아래 주석 해제
      const res = await saveGoogleDoc(docTitle, result);
      setSavedDocUrl(res.url);
    } catch (err) {
      const apiErr = err as ApiError;
      setError(apiErr.detail ?? 'Google Docs 저장 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  }

  // ── 표시용 데이터 (result가 없으면 mock 데이터 fallback) ──────────
  /**
   * 역할: 화면에 표시할 실제 데이터를 결정한다.
   * - API 연결 전에도 UI를 미리볼 수 있도록 mock 데이터를 fallback으로 사용
   * - API 연결 후 result에 실제 응답이 담기면 자동으로 교체됨
   */
  const displayData: AnalysisResult = result ?? {
    summary: '',
    decisions: [],
    action_items: [],
    risks: [],
    missing_info: [],
  };


  return (
    <div className="min-h-screen bg-[#fafafa]">
      <div className="max-w-[1440px] mx-auto p-8">
        {/* Hero Section */}
        <div className="mb-12">
          <div className="flex items-start justify-between gap-8">
            <div className="flex-1">
              <h1 className="mb-3">ActionNote AI</h1>
              <p className="text-lg text-muted-foreground mb-2">
                자유 형식 회의록과 문서 파일을 AI로 분석해 업무 후속 조치를 자동 정리합니다.
              </p>
              <p className="text-sm text-muted-foreground">
                요약, 결정사항, 실행 항목, 리스크, 누락 정보를 구조화하고 Google Docs로 저장할 수 있습니다.
              </p>
            </div>

            {/* Process Flow Cards */}
            <div className="flex items-center gap-3 bg-white rounded-lg p-4 shadow-sm border border-border">
              <div className="flex flex-col items-center gap-1">
                <div className="w-12 h-12 rounded-lg bg-primary/5 flex items-center justify-center">
                  <FileText className="w-6 h-6 text-primary" />
                </div>
                <span className="text-xs text-muted-foreground">입력</span>
              </div>
              <ArrowRight className="w-4 h-4 text-muted-foreground" />
              <div className="flex flex-col items-center gap-1">
                <div className="w-12 h-12 rounded-lg bg-primary/5 flex items-center justify-center">
                  <TrendingUp className="w-6 h-6 text-primary" />
                </div>
                <span className="text-xs text-muted-foreground">AI 분석</span>
              </div>
              <ArrowRight className="w-4 h-4 text-muted-foreground" />
              <div className="flex flex-col items-center gap-1">
                <div className="w-12 h-12 rounded-lg bg-primary/5 flex items-center justify-center">
                  <CheckCircle2 className="w-6 h-6 text-primary" />
                </div>
                <span className="text-xs text-muted-foreground">검증</span>
              </div>
              <ArrowRight className="w-4 h-4 text-muted-foreground" />
              <div className="flex flex-col items-center gap-1">
                <div className="w-12 h-12 rounded-lg bg-primary/5 flex items-center justify-center">
                  <Download className="w-6 h-6 text-primary" />
                </div>
                <span className="text-xs text-muted-foreground">문서 저장</span>
              </div>
            </div>
          </div>
        </div>

        {/* Main Input Section */}
        <div className="mb-8">
          <div className="bg-white rounded-xl shadow-sm border border-border p-6">
            <h3 className="mb-4">입력</h3>

            {/* Tabs */}
            <div className="flex gap-2 mb-4 border-b border-border">
              <button
                onClick={() => setActiveInputTab('text')}
                className={`px-4 py-2 border-b-2 transition-colors ${activeInputTab === 'text'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
                  }`}
              >
                텍스트 입력
              </button>
              <button
                onClick={() => setActiveInputTab('file')}
                className={`px-4 py-2 border-b-2 transition-colors ${activeInputTab === 'file'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
                  }`}
              >
                파일 업로드
              </button>
            </div>

            {/* Tab Content */}
            {activeInputTab === 'text' ? (
              <div>
                {/* 텍스트 입력 → inputText 상태에 바인딩 */}
                <textarea
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  placeholder="회의록이나 업무 메모를 입력하세요..."
                  className="w-full h-48 p-4 rounded-lg bg-input-background border border-border resize-none focus:outline-none focus:ring-2 focus:ring-primary/20"
                />
              </div>
            ) : (
              <div
                onDragEnter={handleDragOver}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${isDragActive
                  ? 'border-primary bg-primary/5'
                  : 'border-border bg-muted/30'
                  }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".txt,.docx,.pdf,.xlsx"
                  className="hidden"
                  onChange={handleFileChange}
                />

                <Upload className="w-12 h-12 text-muted-foreground mx-auto mb-4" />

                <p className="text-foreground mb-2">
                  {isDragActive ? '여기에 파일을 놓아주세요' : '파일을 드래그하여 업로드'}
                </p>

                <p className="text-sm text-muted-foreground mb-4">
                  PDF, DOCX, XLSX, TXT 지원
                </p>

                {selectedFile && (
                  <p className="text-sm text-primary mb-2">
                    선택됨: {selectedFile.name}
                  </p>
                )}

                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="px-6 py-2 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 transition-colors"
                >
                  파일 선택
                </button>
              </div>
            )}

            {/* 에러 메시지 표시 영역 */}
            {error && (
              <div className="mt-4 p-3 rounded-lg bg-red-50 border border-red-200 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            {/* 분석 버튼 → handleAnalyze 연결, 로딩 중 비활성화 */}
            <button
              onClick={handleAnalyze}
              disabled={isLoading}
              className="mt-6 w-full py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? '분석 중...' : '분석하기'}
            </button>
          </div>
        </div>

        {/* result가 있을 때만 결과 표시 */}
        {result ? (
          <>
            <div className="relative">
              {isLoading && result && (
                <div className="absolute inset-0 z-20 flex items-center justify-center rounded-xl bg-white/70 backdrop-blur-[1px]">
                  <div className="rounded-lg border border-border bg-white px-5 py-3 shadow-sm text-sm">
                    작업을 진행 중입니다. 잠시만 기다려 주세요.
                  </div>
                </div>
              )}

              <div className={isLoading && result ? 'pointer-events-none select-none opacity-60' : ''}></div>
              {/* Analysis Results Section */}
              <div className="mb-8">
                {/* 요약 카드 — displayData.summary 표시 */}
                <div className="bg-white rounded-xl shadow-sm border border-border p-6 mb-4">
                  <h3 className="mb-3 flex items-center gap-2">
                    <FileText className="w-5 h-5" />
                    요약
                  </h3>
                  <p className="text-muted-foreground leading-relaxed">
                    {displayData.summary}
                  </p>
                </div>

                {/* 통계 카드 — metrics 변수에서 계산 */}
                <div className="grid grid-cols-4 gap-4 mb-8">
                  <div className="bg-white rounded-xl shadow-sm border border-border p-6">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-muted-foreground">실행 항목 수</span>
                      <Target className="w-4 h-4 text-primary" />
                    </div>
                    <div className="text-3xl mb-1">{metrics.totalActionItems}</div>
                    <p className="text-xs text-muted-foreground">총 실행 항목</p>
                  </div>

                  <div className="bg-white rounded-xl shadow-sm border border-border p-6">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-muted-foreground">담당자 미정</span>
                      <Users className="w-4 h-4 text-orange-500" />
                    </div>
                    <div className="text-3xl text-orange-500 mb-1">{metrics.unassignedCount}</div>
                    <p className="text-xs text-muted-foreground">할당 필요</p>
                  </div>

                  <div className="bg-white rounded-xl shadow-sm border border-border p-6">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-muted-foreground">마감일 미정</span>
                      <Clock className="w-4 h-4 text-amber-500" />
                    </div>
                    <div className="text-3xl text-amber-500 mb-1">{metrics.noDueDateCount}</div>
                    <p className="text-xs text-muted-foreground">일정 설정 필요</p>
                  </div>

                  <div className="bg-white rounded-xl shadow-sm border border-border p-6">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-muted-foreground">리스크 수</span>
                      <Shield className="w-4 h-4 text-red-500" />
                    </div>
                    <div className="text-3xl text-red-500 mb-1">{metrics.riskCount}</div>
                    <p className="text-xs text-muted-foreground">주의 필요</p>
                  </div>
                </div>
              </div>

              {/* Detailed Results Section */}
              <div className="bg-white rounded-xl shadow-sm border border-border p-6 mb-8">
                <h3 className="mb-4">상세 결과</h3>

                {/* Result Tabs */}
                <div className="flex gap-2 mb-6 border-b border-border">
                  <button
                    onClick={() => setActiveResultTab('decisions')}
                    className={`px-4 py-2 border-b-2 transition-colors ${activeResultTab === 'decisions'
                      ? 'border-primary text-primary'
                      : 'border-transparent text-muted-foreground hover:text-foreground'
                      }`}
                  >
                    결정사항
                  </button>
                  <button
                    onClick={() => setActiveResultTab('actions')}
                    className={`px-4 py-2 border-b-2 transition-colors ${activeResultTab === 'actions'
                      ? 'border-primary text-primary'
                      : 'border-transparent text-muted-foreground hover:text-foreground'
                      }`}
                  >
                    실행 항목
                  </button>
                  <button
                    onClick={() => setActiveResultTab('risks')}
                    className={`px-4 py-2 border-b-2 transition-colors ${activeResultTab === 'risks'
                      ? 'border-primary text-primary'
                      : 'border-transparent text-muted-foreground hover:text-foreground'
                      }`}
                  >
                    리스크
                  </button>
                  <button
                    onClick={() => setActiveResultTab('missing')}
                    className={`px-4 py-2 border-b-2 transition-colors ${activeResultTab === 'missing'
                      ? 'border-primary text-primary'
                      : 'border-transparent text-muted-foreground hover:text-foreground'
                      }`}
                  >
                    누락 정보
                  </button>
                </div>

                {/* 실행 항목 탭 — displayData.action_items 동적 렌더링 */}
                {activeResultTab === 'actions' && (
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-border">
                          <th className="text-left py-3 px-4 text-sm text-muted-foreground">할 일</th>
                          <th className="text-left py-3 px-4 text-sm text-muted-foreground">담당자</th>
                          <th className="text-left py-3 px-4 text-sm text-muted-foreground">마감일</th>
                          <th className="text-left py-3 px-4 text-sm text-muted-foreground">우선순위</th>
                          <th className="text-left py-3 px-4 text-sm text-muted-foreground">원문 근거</th>
                        </tr>
                      </thead>
                      <tbody>
                        {displayData.action_items.map((item, idx) => (
                          <tr key={idx} className="border-b border-border hover:bg-muted/30 transition-colors">
                            <td className="py-4 px-4">{item.task}</td>
                            <td className="py-4 px-4">
                              {isUnspecified(item.owner)
                                ? <span className="text-orange-500">미정</span>
                                : item.owner}
                            </td>
                            <td className="py-4 px-4">
                              {isUnspecified(item.due_date)
                                ? <span className="text-amber-500">미정</span>
                                : item.due_date}
                            </td>
                            <td className="py-4 px-4">
                              {item.priority === '높음' && <span className="px-2 py-1 rounded bg-red-100 text-red-700 text-xs">높음</span>}
                              {item.priority === '보통' && <span className="px-2 py-1 rounded bg-amber-100 text-amber-700 text-xs">보통</span>}
                              {item.priority === '낮음' && <span className="px-2 py-1 rounded bg-blue-100 text-blue-700 text-xs">낮음</span>}
                              {isUnspecified(item.priority) && <span className="text-muted-foreground text-xs">미정</span>}
                            </td>
                            <td className="py-4 px-4 text-sm text-muted-foreground max-w-xs truncate">
                              "{item.evidence_text}"
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* 결정사항 탭 — displayData.decisions 동적 렌더링 */}
                {activeResultTab === 'decisions' && (
                  <div className="space-y-4">
                    {displayData.decisions.map((d, idx) => (
                      <div key={idx} className="p-4 rounded-lg bg-muted/30 border border-border">
                        <div className="flex items-start gap-3">
                          <CheckCircle2 className="w-5 h-5 text-primary mt-0.5" />
                          <div>
                            <p className="mb-2">{d.content}</p>
                            <p className="text-sm text-muted-foreground">근거: "{d.evidence_text}"</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* 리스크 탭 — displayData.risks 동적 렌더링 */}
                {activeResultTab === 'risks' && (
                  <div className="space-y-4">
                    {displayData.risks.map((r, idx) => (
                      <div key={idx} className="p-4 rounded-lg bg-red-50 border border-red-200">
                        <div className="flex items-start gap-3">
                          <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
                          <div>
                            <p className="mb-2">{r.risk}</p>
                            {!isUnspecified(r.response) && (
                              <p className="text-sm text-muted-foreground mb-1">대응: {r.response}</p>
                            )}
                            <p className="text-sm text-muted-foreground">근거: "{r.evidence_text}"</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* 누락 정보 탭 — displayData.missing_info 동적 렌더링 */}
                {activeResultTab === 'missing' && (
                  <div className="space-y-4">
                    {displayData.missing_info.map((m, idx) => (
                      <div key={idx} className="p-4 rounded-lg bg-amber-50 border border-amber-200">
                        <div className="flex items-start gap-3">
                          <Info className="w-5 h-5 text-amber-600 mt-0.5" />
                          <div>
                            <p className="mb-2">{m}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* 저장 섹션 — docTitle 상태 바인딩, 저장 핸들러 연결 */}
              <div className="bg-white rounded-xl shadow-sm border border-border p-6 mb-8">
                <h3 className="mb-4">저장</h3>

                <div className="mb-4">
                  <label className="block mb-2 text-sm">Google Docs 문서 이름</label>
                  {/* docTitle 상태에 바인딩 */}
                  <input
                    type="text"
                    value={docTitle}
                    onChange={(e) => setDocTitle(e.target.value)}
                    placeholder="비워두면 자동 생성됩니다 (YYYY-MM-DD_회의록)"
                    className="w-full p-3 rounded-lg bg-input-background border border-border focus:outline-none focus:ring-2 focus:ring-primary/20"
                  />
                  <p className="mt-2 text-xs text-muted-foreground">
                    이름을 비워두면 "YYYY-MM-DD_회의록", "YYYY-MM-DD_회의록_1" 형식으로 자동 저장됩니다
                  </p>
                </div>

                {/* 저장 완료 시 URL 표시 */}
                {savedDocUrl && (
                  <div className="mb-4 p-3 rounded-lg bg-green-50 border border-green-200">
                    <p className="text-sm text-green-700">
                      저장 완료!{' '}
                      <a href={savedDocUrl} target="_blank" rel="noopener noreferrer" className="underline">
                        문서 열기
                      </a>
                    </p>
                  </div>
                )}

                <div className="flex gap-3">
                  {/* Google Docs 저장 버튼 → handleSaveGoogleDoc 연결 */}
                  <button
                    onClick={handleSaveGoogleDoc}
                    disabled={isLoading}
                    className="flex-1 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Download className="w-4 h-4" />
                    {isLoading ? '저장 중...' : 'Google Docs로 저장'}
                  </button>
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="bg-white rounded-xl shadow-sm border border-border p-8 mb-8 text-center">
            <FileText className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="mb-2">아직 분석 결과가 없습니다</h3>
            <p className="text-sm text-muted-foreground">
              회의록 텍스트를 입력하거나 문서 파일을 업로드한 뒤 분석하기 버튼을 눌러주세요.
            </p>
          </div>

        )}

        {/* Validation Points */}
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
          <h4 className="mb-3 flex items-center gap-2">
            <Info className="w-5 h-5 text-blue-600" />
            검증 포인트
          </h4>
          <ul className="space-y-2 text-sm text-foreground/80">
            <li className="flex items-start gap-2">
              <span className="text-blue-600 mt-1">•</span>
              <span>AI가 원문에 없는 담당자나 마감일을 추측하지 않도록 미정 처리합니다</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600 mt-1">•</span>
              <span>각 결과에 원문 근거(evidence_text)를 표시하여 검증 가능하도록 합니다</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600 mt-1">•</span>
              <span>파일 입력은 텍스트로 추출한 뒤 동일한 분석 흐름으로 처리됩니다</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600 mt-1">•</span>
              <span>PDF 표 추출은 일부 순서가 섞일 수 있어 사용자 검토가 필요합니다</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}