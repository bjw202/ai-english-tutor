---
id: SPEC-UI-001
title: Mobile-First UI/UX Improvement with Cross-Platform Support
version: 1.0.0
status: draft
created: 2026-02-21
updated: 2026-02-21
author: jw
priority: high
tags: [mobile, responsive, camera, ui-ux, cross-platform]
related_specs: [SPEC-FRONTEND-001]
---

# SPEC-UI-001: Mobile-First UI/UX 개선 및 크로스 플랫폼 지원

## HISTORY

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|-----------|
| 1.0.0 | 2026-02-21 | jw | 초기 SPEC 작성 |

---

## 1. Environment (환경)

### 1.1 현재 시스템 상태

- **프레임워크**: Next.js 15, React 19, TypeScript 5.9+
- **스타일링**: Tailwind CSS 4.x, shadcn/ui
- **현재 레이아웃**: PC 최적화 2-column grid (`grid-cols-1 lg:grid-cols-2`)
  - 왼쪽: ChatContainer (MessageList + ImageUpload + ChatInput)
  - 오른쪽: LevelSlider + TabbedOutput (Reading/Grammar/Vocabulary)
- **이미지 업로드**: 파일 선택 + Drag & Drop 방식만 지원
- **모바일 대응**: CSS grid 단순 스택 (1-column) - 전용 모바일 UI 없음

### 1.2 기술 제약사항

- 신규 npm 패키지 추가 금지 (기존 의존성만 사용)
- 백엔드 변경 없음 (프론트엔드 전용 SPEC)
- SSR/Hydration 안전성 보장 필수 (Next.js App Router)

### 1.3 대상 디바이스

- **모바일**: iOS Safari 16+, Android Chrome 100+ (뷰포트 < 1024px)
- **데스크톱**: Chrome, Firefox, Safari, Edge 최신 2개 버전 (뷰포트 >= 1024px)

---

## 2. Assumptions (가정)

### 2.1 기술적 가정

- HTML5 `capture="environment"` 속성은 모바일 브라우저에서 카메라 앱을 실행하며, 데스크톱에서는 무시되어 파일 선택기가 열린다 (graceful degradation)
- `window.matchMedia` API는 모든 대상 브라우저에서 지원된다
- SSR 환경에서 `window` 객체에 접근할 수 없으므로, `useMediaQuery` hook은 서버에서 `null`을 반환해야 한다
- Tailwind CSS의 `lg:` 브레이크포인트(1024px)가 모바일/데스크톱 분기점으로 적합하다

### 2.2 사용자 행동 가정

- 모바일 사용자의 주요 사용 시나리오는 교재/시험지를 카메라로 촬영하여 즉시 분석하는 것이다
- 모바일 사용자는 채팅 히스토리보다 최신 분석 결과에 더 관심이 있다
- 이미지 업로드 후 사용자는 즉시 분석 결과를 보기 원한다 (자동 탭 전환)
- 데스크톱 사용자는 기존 2-column 레이아웃에 익숙하다

### 2.3 비즈니스 가정

- 대상 사용자(중학생)의 70% 이상이 모바일 디바이스를 주로 사용한다
- 카메라 촬영 기능이 앱의 핵심 가치 제안(Value Proposition) 중 하나이다

---

## 3. Requirements (요구사항)

### REQ-UI-001: 반응형 레이아웃 감지 (Ubiquitous)

시스템은 **항상** 사용자의 뷰포트 크기를 감지하여 모바일(< 1024px) 또는 데스크톱(>= 1024px) 레이아웃을 자동으로 적용해야 한다.

- `useMediaQuery` 커스텀 hook을 통해 브레이크포인트 감지
- SSR에서는 `null` 반환 후 클라이언트 hydration 시 실제 값 결정
- hydration 불일치 방지를 위해 초기 로딩 상태(skeleton) 표시

### REQ-UI-002: 모바일 하단 탭 내비게이션 (State-Driven)

**IF** 뷰포트가 모바일(< 1024px)이면 **THEN** 하단 탭 내비게이션을 표시하고, 전체 화면 탭 컨텐츠로 전환해야 한다.

