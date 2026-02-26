# SPEC-VOCAB-002: Implementation Plan

| Field   | Value          |
|---------|----------------|
| SPEC ID | SPEC-VOCAB-002 |
| Phase   | Plan           |

---

## 1. 구현 전략

### 1.1 접근 방식

vocabulary 에이전트의 LLM 호출을 `ainvoke()` (배치)에서 `astream()` (토큰 스트리밍)으로 전환한다. vocabulary가 LangGraph 그래프 외부에서 `asyncio.Task`로 실행되므로, `asyncio.Queue`를 토큰 전달 채널로 사용하여 라우터가 토큰을 실시간 SSE 이벤트로 전송할 수 있도록 한다.

### 1.2 핵심 설계 원칙

1. **최소 변경**: 기존 vocabulary_node의 반환값 구조, 기존 SSE 이벤트 플로우를 모두 유지
2. **기존 패턴 활용**: `reading_token`/`grammar_token`과 동일한 SSE 이벤트 패턴 적용
3. **하위 호환성**: `token_queue` 파라미터를 선택적으로 받아 기존 테스트와 호출부에 영향 없음
4. **방어적 프로그래밍**: Queue sentinel, 에러 시 sentinel 전송, task 상태 확인 등

---

## 2. Milestones

### Milestone 1: Backend 스트리밍 인프라 (Primary Goal)

**목표:** vocabulary_node가 토큰을 Queue로 전달하고, 라우터가 SSE로 스트리밍

**변경 파일:**

| 파일 | 변경 내용 | 위험도 |
|------|----------|--------|
| `backend/src/tutor/agents/vocabulary.py` | `ainvoke` -> `astream` + `token_queue` 파라미터 추가 | Medium |
| `backend/src/tutor/services/streaming.py` | `format_vocabulary_token()` 함수 추가 | Low |
| `backend/src/tutor/routers/tutor.py` | vocabulary 처리 루프를 Queue 기반 토큰 스트리밍으로 전환 | Medium |

**구현 순서:**

1. `streaming.py`에 `format_vocabulary_token()` 추가 (가장 단순, 독립적)
2. `vocabulary.py`에서 `ainvoke` -> `astream` + Queue 전달 로직 구현
3. `tutor.py`에서 Queue 생성 + 토큰 스트리밍 루프 구현

**검증:**

- 백엔드 로컬 테스트로 `vocabulary_token` SSE 이벤트가 토큰마다 전송되는지 확인
- 스트리밍 완료 후 `vocabulary_chunk` 이벤트에 구조화된 데이터가 포함되는지 확인
- 에러 발생 시 `vocabulary_error` + `vocabulary_done` 이벤트가 정상 전송되는지 확인

### Milestone 2: Frontend 토큰 핸들러 (Primary Goal)

**목표:** 프론트엔드가 `vocabulary_token` 이벤트를 수신하여 누적 처리

**변경 파일:**

| 파일 | 변경 내용 | 위험도 |
|------|----------|--------|
| `src/hooks/use-tutor-stream.ts` | `vocabularyRawContent` 상태 추가 + `vocabulary_token` 핸들러 | Low |

**구현 순서:**

1. `TutorStreamState`에 `vocabularyRawContent: string` 추가
2. 초기값 및 리셋 로직 추가
3. `vocabulary_token` 이벤트 핸들러 추가

**검증:**

- `vocabulary_token` 이벤트 수신 시 `vocabularyRawContent`가 누적되는지 확인
- 기존 `vocabulary_chunk`, `vocabulary_done`, `vocabulary_error` 핸들러가 정상 동작하는지 확인

### Milestone 3: Vocabulary Panel 스트리밍 UX (Secondary Goal)

**목표:** 스트리밍 중 raw 텍스트를 실시간 표시하여 사용자에게 진행 상태 제공

**변경 파일:**

| 파일 | 변경 내용 | 위험도 |
|------|----------|--------|
| `src/components/tutor/vocabulary-panel.tsx` | 스트리밍 중 raw Markdown 표시 로직 추가 | Low |

**구현 순서:**

1. `vocabularyRawContent` prop 추가
2. 스트리밍 중 raw 콘텐츠가 있으면 Markdown으로 렌더링 (skeleton 대체)
3. `vocabularyWords`가 도착하면 기존 구조화된 표시로 전환

**검증:**

- 스트리밍 중 사용자에게 실시간 텍스트가 보이는지 확인
- 최종 결과 도착 시 구조화된 단어별 표시로 자연스럽게 전환되는지 확인

### Milestone 4: 테스트 및 검증 (Primary Goal)

**목표:** 모든 변경사항에 대한 테스트 작성 및 기존 테스트 통과 확인

**테스트 범위:**

| 테스트 | 파일 | 내용 |
|--------|------|------|
| Backend unit | `test_agents.py` | vocabulary_node가 Queue에 토큰을 전달하는지 확인 |
| Backend unit | `test_services.py` | `format_vocabulary_token` SSE 포맷 확인 |
| Backend unit | `test_router.py` (or `test_graph.py`) | vocabulary 토큰 스트리밍 루프 동작 확인 |
| Frontend unit | `use-tutor-stream.test.ts` | `vocabulary_token` 이벤트 핸들링 확인 |
| Frontend unit | `vocabulary-panel.test.tsx` | 스트리밍 중 raw 텍스트 표시 확인 (Milestone 3 포함 시) |
| Regression | 전체 | 기존 reading/grammar 테스트 통과 확인 |

