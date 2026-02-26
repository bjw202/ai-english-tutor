# SPEC-VOCAB-003: Implementation Plan

| Field   | Value          |
|---------|----------------|
| SPEC ID | SPEC-VOCAB-003 |
| Phase   | Plan           |

---

## 1. Strategy Overview

SPEC-VOCAB-002에서 vocabulary에 적용한 `astream()` + `asyncio.Queue` 패턴을 reading과 grammar에도 동일하게 적용하고, analyze flow 전체를 LangGraph에서 분리하여 `asyncio.gather()` 기반 직접 병렬 실행으로 전환한다.

**Core Principle**: vocabulary_node의 현재 구현이 target pattern이다. reading_node와 grammar_node를 이 패턴에 맞추고, 라우터에서 3개 Queue를 인터리빙 머지하는 것이 핵심이다.

**Approach**: Bottom-up (agent layer -> router layer -> graph layer -> frontend)

---

## 2. Milestones

### Milestone 1: Reading/Grammar Agent astream() Conversion (Primary Goal)

**Scope**: `reading.py`, `grammar.py`

**Tasks:**

1. `reading.py`: `import asyncio` 추가
2. `reading_node()` signature에 `token_queue: asyncio.Queue | None = None` parameter 추가
3. `ainvoke()` -> `astream()` loop 교체 (vocabulary_node과 동일 패턴)
4. Token accumulation + Queue put + None sentinel 구현
5. Error handling에서 None sentinel 전송 + `reading_error` key 반환
6. `grammar.py`: reading과 동일 패턴 적용

**Validation:**
- `reading_node(state, token_queue=queue)` 호출 시 Queue에 토큰이 순서대로 도착하고 None sentinel로 종료
- `reading_node(state)` 호출 시 (token_queue=None) 기존과 동일하게 동작 (하위 호환)
- 에러 발생 시 Queue에 None sentinel 전송 후 `reading_error` key 반환

### Milestone 2: Router New Streaming Architecture (Primary Goal)

**Scope**: `tutor.py`

**Tasks:**

1. `_merge_agent_streams()` 함수 구현
   - 3개 Queue에서 `asyncio.wait(FIRST_COMPLETED)` 기반 토큰 머지
   - active set 관리 (None sentinel 수신 시 제거)
   - heartbeat timeout 처리

2. `_stream_analyze_events()` 함수 구현
   - supervisor_node 직접 await 호출
   - 3개 Queue + Task 생성
   - `_merge_agent_streams()` 호출하여 토큰 스트리밍
   - `asyncio.gather(return_exceptions=True)` 결과 처리
   - section_done + vocabulary_chunk + done 이벤트 전송

3. `_stream_graph_events()` 수정
   - analyze flow에서 `_stream_analyze_events()`로 위임
   - image_process/chat flow는 기존 LangGraph 경로 유지

**Validation:**
- 3개 에이전트 토큰이 도착 순서대로 인터리빙되어 단일 SSE 스트림으로 머지
- 개별 에이전트 실패 시 나머지 에이전트 스트리밍 계속
- heartbeat가 timeout 시 정상 전송

### Milestone 3: Graph.py Modification (Secondary Goal)

**Scope**: `graph.py`

**Tasks:**

1. `route_by_task()`에서 analyze 분기: `Send("reading")`, `Send("grammar")` 제거, 빈 리스트 반환
2. `create_graph()`에서 reading/grammar node 및 관련 edge 제거
3. aggregator_node가 chat/image_process flow에서 필요한지 확인
   - chat flow: `graph.ainvoke()` 사용하므로 aggregator 경유 여부 확인
   - image_process flow: `route_after_image()` -> supervisor -> `route_by_task()` -> analyze (빈 리스트 반환됨) 경로 확인 필요

**Important**: image_process flow가 supervisor를 거쳐 다시 analyze로 라우팅되는 경우, 빈 리스트를 반환하면 aggregator에 도달하지 않는다. image_process flow에 대한 별도 처리가 필요할 수 있다.

