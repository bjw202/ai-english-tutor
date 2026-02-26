# SPEC-VOCAB-002: Acceptance Criteria

| Field      | Value          |
|------------|----------------|
| SPEC ID    | SPEC-VOCAB-002 |
| Phase      | Complete       |
| Commit     | 93b9c16        |
| Completed  | 2026-02-26     |

---

## 1. 수락 기준

### AC-1: Vocabulary 토큰 레벨 SSE 스트리밍 (REQ-1)

**Given** 유효한 영어 텍스트로 분석 요청이 제출된 상태에서
**When** vocabulary 에이전트가 LLM으로부터 토큰을 수신할 때
**Then** 각 토큰이 `vocabulary_token` SSE 이벤트로 즉시 전송된다
**And** 이벤트 형식은 `event: vocabulary_token\ndata: {"token": "<토큰>"}\n\n` 이다
**And** heartbeat 코멘트 대신 실제 `data:` 이벤트가 지속적으로 전송되어 SSE 연결이 유지된다

### AC-2: asyncio.Queue 기반 토큰 전달 (REQ-2)

**Given** vocabulary_node가 `token_queue` 파라미터와 함께 호출된 상태에서
**When** LLM이 토큰을 생성할 때
**Then** 각 토큰이 `asyncio.Queue.put()`을 통해 라우터에 전달된다
**And** 스트리밍 완료 시 `None` sentinel이 Queue에 전송된다
**And** 에러 발생 시에도 `None` sentinel이 전송되어 라우터의 Queue 읽기 루프가 종료된다

### AC-3: 스트리밍 완료 후 구조화된 결과 전송 (REQ-3)

**Given** vocabulary 토큰 스트리밍이 완료된 상태에서
**When** vocabulary_task가 최종 결과를 반환할 때
**Then** 누적된 텍스트가 `_parse_vocabulary_words()`로 파싱되어 `vocabulary_chunk` SSE 이벤트로 전송된다
**And** `vocabulary_chunk`의 데이터 구조는 기존과 동일하다: `{"words": [{"word": "...", "content": "..."}, ...]}`
**And** `vocabulary_chunk` 이후 `vocabulary_done` 이벤트가 전송된다

### AC-4: 프론트엔드 vocabulary_token 처리 (REQ-4)

**Given** 프론트엔드에서 SSE 스트림을 수신 중인 상태에서
**When** `vocabulary_token` 이벤트가 도착할 때
**Then** `vocabularyRawContent` 상태가 토큰으로 누적 업데이트된다
**And** 기존 `vocabulary_chunk` 핸들러가 정상 동작하여 `vocabularyWords`가 설정된다
**And** `vocabulary_done` 핸들러가 정상 동작하여 `vocabularyStreaming`이 `false`로 전환된다

### AC-5: LangGraph 그래프 외부 유지 (REQ-5)

**Given** vocabulary 에이전트의 구현이 변경된 상태에서
**When** 텍스트 분석 요청이 처리될 때
**Then** vocabulary는 `asyncio.create_task()` 기반 asyncio.Task로 실행된다
**And** LangGraph의 `Send()` dispatch에 포함되지 않는다
**And** FuturesDict weakref GC 버그가 발생하지 않는다

### AC-6: 기존 이벤트 플로우 회귀 방지 (REQ-6)

**Given** vocabulary 스트리밍 변경이 적용된 상태에서
**When** 텍스트 분석 요청이 처리될 때
**Then** `reading_token`, `reading_done`, `grammar_token`, `grammar_done` 이벤트가 기존과 동일하게 동작한다
**And** `vocabulary_done`, `vocabulary_error` 이벤트가 기존과 동일하게 동작한다
**And** 기존 reading/grammar 관련 테스트가 수정 없이 모두 통과한다

### AC-7: 에러 시나리오 처리

**Given** vocabulary LLM 호출 중 예외가 발생한 상태에서
**When** 에러가 `vocabulary_node`에서 catch될 때
**Then** Queue에 `None` sentinel이 전송되어 토큰 스트리밍 루프가 종료된다
**And** `vocabulary_error` SSE 이벤트가 에러 메시지와 함께 전송된다
**And** `vocabulary_done` SSE 이벤트가 에러 이벤트 이후에 전송된다
**And** 프론트엔드에서 에러 메시지가 표시된다

### AC-8: 부분 스트리밍 후 에러 처리

**Given** vocabulary가 일부 토큰을 성공적으로 스트리밍한 후 에러가 발생한 상태에서
**When** 에러가 감지될 때
**Then** 이미 전송된 `vocabulary_token` 이벤트는 프론트엔드에서 누적된 상태이다
**And** `vocabulary_error` 이벤트가 전송되어 에러 상태를 알린다
**And** `vocabulary_done` 이벤트가 전송된다
**And** 프론트엔드는 에러 메시지를 표시하며, 부분적으로 수신된 raw 텍스트는 표시하지 않는다

### AC-9: token_queue 하위 호환성

