# Mobile UI/UX Improvement Plan

## Context

현재 AI English Tutor는 PC에서 최적화된 좌/우 분할 레이아웃을 사용하고 있다. 하지만 모바일에서는 두 컬럼이 수직으로 쌓이면서 UX가 저하된다.

### 핵심 사용 시나리오
- 학생이 핸드폰으로 문제집 사진 촬영/업로드
- 사진의 텍스트는 이미 문제집에 있으므로 원문 표시 불필요
- 오직 해설(Reading, Grammar, Vocabulary)만 보면 됨

### 현재 문제점
1. 모바일에서 입력부와 해설탭이 수직으로 쌓여 스크롤 필요
2. 채팅 메시지 영역이 불필요한 공간 차지
3. 이미지 업로드가 보조 기능처럼 표시됨

---

## Proposed Design: Mobile-First Bottom Tab Layout

### Core Concept
모바일에서는 **하단 탭 네비게이션**으로 명확한 두 가지 모드 전환:
1. **Camera Tab**: 사진 촬영/업로드
2. **Analysis Tab**: 해설 결과 (Reading, Grammar, Vocabulary)

### UI Flow

```
┌─────────────────────────┐
│        Header           │
├─────────────────────────┤
│                         │
│                         │
│    [Current View]       │
│                         │
│                         │
├─────────────────────────┤
│ [Camera]    [Analysis]  │  <- Bottom Tab Navigation
└─────────────────────────┘
```

### Tab 1: Camera (Upload) View
```
┌─────────────────────────┐
│        Header           │
├─────────────────────────┤
│                         │
│    ┌───────────────┐    │
│    │               │    │
│    │   [Camera     │    │
│    │    Icon]      │    │
│    │               │    │
│    │  사진 찍기    │    │
│    │  또는 업로드  │    │
│    └───────────────┘    │
│                         │
│   [난이도: ●●●○○]       │  <- Level Slider (compact)
│                         │
│ ┌─────────────────────┐ │
│ │ 텍스트 직접 입력... │ │  <- Optional text input
│ └─────────────────────┘ │
├─────────────────────────┤
│ [Camera]    [Analysis]  │
└─────────────────────────┘
```

### Tab 2: Analysis View
```
┌─────────────────────────┐
│        Header           │
├─────────────────────────┤
│ [Reading][Grammar][Vocab]│  <- Inner tabs (horizontal scroll)
├─────────────────────────┤
│                         │
│    Analysis Content     │
│    (Markdown rendered)  │
│                         │
│                         │
│                         │
├─────────────────────────┤
│ [Camera]    [Analysis]  │
└─────────────────────────┘
```

---

## Key UX Decisions

### 1. 입력부 구성
- **유지**: 이미지 업로드 + 텍스트 입력 모두 제공
- **이유**: 경우에 따라 텍스트 직접 입력도 필요할 수 있음
- **개선**: 채팅 메시지 히스토리는 제거 (불필요한 공간 절약)
- **레이아웃**: Camera Tab 하단에 텍스트 입력창 배치

### 2. 난이도 조절 위치
- **Camera Tab 하단**에 배치
- Compact slider 형태로 공간 절약
- 분석 전에 난이도 설정 유도

### 3. 자동 화면 전환
- 이미지 업로드 완료 → 자동으로 Analysis Tab 전환
- 분석 완료 시 진동/알림으로 사용자 인지

### 4. Analysis Tab 개선
- 3개 내부 탭 (Reading, Grammar, Vocabulary)은 유지
- 가로 스크롤 가능한 탭 헤더
- 전체 화면 활용한 스크롤 가능한 콘텐츠

---

## Implementation Approach

### Phase 1: Conditional Rendering
```tsx
// page.tsx
const isMobile = useMediaQuery("(max-width: 1024px)");

return isMobile ? (
  <MobileLayout />  // Bottom tab navigation
) : (
  <DesktopLayout /> // Current 2-column layout
);
```

### Phase 2: Mobile Layout Component
새 컴포넌트 생성:
- `src/components/layout/mobile-layout.tsx`
- `src/components/layout/bottom-tabs.tsx`
- `src/components/mobile/camera-view.tsx`
- `src/components/mobile/analysis-view.tsx`

### Phase 3: Camera View Enhancement
- 기본 카메라 앱 연동 (`capture="environment"`)
- 업로드된 이미지 미리보기 (작은 썸네일)
- 난이도 슬라이더 통합

### Phase 4: Auto-switch Logic
```tsx
// 이미지 업로드 시 자동으로 Analysis 탭으로 전환
const handleImageSelect = async (file: File) => {
  // ... upload logic
  setActiveTab('analysis');
};
```

---

## Responsive Breakpoint Strategy

| Breakpoint | Layout |
|------------|--------|
| < 768px (md) | Mobile: Bottom tab navigation |
| 768px - 1024px | Tablet: Option for either layout |
| >= 1024px (lg) | Desktop: Current 2-column layout |

---

## Files to Modify

### Primary Changes
1. `src/app/page.tsx` - Add responsive layout switching
2. `src/components/layout/mobile-layout.tsx` - **New** Mobile-specific layout
3. `src/components/layout/bottom-tabs.tsx` - **New** Bottom tab navigation
4. `src/components/mobile/camera-view.tsx` - **New** Simplified camera/upload
5. `src/components/mobile/analysis-view.tsx` - **New** Full-screen analysis

### Secondary Changes
6. `src/components/chat/image-upload.tsx` - Enhance with camera capture
7. `src/components/controls/level-slider.tsx` - Add compact variant
8. `src/hooks/use-media-query.ts` - **New** Responsive breakpoint hook

---

## Verification Plan

1. **Chrome DevTools**: Test at 375px (iPhone SE), 390px (iPhone 12), 768px (iPad)
2. **Real Device Testing**: Upload photo from phone camera
3. **Flow Testing**:
   - Camera → Upload → Auto-switch to Analysis
   - Tab switching between Camera/Analysis
   - Level adjustment before analysis
   - Long content scroll in Analysis tab

---

## Alternative Considered: Bottom Sheet Pattern

처음 고려한 대안:
- 이미지 업로드를 Bottom Sheet로 표시
- 분석 결과를 메인 화면으로

**기각 이유**:
- 사용자의 주 행동이 "사진 찍기"이므로 1단계여야 함
- Bottom Sheet는 보조 기능에 더 적합

---

## Summary

모바일에서는 **입력(카메라)과 출력(해설)을 명확히 분리**하고, 하단 탭으로 전환하는 방식을 추천한다. 이렇게 하면:

1. 각 화면이 단일 목적에 집중
2. 전체 화면을 효율적으로 활용
3. 학생의 핵심 워크플로우 (사진 → 해설) 최적화
4. 불필요한 채팅 UI 제거로 혼란 감소

---

**Created**: 2026-02-21
**Status**: Planning
