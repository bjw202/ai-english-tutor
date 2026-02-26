# 프로젝트 구조 (Project Structure)

## 전체 디렉토리 구조

```
ai-english-tutor/
├── backend/                          # FastAPI 백엔드 서버
│   ├── pyproject.toml               # Python 프로젝트 설정 및 의존성
│   ├── Dockerfile                   # Docker 컨테이너 이미지 정의
│   ├── .env.example                 # 환경 변수 예제
│   └── src/
│       └── tutor/                   # 튜터 애플리케이션 메인 패키지
│           ├── main.py              # FastAPI 앱 초기화 및 라우터 등록
│           ├── config.py            # 설정 관리 (API 키, 데이터베이스 URL 등)
│           ├── schemas.py           # Pydantic 요청/응답 모델
│           ├── state.py             # TutorState TypedDict (LangGraph 상태)
│           ├── graph.py             # LangGraph 워크플로우 정의 및 실행 엔진
│           ├── agents/              # LangGraph 다중 에이전트 시스템
│           │   ├── supervisor.py    # Supervisor Agent (작업 라우팅)
│           │   ├── reading.py       # Reading Tutor Agent
│           │   ├── grammar.py       # Grammar Tutor Agent
│           │   ├── vocabulary.py    # Vocabulary Tutor Agent
│           │   ├── image_processor.py # Image Processor Agent (Vision OCR)
│           │   └── aggregator.py    # Aggregator (결과 통합)
│           ├── prompts.py           # 프롬프트 로더 (파일 읽기 + 변수 주입)
│           ├── prompts/             # 프롬프트 템플릿 (코드와 분리)
│           │   ├── supervisor.md    # Supervisor 라우팅 프롬프트
│           │   ├── reading_tutor.md # 독해 튜터 시스템 프롬프트
│           │   ├── grammar_tutor.md # 문법 튜터 시스템 프롬프트
│           │   ├── vocabulary_tutor.md # 어휘 튜터 시스템 프롬프트
│           │   ├── image_processor.md  # 이미지 처리 프롬프트
│           │   └── level_instructions.yaml # 레벨별 필터링 규칙 (1-5)
│           ├── routers/             # API 라우터
│           │   └── tutor.py         # SSE 스트리밍 라우터 (_stream_graph_events)
│           ├── services/            # 비즈니스 로직 및 유틸리티
│           │   ├── image.py         # 이미지 처리 (OCR 전 처리)
│           │   ├── session.py       # 세션 관리 (메모리 기반)
│           │   └── streaming.py     # SSE 포맷터 (format_vocabulary_error 등)
│           ├── models/              # LLM 클라이언트
│           │   └── llm.py           # LLM 클라이언트 초기화 및 설정
│           └── utils/               # 유틸리티 함수
│               └── markdown_normalizer.py # 마크다운 정규화
│
├── src/                              # Next.js 프론트엔드 (프로젝트 루트)
│   ├── app/                         # App Router (Next.js 15)
│   │   ├── layout.tsx               # 루트 레이아웃 (메타데이터, 전역 스타일)
│   │   ├── page.tsx                 # 홈 페이지 (튜터 인터페이스)
│   │   ├── globals.css              # 전역 CSS 스타일
│   │   └── api/tutor/               # Next.js Route Handlers (API 프록시)
│   │       ├── analyze/route.ts     # 텍스트 분석 프록시
│   │       ├── analyze-image/route.ts # 이미지 분석 프록시
│   │       └── chat/route.ts        # 후속 질문 프록시
│   ├── components/                  # React 컴포넌트
│   │   ├── ui/                      # shadcn/ui 재사용 컴포넌트
│   │   ├── chat/                    # 대화 인터페이스 컴포넌트 (6개)
│   │   │   ├── chat-container.tsx   # 대화 레이아웃
│   │   │   ├── message-list.tsx     # 메시지 목록
│   │   │   ├── user-message.tsx     # 사용자 메시지 UI
│   │   │   ├── tutor-message.tsx    # 튜터 응답 UI (스트리밍)
│   │   │   ├── chat-input.tsx       # 입력 필드
│   │   │   └── image-upload.tsx     # 이미지 업로드 인터페이스
│   │   ├── tutor/                   # 튜터 분석 결과 컴포넌트
│   │   │   ├── tabbed-output.tsx    # 탭 인터페이스 (Reading/Grammar/Vocabulary)
│   │   │   ├── reading-panel.tsx    # 읽기 이해 분석 패널
│   │   │   ├── grammar-panel.tsx    # 문법 분석 패널
│   │   │   └── vocabulary-panel.tsx # 어휘 분석 패널
│   │   ├── layout/                  # 레이아웃 컴포넌트
│   │   │   └── desktop-layout.tsx   # 데스크톱 레이아웃
│   │   ├── mobile/                  # 모바일 컴포넌트
│   │   │   └── analysis-view.tsx    # 분석 결과 뷰
│   │   └── controls/                # 제어 및 설정 컴포넌트
│   │       ├── header.tsx           # 앱 헤더 (제목, 로고)
│   │       └── level-slider.tsx     # 5단계 이해도 슬라이더
│   ├── hooks/                       # React 커스텀 훅
│   │   ├── use-tutor-stream.ts      # SSE 스트리밍 처리 (vocabularyError 상태)
│   │   ├── use-session.ts           # 세션 관리 훅
│   │   └── use-level-config.ts      # 이해도 설정 훅
│   ├── lib/                         # 유틸리티 함수
│   │   ├── api.ts                   # API 클라이언트 함수
│   │   ├── utils.ts                 # 일반 유틸리티 함수
│   │   └── constants.ts             # 상수 정의 (엔드포인트, 레벨 등)
│   └── types/                       # TypeScript 타입 정의
│       ├── tutor.ts                 # 튜터 응답 타입
│       └── chat.ts                  # 대화 관련 타입
│
├── .moai/                           # MoAI-ADK 설정 및 문서
│   ├── config/                      # 프로젝트 설정
│   │   └── sections/
│   │       ├── quality.yaml         # 품질 게이트 설정
│   │       ├── user.yaml            # 사용자 정보
│   │       ├── language.yaml        # 언어 설정
│   │       ├── workflow.yaml        # 워크플로우 설정
│   │       ├── context.yaml         # 컨텍스트 설정
│   │       ├── llm.yaml             # LLM 설정
│   │       └── mx.yaml              # MX 설정
│   ├── specs/                       # SPEC 문서
│   │   ├── SPEC-AUTH-001/
│   │   ├── SPEC-READING-001/
│   │   ├── SPEC-GRAMMAR-001/
│   │   ├── SPEC-VOCAB-001/
│   │   └── ...                      # 기타 SPEC 문서
│   ├── project/                     # 프로젝트 문서
│   │   ├── product.md               # 상품 명세
│   │   ├── structure.md             # 프로젝트 구조
│   │   └── tech.md                  # 기술 스택
│   └── docs/                        # 자동 생성 문서
│
├── .claude/                         # Claude Code 설정
│   ├── agents/                      # 커스텀 에이전트 정의
│   ├── skills/                      # 커스텀 스킬 정의
│   ├── commands/                    # 커스텀 슬래시 명령
│   ├── hooks/                       # 프로젝트 훅
│   └── rules/                       # 프로젝트 규칙
│
├── CLAUDE.md                        # MoAI 실행 지침
├── README.md                        # 프로젝트 개요
├── package.json                     # 프론트엔드 의존성 및 스크립트
├── tsconfig.json                    # TypeScript 설정
├── next.config.ts                   # Next.js 설정
└── .gitignore                       # Git 무시 설정
```

