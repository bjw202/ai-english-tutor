---
id: SPEC-UI-001
title: Mobile-First UI/UX Improvement - Implementation Plan
version: 1.0.0
status: draft
created: 2026-02-21
updated: 2026-02-21
author: jw
priority: high
related_spec: SPEC-UI-001/spec.md
---

# SPEC-UI-001: 구현 계획서

## 1. 기술 사양

### 1.1 사용 기술 (기존 의존성만 사용)

| 기술 | 버전 | 역할 |
|------|------|------|
| Next.js | 15.x | App Router, SSR |
| React | 19.x | UI 컴포넌트 |
| TypeScript | 5.9+ | 타입 안전성 |
| Tailwind CSS | 4.x | 반응형 스타일링 |
| shadcn/ui | latest | 기본 UI 컴포넌트 (Tabs, Slider, Button) |

### 1.2 신규 패키지

없음. 모든 기능은 기존 의존성과 웹 표준 API로 구현한다.

### 1.3 핵심 웹 API

- `window.matchMedia()`: 반응형 브레이크포인트 감지
- `MediaQueryList.addEventListener("change")`: 뷰포트 변경 실시간 감지
- HTML5 `capture="environment"` 속성: 모바일 카메라 접근

---

## 2. 구현 단계

### Phase 1: Foundation (기반 구축)

**목표**: `useMediaQuery` hook 생성 및 데스크톱 레이아웃 추출

**Primary Goal**

| 태스크 | 파일 | 설명 |
|--------|------|------|
| T1-1 | `src/hooks/use-media-query.ts` | SSR-safe `useMediaQuery` hook 구현 |
| T1-2 | `src/components/layout/desktop-layout.tsx` | `page.tsx`에서 기존 2-column 레이아웃을 추출하여 DesktopLayout 컴포넌트 생성 |
| T1-3 | `src/app/page.tsx` | `useMediaQuery` 적용, 조건부 렌더링 분기, 로딩 skeleton 추가 |

**기술 세부사항:**

`useMediaQuery` hook 구현:
- 매개변수: `query: string` (예: `"(min-width: 1024px)"`)
- 반환값: `boolean | null` (null = SSR 또는 미마운트)
- `useState(null)` 초기화 -> `useEffect`에서 `matchMedia` 바인딩
- `change` 이벤트 리스너로 실시간 업데이트
- cleanup에서 이벤트 리스너 제거

**의존성**: 없음 (첫 번째 단계)

---

### Phase 2: Mobile Layout Shell (모바일 레이아웃 골격)

**목표**: 모바일 하단 탭 내비게이션 컴포넌트 구현

**Primary Goal**

| 태스크 | 파일 | 설명 |
|--------|------|------|
| T2-1 | `src/components/layout/mobile-layout.tsx` | 하단 탭 내비게이션 + 전체 화면 탭 컨텐츠 레이아웃 |
| T2-2 | `src/components/mobile/analysis-view.tsx` | 분석 결과 전체 화면 뷰 (TabbedOutput wrapper) |

**기술 세부사항:**

MobileLayout 구조:
```
<div class="flex flex-col h-screen">
  <!-- 컨텐츠 영역 (flex-1, overflow-y-auto) -->
  <main class="flex-1 overflow-y-auto">
    {activeTab === "camera" ? <CameraView /> : <AnalysisView />}
  </main>

  <!-- 하단 탭 바 (fixed bottom) -->
  <nav class="flex border-t bg-background" role="tablist">
    <button role="tab" aria-selected="...">카메라/업로드</button>
    <button role="tab" aria-selected="...">분석 결과</button>
  </nav>
</div>
```

AnalysisView:
- `TabbedOutput` 컴포넌트를 전체 화면으로 확장
- 스트리밍 상태 표시 (isStreaming prop)
- 분석 결과 없을 때 안내 메시지

**의존성**: Phase 1 완료 필요

---

### Phase 3: Camera/Upload Enhancement (카메라/업로드 강화)

**목표**: 카메라 촬영 기능 추가, 이미지 업로드 컴포넌트 확장

**Secondary Goal**

| 태스크 | 파일 | 설명 |
|--------|------|------|
| T3-1 | `src/components/chat/image-upload.tsx` | `capture` 속성 지원, `compact` variant prop 추가 |
| T3-2 | `src/components/mobile/camera-view.tsx` | 카메라/업로드 탭 전용 컨텐츠 (카메라 버튼 + 갤러리 버튼 + 프리뷰 + 텍스트 입력) |

**기술 세부사항:**

ImageUpload 확장:
- 새 prop: `variant?: "default" | "compact"`, `enableCapture?: boolean`
- `compact` variant: 버튼만 표시 (Drag & Drop 영역 숨김)
- `enableCapture`: true일 때 별도 카메라 input 렌더링

