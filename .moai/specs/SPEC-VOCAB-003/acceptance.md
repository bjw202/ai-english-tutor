# SPEC-VOCAB-003: Acceptance Criteria

| Field   | Value          |
|---------|----------------|
| SPEC ID | SPEC-VOCAB-003 |
| Phase   | Acceptance     |

---

## 1. Acceptance Criteria (Given/When/Then)

### AC-1: Reading/Grammar astream() Token Streaming (REQ-1)

**Scenario 1: reading_node token streaming via Queue**

```gherkin
Given reading_node가 token_queue 파라미터와 함께 호출된다
When LLM이 "Hello" "World" 두 개의 토큰을 생성한다
Then token_queue에 "Hello", "World" 순서로 put된다
And token_queue에 None sentinel이 마지막으로 put된다
And 반환값에 reading_result가 포함된다
And reading_result.content에 "HelloWorld"가 포함된다
```

**Scenario 2: grammar_node token streaming via Queue**

```gherkin
Given grammar_node가 token_queue 파라미터와 함께 호출된다
When LLM이 토큰을 생성한다
Then token_queue에 토큰이 순서대로 put된다
And token_queue에 None sentinel이 마지막으로 put된다
And 반환값에 grammar_result가 포함된다
```

**Scenario 3: reading_node backward compatibility (token_queue=None)**

```gherkin
Given reading_node가 token_queue 없이 호출된다 (기존 호출 방식)
When LLM이 토큰을 생성한다
Then 반환값에 reading_result가 포함된다
And Queue 관련 에러가 발생하지 않는다
```

**Scenario 4: grammar_node backward compatibility (token_queue=None)**

```gherkin
Given grammar_node가 token_queue 없이 호출된다
When LLM이 토큰을 생성한다
Then 반환값에 grammar_result가 포함된다
And Queue 관련 에러가 발생하지 않는다
```

### AC-2: asyncio.gather() Parallel Execution (REQ-2)

**Scenario 5: Three agents run in parallel**

```gherkin
Given analyze 요청이 수신된다
When _stream_analyze_events()가 실행된다
Then reading_node, grammar_node, vocabulary_node가 asyncio.gather()로 동시 실행된다
And 각 에이전트에 전용 asyncio.Queue가 할당된다
And LangGraph Send() dispatch가 사용되지 않는다
```

**Scenario 6: All three queues receive tokens**

```gherkin
Given 3개 에이전트가 동시 실행 중이다
When 각 에이전트가 LLM 토큰을 생성한다
Then reading_queue, grammar_queue, vocab_queue 각각에 토큰이 도착한다
And 모든 queue에 최종적으로 None sentinel이 도착한다
```

### AC-3: Supervisor Direct Invocation (REQ-3)

**Scenario 7: Supervisor called without LangGraph**

```gherkin
Given analyze 요청이 수신된다
When _stream_analyze_events()가 실행된다
Then supervisor_node()가 await로 직접 호출된다 (LangGraph graph 미사용)
And supervisor_analysis가 반환된다
And supervisor_analysis가 3개 에이전트 state에 주입된다
```

**Scenario 8: Supervisor fallback on error**

```gherkin
Given supervisor_node()의 LLM 호출이 실패한다
When supervisor_node()가 직접 호출된다
Then fallback analysis가 반환된다 (period 기반 문장 분리)
And 3개 에이전트가 fallback analysis를 사용하여 정상 실행된다
```

### AC-4: Independent Agent Failure Handling (REQ-4)

**Scenario 9: Reading agent fails, others continue**

```gherkin
Given 3개 에이전트가 동시 실행 중이다
When reading_node에서 예외가 발생한다
Then reading_queue에 None sentinel이 전송된다
And reading_error SSE 이벤트가 전송된다
And grammar와 vocabulary 스트리밍은 계속된다
And grammar_done과 vocabulary_done이 정상 전송된다
```

**Scenario 10: Grammar agent fails, others continue**

```gherkin
Given 3개 에이전트가 동시 실행 중이다
When grammar_node에서 예외가 발생한다
Then grammar_queue에 None sentinel이 전송된다
And grammar_error SSE 이벤트가 전송된다
And reading과 vocabulary 스트리밍은 계속된다
```

**Scenario 11: Vocabulary agent fails, others continue**

```gherkin
Given 3개 에이전트가 동시 실행 중이다
When vocabulary_node에서 예외가 발생한다
Then vocab_queue에 None sentinel이 전송된다
And vocabulary_error SSE 이벤트가 전송된다
And reading과 grammar 스트리밍은 계속된다
```

**Scenario 12: Multiple agents fail simultaneously**

```gherkin
Given 3개 에이전트가 동시 실행 중이다
When reading_node와 grammar_node 모두 예외가 발생한다
Then reading_error와 grammar_error SSE 이벤트가 각각 전송된다
And vocabulary 스트리밍은 정상 계속된다
And done 이벤트가 최종 전송된다
```

### AC-5: Token Interleaving Merge (REQ-5)

