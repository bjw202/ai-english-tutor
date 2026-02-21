# SPEC-BACKEND-001 구현 계획

> 참조: SPEC-BACKEND-001 (spec.md)
> 개발 방법론: TDD (RED-GREEN-REFACTOR) - 모든 코드 신규 작성

---

## 1. 작업 분해 (Task Decomposition)

### Task 01: 프로젝트 스캐폴딩

**목표:** `backend/` 디렉토리 구조, `pyproject.toml`, `src/tutor/` 패키지 초기화

**생성 파일:**
- `backend/pyproject.toml`
- `backend/.env.example`
- `backend/src/tutor/__init__.py`
- `backend/tests/conftest.py`
- `backend/tests/fixtures/__init__.py`

**주요 내용 (pyproject.toml):**
```toml
[project]
name = "ai-english-tutor"
version = "0.1.0"
requires-python = ">=3.13"

[project.dependencies]
fastapi = ">=0.115.0"
uvicorn = {extras = ["standard"], version = ">=0.34.0"}
pydantic = ">=2.10.0"
pydantic-settings = ">=2.7.0"
langgraph = ">=0.3.0"
langchain-openai = ">=0.3.0"
langchain-anthropic = ">=0.3.0"
python-multipart = ">=0.0.20"
pillow = ">=11.0.0"

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.25.0",
    "pytest-cov>=6.0.0",
    "httpx>=0.28.0",
    "ruff>=0.9.0",
]
```

**의존성:** 없음 (시작점)

---

### Task 02: 설정 시스템 (`config.py`)

**목표:** Pydantic `BaseSettings` 기반 설정 시스템 구현

**생성 파일:**
- `backend/src/tutor/config.py`
- `backend/.env.example`

**핵심 설정 필드:**
```python
class Settings(BaseSettings):
    # LLM API 키
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str

    # 모델 설정
    SUPERVISOR_MODEL: str = "gpt-4o-mini"
    READING_MODEL: str = "claude-sonnet-4-5"
    GRAMMAR_MODEL: str = "gpt-4o"
    VOCABULARY_MODEL: str = "claude-haiku-4-5"

    # 서버 설정
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # 세션 설정
    SESSION_TTL_HOURS: int = 24

    model_config = SettingsConfig(env_file=".env", env_file_encoding="utf-8")
```

**의존성:** Task 01

---

### Task 03: Pydantic 스키마 (`schemas.py`)

**목표:** 모든 요청/응답 스키마 정의

**생성 파일:**
- `backend/src/tutor/schemas.py`

**TDD 접근:** 스키마 유효성 검사 테스트 먼저 작성

```
tests/unit/test_schemas.py:
  - test_analyze_request_valid()
  - test_analyze_request_text_too_short()
  - test_analyze_request_text_too_long()
  - test_analyze_request_invalid_level()
  - test_reading_result_structure()
  - test_grammar_result_structure()
  - test_vocabulary_result_word_list()
```

**의존성:** Task 01

---

### Task 04: LLM 클라이언트 (`models/llm.py`)

**목표:** OpenAI 및 Anthropic 클라이언트 초기화 및 팩토리 함수

**생성 파일:**
- `backend/src/tutor/models/__init__.py`
- `backend/src/tutor/models/llm.py`

**핵심 구조:**
```python
def get_llm(model_name: str) -> BaseChatModel:
    """모델명에 따라 적절한 LLM 클라이언트 반환"""
    if model_name.startswith("gpt-"):
        return ChatOpenAI(model=model_name, ...)
    elif model_name.startswith("claude-"):
        return ChatAnthropic(model=model_name, ...)
    raise ValueError(f"Unknown model: {model_name}")
```

**의존성:** Task 02 (설정 필요)

---

### Task 05: 프롬프트 시스템 (`prompts.py` + 템플릿)

**목표:** `.md` 파일 기반 프롬프트 로더 및 변수 주입 시스템

**생성 파일:**
- `backend/src/tutor/prompts.py`
- `backend/src/tutor/prompts/supervisor.md`
- `backend/src/tutor/prompts/reading.md`
- `backend/src/tutor/prompts/grammar.md`
- `backend/src/tutor/prompts/vocabulary.md`
- `backend/src/tutor/prompts/level_instructions.yaml`

**level_instructions.yaml 구조:**
```yaml
levels:
  1:
    description: "매우 기초 - 초등 고학년 수준"
    instructions: "매우 간단한 단어와 짧은 문장으로 설명하세요..."
  2:
    description: "기초 - 중학교 1학년 수준"
    instructions: "기본 영어 용어를 사용하되 한국어로 보충 설명하세요..."
  3:
    description: "중급 - 중학교 2-3학년 수준"
    instructions: "일반적인 문법 용어를 사용하고 예시를 충분히 제공하세요..."
  4:
    description: "상급 - 고등학교 수준"
    instructions: "고급 문법 개념과 언어학적 분석을 포함하세요..."
  5:
    description: "고급 - 수능/토익 대비 수준"
    instructions: "학술적 영어 분석과 시험 전략을 포함하세요..."
```

