---
id: SPEC-FRONTEND-001
document: plan
version: "1.0.0"
---

# SPEC-FRONTEND-001 구현 계획 (plan.md)

## 관련 SPEC

- **이 SPEC**: SPEC-FRONTEND-001 (프론트엔드)
- **의존 SPEC**: SPEC-BACKEND-001 (FastAPI 백엔드 API 계약)

---

## 1. 태스크 분해 (Task Decomposition)

### T1: 프로젝트 스캐폴딩

**범위**: Next.js 15 프로젝트 초기화, 모든 개발 의존성 설치, 설정 파일 구성

**구현 파일**:
- `next.config.ts` — Next.js 설정 (이미지 도메인, 실험적 기능)
- `tsconfig.json` — strict 모드, 절대 경로 (`@/*`)
- `components.json` — shadcn/ui 설정
- `.env.local` — 환경 변수 (`NEXT_PUBLIC_API_BASE_URL`, `BACKEND_URL`)
- `vitest.config.ts` — Vitest 설정 (jsdom, coverage)
- `playwright.config.ts` — Playwright E2E 설정

**핵심 명령어**:
```bash
pnpm create next-app@latest ai-english-tutor \
  --typescript --tailwind --app --src-dir --import-alias "@/*"

pnpm add clsx tailwind-merge
pnpm add -D vitest @vitest/coverage-v8 jsdom @testing-library/react \
  @testing-library/user-event @testing-library/jest-dom msw playwright
```

**의존성**: 없음 (시작 태스크)

---

### T2: 타입 정의 및 상수

**범위**: 모든 TypeScript 타입과 상수 정의 — SPEC-BACKEND-001 API 계약과 일치

**구현 파일**:
- `src/types/tutor.ts`
  - `ReadingResult`: `{ summary: string; keyPoints: string[]; comprehensionLevel: number }`
  - `GrammarResult`: `{ issues: GrammarIssue[]; overallScore: number; suggestions: string[] }`
  - `VocabularyResult`: `{ words: VocabularyWord[]; difficultyLevel: number }`
  - `AnalyzeResponse`: `{ reading: ReadingResult; grammar: GrammarResult; vocabulary: VocabularyResult; sessionId: string }`
- `src/types/chat.ts`
  - `UserMessage`: `{ id: string; role: 'user'; content: string; timestamp: Date }`
  - `TutorMessage`: `{ id: string; role: 'tutor'; content: string; timestamp: Date; isStreaming?: boolean }`
  - `Message`: `UserMessage | TutorMessage`
  - `ChatSession`: `{ sessionId: string; messages: Message[] }`
- `src/lib/constants.ts`
  - `API_ENDPOINTS`: Route Handler 경로 (`/api/tutor/analyze`, `/api/tutor/chat`, 등)
  - `LEVEL_DEFINITIONS`: 레벨 1–5 (label, description 포함)
  - `DEFAULT_SETTINGS`: 기본 레벨 = 3, 최대 파일 크기 = 10MB

**의존성**: T1 완료 후

---

### T3: API 클라이언트 및 유틸리티

**범위**: 백엔드 통신 레이어 구현 (SSE 포함), 유틸리티 함수

**구현 파일**:
- `src/lib/utils.ts`
  ```ts
  export function cn(...inputs: ClassValue[]): string  // clsx + tailwind-merge
  export function formatTimestamp(date: Date): string
  export function generateId(): string  // crypto.randomUUID()
  ```
- `src/lib/api.ts`
  ```ts
  export async function analyzeText(text: string, level: number): Promise<Response>
  export async function analyzeImage(file: File, level: number): Promise<Response>
  export async function sendChat(
    sessionId: string, message: string, level: number
  ): Promise<Response>
  // 내부: fetchWithSSE() — ReadableStream을 반환하는 공통 SSE 헬퍼
  ```

**SSE 구현 전략**:
```ts
// fetch API ReadableStream 활용
const response = await fetch('/api/tutor/analyze', { method: 'POST', body });
const reader = response.body!.getReader();
const decoder = new TextDecoder();
// while loop으로 청크 파싱
```

**의존성**: T2 완료 후

---

### T4: 커스텀 훅

**범위**: 애플리케이션 상태 관리를 위한 세 가지 커스텀 훅

**구현 파일**:

**`src/hooks/use-tutor-stream.ts`**:
```ts
interface TutorStreamState {
  readingContent: string;
  grammarContent: string;
  vocabularyContent: string;
  isStreaming: boolean;
  error: Error | null;
}
export function useTutorStream(): {
  state: TutorStreamState;
  startStream: (fetchFn: () => Promise<Response>) => void;
  reset: () => void;
}
```

