# 기술 스택 (Technology Stack)

## 기술 스택 개요

### Backend 기술 스택

| 카테고리 | 기술 | 버전 | 목적 |
|---------|------|------|------|
| **프레임워크** | FastAPI | 0.115+ | REST API 서버 |
| **런타임** | Python | 3.13+ | 서버 사이드 언어 |
| **서버** | Uvicorn | 0.34+ | ASGI 웹 서버 |
| **AI 오케스트레이션** | LangGraph | 0.3+ | 멀티 에이전트 워크플로우 |
| **LLM 인테그레이션** | langchain-openai | 0.3+ | OpenAI API 통합 |
| **LLM 인테그레이션** | langchain-anthropic | 0.3+ | Anthropic API 통합 |
| **데이터 검증** | Pydantic | 2.10+ | 요청/응답 모델 |
| **패키지 관리** | uv | 0.6+ | Python 패키지 관리 (빠른 속도) |
| **테스트** | pytest | 8.3+ | 단위 및 통합 테스트 |
| **코드 포맷팅** | ruff | 0.9+ | 린팅 및 포맷팅 |

### Frontend 기술 스택

| 카테고리 | 기술 | 버전 | 목적 |
|---------|------|------|------|
| **프레임워크** | Next.js | 15.x | React 풀스택 프레임워크 |
| **라이브러리** | React | 19.x | UI 컴포넌트 |
| **언어** | TypeScript | 5.9+ | 타입 안정성 |
| **스타일링** | Tailwind CSS | 4.x | 유틸리티 기반 CSS |
| **UI 컴포넌트** | shadcn/ui | latest | 재사용 가능 컴포넌트 |
| **패키지 관리** | pnpm | 10.x | 효율적 패키지 관리 |
| **테스트** | Vitest | 3.x | 빠른 단위 테스트 |

### LLM API 서비스

| 서비스 | 모델 | 역할 | 선택 이유 |
|--------|------|------|----------|
| **OpenAI** | GPT-4o-mini | Supervisor Agent (라우팅) | 비용 효율, 높은 지능 |
| **OpenAI** | GPT-4o | Grammar Tutor | 문법 분석 정확도, 구조화된 출력 |
| **Anthropic** | Claude Sonnet | Reading Tutor | 한국어 설명 품질, 장문 분석 |
| **Anthropic** | Claude Sonnet | Image Processor | Vision API 고품질 OCR |
| **Anthropic** | Claude Haiku | Vocabulary Tutor | 속도 & 비용 효율 (같은 품질) |

## Framework 선택 이유

### Backend: FastAPI

**선택 이유:**

1. **성능:** Node.js Express 대비 2-3배 빠른 성능, 높은 처리량 지원
2. **LLM 친화성:** LangChain, LangGraph와 완벽 통합
3. **타입 안정성:** Python 타입 힌팅으로 실행 시간 검증
4. **비동기 지원:** 기본적으로 async/await 지원, 동시 요청 처리 최적화
5. **자동 문서화:** Swagger UI, ReDoc 자동 생성
6. **SSE 스트리밍:** StreamingResponse로 간단한 구현

**대안 검토:**
- **Django:** 너무 무거움, 기본 기능이 과함
- **Flask:** 너무 단순함, SSE 구현 복잡
- **Node.js (Express):** LLM 라이브러리 부족 (Python 생태계 우수)

### Frontend: Next.js 15

**선택 이유:**

1. **App Router:** 최신 라우팅 시스템, Server Components와 Client Components 구분
2. **SSE 클라이언트:** EventSource API 기본 지원
3. **배포 용이:** Vercel 원클릭 배포
4. **TypeScript 기본:** 타입 안정성 확보
5. **성능:** 자동 코드 분할, 이미지 최적화
6. **React 19:** 최신 UI 기능, 향상된 성능

**대안 검토:**
- **Vite + React:** 번들 크기 작지만 배포 설정 복잡
- **Vue 3:** 좋은 대안이나 생태계 작음
- **Svelte:** 번들 크기 작지만 팀 생산성 고려 시 React 우수

### UI Framework: shadcn/ui

**선택 이유:**

1. **커스터마이징:** Tailwind CSS로 완전 커스터마이징 가능
2. **의존성 최소:** 컴포넌트를 직접 프로젝트에 복사 (의존성 최소화)
3. **접근성:** WAI-ARIA 준수
4. **중학생 친화:** 모던하면서도 심플한 디자인

**포함 컴포넌트:**
- Button, Input, Textarea: 기본 입력
- Tabs: Reading/Grammar/Vocabulary 탭
- Slider: 이해도 수준 슬라이더 (1-5)
- Card: 메시지 및 결과 카드
- Toast: 에러 및 알림

