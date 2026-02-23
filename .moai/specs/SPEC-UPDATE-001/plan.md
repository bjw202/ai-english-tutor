---
spec_id: SPEC-UPDATE-001
title: Korean Tutoring Prompt Redesign - Implementation Plan
version: 1.0.0
created: 2026-02-22
updated: 2026-02-22
author: jw
tags: TAG-SUP-01, TAG-PROMPT-01, TAG-SCHEMA-01, TAG-MODEL-01, TAG-FRONT-01, TAG-LEVEL-01
---

# Implementation Plan: SPEC-UPDATE-001

## 1. Overview

AI English Tutor를 영어 분석 중심에서 한국어 교육 중심으로 전환하는 대규모 업데이트.
총 22개 프로덕션 파일 변경, 6개 요구사항 구현.

---

## 2. Milestone Breakdown

### Milestone 1: Foundation (Priority: High)

**목표**: 스키마와 상태 정의 재설계 - 모든 후속 변경의 기반

**관련 TAG**: TAG-SCHEMA-01

**Task 목록**:

- [M1-T1] `schemas.py` 재작성
  - `SentenceEntry` Pydantic 모델 추가 (`text: str`, `difficulty: int`, `focus: list[str]`)
  - `SupervisorAnalysis` Pydantic 모델 추가 (`sentences: list[SentenceEntry]`, `overall_difficulty: int`, `focus_summary: list[str]`)
  - `VocabularyWordEntry` Pydantic 모델 추가 (`word: str`, `content: str`)
  - `ReadingResult` 변경: 기존 필드 제거, `content: str` 단일 필드
  - `GrammarResult` 변경: 기존 필드 제거, `content: str` 단일 필드
  - `VocabularyResult` 변경: `words: list[VocabularyWordEntry]`
  - 기존 `AnalyzeRequest`, `AnalyzeImageRequest`, `ChatRequest`, `AnalyzeResponse` 유지
  - `AnalyzeResponse`에 `supervisor_analysis: SupervisorAnalysis | None` 추가 고려

- [M1-T2] `state.py` 수정
  - `supervisor_analysis: NotRequired[SupervisorAnalysis | None]` 필드 추가
  - import 경로 업데이트 (새 스키마 참조)
  - 기존 result 필드 타입이 새 스키마를 참조하도록 변경

**Acceptance Gate**: Pydantic 모델 유효성 검증 테스트 통과

---

### Milestone 2: Prompt Infrastructure (Priority: High)

**목표**: 한국어 교육 프롬프트 전면 재작성

**관련 TAG**: TAG-PROMPT-01, TAG-LEVEL-01

**Task 목록**:

- [M2-T1] `level_instructions.yaml` 재작성
  - 5개 레벨 전체를 한국어 교육학적 설명으로 변경
  - 각 에이전트(reading, grammar, vocabulary)별 레벨 지시문 분리
  - Level 1-5 교육 목표와 설명 톤 명확히 정의

- [M2-T2] `prompts/supervisor.md` 작성
  - 한국어 사전 분석 프롬프트
  - 문장 분리 지시 (마침표, 세미콜론, 콜론 기준)
  - 난이도 5단계 평가 기준 제시
  - 학습 포커스 추천 카테고리 정의
  - JSON 출력 포맷 명시

- [M2-T3] `prompts/reading_tutor.md` 작성
  - 참조: `my-prompt/reading-prompt.md`
  - 문장별 4단계 구조: 슬래시 직독 끊기 -> 단위별 한국어 해석 -> 자연스러운 해석 -> 읽기 지시
  - 직독 끊기 규칙 포함
  - 읽기 지시 규칙 포함 (지시형 말투)
  - 레벨 플레이스홀더 (`{level_instructions}`) 포함