**Scenario 13: Tokens merged in arrival order**

```gherkin
Given 3개 에이전트가 동시에 토큰을 생성한다
When reading이 "R1"을 먼저 보내고 grammar가 "G1"을, vocabulary가 "V1"을 보낸다
Then SSE 스트림에 reading_token("R1"), grammar_token("G1"), vocabulary_token("V1") 순서로
    (실제 도착 순서에 따라) 인터리빙되어 전송된다
```

**Scenario 14: Heartbeat on timeout**

```gherkin
Given 3개 에이전트가 동시 실행 중이다
When _HEARTBEAT_INTERVAL_SECONDS 동안 어떤 Queue에서도 토큰이 도착하지 않는다
Then ": heartbeat\n\n" SSE 코멘트가 전송된다
And 머지 루프가 계속 동작한다
```

**Scenario 15: Agent completion removes from active set**

```gherkin
Given reading_queue에서 None sentinel이 수신된다
When 다음 머지 사이클이 실행된다
Then reading이 active set에서 제거된다
And grammar_queue와 vocab_queue에서만 토큰을 대기한다
And 모든 active agent가 완료되면 머지 루프가 종료된다
```

### AC-6: LangGraph Partial Retention (REQ-6)

**Scenario 16: Analyze flow bypasses LangGraph**

```gherkin
Given analyze 요청이 수신된다
When graph.py의 route_by_task()가 호출된다
Then analyze 분기에서 빈 리스트가 반환된다
And reading/grammar Send() dispatch가 실행되지 않는다
```

**Scenario 17: Chat flow unchanged**

```gherkin
Given chat 요청이 수신된다
When graph.ainvoke()가 호출된다
Then 기존 LangGraph 경로를 통해 정상 처리된다
And 결과가 정상 반환된다
```

**Scenario 18: Image process flow unchanged**

```gherkin
Given image_process 요청이 수신된다
When graph의 image_processor node가 실행된다
Then 텍스트 추출 후 supervisor를 거쳐 analyze 재라우팅된다
And 재라우팅된 analyze는 _stream_analyze_events() 패턴으로 처리된다
And 모든 SSE 이벤트가 정상 전송된다
```

### AC-7: vocabulary_chunk Backward Compatibility (REQ-7)

**Scenario 19: vocabulary_chunk emitted after streaming**

```gherkin
Given vocabulary 토큰 스트리밍이 완료된다
When vocabulary_node가 결과를 반환한다
Then _parse_vocabulary_words()로 파싱된 단어 배열이 vocabulary_chunk 이벤트로 전송된다
And vocabulary_chunk의 데이터 형식은 기존과 동일하다: {"words": [...]}
And vocabulary_done 이벤트가 전송된다
```

### AC-8: Existing SSE Event Format Immutability (REQ-8)

**Scenario 20: All existing events unchanged**

```gherkin
Given 시스템이 업데이트된다
When 프론트엔드가 기존 SSE 이벤트를 수신한다
Then reading_token, grammar_token, vocabulary_token의 데이터 형식이 {"token": "string"}이다
And reading_done, grammar_done, vocabulary_done의 데이터 형식이 {"section": "string"}이다
And vocabulary_chunk의 데이터 형식이 {"words": [...]}이다
And vocabulary_error의 데이터 형식이 {"message": "string", "code": "string"}이다
And error의 데이터 형식이 {"message": "string", "code": "string"}이다
And done의 데이터 형식이 {"session_id": "string", "status": "complete"}이다
```

**Scenario 21: New error events follow existing pattern**

```gherkin
Given reading_node가 에러를 발생시킨다
When reading_error SSE 이벤트가 전송된다
Then 데이터 형식이 {"message": "string", "code": "reading_error"}이다
And vocabulary_error와 동일한 패턴이다
```

---

## 2. Test Scenarios

### 2.1 Backend Unit Tests

#### test_agents.py - reading_node

**Test 1: reading_node with token_queue streams tokens**

```python
@pytest.mark.asyncio
async def test_reading_node_streams_tokens():
    """reading_node should put tokens into queue and end with None sentinel."""
    queue = asyncio.Queue()
    state = {"input_text": "Hello world.", "level": 3}
    # Mock LLM to return known chunks

    result = await reading_node(state, token_queue=queue)

    tokens = []
    while True:
        token = queue.get_nowait()
        if token is None:
            break
        tokens.append(token)

    assert len(tokens) > 0
    assert result.get("reading_result") is not None
```

**Test 2: reading_node without token_queue (backward compat)**

```python
@pytest.mark.asyncio
async def test_reading_node_without_queue():
    """reading_node should work normally without token_queue."""
    state = {"input_text": "Hello world.", "level": 3}

    result = await reading_node(state)

    assert result.get("reading_result") is not None
    assert result["reading_result"].content
```

**Test 3: reading_node error sends sentinel**

