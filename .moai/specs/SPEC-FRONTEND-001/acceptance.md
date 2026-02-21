---
id: SPEC-FRONTEND-001
document: acceptance
version: "1.0.0"
---

# SPEC-FRONTEND-001 인수 기준 (acceptance.md)

## 관련 SPEC

- **이 SPEC**: SPEC-FRONTEND-001 (프론트엔드)
- **의존 SPEC**: SPEC-BACKEND-001 (FastAPI 백엔드 API 계약)

---

## 테스트 환경

| 구분 | 단위/통합 테스트 | E2E 테스트 |
|------|----------------|------------|
| 도구 | Vitest + @testing-library/react | Playwright |
| API 모킹 | MSW (Mock Service Worker) | 실제 FastAPI 백엔드 |
| LLM | 모킹 (실제 응답 형태) | 실제 LLM API |
| 실행 조건 | `pnpm test` | 백엔드 실행 중, `pnpm test:e2e` |

---

## Feature 1: 텍스트 입력 및 분석

### 시나리오 1-1: 영어 텍스트 정상 분석

```gherkin
Feature: 텍스트 입력 및 분석

  Scenario: 영어 텍스트 입력 후 3개 탭에 결과 표시
    Given 사용자가 AI English Tutor 메인 페이지에 접속해 있다
    And Level 슬라이더가 Level 3 (중급)으로 설정되어 있다
    When 사용자가 채팅 입력창에 영어 텍스트를 입력한다:
      """
      Climate change is one of the most pressing issues of our time.
      """
    And 사용자가 Enter 키를 누른다
    Then 시스템이 "/api/tutor/analyze" Route Handler에 POST 요청을 전송한다
    And "Reading" 탭에 텍스트 요약과 핵심 포인트가 표시된다
    And "Grammar" 탭에 문법 분석 결과와 점수가 표시된다
    And "Vocabulary" 탭에 어휘 목록과 난이도가 표시된다
    And 채팅 영역에 사용자 메시지 버블이 표시된다
    And 채팅 영역에 튜터 응답 버블이 표시된다
```

**검증 포인트**:
- `ReadingPanel`이 `summary` 텍스트를 렌더링한다
- `GrammarPanel`이 `overallScore`를 표시한다
- `VocabularyPanel`이 단어 목록을 렌더링한다
- `TabbedOutput`의 세 탭이 모두 활성화된다

**테스트 타입**: Vitest (컴포넌트) + Playwright E2E

---

### 시나리오 1-2: SSE 스트리밍 중 실시간 결과 표시

```gherkin
  Scenario: SSE 스트리밍 수신 시 실시간 점진적 표시
    Given 사용자가 영어 텍스트를 제출했다
    When FastAPI 백엔드가 SSE 청크를 순차적으로 전송하기 시작한다:
      | 청크 | 데이터 |
      | 1번  | [READING] Climate change refers to... |
      | 2번  | [GRAMMAR] The sentence structure... |
      | 3번  | [VOCABULARY] pressing: urgent, critical |
      | 4번  | [DONE] |
    Then 각 청크 수신 즉시 해당 탭의 내용이 업데이트된다
    And 스트리밍 중에는 입력창이 비활성화(disabled)된다
    And 스트리밍 중에는 탭 패널에 로딩 인디케이터가 표시된다
    And "[DONE]" 이벤트 수신 후 입력창이 다시 활성화된다
    And 로딩 인디케이터가 사라진다
```

**검증 포인트**:
- `useTutorStream` 훅이 청크를 올바르게 파싱한다
- `isStreaming: true` 상태에서 `ChatInput`이 `disabled` 속성을 가진다
- `[DONE]` 이벤트 후 `isStreaming: false`로 전환된다

**테스트 타입**: Vitest (훅 테스트, MSW로 SSE 모킹)

---

## Feature 2: 이미지 업로드

### 시나리오 2-1: 이미지 파일 선택 후 분석

```gherkin
Feature: 이미지 업로드 및 OCR 분석

  Scenario: 이미지 파일 선택 후 OCR 분석 결과 표시
    Given 사용자가 메인 페이지에 접속해 있다
    When 사용자가 ImageUpload 컴포넌트의 "파일 선택" 버튼을 클릭한다
    And 파일 선택 다이얼로그에서 영어 텍스트가 포함된 JPEG 이미지를 선택한다
    Then 이미지 미리보기가 ImageUpload 컴포넌트에 표시된다
    And 파일명과 크기가 표시된다
    When 사용자가 "분석 시작" 버튼을 클릭한다
    Then 시스템이 "/api/tutor/analyze-image" Route Handler에 multipart/form-data POST 요청을 전송한다
    And OCR로 추출된 텍스트 기반의 분석 결과가 3개 탭에 표시된다
```