- [M2-T4] `prompts/grammar_tutor.md` 작성
  - 참조: `my-prompt/grammar-prompt.md`
  - 문장별 4단계 구조: 문법 포인트 -> 왜 이 구조를 썼는가 -> 한국어와의 구조 차이 -> 시험 포인트
  - 슬래시 읽기 포함 (문법 구조 관점)
  - 중고등학교 문법 용어 사용 필수
  - 레벨 플레이스홀더 포함

- [M2-T5] `prompts/vocabulary_tutor.md` 작성
  - 참조: `my-prompt/vocabulary-prompt.md`
  - 단어별 6단계 구조: 기본 뜻 -> 문장 속 의미 -> 핵심 이미지 -> 어원(PIE) -> 파생어 -> 기억 팁
  - 단어 선정 원칙 포함
  - 절대 금지 사항 포함
  - 레벨 플레이스홀더 포함

- [M2-T6] `prompts.py` 수정
  - 새 프롬프트 파일 경로 로딩 로직 추가/수정
  - Supervisor 프롬프트 로딩 함수 추가 (기존에 없었다면)
  - 레벨 지시문 주입 로직 검증

**Acceptance Gate**: 모든 프롬프트 파일이 올바르게 로드되고, 변수 치환이 정상 동작

---

### Milestone 3: Agent Implementation (Priority: High)

**목표**: 에이전트 로직 업데이트 - LLM Supervisor 전환 및 모델 변경

**관련 TAG**: TAG-SUP-01, TAG-MODEL-01, TAG-PROMPT-01

**Task 목록**:

- [M3-T1] `agents/supervisor.py` 대규모 재작성
  - 순수 라우터(`if/elif` 분기)에서 LLM 기반 사전 분석기로 전환
  - Claude Haiku 모델 호출 로직 추가 (`get_llm("haiku")`)
  - 한국어 사전 분석 프롬프트 로딩 및 적용
  - JSON 구조화 출력 파싱 -> `SupervisorAnalysis` 스키마 매핑
  - Fallback 로직: LLM 실패 시 기본 문장 분리(마침표 기준)
  - `state["supervisor_analysis"]`에 결과 저장
  - 기존 라우팅 로직(`next_nodes` 반환) 유지

- [M3-T2] `agents/vocabulary.py` 수정
  - 모델 변경: Haiku -> Sonnet (`get_llm("sonnet")`)
  - 새 어원 네트워크 프롬프트 적용
  - 결과를 `VocabularyResult(words=[VocabularyWordEntry(...)])` 스키마로 변환
  - Supervisor 분석 결과(`supervisor_analysis`) 활용하여 문맥 전달

- [M3-T3] `agents/grammar.py` 수정
  - 새 문법 구조 이해 프롬프트 적용
  - 결과를 `GrammarResult(content=...)` 스키마로 변환
  - Supervisor 분석 결과 활용

- [M3-T4] `agents/reading.py` 수정
  - 새 읽기 훈련 프롬프트 적용
  - 결과를 `ReadingResult(content=...)` 스키마로 변환
  - Supervisor 분석 결과 활용

**Acceptance Gate**: 각 에이전트가 올바른 모델을 호출하고, 결과가 새 스키마에 맞는지 검증

---

### Milestone 4: Frontend Update (Priority: High)

**목표**: 프론트엔드 타입 및 컴포넌트를 새 스키마에 맞게 변경

**관련 TAG**: TAG-FRONT-01, TAG-SCHEMA-01

**Task 목록**:

- [M4-T1] `types/tutor.ts` 재작성
  - `ReadingResult`: `{ content: string }`
  - `GrammarResult`: `{ content: string }`
  - `VocabularyWordEntry`: `{ word: string; content: string }`
  - `VocabularyResult`: `{ words: VocabularyWordEntry[] }`
  - 기존 `GrammarIssue`, `VocabularyWord` 인터페이스 제거
  - `AnalyzeResponse` 업데이트

- [M4-T2] `hooks/use-tutor-stream.ts` 수정
  - SSE 이벤트 파싱 로직을 새 스키마에 맞게 업데이트
  - `content` 기반 결과 누적 로직 적용
  - 기존 구조화 데이터 파싱 로직 제거

