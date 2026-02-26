# SPEC-VOCAB-001: Fix Vocabulary SSE Streaming Pipeline

| Field     | Value                                        |
|-----------|----------------------------------------------|
| SPEC ID   | SPEC-VOCAB-001                               |
| Title     | Fix Vocabulary SSE Streaming Pipeline        |
| Created   | 2026-02-26                                   |
| Status    | Completed                                    |
| Priority  | High                                         |
| Lifecycle | spec-first                                   |
| Tags      | `vocabulary`, `sse`, `streaming`, `bug-fix`  |

---

## 1. Environment

### 1.1 System Context

The AI English Tutor application uses a LangGraph multi-agent pipeline that dispatches three parallel agents (reading, grammar, vocabulary) via the `Send()` API. Results are streamed to the frontend as Server-Sent Events (SSE). The reading and grammar agents use token-level streaming (`on_chat_model_stream`) with dedicated `_done` section events, while the vocabulary agent produces a batch result (`VocabularyResult`) that must be delivered as a single `vocabulary_chunk` event.

### 1.2 Architecture Overview

```
[Frontend]  <--SSE--  [FastAPI Router]  <--astream_events--  [LangGraph]
                         tutor.py                              graph.py
                                                                 |
                                                    +------------+------------+
                                                    |            |            |
                                                 reading     grammar     vocabulary
                                                    |            |            |
                                                    +------> aggregator ------+
                                                                 |
                                                                END
```

### 1.3 Current SSE Event Flow

| Agent      | Token Streaming       | Section Done Event | Batch Chunk Event  |
|------------|-----------------------|--------------------|--------------------|
| reading    | `reading_token`       | `reading_done`     | `reading_chunk`    |
| grammar    | `grammar_token`       | `grammar_done`     | `grammar_chunk`    |
| vocabulary | (none - batch only)   | (none)             | `vocabulary_chunk` |

### 1.4 Affected Files

**Backend:**

| File | Purpose | Lines of Interest |
|------|---------|-------------------|
| `backend/src/tutor/routers/tutor.py` | SSE event routing (`_stream_graph_events`) | 39-101 |
| `backend/src/tutor/services/streaming.py` | SSE event formatter functions | Full file |
| `backend/src/tutor/agents/vocabulary.py` | Vocabulary agent with error handling | 125-133 |
| `backend/src/tutor/state.py` | `TutorState` TypedDict | Full file |

**Frontend:**

| File | Purpose |
|------|---------|
| `src/hooks/use-tutor-stream.ts` | SSE event parsing and state management |
| `src/components/tutor/vocabulary-panel.tsx` | Vocabulary display component |
| `src/components/tutor/tabbed-output.tsx` | Error state prop forwarding |
| `src/components/layout/desktop-layout.tsx` | Error state prop forwarding |
| `src/components/mobile/analysis-view.tsx` | Error state prop forwarding |

**Tests:**

| File | Purpose |
|------|---------|
| `backend/tests/unit/test_agents.py` | Backend agent unit tests |
| `backend/tests/unit/test_graph.py` | LangGraph graph tests |
| `src/hooks/__tests__/use-tutor-stream.test.ts` | Frontend hook tests |
| `src/components/tutor/__tests__/vocabulary-panel.test.tsx` | Panel component tests |

---

## 2. Assumptions

### 2.1 Validated Assumptions

| # | Assumption | Confidence | Evidence |
|---|-----------|------------|----------|
| A1 | The vocabulary agent completes successfully in most cases but its output is lost in the aggregator SSE extraction path. | High | Code inspection of `tutor.py` lines 85-94 shows vocabulary extraction depends on `aggregator` `on_chain_end` event matching a specific `analyze_response.vocabulary` structure. |
| A2 | Reading and grammar agents work correctly because they use `on_chain_end` events keyed to their own node name (`reading`, `grammar`), independent of the aggregator. | High | Code inspection of `tutor.py` lines 81-84. |
| A3 | The vocabulary node's own `on_chain_end` event is emitted by LangGraph but is currently ignored (no handler for `node_name == "vocabulary"`). | High | LangGraph `astream_events(version="v2")` emits `on_chain_end` for every node including `vocabulary`. The router only handles `reading`, `grammar`, and `aggregator` node names. |
| A4 | Vocabulary errors are silently swallowed and indistinguishable from legitimate empty results. | High | `vocabulary.py` line 131-133: the `except` block returns `VocabularyResult(words=[])`. |

### 2.2 Unvalidated Assumptions