CameraView 구현:
```
<div class="flex flex-col h-full p-4 space-y-4">
  <!-- 이미지 프리뷰 영역 -->
  {preview ? <img ... /> : <placeholder />}

  <!-- 카메라 + 갤러리 버튼 -->
  <div class="grid grid-cols-2 gap-3">
    <Button size="lg" onClick={openCamera}>카메라 촬영</Button>
    <Button size="lg" variant="outline" onClick={openGallery}>사진 선택</Button>
  </div>

  <!-- LevelSlider compact -->
  <LevelSlider variant="compact" ... />

  <!-- 텍스트 입력 -->
  <ChatInput ... />
</div>
```

**의존성**: Phase 2 완료 필요

---

### Phase 4: LevelSlider Compact (슬라이더 compact 모드)

**목표**: LevelSlider에 인라인 수평 compact variant 추가

**Secondary Goal**

| 태스크 | 파일 | 설명 |
|--------|------|------|
| T4-1 | `src/components/controls/level-slider.tsx` | `variant` prop 추가 (`"default" | "compact"`) |

**기술 세부사항:**

LevelSlider compact variant:
- 한 줄 레이아웃: `[Label: Lv.3] [===|===]`
- `flex items-center gap-3` 적용
- 세부 단계 라벨(기초/초급/중급/고급/심화) 숨김
- 현재 레벨 번호만 표시

**의존성**: 없음 (독립 태스크, Phase 1과 병렬 가능)

---

### Phase 5: Auto-Switch & Integration (자동 전환 및 통합)

**목표**: 이미지 업로드 시 자동 탭 전환, 스트리밍 상태 연동

**Final Goal**

| 태스크 | 파일 | 설명 |
|--------|------|------|
| T5-1 | `src/components/layout/mobile-layout.tsx` | `onImageUpload` 콜백에서 `activeMobileTab`을 `"analysis"`로 전환 |
| T5-2 | `src/app/page.tsx` | 모바일 레이아웃에 스트리밍 상태 및 콜백 연결 |

**기술 세부사항:**

자동 탭 전환 로직:
```typescript
// page.tsx
const handleImageUpload = (file: File) => {
  // 기존 업로드 로직 실행
  processImage(file);
  // 모바일이면 분석 탭으로 전환
  if (isMobile) {
    setActiveMobileTab("analysis");
  }
};
```

**의존성**: Phase 2, 3 완료 필요

---

### Phase 6: Polish & Testing (마무리 및 테스트)

**Optional Goal**

| 태스크 | 파일 | 설명 |
|--------|------|------|
| T6-1 | 전체 | 크로스 디바이스 수동 테스트 (iOS Safari, Android Chrome, Desktop) |
| T6-2 | 전체 | 접근성 검증 (aria 속성, 터치 타겟, 키보드 내비게이션) |
| T6-3 | 전체 | landscape 모드 검증 |
| T6-4 | 전체 | 에지 케이스 검증 (다중 업로드, 뷰포트 리사이즈 중 전환) |

**의존성**: Phase 1-5 전체 완료 필요

---

## 3. 파일별 변경 상세

### 3.1 신규 파일

#### `src/hooks/use-media-query.ts`
- SSR-safe `useMediaQuery(query: string): boolean | null` hook
- `useState(null)` + `useEffect` 패턴으로 hydration 안전성 보장
- `matchMedia("change")` 이벤트로 실시간 반응

#### `src/components/layout/desktop-layout.tsx`
- `page.tsx`에서 기존 2-column 레이아웃 코드 추출
- Props: 기존 page.tsx와 동일한 비즈니스 로직 props 전달
- ChatContainer, ImageUpload, ChatInput, LevelSlider, TabbedOutput 조합

#### `src/components/layout/mobile-layout.tsx`
- 하단 고정 탭 내비게이션 (2탭: 카메라/업로드, 분석)
- `activeMobileTab` 상태 관리
- 전체 화면 컨텐츠 영역
- Props: 비즈니스 로직 + `onTabChange` 콜백

#### `src/components/mobile/camera-view.tsx`
- 카메라 촬영 버튼 (`capture="environment"`)
- 갤러리 선택 버튼 (capture 없음)
- 이미지 프리뷰
- LevelSlider compact
- 텍스트 입력 필드
- Props: `onFileSelect`, `onTextSubmit`, 레벨 관련 props

#### `src/components/mobile/analysis-view.tsx`
- TabbedOutput을 전체 화면으로 감싸는 wrapper
- 스트리밍 로딩 상태 표시
- 분석 결과 없을 때 안내 문구
- Props: TabbedOutput에 전달할 분석 결과 props

