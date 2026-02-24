# 이미지 분석 배포 학습 가이드

## 문서 정보

- **작성일**: 2026-02-24
- **관련 SPEC**: SPEC-IMAGE-001
- **기술 스택**: LangGraph, FastAPI, Next.js, Vercel, Railway
- **대상 독자**: 이 프로젝트의 현재 및 미래 개발자
- **목적**: 배포 중 발생한 4가지 버그에서 얻은 교훈을 체계화하여 미래의 유사한 문제를 예방

---

## 섹션 1: 문제 요약

### 무엇이 잘못되었나

이미지 분석 기능이 첫 프로덕션 배포 후 완전히 동작하지 않았습니다. 로컬 개발 환경에서는 정상 동작했지만, Vercel(Frontend) + Railway(Backend) 프로덕션 환경에서는 세 가지 다른 원인으로 인한 네 가지 버그가 중첩하여 나타났습니다.

최종 사용자 경험:
1. 이미지를 업로드하면 결과가 항상 비어있었습니다 (Bug-1)
2. "분석중" 상태가 10초 후 멈추었습니다 (Bug-2)
3. "GraphRecursionError: Recursion limit of 25 reached" 오류가 발생했습니다 (Bug-3)
4. 오류 발생 시 사용자에게 아무것도 표시되지 않았습니다 (Bug-4)

### 타임라인

```
[00:30]  이미지 분석 기능 첫 배포 완료
[00:40]  사용자 테스트 시작: 빈 결과 발견
[00:45]  Railway 로그 확인: "No image_data provided" 경고 발견
[01:00]  근본 원인 분석: TypedDict 누락 필드 발견
[01:12]  Bug-1 수정 배포 (e624069)
[01:20]  재테스트: 이번엔 10초 후 멈춤
[01:25]  Vercel 로그 확인: 함수 타임아웃 확인
[01:40]  Bug-2 수정 배포 (477f00b)
[01:50]  재테스트: GraphRecursionError 발생
[02:00]  LangGraph Send() 동작 원리 심층 분석
[06:00]  Bug-3, Bug-4 수정 코딩 완료
[06:36]  Bug-3, Bug-4 수정 배포 (31f9fb9)
[07:00]  사용자 확인: "잘 동작한다"
```

총 소요 시간: 약 6.5시간 (새벽 시간대 작업)

### 발견된 근본 원인들

1. **LangGraph TypedDict 필드 누락**: 프레임워크의 상태 관리 메커니즘을 완전히 이해하지 못함
2. **Vercel 서버리스 제약 미반영**: 로컬 개발 환경과 클라우드 환경의 타임아웃 차이 간과
3. **LangGraph Send() API 동작 오해**: Send()로 전달한 상태가 그래프 전역 상태를 업데이트하지 않음
4. **방어적 코딩 누락**: HTTP 응답 상태 확인이 기본 패턴에 없었음

---

## 섹션 2: Bug-1 - TutorState 누락 필드

### 증상

Railway 백엔드 로그:
```
WARNING: No image_data provided to image_processor_node
```

이미지를 업로드했지만 `image_processor_node`에서는 이미지 데이터가 없다고 판단하여 빈 결과를 반환했습니다.

### 근본 원인: LangGraph StateGraph의 TypedDict 보존 메커니즘

LangGraph의 StateGraph는 상태(state)를 TypedDict로 정의합니다. 이 TypedDict는 단순한 타입 힌트가 아니라, 실제로 LangGraph가 어떤 키를 상태로 유지할지 결정하는 스키마입니다.

**핵심 원칙**: LangGraph는 TypedDict에 정의된 키만 상태로 전파합니다. 정의되지 않은 키는 런타임에 조용히 무시됩니다.

문제가 된 코드:
```python
# 수정 전 state.py - image_data와 mime_type 필드 없음
class TutorState(TypedDict):
    messages: list[dict]
    level: int
    session_id: str
    input_text: str
    task_type: str
    reading_result: NotRequired[ReadingResult | None]
    grammar_result: NotRequired[GrammarResult | None]
    vocabulary_result: NotRequired[VocabularyResult | None]
    extracted_text: NotRequired[str | None]
    supervisor_analysis: NotRequired[SupervisorAnalysis | None]
    # image_data와 mime_type이 없음!
```