## 주요 디렉토리 설명

### backend/ - FastAPI 백엔드 서버

**목적:** REST API 서버 및 LLM 멀티 에이전트 시스템 구현

**핵심 책임:**
- HTTP 엔드포인트 제공 (텍스트/이미지 분석, 후속 질문)
- LangGraph 멀티 에이전트 오케스트레이션
- SSE 스트리밍을 통한 실시간 응답 전송
- 세션 관리 및 대화 이력 저장
- 이미지 OCR 처리

**주요 파일:**
- `src/main.py`: FastAPI 앱 초기화, 라우터 등록, 미들웨어 설정
- `src/agents/graph.py`: LangGraph 워크플로우 정의 및 에이전트 연결
- `src/api/tutor.py`: 핵심 엔드포인트 구현 (analyze, analyze-image, chat)
- `src/services/streaming.py`: SSE 메시지 포맷팅 및 전송
- `src/agents/prompts/`: 프롬프트 템플릿 디렉토리 (코드 변경 없이 프롬프트 튜닝 가능)

### src/ - Next.js 프론트엔드 (프로젝트 루트)

**목적:** 사용자 인터페이스 및 백엔드 API 통신

**핵심 책임:**
- 반응형 웹 UI 제공
- 사용자 입력 수집 (텍스트/이미지)
- 이해도 단계 설정 (Level 1-5)
- SSE 스트리밍 처리 및 실시간 표시
- 탭 기반 결과 표시 (Reading/Grammar/Vocabulary)
- 후속 질문 입력 및 대화 관리

