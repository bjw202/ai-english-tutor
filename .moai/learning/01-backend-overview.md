# AI 영어 튜터 백엔드 가이드 - 1부: 전체 구조

> 주니어 개발자를 위한 친절한 설명서
> 작성일: 2026-02-21

---

## 1. 프로젝트 개요

### 1.1 이 프로젝트가 뭐죠?

**AI 기반 개인 맞춤형 영어 학습 튜터**의 백엔드 시스템입니다.

```
사용자 입력: "The quick brown fox jumps over the lazy dog."

AI 응답:
  - 요약: 여우가 개를 뛰어넘는 이야기입니다.
  - 문법: 현재 시제, 능동태, 단순문
  - 어휘: quick(빠른), jumps(뛰다), lazy(게으른)
```

### 1.2 기술 스택

| 기술 | 버전 | 왜 썼나요? |
|------|------|-----------|
| Python | 3.13+ | AI/ML 분야 표준 언어 |
| FastAPI | 0.115+ | 빠르고 현대적인 웹 프레임워크 |
| LangGraph | 0.3+ | AI 에이전트 조율 도구 |
| Pydantic | 2.10+ | 데이터 검증 |
| uv | 0.6+ | pip보다 10배 빠른 패키지 매니저 |
| pytest | 8.3+ | 테스트 프레임워크 |
| LangChain OpenAI | 0.3+ | OpenAI 및 GLM API 통합 |

---

## 2. 디렉토리 구조

```
backend/
├── pyproject.toml          # 프로젝트 설정
├── .env.example            # 환경변수 예시
├── src/tutor/              # 메인 소스 코드
│   ├── main.py             # FastAPI 앱 진입점
│   ├── config.py           # 설정 관리
│   ├── schemas.py          # 데이터 모델
│   ├── state.py            # LangGraph 상태 정의
│   ├── graph.py            # LangGraph 그래프 정의
│   ├── agents/             # AI 에이전트들
│   │   ├── supervisor.py   # 작업 분배 담당
│   │   ├── reading.py      # 읽기 분석
│   │   ├── grammar.py      # 문법 분석
│   │   ├── vocabulary.py   # 어휘 분석
│   │   └── aggregator.py   # 결과 통합
│   ├── models/             # LLM 모델 팩토리
│   │   └── llm.py          # get_llm() 팩토리 함수
│   ├── utils/              # 유틸리티
│   │   └── markdown_normalizer.py  # LLM 출력 정규화
│   ├── services/           # 비즈니스 로직
│   │   ├── session.py      # 세션 관리
│   │   ├── streaming.py    # SSE 스트리밍
│   │   └── image.py        # 이미지 처리
│   └── routers/            # API 엔드포인트
│       └── tutor.py        # /api/v1/tutor/* 엔드포인트
└── tests/                  # 테스트 코드
    ├── conftest.py         # 테스트 설정
    ├── unit/               # 단위 테스트
    └── integration/        # 통합 테스트
```

---

