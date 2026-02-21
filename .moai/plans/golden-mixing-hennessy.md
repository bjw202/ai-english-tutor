# AI English Tutor - Architecture Design Document

## Context

고등학교 영어 선행을 하는 중학생을 위한 AI 영어 튜터링 웹앱을 설계한다. 사용자가 영어 지문(텍스트 또는 사진)을 입력하면, LangGraph 기반 멀티 에이전트 시스템이 **독해/문법/어휘** 3개 영역의 튜터링 문서를 생성하여 탭 형태의 채팅 UI로 제공한다. 모든 설명은 한국어로 제공되며, 통합 슬라이더로 설명 레벨(범위)을 조절할 수 있다.

---

## 1. System Architecture

```
[Browser]
    |  HTTPS
    v
[Next.js 15 on Vercel]         -- Frontend + API Proxy
    |  SSE (Server-Sent Events)
    v
[FastAPI on Railway]            -- Backend API Server
    |
    v
[LangGraph StateGraph]         -- Multi-Agent Orchestrator
    |
    +---> Reading Tutor   (Claude Sonnet)  -- 독해 분석
    +---> Grammar Tutor   (GPT-4o)         -- 문법 분석
    +---> Vocabulary Tutor (Claude Haiku)   -- 어휘 분석
```

### Design Principles

- **Parallel Dispatch**: Supervisor가 Send() API로 3개 Tutor를 동시 실행 (응답 시간 ~3x 단축)
- **Independent Streaming**: 각 Tutor 결과가 SSE event 타입으로 분리되어 해당 탭에 독립 스트리밍
- **LLM Vision OCR**: Tesseract.js 대신 Claude Vision API로 이미지 텍스트 추출 + 문맥 이해 동시 수행
- **Korean Explanations**: 모든 튜터링 설명을 한국어로 제공 (영어 원문은 보존)
- **Session-based**: 인증 없이 브라우저 세션 기반으로 대화 이력 유지

---

## 2. Multi-Agent Architecture (LangGraph)

### 2.1 Graph Structure

```
START
  |
  v
[image_processor]  -- 이미지 입력 시 Vision API로 텍스트 추출, 텍스트만이면 패스
  |
  v
[supervisor]       -- Send()로 3개 Tutor에 병렬 디스패치
  |         |         |
  v         v         v
[reading] [grammar] [vocabulary]   -- 병렬 실행
  |         |         |
  v         v         v
[aggregator]       -- 결과 집계, 세션 상태 업데이트
  |
  v
END
```

### 2.2 State Schema

```python
class TutorState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]  # 대화 이력
    input_text: str                         # 영어 텍스트
    input_image_url: Optional[str]          # 이미지 (있는 경우)
    extracted_text: Optional[str]           # Vision API 추출 텍스트
    explanation_level: int                  # 1-5 통합 레벨
    reading_analysis: Optional[dict]        # 독해 분석 결과
    grammar_feedback: Optional[dict]        # 문법 분석 결과
    vocabulary_list: Optional[dict]         # 어휘 분석 결과
    session_id: str
    processing_status: dict                 # 각 tutor 처리 상태
```

### 2.3 Explanation Level System (통합 슬라이더 1개)

대상: 고등학교 영어 선행을 하는 중학생

| Level | Name | Description |
|-------|------|-------------|
| 1 | 기초 | 모든 문법/어휘/구문을 상세히 설명. 한국어 번역 문장 단위 제공 |
| 2 | 초중급 | 기초 문법(be동사, 단순시제) 생략. 중급 이상 설명 |
| 3 | 중급 (기본값) | 일반적 문법/어휘 생략. 복잡한 구문과 고급 어휘 중심 |
| 4 | 중고급 | 고급 문법 패턴, 뉘앙스, 문체 분석 중심 |
| 5 | 고급 | 미묘한 뉘앙스, 문화적 맥락, 수사적 장치만 설명 |

각 Tutor의 System Prompt에 레벨 필터링 규칙을 주입하여 설명 범위를 제어한다.

### 2.4 LLM Model Assignment

| Agent | Model | Rationale |
|-------|-------|-----------|
| Image Processor | Claude Sonnet | Vision API, 정확한 텍스트 추출 |
| Supervisor | GPT-4o-mini | 라우팅만 담당, 비용 효율적 |
| Reading Tutor | Claude Sonnet | 긴 컨텍스트, 깊이 있는 분석 |
| Grammar Tutor | GPT-4o | Structured Output, 문법 분석 정확도 |
| Vocabulary Tutor | Claude Haiku | 빠른 응답, 비용 효율적 |

### 2.5 Follow-up Questions

대화 이력(`messages`)을 유지하여 후속 질문을 지원한다. Supervisor가 질문을 분석하여 관련 Tutor에게만 라우팅하거나 전체에 재디스패치한다.

---

## 3. Backend Architecture (FastAPI + LangGraph)

