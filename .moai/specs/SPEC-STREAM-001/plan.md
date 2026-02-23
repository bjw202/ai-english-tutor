---
id: SPEC-STREAM-001
type: plan
version: "1.0.0"
status: implemented
---

# SPEC-STREAM-001: Implementation Plan

## Overview

기존 `graph.ainvoke()` 기반의 일괄 전송 방식에서 `graph.astream_events(version="v2")` 기반의 토큰 단위 스트리밍으로 전환하는 구현 계획.

## Execution Strategy

- **Development Mode**: Hybrid (TDD for new code, DDD for modified code)
- **New code (TDD)**: `format_reading_token()`, `format_grammar_token()`, `format_section_done()`, `SectionStreamingState`, 토큰 스트리밍 테스트
- **Modified code (DDD)**: `tutor.py` 라우터 리팩토링, `use-tutor-stream.ts` 확장, UI 컴포넌트 수정

## Phase Breakdown

### Phase 1: Backend LLM Configuration (Priority: High)

**Goal**: ChatOpenAI 인스턴스에 `streaming=True`를 활성화하여 토큰 단위 스트리밍의 전제 조건 확보

**Changes**:
- `backend/src/tutor/models/llm.py`: 모든 ChatOpenAI 생성자에 `streaming=True` 추가

**Dependencies**: None (independent)

**Risks**:
- Risk: `streaming=True` 설정이 기존 `ainvoke` 호출에 영향을 줄 수 있음
- Mitigation: `ainvoke`는 `streaming` 파라미터와 무관하게 동작 확인 완료

### Phase 2: Backend Streaming Infrastructure (Priority: High)

**Goal**: SSE 토큰 이벤트 포맷터 및 그래프 스트리밍 헬퍼 구축

**Changes**:
- `backend/src/tutor/services/streaming.py`: `format_reading_token()`, `format_grammar_token()`, `format_section_done()` 함수 추가
- `backend/src/tutor/routers/tutor.py`: `_stream_graph_events()` 공유 헬퍼 작성, `ainvoke` -> `astream_events(v2)` 전환

**Dependencies**: Phase 1 (streaming=True 필수)

**Risks**:
- Risk: `astream_events` v2의 이벤트 구조가 LangGraph 버전에 따라 다를 수 있음
- Mitigation: `metadata.langgraph_node`로 노드 식별, LangGraph 0.3.x 호환 확인
- Risk: 클라이언트가 중간에 연결을 끊을 경우 `asyncio.CancelledError` 발생
- Mitigation: `try/except asyncio.CancelledError: pass` 패턴으로 graceful handling

### Phase 3: Frontend Type Definitions & Hook Extension (Priority: High)

**Goal**: 프론트엔드 스트리밍 상태 관리 인프라 구축

**Changes**:
- `src/types/tutor.ts`: `SectionStreamingState` 인터페이스 추가
- `src/hooks/use-tutor-stream.ts`: `reading_token`/`grammar_token` append 핸들러, `reading_done`/`grammar_done` 플래그 핸들러, 기존 `reading_chunk`/`grammar_chunk` 하위 호환 핸들러 유지

**Dependencies**: Phase 2 (백엔드 이벤트 스키마 확정 후)

**Risks**:
- Risk: 토큰 단위 `setState` 호출이 렌더링 성능에 영향을 줄 수 있음
- Mitigation: React 19의 automatic batching이 고빈도 setState를 자동 최적화

### Phase 4: Frontend UI Components (Priority: Medium)

**Goal**: 스트리밍 상태에 따른 시각적 피드백 제공

**Changes**:
- `src/components/tutor/tabbed-output.tsx`: Streaming props 수신, pulsing dot 인디케이터
- `src/components/tutor/reading-panel.tsx`: 블링킹 커서, streaming-aware empty state
- `src/components/tutor/grammar-panel.tsx`: 블링킹 커서 패턴 (reading과 동일)
- `src/components/tutor/vocabulary-panel.tsx`: 스켈레톤 로딩 UI

**Dependencies**: Phase 3 (streaming 플래그 사용 가능해야 함)

