# Plan: Token-Level Streaming Output

> v2 - 레드팀/블루팀 검토 반영 (2026-02-23)

## Context

현재 백엔드는 `graph.ainvoke()`로 reading/grammar/vocabulary 3개 에이전트가 모두 완료된 후에야 SSE 이벤트를 일괄 전송한다. 프론트엔드는 완성된 청크를 한 번에 받아 상태를 교체하기 때문에 분석 결과가 한꺼번에 뚝 표시된다.

**목표**: LLM이 토큰을 생성하는 즉시 글자 단위로 스트리밍하여 ChatGPT처럼 타이핑 효과를 구현하고, 3개 탭 간 이동 시에도 각 탭의 스트리밍 상태가 유지되도록 한다.

---

## 핵심 설계 결정

### 섹션별 스트리밍 전략

| 섹션 | 전략 | 이유 |
|------|------|------|
| 독해(Reading) | 토큰 단위 스트리밍 | Markdown 텍스트 → 글자씩 append |
| 문법(Grammar) | 토큰 단위 스트리밍 | Markdown 텍스트 → 글자씩 append |
| 어휘(Vocabulary) | 완료 후 일괄 표시 | `VocabularyWordEntry[]` 구조체 → 토큰 스트리밍 불가 |

### 새로운 SSE 이벤트 스키마

```
# 기존 이벤트 (변경 없음)
event: vocabulary_chunk
data: {"words": [...]}

event: done
data: {"session_id": "..."}

# 신규 이벤트
event: reading_token
data: {"token": "증분 텍스트"}

event: grammar_token
data: {"token": "증분 텍스트"}

event: reading_done    ← reading 노드 완료 신호
data: {}

event: grammar_done    ← grammar 노드 완료 신호
data: {}
```

### LangGraph `astream_events` 이벤트 타입 구분 [중요]

LangGraph 0.3.x의 `astream_events(version="v2")`는 이벤트 타입에 따라 노드 식별 방법이 다르다:

| 이벤트 종류 | 노드 식별 키 | 예시 |
|-------------|-------------|------|
| `on_chat_model_stream` (LLM 토큰) | `event["metadata"]["langgraph_node"]` | `"reading"`, `"grammar"` |
| `on_chain_end` (노드 완료) | `event["name"]` | `"reading"`, `"aggregator"` |

### Aggregator 출력 구조 [중요]

`aggregator.py` (line 47)의 실제 반환값:
```python
return {"analyze_response": AnalyzeResponse(...)}
```
- `vocabulary_result` 키로 직접 접근 **불가**
- `output["analyze_response"].vocabulary`로 접근해야 함

### 탭 이동 중 스트리밍 유지

- React 상태는 탭 전환과 무관하게 축적 계속 (Reading/Grammar 모두 동시 스트리밍)
- 각 탭 라벨에 섹션별 스트리밍 인디케이터 표시
- `isStreaming` 중이면 빈 내용이어도 탭 UI 즉시 표시 (`hasContent` 로직 수정)

---

## 구현 계획

### Phase 1: 백엔드 (3개 파일)

#### 1. `backend/src/tutor/models/llm.py`
`ChatOpenAI` 생성자에 `streaming=True` 추가 (line 63, line 77).
이 설정 없으면 `astream_events`가 `on_chat_model_stream` 이벤트를 방출하지 않음.

```python
# line 63
return ChatOpenAI(
    model=model_name,
    streaming=True,   # 추가
    timeout=timeout,
    ...
)
```

#### 2. `backend/src/tutor/services/streaming.py`
기존 함수 유지 + 신규 추가:

```python
def format_reading_token(token: str) -> str:
    return format_sse_event("reading_token", {"token": token})

def format_grammar_token(token: str) -> str:
    return format_sse_event("grammar_token", {"token": token})

def format_section_done(section: str) -> str:
    """section: 'reading' or 'grammar'"""
    return format_sse_event(f"{section}_done", {})
```

