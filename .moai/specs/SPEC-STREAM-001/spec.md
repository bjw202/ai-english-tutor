---
id: SPEC-STREAM-001
version: "1.0.1"
status: completed
created: "2026-02-23"
updated: "2026-02-23"
author: jw
priority: high
---

# SPEC-STREAM-001: Token-Level SSE Streaming

## HISTORY

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.1 | 2026-02-23 | jw | Documentation sync completed, status → completed |
| 1.0.0 | 2026-02-23 | jw | Retroactive SPEC creation (implementation complete) |

## Overview

AI English Tutor는 LangGraph로 3개의 병렬 에이전트(reading, grammar, vocabulary)를 사용하여 영어 텍스트를 분석한다. 기존에는 `graph.ainvoke()`를 사용하여 모든 에이전트가 완료될 때까지 대기한 후 SSE 이벤트를 한꺼번에 전송했다. 이로 인해 콘텐츠가 "한 번에 번쩍" 표시되는 문제가 발생했다.

본 SPEC은 `graph.astream_events(version="v2")`를 활용하여 reading과 grammar 섹션에 토큰 단위 스트리밍을 도입하고, vocabulary는 구조화 데이터 특성상 일괄 전달 방식을 유지하는 것을 정의한다.

## Environment

- **Backend**: Python 3.13+, FastAPI 0.115+, LangGraph 0.3.x, LangChain ChatOpenAI (`streaming=True`)
- **Frontend**: Next.js 15.x, React 19.x, TypeScript 5.9+, Vitest 3.x
- **Protocol**: Server-Sent Events (SSE) via `text/event-stream`
- **LLM**: OpenAI GPT-4o-mini (configurable), Zhipu GLM 모델 지원

## Assumptions

1. LangGraph `astream_events(version="v2")`는 `on_chat_model_stream` 이벤트를 통해 개별 토큰을 전달한다.
2. ChatOpenAI 생성자에 `streaming=True` 설정이 토큰 단위 스트리밍의 전제 조건이다.
3. Vocabulary 에이전트의 출력은 JSON 구조화 데이터이므로 토큰 단위 스트리밍이 불가하다 (중간 파싱 불가).
4. 기존 `reading_chunk` / `grammar_chunk` 이벤트를 수신하는 클라이언트와의 하위 호환성이 필요하다.
5. SSE 연결은 클라이언트가 중간에 끊을 수 있으며, 서버는 이를 gracefully 처리해야 한다.

## Requirements

### 1. Ubiquitous Requirements (항상 적용)

- **[REQ-U-001]** Reading 및 Grammar 섹션은 항상 토큰 단위 스트리밍으로 표시되어야 한다.
- **[REQ-U-002]** Vocabulary 섹션은 구조화 데이터이므로 항상 에이전트 완료 후 일괄 표시되어야 한다.
- **[REQ-U-003]** 모든 LLM 클라이언트(ChatOpenAI)는 항상 `streaming=True`로 초기화되어야 한다.

### 2. Event-Driven Requirements (이벤트 발생 시)

- **[REQ-E-001]** WHEN LLM이 reading 노드에서 토큰을 생성하면, THEN `reading_token` SSE 이벤트가 `{"token": "<text>"}` 형식으로 즉시 발행되어야 한다.
- **[REQ-E-002]** WHEN LLM이 grammar 노드에서 토큰을 생성하면, THEN `grammar_token` SSE 이벤트가 `{"token": "<text>"}` 형식으로 즉시 발행되어야 한다.
- **[REQ-E-003]** WHEN reading 노드가 완료되면, THEN `reading_done` 이벤트가 `{"section": "reading"}` 형식으로 발행되어야 한다.
- **[REQ-E-004]** WHEN grammar 노드가 완료되면, THEN `grammar_done` 이벤트가 `{"section": "grammar"}` 형식으로 발행되어야 한다.
- **[REQ-E-005]** WHEN aggregator 노드가 완료되면, THEN `vocabulary_chunk` 이벤트가 전체 어휘 데이터와 함께 발행되어야 한다.
- **[REQ-E-006]** WHEN 모든 에이전트가 완료되면, THEN `done` 이벤트가 발행되어야 한다.

### 3. State-Driven Requirements (상태 기반)

- **[REQ-S-001]** IF reading/grammar/vocabulary 중 하나라도 스트리밍 중이면, THEN 해당 탭 라벨에 pulsing dot 인디케이터가 표시되어야 한다.
- **[REQ-S-002]** IF 섹션이 스트리밍 중이면, THEN 빈 콘텐츠라도 탭 UI가 표시되어야 한다 (empty state 숨기기).
- **[REQ-S-003]** IF Reading 또는 Grammar 섹션이 스트리밍 중이면, THEN 콘텐츠 끝에 블링킹 커서가 표시되어야 한다.
- **[REQ-S-004]** IF Vocabulary 섹션이 스트리밍 중이면, THEN 스켈레톤 로딩 UI가 표시되어야 한다.

### 4. Unwanted Behavior Requirements (금지)

- **[REQ-N-001]** Vocabulary 토큰을 개별 스트리밍해서는 안 된다 (JSON 파싱 불가).
- **[REQ-N-002]** `done` 이벤트 수신 후 어떤 스트리밍 플래그(`readingStreaming`, `grammarStreaming`, `vocabularyStreaming`)도 `true`로 남아있어서는 안 된다.
- **[REQ-N-003]** 빈 토큰(empty string)은 SSE 이벤트로 발행해서는 안 된다.

### 5. Complex Requirements (조합)

