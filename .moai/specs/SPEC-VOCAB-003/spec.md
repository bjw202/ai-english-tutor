# SPEC-VOCAB-003: Unified Streaming Architecture - 3 Agent astream() + asyncio.Queue Unification

| Field     | Value                                                                          |
|-----------|--------------------------------------------------------------------------------|
| SPEC ID   | SPEC-VOCAB-003                                                                 |
| Title     | Unified Streaming Architecture - 3 Agent astream() + asyncio.Queue            |
| Version   | 1.0.0                                                                          |
| Created   | 2026-02-26                                                                     |
| Updated   | 2026-02-26                                                                     |
| Status    | Planned                                                                        |
| Priority  | High                                                                           |
| Author    | jw                                                                             |
| Lifecycle | spec-first                                                                     |
| Tags      | `streaming`, `asyncio`, `astream`, `queue`, `langgraph`, `sse`, `unification` |
| Related   | SPEC-VOCAB-001 (Complete), SPEC-VOCAB-002 (Complete)                          |

---

## HISTORY

| Version | Date       | Author | Description                                              |
|---------|------------|--------|----------------------------------------------------------|
| 1.0.0   | 2026-02-26 | jw     | Initial SPEC - Unified streaming architecture for 3 agents |

---

## 1. Environment

### 1.1 System Context

AI English Tutor is a multi-agent LLM pipeline that runs 3 tutor agents (reading, grammar, vocabulary) in parallel for the `analyze` flow. The system uses FastAPI + LangGraph backend with Next.js frontend, communicating via Server-Sent Events (SSE).

**SPEC-VOCAB-001** (Complete): vocabulary agent was moved outside LangGraph to avoid the FuturesDict weakref GC bug.

**SPEC-VOCAB-002** (Complete): vocabulary agent was switched from `ainvoke()` to `astream()` + `asyncio.Queue` for token-level streaming.

### 1.2 Current Architecture

```
[Frontend] <--SSE-- [FastAPI Router] <--astream_events-- [LangGraph]
                       tutor.py                            graph.py
                         |                                    |
                    vocabulary_task              +-----------+----------+
                    (asyncio.Task)               |           |          |
                    vocabulary.py              reading.py  grammar.py  supervisor.py
                         |                       |           |
                    astream() + Queue        ainvoke()    ainvoke()
                    (token streaming)        (batch)      (batch)
```

**Problem**: reading/grammar are INSIDE LangGraph and use `ainvoke()` (batch mode). Token streaming is achieved indirectly via LangGraph's `astream_events()` intercepting `on_chat_model_stream` events. vocabulary is OUTSIDE LangGraph and uses `astream()` + `asyncio.Queue` directly (SPEC-VOCAB-002 pattern).

**Root Cause Analysis**:

The FuturesDict GC bug was a symptom of a structural problem. If ANY agent (not just vocabulary) is the slowest to complete in LangGraph's parallel `Send()` dispatch, the same bug could occur. The current half-in/half-out architecture is fragile and inconsistent.

### 1.3 Target Architecture

```
supervisor_node() called directly (await, no LangGraph)
          |
          v  supervisor_analysis injected into state
asyncio.gather(
  reading_task   <-- astream() + asyncio.Queue --> reading_token x N  --> reading_done
  grammar_task   <-- astream() + asyncio.Queue --> grammar_token x N  --> grammar_done
  vocab_task     <-- astream() + asyncio.Queue --> vocabulary_token x N --> vocabulary_done + vocabulary_chunk
)
          |
          v
done event
```

ALL 3 agents use the SAME mechanism:
- Each runs as an independent `asyncio.Task`
- Each uses `llm.astream()` directly for token streaming
- Each delivers tokens via `asyncio.Queue` with `None` sentinel
- Coordinated by `asyncio.gather()` in the router
- NO LangGraph parallel `Send()` dispatch for analyze flow

### 1.4 Current Source Code Analysis

**reading_node** (`backend/src/tutor/agents/reading.py:22`):
```python
async def reading_node(state: TutorState) -> dict:
    ...
    response = await llm.ainvoke(prompt)  # batch, NOT astream
    content = response.content if hasattr(response, "content") else str(response)
    content = normalize_reading_output(content)
    return {"reading_result": ReadingResult(content=content)}
```