#### 3. `backend/src/tutor/routers/tutor.py`

`/tutor/analyze`와 `/tutor/analyze-image` 엔드포인트의 `generate()` 함수 교체:

```python
async def generate() -> AsyncGenerator[str]:
    session_id = session_manager.create()
    input_state = {
        "messages": [], "level": request.level,
        "session_id": session_id,
        "input_text": request.text,
        "task_type": "analyze",
    }

    try:
        async for event in graph.astream_events(input_state, version="v2"):
            kind = event["event"]

            # 1. LLM 토큰 스트리밍
            # on_chat_model_stream → metadata["langgraph_node"]으로 노드 식별
            if kind == "on_chat_model_stream":
                token = event["data"]["chunk"].content
                if not token:
                    continue
                node = event.get("metadata", {}).get("langgraph_node", "")
                if node == "reading":
                    yield format_reading_token(token)
                elif node == "grammar":
                    yield format_grammar_token(token)

            # 2. 노드 완료 신호
            # on_chain_end → event["name"]으로 노드 식별
            elif kind == "on_chain_end":
                node_name = event.get("name", "")
                output = event["data"].get("output", {})

                if node_name == "reading":
                    yield format_section_done("reading")
                elif node_name == "grammar":
                    yield format_section_done("grammar")

                # 3. 어휘 결과 추출 (aggregator 완료 시)
                # aggregator.py가 반환: {"analyze_response": AnalyzeResponse(...)}
                elif node_name == "aggregator" and isinstance(output, dict):
                    analyze_response = output.get("analyze_response")
                    if analyze_response and analyze_response.vocabulary:
                        yield format_vocabulary_chunk(
                            analyze_response.vocabulary.model_dump()
                        )

        yield format_done_event(session_id)

    except asyncio.CancelledError:
        # 클라이언트 연결 끊김 처리
        pass
    except Exception as e:
        yield format_error_event(str(e), "processing_error")
```

**`import asyncio`** 추가 필요.

---

### Phase 2: 프론트엔드 (7개 파일)

#### 4. `src/types/tutor.ts`
섹션별 스트리밍 상태 인터페이스 추가:

```typescript
export interface SectionStreamingState {
  readingStreaming: boolean;
  grammarStreaming: boolean;
  vocabularyStreaming: boolean;
}
```

#### 5. `src/hooks/use-tutor-stream.ts`

**`TutorStreamState` 인터페이스 확장:**
```typescript
export interface TutorStreamState {
  readingContent: string;
  grammarContent: string;
  vocabularyWords: VocabularyWordEntry[];
  isStreaming: boolean;
  readingStreaming: boolean;    // 추가
  grammarStreaming: boolean;    // 추가
  vocabularyStreaming: boolean; // 추가
  error: Error | null;
}
```

**초기 상태에 추가:**
```typescript
const [state, setState] = useState<TutorStreamState>({
  ...,
  readingStreaming: false,
  grammarStreaming: false,
  vocabularyStreaming: false,
});
```

**스트림 시작 시 초기화:**
```typescript
setState((prev) => ({
  ...prev,
  isStreaming: true,
  readingStreaming: true,    // 추가
  grammarStreaming: true,    // 추가
  vocabularyStreaming: true, // 추가
  error: null,
  readingContent: "",
  grammarContent: "",
  vocabularyWords: [],
}));
```

**새 이벤트 처리 (append 방식, replace 아님):**
```typescript
if (currentEvent === "reading_token") {
  // APPEND (기존 reading_chunk는 replace였음 - 핵심 변경점)
  setState((prev) => ({
    ...prev,
    readingContent: prev.readingContent + (data.token || ""),
  }));
} else if (currentEvent === "grammar_token") {
  setState((prev) => ({
    ...prev,
    grammarContent: prev.grammarContent + (data.token || ""),
  }));
} else if (currentEvent === "reading_done") {
  setState((prev) => ({ ...prev, readingStreaming: false }));
} else if (currentEvent === "grammar_done") {
  setState((prev) => ({ ...prev, grammarStreaming: false }));
} else if (currentEvent === "vocabulary_chunk") {
  setState((prev) => ({
    ...prev,
    vocabularyWords: data.words || [],
    vocabularyStreaming: false,
  }));
}
```