| # | Assumption | Confidence | Risk if Wrong |
|---|-----------|------------|---------------|
| A5 | The `on_chain_end` event for `vocabulary` node includes the returned dict in `event.data.output`. | Medium | If the output structure differs, the vocabulary data extraction logic must be adjusted. Validate with a debug log during implementation. |
| A6 | Adding a `vocabulary_done` event will not cause race conditions with the `done` event. | Medium | The `done` event is emitted after the full `astream_events` loop completes, so `vocabulary_done` (emitted mid-loop) should always precede it. |

---

## 3. Requirements

### 3.1 Core Requirements (EARS Format)

**REQ-1: Direct Vocabulary Chunk Emission (Event-Driven)**

> **When** the vocabulary node's `on_chain_end` event is received in `_stream_graph_events`, the system **shall** extract the `vocabulary_result` from `event.data.output` and emit a `vocabulary_chunk` SSE event directly, without depending on the aggregator node's `on_chain_end` event.

- Rationale: The current architecture routes vocabulary data through the aggregator, creating a fragile dependency where structural mismatches silently lose data.
- Target flow: `vocabulary_node` -> `on_chain_end("vocabulary")` -> `vocabulary_chunk`
- Implementation file: `backend/src/tutor/routers/tutor.py` lines 79-94

**REQ-2: Vocabulary Done Section Event (Event-Driven)**

> **When** the vocabulary node completes (whether successfully or with an error), the system **shall** emit a `vocabulary_done` SSE event, matching the existing pattern of `reading_done` and `grammar_done` events.

- Rationale: Without `vocabulary_done`, the frontend `vocabularyStreaming` flag only transitions to `false` when either `vocabulary_chunk` is received or the final `done` event fires. If `vocabulary_chunk` is lost, the loading skeleton persists until `done`.
- Backend implementation: `backend/src/tutor/routers/tutor.py` (yield `format_section_done("vocabulary")`)
- Frontend implementation: `src/hooks/use-tutor-stream.ts` (add `vocabulary_done` handler)

**REQ-3: Vocabulary Error Propagation (Unwanted Behavior)**

> The system **shall not** silently return `VocabularyResult(words=[])` when the vocabulary LLM invocation fails. **When** an exception occurs in `vocabulary_node`, the system **shall** return error information in the state (e.g., `vocabulary_error` field), and the SSE router **shall** emit a `vocabulary_error` SSE event containing the error message.

- Rationale: Silent error swallowing makes debugging impossible and presents an empty result indistinguishable from a valid "no vocabulary" case.
- Backend files: `backend/src/tutor/agents/vocabulary.py`, `backend/src/tutor/services/streaming.py`, `backend/src/tutor/routers/tutor.py`
- State file: `backend/src/tutor/state.py` (add `vocabulary_error` field)

**REQ-4: Frontend Error Display (Event-Driven)**

> **When** the frontend receives a `vocabulary_error` SSE event, the `VocabularyPanel` **shall** display a user-friendly error message instead of the default empty state message ("No vocabulary analysis yet").

- Frontend files: `src/hooks/use-tutor-stream.ts`, `src/components/tutor/vocabulary-panel.tsx`
- Prop threading: `tabbed-output.tsx`, `desktop-layout.tsx`, `analysis-view.tsx`

**REQ-5: Regression Prevention (Ubiquitous)**

> The reading and grammar SSE streaming behavior (token-level streaming, `_done` events, and chunk events) **shall** remain unaffected by these changes.

- Validation: Existing tests for reading and grammar must continue to pass.
- No modification to reading/grammar event handlers or formatters.

### 3.2 Constraints

| ID | Constraint | Type |
|----|-----------|------|
| C1 | The LangGraph `astream_events(version="v2")` API must be used as-is; no LangGraph version change. | Technical |
| C2 | SSE event format must remain compatible with the existing frontend parser (event + data line format). | Technical |
| C3 | The aggregator node architecture must remain intact; vocabulary extraction is supplemented, not replaced. | Architectural |
| C4 | Backend changes must not require database migrations or configuration file changes. | Operational |

---

## 4. Specifications

### 4.1 Change 1: Direct Vocabulary Chunk from Vocabulary Node

**Target:** `backend/src/tutor/routers/tutor.py` (`_stream_graph_events` function)

**Current behavior (lines 79-94):**
- `on_chain_end` with `node_name == "reading"` -> `format_section_done("reading")`
- `on_chain_end` with `node_name == "grammar"` -> `format_section_done("grammar")`
- `on_chain_end` with `node_name == "aggregator"` -> extract vocabulary from `analyze_response.vocabulary`

**Target behavior:**
- Add handler: `on_chain_end` with `node_name == "vocabulary"` -> extract `vocabulary_result` from `event.data.output` -> yield `format_vocabulary_chunk(vocabulary_result.model_dump())` -> yield `format_section_done("vocabulary")`
- Keep the aggregator-based vocabulary extraction as a fallback (defensive coding).