**주요 파일:**
- `app/page.tsx`: 메인 튜터 인터페이스
- `components/chat/chat-container.tsx`: 대화 레이아웃
- `components/tutor/tabbed-output.tsx`: 분석 결과 탭
- `hooks/use-tutor-stream.ts`: SSE 스트리밍 처리 로직 (vocabularyError 상태)
- `app/api/tutor/analyze/route.ts`: 백엔드 API 프록시

### .moai/ - MoAI-ADK 설정

**목적:** 프로젝트 관리, 문서, 설정

**포함 내용:**
- 품질 게이트 설정 (TRUST 5 프레임워크)
- 프로젝트 명세 및 구조 문서
- SPEC 문서 저장소
- 자동 생성 문서

## 모듈 간 의존성

### Backend 모듈 의존성

```
tutor/main.py
    ├── routers/tutor.py (_stream_graph_events)
    │   └── graph.py
    │       ├── state.py
    │       ├── agents/supervisor.py
    │       ├── agents/reading.py
    │       │   └── prompts/reading_tutor.md
    │       ├── agents/grammar.py
    │       │   └── prompts/grammar_tutor.md
    │       ├── agents/vocabulary.py
    │       │   └── prompts/vocabulary_tutor.md
    │       ├── agents/image_processor.py
    │       │   └── prompts/image_processor.md
    │       └── agents/aggregator.py
    ├── services/streaming.py (SSE 포맷터)
    ├── services/session.py
    ├── services/image.py
    ├── models/llm.py
    └── config.py
```

**흐름:**
1. 사용자 요청이 `api/tutor.py` 엔드포인트에 도착
2. `services/image.py`로 이미지 처리 (필요한 경우)
3. `agents/graph.py`를 통해 멀티 에이전트 시스템 실행
4. `agents/supervisor.py`가 작업 라우팅
5. 각 튜터 에이전트 병렬 실행 (Reading, Grammar, Vocabulary, Image Processor)
6. `agents/aggregator.py`가 결과 수집
7. `services/streaming.py`로 SSE 이벤트 포맷팅 및 전송
8. `services/session.py`에 결과 저장

### Frontend 모듈 의존성

```
app/page.tsx (Main Interface)
    ├── components/chat/chat-container.tsx
    │   ├── components/chat/message-list.tsx
    │   ├── components/chat/user-message.tsx
    │   ├── components/chat/tutor-message.tsx
    │   │   └── hooks/use-tutor-stream.ts (vocabularyError 상태 처리)
    │   ├── components/chat/chat-input.tsx
    │   └── components/chat/image-upload.tsx
    ├── components/tutor/tabbed-output.tsx
    │   ├── components/tutor/reading-panel.tsx
    │   ├── components/tutor/grammar-panel.tsx
    │   └── components/tutor/vocabulary-panel.tsx
    ├── components/controls/level-slider.tsx
    │   └── hooks/use-level-config.ts
    ├── components/controls/header.tsx
    ├── hooks/use-session.ts
    └── lib/api.ts (API Client)
```