FastAPI 라우터에서 `image_data`와 `mime_type`을 `initial_state`에 넣어 그래프에 전달했지만, LangGraph는 TypedDict 스키마를 기준으로 상태를 관리하므로 이 두 필드를 그래프 실행 중 자동으로 제거했습니다.

### 수정

```python
# 수정 후 state.py
class TutorState(TypedDict):
    # ... 기존 필드 ...
    image_data: NotRequired[str | None]   # 추가
    mime_type: NotRequired[str | None]    # 추가
```

`NotRequired`를 사용한 이유: 텍스트 분석 시에는 이 두 필드가 없어도 됩니다. Python의 `typing.NotRequired`는 해당 키가 딕셔너리에 없어도 TypedDict 유효성 검사를 통과시킵니다.

### 학습 원칙

**[원칙-1] LangGraph TypedDict는 단순 타입 힌트가 아니다.**

LangGraph StateGraph에서 TypedDict는 실제 상태 스키마입니다. 그래프를 통해 전달하려는 모든 데이터는 TypedDict에 정의되어야 합니다. 정의하지 않은 필드는 런타임에 경고 없이 사라집니다.

**새 필드 추가 체크리스트:**
- [ ] `TutorState` TypedDict에 필드 정의 (필수)
- [ ] 선택적 필드는 `NotRequired[T | None]` 타입 사용
- [ ] 해당 필드를 사용하는 노드에서 `state.get("field_name", default)` 패턴으로 접근

---

## 섹션 3: Bug-2 - Vercel 서버리스 타임아웃

### 증상

Vercel 프론트엔드 로그: 함수 실행 시간 초과
사용자 화면: "분석중" 텍스트가 10초 후 멈추고 결과 없음
(텍스트 분석은 정상 동작, 이미지 분석만 실패)

### 근본 원인: 두 가지 타임아웃의 차이

**Idle Timeout (프록시 타임아웃)**
- 연속된 데이터 없이 10초가 지나면 연결이 끊어집니다.
- Vercel의 CDN/프록시 레이어가 적용합니다.
- SSE(Server-Sent Events)의 경우 실제 데이터 없이 유지하려면 더미 데이터를 주기적으로 보내야 합니다.

**Execution Timeout (함수 실행 타임아웃)**
- Vercel Hobby 플랜: 기본 10초, `maxDuration` 설정 시 최대 60초
- 함수 자체의 실행 시간 제한입니다.
- OpenAI Vision API는 이미지 처리에 25-35초가 필요합니다.

텍스트 분석이 10초 이내에 완료되어 이슈가 없었지만, 이미지 분석은 두 제약 모두를 위반했습니다.

### 수정: maxDuration + SSE 하트비트

**수정 1: Vercel 함수 실행 시간 연장**

```typescript
// src/app/api/tutor/analyze-image/route.ts
export const maxDuration = 60; // Vercel Hobby 플랜 최대값

export async function POST(request: NextRequest) {
  // ...기존 코드
}
```

주의: `maxDuration`은 파일 최상위 레벨의 export 상수로 선언해야 합니다. 함수 내부에서 선언해도 적용되지 않습니다.

**수정 2: SSE 하트비트로 Idle Timeout 방지**

```python
# backend/src/tutor/routers/tutor.py
async def heartbeat_producer(queue: asyncio.Queue, stop_event: asyncio.Event):
    """주기적으로 SSE 주석을 전송하여 연결이 끊어지지 않게 유지"""
    while not stop_event.is_set():
        try:
            await asyncio.sleep(5)
            if not stop_event.is_set():
                await queue.put(": comment\n\n")  # SSE 주석 형식
        except asyncio.CancelledError:
            break

async def content_producer(queue, stop_event, ...):
    """실제 LLM 스트리밍 내용 생성"""
    try:
        # 분석 실행
        async for event in streaming:
            await queue.put(event)
    finally:
        stop_event.set()
        await queue.put(None)  # 종료 신호
```

SSE 하트비트 형식: `: comment\n\n`
- SSE 규격에서 `:` 으로 시작하는 라인은 주석(comment)입니다.
- 브라우저와 SSE 클라이언트 라이브러리 모두 이를 무시합니다.
- 프록시는 이것을 실제 데이터로 인식하여 idle timeout 타이머를 리셋합니다.