**Data extraction pattern:**
```
event.data.output -> dict with key "vocabulary_result" -> VocabularyResult instance
```

### 4.2 Change 2: Add `vocabulary_done` Section Event

**Backend (`tutor.py`):**
- Yield `format_section_done("vocabulary")` immediately after `format_vocabulary_chunk` in the vocabulary node handler.
- If vocabulary encounters an error, yield `vocabulary_error` first, then `vocabulary_done`.

**Backend (`streaming.py`):**
- The existing `format_section_done("vocabulary")` function already works via the generic `format_section_done(section)` helper. No new function needed.
- Add `format_vocabulary_error(message)` function following the pattern of `format_error_event`.

**Frontend (`use-tutor-stream.ts`):**
- Add `vocabulary_done` event handler:
  ```
  else if (currentEvent === "vocabulary_done") {
    setState(prev => ({ ...prev, vocabularyStreaming: false }));
  }
  ```
- Add `vocabulary_error` event handler:
  ```
  else if (currentEvent === "vocabulary_error") {
    setState(prev => ({
      ...prev,
      vocabularyStreaming: false,
      vocabularyError: data.message || "Vocabulary analysis failed",
    }));
  }
  ```

### 4.3 Change 3: Explicit Error Propagation

**State (`state.py`):**
- Add field: `vocabulary_error: NotRequired[str | None]`

**Vocabulary agent (`vocabulary.py`):**
- In the `except` block (lines 131-133), instead of returning `VocabularyResult(words=[])`, return both:
  ```python
  return {
      "vocabulary_result": VocabularyResult(words=[]),
      "vocabulary_error": str(e),
  }
  ```

**SSE Router (`tutor.py`):**
- In the vocabulary `on_chain_end` handler, check for `vocabulary_error` in the output:
  ```python
  output = event.get("data", {}).get("output", {})
  vocab_error = output.get("vocabulary_error")
  vocab_result = output.get("vocabulary_result")
  if vocab_error:
      yield format_vocabulary_error(vocab_error)
  elif vocab_result and vocab_result.words:
      yield format_vocabulary_chunk(vocab_result.model_dump())
  yield format_section_done("vocabulary")
  ```

**Streaming service (`streaming.py`):**
- Add `format_vocabulary_error(message: str) -> str` function:
  ```python
  def format_vocabulary_error(message: str) -> str:
      return format_sse_event("vocabulary_error", {"message": message, "code": "vocabulary_error"})
  ```

**Frontend state (`use-tutor-stream.ts`):**
- Add `vocabularyError: string | null` to `TutorStreamState` interface.
- Initialize to `null`, reset on new stream start.

**Vocabulary Panel (`vocabulary-panel.tsx`):**
- Add `error?: string | null` prop.
- When `error` is truthy, display an error card instead of the empty state.

**Prop threading:**
- Thread `vocabularyError` through `tabbed-output.tsx`, `desktop-layout.tsx`, and `analysis-view.tsx`.

---

## 5. Acceptance Criteria

### AC-1: Vocabulary chunk delivered from vocabulary node (REQ-1)

**Given** a text analysis request with valid English text
**When** the vocabulary agent completes successfully
**Then** a `vocabulary_chunk` SSE event is emitted with the vocabulary data
**And** the data originates from the vocabulary node's `on_chain_end` event (not the aggregator)

### AC-2: Vocabulary done event emitted (REQ-2)

**Given** a text analysis request
**When** the vocabulary node completes processing (success or failure)
**Then** a `vocabulary_done` SSE event is emitted
**And** on the frontend, `vocabularyStreaming` transitions to `false`

### AC-3: Error propagation instead of silent swallow (REQ-3)

**Given** the vocabulary LLM invocation throws an exception
**When** the exception is caught in `vocabulary_node`
**Then** the returned state contains `vocabulary_error` with the error message
**And** a `vocabulary_error` SSE event is emitted to the frontend
**And** a `vocabulary_done` SSE event is emitted after the error event

### AC-4: Frontend error display (REQ-4)

**Given** the frontend receives a `vocabulary_error` SSE event
**When** the vocabulary panel renders
**Then** a user-friendly error message is displayed
**And** the loading skeleton is not shown
**And** the empty state message is not shown

### AC-5: Reading and grammar regression prevention (REQ-5)

**Given** the SSE streaming pipeline changes are applied
**When** a text analysis request is processed
**Then** `reading_token`, `reading_done`, `grammar_token`, and `grammar_done` events behave identically to the pre-change behavior
**And** all existing reading/grammar tests pass without modification

### AC-6: Aggregator fallback preserved (C3)

