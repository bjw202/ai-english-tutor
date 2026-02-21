---
id: SPEC-FRONTEND-001
version: "1.0.0"
status: draft
created: "2026-02-20"
updated: "2026-02-20"
author: jw
priority: high
depends_on: SPEC-BACKEND-001
---

## HISTORY

| 날짜 | 버전 | 변경 내용 |
|------|------|-----------|
| 2026-02-20 | 1.0.0 | 최초 작성 |

---

# SPEC-FRONTEND-001: AI English Tutor 프론트엔드 애플리케이션

## 1. 환경 (Environment)

### 1.1 기술 스택

| 구분 | 기술 | 버전 |
|------|------|------|
| 프레임워크 | Next.js App Router | 15.x |
| UI 라이브러리 | React | 19.x |
| 언어 | TypeScript | 5.9+ |
| 스타일링 | Tailwind CSS | 4.x |
| 컴포넌트 | shadcn/ui | latest |
| 패키지 매니저 | pnpm | 10.x |
| 단위/통합 테스트 | Vitest | 3.x |
| 컴포넌트 테스트 | @testing-library/react | latest |
| E2E 테스트 | Playwright | latest |
| HTTP 모킹 | MSW (Mock Service Worker) | latest |

### 1.2 백엔드 의존성

- **SPEC-BACKEND-001** 의존: FastAPI 백엔드 API 계약 준수
- 백엔드 URL: `http://localhost:8000` (개발), 환경 변수로 구성
- API 경로 접두사: `/api/v1/tutor/`
- 스트리밍 방식: SSE (Server-Sent Events)

### 1.3 Next.js Route Handler (API 프록시) 구조

프론트엔드는 Next.js Route Handler를 API 프록시로 사용하여 백엔드와 통신합니다:

```
클라이언트 → Next.js Route Handler (/api/tutor/*) → FastAPI (/api/v1/tutor/*)
```

### 1.4 디렉토리 구조

```
src/
├── app/
│   ├── layout.tsx            # 루트 레이아웃
│   ├── page.tsx              # 메인 페이지
│   ├── globals.css           # 전역 스타일
│   └── api/
│       └── tutor/
│           ├── analyze/route.ts
│           ├── analyze-image/route.ts
│           └── chat/route.ts
├── components/
│   ├── ui/                   # shadcn/ui 컴포넌트
│   ├── chat/                 # 채팅 관련 컴포넌트
│   ├── tutor/                # 튜터 패널 컴포넌트
│   └── controls/             # 제어 컴포넌트
├── hooks/                    # 커스텀 React 훅
├── lib/                      # 유틸리티 및 API 클라이언트
└── types/                    # TypeScript 타입 정의
```

---

## 2. 가정 (Assumptions)

| # | 가정 | 근거 | 위험도 |
|---|------|------|--------|
| A1 | Tailwind CSS 4.x와 shadcn/ui가 호환된다 | 공식 문서 기준 (2026-02-20) | 중간 |
| A2 | 브라우저가 `ReadableStream` API를 지원한다 | 모던 브라우저 표준 기능 | 낮음 |
| A3 | 이미지 업로드 크기는 최대 10MB로 제한된다 | 백엔드 API 계약 (SPEC-BACKEND-001) | 낮음 |
| A4 | 사용자는 Chrome 120+, Firefox 120+, Safari 17+ 환경을 사용한다 | 중학생 대상 서비스, 현대적 브라우저 전제 | 낮음 |
| A5 | SSE 스트리밍은 `text/event-stream` MIME 타입을 사용한다 | 백엔드 API 계약 | 낮음 |
| A6 | localStorage가 세션 및 설정 저장에 사용 가능하다 | 브라우저 표준 API | 낮음 |
| A7 | 대상 사용자(중학생)는 한국어 UI를 선호한다 | 제품 요구사항 | 낮음 |

---

## 3. 요구사항 모듈 (Requirements Modules)

### 모듈 M1: 프로젝트 스캐폴딩 및 기반 설정

**M1-R1** (Ubiquitous): The system shall configure Next.js 15 with App Router, TypeScript strict mode (`"strict": true`), and absolute path aliases (`@/*` → `./src/*`).

**M1-R2** (Ubiquitous): The system shall integrate Tailwind CSS 4 with `@import "tailwindcss"` directive in `globals.css`, replacing the v3 `@tailwind` syntax.

**M1-R3** (Ubiquitous): The system shall configure shadcn/ui with `components.json` specifying the `default` style, Tailwind CSS configuration, and RSC (React Server Components) support.

**M1-R4** (Ubiquitous): The system shall define TypeScript path aliases so all internal imports use `@/` prefix instead of relative paths.

**M1-R5** (Unwanted): If `next.config.ts` is not configured, then the system shall not start the development server without proper image domain allowlists and experimental settings.

---

### 모듈 M2: 타입 정의, 상수, API 클라이언트

