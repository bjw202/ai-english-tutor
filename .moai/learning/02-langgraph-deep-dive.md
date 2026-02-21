# AI 영어 튜터 백엔드 가이드 - 2부: LangGraph 멀티 에이전트

> State, Message 전달 및 병렬 실행 상세 설명

---

## 1. LangGraph란?

**LangGraph**는 여러 AI 에이전트가 협력해서 일할 수 있게 해주는 프레임워크입니다.

### 1.1 비유로 이해하기

```
회사 조직도:

    CEO (Supervisor)
         │
    ┌────┼────┐
    │    │    │
  영업  개발  디자인
  (Reading) (Grammar) (Vocabulary)
    │    │    │
    └────┼────┘
         │
    보고서 취합 (Aggregator)
```

### 1.2 왜 LangGraph를 쓰나요?

| 기존 방식 | LangGraph 방식 |
|----------|---------------|
| if-else로 분기 | 그래프로 흐름 정의 |
| 순차 실행만 가능 | 병렬 실행 지원 |
| 상태 관리 어려움 | State 자동 병합 |
| 재사용 어려움 | 모듈화된 노드 |

---

## 2. State (상태) 상세 설명

### 2.1 State가 뭐죠?

**State** = 에이전트들이 주고받는 **공유 데이터 컨테이너**

```python
# state.py
from typing import TypedDict, NotRequired

class TutorState(TypedDict):
    # ===== 필수 필드 (처음에 채워짐) =====
    messages: list[dict]      # 대화 내역
    level: int                # 학습 레벨 (1-5)
    session_id: str           # 세션 ID
    input_text: str           # 분석할 텍스트
    task_type: str            # 작업 유형

    # ===== 선택 필드 (에이전트가 채움) =====
    reading_result: NotRequired[ReadingResult | None]
    grammar_result: NotRequired[GrammarResult | None]
    vocabulary_result: NotRequired[VocabularyResult | None]
    extracted_text: NotRequired[str | None]
```

### 2.2 State 생애주기

```
┌─────────────────────────────────────────────────────────────────┐
│                      State 생애주기                               │
└─────────────────────────────────────────────────────────────────┘

1단계: 초기화 (API에서)
┌────────────────────────────────────────┐
│ TutorState = {                         │
│   messages: [],                        │
│   level: 3,                            │
│   session_id: "abc-123",               │
│   input_text: "Hello world",           │
│   task_type: "analyze"                 │
│ }                                      │
└────────────────────────────────────────┘
                    │
                    ▼
2단계: Supervisor 통과 (변화 없음)
┌────────────────────────────────────────┐
│ State 그대로 전달                       │
│ (Supervisor는 라우팅만 담당)            │
└────────────────────────────────────────┘
                    │
                    ▼
3단계: 병렬 에이전트 실행 (State 분할)
┌─────────────┬─────────────┬─────────────┐
│  Reading    │  Grammar    │  Vocabulary │
│  State 복사 │  State 복사 │  State 복사 │
└──────┬──────┴──────┬──────┴──────┬──────┘
       │             │             │
       ▼             ▼             ▼
┌─────────────┬─────────────┬─────────────┐
│reading_result│grammar_result│vocabulary_result│
│   추가됨    │   추가됨    │   추가됨    │
└─────────────┴─────────────┴─────────────┘
                    │
                    ▼
4단계: Aggregator에서 병합
┌────────────────────────────────────────┐
│ 최종 State = {                         │
│   ...기존 필드...,                      │
│   reading_result: {...},               │
│   grammar_result: {...},               │
│   vocabulary_result: {...}             │
│ }                                      │
└────────────────────────────────────────┘
```

### 2.3 State 병합 (Merge) 규칙

**LangGraph의 핵심 기능!**

```python
# 각 에이전트가 반환하는 것
reading_node → {"reading_result": ReadingResult(...)}
grammar_node → {"grammar_result": GrammarResult(...)}
vocabulary_node → {"vocabulary_result": VocabularyResult(...)}

# LangGraph가 자동으로 병합
final_state = {
    **initial_state,
    "reading_result": ReadingResult(...),
    "grammar_result": GrammarResult(...),
    "vocabulary_result": VocabularyResult(...)
}
```

**병합 규칙:**
1. **새 필드** → 추가
2. **기존 필드** → 덮어쓰기
3. **list/dict** → LangGraph Reducer로 병합 가능

---

## 3. 그래프 구조 상세

### 3.1 graph.py 분석

```python
# graph.py
from langgraph.constants import END, START
from langgraph.graph import StateGraph
from langgraph.types import Send

def create_graph():
    # 1. StateGraph 생성 (State 타입 지정)
    workflow = StateGraph(TutorState)

    # 2. 노드 추가 (각각의 에이전트 함수)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("reading", reading_node)
    workflow.add_node("grammar", grammar_node)
    workflow.add_node("vocabulary", vocabulary_node)
    workflow.add_node("image_processor", image_processor_node)
    workflow.add_node("aggregator", aggregator_node)

    # 3. 시작점 설정
    workflow.add_edge(START, "supervisor")

    # 4. 조건부 엣지 (라우팅)
    workflow.add_conditional_edges("supervisor", route_by_task)

    # 5. 모든 튜터 → aggregator
    workflow.add_edge("reading", "aggregator")
    workflow.add_edge("grammar", "aggregator")
    workflow.add_edge("vocabulary", "aggregator")
    workflow.add_edge("image_processor", "aggregator")

    # 6. 종료점
    workflow.add_edge("aggregator", END)

    # 7. 컴파일 (실행 가능한 그래프로)
    return workflow.compile()

# 전역 인스턴스
graph = create_graph()
```

