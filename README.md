# AI English Tutor

AI 기반 개인 맞춤형 영어 학습 튜터 - 풀스택 애플리케이션

중학생(13-15세)을 대상으로 고등학교 영어 선행학습을 지원합니다.

## 기술 스택

### 프론트엔드

| 구성 요소 | 버전 | 역할 |
|-----------|------|------|
| Next.js | 15.x | React 프레임워크 (App Router) |
| React | 19.x | UI 라이브러리 |
| TypeScript | 5.9+ | 타입 안전성 |
| Tailwind CSS | 4.x | 스타일링 |
| shadcn/ui | latest | UI 컴포넌트 |
| pnpm | 10.x | 패키지 매니저 |
| Vitest | 3.x | 단위/통합 테스트 |
| Playwright | latest | E2E 테스트 |

### 백엔드

| 구성 요소 | 버전 | 역할 |
|-----------|------|------|
| Python | 3.13+ | 런타임 |
| FastAPI | 0.115+ | 웹 프레임워크 |
| LangGraph | 0.3+ | 에이전트 오케스트레이션 |
| Pydantic | 2.10+ | 데이터 검증 |
| uv | 0.6+ | 패키지 관리자 |

## 프로젝트 구조

```
ai-english-tutor/
├── src/                    # Next.js 프론트엔드
│   ├── app/
│   │   ├── api/tutor/      # API Route Handlers (프록시)
│   │   ├── layout.tsx      # 루트 레이아웃
│   │   ├── page.tsx        # 메인 페이지
│   │   └── globals.css     # 전역 스타일
│   ├── components/
│   │   ├── chat/           # 채팅 컴포넌트 (6개)
│   │   ├── controls/       # 제어 컴포넌트 (Header, LevelSlider)
│   │   ├── tutor/          # 튜터 패널 (TabbedOutput, Reading/Grammar/Vocabulary)
│   │   └── ui/             # shadcn/ui 컴포넌트
│   ├── hooks/              # 커스텀 훅 (useSession, useLevelConfig, useTutorStream)
│   ├── lib/                # 유틸리티 (api.ts, constants.ts, utils.ts)
│   └── types/              # TypeScript 타입 정의
├── backend/                # FastAPI 백엔드
│   ├── src/tutor/
│   │   ├── agents/         # LangGraph 에이전트
│   │   ├── models/         # LLM 모델
│   │   ├── routers/        # API 라우터
│   │   ├── services/       # 비즈니스 로직
│   │   └── prompts/        # 프롬프트 템플릿
│   └── tests/              # 백엔드 테스트
├── .moai/                  # MoAI-ADK 설정
│   ├── specs/              # SPEC 문서
│   └── project/            # 프로젝트 문서
└── package.json
```

## 주요 기능

- **텍스트 분석**: 영어 텍스트 입력 후 독해/문법/어휘 분석
- **이미지 분석**: 교과서 이미지 업로드 후 OCR 기반 분석
- **후속 질문**: 분석 결과에 대한 컨텍스트 기반 대화
- **이해도 조절**: Level 1-5 슬라이더로 분석 깊이 조절
- **실시간 스트리밍**: SSE(Server-Sent Events) 기반 실시간 응답

## 설치 및 실행

### 요구사항

- Node.js 20+
- Python 3.13+
- pnpm 10.x
- uv 패키지 매니저
- OpenAI API 키
- Anthropic API 키

### 프론트엔드 설정

```bash
# 의존성 설치
pnpm install

# 환경 변수 설정
cp .env.local.example .env.local
```

`.env.local` 파일:
```env
BACKEND_URL=http://localhost:8000
```

### 백엔드 설정

```bash
cd backend

# 의존성 설치
uv sync

# 환경 변수 설정
cp .env.example .env
```

`.env` 파일:
```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

### 개발 서버 실행

```bash
# 터미널 1: 백엔드
cd backend
uv run uvicorn src.tutor.main:app --reload

# 터미널 2: 프론트엔드
pnpm dev
```

- 프론트엔드: http://localhost:3000
- 백엔드 API 문서: http://localhost:8000/docs

## 테스트

### 프론트엔드

```bash
# 단위/통합 테스트
pnpm test

# 커버리지 포함
pnpm test:coverage

# 타입 체크
pnpm type-check

# 린트
pnpm lint

# 빌드
pnpm build

# E2E 테스트 (백엔드 실행 필요)
pnpm test:e2e
```

### 백엔드

```bash
cd backend

# 테스트 실행
uv run pytest tests/ -v

# 커버리지 포함
uv run pytest tests/ -v --cov=src/tutor --cov-report=term-missing
```

## API 엔드포인트

### 프론트엔드 → 백엔드 프록시

| 엔드포인트 | 메서드 | 설명 |
|------------|--------|------|
| `/api/tutor/analyze` | POST | 텍스트 분석 (SSE) |
| `/api/tutor/analyze-image` | POST | 이미지 분석 (SSE) |
| `/api/tutor/chat` | POST | 후속 질문 (SSE) |

### 백엔드 직접 접근

| 엔드포인트 | 메서드 | 설명 |
|------------|--------|------|
| `/api/v1/health` | GET | 헬스 체크 |
| `/api/v1/tutor/analyze` | POST | 텍스트 분석 |
| `/api/v1/tutor/analyze-image` | POST | 이미지 분석 |
| `/api/v1/tutor/chat` | POST | 채팅 |

## 품질 지표

### 프론트엔드

- **테스트**: 101개 통과
- **커버리지**: 91.98% (Lines), 86.5% (Branches)
- **TypeScript**: strict mode, 0 에러
- **ESLint**: 0 에러

### 백엔드

- **테스트**: 34개 통과
- **커버리지**: 96% (Lines)
- **Ruff**: 0 에러

## 라이선스

MIT