**grammar_node** (`backend/src/tutor/agents/grammar.py:22`):
```python
async def grammar_node(state: TutorState) -> dict:
    ...
    response = await llm.ainvoke(prompt)  # batch, NOT astream
    content = response.content if hasattr(response, "content") else str(response)
    content = normalize_grammar_output(content)
    return {"grammar_result": GrammarResult(content=content)}
```

**vocabulary_node** (`backend/src/tutor/agents/vocabulary.py:84`):
```python
async def vocabulary_node(state: TutorState, token_queue: asyncio.Queue | None = None) -> dict:
    ...
    accumulated = ""
    async for chunk in llm.astream(prompt):
        ...
        if token_queue is not None:
            await token_queue.put(token)
    if token_queue is not None:
        await token_queue.put(None)  # sentinel
    ...
```

**graph.py route_by_task** (line 49):
```python
if task_type == "analyze":
    return [
        Send("reading", state),
        Send("grammar", state),
    ]  # vocabulary excluded (SPEC-VOCAB-001)
```

### 1.5 SSE Event Contract (12 + 2 new)

| Event              | Type              | Status        | Description                                |
|--------------------|-------------------|---------------|--------------------------------------------|
| `reading_token`    | Token streaming   | Existing      | Reading agent token (per-token)            |
| `grammar_token`    | Token streaming   | Existing      | Grammar agent token (per-token)            |
| `vocabulary_token` | Token streaming   | Existing      | Vocabulary agent token (per-token)         |
| `reading_done`     | Section complete  | Existing      | Reading section finished                   |
| `grammar_done`     | Section complete  | Existing      | Grammar section finished                   |
| `vocabulary_done`  | Section complete  | Existing      | Vocabulary section finished                |
| `vocabulary_chunk` | Structured data   | Existing      | Parsed vocabulary words `{"words":[...]}`  |
| `vocabulary_error` | Error             | Existing      | Vocabulary agent error                     |
| `reading_error`    | Error             | **NEW**       | Reading agent error (isolated failure)     |
| `grammar_error`    | Error             | **NEW**       | Grammar agent error (isolated failure)     |
| `reading_chunk`    | Batch fallback    | Existing      | Full reading content (backward compat)     |
| `grammar_chunk`    | Batch fallback    | Existing      | Full grammar content (backward compat)     |
| `error`            | Global error      | Existing      | Global processing error                    |
| `done`             | Completion        | Existing      | All processing complete                    |

### 1.6 Affected Files

| File | Action | Description |
|------|--------|-------------|
| `backend/src/tutor/agents/reading.py` | Modify | `token_queue` param 추가, `ainvoke` -> `astream`, vocabulary_node과 동일 패턴 |
| `backend/src/tutor/agents/grammar.py` | Modify | reading.py와 동일한 변경 |
| `backend/src/tutor/agents/vocabulary.py` | No change | SPEC-VOCAB-002에서 이미 target 패턴 구현 완료 |
| `backend/src/tutor/routers/tutor.py` | Major rewrite | `_stream_analyze_events()` + `_merge_agent_streams()` 신규, LangGraph graph import 제거 (analyze) |
| `backend/src/tutor/graph.py` | Modify | analyze 분기에서 `Send("reading")`, `Send("grammar")` 제거. chat/image_process 유지. |
| `backend/src/tutor/agents/aggregator.py` | Evaluate | analyze flow에서 불필요. chat flow에서 사용 여부 확인 후 결정. |
| `backend/src/tutor/services/streaming.py` | Modify | `format_reading_error()`, `format_grammar_error()` 추가 |
| `backend/tests/unit/test_agents.py` | Modify | reading/grammar token_queue 테스트 추가 (vocabulary와 동일 3-패턴) |
| `backend/tests/unit/test_graph.py` | Update | 변경된 graph 구조 반영 |
| `src/hooks/use-tutor-stream.ts` | Modify | `reading_error`, `grammar_error` 이벤트 핸들러 추가 |
| `src/hooks/__tests__/use-tutor-stream.test.ts` | Modify | 신규 에러 이벤트 테스트 추가 |