**Validation:**
- chat flow 정상 동작
- image_process flow 정상 동작 (OCR -> supervisor -> analyze 재라우팅 포함)

### Milestone 4: Aggregator Evaluation (Secondary Goal)

**Scope**: `aggregator.py`

**Tasks:**

1. aggregator_node의 호출 경로 분석
   - analyze flow: 불필요 (직접 asyncio.Task 실행)
   - chat flow: `graph.ainvoke()` 결과로 사용 여부 확인
   - image_process flow: 텍스트 미추출 시 직접 aggregator로 라우팅됨
2. 결정: 유지 또는 삭제 (chat/image_process에서 사용 시 유지)

### Milestone 5: SSE Error Event Functions (Secondary Goal)

**Scope**: `streaming.py`

**Tasks:**

1. `format_reading_error(message: str) -> str` 추가
2. `format_grammar_error(message: str) -> str` 추가
3. `tutor.py`에서 import 추가

**Validation:**
- `format_reading_error("test")` 가 `'event: reading_error\ndata: {"message": "test", "code": "reading_error"}\n\n'` 반환

### Milestone 6: Frontend Error Handlers (Final Goal)

**Scope**: `use-tutor-stream.ts`

**Tasks:**

1. `TutorStreamState` interface에 `readingError: string | null`, `grammarError: string | null` 추가
2. 초기 state와 reset에 새 필드 추가
3. SSE parser에 `reading_error`, `grammar_error` 이벤트 핸들러 추가
4. 기존 `done` 이벤트 핸들러에 error state 초기화 불필요 (done은 전체 스트림 종료이므로)

**Validation:**
- `reading_error` 이벤트 수신 시 `readingStreaming: false`, `readingError: message` 설정
- `grammar_error` 이벤트 수신 시 `grammarStreaming: false`, `grammarError: message` 설정

### Milestone 7: Tests (Final Goal)

**Scope**: `test_agents.py`, `test_graph.py`, frontend tests

**Backend Tests:**

1. `test_agents.py`: reading_node token_queue 테스트 (3-pattern)
   - Test 1: token_queue=None일 때 기존과 동일 동작
   - Test 2: token_queue에 토큰이 순서대로 전달되고 None sentinel로 종료
   - Test 3: 에러 발생 시 None sentinel 전송
2. `test_agents.py`: grammar_node 동일 3-pattern 테스트
3. `test_graph.py`: 변경된 그래프 구조 테스트
   - analyze 분기에서 빈 리스트 반환 확인
   - chat/image_process 분기 동작 확인

**Frontend Tests:**

4. `use-tutor-stream.test.ts`: reading_error/grammar_error 이벤트 핸들링 테스트

---

## 3. Technical Approach

### 3.1 Agent Layer Pattern (reading.py, grammar.py)

vocabulary_node의 현재 구현을 그대로 복제하는 것이 핵심이다:

```python
# Target pattern (from vocabulary_node):
async def agent_node(state: TutorState, token_queue: asyncio.Queue | None = None) -> dict:
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
            await token_queue.put(None)  # sentinel

        content = normalize_output(accumulated)
        return {"result": Result(content=content)}
    except Exception as e:
        if token_queue is not None:
            await token_queue.put(None)  # sentinel on error
        return {"result": None, "error": str(e)}
```

### 3.2 Token Merge Algorithm

`_merge_agent_streams()`의 핵심 알고리즘:

```
INIT:
  queues = {reading: Q1, grammar: Q2, vocabulary: Q3}
  active = {reading, grammar, vocabulary}

LOOP while active is not empty:
  create get_task for each active agent
  wait(get_tasks, timeout=5s, FIRST_COMPLETED)

  IF timeout (no done tasks):
    yield heartbeat
    cancel pending tasks
    continue

  FOR each done task:
    identify agent_name from task
    token = task.result()
    IF token is None:
      remove agent_name from active
    ELSE:
      yield formatter[agent_name](token)

  cancel pending tasks
```

### 3.3 Supervisor Direct Call Strategy