## 3. 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                        클라이언트 (프론트엔드)                      │
│                           사용자                                  │
└─────────────────────────────┬───────────────────────────────────┘
                              │ 텍스트 입력
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI 서버                               │
│  ┌──────────────┐    ┌──────────────┐                           │
│  │ API Router   │───▶│ Pydantic     │                           │
│  │ /api/v1/*    │    │ 데이터 검증   │                           │
│  └──────────────┘    └──────────────┘                           │
└─────────────────────────────┬───────────────────────────────────┘
                              │ TutorState 전달
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LangGraph 멀티 에이전트                         │
│                                                                  │
│    ┌───────────┐                                                │
│    │ Supervisor│◀── Claude Haiku로 사전 분석                    │
│    └─────┬─────┘     (문장 분리, 난이도 평가)                    │
│          │                                                       │
│    ┌─────┼─────────────────────────┐                            │
│    │     │                         │                            │
│    ▼     ▼                         ▼                            │
│ ┌──────┐ ┌──────┐             ┌─────────┐                       │
│ │Reading│ │Grammar│             │Vocabulary│                     │
│ │Agent │ │Agent │             │ Agent   │                       │
│ └──┬───┘ └──┬───┘             └────┬────┘                       │
│    │        │                      │                            │
│    └────────┼──────────────────────┘                            │
│             ▼                                                    │
│      ┌─────────────┐                                             │
│      │ Aggregator  │                                             │
│      └──────┬──────┘                                             │
└─────────────┼───────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        LLM 모델들                                 │
│  ┌──────────────────────────────────────────┐                  │
│  │   OpenAI gpt-4o-mini (모든 에이전트)      │                  │
│  │   - Supervisor, Reading, Grammar, Vocab  │                  │
│  └──────────────────────────────────────────┘                  │
│  ┌──────────────────────────────────────────┐ (선택)           │
│  │   GLM via OpenAI API Compatible          │                  │
│  │   - base_url: https://open.bigmodel.cn/  │                  │
│  └──────────────────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. 요청 흐름

```
1. 사용자가 텍스트 입력
   │
   ▼
2. POST /api/v1/tutor/analyze 요청
   │
   ▼
3. Pydantic이 데이터 검증 (text: 10-5000자, level: 1-5)
   │
   ▼
4. LangGraph 그래프 시작
   │
   ▼
5. Supervisor가 Claude Haiku로 사전 분석 (문장 분리, 난이도 평가, 학습 포커스 추천) → supervisor_analysis 생성
   │
   ▼
6. 3개 에이전트 병렬 실행 (Send API)
   ├── Reading Agent  ──▶ Claude Sonnet
   ├── Grammar Agent  ──▶ GPT-4o
   └── Vocabulary Agent ─▶ Claude Haiku
   │
   ▼
7. Aggregator가 3개 결과 통합
   │
   ▼
8. SSE로 실시간 스트리밍 응답
   │
   ▼
9. 사용자에게 결과 표시
```

---

## 5. LLM 모델 설정

### 5.0 모델 통합 (v1.1.1 이후)

2026-02-23 업데이트: 모든 에이전트가 **gpt-4o-mini**로 통일되었습니다.

**비용 절감:**
- 기존: ~$152/월 (1,000 requests) - Claude Sonnet/Haiku + GPT-4o 혼합
- 현재: ~$7/월 (1,000 requests) - gpt-4o-mini 통일
- **95% 비용 절감**

**LLM 팩토리 함수 (`models/llm.py`):**

```python
def get_llm(model_name: str, max_tokens: int = 2048, timeout: int = 120):
    if "claude" in model_name:
        # Claude 모델 요청 → ValueError 발생
        raise ValueError("Claude models are not supported. Use OpenAI or GLM models instead.")
    elif "gpt" in model_name:
        return ChatOpenAI(model=model_name, max_tokens=max_tokens, timeout=timeout)
    elif "glm" in model_name:
        return ChatOpenAI(
            model=model_name,
            base_url="https://open.bigmodel.cn/api/paas/v4/",
            api_key=settings.GLM_API_KEY,
            max_tokens=max_tokens,
            timeout=timeout,
        )
    else:
        raise ValueError(f"Unknown model: {model_name}")
```

**설정 기반 모델 선택 (`config.py`):**

```python
SUPERVISOR_MODEL: str = "gpt-4o-mini"
READING_MODEL: str = "gpt-4o-mini"
GRAMMAR_MODEL: str = "gpt-4o-mini"
VOCABULARY_MODEL: str = "gpt-4o-mini"
GLM_API_KEY: str | None = None  # 선택사항
OCR_MODEL: str = "glm-4v-flash"  # 향후 이미지 분석용
```

**환경 변수:**
- `OPENAI_API_KEY`: 필수 (gpt-4o-mini용)
- `GLM_API_KEY`: 선택 (GLM 모델 사용 시에만)
- `ANTHROPIC_API_KEY`: 제거됨 (v1.1.1부터 불필요)

---

## 6. 핵심 파일 설명

### 5.1 main.py - 앱 진입점

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def create_app() -> FastAPI:
    # 1. FastAPI 앱 생성
    app = FastAPI(
        title="AI English Tutor",
        version="0.1.0",
    )

    # 2. CORS 설정 (프론트엔드 접근 허용)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 3. API 라우터 등록
    app.include_router(tutor.router, prefix="/api/v1")

    return app

# 전역 인스턴스 (uvicorn이 이걸 실행)
app = create_app()
```

**실행 방법:**
```bash
uv run uvicorn tutor.main:app --reload
```

### 5.2 schemas.py - 데이터 모델

```python
from pydantic import BaseModel, Field

# 요청 모델
class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=5000)
    level: int = Field(..., ge=1, le=5)  # 1~5 사이

# 결과 모델들 (모두 마크다운 콘텐츠 기반으로 변경됨)
class ReadingResult(BaseModel):
    content: str  # 한국어 마크다운 (슬래시 읽기 훈련)

class GrammarResult(BaseModel):
    content: str  # 한국어 마크다운 (구조 중심 문법)

class VocabularyWordEntry(BaseModel):
    word: str           # 단어
    content: str        # 한국어 마크다운 (6단계 어원 설명)

class VocabularyResult(BaseModel):
    words: list[VocabularyWordEntry]

# NEW: Supervisor 사전 분석
class SentenceEntry(BaseModel):
    text: str
    difficulty: int  # 1-5
    focus: list[str]

class SupervisorAnalysis(BaseModel):
    sentences: list[SentenceEntry]
    overall_difficulty: int
    focus_summary: list[str]

# 최종 응답
class AnalyzeResponse(BaseModel):
    session_id: str
    supervisor_analysis: SupervisorAnalysis
    reading: ReadingResult | None
    grammar: GrammarResult | None
    vocabulary: VocabularyResult | None
```

**Pydantic이 하는 일:**
1. **검증**: 잘못된 데이터가 들어오면 HTTP 422 에러
2. **직렬화**: Python 객체 ↔ JSON 변환
3. **문서화**: Swagger UI에 스키마 표시

---

## 6. API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| GET | /api/v1/health | 서버 상태 확인 |
| POST | /api/v1/tutor/analyze | 텍스트 분석 |
| POST | /api/v1/tutor/analyze-image | 이미지 분석 |
| POST | /api/v1/tutor/chat | 대화 |

**요청 예시:**
```bash
curl -X POST http://localhost:8000/api/v1/tutor/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world, this is a test.", "level": 3}'
```

**응답 (SSE 스트리밍):**
```
event: supervisor_analysis_chunk
data: {"sentences": [{"text": "...", "difficulty": 3, "focus": ["..."]}, ...], "overall_difficulty": 3, "focus_summary": ["..."]}

event: reading_chunk
data: {"content": "### 문장 1\n\n> The quick brown fox...\n\n#### 단위별 해석\n\n..."}

event: grammar_chunk
data: {"content": "### 문장 1\n\n> 원문\n\n#### 문법 포인트\n\n..."}

event: vocabulary_chunk
data: {"words": [{"word": "quick", "content": "## quick\n\n### 1. 기본 뜻\n\n..."}, ...]}

event: done
data: {"session_id": "uuid", "status": "complete"}
```