### Vercel 배포 타임아웃 참조표

| 플랜 | 기본 실행 시간 | maxDuration 최대값 | 비용 |
|------|---------------|-------------------|------|
| Hobby | 10초 | 60초 | 무료 |
| Pro | 15초 | 300초 | $20/월 |
| Enterprise | 15초 | 900초 | 협의 |

### 학습 원칙

**[원칙-2] 서버리스 환경에서는 타임아웃을 명시적으로 설정하라.**

클라우드 서버리스 플랫폼(Vercel, Netlify 등)에는 두 가지 타임아웃이 존재합니다:
- **Idle timeout**: 연속 데이터 없을 때 (SSE 하트비트로 우회)
- **Execution timeout**: 함수 전체 실행 시간 (maxDuration으로 연장)

**LLM API 처리 시간 추정:**
- 텍스트 분석 (gpt-4o-mini): ~5-10초
- 이미지 OCR (Vision API): ~25-35초
- 복잡한 멀티-에이전트: ~30-60초

**배포 전 타임아웃 체크리스트:**
- [ ] LLM API 최대 처리 시간 확인
- [ ] `maxDuration` > LLM 최대 처리 시간 으로 설정
- [ ] 장시간 실행 SSE에 5초 이내 하트비트 추가
- [ ] 로컬 개발과 프로덕션 타임아웃 설정 비교

---

## 섹션 4: Bug-3 - LangGraph GraphRecursionError

### 증상

```
langchain_core.exceptions.LangChainException:
Recursion limit of 25 reached without hitting a stop condition.
You can increase the limit by setting the "recursion_limit" config key.
```

### 근본 원인: LangGraph Send() API의 상태 업데이트 동작

이 버그를 이해하려면 LangGraph의 두 가지 라우팅 방식의 차이를 알아야 합니다.

**일반 조건부 엣지 (Conditional Edge)**
```python
graph.add_conditional_edges("node_a", route_fn)
# route_fn이 반환한 노드로 이동하며, 현재 그래프 상태를 그대로 사용
```

**Send() API (동적 라우팅)**
```python
graph.add_conditional_edges("node_a", lambda state: [Send("node_b", custom_state)])
# node_b에 custom_state를 입력으로 제공하지만,
# 그래프 전역 상태(graph-level state)는 custom_state로 업데이트되지 않음!
```

Send()의 핵심 특징:
- Send()로 제공한 상태는 해당 노드의 입력(input state)으로만 사용됩니다.
- 그래프의 전역 상태는 Send()로 업데이트되지 않습니다.
- 노드가 실행된 후 반환하는 딕셔너리가 그래프 전역 상태를 업데이트합니다.

### 버그 발생 과정

```python
# 문제가 된 image_processor_node의 반환값 (수정 전)
return {"extracted_text": extracted_text, "input_text": extracted_text}
# task_type을 반환하지 않음!
```

1. 초기 상태: `graph_state.task_type = "image_process"`
2. `supervisor_node` 실행 (skip, 빈 input_text)
3. `route_by_task("image_process")` → `image_processor` 실행
4. `image_processor`가 반환: `{"extracted_text": "...", "input_text": "..."}`
5. 그래프 상태 업데이트: `task_type`은 여전히 `"image_process"` (업데이트 안 됨!)
6. `route_after_image` → `Send("supervisor", {input_text=extracted_text, task_type="analyze"})`
7. `supervisor_node`가 Send() 입력으로 `task_type="analyze"`를 받아 실행
8. `supervisor_node`가 반환: `{...supervisor_analysis...}` (task_type 반환 안 함)
9. 그래프 상태: `task_type = "image_process"` (여전히!)
10. `route_by_task("image_process")` → `image_processor` 다시 실행
11. 무한 루프 → RecursionError 발생

### 수정

```python
# 수정 후 image_processor_node
return {
    "extracted_text": extracted_text,
    "input_text": extracted_text,
    "task_type": "analyze"  # 그래프 상태 업데이트!
}
```

이제 `image_processor_node`가 완료된 후:
- 그래프 상태: `task_type = "analyze"`
- `route_after_image` → `Send("supervisor", {..., task_type="analyze"})`
- `supervisor_node` 실행 후 → `route_by_task("analyze")` → 분석 에이전트로 라우팅