- [M4-T3] `components/tutor/tabbed-output.tsx` 수정
  - 탭 라벨 변경: "Reading" -> "독해", "Grammar" -> "문법", "Vocabulary" -> "어휘"
  - Props 타입 업데이트

- [M4-T4] `components/tutor/reading-panel.tsx` 재작성
  - 기존 구조화 렌더링 제거 (summary, keyPoints 등)
  - ReactMarkdown으로 `content` 필드 렌더링
  - 한국어 Markdown 스타일링 적용

- [M4-T5] `components/tutor/grammar-panel.tsx` 재작성
  - 기존 구조화 렌더링 제거 (issues, overallScore 등)
  - ReactMarkdown으로 `content` 필드 렌더링

- [M4-T6] `components/tutor/vocabulary-panel.tsx` 재작성
  - 기존 VocabularyWord 테이블 렌더링 제거
  - 각 VocabularyWordEntry의 `content`를 ReactMarkdown으로 렌더링
  - 단어별 접기/펼치기 UI 고려

- [M4-T7] `components/layout/desktop-layout.tsx` 수정
  - 새 타입에 맞는 props 전달 조정

- [M4-T8] `components/mobile/analysis-view.tsx` 수정
  - 새 타입에 맞는 props 전달 조정

**Acceptance Gate**: 모든 패널이 한국어 Markdown을 올바르게 렌더링하고, 탭 라벨이 한국어로 표시

---

### Milestone 5: Integration Testing (Priority: Medium)

**목표**: 전체 파이프라인 통합 테스트

**Task 목록**:

- [M5-T1] Backend 통합 테스트
  - Supervisor LLM 사전 분석 -> 튜터 에이전트 병렬 실행 -> 결과 수집 파이프라인 검증
  - Supervisor fallback 시나리오 테스트
  - 새 스키마 직렬화/역직렬화 검증

- [M5-T2] Frontend 통합 테스트
  - SSE 스트리밍으로 수신한 새 스키마 데이터의 ReactMarkdown 렌더링 검증
  - 탭 전환 시 한국어 콘텐츠 정상 표시 검증
  - 모바일/데스크톱 레이아웃 검증

- [M5-T3] End-to-End 테스트
  - 실제 텍스트 입력 -> SSE 스트리밍 -> 한국어 결과 표시 전체 흐름
  - 이미지 업로드 -> OCR -> 한국어 결과 흐름

**Acceptance Gate**: 전체 파이프라인이 한국어 교육 콘텐츠를 정상 생성 및 표시

---

## 3. Technical Approach

### 3.1 Supervisor 전환 전략

기존 Supervisor는 `task_type` 기반 순수 라우터(`if/elif`)였다. 새 Supervisor는:

1. LLM 호출 (Claude Haiku)로 텍스트 사전 분석 수행
2. 분석 결과를 `SupervisorAnalysis`로 구조화
3. **기존 라우팅 로직 유지** (`next_nodes` 반환)
4. 분석 결과를 state에 저장하여 후속 에이전트가 참조

```
[기존] 텍스트 입력 -> Supervisor(if/elif) -> Send(reading, grammar, vocabulary)
[신규] 텍스트 입력 -> Supervisor(LLM 분석 + 라우팅) -> Send(reading, grammar, vocabulary)
                         |
                         v
                  SupervisorAnalysis 저장
                  (sentences, difficulty, focus)
```

### 3.2 Content-Based Schema 전략

구조화된 JSON 스키마에서 `content: str` Markdown 기반으로 전환:

**장점**:
- LLM이 자유 형식으로 풍부한 교육 콘텐츠 생성 가능
- 프롬프트 변경만으로 출력 형식 조정 가능
- 프론트엔드 렌더링 로직 단순화 (ReactMarkdown 통합)

**주의사항**:
- Markdown 품질은 프롬프트 품질에 의존
- SSE 스트리밍 중 부분 Markdown 렌더링 처리 필요
- XSS 방지를 위한 Markdown sanitization 필요 (ReactMarkdown 기본 제공)