```python
@pytest.mark.asyncio
async def test_reading_node_error_sends_sentinel():
    """On error, reading_node should put None sentinel and return error key."""
    queue = asyncio.Queue()
    state = {"input_text": "Hello world.", "level": 3}
    # Mock LLM to raise exception

    result = await reading_node(state, token_queue=queue)

    # Queue should have None sentinel
    sentinel = await queue.get()
    assert sentinel is None
    assert result.get("reading_error") is not None
```

#### test_agents.py - grammar_node

동일한 3개 테스트 패턴을 grammar_node에 대해 반복:

- `test_grammar_node_streams_tokens()`
- `test_grammar_node_without_queue()`
- `test_grammar_node_error_sends_sentinel()`

#### test_graph.py

**Test 4: route_by_task analyze returns empty list**

```python
def test_route_by_task_analyze_returns_empty():
    """Analyze flow should return empty list (no LangGraph dispatch)."""
    state = {"task_type": "analyze"}
    result = route_by_task(state)
    assert result == []
```

**Test 5: route_by_task chat still works**

```python
def test_route_by_task_chat_unchanged():
    """Chat flow should still route via LangGraph."""
    state = {"task_type": "chat"}
    result = route_by_task(state)
    assert len(result) == 1
    assert result[0].node == "chat"
```

**Test 6: route_by_task image_process still works**

```python
def test_route_by_task_image_process_unchanged():
    """Image process flow should still route via LangGraph."""
    state = {"task_type": "image_process"}
    result = route_by_task(state)
    assert len(result) == 1
    assert result[0].node == "image_processor"
```

#### test_services.py - streaming

**Test 7: format_reading_error**

```python
def test_format_reading_error():
    result = format_reading_error("test error")
    assert "reading_error" in result
    assert "test error" in result
```

**Test 8: format_grammar_error**

```python
def test_format_grammar_error():
    result = format_grammar_error("test error")
    assert "grammar_error" in result
    assert "test error" in result
```

### 2.2 Frontend Unit Tests

#### use-tutor-stream.test.ts

**Test 9: reading_error event handling**

```typescript
it("should handle reading_error event", () => {
  // Simulate SSE event: event: reading_error\ndata: {"message":"LLM failed","code":"reading_error"}
  // Assert: readingStreaming === false
  // Assert: readingError === "LLM failed"
  // Assert: grammarStreaming === true (unaffected)
  // Assert: vocabularyStreaming === true (unaffected)
});
```

**Test 10: grammar_error event handling**

```typescript
it("should handle grammar_error event", () => {
  // Simulate SSE event: event: grammar_error\ndata: {"message":"LLM failed","code":"grammar_error"}
  // Assert: grammarStreaming === false
  // Assert: grammarError === "LLM failed"
  // Assert: readingStreaming === true (unaffected)
  // Assert: vocabularyStreaming === true (unaffected)
});
```

---

## 3. Quality Gate (Definition of Done)

### Backend Checklist

- [ ] reading_node에 `token_queue: asyncio.Queue | None = None` parameter 추가
- [ ] reading_node가 `astream()` + Queue 토큰 전달 패턴 사용
- [ ] reading_node 에러 시 None sentinel 전송 + `reading_error` key 반환
- [ ] grammar_node에 동일 패턴 적용
- [ ] vocabulary_node 변경 없음 확인
- [ ] `_stream_analyze_events()` 구현 (supervisor 직접 호출 + asyncio.gather)
- [ ] `_merge_agent_streams()` 구현 (asyncio.wait FIRST_COMPLETED)
- [ ] `_stream_graph_events()`에서 analyze flow 위임
- [ ] `graph.py` route_by_task analyze 분기에서 빈 리스트 반환
- [ ] `graph.py` create_graph에서 reading/grammar node 제거
- [ ] image_process flow에서 OCR 후 analyze 재라우팅 정상 동작
- [ ] chat flow 정상 동작
- [ ] `format_reading_error()`, `format_grammar_error()` 추가
- [ ] 개별 에이전트 실패 시 나머지 에이전트 계속 스트리밍
- [ ] 기존 12개 SSE 이벤트 형식 불변
- [ ] 신규 reading_error, grammar_error 이벤트 정상 전송
- [ ] heartbeat timeout 동작
- [ ] Backend unit tests 통과 (test_agents, test_graph, test_services)

### Frontend Checklist

- [ ] `TutorStreamState`에 `readingError`, `grammarError` 필드 추가
- [ ] `reading_error` 이벤트 핸들러 추가
- [ ] `grammar_error` 이벤트 핸들러 추가
- [ ] 초기 state 및 reset에 새 필드 포함
- [ ] Frontend tests 통과

### Integration Checklist

- [ ] 텍스트 분석 (analyze) 요청 시 3개 에이전트 토큰이 인터리빙 스트리밍
- [ ] 이미지 분석 (image_process) 요청 시 OCR 후 analyze 패턴으로 정상 스트리밍
- [ ] 후속 질문 (chat) 요청 시 기존과 동일 동작
- [ ] 프로덕션 환경 (Railway) 에서 SSE 연결 유지
- [ ] 각 에이전트 개별 실패 시 나머지 정상 동작 확인