---

## 2. Assumptions

### 2.1 Verified Assumptions

| # | Assumption | Confidence | Evidence |
|---|-----------|-----------|---------|
| A1 | `llm.astream(prompt)`은 reading/grammar 에이전트에서도 vocabulary와 동일하게 토큰 단위 `AIMessageChunk`를 yield한다 | High | vocabulary.py에서 이미 정상 동작 확인. LangChain의 `BaseChatModel.astream()`은 모든 구현체에서 동일한 인터페이스를 제공한다. |
| A2 | `asyncio.Queue` + `asyncio.gather()` 조합으로 3개 에이전트를 안전하게 병렬 실행할 수 있다 | High | vocabulary_node가 이미 asyncio.Task + Queue 패턴으로 정상 동작 중. `asyncio.gather()`는 Python asyncio의 표준 병렬 실행 메커니즘이다. |
| A3 | supervisor_node()는 LangGraph 없이 직접 `await` 호출해도 동일하게 동작한다 | High | supervisor_node는 순수 async 함수이며 LangGraph 상태 관리에 의존하지 않는다. `state: TutorState` dict를 받아 `supervisor_analysis`를 반환하는 독립 함수이다. |
| A4 | `asyncio.wait(FIRST_COMPLETED)` 기반 토큰 머지가 공정하게 동작한다 | High | Python asyncio.wait는 완료된 Future를 반환하므로 도착 순서대로 처리된다. 특정 에이전트에 대한 편향(starvation)이 발생하지 않는다. |
| A5 | LangGraph를 analyze flow에서 제거해도 chat/image_process flow는 영향 없다 | High | `route_by_task()`의 chat/image_process 분기는 reading/grammar와 무관한 독립 경로이다. |
| A6 | reading/grammar의 normalize 함수(`normalize_reading_output`, `normalize_grammar_output`)는 전체 누적 텍스트에 대해 호출 가능하다 | High | 현재 `ainvoke()` 결과의 전체 content에 적용되고 있으므로 동일한 전체 텍스트에 대해 동작한다. |

### 2.2 Unverified Assumptions

| # | Assumption | Confidence | Impact if Wrong |
|---|-----------|-----------|----------------|
| A7 | aggregator_node는 chat flow에서 사용되지 않으므로 삭제 가능하다 | Medium | chat flow가 aggregator를 경유한다면 삭제 시 chat이 동작하지 않을 수 있다. 코드 확인 후 결정 필요. |
| A8 | image_process flow에서 OCR 후 analyze로 재라우팅될 때 새로운 _stream_analyze_events 패턴도 적용해야 할 수 있다 | Medium | image_process -> supervisor -> analyze 재라우팅 시 기존 LangGraph 경로와 신규 asyncio 경로 간 연결이 필요할 수 있다. |

---

## 3. Requirements

### REQ-1: Reading/Grammar astream() Conversion (Event-Driven)

> **WHEN** reading_node 또는 grammar_node가 LLM에서 토큰을 수신할 때마다, 시스템은 해당 토큰을 `token_queue`를 통해 라우터로 즉시 전달**해야 한다**.

- Pattern: vocabulary_node (SPEC-VOCAB-002)와 동일한 `astream()` + `asyncio.Queue` 패턴
- Target files: `reading.py`, `grammar.py`
- Signature change: `async def reading_node(state: TutorState, token_queue: asyncio.Queue | None = None) -> dict:`

### REQ-2: asyncio.gather() Based Parallel Execution (State-Driven)

> **WHILE** analyze 요청이 처리되는 동안, 시스템은 reading_node, grammar_node, vocabulary_node를 `asyncio.gather()`로 동시 실행**해야 하며** LangGraph `Send()` dispatch를 사용하지 않**아야 한다**.

- 3개 에이전트가 각각 독립 `asyncio.Task`로 실행
- 각 Task에 전용 `asyncio.Queue` 할당
- `asyncio.gather()`로 조율

### REQ-3: Supervisor Direct Invocation (Event-Driven)