**`done` 이벤트 처리 시 모든 섹션 플래그 해제:**
```typescript
if (currentEvent === "done") {
  setState((prev) => ({
    ...prev,
    isStreaming: false,
    readingStreaming: false,
    grammarStreaming: false,
    vocabularyStreaming: false,
  }));
  return;
}
```

**`reset()` 함수에도 초기화 추가:**
```typescript
setState({
  ...,
  readingStreaming: false,
  grammarStreaming: false,
  vocabularyStreaming: false,
});
```

#### 6. `src/components/tutor/tabbed-output.tsx`

**Props 확장:**
```typescript
interface TabbedOutputProps {
  reading: ReadingResult | null;
  grammar: GrammarResult | null;
  vocabulary: VocabularyResult | null;
  isStreaming?: boolean;
  readingStreaming?: boolean;
  grammarStreaming?: boolean;
  vocabularyStreaming?: boolean;
  className?: string;
}
```

**`hasContent` 로직 수정 (스트리밍 시작 즉시 탭 표시):**
```typescript
// 기존: const hasContent = reading || grammar || vocabulary;
const hasContent = isStreaming || reading || grammar || vocabulary;
```

**탭 라벨에 스트리밍 인디케이터 (접근성 포함):**
```tsx
<TabsTrigger value="reading">
  독해
  {readingStreaming && (
    <span
      className="inline-block w-2 h-2 bg-blue-500 rounded-full animate-pulse ml-1"
      aria-label="독해 분석 중"
      role="status"
    />
  )}
</TabsTrigger>
<TabsTrigger value="grammar">
  문법
  {grammarStreaming && (
    <span
      className="inline-block w-2 h-2 bg-blue-500 rounded-full animate-pulse ml-1"
      aria-label="문법 분석 중"
      role="status"
    />
  )}
</TabsTrigger>
<TabsTrigger value="vocabulary">
  어휘
  {vocabularyStreaming && (
    <span
      className="inline-block w-2 h-2 bg-blue-500 rounded-full animate-pulse ml-1"
      aria-label="어휘 분석 중"
      role="status"
    />
  )}
</TabsTrigger>
```

**패널에 스트리밍 props 전달:**
```tsx
<ReadingPanel result={reading} isStreaming={readingStreaming} />
<GrammarPanel result={grammar} isStreaming={grammarStreaming} />
<VocabularyPanel result={vocabulary} isStreaming={vocabularyStreaming} />
```

#### 7. `src/components/tutor/reading-panel.tsx`

**Props + 스트리밍 커서:**
```typescript
interface ReadingPanelProps {
  result: ReadingResult | null;
  isStreaming?: boolean;
  className?: string;
}
```

스트리밍 중 빈 상태 표시 (result가 없어도 스트리밍 중이면 컨테이너 표시):
```tsx
if (!result && !isStreaming) {
  return <Card>...빈 상태...</Card>;
}
return (
  <Card className={className}>
    <CardHeader>
      <CardTitle className="text-lg">독해 훈련</CardTitle>
    </CardHeader>
    <CardContent>
      <div className="prose prose-sm dark:prose-invert max-w-none">
        {result && <ReactMarkdown>{result.content}</ReactMarkdown>}
      </div>
      {isStreaming && (
        <span
          className="inline-block w-0.5 h-4 bg-current animate-pulse ml-0.5"
          aria-label="텍스트 생성 중"
          role="status"
        />
      )}
    </CardContent>
  </Card>
);
```

#### 8. `src/components/tutor/grammar-panel.tsx`
ReadingPanel과 동일한 패턴 적용.