### CSS Framework: Tailwind CSS 4.x

**선택 이유:**

1. **성능:** Just-in-time CSS 생성, 불필요한 스타일 제거
2. **반응성:** 모바일 우선 설계
3. **다크 모드:** 기본 지원
4. **개발 속도:** 클래스 명 조합으로 빠른 스타일링

## LLM 모델 할당 전략

### 다중 LLM 사용 이유

다양한 LLM을 작업별로 최적 선택하여 비용과 성능을 균형:

```
Supervisor 라우팅 (저비용)
         ↓
    ┌────┼────┐
    ↓    ↓    ↓
Reading Grammar Vocab + Image
(품질) (정확도) (속도/비용)
```

### Supervisor Agent: GPT-4o-mini

**역할:** 사용자 입력 분석, 작업 라우팅

**선택 이유:**
- **비용 효율:** GPT-4o 대비 10배 저렴
- **충분한 지능:** 라우팅 결정에는 충분한 수준
- **빠른 응답:** 텍스트 분류에 최적화

**할당:**
- 입력: 사용자 질문 또는 분석 텍스트
- 출력: 어떤 에이전트가 필요한지 결정

### Reading Tutor: Claude Sonnet

**역할:** 텍스트의 전체 의미, 요약, 세부 이해 제공

**선택 이유:**
- **한국어 품질:** Claude가 한국어 설명을 더 자연스럽게 생성
- **긴 컨텍스트:** 200K 토큰, 긴 텍스트 분석 가능
- **품질:** GPT-4 대비 높은 문해력 (특히 문학, 뉘앙스)

**할당:**
- 입력: 영어 텍스트
- 출력: 의미 분석, 요약, 주제, 감정 톤

### Grammar Tutor: GPT-4o

**역할:** 문법 분석, 구문 분석, 문장 구조 설명

**선택 이유:**
- **구조화된 출력:** JSON 형식으로 문법 구조 반환 가능
- **정확도:** 영어 문법 분석에 가장 높은 정확도
- **교육적 설명:** 중학생 수준의 명확한 설명

**할당:**
- 입력: 영어 텍스트, 이해도 수준
- 출력: 시제, 태, 문장 구조, 핵심 문법 요소

### Vocabulary Tutor: Claude Haiku

**역할:** 주요 단어 추출, 의미, 용법 제시

**선택 이유:**
- **속도:** Sonnet 대비 4배 빠름
- **비용:** Sonnet 대비 5배 저렴
- **충분한 성능:** 어휘 설명에는 Haiku 충분
- **효율성:** 병렬 처리로 전체 응답 시간 단축

**할당:**
- 입력: 영어 텍스트, 단어 수 (예: 상위 10개)
- 출력: 단어, 의미, 예문, 동의어

### Image Processor: Claude Sonnet (Vision)

**역할:** 이미지에서 텍스트 추출 (OCR)

**선택 이유:**
- **Vision 성능:** Claude Vision이 문맥 이해도 높음
- **정확도:** Tesseract 같은 오픈소스보다 정확
- **유연성:** 필기, 인쇄, 교과서 모두 처리
- **통합:** Image Processor가 Sonnet이면 추가 설정 불필요

**할당:**
- 입력: 이미지 (PNG, JPG)
- 출력: 추출된 영어 텍스트 (Reading → Grammar → Vocabulary 계속)

## 개발 환경 요구사항

### 로컬 개발 환경

**필수 도구:**
- Python 3.13 이상
- Node.js 20.x 이상 (pnpm 설치 필요)
- Git 2.0 이상
- Docker (선택사항, 배포 테스트용)

**환경 변수:**

Backend (.env 파일):
```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

Frontend (.env.local 파일):
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 개발 서버 시작

Backend:
```bash
cd backend
uv sync
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:
```bash
cd frontend
pnpm install
pnpm dev
```

## 빌드 및 배포 설정

### Backend 배포 (Railway)