---

## 3. 기술적 접근

### 3.1 asyncio.Queue 토큰 전달 패턴

```
vocabulary_node()                    _stream_graph_events()
    |                                        |
    |-- astream(prompt) ------+              |
    |                         |              |
    |   chunk1 -> queue.put() +-- queue.get() --> yield vocabulary_token
    |   chunk2 -> queue.put() +-- queue.get() --> yield vocabulary_token
    |   ...                   |              |
    |   chunkN -> queue.put() +-- queue.get() --> yield vocabulary_token
    |   None   -> queue.put() +-- queue.get() --> break (sentinel)
    |                                        |
    |-- return result -------> await task --> yield vocabulary_chunk
    |                                        yield vocabulary_done
```

### 3.2 에러 처리 시나리오

| 시나리오 | vocabulary_node 동작 | 라우터 동작 |
|----------|---------------------|------------|
| 정상 완료 | 토큰 전송 -> sentinel -> 결과 반환 | 토큰 스트리밍 -> chunk + done 전송 |
| LLM 에러 | sentinel 전송 -> 에러 결과 반환 | 스트리밍 종료 -> error + done 전송 |
| Queue timeout | N/A | heartbeat 전송 후 재시도 |
| Task 예외 | sentinel 전송 -> 예외 | 스트리밍 종료 -> error + done 전송 |
| 부분 스트리밍 후 에러 | 부분 토큰 전송 -> sentinel -> 에러 반환 | 부분 토큰 스트리밍 -> error + done 전송 |

### 3.3 SSE 이벤트 시퀀스 (정상 플로우)

```
event: reading_token        (reading 토큰 스트리밍)
event: grammar_token        (grammar 토큰 스트리밍)
event: reading_done
event: grammar_done
event: vocabulary_token     (NEW: vocabulary 토큰 스트리밍 시작)
event: vocabulary_token
event: vocabulary_token
...
event: vocabulary_chunk     (EXISTING: 최종 구조화된 결과)
event: vocabulary_done      (EXISTING: vocabulary 완료)
event: done                 (EXISTING: 전체 완료)
```

### 3.4 reading/grammar 대비 vocabulary 스트리밍 차이점

| 측면 | reading/grammar | vocabulary |
|------|----------------|------------|
| 실행 위치 | LangGraph 그래프 내부 | asyncio.Task (그래프 외부) |
| 토큰 전달 | `astream_events` (`on_chat_model_stream`) | `asyncio.Queue` |
| 스트리밍 시점 | 그래프 스트리밍 중 동시 | 그래프 스트리밍 완료 후 |
| 구조화된 결과 | 없음 (raw Markdown만 전송) | `vocabulary_chunk` (단어 배열) |
| 파서 | 프론트엔드에서 Markdown 렌더링 | 백엔드에서 `_parse_vocabulary_words()` |

---

## 4. 위험 분석 및 대응

| 위험 | 가능성 | 영향도 | 대응 방안 |
|------|--------|--------|----------|
| `astream()`의 TTFT가 프록시 타임아웃보다 긴 경우 | Low | High | Queue timeout 시 heartbeat 전송으로 대응. 일반적으로 LLM TTFT는 1-3초 |
| 부분 스트리밍 후 에러 시 프론트엔드에 불완전한 텍스트가 잔류 | Medium | Low | `vocabulary_chunk` 도착 시 구조화된 데이터로 교체. 에러 시 에러 표시로 전환 |
| Queue sentinel 미전송으로 라우터가 무한 대기 | Low | High | try/finally 블록에서 sentinel 전송 보장. task.done() 체크로 이중 안전장치 |
| 기존 테스트에서 vocabulary_node 시그니처 변경 감지 | Low | Low | `token_queue=None` 기본값으로 기존 호출부 영향 없음 |
| Railway 프록시가 `vocabulary_token` 이벤트도 무시하는 경우 | Very Low | High | `vocabulary_token`은 표준 SSE `data:` 이벤트이므로 heartbeat 코멘트와 달리 프록시가 인식해야 함 |

---

## 5. 범위 외 (Out of Scope)

- vocabulary를 LangGraph 그래프 내부로 재편입 (FuturesDict GC 버그 미해결)
- vocabulary 프롬프트 또는 모델 변경
- `_parse_vocabulary_words()` 파서 로직 변경
- vocabulary 부분 파싱(단어 하나씩 실시간 구조화) - 전체 텍스트 완료 후 파싱 유지
- Chat 엔드포인트 변경
- LangGraph 버전 업그레이드

---

## 6. 다음 단계

1. `/moai:2-run SPEC-VOCAB-002` 로 구현 시작
2. 구현 완료 후 프로덕션 배포 및 Railway에서 vocabulary 출력 잘림 해소 확인
3. `/moai:3-sync SPEC-VOCAB-002` 로 문서 동기화
