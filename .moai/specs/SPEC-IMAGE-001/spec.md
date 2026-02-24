---
id: SPEC-IMAGE-001
version: 2.0.0
status: Completed
created: 2026-02-23
updated: 2026-02-24
author: jw
priority: High
tags: [image-processing, ocr, supervisor, langgraph, pipeline-fix, deployment-incidents]
related_specs: [SPEC-GLM-001, SPEC-OCR-001, SPEC-STREAM-001]
lifecycle: spec-anchored
---

# SPEC-IMAGE-001: 이미지 분석 파이프라인 - 배포 후 버그 수정 이력

## 개요

이미지 업로드 → OCR → 영어 튜터 분석 파이프라인의 완성 명세입니다.
최초 구현 이후 프로덕션 배포 과정에서 발견된 4가지 버그를 3회의 커밋으로 수정하여 안정화되었습니다.

## 환경

- **Runtime**: Python 3.13+, FastAPI backend
- **Workflow Engine**: LangGraph StateGraph with Send() API
- **OCR Service**: OpenAI Vision API (gpt-4o-mini)
- **배포 환경**: Vercel (Frontend) + Railway (Backend)
- **핵심 파일**:
  - `backend/src/tutor/state.py` - TutorState TypedDict
  - `backend/src/tutor/agents/image_processor.py` - OCR + Vision 에이전트
  - `backend/src/tutor/agents/supervisor.py` - Supervisor 에이전트
  - `backend/src/tutor/routers/tutor.py` - FastAPI 라우터 (SSE 스트리밍)
  - `src/app/api/tutor/analyze-image/route.ts` - Next.js 프록시 라우트
  - `src/hooks/use-tutor-stream.ts` - SSE 스트림 처리 훅

---

## 최종 구현 아키텍처

### 이미지 분석 데이터 흐름

```
사용자 이미지 업로드
    |
Next.js /api/tutor/analyze-image (maxDuration=60)
    |
FastAPI /api/v1/tutor/analyze-image
    |
LangGraph StateGraph
    |
supervisor_node (task_type="image_process", input_text="" → SKIP)
    |
route_by_task("image_process")
    |
image_processor_node (OpenAI Vision OCR)
    → returns: {extracted_text, input_text, task_type="analyze"}
    |
route_after_image
    ├── extracted_text 비어있음 → Send("aggregator", state)
    └── extracted_text 있음 → Send("supervisor", new_state)
                                       |
                            supervisor_node (task_type="analyze", input_text=extracted_text)
                                       |
                            route_by_task("analyze")
                                       |
                    ┌──────────────────┼──────────────────┐
                reading_node    grammar_node    vocabulary_node  (병렬)
                    |                |                |
                    └──────────────────┴──────────────────┘
                                       |
                            aggregator_node
                                       |
                            SSE 스트리밍 응답
```

### SSE 하트비트 흐름

```
FastAPI SSE 라우터
    |
heartbeat_producer (5초마다 ": comment\n\n" 전송)
    |
content_producer (실제 LLM 스트리밍)
    |
asyncio.Queue → SSE EventSourceResponse
    |
Vercel 프록시 (10초 idle timeout 방지)
    |
Next.js 클라이언트 (response.ok 검증 후 스트림 읽기)
```

---

## 요구사항

### REQ-IMG-001: OCR 텍스트의 Supervisor 경유 보장

**WHEN** `image_processor_node`가 OCR 추출을 완료하고 `extracted_text`가 비어있지 않으면,
**THEN** 시스템은 `task_type="analyze"`, `input_text=extracted_text`로 `supervisor_node`를 통해 라우팅하여 분석 에이전트에 전달 전 `supervisor_analysis`를 생성한다.

### REQ-IMG-002: 분석 에이전트에서 Supervisor 분석 결과 사용 가능

**WHEN** `supervisor_node`가 `task_type="analyze"`와 비어있지 않은 `input_text`로 재라우팅된 OCR 텍스트를 받으면,
**THEN** 시스템은 문장 분리, 난이도 점수, 학습 포커스 추천이 포함된 `supervisor_analysis` 결과를 생성하여 하위 에이전트에서 사용 가능하게 한다.

### REQ-IMG-003: 빈 OCR 결과 처리

**IF** `image_processor_node`가 빈 `extracted_text`를 반환하면 (OCR 실패 또는 텍스트 없는 이미지),
**THEN** 시스템은 supervisor 재분석과 분석 에이전트를 건너뛰고 `aggregator_node`로 직접 라우팅한다.

### REQ-IMG-004: TutorState 필드 무결성

시스템은 `image_data`와 `mime_type`을 `TutorState`의 선택적(optional) 필드로 **항상** 포함시켜 LangGraph가 `input_state`에서 이 값들을 조용히 삭제하지 않도록 보장한다.

### REQ-IMG-005: 텍스트 입력 시 Supervisor 중복 실행 방지

**WHEN** `task_type`이 `"analyze"`이면 (직접 텍스트 입력, 이미지 아님),
**THEN** 시스템은 `supervisor_node`를 정확히 한 번만 실행하며 재라우팅 없이 기존 흐름을 따른다.

### REQ-IMG-006: Vercel 타임아웃 방지