**의존성:** Task 01

---

### Task 06: 에이전트 상태 (`state.py`)

**목표:** `TutorState` TypedDict 정의

**생성 파일:**
- `backend/src/tutor/state.py`

**의존성:** Task 03 (스키마 참조)

---

### Task 07: 개별 에이전트 구현

**목표:** 5개 에이전트 구현 (supervisor, reading, grammar, vocabulary, image_processor) + aggregator

**생성 파일:**
- `backend/src/tutor/agents/__init__.py`
- `backend/src/tutor/agents/supervisor.py`
- `backend/src/tutor/agents/reading.py`
- `backend/src/tutor/agents/grammar.py`
- `backend/src/tutor/agents/vocabulary.py`
- `backend/src/tutor/agents/image_processor.py`
- `backend/src/tutor/agents/aggregator.py`

**TDD 접근 (Mock LLM 사용):**
```
tests/unit/test_agents.py:
  - test_supervisor_routes_to_analyze()
  - test_supervisor_routes_to_image_process()
  - test_supervisor_routes_to_chat()
  - test_reading_agent_returns_reading_result()
  - test_grammar_agent_returns_grammar_result()
  - test_vocabulary_agent_returns_vocabulary_result()
  - test_image_processor_extracts_text()
  - test_aggregator_combines_results()
```

**의존성:** Task 04, Task 05, Task 06

---

### Task 08: LangGraph 그래프 (`graph.py`)

**목표:** Send() API를 사용한 병렬 에이전트 디스패치 그래프 구현

**생성 파일:**
- `backend/src/tutor/graph.py`

**핵심 구조:**
```python
def create_graph() -> CompiledGraph:
    workflow = StateGraph(TutorState)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("reading", reading_node)
    workflow.add_node("grammar", grammar_node)
    workflow.add_node("vocabulary", vocabulary_node)
    workflow.add_node("image_processor", image_processor_node)
    workflow.add_node("aggregator", aggregator_node)

    # 조건부 엣지 (Send() API로 병렬 디스패치)
    workflow.add_conditional_edges("supervisor", route_task)
    # ...
    return workflow.compile()
```

**의존성:** Task 07

---

### Task 09: 서비스 계층

**목표:** 세션 관리, SSE 스트리밍, 이미지 처리 서비스 구현

**생성 파일:**
- `backend/src/tutor/services/__init__.py`
- `backend/src/tutor/services/session.py`
- `backend/src/tutor/services/streaming.py`
- `backend/src/tutor/services/image.py`

**TDD 접근:**
```
tests/unit/test_services.py:
  - test_session_create_and_retrieve()
  - test_session_ttl_expiry()
  - test_session_not_found()
  - test_sse_format_reading_chunk()
  - test_sse_format_grammar_chunk()
  - test_sse_format_done_event()
  - test_image_validate_size_limit()
  - test_image_validate_mime_type()
  - test_image_base64_encode()
```

**의존성:** Task 03

---

### Task 10: API 엔드포인트 및 FastAPI 앱

**목표:** 라우터, 엔드포인트, FastAPI 앱 설정

**생성 파일:**
- `backend/src/tutor/routers/__init__.py`
- `backend/src/tutor/routers/tutor.py`
- `backend/src/tutor/main.py`

**TDD 접근 (httpx AsyncClient 사용):**
```
tests/integration/test_api.py:
  - test_health_endpoint_returns_200()
  - test_analyze_endpoint_streams_sse()
  - test_analyze_endpoint_validates_input()
  - test_analyze_image_endpoint_streams_sse()
  - test_chat_endpoint_streams_sse()
  - test_chat_endpoint_creates_new_session_if_missing()
```

**의존성:** Task 08, Task 09

---

### Task 11: 통합 테스트 및 실제 LLM 테스트

**목표:** `@pytest.mark.integration` 마커로 실제 API 키 기반 테스트 작성

**생성 파일:**
- `backend/tests/integration/test_real_llm.py`

**테스트 구조:**
```python
@pytest.mark.integration
async def test_reading_agent_with_real_llm():
    """실제 Claude Sonnet으로 읽기 분석 검증"""
    ...

@pytest.mark.integration
async def test_full_graph_e2e():
    """전체 LangGraph 파이프라인 E2E 검증"""
    ...
```

