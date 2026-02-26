# SPEC-VOCAB-002: Vocabulary Agent Batch-to-Streaming 전환

| Field     | Value                                                      |
|-----------|------------------------------------------------------------|
| SPEC ID   | SPEC-VOCAB-002                                             |
| Title     | Vocabulary Agent Batch-to-Streaming Migration              |
| Created   | 2026-02-26                                                 |
| Status    | Planned                                                    |
| Priority  | High                                                       |
| Lifecycle | spec-first                                                 |
| Tags      | `vocabulary`, `streaming`, `sse`, `proxy-timeout`, `astream` |
| Related   | SPEC-VOCAB-001 (Completed - SSE routing fix)               |

---

## 1. Environment

### 1.1 시스템 컨텍스트

AI English Tutor 애플리케이션은 LangGraph 멀티 에이전트 파이프라인을 사용하여 reading, grammar, vocabulary 세 에이전트를 병렬 실행한다. SPEC-VOCAB-001에서 vocabulary는 LangGraph 0.3.34 FuturesDict weakref GC 버그를 우회하기 위해 LangGraph 그래프 외부에서 `asyncio.Task`로 실행되도록 변경되었다.

현재 reading과 grammar 에이전트는 `llm.astream()` 기반 토큰 레벨 스트리밍을 사용하여 `reading_token`/`grammar_token` SSE 이벤트를 실시간으로 전송한다. 반면 vocabulary 에이전트는 `llm.ainvoke()` (배치) 방식으로 모든 토큰 생성이 완료될 때까지 블로킹한 후 한 번에 `vocabulary_chunk` 이벤트를 전송한다.

### 1.2 아키텍처 개요

```
[Frontend] <--SSE-- [FastAPI Router] <--astream_events-- [LangGraph]
                       tutor.py                            graph.py
                         |                                    |
                    vocabulary_task              +-----------+----------+
                    (asyncio.Task)               |           |          |
                    vocabulary.py              reading   grammar   supervisor
                         |                       |           |
                    ainvoke() <-- 문제!       astream()   astream()
                    (30-60초 블로킹)         (토큰 스트리밍) (토큰 스트리밍)
```

### 1.3 현재 SSE 이벤트 플로우

| Agent      | 토큰 스트리밍          | Section Done     | Batch Chunk        |
|------------|----------------------|------------------|--------------------|
| reading    | `reading_token`      | `reading_done`   | `reading_chunk`    |
| grammar    | `grammar_token`      | `grammar_done`   | `grammar_chunk`    |
| vocabulary | **(없음 - 배치 전용)** | `vocabulary_done`| `vocabulary_chunk` |

### 1.4 근본 원인 (Root Cause)

`backend/src/tutor/agents/vocabulary.py` 126번째 줄:

```python
response = await llm.ainvoke(prompt)  # 모든 토큰 생성 완료까지 30-60초 블로킹
```

**문제 메커니즘:**

1. `ainvoke()`는 LLM이 모든 토큰을 생성할 때까지 대기한다 (다수 단어 어원 설명 시 30-60초)
2. 이 대기 시간 동안 SSE 연결에는 heartbeat 코멘트(`: heartbeat\n\n`)만 5초마다 전송된다
3. Railway/Nginx 리버스 프록시는 실제 `data:` 이벤트가 없는 SSE 연결을 일정 시간 후 끊는다
4. 결과적으로 vocabulary 출력이 잘리거나 아예 수신되지 않는다

**reading/grammar가 정상 작동하는 이유:**

reading과 grammar는 LangGraph 내부에서 `astream_events`를 통해 토큰을 스트리밍하므로, 매 토큰마다 실제 `data:` 이벤트가 전송되어 프록시가 연결을 유지한다.

### 1.5 영향 파일

**Backend:**

| 파일 | 역할 | 변경 범위 |
|------|------|----------|
| `backend/src/tutor/agents/vocabulary.py` | vocabulary_node() 함수 | `ainvoke` -> `astream` + Queue 토큰 전달 |
| `backend/src/tutor/routers/tutor.py` | `_stream_graph_events()` | vocabulary 토큰 스트리밍 루프 추가 |
| `backend/src/tutor/services/streaming.py` | SSE 포맷 함수 | `format_vocabulary_token()` 추가 |

**Frontend:**

| 파일 | 역할 | 변경 범위 |
|------|------|----------|
| `src/hooks/use-tutor-stream.ts` | SSE 이벤트 파서 | `vocabulary_token` 핸들러 추가 |
| `src/components/tutor/vocabulary-panel.tsx` | vocabulary 표시 컴포넌트 | 스트리밍 중 raw 텍스트 표시 (선택적) |