**검증 포인트**:
- `ImageUpload` 컴포넌트가 `input[type="file"]`을 올바르게 트리거한다
- `URL.createObjectURL`로 미리보기가 생성된다
- `FormData`에 이미지 파일과 `level` 필드가 포함된다
- Route Handler가 `multipart/form-data`를 올바르게 처리한다

**테스트 타입**: Vitest (컴포넌트) + Playwright E2E

---

### 시나리오 2-2: 드래그&드롭 이미지 업로드

```gherkin
  Scenario: 드래그&드롭으로 이미지 업로드
    Given 사용자가 메인 페이지에 접속해 있다
    When 사용자가 이미지 파일을 ImageUpload 드롭존으로 드래그한다
    Then 드롭존이 하이라이트 스타일(강조 테두리)로 변경된다
    When 사용자가 파일을 드롭존 위에 드롭한다
    Then 이미지 미리보기가 표시된다
    And 파일이 자동으로 분석 요청에 포함된다
```

**검증 포인트**:
- `dragenter` 이벤트에서 드롭존 스타일이 변경된다
- `dragleave` 이벤트에서 드롭존 스타일이 복구된다
- `drop` 이벤트에서 `e.preventDefault()`가 호출된다
- `e.dataTransfer.files[0]`가 올바르게 처리된다

**테스트 타입**: Vitest (컴포넌트, @testing-library/user-event)

---

### 시나리오 2-3: 10MB 초과 이미지 거부

```gherkin
  Scenario: 10MB 초과 이미지 파일 업로드 거부
    Given 사용자가 ImageUpload 컴포넌트에 있다
    When 사용자가 15MB 크기의 이미지 파일을 선택한다
    Then 파일이 업로드 대기열에 추가되지 않는다
    And 토스트 에러 알림이 표시된다: "파일 크기는 10MB를 초과할 수 없습니다"
    And 이미지 미리보기가 표시되지 않는다
```

**검증 포인트**:
- 파일 크기 검사가 `file.size > 10 * 1024 * 1024`로 구현된다
- `toast.error()` (Sonner)가 호출된다
- API 요청이 전송되지 않는다

**테스트 타입**: Vitest (컴포넌트)

---

## Feature 3: 이해도 수준 조절

### 시나리오 3-1: Level 1 선택 시 가장 쉬운 설명

```gherkin
Feature: 이해도 수준 조절

  Scenario: Level 1 선택 시 기초 수준 분석 요청
    Given 사용자가 메인 페이지에 접속해 있다
    And Level 슬라이더가 Level 3으로 설정되어 있다
    When 사용자가 Level 슬라이더를 Level 1 위치로 이동한다
    Then 슬라이더 레이블이 "기초"로 표시된다
    And localStorage의 'tutor_level' 값이 "1"로 저장된다
    When 사용자가 영어 텍스트를 제출한다
    Then API 요청 본문에 "level": 1 이 포함된다
```

**검증 포인트**:
- `useLevelConfig.setLevel(1)` 호출 후 `level === 1`
- `levelLabel === "기초"`
- `localStorage.getItem('tutor_level') === "1"`
- `analyzeText(text, 1)` 호출 시 요청 본문에 `level: 1` 포함

**테스트 타입**: Vitest (훅 테스트, 컴포넌트 테스트)

---

### 시나리오 3-2: Level 변경 후 다음 분석에 반영

```gherkin
  Scenario: Level 변경 후 다음 요청에 새 Level 반영
    Given 사용자가 이전에 Level 2로 분석을 완료했다
    When 사용자가 Level 슬라이더를 Level 5 (심화)로 변경한다
    Then 슬라이더 레이블이 "심화"로 업데이트된다
    When 사용자가 다음 텍스트 분석을 요청한다
    Then API 요청 본문에 "level": 5 가 포함된다
    And Level 5에 적합한 심화 분석 결과가 반환된다
```

**검증 포인트**:
- 레벨 변경 후 다음 API 호출의 `level` 파라미터가 즉시 업데이트된다
- `page.tsx`에서 `level` 상태가 API 호출에 올바르게 전달된다

**테스트 타입**: Vitest (통합 테스트)

---

### 시나리오 3-3: 페이지 새로고침 후 Level 복원

