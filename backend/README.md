# AI English Tutor Backend

AI 기반 개인 맞춤형 영어 학습 튜터 백엔드 시스템

중학생(13-15세)을 대상으로 고등학교 영어 선행학습을 지원합니다.

## 기술 스택

| 구성 요소 | 버전 | 역할 |
|-----------|------|------|
| Python | 3.13+ | 런타임 |
| FastAPI | 0.115+ | 웹 프레임워크 |
| LangGraph | 0.3+ | 에이전트 오케스트레이션 |
| Pydantic | 2.10+ | 데이터 검증 및 직렬화 |
| uv | 0.6+ | 패키지 관리자 |

## 설치 및 실행

### 요구사항

- Python 3.13 이상
- uv 패키지 매니저
- OpenAI API 키
- Anthropic API 키

### 설치

```bash
cd backend
uv sync
```

### 환경 변수 설정

```bash
cp .env.example .env
```

`.env` 파일을 열어 API 키를 입력합니다:

```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
ENVIRONMENT=development
LOG_LEVEL=DEBUG
HOST=0.0.0.0
PORT=8000
```

### 개발 서버 실행

```bash
uv run uvicorn src.tutor.main:app --reload
```

서버가 `http://localhost:8000`에서 실행됩니다.

### API 문서

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 테스트

### 전체 테스트 실행

```bash
uv run pytest tests/ -v
```

### 커버리지 포함

```bash
uv run pytest tests/ -v --cov=src/tutor --cov-report=term-missing
```

### 린트 검사

```bash
uv run ruff check src tests
uv run ruff format --check src tests
```

## API 엔드포인트

### GET /api/v1/health

헬스 체크 엔드포인트

**응답:**
```json
{
  "status": "healthy",
  "openai": "connected",
  "anthropic": "connected",
  "version": "0.1.0"
}
```

### POST /api/v1/tutor/analyze

텍스트 분석 (SSE 스트리밍)

**요청:**
```json
{
  "text": "The quick brown fox jumps over the lazy dog.",
  "level": 3
}
```

**응답 (SSE 이벤트):**
- `reading_chunk`: 독해 분석 결과
- `grammar_chunk`: 문법 분석 결과
- `vocabulary_chunk`: 어휘 분석 결과
- `done`: 완료 이벤트
- `error`: 오류 이벤트

### POST /api/v1/tutor/analyze-image

이미지 분석 (SSE 스트리밍)

**요청:**
```json
{
  "image_data": "base64...",
  "mime_type": "image/png",
  "level": 3
}
```

### POST /api/v1/tutor/chat

채팅 (SSE 스트리밍)

**요청:**
```json
{
  "session_id": "uuid",
  "question": "What does 'ubiquitous' mean?",
  "level": 3
}
```

## 프로젝트 구조

```
src/tutor/
├── __init__.py          # 패키지 초기화
├── main.py              # FastAPI 앱 진입점
├── config.py            # 설정 관리 (Pydantic BaseSettings)
├── schemas.py           # 요청/응답 Pydantic 스키마
├── state.py             # LangGraph 상태 정의 (TutorState)
├── graph.py             # LangGraph 그래프 정의
├── prompts.py           # 프롬프트 로더
├── models/              # LLM 모델
│   ├── __init__.py
│   └── llm.py           # OpenAI/Anthropic 클라이언트 팩토리
├── agents/              # LangGraph 에이전트
│   ├── __init__.py
│   ├── supervisor.py    # 작업 라우팅
│   ├── reading.py       # 독해 분석
│   ├── grammar.py       # 문법 분석
│   ├── vocabulary.py    # 어휘 분석
│   ├── image_processor.py # 이미지 OCR
│   └── aggregator.py    # 결과 집계
├── services/            # 비즈니스 로직
│   ├── __init__.py
│   ├── session.py       # 세션 관리
│   ├── streaming.py     # SSE 포맷팅
│   └── image.py         # 이미지 처리
├── routers/             # API 라우터
│   ├── __init__.py
│   └── tutor.py         # 튜터 엔드포인트
└── prompts/             # 프롬프트 템플릿
    ├── supervisor.md
    ├── reading.md
    ├── grammar.md
    ├── vocabulary.md
    └── level_instructions.yaml
```

## LangGraph 워크플로우

```
[START]
  ↓
[supervisor]  ← task_type 판단
  ↓
  ├─ "analyze" → [reading, grammar, vocabulary] (병렬)
  ├─ "image_process" → [image_processor] → [tutors] (순차 후 병렬)
  └─ "chat" → [chat]
  ↓
[aggregator]  ← 결과 집계
  ↓
[END]
```

## LLM 모델 배정

| 에이전트 | 모델 | 역할 |
|----------|------|------|
| Supervisor | GPT-4o-mini | 작업 라우팅 및 조율 |
| Reading Tutor | Claude Sonnet | 읽기 이해 분석 |
| Grammar Tutor | GPT-4o | 문법 분석 (구조화된 출력) |
| Vocabulary Tutor | Claude Haiku | 어휘 분석 (비용 최적화) |
| Image Processor | Claude Sonnet Vision | 이미지 텍스트 추출 |

## 개발 가이드

### 새 에이전트 추가

1. `src/tutor/agents/`에 새 에이전트 파일 생성
2. `src/tutor/graph.py`에 노드 추가
3. 라우팅 로직 업데이트

### 새 API 엔드포인트 추가

1. `src/tutor/schemas.py`에 요청/응답 스키마 추가
2. `src/tutor/routers/tutor.py`에 엔드포인트 구현
3. 테스트 작성

## 라이선스

MIT