### 3.1 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/tutor/analyze` | 텍스트 분석 (SSE 스트리밍 응답) |
| POST | `/api/v1/tutor/analyze-image` | 이미지 분석 (multipart + SSE) |
| POST | `/api/v1/tutor/chat` | Follow-up 질문 (SSE) |
| GET | `/api/v1/tutor/session/{id}` | 세션 이력 조회 |
| PUT | `/api/v1/tutor/config` | 설명 레벨 변경 |
| GET | `/api/v1/health` | Health check |

### 3.2 SSE Streaming Design

각 Tutor 결과를 SSE `event` 필드로 분리하여 독립 스트리밍:

```
event: reading
data: {"type": "chunk", "content": "..."}

event: grammar
data: {"type": "chunk", "content": "..."}

event: vocabulary
data: {"type": "chunk", "content": "..."}

event: complete
data: {"status": "done"}
```

### 3.3 Image Processing

LLM Vision API를 직접 사용하여 이미지에서 텍스트를 추출한다. Tesseract.js 대비 장점:
- 텍스트 추출 + 문맥 이해 동시 수행
- 손글씨, 교과서 사진, 시험지 등 다양한 형식 지원
- 추가 라이브러리 의존성 불필요

### 3.4 Session Management

- MVP: LangGraph `MemorySaver` (in-memory checkpointer)
- 향후: Redis checkpointer로 확장 가능

---

## 4. Frontend Architecture (Next.js 15)

### 4.1 Component Hierarchy

```
App (layout.tsx)
+-- Header
|   +-- Logo
|   +-- LevelSlider (통합 1-5)
|
+-- ChatPage (page.tsx)
    +-- ChatContainer
        +-- MessageList
        |   +-- UserMessage (텍스트 + 이미지 미리보기)
        |   +-- TutorMessage
        |       +-- TabbedOutput (shadcn/ui Tabs)
        |           +-- Tab: Reading (독해 분석)
        |           +-- Tab: Grammar (문법 분석)
        |           +-- Tab: Vocabulary (어휘 분석)
        |
        +-- ChatInput
            +-- TextArea
            +-- ImageUploadButton
            +-- SendButton
```

### 4.2 Key Custom Hooks

- `use-tutor-stream.ts`: SSE EventSource로 각 Tutor 결과를 독립 수신/관리
- `use-session.ts`: 세션 ID 생성 및 유지
- `use-level-config.ts`: 설명 레벨 설정 관리 (localStorage 저장)

### 4.3 Streaming Flow

1. 사용자가 텍스트/이미지 입력
2. `useTutorStream` 훅이 SSE 연결 시작
3. `event: reading` → Reading 탭에 실시간 렌더링
4. `event: grammar` → Grammar 탭에 실시간 렌더링
5. `event: vocabulary` → Vocabulary 탭에 실시간 렌더링
6. `event: complete` → 스트리밍 종료

### 4.4 Next.js Route Handlers (API Proxy)

Frontend → Backend SSE 스트림을 패스스루하는 Route Handler:
- `app/api/tutor/analyze/route.ts`
- `app/api/tutor/analyze-image/route.ts`
- `app/api/tutor/chat/route.ts`

이점: CORS 문제 회피, API 키 보호, 단일 도메인 접근

---

## 5. Deployment Architecture

| Component | Platform | Cost |
|-----------|----------|------|
| Frontend (Next.js) | Vercel Hobby | Free |
| Backend (FastAPI) | Railway | ~$5/month |
| LLM APIs | OpenAI + Anthropic | Pay per use |

### Environment Variables

**Vercel**: `BACKEND_URL`
**Railway**: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `ALLOWED_ORIGINS`

---

## 6. Directory Structure