### 3.3 프롬프트 설계 원칙

1. **참조 기반**: `my-prompt/` 디렉토리의 검증된 프롬프트를 시스템 프롬프트로 변환
2. **레벨 주입**: `{level_instructions}` 플레이스홀더로 레벨별 지시문 동적 주입
3. **Supervisor 컨텍스트 전달**: 사전 분석 결과(문장 목록, 난이도)를 각 에이전트에 전달
4. **한국어 전용**: 모든 프롬프트와 출력을 한국어로 작성
5. **No Few-shot**: 예시 없이 규칙 기반 프롬프트만 사용

### 3.4 모델 변경 영향 분석

| Change              | Cost Impact                   | Quality Impact              |
|---------------------|-------------------------------|-----------------------------|
| Supervisor: mini->Haiku | 유사 (둘 다 저비용 모델)     | 향상 (LLM 분석 추가)       |
| Vocabulary: Haiku->Sonnet | 증가 (~5x)                | 대폭 향상 (어원 설명 품질)  |

**비용 추정 (1,000 요청 기준)**:
- Supervisor (Haiku): ~$0.5 (기존 mini와 유사)
- Vocabulary (Sonnet): ~$15 (기존 Haiku $2에서 증가)
- 전체 영향: 요청당 ~$0.013 추가

---

## 4. Risk Analysis

### Risk 1: Supervisor LLM 응답 불안정

- **확률**: Medium
- **영향**: High
- **완화**: JSON 파싱 실패 시 마침표 기준 fallback 문장 분리 구현
- **모니터링**: Supervisor 성공률 로깅

### Risk 2: Vocabulary Sonnet 비용 증가

- **확률**: High (확정적)
- **영향**: Medium
- **완화**: Supervisor Haiku 유지로 전체 비용 균형, 캐싱 전략 향후 적용
- **모니터링**: 월간 LLM API 비용 추적

### Risk 3: ReactMarkdown 렌더링 불일치

- **확률**: Low
- **영향**: Medium
- **완화**: 프롬프트에 Markdown 출력 형식 명시, 렌더링 테스트 자동화
- **모니터링**: 프론트엔드 E2E 테스트

### Risk 4: 기존 테스트 대량 실패

- **확률**: High (확정적)
- **영향**: Medium
- **완화**: 스키마 변경에 따른 테스트 업데이트를 Milestone 별로 진행
- **모니터링**: CI/CD 파이프라인

### Risk 5: SSE 스트리밍 호환성

- **확률**: Low
- **영향**: High
- **완화**: `services/streaming.py`는 구조 비의존적으로 설계되어 있어 호환 예상
- **검증**: 통합 테스트에서 스트리밍 데이터 포맷 확인

---

## 5. Implementation Order

```
M1 (Foundation) -> M2 (Prompts) -> M3 (Agents) -> M4 (Frontend) -> M5 (Integration)
     schemas         prompts          supervisor       types          E2E test
     state           level_inst       vocabulary       panels
                     prompts.py       grammar          tabs
                                      reading          layouts
```

**의존성 관계**:
- M2는 M1 완료 후 시작 (스키마 참조)
- M3는 M1 + M2 완료 후 시작 (스키마 + 프롬프트 참조)
- M4는 M1 완료 후 시작 가능 (M3와 병렬 가능)
- M5는 M3 + M4 모두 완료 후 시작

---

## 6. Expert Consultation Recommendations

### Backend Expert (expert-backend)

- Supervisor LLM 호출 패턴 및 fallback 전략 설계
- LangGraph state 업데이트 패턴 검증
- Pydantic 스키마 마이그레이션 전략

### Frontend Expert (expert-frontend)

- ReactMarkdown 통합 및 스타일링 전략
- SSE 스트리밍 데이터의 실시간 Markdown 렌더링 패턴
- 한국어 타이포그래피 및 UI/UX 고려사항
