---
id: SPEC-STREAM-001
type: acceptance
version: "1.0.0"
status: implemented
---

# SPEC-STREAM-001: Acceptance Criteria

## Test Scenarios (Given-When-Then)

### Scenario 1: Reading Token Streaming

```gherkin
Given reading 에이전트가 토큰을 스트리밍 중이고
  And 프론트엔드가 SSE 연결을 유지하고 있을 때
When 프론트엔드가 reading_token 이벤트를 수신하면
Then 콘텐츠가 기존 readingContent에 문자 단위로 append 되어야 한다
  And readingStreaming 플래그가 true로 유지되어야 한다
  And 블링킹 커서가 콘텐츠 끝에 표시되어야 한다
```

### Scenario 2: Grammar Section Done Signal

```gherkin
Given grammar 에이전트가 스트리밍을 완료했을 때
When grammar_done 이벤트를 수신하면
Then grammarStreaming 플래그가 false로 변경되어야 한다
  And readingStreaming 및 vocabularyStreaming 플래그는 변경되지 않아야 한다
  And grammar 탭의 pulsing dot 인디케이터가 사라져야 한다
  And 블링킹 커서가 더 이상 표시되지 않아야 한다
```

### Scenario 3: Tab Switching During Streaming

```gherkin
Given 3개의 에이전트(reading, grammar, vocabulary)가 모두 스트리밍 중이고
  And reading 탭에 일부 콘텐츠가 누적되어 있을 때
When 사용자가 grammar 탭으로 전환하면
Then reading 탭의 누적된 콘텐츠가 보존되어야 한다
  And grammar 탭의 스트리밍 콘텐츠가 표시되어야 한다
  And 다시 reading 탭으로 돌아왔을 때 이전 콘텐츠가 유지되어야 한다
```

### Scenario 4: Vocabulary Batch Delivery

```gherkin
Given vocabulary 에이전트가 aggregator를 통해 완료되었을 때
When vocabulary_chunk 이벤트가 도착하면
Then 어휘 단어 목록이 일괄 표시되어야 한다
  And vocabularyStreaming 플래그가 false로 변경되어야 한다
  And 스켈레톤 로딩 UI가 실제 콘텐츠로 교체되어야 한다
```

### Scenario 5: Client Disconnect Handling

```gherkin
Given 백엔드가 astream_events를 통해 토큰을 스트리밍 중일 때
When 클라이언트가 SSE 연결을 중간에 끊으면 (asyncio.CancelledError 발생)
Then 서버가 에러 로깅 없이 gracefully 처리해야 한다
  And 서버 프로세스가 정상적으로 유지되어야 한다
  And 다른 활성 연결에 영향을 주지 않아야 한다
```

### Scenario 6: Legacy Chunk Backward Compatibility

```gherkin
Given 백엔드가 레거시 reading_chunk 이벤트를 전송할 때
When 프론트엔드가 reading_chunk 이벤트를 수신하면
Then 콘텐츠가 append가 아닌 replace 방식으로 처리되어야 한다
  And 기존 reading_token 방식과 공존할 수 있어야 한다
```

### Scenario 7: Streaming Flags Reset on Done

```gherkin
Given 일부 섹션이 아직 스트리밍 중일 때
When done 이벤트를 수신하면
Then readingStreaming이 false로 설정되어야 한다
  And grammarStreaming이 false로 설정되어야 한다
  And vocabularyStreaming이 false로 설정되어야 한다
  And isStreaming이 false로 설정되어야 한다
```

### Scenario 8: Empty Token Filtering

```gherkin
Given LLM이 빈 토큰(empty string)을 생성할 때
When 백엔드가 on_chat_model_stream 이벤트를 처리하면
Then 빈 토큰은 SSE 이벤트로 발행되지 않아야 한다
  And 프론트엔드에 불필요한 이벤트가 전달되지 않아야 한다
```

### Scenario 9: Pulsing Dot Indicator

```gherkin
Given reading 섹션이 스트리밍 중일 때 (readingStreaming === true)
When 사용자가 탭 헤더를 확인하면
Then reading 탭 라벨 옆에 pulsing dot 인디케이터가 표시되어야 한다
  And reading_done 이벤트 수신 후 인디케이터가 사라져야 한다
```