현재 supervisor_node는 LangGraph graph의 첫 번째 노드로 실행된다. analyze flow에서는 이를 직접 호출로 전환:

```python
# Direct call (no LangGraph):
supervisor_result = await supervisor_node(cast(TutorState, input_state))
supervisor_analysis = supervisor_result.get("supervisor_analysis")
```

supervisor_node 함수 자체는 변경하지 않는다. TutorState dict를 받아 dict를 반환하는 순수 함수이므로 직접 호출이 가능하다.

### 3.4 Image Process Flow Consideration

image_process flow는 현재:
1. LangGraph `image_processor` node 실행
2. `route_after_image()`: 텍스트 추출 시 -> `Send("supervisor", new_state)` (task_type="analyze")
3. supervisor 실행 후 -> `route_by_task()` -> analyze 분기

SPEC-VOCAB-003에서 analyze 분기가 빈 리스트를 반환하면, image_process -> supervisor -> (빈 리스트) 경로가 된다. 이 경우 aggregator에 도달하지 않아 image_process flow가 정상 종료되지 않을 수 있다.

**Solution options:**
- Option A: image_process flow도 직접 asyncio.Task 패턴으로 전환 (큰 범위)
- Option B: image_process에서 supervisor 후 analyze로 재라우팅하는 대신, 라우터에서 직접 처리 (중간 범위)
- Option C: graph.py에서 image_process 후 재라우팅된 analyze만 별도 처리 (최소 범위)

**Recommendation**: Option B - image_process flow의 라우터(`_stream_graph_events`)에서 OCR 후 텍스트를 얻으면 `_stream_analyze_events()`를 호출하는 방식. 이렇게 하면 image_process의 OCR 부분만 LangGraph에 남기고, analyze 부분은 통합 패턴 사용.

---

## 4. Risk Analysis

| Risk | Severity | Likelihood | Mitigation |
|------|----------|------------|------------|
| image_process flow가 analyze 재라우팅 시 동작하지 않음 | High | High | 4.3에서 image_process flow를 명시적으로 처리. OCR 후 `_stream_analyze_events()` 호출. |
| `asyncio.wait()` 기반 머지에서 특정 Queue의 토큰이 지연되어 다른 Queue가 블록됨 | Medium | Low | `asyncio.wait(FIRST_COMPLETED)` + timeout으로 블록 방지. 각 Queue는 독립적. |
| reading/grammar의 `astream()` 호환성 문제 (모델별 차이) | Low | Low | vocabulary에서 이미 검증된 패턴. langchain의 `BaseChatModel.astream()`은 모든 구현체에서 동일. |
| chat flow에서 aggregator 누락으로 인한 오류 | Medium | Medium | chat flow 코드 경로를 사전에 분석하여 aggregator 의존성 확인. 필요 시 유지. |
| 기존 프론트엔드 테스트가 SSE 이벤트 순서 변경으로 실패 | Low | Medium | 기존 이벤트 형식은 불변. 순서만 인터리빙으로 변경되므로 순서 의존 테스트만 수정. |

---

## 5. Out of Scope

- LangGraph 버전 업그레이드
- chat flow 변경
- vocabulary.py 변경 (SPEC-VOCAB-002에서 이미 완료)
- 새로운 프론트엔드 UI 컴포넌트 추가 (에러 표시 UI는 기존 패턴 재사용)
- supervisor_node 함수 자체의 변경
- `_parse_vocabulary_words()` 파서 변경
- 데이터베이스 마이그레이션 또는 설정 파일 변경
- SSE heartbeat 간격 변경

---

## 6. Dependencies

| Dependency | Type | Status |
|-----------|------|--------|
| SPEC-VOCAB-001 (FuturesDict GC bug workaround) | SPEC | Complete |
| SPEC-VOCAB-002 (Vocabulary astream + Queue) | SPEC | Complete |
| vocabulary_node current implementation | Code | Stable, no changes needed |
| LangGraph 0.3.x | Library | Retained for chat/image_process flows |
| langchain-openai, langchain-anthropic | Library | `astream()` interface required |