**WHEN** 이미지 분석 요청이 들어오면,
**THEN** 시스템은 5초 간격의 SSE 하트비트로 프록시 idle timeout을 방지하고, Vercel 함수의 `maxDuration=60`으로 실행 시간을 보장한다.

### REQ-IMG-007: GraphRecursionError 방지

**WHEN** `image_processor_node`가 완료되면,
**THEN** 반환 딕셔너리에 `task_type="analyze"`를 포함하여 그래프 상태를 업데이트하고, `supervisor → image_processor` 무한 사이클을 차단한다.

### REQ-IMG-008: HTTP 응답 상태 검증

**WHEN** 프론트엔드가 이미지 분석 요청을 보내면,
**THEN** `response.ok` 확인 후 SSE 스트림을 읽기 시작하여 HTTP 오류를 사용자에게 명확히 표시한다.

---

## 배포 중 발견된 버그 (Bug Incidents)

### Bug-1: TutorState 필드 누락 (커밋 e624069)

**증상**: 이미지 업로드 후 결과가 항상 비어있음. 로그에 "No image_data provided to image_processor_node" 경고.

**근본 원인**: `TutorState` TypedDict에 `image_data`와 `mime_type` 필드가 없었음. LangGraph의 Send() API는 TypedDict에 정의된 키만 상태로 유지하고 미정의 키는 조용히 삭제함.

**수정**: `backend/src/tutor/state.py`에 두 필드 추가.
```python
image_data: NotRequired[str | None]
mime_type: NotRequired[str | None]
```

**학습**: LangGraph StateGraph는 TypedDict에 정의된 키만 상태 전파를 보장한다.

---

### Bug-2: Vercel 서버리스 타임아웃 (커밋 477f00b)

**증상**: 이미지 분석이 "분석중"에서 10초 후 멈춤. 텍스트 분석은 정상 동작.

**근본 원인**: OpenAI Vision API 처리 시간(25-35초)이 Vercel Hobby 플랜의 함수 실행 제한(10초)을 초과. Vercel 프록시의 idle timeout(10초)과 함수 실행 timeout(10초)을 구분하지 못함.

**수정**:
- `src/app/api/tutor/analyze-image/route.ts`에 `export const maxDuration = 60` 추가
- `src/app/api/tutor/analyze/route.ts`에도 동일하게 추가
- FastAPI 라우터에 5초 간격 SSE 하트비트 추가 (`": comment\n\n"`)

**학습**: Idle timeout(프록시)과 함수 실행 timeout(서버리스 함수)은 다르다. Vercel Hobby 최대 60초.

---

### Bug-3: LangGraph GraphRecursionError (커밋 31f9fb9)

**증상**: 이미지 업로드 후 "Recursion limit of 25 reached" 오류.

**근본 원인**: LangGraph Send()는 대상 노드에 입력 상태를 제공하지만 그래프 전역 상태는 업데이트하지 않음. `image_processor_node`가 반환값에 `task_type`을 포함하지 않아 그래프 상태는 계속 `task_type="image_process"`를 유지 → `route_by_task`가 반복적으로 `image_processor`로 라우팅 → 무한 순환.

**수정**: `image_processor_node`가 `task_type: "analyze"` 반환, 재귀 한도를 50으로 증가.
```python
return {"extracted_text": extracted_text, "input_text": extracted_text, "task_type": "analyze"}
```

**학습**: LangGraph 노드 출력은 그래프 상태를 업데이트한다. Send()의 입력은 해당 노드 실행에만 사용되고 전역 상태에는 반영되지 않는다.

---

### Bug-4: 무증상 오류 (커밋 31f9fb9)

**증상**: UI가 오류 메시지 없이 빈 결과를 표시함.

**근본 원인**: `src/hooks/use-tutor-stream.ts`가 `response.ok` 확인을 하지 않아 HTTP 4xx/5xx 응답을 성공으로 처리 후 빈 스트림 읽기.

**수정**: `response.ok` 확인 블록 추가.
```typescript
if (!response.ok) {
  const errorText = await response.text().catch(() => "");
  let errorMessage = `Analysis failed (${response.status})`;
  // JSON 오류 응답 파싱 시도...
  throw new Error(errorMessage);
}
```

**학습**: 모든 스트리밍 핸들러에서 HTTP 응답 상태를 기본으로 검증한다.

---

## 완료된 커밋 이력

| 커밋 | 날짜 | 내용 |
|------|------|------|
| e624069 | 2026-02-24 01:12 | fix: add image_data and mime_type to TutorState |
| 477f00b | 2026-02-24 01:40 | fix: prevent SSE timeout with heartbeat and maxDuration |
| 31f9fb9 | 2026-02-24 06:36 | fix: resolve GraphRecursionError + response validation |

---

## 테스트 추적

| 요구사항 | 파일 | 테스트명 |
|----------|------|---------|
| REQ-IMG-004 | `backend/tests/unit/test_agents.py` | `test_image_processor_returns_task_type_analyze` |
| REQ-IMG-007 | `backend/tests/unit/test_agents.py` | `test_image_processor_no_data_returns_analyze` |
| REQ-IMG-008 | `src/hooks/use-tutor-stream.ts` | (통합 테스트) |
