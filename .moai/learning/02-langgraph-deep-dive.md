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
    task_type: str            # 작업 유형: "analyze" | "image_process" | "chat"

    # ===== 선택 필드 (에이전트가 채움) =====
    reading_result: NotRequired[ReadingResult | None]
    grammar_result: NotRequired[GrammarResult | None]
    vocabulary_result: NotRequired[VocabularyResult | None]
    extracted_text: NotRequired[str | None]
    supervisor_analysis: NotRequired[SupervisorAnalysis | None]  # NEW: Supervisor LLM 분석 결과
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
2단계: Supervisor 분석 (gpt-4o-mini 호출)
┌────────────────────────────────────────┐
│ Supervisor가 LLM 호출:                  │
│ - 입력 텍스트 사전 분석                  │
│ - 문장 분류 (난이도, 초점)               │
│ - supervisor_analysis 생성              │
│ State에 supervisor_analysis 추가됨      │
└────────────────────────────────────────┘
                    │
                    ▼
3단계: 병렬 에이전트 실행 (State 분할)
┌─────────────┬─────────────┬─────────────┐
│  Reading    │  Grammar    │  Vocabulary │
│  State 복사 │  State 복사 │  State 복사 │
│ (분석 포함) │ (분석 포함) │ (분석 포함) │
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
│   supervisor_analysis: {...},          │
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
supervisor_node → {"supervisor_analysis": SupervisorAnalysis(...)}
reading_node → {"reading_result": ReadingResult(...)}
grammar_node → {"grammar_result": GrammarResult(...)}
vocabulary_node → {"vocabulary_result": VocabularyResult(...)}