#### 9. `src/components/tutor/vocabulary-panel.tsx`

**스켈레톤 로딩 상태 (단어 수 미확정으로 동적 표시):**
```typescript
interface VocabularyPanelProps {
  result: VocabularyResult | null;
  isStreaming?: boolean;
  className?: string;
}
```

```tsx
if (isStreaming && !result) {
  // 스켈레톤: 고정 3개 아닌 추상적 로딩 표시
  return (
    <div className="space-y-3">
      <div className="p-4 rounded-lg border animate-pulse">
        <div className="flex items-center gap-3">
          <div className="w-4 h-4 bg-muted rounded-full" />
          <div className="text-sm text-muted-foreground">어휘 분석 중...</div>
        </div>
        <div className="mt-3 space-y-2">
          <div className="h-3 bg-muted rounded w-full" />
          <div className="h-3 bg-muted rounded w-4/5" />
          <div className="h-3 bg-muted rounded w-3/5" />
        </div>
      </div>
    </div>
  );
}
```

---

### Phase 3: Props 전달 체인 (2개 파일)

#### 10. `src/components/layout/desktop-layout.tsx`

`TabbedOutput` 호출 시 스트리밍 flags 추가 (line 89-105):
```tsx
<TabbedOutput
  reading={streamState.readingContent ? { content: streamState.readingContent } : null}
  grammar={streamState.grammarContent ? { content: streamState.grammarContent } : null}
  vocabulary={
    streamState.vocabularyWords?.length > 0
      ? { words: streamState.vocabularyWords }
      : null
  }
  isStreaming={streamState.isStreaming}                          // 추가
  readingStreaming={streamState.readingStreaming}                // 추가
  grammarStreaming={streamState.grammarStreaming}                // 추가
  vocabularyStreaming={streamState.vocabularyStreaming}          // 추가
/>
```

#### 11. `src/components/mobile/analysis-view.tsx`

`AnalysisView`가 `streamState`를 받아 `TabbedOutput`에 전달:
```tsx
// AnalysisView props 확장
interface AnalysisViewProps {
  streamState: TutorStreamState;
  level: number;
}

// TabbedOutput 호출 시 streaming props 추가
<TabbedOutput
  ...기존 props...
  isStreaming={streamState.isStreaming}
  readingStreaming={streamState.readingStreaming}
  grammarStreaming={streamState.grammarStreaming}
  vocabularyStreaming={streamState.vocabularyStreaming}
/>
```

`page.tsx`와 `mobile-layout.tsx`는 이미 `streamState` 전체를 전달하므로 수정 불필요.

---

### Phase 4: 테스트 업데이트 (1개 파일)

#### 12. `src/hooks/__tests__/use-tutor-stream.test.ts`

기존 5개 테스트 유지 + 신규 6개 추가:

```typescript
// 신규 테스트 1: reading_token append 동작
it("should append multiple reading_token events sequentially", async () => {
  // 'He', 'llo', ' World' 3개 토큰 → 'Hello World' 합산 검증
});

// 신규 테스트 2: grammar_token append 동작
it("should append grammar_token events without overwriting", async () => {});

// 신규 테스트 3: reading_done이 readingStreaming만 false로
it("should set readingStreaming to false on reading_done event", async () => {
  // grammarStreaming은 여전히 true 유지 검증
});

// 신규 테스트 4: grammar_done이 grammarStreaming만 false로
it("should set grammarStreaming to false on grammar_done event", async () => {});

// 신규 테스트 5: vocabulary_chunk가 vocabularyStreaming false 설정
it("should set vocabularyStreaming to false when vocabulary_chunk arrives", async () => {});

// 신규 테스트 6: 초기 상태에 섹션별 스트리밍 플래그 포함
it("should initialize all section streaming flags to false", async () => {
  // readingStreaming, grammarStreaming, vocabularyStreaming 모두 false 확인
});
```