> **WHEN** analyze 요청이 시작될 때, 시스템은 `supervisor_node()`를 LangGraph 없이 직접 `await` 호출하여 `supervisor_analysis`를 얻고, 이를 3개 에이전트에 전달**해야 한다**.

- supervisor_node는 순수 async 함수로 직접 호출 가능
- 반환된 `supervisor_analysis`를 각 에이전트의 state에 주입

### REQ-4: Independent Agent Failure Handling (Event-Driven)

> **WHEN** reading_node 또는 grammar_node가 예외를 발생시킬 때, 시스템은 `reading_error` 또는 `grammar_error` SSE 이벤트를 전송하고 나머지 에이전트는 계속 스트리밍을 유지**해야 한다**.

- vocabulary_error와 동일한 패턴: `format_reading_error()`, `format_grammar_error()`
- `asyncio.gather(return_exceptions=True)` 사용하여 개별 실패 격리
- 에러 발생 시 해당 Queue에 None sentinel 전송하여 머지 루프가 정상 종료

### REQ-5: Token Interleaving Merge (State-Driven)

> **WHILE** 3개 에이전트가 동시에 스트리밍되는 동안, 시스템은 per-agent `asyncio.Queue`와 `asyncio.wait(FIRST_COMPLETED)`를 사용하여 토큰을 도착 순서대로 단일 SSE 스트림에 머지**해야 한다**.

- 각 에이전트의 Queue에서 `asyncio.create_task(queue.get())`으로 대기
- `asyncio.wait(return_when=FIRST_COMPLETED)`로 가장 먼저 도착한 토큰 처리
- `None` sentinel 수신 시 해당 에이전트를 active set에서 제거
- 모든 에이전트가 완료될 때까지 반복

### REQ-6: LangGraph Partial Retention (Constraint)

> 시스템은 analyze 플로우에서**만** reading/grammar를 LangGraph `Send()` dispatch에서 제거**해야 하며**, chat과 image_process 플로우는 변경하지 않**아야 한다**.

- `graph.py`의 `route_by_task()`에서 analyze 분기 수정
- chat 분기와 image_process 분기는 현재 구조 유지

### REQ-7: vocabulary_chunk Backward Compatibility (Event-Driven)

> **WHEN** vocabulary 스트리밍이 완료된 후, 시스템은 기존과 동일한 `vocabulary_chunk` SSE 이벤트를 전송**해야 한다**.

- `_parse_vocabulary_words()` 호출 및 `vocabulary_chunk` 이벤트 전송 로직 유지
- vocabulary_node의 반환값 구조 변경 없음

### REQ-8: Existing SSE Event Format Immutability (Unwanted Behavior)

> 시스템은 기존 12개 SSE 이벤트의 이름과 데이터 형식을 변경**해서는 안 된다**.

- 모든 기존 이벤트명 및 JSON 페이로드 형식 불변
- 신규 이벤트(`reading_error`, `grammar_error`)만 추가

---

## 4. Specifications

### 4.1 reading.py Changes

**Target:** `backend/src/tutor/agents/reading.py` (`reading_node` function)

**Current signature (line 22):**
```python
async def reading_node(state: TutorState) -> dict:
```

**New signature:**
```python
async def reading_node(state: TutorState, token_queue: asyncio.Queue | None = None) -> dict:
```

**Implementation (vocabulary_node pattern 적용):**

```python
async def reading_node(state: TutorState, token_queue: asyncio.Queue | None = None) -> dict:
    settings = get_settings()
    llm = get_llm(settings.READING_MODEL, max_tokens=6144)

    level = state.get("level", 3)
    input_text = state.get("input_text", "")
    level_instructions = get_level_instructions(level)

    supervisor_analysis = state.get("supervisor_analysis")
    supervisor_context = ""
    if supervisor_analysis:
        supervisor_context = (
            f"\n\n[사전 분석]\n"
            f"전체 난이도: {supervisor_analysis.overall_difficulty}/5\n"
            f"학습 포커스: {', '.join(supervisor_analysis.focus_summary)}"
        )

    prompt = render_prompt(
        "reading.md",
        text=input_text,
        level=level,
        level_instructions=level_instructions,
        supervisor_context=supervisor_context,
    )

    try:
        accumulated = ""
        async for chunk in llm.astream(prompt):
            raw = chunk.content if hasattr(chunk, "content") else ""
            if not isinstance(raw, str):
                continue
            token = raw
            if token:
                accumulated += token
                if token_queue is not None:
                    await token_queue.put(token)

        if token_queue is not None:
            await token_queue.put(None)  # sentinel: streaming complete

        content = normalize_reading_output(accumulated)
        return {"reading_result": ReadingResult(content=content)}
    except Exception as e:
        logger.error(f"Error in reading_node: {e}")
        if token_queue is not None:
            await token_queue.put(None)  # sentinel: ensure consumer loop exits
        return {
            "reading_result": None,
            "reading_error": str(e),
        }
```