```gherkin
  Scenario: 페이지 새로고침 후 저장된 Level 복원
    Given 사용자가 Level 4를 선택했다
    And 페이지를 새로고침한다
    When 메인 페이지가 로드된다
    Then Level 슬라이더가 Level 4 위치에 있다
    And 슬라이더 레이블이 "고급"으로 표시된다
```

**검증 포인트**:
- `useLevelConfig` 훅이 초기화 시 `localStorage`에서 값을 복원한다
- `localStorage.getItem('tutor_level')` 반환값이 슬라이더 초기값으로 사용된다

**테스트 타입**: Vitest (훅 테스트)

---

## Feature 4: 후속 질문 (Follow-up Chat)

### 시나리오 4-1: 이전 분석 후 후속 질문

```gherkin
Feature: 후속 질문 및 컨텍스트 기반 대화

  Scenario: 분석 완료 후 후속 질문 전송
    Given 사용자가 영어 텍스트 분석을 완료했다
    And 분석 결과가 3개 탭에 표시되어 있다
    When 사용자가 채팅 입력창에 후속 질문을 입력한다:
      """
      'pressing'이라는 단어의 더 자세한 예문을 알려줄 수 있어?
      """
    And 사용자가 Enter 키를 누른다
    Then 시스템이 "/api/tutor/chat" Route Handler에 POST 요청을 전송한다
    And 요청 본문에 세션 ID(`sessionId`)가 포함된다
    And 채팅 영역에 사용자 질문 메시지 버블이 추가된다
    And 튜터의 SSE 스트리밍 응답이 채팅 영역에 실시간으로 표시된다
    And 응답이 이전 분석의 'pressing' 단어 컨텍스트를 반영한다
```

**검증 포인트**:
- `useSession`의 `sessionId`가 채팅 요청에 포함된다
- 채팅 메시지 목록에 `UserMessage`와 `TutorMessage`가 순서대로 추가된다
- `TutorMessage`가 스트리밍 중 점진적으로 내용을 업데이트한다

**테스트 타입**: Vitest (통합 테스트) + Playwright E2E

---

### 시나리오 4-2: 이전 대화 내용 스크롤 확인

```gherkin
  Scenario: 대화 이력 스크롤로 확인
    Given 사용자가 여러 차례 분석과 후속 질문을 수행했다
    And 채팅 영역이 여러 메시지로 가득 차 있다
    When 사용자가 채팅 메시지 목록을 위로 스크롤한다
    Then 이전 사용자 메시지와 튜터 응답이 시간 순서대로 표시된다
    And 각 메시지에 타임스탬프가 표시된다
    When 새 메시지가 수신된다
    Then 메시지 목록이 자동으로 최신 메시지 위치로 스크롤된다
```

**검증 포인트**:
- `MessageList`가 메시지 순서를 올바르게 렌더링한다
- `scrollIntoView` 또는 `scrollTop`이 새 메시지 수신 시 호출된다
- 각 메시지에 `formatTimestamp(timestamp)` 결과가 표시된다

**테스트 타입**: Vitest (컴포넌트 테스트)

---

### 시나리오 4-3: 세션 ID 유지 및 리셋

```gherkin
  Scenario: 세션 ID가 대화 전체에서 동일하게 유지된다
    Given 사용자가 메인 페이지에 처음 접속했다
    Then localStorage에 새로운 UUID 세션 ID가 생성된다
    When 사용자가 분석을 3회, 후속 질문을 2회 수행한다
    Then 모든 API 요청에 동일한 sessionId가 포함된다
    When 사용자가 페이지를 새로고침한다
    Then 동일한 세션 ID가 복원된다
```

**검증 포인트**:
- `useSession` 훅이 UUID v4 형식의 `sessionId`를 생성한다
- 모든 `analyzeText`, `sendChat` 호출이 동일한 `sessionId`를 사용한다
- 새로고침 후 `localStorage.getItem('tutor_session_id')`가 동일한 값을 반환한다

**테스트 타입**: Vitest (훅 테스트)

---

## Feature 5: 반응형 UI

### 시나리오 5-1: 모바일 화면 최적화 레이아웃

```gherkin
Feature: 반응형 디자인 및 다크 모드

  Scenario: 모바일 화면(< 768px)에서 최적화된 레이아웃 표시
    Given 사용자가 모바일 기기(너비 375px)로 메인 페이지에 접속했다
    When 페이지가 로드된다
    Then 모든 컴포넌트가 단일 컬럼 레이아웃으로 표시된다
    And Header, LevelSlider, TabbedOutput, ChatContainer가 세로로 쌓인다
    And 탭 버튼의 텍스트가 잘리지 않는다
    And 입력창이 화면 너비에 맞게 조정된다
    And 가로 스크롤이 발생하지 않는다
```