- **[REQ-C-001]** IF 사용자가 탭을 전환하는 중이고, AND 스트리밍이 진행 중이면, THEN 각 탭의 스트리밍 상태와 누적된 콘텐츠가 유지되어야 한다.
- **[REQ-C-002]** IF 백엔드가 레거시 `reading_chunk` / `grammar_chunk` 이벤트를 전송하면, THEN 프론트엔드는 콘텐츠를 교체(replace) 방식으로 처리하여 하위 호환성이 유지되어야 한다.

## Specifications

### SSE Event Schema

| Event Type | Payload | Delivery | Description |
|---|---|---|---|
| `reading_token` | `{"token": "<text>"}` | Per-token (append) | Reading 에이전트 토큰 스트림 |
| `grammar_token` | `{"token": "<text>"}` | Per-token (append) | Grammar 에이전트 토큰 스트림 |
| `reading_done` | `{"section": "reading"}` | Once | Reading 섹션 완료 신호 |
| `grammar_done` | `{"section": "grammar"}` | Once | Grammar 섹션 완료 신호 |
| `vocabulary_chunk` | `{"words": [...]}` | Batch (once) | Vocabulary 전체 데이터 |
| `reading_chunk` | `{"content": "<md>"}` | Legacy (replace) | 하위 호환 reading 청크 |
| `grammar_chunk` | `{"content": "<md>"}` | Legacy (replace) | 하위 호환 grammar 청크 |
| `done` | `{"session_id": "...", "status": "complete"}` | Once | 전체 완료 |
| `error` | `{"message": "...", "code": "..."}` | On error | 에러 발생 |

### Backend Architecture

- `_stream_graph_events()` 공유 헬퍼가 `graph.astream_events(version="v2")`를 소비
- `on_chat_model_stream` 이벤트에서 `metadata.langgraph_node`로 reading/grammar 구분
- `on_chain_end` 이벤트에서 노드 완료 감지 및 section_done / vocabulary_chunk 발행
- `asyncio.CancelledError`는 조용히 pass 처리 (클라이언트 연결 끊김)

### Frontend Architecture

- `SectionStreamingState` 인터페이스: `readingStreaming`, `grammarStreaming`, `vocabularyStreaming` 플래그
- `useTutorStream` 훅: 토큰 append 핸들러 + 레거시 chunk replace 핸들러
- `TabbedOutput`: streaming props 수신 및 pulsing dot 인디케이터 표시
- `ReadingPanel` / `GrammarPanel`: 블링킹 커서 표시
- `VocabularyPanel`: 스켈레톤 로딩 UI
- Desktop/Mobile 레이아웃: 4개 streaming 플래그 전달

### Modified Files (12 files)

**Backend (3 files):**

1. `backend/src/tutor/models/llm.py` - ChatOpenAI 생성자에 `streaming=True` 추가
2. `backend/src/tutor/services/streaming.py` - `format_reading_token()`, `format_grammar_token()`, `format_section_done()` 추가
3. `backend/src/tutor/routers/tutor.py` - `ainvoke` -> `astream_events(v2)` 전환, `_stream_graph_events` 헬퍼, `asyncio.CancelledError` 처리

**Frontend (9 files):**

4. `src/types/tutor.ts` - `SectionStreamingState` 인터페이스 추가
5. `src/hooks/use-tutor-stream.ts` - 토큰 append 핸들러, section streaming 플래그, 하위 호환 chunk 핸들러
6. `src/components/tutor/tabbed-output.tsx` - Streaming props, pulsing dot 인디케이터
7. `src/components/tutor/reading-panel.tsx` - 블링킹 커서, streaming-aware empty state
8. `src/components/tutor/grammar-panel.tsx` - 블링킹 커서 패턴 (reading과 동일)
9. `src/components/tutor/vocabulary-panel.tsx` - 스켈레톤 로딩 UI
10. `src/components/layout/desktop-layout.tsx` - 4개 streaming 플래그 TabbedOutput 전달
11. `src/components/mobile/analysis-view.tsx` - 4개 streaming 플래그 TabbedOutput 전달
12. `src/hooks/__tests__/use-tutor-stream.test.ts` - 토큰 스트리밍 관련 6개 테스트 추가

## Traceability

| Requirement | Implementation | Test |
|---|---|---|
| REQ-U-001 | `tutor.py:_stream_graph_events`, `use-tutor-stream.ts` | `use-tutor-stream.test.ts` (token append tests) |
| REQ-U-002 | `tutor.py:aggregator` handler, `use-tutor-stream.ts:vocabulary_chunk` | `use-tutor-stream.test.ts` (vocabulary_chunk test) |
| REQ-U-003 | `llm.py:streaming=True` | Backend unit tests |
| REQ-E-001 | `tutor.py:format_reading_token` | `use-tutor-stream.test.ts` (reading_token test) |
| REQ-E-002 | `tutor.py:format_grammar_token` | `use-tutor-stream.test.ts` (grammar_token test) |
| REQ-E-003 | `tutor.py:format_section_done("reading")` | `use-tutor-stream.test.ts` (reading_done test) |
| REQ-E-004 | `tutor.py:format_section_done("grammar")` | `use-tutor-stream.test.ts` (grammar_done test) |
| REQ-E-005 | `tutor.py:format_vocabulary_chunk` | `use-tutor-stream.test.ts` (vocabulary_chunk test) |
| REQ-N-001 | Vocabulary는 `on_chain_end`에서만 처리 | Architecture constraint |
| REQ-N-002 | `done` handler에서 모든 플래그 false 설정 | `use-tutor-stream.test.ts` |
| REQ-C-001 | React state 기반 독립적 탭 콘텐츠 관리 | Manual E2E verification |
| REQ-C-002 | `reading_chunk`/`grammar_chunk` replace 핸들러 | `use-tutor-stream.test.ts` (chunk tests) |