**Key changes:**
- `import asyncio` 추가
- `token_queue: asyncio.Queue | None = None` parameter 추가
- `ainvoke()` -> `astream()` + token accumulation
- `None` sentinel on completion and error
- `reading_error` key in return dict on failure

### 4.2 grammar.py Changes

**Target:** `backend/src/tutor/agents/grammar.py` (`grammar_node` function)

reading.py와 완전히 동일한 패턴 적용:
- `token_queue` parameter 추가
- `ainvoke()` -> `astream()` + token accumulation
- `normalize_grammar_output()` on accumulated text
- `grammar_error` key in return dict on failure
- `None` sentinel on completion and error

### 4.3 tutor.py New Architecture

**Target:** `backend/src/tutor/routers/tutor.py`

**Major changes:**

1. **`_stream_analyze_events()` (NEW)**: analyze flow 전용 스트리밍 함수. LangGraph를 사용하지 않음.
2. **`_merge_agent_streams()` (NEW)**: 3개 Queue에서 토큰을 FIRST_COMPLETED 방식으로 머지.
3. **`_stream_graph_events()` 수정**: analyze flow에서 `_stream_analyze_events()`로 위임.

**_stream_analyze_events pseudocode:**

```python
async def _stream_analyze_events(input_state: dict, session_id: str) -> AsyncGenerator[str]:
    # Step 1: Supervisor direct call
    supervisor_result = await supervisor_node(cast(TutorState, input_state))
    supervisor_analysis = supervisor_result.get("supervisor_analysis")
    agent_state = {**input_state, "supervisor_analysis": supervisor_analysis}

    # Step 2: Create queues
    reading_queue = asyncio.Queue()
    grammar_queue = asyncio.Queue()
    vocab_queue = asyncio.Queue()

    # Step 3: Launch 3 agent tasks
    reading_task = asyncio.create_task(
        reading_node(cast(TutorState, agent_state), token_queue=reading_queue)
    )
    grammar_task = asyncio.create_task(
        grammar_node(cast(TutorState, agent_state), token_queue=grammar_queue)
    )
    vocab_task = asyncio.create_task(
        vocabulary_node(cast(TutorState, agent_state), token_queue=vocab_queue)
    )

    # Step 4: Merge streams
    async for sse_event in _merge_agent_streams(reading_queue, grammar_queue, vocab_queue):
        yield sse_event

    # Step 5: Await results and emit final events
    results = await asyncio.gather(reading_task, grammar_task, vocab_task, return_exceptions=True)

    # Process reading result
    if isinstance(results[0], Exception):
        yield format_reading_error(str(results[0]))
    yield format_section_done("reading")

    # Process grammar result
    if isinstance(results[1], Exception):
        yield format_grammar_error(str(results[1]))
    yield format_section_done("grammar")

    # Process vocabulary result
    if isinstance(results[2], Exception):
        yield format_vocabulary_error(str(results[2]))
    else:
        vocab_result = results[2]
        vocabulary_result = vocab_result.get("vocabulary_result")
        vocab_error = vocab_result.get("vocabulary_error")
        if vocab_error:
            yield format_vocabulary_error(vocab_error)
        elif vocabulary_result and hasattr(vocabulary_result, "model_dump"):
            data = vocabulary_result.model_dump()
            if data.get("words"):
                yield format_vocabulary_chunk(data)
    yield format_section_done("vocabulary")

    yield format_done_event(session_id)
```