---

## 수정 파일 목록

| 파일 | 변경 유형 | 검토 이슈 |
|------|----------|----------|
| `backend/src/tutor/models/llm.py` | `streaming=True` 추가 | Red #3 |
| `backend/src/tutor/services/streaming.py` | 토큰/완료 포맷터 추가 | - |
| `backend/src/tutor/routers/tutor.py` | ainvoke → astream_events, 올바른 집계 추출 | Red #1,2 |
| `src/types/tutor.ts` | `SectionStreamingState` 추가 | Blue #2 |
| `src/hooks/use-tutor-stream.ts` | append 로직 + 섹션 상태 + 이벤트 핸들러 | Red #4, Blue #1,3 |
| `src/components/tutor/tabbed-output.tsx` | streaming props + hasContent 수정 | Blue #4 |
| `src/components/tutor/reading-panel.tsx` | 커서 + ARIA + 빈 상태 처리 | Blue #8 |
| `src/components/tutor/grammar-panel.tsx` | 동상 | Blue #8 |
| `src/components/tutor/vocabulary-panel.tsx` | 동적 스켈레톤 로딩 | Blue #10 |
| `src/components/layout/desktop-layout.tsx` | TabbedOutput에 streaming props 전달 | Blue #5 |
| `src/components/mobile/analysis-view.tsx` | TabbedOutput에 streaming props 전달 | Blue #13 |
| `src/hooks/__tests__/use-tutor-stream.test.ts` | 신규 토큰 이벤트 테스트 추가 | Blue #12 |

---

## 레드팀/블루팀 검토 결과 요약

### 수정된 크리티컬 이슈

| # | 이슈 | 조치 |
|---|------|------|
| R1 | aggregator `output["vocabulary_result"]` → `output["analyze_response"].vocabulary` | 플랜 코드 수정 |
| R2 | `on_chain_end` 이벤트는 `event["name"]`으로, `on_chat_model_stream`은 `metadata["langgraph_node"]`으로 노드 식별 | 이벤트 타입별 분기 명시 |
| R4 | 프론트엔드 append vs replace 로직 혼동 | 명시적 append 코드 추가 |
| B4 | `hasContent`에 `isStreaming` 미포함 → 스트리밍 시작 후에도 빈 화면 | 수정 |
| B5 | DesktopLayout → TabbedOutput props 체인 미명시 | 명시적 코드 추가 |
| B13 | `analysis-view.tsx` → TabbedOutput props 체인 미명시 | 명시적 코드 추가 |

### 미채택 제안 (의도적 제외)

- **토큰 배칭(B9)**: 50ms 지연은 스트리밍 UX 목적에 반함. 기본 성능 최적화는 React 배치 업데이트에 위임.
- **섹션별 Error 상태(B14)**: 현재 scope 외. 전체 error 상태로 충분.
- **탭 자동 포커스(B15)**: 사용자 탭 선택 방해 가능성. 미포함.

---

## 검증 방법

1. **백엔드 서버 실행**: `cd backend && uvicorn tutor.main:app --reload`
2. **프론트엔드 실행**: `pnpm dev`
3. **텍스트 제출** 후 관찰:
   - 독해 탭: 글자가 하나씩 타이핑되듯 나타나며 탭에 파란 점 표시
   - 문법 탭: 동일하게 글자 단위 스트리밍 + 파란 점 표시
   - 어휘 탭: 로딩 스켈레톤 표시 → 완료 시 단어 카드 표시
4. **탭 전환 테스트**: 스트리밍 중 탭 이동 후 돌아와도 내용 유지 및 계속 쌓임
5. **백엔드 테스트**: `cd backend && pytest` (기존 테스트 통과 확인)
6. **프론트엔드 테스트**: `pnpm test` (기존 5개 + 신규 6개 테스트)
7. **접근성 확인**: 스크린리더로 스트리밍 인디케이터의 `aria-label` 읽힘 확인