추가로 재귀 한도를 증가시켜 안전망을 만들었습니다:
```python
app = graph.compile()
config = {"recursion_limit": 50}  # 기본값 25 → 50
```

### LangGraph Send() vs 일반 라우팅 비교

| 특성 | 일반 조건부 엣지 | Send() API |
|------|-----------------|------------|
| 사용 목적 | 단순 분기 | 동적 멀티-에이전트 팬아웃 |
| 상태 전달 | 현재 그래프 상태 | 커스텀 상태 (노드별) |
| 그래프 상태 업데이트 | 노드 출력으로 업데이트 | Send() 입력은 업데이트 안 함 |
| 병렬 실행 | 불가 | 가능 (여러 Send 동시 실행) |
| 주요 사용 사례 | 단순 라우팅 | 병렬 분석, 맵-리듀스 패턴 |

### 학습 원칙

**[원칙-3] LangGraph 노드는 그래프 상태를 명시적으로 업데이트해야 한다.**

Send()로 전달한 커스텀 상태는 해당 노드의 입력에만 영향을 미칩니다. 그래프 전역 상태를 변경하려면 노드가 반환하는 딕셔너리에 해당 키를 포함해야 합니다.

**LangGraph 노드 반환값 체크리스트:**
- [ ] 다음 라우팅에 영향을 주는 모든 상태 키를 반환에 포함
- [ ] 특히 `task_type`, `extracted_text`, `input_text` 등 라우팅 결정에 사용되는 필드
- [ ] Send()를 사용하는 노드는 반환값이 그래프 전역 상태를 업데이트함을 명심

**Send() API 사용 시 주의사항:**
- Send()의 두 번째 인자(커스텀 상태)는 해당 노드 실행에만 사용됩니다.
- 노드 자체의 반환값이 그래프 상태를 업데이트합니다.
- 순환 가능성이 있는 그래프는 `recursion_limit`을 적절히 설정하세요.

---

## 섹션 5: Bug-4 - 무증상 오류 (Silent Failures)

### 증상

이미지 분석이 실패해도 UI는 빈 결과만 보여주고 오류 메시지가 없었습니다. 사용자는 무엇이 잘못되었는지 알 수 없었습니다.

### 근본 원인: response.ok 미확인

```typescript
// 수정 전 use-tutor-stream.ts
const startStream = useCallback(async (fetchFn: () => Promise<Response>) => {
  // ...
  const response = await fetchFn();
  // response.ok 확인 없음!

  const reader = response.body?.getReader();
  // HTTP 오류 응답의 경우 body가 오류 메시지지만 그냥 읽기 시작
```

HTTP 4xx/5xx 응답이 오더라도 `response.ok`를 확인하지 않으면:
1. 오류 응답의 body를 SSE 스트림으로 오해
2. JSON이나 HTML 오류 메시지를 SSE 이벤트로 파싱 실패
3. 조용히 종료 → 빈 결과 화면

### 수정

```typescript
const response = await fetchFn();

// HTTP 오류 상태 즉시 처리
if (!response.ok) {
  const errorText = await response.text().catch(() => "");
  let errorMessage = `Analysis failed (${response.status})`;
  try {
    const errorData = JSON.parse(errorText);
    errorMessage = errorData.error || errorData.detail || errorMessage;
  } catch {
    // JSON이 아닌 경우 기본 메시지 사용
  }
  throw new Error(errorMessage);
}

// 여기부터 response.ok인 경우만 실행
const reader = response.body?.getReader();
```

### 학습 원칙

**[원칙-4] 모든 HTTP 스트리밍 핸들러는 response.ok를 먼저 확인하라.**

스트리밍(SSE, ReadableStream) 처리에서 `response.ok`를 확인하지 않으면:
- 오류 응답이 조용히 무시됨
- 사용자는 오류 메시지 없이 빈 결과만 봄
- 디버깅이 매우 어려워짐

**모든 스트림 핸들러의 기본 패턴:**
```typescript
const response = await fetchFn();
if (!response.ok) {
  // 오류 처리 (필수!)
  throw new Error(`Request failed: ${response.status}`);
}
// 스트림 읽기 시작
```