**_merge_agent_streams pseudocode:**

```python
async def _merge_agent_streams(
    reading_queue: asyncio.Queue,
    grammar_queue: asyncio.Queue,
    vocab_queue: asyncio.Queue,
) -> AsyncGenerator[str]:
    queues = {
        "reading": reading_queue,
        "grammar": grammar_queue,
        "vocabulary": vocab_queue,
    }
    formatters = {
        "reading": format_reading_token,
        "grammar": format_grammar_token,
        "vocabulary": format_vocabulary_token,
    }
    active = set(queues.keys())

    while active:
        get_tasks = {
            name: asyncio.create_task(queues[name].get())
            for name in active
        }

        done, pending = await asyncio.wait(
            get_tasks.values(),
            timeout=_HEARTBEAT_INTERVAL_SECONDS,
            return_when=asyncio.FIRST_COMPLETED,
        )

        if not done:
            # Timeout with no tokens -> heartbeat
            yield _SSE_HEARTBEAT_COMMENT
            for t in pending:
                t.cancel()
            continue

        for task in done:
            agent_name = next(name for name, t in get_tasks.items() if t is task)
            token = task.result()
            if token is None:
                active.discard(agent_name)
            else:
                yield formatters[agent_name](token)

        for t in pending:
            t.cancel()
```

### 4.4 graph.py Changes

**Target:** `backend/src/tutor/graph.py`

**Change in `route_by_task()` (line 75):**

```python
# BEFORE:
if task_type == "analyze":
    return [
        Send("reading", state),
        Send("grammar", state),
    ]

# AFTER:
if task_type == "analyze":
    # Reading, grammar, vocabulary are all handled as direct asyncio.Tasks
    # in the streaming router (SPEC-VOCAB-003). No LangGraph dispatch.
    return []
```

**Change in `create_graph()` (line 96):**

```python
# Remove reading and grammar nodes and edges for analyze flow:
# - Remove: workflow.add_node("reading", reading_node)
# - Remove: workflow.add_node("grammar", grammar_node)
# - Remove: workflow.add_edge("reading", "aggregator")
# - Remove: workflow.add_edge("grammar", "aggregator")
```

Note: supervisor node remains in graph for image_process flow. chat flow and image_process flow are unchanged.

### 4.5 SSE Error Events

**Target:** `backend/src/tutor/services/streaming.py`

**New functions:**

```python
def format_reading_error(message: str) -> str:
    """Format reading error as SSE event."""
    return format_sse_event("reading_error", {"message": message, "code": "reading_error"})


def format_grammar_error(message: str) -> str:
    """Format grammar error as SSE event."""
    return format_sse_event("grammar_error", {"message": message, "code": "grammar_error"})
```

`format_vocabulary_error`와 동일한 패턴.

### 4.6 Frontend Error Handlers

**Target:** `src/hooks/use-tutor-stream.ts`

**New state fields in `TutorStreamState`:**

```typescript
export interface TutorStreamState {
  // ... existing fields ...
  readingError: string | null;   // NEW
  grammarError: string | null;   // NEW
}
```

**New event handlers in SSE parser:**

```typescript
else if (currentEvent === "reading_error") {
  setState((prev) => ({
    ...prev,
    readingStreaming: false,
    readingError: data.message || "Reading analysis failed",
  }));
} else if (currentEvent === "grammar_error") {
  setState((prev) => ({
    ...prev,
    grammarStreaming: false,
    grammarError: data.message || "Grammar analysis failed",
  }));
}
```

---

## 5. Traceability

| Requirement | Specification | Acceptance Criteria |
|-------------|---------------|---------------------|
| REQ-1       | 4.1, 4.2      | AC-1                |
| REQ-2       | 4.3           | AC-2                |
| REQ-3       | 4.3           | AC-3                |
| REQ-4       | 4.3, 4.5, 4.6 | AC-4                |
| REQ-5       | 4.3           | AC-5                |
| REQ-6       | 4.4           | AC-6                |
| REQ-7       | 4.3           | AC-7                |
| REQ-8       | All           | AC-8                |