---

## 2. Assumptions

### 2.1 검증된 가정

| # | 가정 | 신뢰도 | 근거 |
|---|------|--------|------|
| A1 | `llm.ainvoke(prompt)`가 30-60초 블로킹되어 프록시 타임아웃을 유발한다 | High | 프로덕션 로그에서 vocabulary 출력 잘림 현상 확인. heartbeat 코멘트만으로는 프록시가 연결을 유지하지 않는다. |
| A2 | `langchain-anthropic`의 `ChatAnthropic.astream(prompt)`가 reading/grammar와 동일하게 토큰 단위 `AIMessageChunk`를 yield한다 | High | reading/grammar에서 동일 패턴(`on_chat_model_stream`)이 정상 동작 중. LangChain의 `BaseChatModel.astream()`은 모든 구현체에서 동일한 인터페이스를 제공한다. |
| A3 | vocabulary가 LangGraph 그래프 외부 asyncio.Task로 실행되므로 `astream_events`를 통한 토큰 전달이 불가능하다 | High | SPEC-VOCAB-001에서 FuturesDict GC 버그 우회를 위해 의도적으로 그래프 외부로 분리. 다시 그래프에 넣으면 동일 버그 재발. |
| A4 | `asyncio.Queue`를 통해 vocabulary_node에서 router로 토큰을 전달할 수 있다 | High | Python asyncio.Queue는 코루틴 간 안전한 데이터 전달을 보장하며, 같은 이벤트 루프 내에서 동작한다. |
| A5 | `_parse_vocabulary_words()`는 전체 누적 텍스트를 대상으로 호출해야 하므로 스트리밍 완료 후 파싱이 필요하다 | High | 파서가 `## word` 헤더 기반 분할을 수행하므로 부분 텍스트로는 정확한 파싱이 불가능하다. |

### 2.2 미검증 가정

| # | 가정 | 신뢰도 | 틀릴 경우 영향 |
|---|------|--------|---------------|
| A6 | Railway 프록시의 SSE 타임아웃 임계값이 실제 `data:` 이벤트 부재 기준이다 (heartbeat 코멘트 불인정) | Medium | 만약 heartbeat 코멘트도 인정한다면 근본 원인이 다를 수 있다. 단, 프로덕션에서 vocabulary만 잘리는 현상은 이 가정과 일치한다. |
| A7 | `astream()`의 첫 토큰 도달까지의 TTFT (Time To First Token)가 프록시 타임아웃보다 짧다 | Medium | TTFT가 너무 길면 첫 토큰 전 연결이 끊길 수 있다. 일반적으로 LLM TTFT는 1-3초이므로 문제없을 것으로 예상. |

---

## 3. Requirements

### 3.1 핵심 요구사항 (EARS Format)

**REQ-1: Vocabulary 토큰 레벨 스트리밍 (Event-Driven)**

> **WHEN** vocabulary 에이전트가 LLM에서 토큰을 수신할 때마다, 시스템은 해당 토큰을 `vocabulary_token` SSE 이벤트로 **즉시** 전송**해야 한다**.

- 근거: 실제 `data:` 이벤트가 지속적으로 전송되어야 Railway/Nginx 프록시가 SSE 연결을 유지한다.
- 대상 파일: `vocabulary.py`, `tutor.py`, `streaming.py`
- 기존 패턴: `reading_token`, `grammar_token` 이벤트와 동일한 방식

**REQ-2: asyncio.Queue 기반 토큰 전달 (State-Driven)**

> **IF** vocabulary가 LangGraph 그래프 외부 asyncio.Task로 실행되는 상태라면, 시스템은 `asyncio.Queue`를 통해 vocabulary_node에서 라우터로 토큰을 전달**해야 한다**.

- 근거: vocabulary는 FuturesDict GC 버그 우회를 위해 그래프 외부에서 실행되므로 `astream_events`를 사용할 수 없다. `asyncio.Queue`가 코루틴 간 안전한 데이터 채널 역할을 한다.
- 대상 파일: `vocabulary.py` (Queue에 토큰 put), `tutor.py` (Queue에서 토큰 get)

**REQ-3: 스트리밍 완료 후 구조화된 결과 전송 (Event-Driven)**

> **WHEN** vocabulary LLM 스트리밍이 완료되면, 시스템은 누적된 전체 텍스트를 파싱하여 기존과 동일한 `vocabulary_chunk` SSE 이벤트로 구조화된 결과(단어 배열)를 전송**해야 한다**.