# LangGraph가 자동으로 병합
final_state = {
    **initial_state,
    "supervisor_analysis": SupervisorAnalysis(...),
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
                  │(LLM 분석)    │
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

### 6.1 공통 패턴 (변경됨!)

모든 에이전트가 따르는 **새로운** 구조:

```python
async def xxx_node(state: TutorState) -> dict:
    """
    에이전트 함수 템플릿 (마크다운 기반 출력)

    Args:
        state: 현재 State

    Returns:
        dict: State에 병합될 업데이트
    """
    try:
        # 1. State에서 필요한 값 추출
        input_text = state.get("input_text", "")
        level = state.get("level", 3)

        # 2. Supervisor 분석 가져오기 (에이전트 방향성 제공)
        supervisor_analysis = state.get("supervisor_analysis")
        supervisor_context = ""
        if supervisor_analysis:
            supervisor_context = f"""
## Supervisor 분석
- 난이도: {supervisor_analysis.overall_difficulty}/5
- 초점: {', '.join(supervisor_analysis.focus_summary)}
- 문장 분류: {len(supervisor_analysis.sentences)}개 문장
"""

        # 3. LLM 클라이언트 가져오기 (새로운 팩토리 패턴)
        from tutor.models.llm import get_llm
        llm = get_llm("모델명")

        # 4. 프롬프트 준비
        prompt = render_prompt(
            "프롬프트파일.md",
            text=input_text,
            level=level,
            supervisor_context=supervisor_context
        )

        # 5. LLM 호출 (새로운 패턴: ainvoke 직접 사용)
        response = await llm.ainvoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)

        # 6. 마크다운 정규화 (새로운 단계!)
        from tutor.utils.markdown_normalizer import normalize_reading_output
        content = normalize_reading_output(content)

        # 7. 결과 반환 (마크다운 콘텐츠)
        return {"xxx_result": ResultModel(content=content)}

    except Exception as e:
        # 8. 에러 처리
        logger.error(f"Error: {e}")
        return {"xxx_result": None}
```

**주요 변경사항:**
- `with_structured_output()` 제거
- `ainvoke()`로 직접 응답 받음
- `response.content` 추출
- `markdown_normalizer` 적용

### 6.2 Reading 에이전트 상세 (완전 업데이트)

```python
# agents/reading.py
from tutor.models.llm import get_llm
from tutor.utils.markdown_normalizer import normalize_reading_output

async def reading_node(state: TutorState) -> dict:
    """읽기 이해 분석 - gpt-4o-mini (마크다운 기반)"""
    try:
        # 1. gpt-4o-mini (높은 품질, 마크다운 생성)
        llm = get_llm("claude-sonnet-4-5", max_tokens=2000, timeout=30)

        # 2. 레벨별 지침
        level = state.get("level", 3)
        level_instructions = get_level_instructions(level)

        # 3. Supervisor 분석 컨텍스트 추가
        supervisor_analysis = state.get("supervisor_analysis")
        supervisor_context = ""
        if supervisor_analysis:
            focus_tags = ", ".join(supervisor_analysis.focus_summary)
            supervisor_context = f"""
## 문맥 정보
- 전체 난이도: {supervisor_analysis.overall_difficulty}/5
- 분석 초점: {focus_tags}
- 대상 문장: {len(supervisor_analysis.sentences)}개
"""

        # 4. 프롬프트 렌더링
        prompt = render_prompt(
            "reading.md",
            text=state.get("input_text", ""),
            level=level,
            level_instructions=level_instructions,
            supervisor_context=supervisor_context,
        )

        # 5. LLM 호출 (구조화되지 않은 응답)
        response = await llm.ainvoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)

        # 6. 마크다운 정규화
        content = normalize_reading_output(content)

        # 7. 결과 반환 (마크다운 콘텐츠)
        return {"reading_result": ReadingResult(content=content)}

    except Exception as e:
        logger.error(f"Error in reading_node: {e}")
        return {"reading_result": None}
```

**ReadingResult 스키마 (변경됨!):**
```python
class ReadingResult(BaseModel):
    content: str  # 한국어 마크다운 형식의 읽기 분석
    # 예: "## 주요 내용\n텍스트 요약\n## 감정 톤\n긍정적"
```

### 6.3 Grammar 에이전트 (gpt-4o-mini)

```python
# agents/grammar.py
from tutor.models.llm import get_llm
from tutor.utils.markdown_normalizer import normalize_grammar_output

async def grammar_node(state: TutorState) -> dict:
    """문법 분석 - gpt-4o-mini (마크다운 기반)"""
    try:
        # gpt-4o-mini (구조화된 출력은 더 이상 사용 안 함)
        llm = get_llm("gpt-4o-mini", max_tokens=2000, timeout=30)

        level = state.get("level", 3)
        level_instructions = get_level_instructions(level)

        # Supervisor 분석 컨텍스트
        supervisor_analysis = state.get("supervisor_analysis")
        supervisor_context = ""
        if supervisor_analysis:
            focus_tags = ", ".join(supervisor_analysis.focus_summary)
            supervisor_context = f"분석 초점: {focus_tags}, 난이도: {supervisor_analysis.overall_difficulty}/5"

        prompt = render_prompt(
            "grammar.md",
            text=state.get("input_text", ""),
            level=level,
            level_instructions=level_instructions,
            supervisor_context=supervisor_context,
        )

        # LLM 호출 (구조화되지 않음)
        response = await llm.ainvoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)

        # 마크다운 정규화
        content = normalize_grammar_output(content)

        return {"grammar_result": GrammarResult(content=content)}

    except Exception as e:
        logger.error(f"Error in grammar_node: {e}")
        return {"grammar_result": None}
```

**GrammarResult 스키마 (변경됨!):**
```python
class GrammarResult(BaseModel):
    content: str  # 한국어 마크다운 형식의 문법 분석
    # 예: "## 시제\n과거형 사용\n## 구조\n복합문"
```

### 6.4 Vocabulary 에이전트 (업그레이드!)

```python
# agents/vocabulary.py
from tutor.models.llm import get_llm
from tutor.utils.markdown_normalizer import normalize_vocabulary_output

async def vocabulary_node(state: TutorState) -> dict:
    """어휘 분석 - gpt-4o-mini (6단계 어원)"""
    try:
        # gpt-4o-mini (통일된 모델로 선택)
        llm = get_llm("claude-sonnet-4-5", max_tokens=3000, timeout=30)

        level = state.get("level", 3)
        level_instructions = get_level_instructions(level)

        # Supervisor 분석 컨텍스트
        supervisor_analysis = state.get("supervisor_analysis")
        supervisor_context = ""
        if supervisor_analysis:
            focus_tags = ", ".join(supervisor_analysis.focus_summary)
            supervisor_context = f"초점: {focus_tags}, 난이도: {supervisor_analysis.overall_difficulty}/5"

        prompt = render_prompt(
            "vocabulary.md",
            text=state.get("input_text", ""),
            level=level,
            level_instructions=level_instructions,
            supervisor_context=supervisor_context,
        )

        # LLM 호출
        response = await llm.ainvoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)

        # 마크다운 정규화
        content = normalize_vocabulary_output(content)

        # 마크다운을 파싱해서 단어별로 분할
        words = parse_vocabulary_markdown(content)

        return {"vocabulary_result": VocabularyResult(words=words)}

    except Exception as e:
        logger.error(f"Error in vocabulary_node: {e}")
        return {"vocabulary_result": None}
```

**VocabularyResult 스키마 (변경됨!):**
```python
class VocabularyWordEntry(BaseModel):
    word: str
    content: str  # 한국어 마크다운 (6단계 어원 포함)
    # 예: "## 뜻\n동사: 가다\n## 예문\nI go to school."

class VocabularyResult(BaseModel):
    words: list[VocabularyWordEntry]
```

### 6.5 Supervisor 에이전트 (새로운 패턴!)

```python
# agents/supervisor.py
from tutor.models.llm import get_llm

async def supervisor_node(state: TutorState) -> dict:
    """
    Supervisor는 이제 단순 라우터가 아니라 LLM 기반 분석 수행
    """
    try:
        input_text = state.get("input_text", "")
        if not input_text:
            return {"supervisor_analysis": None}

        # gpt-4o-mini (효율적인 사전 분석)
        llm = get_llm("claude-haiku-4-5", max_tokens=1024, timeout=30)

        prompt = render_prompt(
            "supervisor.md",
            text=input_text,
        )

        # LLM 호출해서 분석 결과 얻기
        response = await llm.ainvoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)

        # 응답을 SupervisorAnalysis로 파싱
        # Period 기반 폴백: LLM 실패 시 마침표로 문장 분할
        analysis = parse_supervisor_analysis(content, input_text)

        return {"supervisor_analysis": analysis}

    except Exception as e:
        logger.warning(f"Supervisor analysis failed, using fallback: {e}")
        # 폴백: 마침표 기반 분할
        sentences = parse_sentences_fallback(state.get("input_text", ""))
        analysis = SupervisorAnalysis(
            sentences=sentences,
            overall_difficulty=3,
            focus_summary=["general"]
        )
        return {"supervisor_analysis": analysis}
```

**SupervisorAnalysis 스키마 (새로운!):**
```python
class SentenceEntry(BaseModel):
    text: str
    difficulty: int  # 1-5
    focus: list[str]  # ["grammar", "vocabulary", "reading"]

class SupervisorAnalysis(BaseModel):
    sentences: list[SentenceEntry]
    overall_difficulty: int  # 1-5
    focus_summary: list[str]  # ["grammar", "vocabulary", etc.]
```

### 6.6 Aggregator 에이전트

```python
# agents/aggregator.py
def aggregator_node(state: TutorState) -> dict:
    """결과 통합"""
    try:
        session_id = state["session_id"]

        # State에서 각 결과 추출
        supervisor_analysis = state.get("supervisor_analysis")
        reading_result = state.get("reading_result")
        grammar_result = state.get("grammar_result")
        vocabulary_result = state.get("vocabulary_result")

        # 최종 응답 생성
        analyze_response = AnalyzeResponse(
            session_id=session_id,
            supervisor_analysis=supervisor_analysis,
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

## 7. LLM 팩토리 패턴 (새로운 섹션!)

### 7.1 LLM 팩토리란?

**모델 생성을 중앙에서 관리하는 패턴**입니다. 모든 코드에서 `from tutor.models.llm import get_llm`을 쓰면 일관된 설정으로 모델을 받을 수 있습니다.

### 7.2 사용 방법

```python
# tutor/models/llm.py (새로운 파일!)
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

def get_llm(model_name: str, max_tokens: int = 2048, timeout: int = 30):
    """
    LLM 팩토리 함수

    Args:
        model_name: 모델 이름 (예: "claude-haiku-4-5", "gpt-4o")
        max_tokens: 최대 토큰 수
        timeout: 타임아웃 (초)

    Returns:
        LLM 인스턴스
    """
    if "claude" in model_name:
        return ChatAnthropic(
            model=model_name,
            max_tokens=max_tokens,
            timeout=timeout,
        )
    elif "gpt" in model_name:
        return ChatOpenAI(
            model=model_name,
            max_tokens=max_tokens,
            timeout=timeout,
        )
    else:
        raise ValueError(f"Unknown model: {model_name}")
```

**각 에이전트에서:**
```python
# 방법 1: 기본값
llm = get_llm("claude-haiku-4-5")

# 방법 2: 커스텀 파라미터
llm = get_llm("claude-sonnet-4-5", max_tokens=3000, timeout=60)
```

---

## 8. 마크다운 정규화 (새로운 섹션!)

### 8.1 정규화가 뭐죠?

**LLM이 생성한 마크다운을 표준화하는 과정**입니다. 예를 들어:
- 제목 레벨 정규화 (#### → ##)
- 잘못된 굵은 텍스트 수정 (**text** → **text**)
- 빈 줄 정리

### 8.2 사용 방법

```python
# tutor/utils/markdown_normalizer.py (새로운 파일!)
import re

def normalize_reading_output(content: str) -> str:
    """Reading 에이전트 출력 정규화"""
    try:
        # 제목 레벨 조정: #### → ##
        content = re.sub(r'^#{4,}', '##', content, flags=re.MULTILINE)

        # 잘못된 굵은 텍스트 수정
        content = re.sub(r'\*\*\*(.+?)\*\*\*', r'**\1**', content)

        # 연속된 빈 줄 정리
        content = re.sub(r'\n\n\n+', '\n\n', content)

        return content
    except Exception as e:
        logger.warning(f"Normalization failed, returning original: {e}")
        return content

def normalize_grammar_output(content: str) -> str:
    """Grammar 에이전트 출력 정규화"""
    # 동일한 정규화
    return normalize_reading_output(content)

def normalize_vocabulary_output(content: str) -> str:
    """Vocabulary 에이전트 출력 정규화"""
    # Vocabulary는 추가 정규화 필요 (단어 분할 등)
    return normalize_reading_output(content)
```

**각 에이전트에서:**
```python
response = await llm.ainvoke(prompt)
content = response.content if hasattr(response, "content") else str(response)

# 정규화 적용
from tutor.utils.markdown_normalizer import normalize_reading_output
content = normalize_reading_output(content)
```

---

## 9. LLM 모델 배정 전략

### 9.1 모델 선택 기준 (업데이트됨!)

| 에이전트 | 모델 | 이유 | 변화 |
|----------|------|------|------|
| Supervisor | gpt-4o-mini | LLM 기반 사전 분석 | v1.1.1 통일 |
| Reading | gpt-4o-mini | 고품질 텍스트 분석 | v1.1.1 통일 |
| Grammar | gpt-4o-mini | 문법 구조 분석 | v1.1.1 통일 |
| Vocabulary | gpt-4o-mini | 어원 네트워크 설명 | v1.1.1 통일 |

### 9.2 비용 최적화 (업데이트됨!)

```
모델별 상대적 비용 (v1.1.1 이후):
┌─────────────────┬────────┐
│ gpt-4o-mini     │   $    │  (모든 에이전트)
└─────────────────┴────────┘

이 프로젝트의 최적화 전략:
- 모든 에이전트: gpt-4o-mini (비용 95% 절감)
- 이전: Claude Sonnet × 2 + GPT-4o × 1 + GPT-4o-mini × 1 ≈ $$$$
- 현재: gpt-4o-mini × 4 ≈ $

총 비용 절감: ~$152/월 → ~$7/월 (1,000 requests/월 기준)
```

---

## 10. 스키마 변경 요약

### 10.1 구조화된 출력 → 마크다운 기반으로 변경

**옛날 방식:**
```python
class ReadingResult(BaseModel):
    summary: str
    main_topic: str
    emotional_tone: str
```

**새로운 방식:**
```python
class ReadingResult(BaseModel):
    content: str  # 마크다운 형식의 전체 분석
```

**장점:**
- LLM이 자유롭게 표현 (JSON 제약 없음)
- 한국어 형식 최적화 가능
- 사용자 친화적 출력
- 정규화로 품질 관리

### 10.2 새로운 SupervisorAnalysis 스키마

```python
class SentenceEntry(BaseModel):
    text: str
    difficulty: int  # 1-5
    focus: list[str]

class SupervisorAnalysis(BaseModel):
    sentences: list[SentenceEntry]
    overall_difficulty: int  # 1-5
    focus_summary: list[str]
```

---

## 11. 요약

### State 전달 핵심
1. State는 모든 에이전트가 공유하는 데이터
2. **Supervisor는 이제 LLM을 호출해서 supervisor_analysis 추가** (변경!)
3. 각 에이전트는 State의 일부를 수정해서 반환
4. LangGraph가 자동으로 병합

### 병렬 실행 핵심
1. `Send()` API로 여러 노드에 동시 전달
2. 독립적인 작업만 병렬 실행 가능
3. Aggregator에서 결과 통합

### 에이전트 패턴 (업데이트!)
1. State에서 입력 + supervisor_analysis 추출
2. `get_llm()` 팩토리로 모델 생성
3. `ainvoke()`로 직접 응답 받음 (with_structured_output 제거)
4. `markdown_normalizer`로 정규화
5. 마크다운 콘텐츠로 결과 반환
6. 에러 시 None 반환 (부분 결과 허용)

### 주요 변경사항 체크리스트
- [x] TutorState에 supervisor_analysis 추가
- [x] Supervisor를 LLM 기반으로 업데이트
- [x] 모든 에이전트에서 supervisor_analysis 활용
- [x] with_structured_output 제거, ainvoke 사용
- [x] 마크다운 정규화 적용
- [x] LLM 팩토리 패턴 도입
- [x] Vocabulary 에이전트를 Sonnet으로 업그레이드