**Given** the vocabulary node's `on_chain_end` event is not received (edge case)
**When** the aggregator's `on_chain_end` event contains vocabulary data
**Then** the system falls back to extracting vocabulary from the aggregator output
**And** a `vocabulary_chunk` SSE event is still emitted

---

## 6. Technical Approach

### 6.1 Implementation Order

| Priority | Change | Files Modified | Risk |
|----------|--------|---------------|------|
| Primary Goal | Direct vocabulary_chunk from vocabulary node | `tutor.py` | Low - additive handler |
| Primary Goal | Add vocabulary_done event | `tutor.py`, `use-tutor-stream.ts` | Low - follows existing pattern |
| Primary Goal | Explicit error propagation | `vocabulary.py`, `state.py`, `streaming.py`, `tutor.py`, `use-tutor-stream.ts`, `vocabulary-panel.tsx` | Medium - cross-stack change |
| Secondary Goal | Prop threading for error state | `tabbed-output.tsx`, `desktop-layout.tsx`, `analysis-view.tsx` | Low - mechanical change |

### 6.2 Testing Strategy

**Backend unit tests:**
- Test vocabulary node returns `vocabulary_error` on LLM failure
- Test `format_vocabulary_error` produces correct SSE format
- Test `_stream_graph_events` emits `vocabulary_chunk` on vocabulary node `on_chain_end`
- Test `_stream_graph_events` emits `vocabulary_done` after vocabulary completion
- Test `_stream_graph_events` emits `vocabulary_error` when error present in output
- Test aggregator fallback still works

**Frontend unit tests:**
- Test `useTutorStream` handles `vocabulary_done` event
- Test `useTutorStream` handles `vocabulary_error` event
- Test `VocabularyPanel` renders error state
- Test `VocabularyPanel` renders loading state during streaming
- Test `VocabularyPanel` renders empty state when no data and not streaming

**Integration tests (manual):**
- Submit text that triggers vocabulary analysis and verify panel populates
- Simulate vocabulary LLM failure and verify error message appears
- Verify reading and grammar panels still work correctly

---

## 7. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| `on_chain_end` output structure for vocabulary node differs from expected `{"vocabulary_result": VocabularyResult}` | Medium | High - vocabulary data still lost | Add debug logging in implementation; test with actual LangGraph event capture |
| Race condition between `vocabulary_done` and `done` events | Low | Low - frontend handles both | `done` event already sets all streaming flags to false; `vocabulary_done` is redundant but safe |
| Breaking change in vocabulary_panel prop interface | Low | Medium - TypeScript compilation error | Thread error prop through all parent components |
| Aggregator fallback sends duplicate vocabulary_chunk | Low | Low - frontend replaces vocabulary state | Frontend `setState` with `vocabularyWords: data.words` is idempotent |

---

## 8. Out of Scope

- Token-level streaming for vocabulary (vocabulary produces structured batch data, not streamable prose)
- Changes to the LangGraph graph structure or node execution order
- Vocabulary agent prompt or model changes
- Chat endpoint modifications
- New UI/UX designs for the vocabulary panel beyond error state display

---

## 9. Implementation Notes

**Completed**: 2026-02-26
**Commit**: `5b4edd1` on `main`

### Summary

All 5 requirements (REQ-1 through REQ-5) and all 6 acceptance criteria (AC-1 through AC-6) were implemented as specified with no scope changes.

### Files Modified (13)

**Backend (6 files):**
- `state.py`: Added `vocabulary_error: NotRequired[str | None]` field
- `vocabulary.py`: Changed except block to return `vocabulary_error` instead of silent swallow
- `streaming.py`: Added `format_vocabulary_error()` function
- `tutor.py`: Added `vocabulary` node `on_chain_end` handler with error/chunk/done emission
- `test_agents.py`: Added vocabulary error propagation test
- `test_services.py`: Added vocabulary error SSE format test

**Frontend (7 files):**
- `use-tutor-stream.ts`: Added `vocabularyError` state, `vocabulary_done` and `vocabulary_error` handlers
- `vocabulary-panel.tsx`: Added error prop and error state rendering
- `tabbed-output.tsx`: Added `vocabularyError` prop threading
- `desktop-layout.tsx`: Added `vocabularyError` prop threading
- `analysis-view.tsx`: Added `vocabularyError` prop threading
- `use-tutor-stream.test.ts`: Added vocabulary_done and vocabulary_error event tests
- `vocabulary-panel.test.tsx`: Added error rendering tests

### Quality Results

- Backend: 238 tests passed, 94% coverage
- Frontend: 107 tests passed, 20 test files
- TypeScript: 0 errors
- ESLint: 0 errors
- No breaking changes, fully backward compatible