- 근거: `vocabulary_token`은 raw 텍스트 조각이므로 프론트엔드가 최종적으로 구조화된 단어 데이터를 필요로 한다. 기존 `vocabulary_chunk` 핸들러와의 호환성을 유지한다.
- 대상 파일: `tutor.py` (스트리밍 완료 후 vocabulary_chunk 전송)

**REQ-4: 프론트엔드 vocabulary_token 처리 (Event-Driven)**

> **WHEN** 프론트엔드가 `vocabulary_token` SSE 이벤트를 수신하면, 시스템은 토큰을 누적 버퍼에 추가**해야 한다**.

- 근거: 토큰을 누적함으로써 스트리밍 중에도 진행 상태를 표시할 수 있으며, `vocabulary_chunk`가 도착하면 최종 구조화된 데이터로 전환한다.
- 대상 파일: `src/hooks/use-tutor-stream.ts`

**REQ-5: LangGraph 그래프 외부 유지 (Unwanted Behavior)**

> 시스템은 vocabulary 에이전트를 LangGraph `Send()` dispatch에 다시 넣**지 않아야 한다**.

- 근거: LangGraph 0.3.34의 FuturesDict weakref GC 버그가 존재하며, vocabulary(가장 느린 병렬 노드)가 그래프 내에서 실행되면 TypeError가 발생한다. SPEC-VOCAB-001에서 의도적으로 분리한 구조이다.

**REQ-6: 기존 이벤트 플로우 유지 (Ubiquitous)**

> `vocabulary_done`, `vocabulary_error`, `vocabulary_chunk` 이벤트의 기존 동작은 변경 없이 **항상** 유지**되어야 한다**. reading과 grammar의 SSE 스트리밍 동작도 영향 받지 않아야 한다.

- 근거: SPEC-VOCAB-001에서 구현한 이벤트 플로우가 정상 작동 중이며, 이번 변경은 `vocabulary_token` 이벤트를 추가하는 것이지 기존 이벤트를 변경하는 것이 아니다.

### 3.2 제약사항

| ID | 제약사항 | 유형 |
|----|---------|------|
| C1 | vocabulary는 LangGraph 그래프 외부 `asyncio.Task`로 유지해야 한다 (FuturesDict GC 버그 우회) | Architectural |
| C2 | SSE 이벤트 형식은 기존 프론트엔드 파서와 호환되어야 한다 (`event:` + `data:` 라인 형식) | Technical |
| C3 | `_parse_vocabulary_words()` 파서는 변경하지 않는다. 전체 누적 텍스트를 대상으로 호출한다 | Technical |
| C4 | 데이터베이스 마이그레이션이나 설정 파일 변경 없이 구현한다 | Operational |
| C5 | LangGraph 버전을 변경하지 않는다 | Technical |

---

## 4. Specifications

### 4.1 변경 1: vocabulary_node에 astream + Queue 토큰 전달

**대상:** `backend/src/tutor/agents/vocabulary.py` (`vocabulary_node` 함수)

**현재 동작 (126번째 줄):**

```python
response = await llm.ainvoke(prompt)
content = response.content if hasattr(response, "content") else str(response)
```

**목표 동작:**

```python
async def vocabulary_node(state: TutorState, token_queue: asyncio.Queue | None = None) -> dict:
    ...
    try:
        accumulated = ""
        async for chunk in llm.astream(prompt):
            token = chunk.content if hasattr(chunk, "content") else str(chunk)
            if token:
                accumulated += token
                if token_queue is not None:
                    await token_queue.put(token)

        if token_queue is not None:
            await token_queue.put(None)  # sentinel: 스트리밍 완료

        content = normalize_vocabulary_output(accumulated)
        words = _parse_vocabulary_words(content)
        return {"vocabulary_result": VocabularyResult(words=words)}
    except Exception as e:
        logger.error(f"Error in vocabulary_node: {e}")
        if token_queue is not None:
            await token_queue.put(None)  # sentinel: 에러 시에도 전송
        return {
            "vocabulary_result": VocabularyResult(words=[]),
            "vocabulary_error": str(e),
        }
```

**핵심 설계 결정:**

- `token_queue` 파라미터를 선택적으로 받아 기존 인터페이스와 하위 호환성 유지
- `None` sentinel으로 스트리밍 완료를 신호
- 에러 발생 시에도 sentinel을 전송하여 라우터의 Queue 읽기 루프가 종료되도록 보장
- 반환값 구조(`dict` with `vocabulary_result` 키)는 변경 없음

### 4.2 변경 2: SSE 포맷 함수 추가