---

## 섹션 6: 조사 방법론

### 이 버그들을 어떻게 발견했나

**1단계: 로그 우선 확인**

버그가 발생했을 때 가장 먼저 할 일은 코드를 수정하는 것이 아니라 로그를 확인하는 것입니다.

- Railway 백엔드 로그 → "No image_data provided" 메시지 발견
- Vercel 함수 로그 → 타임아웃 오류 메시지 발견
- LangGraph 실행 로그 → RecursionError 스택 트레이스 발견

**2단계: 데이터 흐름 추적**

```
Frontend (브라우저)
    → Next.js Route Handler (/api/tutor/analyze-image)
    → FastAPI (/api/v1/tutor/analyze-image)
    → LangGraph StateGraph
        → supervisor_node
        → image_processor_node
        → analysis agents
    → SSE 스트리밍 응답
```

각 단계에서 데이터가 올바르게 전달되는지 확인했습니다.

**3단계: 최소 변경 가설 검증**

문제를 발견하면 최소한의 코드 변경으로 가설을 검증합니다:
- `print(state.get("image_data", "NOT FOUND"))` 로그 추가
- 상태가 실제로 전달되는지 확인
- TypedDict 추가 후 재확인

**4단계: 공식 문서 참조**

LangGraph Send()의 동작을 오해했을 때, 공식 LangGraph 문서를 다시 읽어 Send()가 그래프 상태를 업데이트하지 않는다는 것을 확인했습니다.

### 디버깅 도구

```python
# LangGraph 상태 디버깅
import logging
logger = logging.getLogger(__name__)

async def my_node(state: TutorState) -> dict:
    logger.debug(f"State keys: {list(state.keys())}")
    logger.debug(f"task_type: {state.get('task_type', 'MISSING')}")
    # ...
```

```python
# LangGraph 그래프 시각화
from IPython.display import Image
img = app.get_graph().draw_mermaid_png()
# 또는
print(app.get_graph().draw_ascii())
```

---

## 섹션 7: 미래 예방 전략

### 1. 이미지 처리 통합 테스트 추가

현재 누락된 테스트:
```python
# backend/tests/integration/test_image_pipeline.py (미작성)
async def test_image_analysis_end_to_end():
    """Mock 이미지로 전체 파이프라인 테스트"""
    # Base64 인코딩된 테스트 이미지 준비
    # LangGraph 그래프 실행
    # 결과 검증: extracted_text, supervisor_analysis, 분석 결과
```

```typescript
// src/hooks/use-tutor-stream.test.ts (추가 필요)
test("HTTP 오류 시 에러 상태 설정", async () => {
  const fetchFn = () => Promise.resolve(new Response("Error", { status: 500 }));
  const { result } = renderHook(() => useTutorStream());
  await act(async () => {
    await result.current.startStream(fetchFn);
  });
  expect(result.current.state.error).toBeTruthy();
});
```

### 2. 배포 전 체크리스트 (타임아웃 민감 기능)

```markdown
## 이미지/LLM API 배포 체크리스트

### 타임아웃 설정
- [ ] Vercel `maxDuration` 설정 (이미지 처리: 60초 추천)
- [ ] Railway 서버 timeout 설정 확인
- [ ] SSE 하트비트 간격 설정 (5초 이하 추천)

### LangGraph 상태 관리
- [ ] 새로운 상태 필드를 TutorState TypedDict에 추가
- [ ] Send()를 사용하는 노드의 반환값에 task_type 포함
- [ ] recursion_limit 설정 (기본값 25, 복잡한 그래프는 50+)

### 프론트엔드 오류 처리
- [ ] response.ok 확인 후 스트림 읽기
- [ ] 오류 메시지 사용자에게 표시

### 테스트
- [ ] 로컬에서 전체 파이프라인 테스트
- [ ] Staging 환경에서 타임아웃 시나리오 테스트
```

### 3. LangGraph 패턴 문서화

이 프로젝트에서 사용하는 LangGraph 패턴을 문서화합니다:
- Send() 패턴: 언제 사용하고 어떻게 상태를 관리하는지
- 조건부 엣지 패턴: 단순 라우팅에 사용
- 재귀 방지 패턴: task_type 상태 관리

