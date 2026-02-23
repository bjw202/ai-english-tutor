# AI English Tutor Prompt Redesign - Implementation Plan

## Context

AI English Tutor is a Korean middle school English tutoring app with 3 LLM agents (vocabulary, grammar, reading) orchestrated via LangGraph. Current prompts are English analysis-focused ("Extract vocabulary", "Identify grammar errors") and don't actually tutor. The user has prepared verified Korean tutoring prompts in `my-prompt/` that transform the app into a real tutoring system with etymology networks, structure understanding, and reading training. A new LLM-powered supervisor pre-analysis step is also being introduced.

**Design decisions (confirmed):**
1. No few-shot examples - rules/structure described in detail
2. Grammar/Reading both include slash reading with different focus
3. All prompts in Korean
4. LLM supervisor (Haiku) for sentence splitting + difficulty + focus
5. Vocabulary model: **Sonnet** (upgraded from Haiku for richer Korean etymology)
6. Grammar model: **GPT-4o** (unchanged)
7. Tab labels: **Korean** (독해/문법/어휘)

---

## Phase 0: Foundation - Schema & State

### 0-1. `backend/src/tutor/schemas.py`

Add new schemas, rewrite existing result schemas:

**New:**
- `SentenceEntry(number: int, text: str)`
- `SupervisorAnalysis(sentences, text_difficulty, effective_level, vocabulary_focus, grammar_focus, teaching_notes)`
- `VocabularyWordEntry(term: str, basic_meaning: str)` - replaces old `VocabularyWord`

**Changed:**
- `VocabularyResult` → `words: list[VocabularyWordEntry]` + `content: str` (Korean markdown)
- `GrammarResult` → `sentence_count: int` + `content: str` (Korean markdown)
- `ReadingResult` → `sentence_count: int` + `content: str` (Korean markdown)

**Unchanged:** `AnalyzeRequest`, `AnalyzeImageRequest`, `ChatRequest`, `AnalyzeResponse` (field names same, inner types changed)

### 0-2. `backend/src/tutor/state.py`

Add field: `supervisor_analysis: NotRequired[SupervisorAnalysis | None]`

---

## Phase 1: Prompt Infrastructure

### 1-1. `backend/src/tutor/prompts.py`

Add `format_supervisor_analysis(analysis: SupervisorAnalysis) -> str` helper. Formats structured analysis into readable Korean text for prompt injection. Existing `render_prompt()` and `get_level_instructions()` unchanged.

### 1-2. `backend/src/tutor/prompts/level_instructions.yaml`

Full rewrite in Korean. 5 levels with pedagogical descriptions:
- Level 1 (초등 고학년): Easy etymology only, subject/verb basics, encouraging tone
- Level 2 (중1): Latin/Greek etymology, forms 1-3, Korean grammar terms
- Level 3 (중2-3, default): PIE roots, forms 2-5, "why?" emphasis
- Level 4 (고등): Subjunctive/inversion, exam points
- Level 5 (수능/토익): Academic vocabulary, exam strategy

YAML structure (`levels.N.description`, `levels.N.instructions`) unchanged for `get_level_instructions()` compatibility.

### 1-3. `backend/src/tutor/prompts/supervisor.md`

Full rewrite as Korean pre-analysis prompt. Tasks: sentence splitting, difficulty 1-5, effective_level, vocabulary_focus, grammar_focus, teaching_notes. Variables: `{text}`, `{level}`.

### 1-4. `backend/src/tutor/prompts/vocabulary.md`

Full rewrite based on `my-prompt/vocabulary-prompt.md`. 6-step etymology network structure per word. Variables: `{supervisor_analysis}`, `{text}`, `{level}`, `{effective_level}`, `{level_instructions}`.

### 1-5. `backend/src/tutor/prompts/grammar.md`

Full rewrite based on `my-prompt/grammar-prompt.md`. 4-step structure understanding per sentence. Variables: same as vocabulary.

### 1-6. `backend/src/tutor/prompts/reading.md`

Full rewrite based on `my-prompt/reading-prompt.md`. 4-step reading training per sentence. Variables: same as vocabulary.

---

## Phase 2: Supervisor Agent Upgrade

### 2-1. `backend/src/tutor/agents/supervisor.py`

Full rewrite: pure router → LLM-powered analyzer.

- Model: `claude-haiku-4-5` (cheap/fast pre-analysis)
- Uses `with_structured_output(SupervisorAnalysis)`
- On failure: returns `supervisor_analysis=None` + normal routing (graceful degradation)
- Function changes from sync to async (LangGraph handles both)
- Routing logic preserved: `analyze` → 3 parallel agents, `image_process` → image processor

---

## Phase 3: Tutoring Agent Updates

All 3 agents follow the same pattern:
1. Extract `supervisor_analysis` from state (None-safe)
2. Format via `format_supervisor_analysis()`
3. Pass `supervisor_analysis`, `effective_level` to `render_prompt()`
4. Use new result schema with `content` field

### 3-1. `backend/src/tutor/agents/vocabulary.py`

- Model: **`claude-sonnet-4-5`** (upgraded from Haiku for rich Korean etymology)
- Schema: `VocabularyResult(words, content)`
- Remove: `_parse_vocabulary_from_raw()` fallback, `json_instruction` append

### 3-2. `backend/src/tutor/agents/grammar.py`

- Model: **`gpt-4o`** (unchanged)
- Schema: `GrammarResult(sentence_count, content)`

### 3-3. `backend/src/tutor/agents/reading.py`