**의존성:** Task 10 (전체 시스템)

---

## 2. 의존성 그래프

```
Task 01 (스캐폴딩)
  ├── Task 02 (설정)
  │   └── Task 04 (LLM 클라이언트)
  │       └── Task 07 (에이전트)
  │           └── Task 08 (그래프)
  │               └── Task 10 (API)
  │                   └── Task 11 (통합 테스트)
  ├── Task 03 (스키마)
  │   ├── Task 06 (상태)
  │   │   └── Task 07 (에이전트)
  │   └── Task 09 (서비스)
  │       └── Task 10 (API)
  └── Task 05 (프롬프트)
      └── Task 07 (에이전트)
```

**병렬 실행 가능:**
- Task 02, Task 03, Task 05는 Task 01 완료 후 동시 진행 가능
- Task 06과 Task 09는 Task 03 완료 후 동시 진행 가능

---

## 3. 기술 명세 (버전 고정)

### 핵심 의존성

| 패키지 | 버전 제약 | 역할 |
|--------|-----------|------|
| `fastapi` | `>=0.115.0,<0.116.0` | 웹 프레임워크 |
| `uvicorn[standard]` | `>=0.34.0,<0.35.0` | ASGI 서버 |
| `pydantic` | `>=2.10.0,<3.0.0` | 데이터 검증 |
| `pydantic-settings` | `>=2.7.0,<3.0.0` | 환경 변수 설정 |
| `langgraph` | `>=0.3.0,<0.4.0` | 에이전트 오케스트레이션 |
| `langchain-openai` | `>=0.3.0,<0.4.0` | OpenAI 통합 |
| `langchain-anthropic` | `>=0.3.0,<0.4.0` | Anthropic 통합 |
| `python-multipart` | `>=0.0.20` | 파일 업로드 |
| `pillow` | `>=11.0.0,<12.0.0` | 이미지 처리 |

### 개발 의존성

| 패키지 | 버전 제약 | 역할 |
|--------|-----------|------|
| `pytest` | `>=8.3.0,<9.0.0` | 테스트 프레임워크 |
| `pytest-asyncio` | `>=0.25.0,<0.26.0` | 비동기 테스트 |
| `pytest-cov` | `>=6.0.0,<7.0.0` | 커버리지 측정 |
| `httpx` | `>=0.28.0,<0.29.0` | API 테스트 클라이언트 |
| `ruff` | `>=0.9.0,<1.0.0` | 린터 및 포매터 |

---

## 4. 리스크 분석

### 리스크 R1: LLM 응답 비결정성

| 항목 | 내용 |
|------|------|
| 위험 | LLM 응답이 매번 다르게 생성되어 테스트 불안정성 발생 |
| 영향도 | 높음 |
| 완화 전략 | 단위 테스트에서 `unittest.mock.AsyncMock` 사용, 실제 LLM 테스트는 `@pytest.mark.integration`으로 분리 |
| 검증 방법 | Mock 응답은 실제 API 응답 구조와 동일한 형식 사용, Pydantic 스키마 검증으로 구조 확인 |

### 리스크 R2: LangGraph 버전 호환성

| 항목 | 내용 |
|------|------|
| 위험 | LangGraph 0.3+의 `Send()` API 변경으로 병렬 디스패치 미작동 |
| 영향도 | 높음 |
| 완화 전략 | Context7 MCP를 통해 최신 LangGraph 문서 확인, 버전을 `>=0.3.0,<0.4.0`으로 고정 |
| 검증 방법 | 그래프 단위 테스트에서 노드 실행 순서 및 병렬성 검증 |

### 리스크 R3: SSE 스트리밍 테스트 복잡성

| 항목 | 내용 |
|------|------|
| 위험 | SSE 응답 스트림을 일반 HTTP 테스트 방식으로 검증하기 어려움 |
| 영향도 | 중간 |
| 완화 전략 | `httpx.AsyncClient`의 스트리밍 모드 활용, SSE 파서 헬퍼 함수를 `conftest.py`에 구현 |
| 검증 방법 | 각 SSE 이벤트 타입별 fixture 데이터 준비, 스트림 수집 후 이벤트별 검증 |

### 리스크 R4: 다중 LLM API 키 관리

| 항목 | 내용 |
|------|------|
| 위험 | CI 환경에서 실제 API 키 없이 테스트 실패 |
| 영향도 | 중간 |
| 완화 전략 | 단위 테스트는 완전히 Mock으로 분리, 통합 테스트는 `SKIP_INTEGRATION_TESTS` 환경 변수로 선택적 실행 |
| 검증 방법 | `pytest.ini`에 integration 마커 등록, CI에서는 단위 테스트만 실행 |

---