### 4. Vercel 환경 설정 가이드

```typescript
// 권장 Vercel 설정 패턴
// LLM API 사용 Route Handler
export const maxDuration = 60; // 필수: LLM 처리 시간 > 10초

// 일반 API Route Handler
// maxDuration 생략 가능 (기본 10초로 충분)
```

---

## 섹션 8: 기억해야 할 코드 패턴

### 패턴 1: LangGraph TypedDict에서 선택적 필드 정의

```python
from typing import NotRequired, TypedDict

class TutorState(TypedDict):
    # 필수 필드
    input_text: str
    task_type: str

    # 선택적 필드 (이미지 분석 전용)
    image_data: NotRequired[str | None]    # base64 인코딩
    mime_type: NotRequired[str | None]     # "image/jpeg" 등

    # 선택적 필드 (분석 결과)
    reading_result: NotRequired[ReadingResult | None]
```

이 패턴을 사용하면:
- 텍스트 분석 시 `image_data`를 초기화하지 않아도 됨
- 이미지 분석 시에만 해당 필드 설정
- LangGraph가 상태를 올바르게 전파함

### 패턴 2: SSE 하트비트 구현

```python
import asyncio
from sse_starlette.sse import EventSourceResponse

async def streaming_endpoint():
    queue = asyncio.Queue()
    stop_event = asyncio.Event()

    async def heartbeat_producer():
        """프록시 idle timeout 방지용 주기적 하트비트"""
        while not stop_event.is_set():
            await asyncio.sleep(5)  # 5초 간격
            if not stop_event.is_set():
                await queue.put(": comment\n\n")  # SSE 주석 형식

    async def content_producer():
        """실제 콘텐츠 생성"""
        try:
            # LLM 처리...
            async for event in streaming:
                await queue.put(event)
        finally:
            stop_event.set()
            await queue.put(None)  # 종료 신호

    # 두 생산자를 동시에 실행
    asyncio.create_task(heartbeat_producer())
    asyncio.create_task(content_producer())

    async def event_generator():
        while True:
            item = await queue.get()
            if item is None:
                break
            yield item

    return EventSourceResponse(event_generator())
```

SSE 하트비트 형식 `": comment\n\n"`:
- 줄 앞의 `:`는 SSE 주석 형식 (RFC 8895)
- `\n\n`는 SSE 이벤트 구분자
- 브라우저와 SSE 클라이언트는 이를 무시
- 프록시는 실제 데이터로 인식하여 idle timeout 리셋

### 패턴 3: Vercel 장시간 실행 Route Handler

```typescript
// Vercel Route Handler에서 LLM 사용 시
export const maxDuration = 60; // 반드시 파일 최상위에 export

export async function POST(request: NextRequest) {
  // LLM 호출, 이미지 처리 등 시간이 걸리는 작업
}
```

주의사항:
- `maxDuration`은 파일 최상위 레벨에 `export const`로 선언
- Hobby 플랜 최대값: 60초
- Pro 플랜 최대값: 300초

### 패턴 4: LangGraph Send()로 동적 라우팅

```python
from langgraph.types import Send

def route_after_image(state: TutorState) -> list[Send]:
    """OCR 후 라우팅: 텍스트가 있으면 supervisor로, 없으면 aggregator로"""
    extracted_text = state.get("extracted_text", "")

    if extracted_text:
        # supervisor에 새로운 상태로 Send
        new_state = {
            **state,
            "input_text": extracted_text,
            "task_type": "analyze",  # 중요: supervisor가 올바르게 동작하도록
        }
        return [Send("supervisor", new_state)]
    else:
        # 텍스트 없으면 aggregator로 바로
        return [Send("aggregator", state)]
```

Send() 사용 규칙:
- Send()의 두 번째 인자는 해당 노드의 입력 상태
- 그래프 전역 상태를 업데이트하려면 노드의 반환값에 포함
- 현재 그래프 상태를 기반으로 커스텀 상태를 만들 때는 `{**state, ...overrides}` 패턴 사용

### 패턴 5: LangGraph 노드에서 그래프 상태 업데이트

