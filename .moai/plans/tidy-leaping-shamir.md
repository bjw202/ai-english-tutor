# Plan: Token-Level Streaming Implementation

> Based on: `.moai/plans/soft-imagining-tulip.md` (v2 design document)
> Validated against codebase: 2026-02-23

## Context

The backend currently uses `graph.ainvoke()` which waits for all 3 agents (reading, grammar, vocabulary) to complete before sending any SSE events. This results in a "flash" of content instead of progressive token-by-token display. The goal is to implement ChatGPT-like typing effects for reading and grammar sections while keeping vocabulary as batch delivery (structured data).

**Base design**: `soft-imagining-tulip.md` has been validated against the actual codebase. All major assumptions are confirmed correct. Minor corrections are noted below.

---

## Corrections from Codebase Validation

| # | Plan Assumption | Actual | Impact |
|---|----------------|--------|--------|
| 1 | "existing 5 tests" | 6 existing tests | Test count reference only, no code impact |
| 2 | Router accesses `result["vocabulary_result"]` | Confirmed: line 109 in tutor.py | Plan's aggregator-based approach is correct for astream_events |
| 3 | analyze-image uses same ainvoke pattern | Confirmed: line 169, same structure | Both endpoints need identical streaming changes |

---

## Implementation Plan

### Phase 1: Backend (3 files)

**File 1: `backend/src/tutor/models/llm.py`**
- Add `streaming=True` to both ChatOpenAI constructors (lines 63, 77)
- Without this, `astream_events` won't emit `on_chat_model_stream` events

**File 2: `backend/src/tutor/services/streaming.py`**
- Add 3 new functions (keep existing functions unchanged):
  - `format_reading_token(token: str)` -> event type `reading_token`
  - `format_grammar_token(token: str)` -> event type `grammar_token`
  - `format_section_done(section: str)` -> event type `{section}_done`

**File 3: `backend/src/tutor/routers/tutor.py`**
- Add `import asyncio` at top
- Update imports from streaming.py to include new formatters
- Replace `generate()` in both `/tutor/analyze` (line 85) and `/tutor/analyze-image` (line 162):
  - `graph.ainvoke()` -> `graph.astream_events(input_state, version="v2")`
  - Process `on_chat_model_stream` events: route tokens by `metadata["langgraph_node"]`
  - Process `on_chain_end` events: emit section_done by `event["name"]`, extract vocabulary from aggregator
  - Add `asyncio.CancelledError` handling for SSE disconnect
- Extract shared `generate()` logic into helper to avoid duplication between endpoints

**Key event routing logic:**
```
on_chat_model_stream + metadata.langgraph_node == "reading" -> reading_token
on_chat_model_stream + metadata.langgraph_node == "grammar" -> grammar_token
on_chain_end + name == "reading" -> reading_done
on_chain_end + name == "grammar" -> grammar_done
on_chain_end + name == "aggregator" -> vocabulary_chunk (from output.analyze_response.vocabulary)
```

### Phase 2: Frontend State (2 files)

**File 4: `src/types/tutor.ts`**
- Add `SectionStreamingState` interface with 3 boolean flags

**File 5: `src/hooks/use-tutor-stream.ts`**
- Extend `TutorStreamState` with `readingStreaming`, `grammarStreaming`, `vocabularyStreaming`
- Add event handlers for new SSE events:
  - `reading_token`: APPEND to `readingContent` (not replace)
  - `grammar_token`: APPEND to `grammarContent` (not replace)
  - `reading_done`: set `readingStreaming: false`
  - `grammar_done`: set `grammarStreaming: false`
  - `vocabulary_chunk`: set `vocabularyStreaming: false` (existing handler, add flag)
  - `done`: set all streaming flags to false
- Keep old `reading_chunk`/`grammar_chunk` handlers as backward compatibility fallback
- Update `reset()` to clear section streaming flags
- Set all section streaming flags to `true` on stream start

### Phase 3: Frontend Components (4 files)