- 탭 구성:
  - **카메라/업로드 탭**: 카메라 촬영 버튼(primary) + 갤러리/파일 선택 버튼(secondary) + 이미지 프리뷰 + LevelSlider(compact) + 텍스트 입력
  - **분석 탭**: TabbedOutput (Reading/Grammar/Vocabulary) 전체 화면 표시
- 탭 간 전환은 애니메이션 없이 즉시 렌더링
- 채팅 메시지 히스토리는 모바일에서 표시하지 않음

### REQ-UI-003: 카메라 촬영 지원 (Event-Driven)

**WHEN** 모바일 사용자가 카메라 버튼을 터치하면 **THEN** 디바이스 카메라가 실행되어 이미지를 촬영할 수 있어야 한다.

- HTML5 `<input type="file" accept="image/*" capture="environment" />` 사용
- 촬영 완료 시 이미지 프리뷰 표시
- 기존 파일 유효성 검증(크기 제한 10MB, 이미지 타입) 유지

### REQ-UI-004: 파일 선택 업로드 지원 (Event-Driven)

**WHEN** 사용자가 갤러리/파일 선택 버튼을 클릭하면 **THEN** 디바이스의 파일 선택기가 열려 이미지를 선택할 수 있어야 한다.

- 모바일: `capture` 속성 없는 별도 `<input type="file" accept="image/*" />` 사용
- 데스크톱: 기존 Drag & Drop + 파일 선택 방식 유지
- 두 플랫폼 모두에서 동일한 파일 유효성 검증 적용

### REQ-UI-005: 이미지 업로드 후 자동 탭 전환 (Event-Driven)

**WHEN** 모바일에서 이미지가 선택/촬영되면 **THEN** 자동으로 분석 탭으로 전환되어야 한다.

- 이미지 선택 즉시 탭 전환 (분석 완료 대기 불필요)
- 분석 중 로딩 상태를 분석 탭에서 표시
- 사용자가 수동으로 카메라/업로드 탭으로 되돌아갈 수 있어야 함

### REQ-UI-006: 데스크톱 레이아웃 유지 (State-Driven)

**IF** 뷰포트가 데스크톱(>= 1024px)이면 **THEN** 기존 2-column 레이아웃을 유지해야 한다.

- 왼쪽 컬럼: ChatContainer (MessageList + ImageUpload + ChatInput)
- 오른쪽 컬럼: LevelSlider + TabbedOutput
- 이미지 업로드 영역의 시각적 강조 개선 (선택사항)

### REQ-UI-007: LevelSlider compact 모드 (State-Driven)

**IF** 모바일 레이아웃이면 **THEN** LevelSlider를 인라인 수평 compact 모드로 표시해야 한다.

- 수평 배치: 라벨 + 슬라이더를 한 줄에 표시
- 세부 단계 라벨(기초/초급/중급/고급/심화) 숨김
- 현재 레벨 값만 표시

### REQ-UI-008: Hydration 불일치 방지 (Unwanted Behavior)

시스템은 SSR과 클라이언트 렌더링 간 hydration 불일치를 **발생시키지 않아야 한다**.

- `useMediaQuery`가 서버에서 `null`을 반환하는 동안 로딩 skeleton 표시
- 조건부 렌더링은 클라이언트에서만 수행
- `useEffect`를 통해 마운트 후 미디어 쿼리 값 결정

### REQ-UI-009: 접근성 지원 (Optional Feature)

**가능하면** 모바일 UI에서 다음 접근성 기능을 제공해야 한다.

- 하단 탭에 `aria-label` 및 `role="tablist"` 적용
- 카메라/업로드 버튼에 적절한 `aria-label` 제공
- 키보드 탭 네비게이션 지원
- 최소 터치 타겟 크기 44x44px 유지

---

## 4. Specifications (세부 사양)

### 4.1 컴포넌트 아키텍처