청크 파싱 로직:
- `[READING]` 접두사 → `readingContent`에 추가
- `[GRAMMAR]` 접두사 → `grammarContent`에 추가
- `[VOCABULARY]` 접두사 → `vocabularyContent`에 추가
- `[DONE]` → `isStreaming: false`

**`src/hooks/use-session.ts`**:
```ts
export function useSession(): {
  sessionId: string;
  resetSession: () => void;
}
// localStorage key: 'tutor_session_id'
// 없으면 crypto.randomUUID() 생성 후 저장
```

**`src/hooks/use-level-config.ts`**:
```ts
export function useLevelConfig(): {
  level: number;          // 1–5
  setLevel: (n: number) => void;
  levelLabel: string;     // 예: "기초", "초급", "중급", "고급", "심화"
}
// localStorage key: 'tutor_level', 기본값: 3
```

**의존성**: T3 완료 후

---

### T5: shadcn/ui 설치 및 Chat 컴포넌트

**범위**: shadcn/ui 컴포넌트 설치 + Chat 관련 컴포넌트 6개 구현

**shadcn/ui 설치**:
```bash
pnpm dlx shadcn@latest add button input textarea tabs slider card sonner
```

**구현 파일**:
- `src/components/chat/chat-container.tsx` — 레이아웃: 상단 스크롤 영역 + 하단 고정 입력
- `src/components/chat/message-list.tsx` — 메시지 목록, 자동 스크롤, `React.memo`
- `src/components/chat/user-message.tsx` — 우측 정렬 사용자 버블
- `src/components/chat/tutor-message.tsx` — 좌측 정렬 튜터 버블 + 스트리밍 커서
- `src/components/chat/chat-input.tsx` — `Textarea` 기반 입력, Enter 전송
- `src/components/chat/image-upload.tsx` — 드래그&드롭, 파일 선택, 미리보기

**의존성**: T1 완료 후 (T3, T4와 병렬 가능)

---

### T6: Tutor 패널 및 Controls 컴포넌트

**범위**: 분석 결과 표시 패널 + 헤더/슬라이더

**구현 파일**:
- `src/components/tutor/tabbed-output.tsx`
  - shadcn/ui `Tabs` 사용
  - 탭: Reading / Grammar / Vocabulary
  - 스트리밍 중 스켈레톤 로딩 표시
- `src/components/tutor/reading-panel.tsx`
  - `summary` 섹션, `keyPoints` 목록, `comprehensionLevel` 배지
- `src/components/tutor/grammar-panel.tsx`
  - `issues` 목록 (issue, type, suggestion), `overallScore` 게이지
- `src/components/tutor/vocabulary-panel.tsx`
  - `words` 표 (단어, 뜻, 예문), `difficultyLevel` 표시
- `src/components/controls/header.tsx`
  - 앱 로고 + 제목 "AI English Tutor"
- `src/components/controls/level-slider.tsx`
  - shadcn/ui `Slider` (min=1, max=5, step=1)
  - 현재 레벨 라벨 표시

**의존성**: T5 완료 후 (T4와 병렬 가능)

---

### T7: Route Handlers 및 페이지 구성

**범위**: API 프록시 Route Handler 3개 + 루트 레이아웃 + 메인 페이지

**구현 파일**:

**`src/app/api/tutor/analyze/route.ts`**:
```ts
export async function POST(request: NextRequest): Promise<Response> {
  // 요청을 백엔드로 전달 (SSE 스트리밍)
  const backendRes = await fetch(`${BACKEND_URL}/api/v1/tutor/analyze`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: await request.text(),
  });
  return new Response(backendRes.body, {
    headers: { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache' },
  });
}
```

**`src/app/api/tutor/analyze-image/route.ts`**:
- `FormData` 그대로 전달 (multipart)

**`src/app/api/tutor/chat/route.ts`**:
- SSE 스트리밍 프록시 (analyze와 동일 패턴)

**`src/app/layout.tsx`**:
```tsx
export const metadata: Metadata = {
  title: 'AI English Tutor',
  description: 'AI 기반 개인 맞춤형 영어 학습 튜터',
};
```

**`src/app/page.tsx`**:
- 모든 컴포넌트 조합
- `useTutorStream`, `useSession`, `useLevelConfig` 훅 사용
- 레이아웃: Header → LevelSlider → TabbedOutput + ChatContainer (메인 영역)