```python
async def image_processor_node(state: TutorState) -> dict:
    """이미지에서 텍스트 추출"""
    # ...처리 코드...

    # 반환값이 그래프 전역 상태를 업데이트
    return {
        "extracted_text": extracted_text,
        "input_text": extracted_text,
        "task_type": "analyze",  # 필수! 다음 라우팅에 영향을 줌
    }
    # 반환하지 않은 키(예: image_data, mime_type)는 그래프 상태에서 유지됨
```

노드 반환값 원칙:
- 반환된 딕셔너리의 키만 그래프 상태를 업데이트
- 반환하지 않은 키는 기존 상태를 유지
- 라우팅 결정에 사용되는 키는 반드시 반환에 포함

### 패턴 6: 스트림 핸들러에서 HTTP 오류 처리

```typescript
export function useTutorStream() {
  const startStream = useCallback(async (fetchFn: () => Promise<Response>) => {
    setState(prev => ({ ...prev, isStreaming: true, error: null }));

    try {
      const response = await fetchFn();

      // 필수: HTTP 오류 상태 먼저 확인
      if (!response.ok) {
        const errorText = await response.text().catch(() => "");
        let errorMessage = `Analysis failed (${response.status})`;
        try {
          const errorData = JSON.parse(errorText);
          errorMessage = errorData.error || errorData.detail || errorMessage;
        } catch {
          // JSON이 아닌 경우 기본 메시지 사용
        }
        throw new Error(errorMessage);
      }

      // 이후 스트림 처리...
    } catch (error) {
      setState(prev => ({ ...prev, isStreaming: false, error }));
    }
  }, []);
}
```

---

## 섹션 9: 타임라인과 커밋

### 커밋 상세

**커밋 e624069** (2026-02-24 01:12)
```
fix: add image_data and mime_type to TutorState for LangGraph state propagation
```
- 파일: `backend/src/tutor/state.py`
- 변경: `image_data: NotRequired[str | None]`, `mime_type: NotRequired[str | None]` 추가
- 효과: 이미지 데이터가 LangGraph를 통해 정상 전달됨

---

**커밋 477f00b** (2026-02-24 01:40)
```
fix: prevent SSE timeout during image analysis with heartbeat and maxDuration
```
- 파일: `backend/src/tutor/routers/tutor.py`, `src/app/api/tutor/analyze-image/route.ts`, `src/app/api/tutor/analyze/route.ts`, `src/hooks/use-tutor-stream.ts`
- 변경:
  - 백엔드: SSE 하트비트 5초 간격 추가
  - 프론트엔드 라우트: `maxDuration=60` 추가
  - 훅: 백엔드 SSE 오류 이벤트 처리 추가
- 효과: 이미지 분석이 타임아웃 없이 완료됨

---

**커밋 31f9fb9** (2026-02-24 06:36)
```
fix: resolve GraphRecursionError in image analysis pipeline
```
- 파일: `backend/src/tutor/agents/image_processor.py`, `backend/src/tutor/routers/tutor.py`, `backend/tests/unit/test_agents.py`, `src/hooks/use-tutor-stream.ts`
- 변경:
  - `image_processor_node` 반환값에 `task_type: "analyze"` 추가
  - `recursion_limit` 50으로 증가
  - 하트비트 생산자 오류 처리 개선
  - 프론트엔드: `response.ok` 검증 추가
- 효과: 무한 루프 해소, 오류 사용자 표시

---

### 최종 상태 확인

- 커밋 후 사용자 테스트: 성공
- 사용자 피드백: "잘 동작한다"
- 배포 상태: 안정적 운영 중

---

## 요약: 핵심 원칙 6가지

1. **TypedDict = 스키마**: LangGraph 상태로 전달하는 모든 필드는 TypedDict에 정의하라
2. **서버리스 타임아웃 명시**: LLM API를 사용하는 경우 항상 `maxDuration` 설정하라
3. **SSE 하트비트**: 장시간 스트리밍 시 5초 이하 간격으로 `: comment` 전송하라
4. **Send() 이해**: Send()는 노드 입력을 제공하지만 그래프 상태는 업데이트하지 않는다
5. **노드 반환값**: 라우팅에 영향을 주는 모든 상태 키를 노드 반환값에 포함하라
6. **response.ok 검증**: 모든 HTTP 스트리밍 핸들러에서 응답 상태를 먼저 확인하라