**File 6: `src/components/tutor/tabbed-output.tsx`**
- Extend `TabbedOutputProps` with streaming flags
- Fix `hasContent`: `isStreaming || reading || grammar || vocabulary`
- Add pulsing dot indicators on tab labels during section streaming
- Pass `isStreaming` prop to each panel component

**File 7: `src/components/tutor/reading-panel.tsx`**
- Add `isStreaming` prop
- Show container even when `result` is null but `isStreaming` is true
- Add blinking cursor during streaming (CSS `animate-pulse`)

**File 8: `src/components/tutor/grammar-panel.tsx`**
- Same pattern as reading-panel

**File 9: `src/components/tutor/vocabulary-panel.tsx`**
- Add `isStreaming` prop
- Show skeleton loading UI when streaming but no result yet

### Phase 4: Props Chain (2 files)

**File 10: `src/components/layout/desktop-layout.tsx`**
- Pass streaming flags from `streamState` to `TabbedOutput` (line 89-105)

**File 11: `src/components/mobile/analysis-view.tsx`**
- Pass streaming flags from `streamState` to `TabbedOutput` (line 33-49)

### Phase 5: Tests (1 file)

**File 12: `src/hooks/__tests__/use-tutor-stream.test.ts`**
- Keep existing 6 tests unchanged
- Add 6 new tests:
  1. `reading_token` sequential append
  2. `grammar_token` sequential append
  3. `reading_done` sets only readingStreaming to false
  4. `grammar_done` sets only grammarStreaming to false
  5. `vocabulary_chunk` sets vocabularyStreaming to false
  6. Initial state includes section streaming flags as false

---

## Dependency Graph

```
Phase 1 (Backend)
  1a. llm.py ─────────┐
  1b. streaming.py ────┤──> 1c. tutor.py
                       │
Phase 2 (State)        │
  2a. types/tutor.ts ──┤──> 2b. use-tutor-stream.ts
                       │
Phase 3 (Components)   │
  3a. tabbed-output.tsx ──> 3b. reading-panel.tsx
                       │──> 3c. grammar-panel.tsx
                       │──> 3d. vocabulary-panel.tsx
Phase 4 (Props)
  4a. desktop-layout.tsx
  4b. analysis-view.tsx

Phase 5 (Tests)
  5a. use-tutor-stream.test.ts
```

Phases 1-2 are sequential. Phases 3-5 can be parallelized after Phase 2 completes.

---

## Execution Strategy

Per `quality.yaml` (hybrid mode):
- **New code** (streaming formatters, new event handlers, streaming UI): TDD approach
- **Modified code** (tutor.py, use-tutor-stream.ts): DDD approach (ANALYZE-PRESERVE-IMPROVE)

Delegation plan:
- Phase 1 (Backend): `expert-backend` subagent
- Phase 2-4 (Frontend): `expert-frontend` subagent
- Phase 5 (Tests): `expert-testing` subagent or inline with Phase 2

---

## Risk Assessment

| Risk | Mitigation |
|------|-----------|
| GLM API may not support streaming | Test with GLM endpoint; fallback to non-streaming for GLM if needed |
| Interleaved tokens from parallel reading/grammar | Frontend handles independently via separate state fields |
| astream_events event format varies by LangGraph version | Pin LangGraph version; test event structure at runtime |
| Vocabulary node emits partial JSON tokens | Correctly filtered: only reading/grammar tokens are streamed |

---

## Verification

1. **Backend unit**: `cd backend && pytest` (existing tests pass)
2. **Backend manual**: `curl` against `/tutor/analyze` SSE endpoint, verify token events arrive incrementally
3. **Frontend unit**: `pnpm test` (existing 6 + new 6 tests pass)
4. **E2E manual**: Submit text, observe:
   - Reading tab: characters appear one-by-one with blinking cursor
   - Grammar tab: same typing effect
   - Vocabulary tab: skeleton -> batch word cards
   - Tab switching preserves accumulated content
5. **Mobile**: Same verification on mobile layout