```
page.tsx (비즈니스 로직 유지)
  |-- useMediaQuery() --> isMobile: boolean | null
  |
  |-- if isMobile === null --> <LoadingSkeleton />
  |-- if isMobile === true --> <MobileLayout />
  |     |-- <MobileTabNavigation>
  |     |     |-- Camera/Upload Tab
  |     |     |     |-- <CameraView />
  |     |     |     |     |-- Camera button (capture="environment")
  |     |     |     |     |-- Gallery button (no capture)
  |     |     |     |     |-- Image preview
  |     |     |     |     |-- <LevelSlider variant="compact" />
  |     |     |     |     |-- Text input
  |     |     |-- Analysis Tab
  |     |           |-- <AnalysisView />
  |     |                 |-- <TabbedOutput /> (full screen)
  |
  |-- if isMobile === false --> <DesktopLayout />
        |-- Left Column
        |     |-- <ChatContainer />
        |     |     |-- <MessageList />
        |     |     |-- <ImageUpload />
        |     |     |-- <ChatInput />
        |-- Right Column
              |-- <LevelSlider />
              |-- <TabbedOutput />
```

### 4.2 파일 구조

**신규 파일 (5개):**

| 파일 경로 | 역할 |
|-----------|------|
| `src/hooks/use-media-query.ts` | SSR-safe 반응형 브레이크포인트 hook |
| `src/components/layout/mobile-layout.tsx` | 모바일 하단 탭 내비게이션 레이아웃 |
| `src/components/layout/desktop-layout.tsx` | 기존 2-column 레이아웃 추출 |
| `src/components/mobile/camera-view.tsx` | 카메라/업로드 탭 컨텐츠 |
| `src/components/mobile/analysis-view.tsx` | 전체 화면 분석 탭 컨텐츠 |

**수정 파일 (3개):**

| 파일 경로 | 변경 내용 |
|-----------|-----------|
| `src/app/page.tsx` | 반응형 레이아웃 스위칭 로직 추가 |
| `src/components/chat/image-upload.tsx` | `capture` 속성 지원 + `compact` variant 추가 |
| `src/components/controls/level-slider.tsx` | `compact` variant 추가 (인라인 수평 모드) |

### 4.3 반응형 전략

- **브레이크포인트**: 1024px (Tailwind `lg` 기준)
- **감지 방식**: `window.matchMedia("(min-width: 1024px)")` + `change` 이벤트 리스너
- **SSR 안전**: 서버에서 `null`, 클라이언트 마운트 후 실제 값 설정
- **조건부 렌더링**: `isMobile ? <MobileLayout /> : <DesktopLayout />`

### 4.4 카메라/업로드 전략

- **카메라 (모바일)**: `<input type="file" accept="image/*" capture="environment" />`
  - 모바일에서 후면 카메라 직접 실행
  - 데스크톱에서는 `capture` 속성이 무시됨 (graceful degradation)
- **갤러리/파일**: `<input type="file" accept="image/*" />` (capture 없음)
  - 모바일: 사진 라이브러리 열기
  - 데스크톱: 파일 탐색기 열기
- **모바일 UI**: 카메라 버튼(primary, 크게) + 갤러리 버튼(secondary, 작게)
- **데스크톱 UI**: 기존 Drag & Drop 영역 유지

### 4.5 상태 관리

- `page.tsx`의 기존 hook 유지: `useTutorStream`, `useSession`, `useLevelConfig`
- 신규 상태:
  - `isMobile: boolean | null` (useMediaQuery)
  - `activeMobileTab: "camera" | "analysis"` (모바일 탭 상태)
- 이미지 업로드 시 `activeMobileTab`을 `"analysis"`로 자동 전환

### 4.6 Traceability (추적성)

| 요구사항 ID | 구현 파일 | 테스트 시나리오 |
|------------|-----------|----------------|
| REQ-UI-001 | `use-media-query.ts`, `page.tsx` | ACC-UI-001, ACC-UI-007 |
| REQ-UI-002 | `mobile-layout.tsx` | ACC-UI-002 |
| REQ-UI-003 | `camera-view.tsx`, `image-upload.tsx` | ACC-UI-003 |
| REQ-UI-004 | `image-upload.tsx`, `camera-view.tsx` | ACC-UI-004 |
| REQ-UI-005 | `mobile-layout.tsx`, `camera-view.tsx` | ACC-UI-005 |
| REQ-UI-006 | `desktop-layout.tsx`, `page.tsx` | ACC-UI-006 |
| REQ-UI-007 | `level-slider.tsx` | ACC-UI-008 |
| REQ-UI-008 | `use-media-query.ts`, `page.tsx` | ACC-UI-007 |
| REQ-UI-009 | `mobile-layout.tsx`, `camera-view.tsx` | ACC-UI-009 |
