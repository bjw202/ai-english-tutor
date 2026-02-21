---
id: SPEC-BACKEND-001
version: "1.0.0"
status: implemented
created: "2026-02-20"
updated: "2026-02-21"
author: jw
priority: high
implementation_date: "2026-02-21"
coverage: "96%"
tests_passed: 159
---

## HISTORY

| 날짜 | 버전 | 변경 내용 |
|------|------|-----------|
| 2026-02-20 | 1.0.0 | 최초 작성 |

---

# SPEC-BACKEND-001: AI 영어 튜터 백엔드 시스템

## 1. 환경 (Environment)

### 1.1 프로젝트 개요

AI 기반 개인 맞춤형 영어 학습 튜터 웹 애플리케이션의 백엔드 시스템.
중학생(13-15세)을 대상으로 고등학교 영어 선행학습을 지원한다.

### 1.2 기술 스택

| 구성 요소 | 버전 | 역할 |
|-----------|------|------|
| Python | 3.13+ | 런타임 |
| FastAPI | 0.115+ | 웹 프레임워크 |
| LangGraph | 0.3+ | 에이전트 오케스트레이션 |
| Pydantic | 2.10+ | 데이터 검증 및 직렬화 |
| uv | 0.6+ | 패키지 관리 |
| pytest | 8.3+ | 테스트 프레임워크 |
| ruff | 0.9+ | 린터 및 포매터 |

### 1.3 LLM 모델 배정

| 에이전트 | 모델 | 역할 |
|----------|------|------|
| Supervisor | GPT-4o-mini | 작업 라우팅 및 조율 |
| Reading Tutor | Claude Sonnet | 읽기 이해 분석 |
| Grammar Tutor | GPT-4o | 문법 분석 (구조화된 출력) |
| Vocabulary Tutor | Claude Haiku | 어휘 분석 (비용 최적화) |
| Image Processor | Claude Sonnet Vision | 이미지 텍스트 추출 |

### 1.4 디렉토리 구조

```
backend/
├── pyproject.toml
├── .env.example
├── src/
│   └── tutor/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       ├── schemas.py
│       ├── state.py
│       ├── graph.py
│       ├── prompts.py
│       ├── models/
│       │   └── llm.py
│       ├── agents/
│       │   ├── supervisor.py
│       │   ├── reading.py
│       │   ├── grammar.py
│       │   ├── vocabulary.py
│       │   ├── image_processor.py
│       │   └── aggregator.py
│       ├── services/
│       │   ├── session.py
│       │   ├── streaming.py
│       │   └── image.py
│       ├── routers/
│       │   └── tutor.py
│       └── prompts/
│           ├── supervisor.md
│           ├── reading.md
│           ├── grammar.md
│           ├── vocabulary.md
│           └── level_instructions.yaml
└── tests/
    ├── conftest.py
    ├── fixtures/
    │   ├── texts.py
    │   ├── llm_responses.py
    │   └── images.py
    ├── unit/
    │   ├── test_schemas.py
    │   ├── test_agents.py
    │   ├── test_services.py
    │   └── test_graph.py
    └── integration/
        └── test_api.py
```

---

## 2. 가정 (Assumptions)

| ID | 가정 내용 | 신뢰도 | 위험도 |
|----|-----------|--------|--------|
| A-01 | OpenAI 및 Anthropic API 키가 환경 변수로 제공된다 | 높음 | 낮음 |
| A-02 | 세션 데이터는 서버 메모리에서 관리하며 영구 저장소는 사용하지 않는다 | 높음 | 중간 |
| A-03 | 동시 사용자 수는 초기에 소규모(100명 미만)로 제한된다 | 중간 | 중간 |
| A-04 | 업로드 이미지는 JPEG, PNG, WebP 형식만 허용하며 최대 10MB이다 | 높음 | 낮음 |
| A-05 | LangGraph 0.3+의 Send() API를 사용한 병렬 노드 디스패치가 지원된다 | 높음 | 중간 |
| A-06 | 클라이언트는 SSE(Server-Sent Events) 스트리밍을 지원한다 | 높음 | 낮음 |

---

## 3. 요구사항 (Requirements)

### 모듈 R1: 프로젝트 스캐폴딩 및 설정 시스템