- Model: **`claude-sonnet-4-5`** (unchanged)
- Schema: `ReadingResult(sentence_count, content)`

---

## Phase 4: Frontend Types & Hooks

### 4-1. `src/types/tutor.ts`

Rewrite interfaces:
- `VocabularyWordEntry { term, basic_meaning }`
- `VocabularyResult { words: VocabularyWordEntry[], content: string }`
- `GrammarResult { sentence_count: number, content: string }`
- `ReadingResult { sentence_count: number, content: string }`

Remove: `GrammarIssue`, old `VocabularyWord`

### 4-2. `src/hooks/use-tutor-stream.ts`

Unified content extraction: all 3 event types extract `data.content`.
Remove: `formatVocabularyData()` helper.

---

## Phase 5: Frontend Panels & Layouts

### 5-1. `src/components/tutor/reading-panel.tsx`

Single `ReactMarkdown` for `result.content`. Remove: keyPoints list, comprehensionLevel badge.

### 5-2. `src/components/tutor/grammar-panel.tsx`

Single `ReactMarkdown` for `result.content`. Remove: Progress bar, issues list, overallScore.

### 5-3. `src/components/tutor/vocabulary-panel.tsx`

Word badges from `words[]` + `ReactMarkdown` for `content`. Remove: `rawContent` prop, difficulty cards, dual-mode rendering.

### 5-4. `src/components/tutor/tabbed-output.tsx`

Tab labels: "독해" / "문법" / "어휘". Remove: `vocabularyRawContent` prop. Update `hasContent` check to use `content` field. Empty state message in Korean.

### 5-5. `src/components/layout/desktop-layout.tsx`

Simplified mapping:
```
reading: { sentence_count: 0, content: streamState.readingContent }
grammar: { sentence_count: 0, content: streamState.grammarContent }
vocabulary: { words: [], content: streamState.vocabularyContent }
```
Remove: `vocabularyRawContent` prop.

### 5-6. `src/components/mobile/analysis-view.tsx`

Same mapping changes as desktop-layout.

---

## Phase 6: Test Updates

### Backend tests:
- `test_schemas.py`: New schemas (SupervisorAnalysis, SentenceEntry, VocabularyWordEntry) + updated Result schema tests
- `test_agents.py`: Rewrite supervisor tests (async + LLM mock), update mock returns for all 3 agents, add `supervisor_analysis=None` fallback tests
- `test_prompts.py` / `test_prompts_integration.py`: `format_supervisor_analysis()` tests, prompt rendering with new variables

### Frontend tests:
- `tutor.test.ts`: New interface shapes
- `use-tutor-stream.test.ts`: New SSE event format with `content` field, remove `formatVocabularyData` tests
- Panel tests: New mock data, ReactMarkdown assertions

---

## Files NOT Changed

| File | Reason |
|------|--------|
| `backend/src/tutor/graph.py` | Send() pattern unchanged, handles async supervisor transparently |
| `backend/src/tutor/models/llm.py` | `get_llm()` factory reused as-is |
| `backend/src/tutor/agents/aggregator.py` | Passthrough aggregation works with new schemas (same field names) |
| `backend/src/tutor/services/streaming.py` | SSE formatters accept `dict` from `model_dump()`, structure-agnostic |
| `backend/src/tutor/routers/tutor.py` | Uses `model_dump()` serialization, works with any Pydantic model |

---

## Dependency Graph

```
Phase 0: schemas.py, state.py (FOUNDATION)
   ↓
Phase 1: prompts.py, level_instructions.yaml, 4 prompt .md files
   ↓
Phase 2: agents/supervisor.py (depends on schemas + supervisor.md)
   ↓
Phase 3: agents/vocabulary.py, grammar.py, reading.py (depends on supervisor in state + new prompts)
   ↓ (parallel with Phase 3)
Phase 4: types/tutor.ts, use-tutor-stream.ts (frontend, depends only on Phase 0 schema definitions)
   ↓
Phase 5: 6 panel/layout components (depends on Phase 4 types)
   ↓
Phase 6: All test updates
```

Phase 3 (backend agents) and Phase 4 (frontend types) can execute in parallel.

---

## Verification

1. `pytest backend/tests/` - all schema/agent/prompt tests pass
2. `npm test` - all frontend component/hook/type tests pass
3. Supervisor test: Masakichi passage at level 3 → 11 sentences, difficulty 3-4
4. Prompt rendering: no unsubstituted `{variables}` in all 4 prompts
5. E2E: Masakichi passage level 3, compare with `my-prompt/` reference output quality
6. Level variation: levels 1, 3, 5 → explanation depth differs appropriately
7. Cross-agent consistency: all 3 agents use same sentence numbers from supervisor
8. Frontend: ReactMarkdown renders Korean + slashes correctly
9. Error path: supervisor failure → agents produce output without supervisor_analysis
10. Model quality: Sonnet vocabulary etymology richness assessment

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Supervisor adds ~1-2s latency | Haiku is fast; acceptable for quality improvement |
| Korean markdown rendering issues | Test ReactMarkdown with slashes/Korean early |
| Structured output with long Korean content | Simpler schema (content string) is more reliable |
| Vocabulary Sonnet cost increase | Quality tradeoff justified; monitor usage |
| GPT-4o Korean grammar quality | Test and iterate; fallback to Claude if needed |

---

## Summary

**22 production files** modified across 6 phases. Core change: English analysis → Korean tutoring with LLM-powered supervisor pre-analysis. Graph structure, LLM factory, aggregator, streaming service, and router all remain unchanged.