**흐름:**
1. 사용자가 `chat-input.tsx`에 텍스트 또는 이미지 입력
2. `use-session.ts`로 세션 ID 관리
3. `lib/api.ts`를 통해 백엔드 API 호출
4. `app/api/tutor/*/route.ts` (프록시)를 거쳐 실제 요청 전송
5. `use-tutor-stream.ts`로 SSE 스트림 수신 및 처리
6. `tutor-message.tsx`에서 실시간 응답 표시
7. `tabbed-output.tsx`에서 최종 분석 결과 표시

## Frontend/Backend 분리

### Backend (FastAPI)

**책임:**
- AI 처리 로직 (LangGraph 멀티 에이전트)
- LLM API 호출 (OpenAI, Anthropic)
- 세션 및 데이터 관리
- SSE 스트림 생성 및 전송

**장점:**
- Python LangGraph 에코시스템 활용
- 복잡한 AI 로직 중앙화
- 보안 (API 키 서버에 숨김)

### Frontend (Next.js)

**책임:**
- 사용자 인터페이스 렌더링
- 사용자 입력 수집
- SSE 스트림 처리 및 UI 업데이트
- 클라이언트 상태 관리 (이해도 단계, 세션)

**장점:**
- 반응형 UI (React 19, Tailwind CSS)
- 빠른 상호작용 (Client Components)
- 배포 간편 (Vercel)

### Next.js Route Handlers (API 프록시)

**목적:** 프론트엔드에서 CORS 문제 방지, 보안 강화

**파일 위치:** `src/app/api/tutor/*/route.ts`

**동작:**
1. 프론트엔드에서 Next.js 라우트 핸들러 호출
2. 라우트 핸들러가 백엔드 FastAPI 호출
3. 백엔드 응답(SSE 스트림)을 프론트엔드로 전달

**예시:**
- `analyze/route.ts`: `POST /api/v1/tutor/analyze` → 텍스트 분석
- `analyze-image/route.ts`: `POST /api/v1/tutor/analyze-image` → 이미지 분석
- `chat/route.ts`: `POST /api/v1/tutor/chat` → 후속 질문

## 핵심 파일 역할

### Backend 핵심 파일

| 파일 | 역할 |
|------|------|
| `src/tutor/state.py` | LangGraph 상태 정의 (메시지, 이해도, 세션 정보) |
| `src/tutor/agents/supervisor.py` | Supervisor Agent (gpt-4o-mini, 작업 라우팅) |
| `src/tutor/agents/reading.py` | Reading Tutor Agent (gpt-4o-mini) |
| `src/tutor/agents/grammar.py` | Grammar Tutor Agent (gpt-4o-mini, 구조화된 출력) |
| `src/tutor/agents/vocabulary.py` | Vocabulary Tutor Agent (gpt-4o-mini) |
| `src/tutor/agents/image_processor.py` | Image Processor Agent (gpt-4o-mini, Vision) |
| `src/tutor/services/streaming.py` | SSE 이벤트 처리 및 포맷팅 |

### Frontend 핵심 파일

| 파일 | 역할 |
|------|------|
| `src/hooks/use-tutor-stream.ts` | SSE 스트림 수신 및 메시지 파싱 |
| `src/hooks/use-session.ts` | 세션 ID 관리 및 로컬스토리지 |
| `src/hooks/use-level-config.ts` | 이해도 단계 설정 및 저장 |
| `src/types/tutor.ts` | ReadingResult, GrammarResult, VocabularyResult 타입 |
| `src/lib/constants.ts` | API 엔드포인트, 레벨 정의 상수 |