**R1-001** [Ubiquitous]
The system shall provide a `backend/` directory with `src/tutor/` package structure managed by `uv` package manager.

시스템은 `uv` 패키지 매니저로 관리되는 `backend/` 디렉토리 및 `src/tutor/` 패키지 구조를 제공해야 한다.

**R1-002** [Ubiquitous]
The system shall define all dependencies in `pyproject.toml` with exact version constraints.

시스템은 모든 의존성을 `pyproject.toml`에 정확한 버전 제약과 함께 정의해야 한다.

**R1-003** [Ubiquitous]
The system shall load all configuration from environment variables using `config.py` with Pydantic `BaseSettings`, falling back to `.env` file.

시스템은 `config.py`의 Pydantic `BaseSettings`를 통해 모든 설정을 환경 변수에서 로드하며, `.env` 파일을 폴백으로 사용해야 한다.

**R1-004** [Event-Driven]
When the application starts, the system shall validate that all required API keys (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`) are present.

애플리케이션 시작 시, 시스템은 필수 API 키(`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`)의 존재를 검증해야 한다.

**R1-005** [Unwanted Behavior]
If required configuration is missing, the system shall raise a `ValidationError` and halt startup.

필수 설정이 누락된 경우, 시스템은 `ValidationError`를 발생시키고 시작을 중단해야 한다.

---

### 모듈 R2: Pydantic 스키마 및 데이터 모델

**R2-001** [Ubiquitous]
The system shall define request schemas: `AnalyzeRequest` (text, level), `AnalyzeImageRequest` (image_data, mime_type, level), and `ChatRequest` (session_id, question, level).

시스템은 요청 스키마를 정의해야 한다: `AnalyzeRequest`(text, level), `AnalyzeImageRequest`(image_data, mime_type, level), `ChatRequest`(session_id, question, level).

**R2-002** [Ubiquitous]
The system shall define result schemas: `ReadingResult` (summary, main_topic, emotional_tone), `GrammarResult` (tenses, voice, sentence_structure, analysis), and `VocabularyResult` (words list with term, meaning, usage, synonyms).

시스템은 결과 스키마를 정의해야 한다: `ReadingResult`(summary, main_topic, emotional_tone), `GrammarResult`(tenses, voice, sentence_structure, analysis), `VocabularyResult`(단어, 의미, 용법, 동의어를 포함한 words 목록).

**R2-003** [Ubiquitous]
The system shall define `AnalyzeResponse` that aggregates all three tutor results and session_id.

시스템은 세 튜터의 결과와 session_id를 집계하는 `AnalyzeResponse`를 정의해야 한다.

**R2-004** [State-Driven]
While validating input text, the system shall enforce: minimum 10 characters, maximum 5,000 characters.

입력 텍스트 검증 시, 시스템은 최소 10자, 최대 5,000자를 강제해야 한다.

**R2-005** [State-Driven]
While validating comprehension level, the system shall accept only integer values from 1 to 5 inclusive.

이해도 수준 검증 시, 시스템은 1에서 5까지의 정수 값만 허용해야 한다.

**R2-006** [Unwanted Behavior]
If schema validation fails, the system shall return HTTP 422 with detailed field-level error messages.

스키마 검증에 실패하면, 시스템은 상세한 필드 수준 오류 메시지와 함께 HTTP 422를 반환해야 한다.

---

### 모듈 R3: LLM 클라이언트 및 프롬프트 시스템

**R3-001** [Ubiquitous]
The system shall initialize OpenAI and Anthropic clients in `models/llm.py` with configurable timeouts and retry logic.

시스템은 `models/llm.py`에서 설정 가능한 타임아웃 및 재시도 로직으로 OpenAI와 Anthropic 클라이언트를 초기화해야 한다.

**R3-002** [Ubiquitous]
The system shall provide a `get_llm(model_name)` factory function that returns the appropriate LLM client instance.

시스템은 적절한 LLM 클라이언트 인스턴스를 반환하는 `get_llm(model_name)` 팩토리 함수를 제공해야 한다.

**R3-003** [Ubiquitous]
The system shall load prompt templates from `.md` files in the `prompts/` directory via `prompts.py` loader.

시스템은 `prompts.py` 로더를 통해 `prompts/` 디렉토리의 `.md` 파일에서 프롬프트 템플릿을 로드해야 한다.

**R3-004** [Event-Driven]
When a prompt is rendered, the system shall inject variables (text, level, level_instructions) using string template substitution.

프롬프트 렌더링 시, 시스템은 문자열 템플릿 치환을 사용하여 변수(text, level, level_instructions)를 주입해야 한다.

**R3-005** [Ubiquitous]
The system shall load `level_instructions.yaml` at startup and provide level-specific instructions (levels 1-5) to all agents.

시스템은 시작 시 `level_instructions.yaml`을 로드하고 모든 에이전트에 수준별 지침(1-5단계)을 제공해야 한다.

**R3-006** [State-Driven]
While level is 1-2, the system shall provide simple, age-appropriate explanations for middle school students.

수준이 1-2일 때, 시스템은 중학생에게 적합한 간단하고 나이에 맞는 설명을 제공해야 한다.

**R3-007** [State-Driven]
While level is 4-5, the system shall provide advanced linguistic analysis with academic terminology.

수준이 4-5일 때, 시스템은 학문적 용어를 사용한 고급 언어 분석을 제공해야 한다.

---

### 모듈 R4: 에이전트 구현 및 LangGraph 그래프

**R4-001** [Ubiquitous]
The system shall define `TutorState` TypedDict in `state.py` with fields: messages, level, session_id, input_text, reading_result, grammar_result, vocabulary_result, extracted_text, task_type.

시스템은 `state.py`에 `TutorState` TypedDict를 정의해야 한다: messages, level, session_id, input_text, reading_result, grammar_result, vocabulary_result, extracted_text, task_type 필드 포함.

**R4-002** [Event-Driven]
When `task_type` is "analyze", the Supervisor agent (GPT-4o-mini) shall route to parallel execution of Reading, Grammar, and Vocabulary agents.

`task_type`이 "analyze"일 때, Supervisor 에이전트(GPT-4o-mini)는 Reading, Grammar, Vocabulary 에이전트의 병렬 실행으로 라우팅해야 한다.

**R4-003** [Event-Driven]
When `task_type` is "image_process", the Supervisor agent shall route to ImageProcessor agent first, then parallel tutor agents.

`task_type`이 "image_process"일 때, Supervisor 에이전트는 먼저 ImageProcessor 에이전트로, 그 다음 병렬 튜터 에이전트로 라우팅해야 한다.

**R4-004** [Event-Driven]
When `task_type` is "chat", the Supervisor agent shall route to the chat handling node with session context.

`task_type`이 "chat"일 때, Supervisor 에이전트는 세션 컨텍스트와 함께 채팅 처리 노드로 라우팅해야 한다.

**R4-005** [Ubiquitous]
The system shall use LangGraph `Send()` API in `graph.py` to dispatch Reading, Grammar, and Vocabulary agents in parallel.

시스템은 `graph.py`에서 LangGraph `Send()` API를 사용하여 Reading, Grammar, Vocabulary 에이전트를 병렬로 디스패치해야 한다.

**R4-006** [Ubiquitous]
The Reading agent (Claude Sonnet) shall analyze text and return structured `ReadingResult` with summary, main_topic, and emotional_tone.

Reading 에이전트(Claude Sonnet)는 텍스트를 분석하고 summary, main_topic, emotional_tone을 포함한 구조화된 `ReadingResult`를 반환해야 한다.

**R4-007** [Ubiquitous]
The Grammar agent (GPT-4o) shall analyze text and return structured `GrammarResult` using OpenAI structured outputs feature.

Grammar 에이전트(GPT-4o)는 텍스트를 분석하고 OpenAI 구조화된 출력 기능을 사용하여 구조화된 `GrammarResult`를 반환해야 한다.

**R4-008** [Ubiquitous]
The Vocabulary agent (Claude Haiku) shall analyze text and return `VocabularyResult` with a list of key vocabulary items.

Vocabulary 에이전트(Claude Haiku)는 텍스트를 분석하고 핵심 어휘 항목 목록을 포함한 `VocabularyResult`를 반환해야 한다.

**R4-009** [Ubiquitous]
The ImageProcessor agent (Claude Sonnet Vision) shall extract text from image using vision capabilities and update `extracted_text` in state.

ImageProcessor 에이전트(Claude Sonnet Vision)는 비전 기능을 사용하여 이미지에서 텍스트를 추출하고 상태의 `extracted_text`를 업데이트해야 한다.

**R4-010** [Ubiquitous]
The Aggregator node shall collect results from all three tutor agents and compile the final `AnalyzeResponse`.

Aggregator 노드는 세 튜터 에이전트의 결과를 수집하고 최종 `AnalyzeResponse`를 컴파일해야 한다.

**R4-011** [Unwanted Behavior]
If any individual agent fails, the system shall return partial results with error indicators rather than failing the entire request.

개별 에이전트가 실패하면, 시스템은 전체 요청을 실패시키는 대신 오류 표시와 함께 부분 결과를 반환해야 한다.

---

### 모듈 R5: 서비스 계층 및 API 엔드포인트

**R5-001** [Ubiquitous]
The system shall provide `session.py` with in-memory session management supporting CRUD operations and 24-hour TTL.

시스템은 CRUD 연산과 24시간 TTL을 지원하는 메모리 기반 세션 관리를 제공하는 `session.py`를 제공해야 한다.

**R5-002** [Event-Driven]
When a session is created, the system shall generate a unique `session_id` (UUID4) and store conversation history.

세션이 생성될 때, 시스템은 고유한 `session_id`(UUID4)를 생성하고 대화 내역을 저장해야 한다.

**R5-003** [State-Driven]
While a session is active, the system shall maintain message history for context-aware follow-up questions.

세션이 활성 상태일 때, 시스템은 문맥 인식 후속 질문을 위한 메시지 내역을 유지해야 한다.

**R5-004** [Ubiquitous]
The system shall provide `streaming.py` that formats LangGraph output as SSE events with types: `reading_chunk`, `grammar_chunk`, `vocabulary_chunk`, `done`, and `error`.

시스템은 LangGraph 출력을 `reading_chunk`, `grammar_chunk`, `vocabulary_chunk`, `done`, `error` 유형의 SSE 이벤트로 포맷하는 `streaming.py`를 제공해야 한다.

**R5-005** [Ubiquitous]
The system shall provide `image.py` with image validation (type, size), base64 encoding, and preprocessing for LLM consumption.

시스템은 이미지 검증(유형, 크기), base64 인코딩, LLM 소비를 위한 전처리를 제공하는 `image.py`를 제공해야 한다.

**R5-006** [Unwanted Behavior]
If an uploaded image exceeds 10MB or has an unsupported format, the system shall return HTTP 400 with a descriptive error message.

업로드된 이미지가 10MB를 초과하거나 지원되지 않는 형식인 경우, 시스템은 설명적인 오류 메시지와 함께 HTTP 400을 반환해야 한다.

**R5-007** [Event-Driven]
When `POST /api/v1/tutor/analyze` is called with valid text, the system shall execute the LangGraph pipeline and stream results via SSE.

`POST /api/v1/tutor/analyze`가 유효한 텍스트로 호출되면, 시스템은 LangGraph 파이프라인을 실행하고 SSE를 통해 결과를 스트리밍해야 한다.

**R5-008** [Event-Driven]
When `POST /api/v1/tutor/analyze-image` is called with a valid image, the system shall process the image and stream tutor results via SSE.

`POST /api/v1/tutor/analyze-image`가 유효한 이미지로 호출되면, 시스템은 이미지를 처리하고 SSE를 통해 튜터 결과를 스트리밍해야 한다.

**R5-009** [Event-Driven]
When `POST /api/v1/tutor/chat` is called with a session_id and question, the system shall retrieve session context and stream a context-aware response.

`POST /api/v1/tutor/chat`이 session_id와 질문으로 호출되면, 시스템은 세션 컨텍스트를 검색하고 문맥 인식 응답을 스트리밍해야 한다.

**R5-010** [Ubiquitous]
The system shall expose `GET /api/v1/health` that returns service status and LLM connectivity check.

시스템은 서비스 상태와 LLM 연결 확인을 반환하는 `GET /api/v1/health`를 노출해야 한다.

**R5-011** [Ubiquitous]
The system shall configure CORS in `main.py` to allow configurable origins, supporting local development and production environments.

시스템은 `main.py`에서 설정 가능한 출처를 허용하도록 CORS를 구성하여 로컬 개발 및 프로덕션 환경을 지원해야 한다.

**R5-012** [Unwanted Behavior]
If a `session_id` is not found in `POST /api/v1/tutor/chat`, the system shall create a new session and proceed with the request.

`POST /api/v1/tutor/chat`에서 `session_id`를 찾을 수 없는 경우, 시스템은 새 세션을 생성하고 요청을 계속 처리해야 한다.

---

## 4. 명세 (Specifications)

### 4.1 API 엔드포인트 명세

#### POST /api/v1/tutor/analyze

```
Request Body (AnalyzeRequest):
  - text: str (10-5000자)
  - level: int (1-5)

Response: text/event-stream (SSE)
  event: reading_chunk  → {"summary": "...", "main_topic": "...", "emotional_tone": "..."}
  event: grammar_chunk  → {"tenses": [...], "voice": "...", "sentence_structure": "...", "analysis": "..."}
  event: vocabulary_chunk → {"words": [{"term": "...", "meaning": "...", "usage": "...", "synonyms": [...]}]}
  event: done           → {"session_id": "uuid", "status": "complete"}
  event: error          → {"message": "...", "code": "..."}
```

#### POST /api/v1/tutor/analyze-image

```
Request Body (AnalyzeImageRequest):
  - image_data: str (base64 인코딩)
  - mime_type: str ("image/jpeg" | "image/png" | "image/webp")
  - level: int (1-5)

Response: text/event-stream (SSE)
  (analyze와 동일한 SSE 이벤트 스트림)
```

#### POST /api/v1/tutor/chat

```
Request Body (ChatRequest):
  - session_id: str (UUID)
  - question: str
  - level: int (1-5)

Response: text/event-stream (SSE)
  event: chat_chunk → {"content": "...", "role": "assistant"}
  event: done       → {"session_id": "uuid", "status": "complete"}
```

#### GET /api/v1/health

```
Response: application/json
  {
    "status": "healthy",
    "openai": "connected" | "error",
    "anthropic": "connected" | "error",
    "version": "1.0.0"
  }
```

### 4.2 LangGraph 그래프 흐름

```
[START]
  ↓
[supervisor_node]  ← task_type 판단
  ↓ (조건부 엣지)
  ├─ "analyze" → Send("reading_node"), Send("grammar_node"), Send("vocabulary_node")  [병렬]
  ├─ "image_process" → [image_processor_node] → Send(3 튜터) [순차 후 병렬]
  └─ "chat" → [chat_node]
  ↓
[aggregator_node]  ← 병렬 결과 수집
  ↓
[END]
```

### 4.3 세션 상태 구조

```python
class TutorState(TypedDict):
    messages: list[dict]          # 대화 내역
    level: int                    # 이해도 수준 (1-5)
    session_id: str               # UUID4
    input_text: str               # 분석할 텍스트
    reading_result: ReadingResult | None
    grammar_result: GrammarResult | None
    vocabulary_result: VocabularyResult | None
    extracted_text: str | None    # OCR 결과
    task_type: str                # "analyze" | "image_process" | "chat"
```

---

## 5. 추적성 태그 (Traceability Tags)

| 태그 ID | 요구사항 | 구현 파일 | 테스트 파일 |
|---------|----------|-----------|-------------|
| TAG-R1 | 프로젝트 스캐폴딩 | `pyproject.toml`, `config.py` | `tests/unit/test_config.py` |
| TAG-R2 | Pydantic 스키마 | `schemas.py` | `tests/unit/test_schemas.py` |
| TAG-R3 | LLM 클라이언트/프롬프트 | `models/llm.py`, `prompts.py` | `tests/unit/test_prompts.py` |
| TAG-R4 | 에이전트 및 그래프 | `agents/*.py`, `graph.py` | `tests/unit/test_agents.py` |
| TAG-R5 | 서비스 및 API | `services/*.py`, `routers/tutor.py` | `tests/integration/test_api.py` |