**M2-R1** (Ubiquitous): The system shall define `ReadingResult`, `GrammarResult`, `VocabularyResult`, and `AnalyzeResponse` types in `src/types/tutor.ts` matching the SPEC-BACKEND-001 API response contract.

**M2-R2** (Ubiquitous): The system shall define `Message`, `ChatSession`, `UserMessage`, and `TutorMessage` types in `src/types/chat.ts` to represent the conversation data model.

**M2-R3** (Ubiquitous): The system shall define API endpoint constants, comprehension level definitions (levels 1–5 with labels), and default application settings in `src/lib/constants.ts`.

**M2-R4** (Ubiquitous): The system shall implement `analyzeText(text: string, level: number): Promise<AnalyzeResponse>` in `src/lib/api.ts` that calls the `/api/tutor/analyze` Route Handler.

**M2-R5** (Ubiquitous): The system shall implement `analyzeImage(file: File, level: number): Promise<AnalyzeResponse>` in `src/lib/api.ts` using `FormData` for multipart upload.

**M2-R6** (Ubiquitous): The system shall implement `sendChat(sessionId: string, message: string, level: number): EventSource | ReadableStream` in `src/lib/api.ts` that establishes an SSE connection to `/api/tutor/chat`.

**M2-R7** (Unwanted): If the API response status is not 2xx, then the system shall throw a typed `ApiError` with `status`, `message`, and `code` fields instead of a generic `Error`.

**M2-R8** (Ubiquitous): The system shall provide a `cn(...inputs)` utility function in `src/lib/utils.ts` combining `clsx` and `tailwind-merge` for conditional class name composition.

---

### 모듈 M3: 커스텀 훅 (Custom Hooks)

**M3-R1** (Ubiquitous): The system shall implement `useTutorStream` hook in `src/hooks/use-tutor-stream.ts` that manages SSE stream connection, parses agent-specific chunks (`reading`, `grammar`, `vocabulary`), and provides `{ data, isStreaming, error, reset }` state.

**M3-R2** (Event-Driven): When an SSE stream chunk is received, the system shall parse the `data` field, identify the agent type from the chunk prefix, and append the content to the corresponding analysis state (`readingChunks`, `grammarChunks`, `vocabularyChunks`).

**M3-R3** (Event-Driven): When an SSE stream emits a `[DONE]` event, the system shall set `isStreaming` to `false` and mark the stream as complete.

**M3-R4** (Unwanted): If an SSE stream error occurs, then the system shall set the `error` state with the error details and set `isStreaming` to `false` without crashing the application.

**M3-R5** (Ubiquitous): The system shall implement `useSession` hook in `src/hooks/use-session.ts` that generates a UUID session ID on first use, persists it to `localStorage`, and provides `{ sessionId, resetSession }`.

**M3-R6** (Ubiquitous): The system shall implement `useLevelConfig` hook in `src/hooks/use-level-config.ts` that manages the comprehension level (1–5), persists to `localStorage` under key `tutor_level`, and provides `{ level, setLevel, levelLabel }`.

**M3-R7** (State-Driven): While the `useTutorStream` hook is in streaming state (`isStreaming: true`), the system shall prevent duplicate stream connections and disable the submit button.

---

### 모듈 M4: UI 컴포넌트

**M4-R1** (Ubiquitous): The system shall install and configure the following shadcn/ui components: `Button`, `Input`, `Textarea`, `Tabs`, `Slider`, `Card`, `Toast` (Sonner).

**M4-R2** (Ubiquitous): The system shall implement `ChatContainer` component (`src/components/chat/chat-container.tsx`) that renders a two-panel layout: a scrollable message list area and a fixed input area at the bottom.

**M4-R3** (Ubiquitous): The system shall implement `MessageList` component (`src/components/chat/message-list.tsx`) that renders a list of messages, auto-scrolls to the latest message, and uses `React.memo` for performance.

**M4-R4** (Ubiquitous): The system shall implement `UserMessage` component (`src/components/chat/user-message.tsx`) that displays user messages in a right-aligned bubble with a distinct background color.

**M4-R5** (Ubiquitous): The system shall implement `TutorMessage` component (`src/components/chat/tutor-message.tsx`) that displays tutor responses in a left-aligned bubble and supports progressive text rendering during streaming.

**M4-R6** (Ubiquitous): The system shall implement `ChatInput` component (`src/components/chat/chat-input.tsx`) that accepts text input, submits on `Enter` key (with `Shift+Enter` for newlines), and disables input during streaming.

**M4-R7** (Ubiquitous): The system shall implement `ImageUpload` component (`src/components/chat/image-upload.tsx`) that supports both drag-and-drop and file picker (`input[type="file"]`) for image upload, with a file preview before submission.

**M4-R8** (Ubiquitous): The system shall implement `TabbedOutput` component (`src/components/tutor/tabbed-output.tsx`) with three tabs (`Reading`, `Grammar`, `Vocabulary`) that displays the corresponding analysis panel content.