**의존성**: T4 + T6 완료 후

---

### T8: Full-Stack E2E 테스트 (Playwright)

**범위**: 실제 백엔드 + 실제 LLM API를 사용하는 End-to-End 테스트

**테스트 파일 구조**:
```
tests/
├── e2e/
│   ├── text-analysis.spec.ts    # 텍스트 입력 → 분석 결과
│   ├── image-analysis.spec.ts   # 이미지 업로드 → OCR → 분석
│   ├── chat-followup.spec.ts    # 후속 질문 → 컨텍스트 기반 답변
│   └── level-change.spec.ts     # 레벨 슬라이더 → 다른 설명 깊이
└── fixtures/
    ├── sample-text.txt
    └── sample-image.jpg
```

**E2E 시나리오**:
1. 텍스트 입력 → SSE 스트리밍 → 3개 탭 분석 결과 표시
2. 이미지 업로드 → OCR → 분석 결과 탭 표시
3. 분석 완료 후 → 후속 질문 → 컨텍스트 기반 답변
4. Level 슬라이더 변경 → 다음 분석에 반영

**전제 조건**:
- FastAPI 백엔드 실행 중 (`http://localhost:8000`)
- 유효한 LLM API 키 설정 (`.env.test.local`)
- `playwright.config.ts`에 `webServer` 설정

**의존성**: T7 완료 후 + SPEC-BACKEND-001 구현 완료

---

## 2. 의존성 그래프 (Dependency Graph)

```
T1 (스캐폴딩)
├── T2 (타입 & 상수)
│   └── T3 (API 클라이언트)
│       └── T4 (커스텀 훅)
│           └── T7 (Route Handlers & 페이지) ──┐
└── T5 (shadcn/ui & Chat 컴포넌트)              │
    └── T6 (Tutor 패널 & Controls)             │
        └── T7 ────────────────────────────────┘
                                                └── T8 (E2E 테스트)
                                                     + SPEC-BACKEND-001
```

**병렬 실행 가능**:
- T3 / T5: T2 완료 후 병렬 실행 가능
- T4 / T6: T3 완료 후, T5 완료 후 각각 병렬 실행 가능

---

## 3. 기술 사양 (Technology Specifications)

### 핵심 의존성 버전

```jsonc
{
  "dependencies": {
    "next": "^15.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "typescript": "^5.9.0",
    "tailwindcss": "^4.0.0",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.5.4"
  },
  "devDependencies": {
    "vitest": "^3.0.0",
    "@vitest/coverage-v8": "^3.0.0",
    "jsdom": "^26.0.0",
    "@testing-library/react": "^16.0.0",
    "@testing-library/user-event": "^14.5.2",
    "@testing-library/jest-dom": "^6.6.3",
    "msw": "^2.7.0",
    "playwright": "^1.50.0",
    "@playwright/test": "^1.50.0"
  }
}
```

### shadcn/ui 컴포넌트 목록

| 컴포넌트 | 사용 위치 |
|----------|-----------|
| `Button` | `ChatInput`, `ImageUpload` |
| `Input` | — |
| `Textarea` | `ChatInput` |
| `Tabs`, `TabsList`, `TabsTrigger`, `TabsContent` | `TabbedOutput` |
| `Slider` | `LevelSlider` |
| `Card`, `CardContent`, `CardHeader` | 패널 컴포넌트 |
| `Sonner` (Toast) | 에러 알림 |

### 환경 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `BACKEND_URL` | `http://localhost:8000` | FastAPI 백엔드 URL (서버 사이드 전용) |
| `NEXT_PUBLIC_API_BASE_URL` | `/api/tutor` | 클라이언트 사이드 API 기본 경로 |

---

## 4. 리스크 분석 (Risk Analysis)

| 리스크 | 가능성 | 영향도 | 대응 전략 |
|--------|--------|--------|-----------|
| Tailwind CSS 4 + shadcn/ui 호환성 이슈 | 중간 | 중간 | 최신 공식 문서 확인, 필요시 CSS 변수 직접 정의, shadcn/ui v4 마이그레이션 가이드 참조 |
| SSE 클라이언트 파싱 복잡성 | 중간 | 높음 | `fetch` API의 `ReadableStream` 활용, 청크 단위 파싱 유닛 테스트 작성 |
| 이미지 업로드 드래그&드롭 UX | 낮음 | 낮음 | 파일 선택 방식 이중 지원, `dragenter`/`dragleave` 시각 피드백 |
| 반응형 레이아웃 복잡성 | 낮음 | 중간 | 모바일 우선 설계, Tailwind `md:`/`lg:` breakpoint 체계적 적용 |
| E2E 테스트 불안정성 (Flakiness) | 중간 | 중간 | Playwright `waitForSelector`, `waitForResponse` 적극 활용, 실제 LLM 응답 시간 고려한 타임아웃 설정 |
| Next.js 15 + React 19 호환성 | 낮음 | 높음 | 공식 지원 조합 사용, `use client` 지시어 적절한 경계 설정 |

