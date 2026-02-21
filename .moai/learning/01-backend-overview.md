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
│    │ Supervisor│◀── task_type 판단                              │
│    └─────┬─────┘                                                │
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
│  ┌──────────────────┐         ┌──────────────────┐              │
│  │ OpenAI GPT-4o    │         │ Anthropic Claude │              │
│  │ (Grammar 분석)   │         │ (Reading, Vocab) │              │
│  └──────────────────┘         └──────────────────┘              │
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
5. Supervisor가 task_type 확인 → "analyze"
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

## 5. 핵심 파일 설명

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

# 결과 모델들
class ReadingResult(BaseModel):
    summary: str          # 텍스트 요약
    main_topic: str       # 주제
    emotional_tone: str   # 감정 톤

class GrammarResult(BaseModel):
    tenses: list[str]     # 사용된 시제들
    voice: str            # 능동태/수동태
    sentence_structure: str  # 문장 구조
    analysis: str         # 상세 분석

class VocabularyWord(BaseModel):
    term: str             # 단어
    meaning: str          # 의미
    usage: str            # 예문
    synonyms: list[str]   # 동의어

class VocabularyResult(BaseModel):
    words: list[VocabularyWord]

# 최종 응답
class AnalyzeResponse(BaseModel):
    session_id: str
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
event: reading_chunk
data: {"summary": "...", "main_topic": "...", "emotional_tone": "..."}

event: grammar_chunk
data: {"tenses": [...], "voice": "...", "sentence_structure": "...", "analysis": "..."}

event: vocabulary_chunk
data: {"words": [...]}

event: done
data: {"session_id": "uuid", "status": "complete"}
```