**Dockerfile:**
```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY pyproject.toml ./
RUN pip install uv && uv sync
COPY src ./src
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Railway 배포 설정:**
- Build Command: `pip install uv && uv sync`
- Start Command: `uvicorn src.main:app --host 0.0.0.0 --port $PORT`
- 환경 변수: OPENAI_API_KEY, ANTHROPIC_API_KEY

**예상 비용:**
- 메모리: 512MB
- 월 실행 시간: 730시간
- 총 비용: ~$5-10/월 (트래픽에 따라)

### Frontend 배포 (Vercel)

**배포 설정:**
1. GitHub에 코드 푸시
2. Vercel에서 프로젝트 선택
3. 자동으로 `next build && next start` 실행
4. 환경 변수 설정:
   - `NEXT_PUBLIC_API_URL`: Railway 백엔드 URL

**배포 크기:**
- 번들 크기: ~150KB (gzip)
- 초기 로드 시간: <2초 (Vercel CDN)
- 비용: 무료 (Hobby 플랜)

### CI/CD 파이프라인

GitHub Actions 워크플로우:

**Backend 테스트:**
```yaml
- run: cd backend && uv sync && pytest --cov=src
- run: cd backend && ruff check src && black --check src
```

**Frontend 테스트:**
```yaml
- run: cd frontend && pnpm install && pnpm test
- run: cd frontend && pnpm build
```

**자동 배포:**
- Main 브랜치 push 시 자동 배포
- 테스트 실패 시 배포 중지

## 핵심 설계 결정

### 1. SSE (Server-Sent Events) 스트리밍

**결정:** REST API + SSE 조합 사용

**이유:**
- **실시간 경험:** 응답을 완성될 때까지 기다리지 않고 실시간 표시
- **단순성:** WebSocket보다 구현이 간단 (단방향)
- **호환성:** 모든 현대 브라우저 지원
- **비용:** WebSocket보다 서버 리소스 적게 사용

**구현:**
- Backend: FastAPI `StreamingResponse` 사용
- Frontend: EventSource API 또는 fetch ReadableStream
- 이벤트 타입: reading_chunk, grammar_chunk, vocabulary_chunk

### 2. LLM Vision을 통한 OCR (Tesseract 미사용)

**결정:** Claude Sonnet Vision API 사용

**이유:**
- **정확도:** Tesseract 대비 90%+ 정확도 (문맥 이해)
- **유연성:** 필기, 인쇄, 다양한 언어 동시 지원
- **통합:** 추가 시스템 설치 불필요
- **비용:** Tesseract 설치/운영 비용 절감

**구현:**
- Image Processor Agent가 base64 인코딩된 이미지 처리
- 추출된 텍스트를 다른 에이전트로 전달

### 3. LangGraph 병렬 dispatch (Send() API)

**결정:** 세 개의 튜터 에이전트 병렬 실행

**이유:**
- **성능:** 순차 처리 3x 시간에서 병렬 처리 1x 시간으로 단축
- **사용자 경험:** 모든 분석 결과를 동시에 표시
- **비용:** 병렬 처리 중 API 호출도 동시에 청구 (비용 절감)

**구현:**
```python
# Supervisor가 세 개의 Send() 호출
graph.add_edge("supervisor", "reading_agent")
graph.add_edge("supervisor", "grammar_agent")
graph.add_edge("supervisor", "vocabulary_agent")
```

### 4. 5단계 이해도 시스템 (5-Level Explanation)

**결정:** 통합 슬라이더로 Level 1-5 선택 (다중 프롬프트 미사용)

**이유:**
- **사용자 경험:** 하나의 슬라이더로 모든 에이전트의 설명 수준 제어
- **비용 효율:** 각 에이전트에 이해도 수준만 전달 (다중 API 호출 불필요)
- **일관성:** 모든 분석 결과가 같은 수준의 설명 제공

**구현:**
- State에 `explanation_level: int (1-5)` 필드
- 각 에이전트 프롬프트에 수준별 지침 포함
- Slider 변경 시 다음 분석부터 적용

### 5. 세션 기반 대화 이력 (인증 미포함)

**결정:** 세션 ID 기반, 메모리 저장소 (MVP)

**이유:**
- **MVP 단순성:** 인증 시스템 불필요
- **개발 속도:** 세션 ID만으로 충분
- **확장성:** 향후 데이터베이스(Redis, PostgreSQL) 추가 용이

**구현:**
- Frontend: localStorage에 sessionId 저장
- Backend: 메모리 딕셔너리에 세션 데이터 저장
- 24시간 자동 만료

**향후 개선:**
- Redis로 이전 (세션 영속성)
- 데이터베이스 추가 (사용자 계정)
- 인증 시스템 (선택사항)

### 6. API 버전 관리

**결정:** `/api/v1/` 프리픽스로 버전 관리

**이유:**
- **하위 호환성:** 새 버전 추가 시 기존 클라이언트 동작 보장
- **명확성:** API 버전이 명확하게 드러남
- **마이그레이션:** 클라이언트 업그레이드 기간 확보

**엔드포인트:**
- v1: POST `/api/v1/tutor/analyze`
- v2: 향후 다른 모델 또는 기능 추가 시 사용

### 7. 프론트엔드 Route Handlers를 통한 API 프록시

**결정:** Next.js Route Handlers로 백엔드 호출 중개

**이유:**
- **CORS 방지:** 클라이언트에서 직접 호출 시 CORS 문제 방지
- **보안:** API 키를 서버에서 관리 (클라이언트에 노출 안 함)
- **인증:** 향후 인증 추가 시 여기서 처리 가능

**구현:**
```typescript
// frontend/src/app/api/tutor/analyze/route.ts
export async function POST(req: Request) {
  const backendUrl = `${process.env.BACKEND_URL}/api/v1/tutor/analyze`;
  // 프론트엔드 요청을 백엔드로 전달
  return fetch(backendUrl, { ...options });
}
```

### 8. 프롬프트 외부화 (Prompt Externalization)

**결정:** 에이전트 시스템 프롬프트를 Python 코드에서 분리하여 별도 파일로 관리

**이유:**
- **빈번한 튜닝:** 튜터 에이전트의 답변 품질 개선을 위해 프롬프트 수정이 자주 발생
- **코드 분리:** 프롬프트 변경 시 Python 코드 수정 불필요 (배포 위험 감소)
- **가독성:** 긴 프롬프트를 Markdown/YAML 파일로 관리하여 편집 용이
- **버전 관리:** Git diff로 프롬프트 변경 이력 명확하게 추적
- **A/B 테스트:** 프롬프트 파일만 교체하여 다른 버전 비교 가능

**파일 구조:**
```
backend/src/agents/prompts/
├── supervisor.md           # Supervisor 라우팅 프롬프트
├── reading_tutor.md        # 독해 튜터 시스템 프롬프트
├── grammar_tutor.md        # 문법 튜터 시스템 프롬프트
├── vocabulary_tutor.md     # 어휘 튜터 시스템 프롬프트
├── image_processor.md      # 이미지 처리 프롬프트
└── level_instructions.yaml # 레벨별 필터링 규칙 (1-5)
```

**구현:**
- `prompts.py`: 프롬프트 로더 (파일 읽기 + Jinja2/f-string 변수 주입)
- 각 `.md` 파일: 에이전트별 시스템 프롬프트 (레벨 플레이스홀더 포함)
- `level_instructions.yaml`: 레벨 1-5별 필터링 규칙 정의

## 성능 최적화 전략

### Backend 성능

- **비동기 처리:** FastAPI의 async 함수로 동시 요청 처리
- **LLM 병렬화:** LangGraph Send() API로 에이전트 병렬 실행
- **캐싱:** 자주 사용되는 분석 결과 인메모리 캐싱 (향후)

### Frontend 성능

- **번들 최적화:** Code splitting으로 초기 로드 최소화
- **이미지 최적화:** Next.js Image 컴포넌트
- **캐싱:** SSE 응답 캐싱 방지 (항상 신선한 결과)

### 네트워크 최적화

- **SSE 스트리밍:** 전체 응답 기다리지 않고 실시간 표시
- **압축:** gzip 압축으로 전송량 50% 감소
- **CDN:** Vercel CDN으로 전 세계 빠른 접근

## 보안 고려사항

### API 보안

- **환경 변수:** OpenAI, Anthropic API 키를 .env에 저장
- **HTTPS:** 모든 통신 암호화
- **속도 제한:** 무차별 대입 공격 방지 (향후)
- **입력 검증:** Pydantic으로 요청 데이터 검증

### 클라이언트 보안

- **XSS 방지:** React 자동 이스케이프, sanitize 라이브러리
- **CSRF 방지:** SameSite 쿠키 설정
- **민감 정보:** API 키 클라이언트에 노출 안 함

## 비용 최적화 전략

### LLM API 비용

**모델별 추정 비용 (1000개 분석 기준):**
- Supervisor (GPT-4o-mini): $0.5
- Reading (Claude Sonnet): $15
- Grammar (GPT-4o): $8
- Vocabulary (Claude Haiku): $2
- Image OCR (Claude Sonnet): $5
- **총 비용: ~$30.50 / 1000 요청 = $0.03/요청**

**월간 예상 비용 (1000 요청/일 기준):**
- LLM: $900/월
- Backend (Railway): $5-10/월
- Frontend (Vercel): 무료
- **총: ~$910/월**

**비용 절감 방안:**
1. Claude Haiku로 간단한 요청 처리
2. 캐싱으로 중복 분석 제거
3. 배치 처리로 API 호출 수 감소