**검증 포인트**:
- Tailwind CSS `< md:` 브레이크포인트가 올바르게 적용된다
- 뷰포트 너비 375px에서 `overflow-x: hidden`이 유지된다
- 모든 인터랙티브 요소의 터치 타겟이 44x44px 이상이다 (WCAG 2.1 AA)

**테스트 타입**: Playwright E2E (모바일 에뮬레이션)

---

### 시나리오 5-2: 다크 모드 테마 적용

```gherkin
  Scenario: 시스템 다크 모드 설정 시 다크 테마 적용
    Given 사용자의 시스템 설정이 다크 모드로 되어 있다
    When 사용자가 메인 페이지에 접속한다
    Then 페이지 배경이 어두운 색상으로 표시된다
    And 텍스트가 밝은 색상으로 표시된다
    And 컴포넌트 배경이 다크 테마에 맞게 조정된다
    And 모든 텍스트 가독성이 WCAG AA 대비비(4.5:1 이상)를 충족한다
```

**검증 포인트**:
- `prefers-color-scheme: dark` 미디어 쿼리에 Tailwind `dark:` 클래스가 반응한다
- shadcn/ui 컴포넌트의 CSS 변수가 다크 모드에서 올바르게 적용된다
- Lighthouse 접근성 점수가 90점 이상을 유지한다

**테스트 타입**: Playwright E2E (다크 모드 에뮬레이션)

---

### 시나리오 5-3: 태블릿/데스크톱 레이아웃

```gherkin
  Scenario: 데스크톱 화면(>= 1024px)에서 최적화된 레이아웃
    Given 사용자가 데스크톱 브라우저(너비 1440px)로 접속했다
    When 페이지가 로드된다
    Then TabbedOutput과 ChatContainer가 좌우 2컬럼으로 배치된다
    And 최대 너비가 적용되어 과도한 콘텐츠 확장이 방지된다
    And LevelSlider가 Header 영역에 인라인으로 표시된다
```

**테스트 타입**: Playwright E2E (데스크톱 뷰포트)

---

## Feature 6: Full-Stack E2E 시나리오

### 시나리오 6-1: 실제 백엔드 + 실제 LLM 텍스트 분석

```gherkin
Feature: Full-Stack End-to-End 시나리오

  Scenario: 실제 백엔드 연동 텍스트 분석 전체 플로우
    Given FastAPI 백엔드가 http://localhost:8000 에서 실행 중이다
    And 유효한 LLM API 키가 환경 변수에 설정되어 있다
    And Next.js 개발 서버가 http://localhost:3000 에서 실행 중이다
    When 사용자가 http://localhost:3000 에 접속한다
    And 채팅 입력창에 다음 영어 텍스트를 입력한다:
      """
      Photosynthesis is the process by which green plants convert sunlight
      into chemical energy stored in glucose.
      """
    And Enter 키를 누른다
    Then Next.js Route Handler가 FastAPI 백엔드로 요청을 프록시한다
    And SSE 스트리밍이 시작된다
    And 실제 AI가 생성한 Reading 분석 내용이 "Reading" 탭에 표시된다
    And 실제 AI가 생성한 Grammar 분석 내용이 "Grammar" 탭에 표시된다
    And 실제 AI가 생성한 Vocabulary 분석 내용이 "Vocabulary" 탭에 표시된다
    And 스트리밍 완료 후 입력창이 다시 활성화된다
    And 전체 응답 시간이 30초를 초과하지 않는다
```

**검증 포인트**:
- Playwright `waitForResponse('/api/tutor/analyze')`로 프록시 요청 확인
- 각 탭에 비어있지 않은 내용이 표시된다
- 스트리밍 완료 후 `ChatInput`의 `disabled` 속성이 제거된다

**테스트 타입**: Playwright E2E (실제 백엔드)

---

### 시나리오 6-2: 이미지 업로드 → 분석 → 후속 질문 전체 플로우