### Scenario 10: Skeleton Loading for Vocabulary

```gherkin
Given vocabulary 섹션이 스트리밍 중일 때 (vocabularyStreaming === true)
  And 아직 vocabulary_chunk 이벤트를 수신하지 않았을 때
When 사용자가 vocabulary 탭을 확인하면
Then 스켈레톤 로딩 UI가 표시되어야 한다
  And vocabulary_chunk 수신 후 실제 단어 카드로 교체되어야 한다
```

## Quality Gate Criteria

### Test Coverage

| Category | Tests | Status |
|----------|-------|--------|
| Frontend Total | 103/103 | PASS |
| Frontend Streaming-specific | 12 tests | PASS |
| Backend Total | 230/230 | PASS |
| Backend Coverage | 97% | PASS |

### Streaming-specific Test Details

| Test | File | Description |
|------|------|-------------|
| 1 | `use-tutor-stream.test.ts` | reading_token append 동작 검증 |
| 2 | `use-tutor-stream.test.ts` | grammar_token append 동작 검증 |
| 3 | `use-tutor-stream.test.ts` | reading_done 플래그 전환 검증 |
| 4 | `use-tutor-stream.test.ts` | grammar_done 플래그 전환 검증 |
| 5 | `use-tutor-stream.test.ts` | vocabulary_chunk 일괄 수신 및 플래그 전환 검증 |
| 6 | `use-tutor-stream.test.ts` | section streaming 초기 상태 검증 |
| 7 | `use-tutor-stream.test.ts` | reading_chunk 하위 호환 검증 |
| 8 | `use-tutor-stream.test.ts` | grammar_chunk 하위 호환 검증 |
| 9 | `use-tutor-stream.test.ts` | vocabulary_chunk 파싱 검증 |
| 10 | `use-tutor-stream.test.ts` | 에러 핸들링 검증 |
| 11 | `use-tutor-stream.test.ts` | reset 동작 검증 |
| 12 | `use-tutor-stream.test.ts` | 초기 상태 검증 |

### Code Quality

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| TypeScript Errors | 0 | 0 | PASS |
| Pyright Errors (production) | 0 | 0 | PASS |
| Frontend Test Pass Rate | 100% | 103/103 | PASS |
| Backend Test Pass Rate | 100% | 230/230 | PASS |
| Backend Coverage | >= 85% | 97% | PASS |

## Definition of Done

- [x] Backend: `streaming=True`가 모든 ChatOpenAI 인스턴스에 적용됨
- [x] Backend: `astream_events(v2)` 기반 토큰 스트리밍 구현 완료
- [x] Backend: `asyncio.CancelledError` graceful handling 구현
- [x] Backend: reading_token, grammar_token, section_done, vocabulary_chunk SSE 이벤트 포맷터 구현
- [x] Frontend: `SectionStreamingState` 인터페이스 정의
- [x] Frontend: `useTutorStream` 훅에 토큰 append + 레거시 chunk 핸들러 구현
- [x] Frontend: Pulsing dot 인디케이터 구현
- [x] Frontend: 블링킹 커서 구현 (Reading/Grammar 패널)
- [x] Frontend: 스켈레톤 로딩 UI 구현 (Vocabulary 패널)
- [x] Frontend: Desktop 및 Mobile 레이아웃에 streaming 플래그 전달
- [x] Frontend: 12개 스트리밍 관련 테스트 통과 (전체 103/103)
- [x] Backend: 전체 230/230 테스트 통과 (97% coverage)
- [x] Zero TypeScript errors
- [x] Zero Pyright errors in production code

## Verification Methods

| Method | Scope | Tool |
|--------|-------|------|
| Unit Test | 토큰 append, 플래그 전환, 에러 핸들링 | Vitest, pytest |
| Integration Test | SSE 이벤트 전체 플로우 | pytest (StreamingResponse) |
| Manual E2E | 탭 전환 중 콘텐츠 보존, 블링킹 커서, pulsing dot | Browser dev tools |
| Type Check | TypeScript strict, Pyright strict | tsc --noEmit, pyright |