```
ai-english-tutor/
+-- backend/
|   +-- pyproject.toml              # uv 패키지 관리
|   +-- Dockerfile
|   +-- .env.example
|   +-- src/
|   |   +-- main.py                 # FastAPI entrypoint
|   |   +-- config.py               # Pydantic Settings
|   |   +-- api/
|   |   |   +-- router.py           # API router
|   |   |   +-- tutor.py            # Tutor endpoints (SSE)
|   |   |   +-- schemas.py          # Request/Response models
|   |   +-- agents/
|   |   |   +-- graph.py            # LangGraph StateGraph build
|   |   |   +-- state.py            # TutorState definition
|   |   |   +-- supervisor.py       # Supervisor routing
|   |   |   +-- reading.py          # Reading Tutor
|   |   |   +-- grammar.py          # Grammar Tutor
|   |   |   +-- vocabulary.py       # Vocabulary Tutor
|   |   |   +-- aggregator.py       # Result aggregation
|   |   |   +-- prompts.py          # 프롬프트 로더 (파일 읽기 + 변수 주입)
|   |   |   +-- prompts/             # 프롬프트 템플릿 (코드와 분리)
|   |   |   |   +-- supervisor.md    # Supervisor 라우팅 프롬프트
|   |   |   |   +-- reading_tutor.md # 독해 튜터 시스템 프롬프트
|   |   |   |   +-- grammar_tutor.md # 문법 튜터 시스템 프롬프트
|   |   |   |   +-- vocabulary_tutor.md # 어휘 튜터 시스템 프롬프트
|   |   |   |   +-- image_processor.md  # 이미지 처리 프롬프트
|   |   |   |   +-- level_instructions.yaml # 레벨별 필터링 규칙 (1-5)
|   |   +-- services/
|   |   |   +-- image.py            # LLM Vision processing
|   |   |   +-- session.py          # Session management
|   |   |   +-- streaming.py        # SSE utilities
|   |   +-- models/
|   |       +-- llm.py              # LLM factory (OpenAI, Anthropic)
|   +-- tests/
|       +-- test_agents/
|       +-- test_api/
|       +-- test_services/
|
+-- frontend/
|   +-- package.json                # pnpm
|   +-- next.config.ts
|   +-- tailwind.config.ts
|   +-- .env.example
|   +-- src/
|   |   +-- app/
|   |   |   +-- layout.tsx
|   |   |   +-- page.tsx            # Main chat page
|   |   |   +-- globals.css
|   |   |   +-- api/tutor/
|   |   |       +-- analyze/route.ts
|   |   |       +-- analyze-image/route.ts
|   |   |       +-- chat/route.ts
|   |   +-- components/
|   |   |   +-- ui/                 # shadcn/ui (tabs, slider, button, etc.)
|   |   |   +-- chat/
|   |   |   |   +-- chat-container.tsx
|   |   |   |   +-- message-list.tsx
|   |   |   |   +-- user-message.tsx
|   |   |   |   +-- tutor-message.tsx
|   |   |   |   +-- chat-input.tsx
|   |   |   |   +-- image-upload.tsx
|   |   |   +-- tutor/
|   |   |   |   +-- tabbed-output.tsx
|   |   |   |   +-- reading-panel.tsx
|   |   |   |   +-- grammar-panel.tsx
|   |   |   |   +-- vocabulary-panel.tsx
|   |   |   +-- controls/
|   |   |       +-- header.tsx
|   |   |       +-- level-slider.tsx
|   |   +-- hooks/
|   |   |   +-- use-tutor-stream.ts
|   |   |   +-- use-session.ts
|   |   |   +-- use-level-config.ts
|   |   +-- lib/
|   |   |   +-- api.ts
|   |   |   +-- utils.ts
|   |   |   +-- constants.ts
|   |   +-- types/
|   |       +-- tutor.ts
|   |       +-- chat.ts
|   +-- tests/
|
+-- CLAUDE.md
+-- .gitignore
+-- README.md
```

---

## 7. Technology Stack

### Backend
| Tech | Version | Purpose |
|------|---------|---------|
| Python | 3.13+ | Runtime |
| FastAPI | 0.115+ | Web framework |
| Uvicorn | 0.34+ | ASGI server |
| LangGraph | 0.3+ | Multi-agent orchestration |
| langchain-openai | 0.3+ | OpenAI integration |
| langchain-anthropic | 0.3+ | Anthropic integration |
| Pydantic | 2.10+ | Data validation |
| uv | 0.6+ | Package management |
| pytest | 8.3+ | Testing |
| ruff | 0.9+ | Linting/Formatting |

### Frontend
| Tech | Version | Purpose |
|------|---------|---------|
| Next.js | 15.x | React framework |
| React | 19.x | UI library |
| TypeScript | 5.9+ | Type safety |
| Tailwind CSS | 4.x | Styling |
| shadcn/ui | latest | UI components (Tabs, Slider, etc.) |
| pnpm | 10.x | Package management |
| Vitest | 3.x | Testing |

---

## 8. Implementation Phases

### Phase 1: Backend Core
- Project init (uv, pyproject.toml, FastAPI skeleton)
- TutorState definition
- LangGraph graph build with Supervisor + 3 Tutors
- SSE streaming endpoint
- Basic tests

### Phase 2: Frontend Core
- Project init (Next.js 15, shadcn/ui, Tailwind)
- Chat UI components (MessageList, ChatInput)
- SSE streaming hook (useTutorStream)
- Tabbed output (Reading/Grammar/Vocabulary panels)
- Level slider
- Route Handler proxies

### Phase 3: Image + Integration
- Image upload UI
- LLM Vision API image processing
- End-to-end integration
- Error handling, loading states

### Phase 4: Deploy + Polish
- Backend Dockerfile + Railway deploy
- Frontend Vercel deploy
- Environment variables
- Performance optimization

---

## 9. Verification Plan

### Backend
- `pytest` 로 각 Agent 노드 단위 테스트
- LangGraph graph 통합 테스트 (텍스트 입력 → 3개 결과 반환)
- SSE 스트리밍 엔드포인트 테스트 (httpx AsyncClient)
- 이미지 처리 테스트 (mock Vision API)

### Frontend
- Vitest + React Testing Library로 컴포넌트 테스트
- SSE hook 테스트 (mock EventSource)
- E2E: 브라우저에서 텍스트 입력 → 3개 탭에 결과 표시 확인

### Integration
- Local: Next.js (3000) + FastAPI (8000) 동시 실행
- 텍스트 입력 → SSE 스트리밍 → 탭별 실시간 렌더링 확인
- 이미지 업로드 → Vision 추출 → 분석 결과 확인
- 레벨 변경 → 설명 범위 변화 확인
- Follow-up 질문 → 관련 탭에 추가 응답 확인