**M4-R9** (Ubiquitous): The system shall implement `ReadingPanel`, `GrammarPanel`, and `VocabularyPanel` components in `src/components/tutor/` that display structured analysis results from the backend response.

**M4-R10** (Ubiquitous): The system shall implement `Header` component (`src/components/controls/header.tsx`) displaying the application title and logo.

**M4-R11** (Ubiquitous): The system shall implement `LevelSlider` component (`src/components/controls/level-slider.tsx`) using the shadcn/ui `Slider`, supporting 5 discrete levels, displaying the current level label, and calling `useLevelConfig.setLevel` on change.

**M4-R12** (Event-Driven): When the user drops an image file onto the `ImageUpload` component, the system shall prevent default browser behavior, validate the file type (`image/*`), and display a preview using `URL.createObjectURL`.

**M4-R13** (Unwanted): If the uploaded image file exceeds 10MB, then the system shall display a toast error notification and reject the file without sending it to the server.

**M4-R14** (State-Driven): While the analysis is streaming, the system shall show a loading skeleton or progress indicator within the corresponding `TabbedOutput` panel.

---

### 모듈 M5: Route Handlers, 페이지 구성 및 반응형 디자인

**M5-R1** (Ubiquitous): The system shall implement `app/api/tutor/analyze/route.ts` as a POST Route Handler that proxies requests to the FastAPI backend at `${BACKEND_URL}/api/v1/tutor/analyze` and streams the SSE response back to the client.

**M5-R2** (Ubiquitous): The system shall implement `app/api/tutor/analyze-image/route.ts` as a POST Route Handler that proxies `multipart/form-data` requests to `${BACKEND_URL}/api/v1/tutor/analyze-image`.

**M5-R3** (Ubiquitous): The system shall implement `app/api/tutor/chat/route.ts` as a POST Route Handler that proxies chat requests to `${BACKEND_URL}/api/v1/tutor/chat` and streams the SSE response.

**M5-R4** (Ubiquitous): The system shall implement `app/layout.tsx` with root metadata (title: "AI English Tutor", description in Korean), global font loading (Geist Sans), and Toaster provider.

**M5-R5** (Ubiquitous): The system shall implement `app/page.tsx` as the main tutor interface, composing `Header`, `LevelSlider`, `TabbedOutput`, `ChatContainer`, and `ImageUpload` components with shared state via hooks.

**M5-R6** (Ubiquitous): The system shall apply responsive design using Tailwind CSS breakpoints: mobile-first single-column layout (`< 768px`), tablet two-column layout (`md:`), and desktop optimized layout (`lg:`).

**M5-R7** (Optional): Where the user's system preference is dark mode (`prefers-color-scheme: dark`), the system shall apply the dark theme using Tailwind CSS `dark:` variant classes.

**M5-R8** (Event-Driven): When the backend `BACKEND_URL` environment variable is not set, the system shall fall back to `http://localhost:8000` and log a warning to the console.

**M5-R9** (Unwanted): If a Route Handler receives an upstream error from the FastAPI backend, then the system shall return a structured JSON error response with the upstream status code and error message.

---

## 4. 트레이서빌리티 (Traceability)

| 요구사항 ID | 구현 파일 | 테스트 파일 |
|-------------|-----------|-------------|
| M1-R1 ~ M1-R5 | `next.config.ts`, `tsconfig.json` | `tests/config/` |
| M2-R1 ~ M2-R2 | `src/types/tutor.ts`, `src/types/chat.ts` | `src/types/__tests__/` |
| M2-R3 | `src/lib/constants.ts` | — |
| M2-R4 ~ M2-R8 | `src/lib/api.ts`, `src/lib/utils.ts` | `src/lib/__tests__/` |
| M3-R1 ~ M3-R7 | `src/hooks/use-tutor-stream.ts`, `src/hooks/use-session.ts`, `src/hooks/use-level-config.ts` | `src/hooks/__tests__/` |
| M4-R1 ~ M4-R14 | `src/components/chat/`, `src/components/tutor/`, `src/components/controls/` | `src/components/__tests__/` |
| M5-R1 ~ M5-R9 | `src/app/api/tutor/`, `src/app/layout.tsx`, `src/app/page.tsx` | `tests/e2e/`, `src/app/__tests__/` |

---

## 5. 제약 사항 (Constraints)

- **성능**: 첫 화면 로딩(LCP) 2.5초 이하
- **접근성**: Lighthouse 접근성 점수 90점 이상 (WCAG 2.1 AA 기준)
- **브라우저**: Chrome 120+, Firefox 120+, Safari 17+ 지원
- **이미지 크기**: 업로드 파일 최대 10MB
- **SSE 타임아웃**: 스트림 연결 최대 60초
- **TypeScript**: `strict: true` 모드, 타입 에러 0
- **ESLint**: 에러 0 (Next.js 기본 규칙 + custom)
- **테스트 커버리지**: 85% 이상 (Vitest)