## 5. 테스트 전략

### 5.1 테스트 Fixture 구조

**실제 영어 텍스트 Fixture (`tests/fixtures/texts.py`):**

```python
SIMPLE_TEXT = """
The cat sat on the mat. It was a sunny day.
The bird sang a happy song in the garden.
"""  # Level 1-2 대상

MEDIUM_TEXT = """
The Industrial Revolution, which began in Britain during the 18th century,
fundamentally transformed the way people lived and worked...
"""  # Level 3 대상

COMPLEX_TEXT = """
The epistemological implications of quantum mechanics challenge our
conventional understanding of objective reality...
"""  # Level 4-5 대상
```

**Mock LLM 응답 Fixture (`tests/fixtures/llm_responses.py`):**

```python
MOCK_READING_RESPONSE = {
    "summary": "A story about a cat on a sunny day.",
    "main_topic": "Nature and animals",
    "emotional_tone": "cheerful"
}

MOCK_GRAMMAR_RESPONSE = {
    "tenses": ["simple past", "simple present"],
    "voice": "active",
    "sentence_structure": "SVO",
    "analysis": "Simple declarative sentences..."
}

MOCK_VOCABULARY_RESPONSE = {
    "words": [
        {"term": "sat", "meaning": "앉다 (과거형)", "usage": "동사", "synonyms": ["perched"]},
        ...
    ]
}
```

**테스트 이미지 Fixture (`tests/fixtures/images.py`):**

```python
def create_test_image_base64() -> str:
    """영어 텍스트가 포함된 테스트 이미지를 base64로 생성"""
    ...

VALID_IMAGE_BASE64 = create_test_image_base64()
OVERSIZED_IMAGE_BASE64 = create_oversized_test_image()  # >10MB
```

**SSE 이벤트 스트림 Fixture:**

```python
EXPECTED_SSE_EVENTS = [
    "event: reading_chunk\ndata: {...}\n\n",
    "event: grammar_chunk\ndata: {...}\n\n",
    "event: vocabulary_chunk\ndata: {...}\n\n",
    "event: done\ndata: {...}\n\n",
]
```

### 5.2 테스트 카테고리

| 카테고리 | 마커 | 실행 환경 | API 키 필요 |
|----------|------|-----------|-------------|
| 단위 테스트 | (없음) | 항상 | 아니오 (Mock) |
| 통합 테스트 (Mock) | (없음) | 항상 | 아니오 |
| 실제 LLM 테스트 | `@pytest.mark.integration` | 선택적 | 예 |

### 5.3 실제 LLM 통합 테스트

```python
# tests/integration/test_real_llm.py

@pytest.mark.integration
async def test_reading_agent_with_real_api():
    """실제 Claude Sonnet으로 ReadingResult 스키마 검증"""
    agent = ReadingAgent(get_llm(settings.READING_MODEL))
    result = await agent.analyze(SIMPLE_TEXT, level=2)
    assert isinstance(result, ReadingResult)
    assert len(result.summary) > 0

@pytest.mark.integration
async def test_full_graph_e2e_with_real_api():
    """전체 그래프 E2E - SSE 이벤트 수신 검증"""
    graph = create_graph()
    events = []
    async for event in graph.astream(initial_state):
        events.append(event)
    assert any(e.get("type") == "done" for e in events)
```

### 5.4 커버리지 목표

- 전체 코드 커버리지: **85% 이상**
- 스키마 모듈: **95% 이상**
- 서비스 모듈: **90% 이상**
- 에이전트 모듈: **85% 이상** (LLM 호출은 Mock)

```ini
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
markers = [
    "integration: Real LLM API tests (require API keys)",
]
addopts = "--cov=src/tutor --cov-report=term-missing --cov-fail-under=85"
```

---

## 6. 구현 마일스톤

### Primary Goal (핵심 기능)

1. Task 01-03 완료: 프로젝트 구조 + 설정 + 스키마
2. Task 04-06 완료: LLM 클라이언트 + 프롬프트 + 상태
3. Task 07-08 완료: 에이전트 + 그래프 (Mock 테스트 통과)

### Secondary Goal (서비스 완성)

4. Task 09-10 완료: 서비스 계층 + API 엔드포인트
5. 85% 커버리지 달성 및 ruff 린트 통과

### Final Goal (품질 보증)

6. Task 11 완료: 실제 LLM 통합 테스트 작성
7. SSE 스트리밍 E2E 검증
8. 전체 TRUST 5 품질 게이트 통과

### Optional Goal (최적화)

- 에이전트 응답 캐싱 (동일 텍스트+레벨 조합)
- 세션 영구 저장소 연동 (Redis)
- API 요청 제한 (Rate Limiting)