### 3.2 그래프 시각화

```
                    ┌─────────┐
                    │  START  │
                    └────┬────┘
                         │
                         ▼
                  ┌─────────────┐
                  │  supervisor │
                  └──────┬──────┘
                         │
            ┌────────────┼────────────┐
            │ route_by_task()         │
            ▼            ▼            ▼
     ┌──────────┐ ┌──────────┐ ┌──────────┐
     │ reading  │ │ grammar  │ │vocabulary│
     └────┬─────┘ └────┬─────┘ └────┬─────┘
          │            │            │
          └────────────┼────────────┘
                       ▼
                ┌───────────┐
                │ aggregator│
                └─────┬─────┘
                      │
                      ▼
                 ┌────────┐
                 │  END   │
                 └────────┘
```

---

## 4. 병렬 실행 (Send API)

### 4.1 Send API란?

**Send** = 여러 노드에 **동시에** State를 전달하는 기능

```python
from langgraph.types import Send

def route_by_task(state: TutorState) -> list[Send]:
    """Supervisor 다음에 실행할 노드 결정"""

    task_type = state.get("task_type", "analyze")

    if task_type == "analyze":
        # 3개 노드에 State를 동시에 전달!
        return [
            Send("reading", state),     # State 복사 → reading
            Send("grammar", state),     # State 복사 → grammar
            Send("vocabulary", state),  # State 복사 → vocabulary
        ]

    elif task_type == "image_process":
        return [Send("image_processor", state)]

    elif task_type == "chat":
        return [Send("chat", state)]

    return []
```

### 4.2 병렬 vs 순차 실행

```
순차 실행 (기존 방식):
┌────────┐   ┌────────┐   ┌────────┐
│Reading │──▶│Grammar │──▶│Vocab   │
│  3초   │   │  3초   │   │  3초   │
└────────┘   └────────┘   └────────┘
총 시간: 3 + 3 + 3 = 9초

병렬 실행 (Send API):
┌────────┐
│Reading │  3초
├────────┤
│Grammar │  3초   ──▶ 동시에 실행!
├────────┤
│Vocab   │  3초
└────────┘
총 시간: max(3, 3, 3) = 3초
```

**3배 빠릅니다!**

### 4.3 병렬 실행 조건

**언제 병렬 실행 가능?**
1. 노드 간 의존성이 없음
2. 각 노드가 State의 다른 필드를 수정
3. 순서가 중요하지 않음

**이 프로젝트에서:**
- Reading, Grammar, Vocabulary는 서로 독립적
- 각각 reading_result, grammar_result, vocabulary_result를 수정
- 순서 상관없음
- → **병렬 실행 가능!**

---

## 5. Message 전달

### 5.1 messages 필드의 역할

```python
class TutorState(TypedDict):
    messages: list[dict]  # 대화 내역
    # ...
```

**messages 구조:**
```python
messages = [
    {"role": "user", "content": "What is the past tense of go?"},
    {"role": "assistant", "content": "The past tense of 'go' is 'went'."},
    {"role": "user", "content": "Give me an example."},
    {"role": "assistant", "content": "I went to school yesterday."},
]
```

### 5.2 Message 흐름

```
1. 사용자 요청
   │
   ▼
2. 세션에서 이전 messages 로드
   │
   ▼
3. State에 messages 포함
   │
   ▼
4. LLM이 messages를 컨텍스트로 사용
   │
   ▼
5. 응답 후 messages에 추가
   │
   ▼
6. 세션에 저장
```

### 5.3 Session Manager

```python
# services/session.py
class SessionManager:
    def __init__(self, ttl_hours: int = 24):
        self._sessions: dict[str, dict] = {}
        self._ttl = timedelta(hours=ttl_hours)

    def create(self) -> str:
        """새 세션 생성"""
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = {
            "id": session_id,
            "messages": [],
            "created_at": datetime.now(),
            "expires_at": datetime.now() + self._ttl,
        }
        return session_id

    def get(self, session_id: str) -> dict | None:
        """세션 조회"""
        session = self._sessions.get(session_id)
        if session and datetime.now() <= session["expires_at"]:
            return session
        return None

    def add_message(self, session_id: str, role: str, content: str):
        """메시지 추가"""
        session = self.get(session_id)
        if session:
            session["messages"].append({"role": role, "content": content})
```

---

## 6. 에이전트 구현 패턴

### 6.1 공통 패턴

모든 에이전트가 따르는 구조:

```python
async def xxx_node(state: TutorState) -> dict:
    """
    에이전트 함수 템플릿

    Args:
        state: 현재 State

    Returns:
        dict: State에 병합될 업데이트
    """
    try:
        # 1. State에서 필요한 값 추출
        input_text = state.get("input_text", "")
        level = state.get("level", 3)

        # 2. LLM 클라이언트 가져오기
        llm = get_llm("모델명")

        # 3. 프롬프트 준비
        prompt = render_prompt("프롬프트파일.md", text=input_text, level=level)

        # 4. LLM 호출 (구조화된 출력)
        structured_llm = llm.with_structured_output(ResultModel)
        result = await structured_llm.ainvoke(prompt)

        # 5. 결과 반환 (State에 병합됨)
        return {"xxx_result": result}

    except Exception as e:
        # 6. 에러 처리
        logger.error(f"Error: {e}")
        return {"xxx_result": None}
```

### 6.2 Reading 에이전트 상세

```python
# agents/reading.py
async def reading_node(state: TutorState) -> dict:
    """읽기 이해 분석"""
    try:
        # 1. Claude Sonnet (높은 품질)
        llm = get_llm("claude-sonnet-4-5")

        # 2. 레벨별 지침
        level = state.get("level", 3)
        level_instructions = get_level_instructions(level)
        # 레벨 1-2: 쉬운 설명
        # 레벨 3: 보통
        # 레벨 4-5: 학술적 용어

        # 3. 프롬프트 렌더링
        prompt = render_prompt(
            "reading.md",
            text=state.get("input_text", ""),
            level=level,
            level_instructions=level_instructions,
        )

        # 4. 구조화된 출력
        structured_llm = llm.with_structured_output(ReadingResult)
        reading_result = await structured_llm.ainvoke(prompt)

        return {"reading_result": reading_result}

    except Exception as e:
        logger.error(f"Error in reading_node: {e}")
        return {"reading_result": None}
```

### 6.3 Grammar 에이전트 (GPT-4o)

```python
# agents/grammar.py
async def grammar_node(state: TutorState) -> dict:
    """문법 분석 - GPT-4o 사용 (Structured Output 지원)"""
    try:
        # GPT-4o (Structured Output 최적)
        llm = get_llm("gpt-4o")

        level = state.get("level", 3)
        level_instructions = get_level_instructions(level)

        prompt = render_prompt(
            "grammar.md",
            text=state.get("input_text", ""),
            level=level,
            level_instructions=level_instructions,
        )

        structured_llm = llm.with_structured_output(GrammarResult)
        grammar_result = await structured_llm.ainvoke(prompt)

        return {"grammar_result": grammar_result}

    except Exception as e:
        logger.error(f"Error in grammar_node: {e}")
        return {"grammar_result": None}
```

### 6.4 Aggregator 에이전트

```python
# agents/aggregator.py
def aggregator_node(state: TutorState) -> dict:
    """결과 통합"""
    try:
        session_id = state["session_id"]

        # State에서 각 결과 추출
        reading_result = state.get("reading_result")
        grammar_result = state.get("grammar_result")
        vocabulary_result = state.get("vocabulary_result")

        # 최종 응답 생성
        analyze_response = AnalyzeResponse(
            session_id=session_id,
            reading=reading_result,
            grammar=grammar_result,
            vocabulary=vocabulary_result,
        )

        return {"analyze_response": analyze_response}

    except Exception as e:
        logger.error(f"Error in aggregator_node: {e}")
        return {"analyze_response": AnalyzeResponse(session_id=state.get("session_id", ""))}
```

---

## 7. LLM 모델 배정 전략

### 7.1 모델 선택 기준

| 에이전트 | 모델 | 이유 |
|----------|------|------|
| Supervisor | GPT-4o-mini | 가벼운 라우팅, 저렴함 |
| Reading | Claude Sonnet | 고품질 텍스트 분석 |
| Grammar | GPT-4o | Structured Output 지원 |
| Vocabulary | Claude Haiku | 빠르고 저렴, 단순 작업 |

### 7.2 비용 최적화

```
모델별 상대적 비용:
┌─────────────────┬────────┐
│ GPT-4o-mini     │   $    │
│ Claude Haiku    │   $$   │
│ Claude Sonnet   │   $$$  │
│ GPT-4o          │   $$$$ │
└─────────────────┴────────┘

이 프로젝트의 전략:
- 복잡한 분석 → 고가 모델 (Sonnet, GPT-4o)
- 단순 작업 → 저가 모델 (Haiku, GPT-4o-mini)
```

---

## 8. 요약

### State 전달 핵심
1. State는 모든 에이전트가 공유하는 데이터
2. 각 에이전트는 State의 일부를 수정해서 반환
3. LangGraph가 자동으로 병합

### 병렬 실행 핵심
1. `Send()` API로 여러 노드에 동시 전달
2. 독립적인 작업만 병렬 실행 가능
3. Aggregator에서 결과 통합

### 에이전트 패턴
1. State에서 입력 추출
2. LLM 호출
3. 구조화된 출력으로 결과 반환
4. 에러 시 None 반환 (부분 결과 허용)