---

## 5. 개발 방법론 (Development Methodology)

**방법론**: TDD (RED-GREEN-REFACTOR)

모든 구현 코드가 신규이므로 TDD 방법론을 전면 적용합니다.

### 사이클 예시: `useTutorStream` 훅

```
RED: 테스트 작성
  - 초기 상태 검증 테스트 작성 (실패 확인)
  - SSE 청크 파싱 테스트 작성 (실패 확인)
  - 에러 핸들링 테스트 작성 (실패 확인)

GREEN: 최소 구현
  - 테스트를 통과하는 최소한의 코드 작성

REFACTOR: 코드 개선
  - 중복 제거, 가독성 향상
  - 타입 안전성 강화
  - 테스트가 여전히 통과하는지 확인
```

---

## 6. 테스트 전략 (Test Strategy)

### 단위/통합 테스트 (Vitest + Testing Library)

**컴포넌트 테스트**:
```ts
// 실제 분석 결과 형태의 mock 데이터 사용
const mockReadingResult: ReadingResult = {
  summary: "The text discusses climate change and its effects...",
  keyPoints: ["Global temperatures are rising", "Human activities are main cause"],
  comprehensionLevel: 3,
};
```

**훅 테스트**:
```ts
// renderHook + 실제 SSE 이벤트 데이터로 테스트
const { result } = renderHook(() => useTutorStream());
// MSW로 SSE 스트림 모킹
```

**Route Handler 테스트**:
```ts
// Next.js 테스트 헬퍼 (testApiHandler 또는 fetch 직접 호출)
```

### E2E 테스트 (Playwright + 실제 백엔드)

| 시나리오 | 검증 포인트 |
|----------|-------------|
| 텍스트 입력 → 3탭 분석 | SSE 스트리밍 후 모든 탭에 실제 분석 내용 표시 |
| 이미지 업로드 → OCR → 분석 | 이미지 처리 후 텍스트 추출 결과 분석 탭 표시 |
| 후속 질문 → 컨텍스트 답변 | 이전 분석 컨텍스트를 반영한 답변 수신 |
| Level 변경 → 다른 깊이 설명 | Level 1 vs Level 5 분석 결과 차이 확인 |

**MSW (Mock Service Worker)**: 단위/통합 테스트에서 Route Handler 모킹

### 커버리지 목표

| 측정 항목 | 목표 |
|-----------|------|
| 라인 커버리지 | 85% 이상 |
| 브랜치 커버리지 | 80% 이상 |
| TypeScript 타입 에러 | 0 |
| ESLint 에러 | 0 |
| Playwright E2E | 전체 통과 |
| Lighthouse 접근성 | 90점 이상 |

---

## 7. 우선순위 기반 마일스톤 (Priority-Based Milestones)

### Priority High (핵심 기능)

- T1: 프로젝트 스캐폴딩 완료
- T2: 타입 정의 및 상수 완료
- T3: API 클라이언트 (SSE 포함) 완료
- T4: 커스텀 훅 3종 완료 (Vitest 테스트 포함)
- T5: Chat 컴포넌트 완료

### Priority Medium (핵심 UI)

- T6: Tutor 패널 및 Controls 완료
- T7: Route Handlers 및 메인 페이지 통합 완료

### Priority Low (품질 보증)

- T8: Full-Stack E2E 테스트 완료 (SPEC-BACKEND-001 구현 완료 후)

---

## 8. Definition of Done

각 태스크의 완료 기준:

- [ ] 모든 구현 파일 작성 완료
- [ ] Vitest 테스트 작성 및 통과 (커버리지 85% 이상)
- [ ] TypeScript 컴파일 에러 0
- [ ] ESLint 에러 0
- [ ] `pnpm build` 성공
- [ ] T7 이후: `pnpm dev` 로컬 실행 및 수동 검증
- [ ] T8: Playwright E2E 전체 통과 (실제 백엔드 연동)