**대상:** `backend/src/tutor/services/streaming.py`

**추가:**

```python
def format_vocabulary_token(token: str) -> str:
    """Format a single vocabulary token as SSE event."""
    return format_sse_event("vocabulary_token", {"token": token})
```

`format_reading_token`, `format_grammar_token`과 동일한 패턴.

### 4.3 변경 3: 라우터의 vocabulary 처리 스트리밍 전환

**대상:** `backend/src/tutor/routers/tutor.py` (`_stream_graph_events` 함수)

**현재 동작 (64-135번째 줄):**

1. supervisor `on_chain_end` 시 `vocabulary_task = asyncio.create_task(vocabulary_node(vocab_state))` 생성
2. 그래프 스트리밍 완료 후 vocabulary_task 대기 (heartbeat 루프)
3. task 완료 시 `vocabulary_chunk`/`vocabulary_error` + `vocabulary_done` 전송

**목표 동작:**

1. supervisor `on_chain_end` 시 `vocab_queue = asyncio.Queue()` 생성 후 `vocabulary_task = asyncio.create_task(vocabulary_node(vocab_state, token_queue=vocab_queue))` 생성
2. 그래프 스트리밍 완료 후 vocab_queue에서 토큰을 읽으며 `vocabulary_token` SSE 이벤트 전송
3. Queue에서 `None` sentinel 수신 시 토큰 스트리밍 종료
4. task 완료 대기 후 `vocabulary_chunk`/`vocabulary_error` + `vocabulary_done` 전송

**변경 코드 패턴:**

```python
# 변경 전 (heartbeat 루프):
while not vocabulary_task.done():
    try:
        await asyncio.wait_for(asyncio.shield(vocabulary_task), timeout=_HEARTBEAT_INTERVAL_SECONDS)
        break
    except asyncio.TimeoutError:
        yield _SSE_HEARTBEAT_COMMENT

# 변경 후 (토큰 스트리밍 루프):
while True:
    try:
        token = await asyncio.wait_for(vocab_queue.get(), timeout=_HEARTBEAT_INTERVAL_SECONDS)
        if token is None:  # sentinel
            break
        yield format_vocabulary_token(token)
    except asyncio.TimeoutError:
        # Queue에서 토큰이 일정 시간 오지 않으면 heartbeat 전송
        if vocabulary_task.done():
            break
        yield _SSE_HEARTBEAT_COMMENT
```

**이후 기존 결과 전송 로직은 동일:**

```python
vocab_result = await vocabulary_task
# vocabulary_error/vocabulary_chunk/vocabulary_done 전송 (기존 코드 유지)
```

### 4.4 변경 4: 프론트엔드 vocabulary_token 핸들러

**대상:** `src/hooks/use-tutor-stream.ts`

**추가 상태:**

- `vocabularyRawContent: string` - 토큰 누적 버퍼 (TutorStreamState에 추가)
- 초기값: `""`, 새 스트림 시작 시 리셋

**추가 이벤트 핸들러:**

```typescript
else if (currentEvent === "vocabulary_token") {
  setState((prev) => ({
    ...prev,
    vocabularyRawContent: prev.vocabularyRawContent + (data.token || ""),
  }));
}
```

**기존 핸들러 유지:**

- `vocabulary_chunk`: `vocabularyWords` 설정 + `vocabularyStreaming: false`
- `vocabulary_done`: `vocabularyStreaming: false`
- `vocabulary_error`: 에러 처리

### 4.5 변경 5: Vocabulary Panel 스트리밍 표시 (선택적 개선)

**대상:** `src/components/tutor/vocabulary-panel.tsx`

**현재 동작:**

- `isStreaming && 데이터 없음` -> loading skeleton 표시

**목표 동작 (선택적):**

- `isStreaming && vocabularyRawContent 있음` -> raw Markdown 텍스트를 실시간 표시
- `vocabularyWords 있음` -> 기존 구조화된 단어별 표시 (최종 결과)

이 변경은 선택적이다. 최소 구현에서는 skeleton을 유지하되, SSE 연결이 실제 `data:` 이벤트로 유지되는 것이 핵심이다.

---

## 5. Traceability

| Requirement | Specification | Acceptance Criteria |
|-------------|---------------|---------------------|
| REQ-1       | 4.1, 4.2, 4.3 | AC-1                |
| REQ-2       | 4.1, 4.3      | AC-2                |
| REQ-3       | 4.3           | AC-3                |
| REQ-4       | 4.4           | AC-4                |
| REQ-5       | 4.1 (note)    | AC-5                |
| REQ-6       | All           | AC-6                |