**Risks**:
- Risk: 블링킹 커서 CSS 애니메이션이 저사양 모바일에서 성능 이슈
- Mitigation: `@media (prefers-reduced-motion)` 쿼리로 접근성 대응

### Phase 5: Layout Integration & Testing (Priority: Medium)

**Goal**: 레이아웃 컴포넌트에 streaming 플래그 전파 및 테스트 완성

**Changes**:
- `src/components/layout/desktop-layout.tsx`: 4개 streaming 플래그 TabbedOutput으로 전달
- `src/components/mobile/analysis-view.tsx`: 4개 streaming 플래그 TabbedOutput으로 전달
- `src/hooks/__tests__/use-tutor-stream.test.ts`: 6개 신규 테스트 추가

**Dependencies**: Phase 4 (UI 컴포넌트 완성 후)

**Risks**:
- Risk: Desktop과 Mobile 레이아웃 간 props 불일치
- Mitigation: TypeScript strict mode가 누락된 props를 컴파일 타임에 감지

## Dependency Graph

```
Phase 1 (LLM Config)
    |
    v
Phase 2 (Backend Streaming)
    |
    v
Phase 3 (Frontend Types & Hook)
    |
    v
Phase 4 (UI Components)
    |
    v
Phase 5 (Layout & Testing)
```

## File Modification Summary

| Phase | File | Change Type | Scope |
|-------|------|-------------|-------|
| 1 | `backend/src/tutor/models/llm.py` | Modified | `streaming=True` 추가 |
| 2 | `backend/src/tutor/services/streaming.py` | Modified | 3개 함수 추가 |
| 2 | `backend/src/tutor/routers/tutor.py` | Modified | `_stream_graph_events` 헬퍼, `astream_events` 전환 |
| 3 | `src/types/tutor.ts` | Modified | `SectionStreamingState` 인터페이스 |
| 3 | `src/hooks/use-tutor-stream.ts` | Modified | 토큰 핸들러, section done 핸들러 |
| 4 | `src/components/tutor/tabbed-output.tsx` | Modified | Streaming props, pulsing dot |
| 4 | `src/components/tutor/reading-panel.tsx` | Modified | 블링킹 커서 |
| 4 | `src/components/tutor/grammar-panel.tsx` | Modified | 블링킹 커서 |
| 4 | `src/components/tutor/vocabulary-panel.tsx` | Modified | 스켈레톤 로딩 |
| 5 | `src/components/layout/desktop-layout.tsx` | Modified | Streaming 플래그 전달 |
| 5 | `src/components/mobile/analysis-view.tsx` | Modified | Streaming 플래그 전달 |
| 5 | `src/hooks/__tests__/use-tutor-stream.test.ts` | Modified | 6개 테스트 추가 |

## Architecture Design Direction

### Before (ainvoke)

```
Client <--SSE-- Server
                  |
                  ainvoke(graph)  -- waits for ALL agents --
                  |
                  reading_chunk (full content)
                  grammar_chunk (full content)
                  vocabulary_chunk (full content)
                  done
```

### After (astream_events v2)

```
Client <--SSE-- Server
                  |
                  astream_events(graph, v2)  -- progressive tokens --
                  |
                  reading_token ("The")
                  reading_token (" cat")
                  reading_token (" sat...")
                  ...
                  reading_done
                  grammar_token ("This")
                  grammar_token (" sentence...")
                  ...
                  grammar_done
                  vocabulary_chunk (batch data)
                  done
```

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LangGraph astream_events API 변경 | Low | High | v2 버전 명시, 마이너 버전 고정 |
| 고빈도 토큰 이벤트로 인한 브라우저 렌더링 부하 | Medium | Medium | React 19 automatic batching 활용 |
| 클라이언트 중간 연결 끊김 | High | Low | asyncio.CancelledError graceful handling |
| 레거시 클라이언트 호환성 깨짐 | Low | High | reading_chunk/grammar_chunk 핸들러 유지 |
| 스켈레톤 UI 깜빡임 (vocabulary 빠른 응답 시) | Low | Low | 최소 표시 시간 설정 가능 |