**Given** vocabulary_node가 `token_queue` 파라미터 없이 호출된 상태에서 (기존 호출 방식)
**When** vocabulary_node가 실행될 때
**Then** Queue 없이 기존과 동일하게 동작하여 최종 결과만 반환한다
**And** 기존 vocabulary_node 단위 테스트가 수정 없이 통과한다

---

## 2. 테스트 시나리오

### 2.1 Backend 단위 테스트

**테스트 1: vocabulary_node Queue 토큰 전달**

```
Given: mock LLM이 ["Hello", " World", " test"] 토큰을 순차 생성하도록 설정
When: vocabulary_node(state, token_queue=queue) 호출
Then: queue에서 "Hello", " World", " test", None (sentinel) 순서로 수신
And: 반환값에 vocabulary_result가 포함
```

**테스트 2: vocabulary_node Queue 에러 시 sentinel 전송**

```
Given: mock LLM이 에러를 발생시키도록 설정
When: vocabulary_node(state, token_queue=queue) 호출
Then: queue에서 None (sentinel) 수신
And: 반환값에 vocabulary_error가 포함
```

**테스트 3: vocabulary_node Queue 없이 하위 호환**

```
Given: token_queue 파라미터 없이 호출
When: vocabulary_node(state) 실행
Then: 기존과 동일하게 vocabulary_result 반환
And: 에러 없이 정상 완료
```

**테스트 4: format_vocabulary_token SSE 포맷**

```
Given: token = "Hello"
When: format_vocabulary_token(token) 호출
Then: 결과가 'event: vocabulary_token\ndata: {"token": "Hello"}\n\n'
```

**테스트 5: 라우터 vocabulary 토큰 스트리밍 루프**

```
Given: mock vocabulary_node가 Queue에 토큰을 전달하도록 설정
When: _stream_graph_events()가 실행
Then: vocabulary_token SSE 이벤트가 순차적으로 yield
And: 스트리밍 완료 후 vocabulary_chunk SSE 이벤트가 yield
And: vocabulary_done SSE 이벤트가 yield
```

### 2.2 Frontend 단위 테스트

**테스트 6: useTutorStream vocabulary_token 핸들러**

```
Given: SSE 스트림에 vocabulary_token 이벤트가 포함
When: 이벤트 파싱 실행
Then: vocabularyRawContent가 토큰으로 누적 업데이트
And: vocabularyStreaming이 true 유지
```

**테스트 7: vocabulary_token 후 vocabulary_chunk 전환**

```
Given: vocabulary_token 이벤트로 raw 텍스트가 누적된 상태
When: vocabulary_chunk 이벤트 수신
Then: vocabularyWords가 구조화된 데이터로 설정
And: vocabularyStreaming이 false로 전환
```

**테스트 8: 스트림 시작 시 vocabularyRawContent 리셋**

```
Given: 이전 스트림에서 vocabularyRawContent에 데이터가 있는 상태
When: 새 스트림이 시작
Then: vocabularyRawContent가 빈 문자열로 리셋
```

### 2.3 통합 테스트 (수동)

**테스트 9: 프로덕션 환경 SSE 연결 유지**

```
Given: Railway에 배포된 백엔드
When: 긴 영어 텍스트로 분석 요청 실행
Then: vocabulary 섹션이 잘리지 않고 완전한 결과가 수신
And: SSE 연결이 vocabulary 스트리밍 완료까지 유지
And: vocabulary_token 이벤트가 프록시를 통해 정상 전달
```

**테스트 10: 기존 기능 회귀 없음**

```
Given: 변경사항이 적용된 상태
When: 여러 다른 텍스트로 분석 요청 실행
Then: reading 탭 결과가 정상 표시
And: grammar 탭 결과가 정상 표시
And: vocabulary 탭 결과가 구조화된 단어별로 정상 표시
```

---

## 3. Quality Gate

### 3.1 Definition of Done

- [x] vocabulary_node가 `astream()` + `asyncio.Queue`를 통해 토큰을 스트리밍한다
- [x] `vocabulary_token` SSE 이벤트가 토큰마다 전송된다
- [x] 스트리밍 완료 후 `vocabulary_chunk` 이벤트가 구조화된 데이터와 함께 전송된다
- [x] 프론트엔드가 `vocabulary_token` 이벤트를 처리한다
- [x] 에러 시 sentinel 전송 + `vocabulary_error` + `vocabulary_done` 이벤트가 정상 작동한다
- [x] `token_queue=None` 기본값으로 기존 호출부 하위 호환성이 유지된다
- [x] 기존 reading/grammar 테스트가 수정 없이 모두 통과한다
- [x] 새 테스트(backend + frontend)가 추가되어 통과한다
- [x] TypeScript 컴파일 에러 0건
- [x] ESLint 에러 0건
- [x] Backend ruff 린팅 에러 0건

### 3.2 검증 도구

| 도구 | 명령어 | 기준 |
|------|--------|------|
| pytest | `cd backend && pytest --cov=src` | 전체 통과, 커버리지 85%+ |
| Vitest | `pnpm test` | 전체 통과 |
| TypeScript | `pnpm tsc --noEmit` | 에러 0건 |
| ESLint | `pnpm lint` | 에러 0건 |
| ruff | `cd backend && ruff check src` | 에러 0건 |