### 3.2 수정 파일

#### `src/app/page.tsx`
- `useMediaQuery("(min-width: 1024px)")` 추가
- `isMobile === null`일 때 로딩 skeleton 렌더링
- `isMobile === true`일 때 `<MobileLayout />` 렌더링
- `isMobile === false`일 때 `<DesktopLayout />` 렌더링
- `activeMobileTab` 상태 + 이미지 업로드 시 자동 전환 로직

#### `src/components/chat/image-upload.tsx`
- `variant` prop 추가: `"default" | "compact"`
- `enableCapture` prop 추가: 카메라 캡처용 별도 input 렌더링
- compact variant: 드래그 앤 드롭 영역 없이 버튼만 표시
- 기존 동작은 `variant="default"`로 유지 (하위 호환)

#### `src/components/controls/level-slider.tsx`
- `variant` prop 추가: `"default" | "compact"`
- compact: 한 줄 인라인 레이아웃, 단계 라벨 숨김
- 기존 동작은 `variant="default"`로 유지 (하위 호환)

---

## 4. 리스크 분석 및 대응

### Risk 1: SSR/Hydration 불일치

- **위험도**: High
- **원인**: `useMediaQuery`가 서버와 클라이언트에서 다른 값 반환
- **대응**: 서버에서 `null` 반환 -> 로딩 skeleton 표시 -> 클라이언트 마운트 후 실제 레이아웃 결정
- **검증**: Next.js dev 모드에서 hydration warning 부재 확인

### Risk 2: Camera API 브라우저 호환성

- **위험도**: Medium
- **원인**: `capture="environment"` 속성의 브라우저별 동작 차이
- **대응**: `capture` 속성은 힌트 속성이므로, 미지원 시 일반 파일 선택기 fallback. 일부 Android에서 카메라/갤러리 선택기가 동시에 표시될 수 있으나 기능에 문제 없음
- **검증**: iOS Safari 16+, Android Chrome 100+에서 카메라 실행 확인

### Risk 3: 다중 업로드 시 상태 충돌

- **위험도**: Low
- **원인**: 연속 이미지 업로드 시 이전 분석이 진행 중일 수 있음
- **대응**: 새 이미지 업로드 시 기존 스트리밍 abort (useTutorStream의 기존 abortController 활용). 프리뷰를 새 이미지로 교체
- **검증**: 분석 진행 중 새 이미지 업로드 시 이전 분석 중단 확인

### Risk 4: 뷰포트 리사이즈 중 레이아웃 전환

- **위험도**: Low
- **원인**: 데스크톱에서 창 크기를 줄이면 모바일 레이아웃으로 전환
- **대응**: `useMediaQuery`의 `change` 이벤트 리스너가 실시간 감지. 상태 유실 방지를 위해 비즈니스 로직은 `page.tsx`에서 관리 (레이아웃과 분리)
- **검증**: 브라우저 리사이즈 시 레이아웃 즉시 전환 확인, 분석 결과 유지 확인

### Risk 5: Landscape 모바일

- **위험도**: Low
- **원인**: 가로 모드에서 하단 탭이 화면을 과도하게 차지할 수 있음
- **대응**: 하단 탭 높이 고정 (`h-14`), 컨텐츠 영역 `flex-1 overflow-y-auto`로 스크롤 가능
- **검증**: 모바일 가로 모드에서 컨텐츠 접근성 확인

---

## 5. Phase 의존성 그래프

```
Phase 1 (Foundation)
  |
  v
Phase 2 (Mobile Layout Shell) -----> Phase 5 (Auto-Switch & Integration)
  |                                          |
  v                                          v
Phase 3 (Camera/Upload) ----------------> Phase 6 (Polish & Testing)

Phase 4 (LevelSlider Compact) -- 독립 실행 가능 (Phase 1과 병렬)
```

**병렬 실행 가능**: Phase 1과 Phase 4는 서로 독립적이므로 병렬 진행 가능

---

## 6. 성공 기준

| 기준 | 측정 방법 |
|------|-----------|
| 모바일에서 카메라 촬영 가능 | iOS Safari, Android Chrome에서 카메라 실행 확인 |
| 데스크톱에서 파일 업로드 가능 | 기존 Drag & Drop + 파일 선택 동작 유지 확인 |
| 자동 탭 전환 동작 | 이미지 선택 후 분석 탭 자동 전환 확인 |
| Hydration 오류 없음 | Next.js dev 모드 콘솔에 hydration warning 없음 |
| 기존 기능 회귀 없음 | 데스크톱 레이아웃의 모든 기능 정상 동작 |