```gherkin
  Scenario: 이미지 업로드부터 후속 질문까지 전체 사용자 플로우
    Given FastAPI 백엔드와 Next.js 서버가 모두 실행 중이다
    When 사용자가 영어 텍스트가 포함된 교과서 페이지 이미지를 업로드한다
    Then 이미지 미리보기가 표시된다
    When 사용자가 "분석 시작"을 클릭한다
    Then OCR 처리 후 3개 탭에 분석 결과가 표시된다
    When 사용자가 채팅 입력창에 후속 질문을 입력한다:
      """
      이 텍스트에서 가장 어려운 문법 구조를 설명해줘.
      """
    And Enter 키를 누른다
    Then 컨텍스트 기반의 후속 답변이 채팅 영역에 스트리밍된다
    And 답변이 이미지에서 추출된 텍스트 내용과 관련이 있다
    And 전체 플로우가 에러 없이 완료된다
```

**검증 포인트**:
- 이미지 → 분석 → 채팅의 세션 ID가 일관되게 유지된다
- 각 단계에서 에러 토스트가 표시되지 않는다
- 채팅 응답이 이미지 분석 결과와 관련된 내용을 포함한다

**테스트 타입**: Playwright E2E (실제 백엔드)

---

### 시나리오 6-3: Level 슬라이더 변경에 따른 실제 AI 응답 차이 확인

```gherkin
  Scenario: Level에 따른 AI 분석 깊이 차이 확인
    Given FastAPI 백엔드와 Next.js 서버가 실행 중이다
    And 동일한 영어 텍스트 샘플이 준비되어 있다
    When 사용자가 Level 슬라이더를 Level 1로 설정한다
    And 텍스트를 분석한다
    Then "Vocabulary" 탭에 기초 수준의 어휘 설명이 표시된다
    When 사용자가 세션을 리셋하고 Level 슬라이더를 Level 5로 변경한다
    And 동일한 텍스트를 분석한다
    Then "Vocabulary" 탭에 심화 수준의 어휘 분석이 표시된다
    And Level 1 결과보다 더 상세하거나 고급 어휘 설명이 포함된다
```

**테스트 타입**: Playwright E2E (실제 백엔드, 수동 검증 포함)

---

## 품질 게이트 기준 (Quality Gate Criteria)

### 자동 검증 (CI/CD 필수 통과)

| 항목 | 기준 | 도구 |
|------|------|------|
| 코드 커버리지 (라인) | 85% 이상 | Vitest + @vitest/coverage-v8 |
| 코드 커버리지 (브랜치) | 80% 이상 | Vitest + @vitest/coverage-v8 |
| Vitest 단위/통합 테스트 | 전체 통과 | Vitest |
| TypeScript 컴파일 | 타입 에러 0 | `tsc --noEmit` |
| ESLint | 에러 0 | `next lint` |
| Next.js 빌드 | 성공 | `next build` |

### E2E 검증 (백엔드 실행 환경 필수)

| 항목 | 기준 | 도구 |
|------|------|------|
| Playwright E2E (텍스트 분석) | 통과 | Playwright |
| Playwright E2E (이미지 분석) | 통과 | Playwright |
| Playwright E2E (후속 질문) | 통과 | Playwright |
| Playwright E2E (Level 변경) | 통과 | Playwright |

### 수동 검증

| 항목 | 기준 | 도구 |
|------|------|------|
| Lighthouse 접근성 점수 | 90점 이상 | Chrome DevTools |
| Lighthouse 성능 점수 | 80점 이상 | Chrome DevTools |
| LCP (Largest Contentful Paint) | 2.5초 이하 | Lighthouse |
| CLS (Cumulative Layout Shift) | 0.1 이하 | Lighthouse |
| 모바일 레이아웃 (375px) | 가로 스크롤 없음, 터치 타겟 44px+ | 수동 검사 |
| 다크 모드 | 가독성 유지, 대비비 4.5:1 이상 | 수동 검사 |
| 크로스 브라우저 | Chrome, Firefox, Safari 정상 동작 | 수동 검사 |

---

## Definition of Done (완료 기준)

다음 항목이 모두 충족될 때 SPEC-FRONTEND-001이 완료된 것으로 간주합니다:

- [ ] 모든 Vitest 테스트 통과 (`pnpm test`)
- [ ] 코드 커버리지 85% 이상 (`pnpm test:coverage`)
- [ ] TypeScript 에러 0 (`pnpm type-check`)
- [ ] ESLint 에러 0 (`pnpm lint`)
- [ ] Next.js 빌드 성공 (`pnpm build`)
- [ ] Playwright E2E 전체 통과 — 실제 백엔드 연동 (`pnpm test:e2e`)
- [ ] Lighthouse 접근성 점수 90점 이상
- [ ] 모바일(375px) 레이아웃 수동 검증 완료
- [ ] 다크 모드 수동 검증 완료
- [ ] SPEC-BACKEND-001 API 계약과의 타입 일치 확인
