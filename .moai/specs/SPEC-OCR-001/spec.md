---
id: SPEC-OCR-001
version: 1.0.0
status: Draft
created: 2026-02-23
updated: 2026-02-23
author: jw
priority: High
tags: [ocr, vision-api, cost-optimization, image-processing]
related_specs: [SPEC-IMAGE-001, SPEC-GLM-001]
---

# SPEC-OCR-001: GLM-OCR to OpenAI Vision API 전환

## 1. 개요

현재 이미지 텍스트 추출(OCR)에 사용 중인 GLM-OCR (`layout_parsing` 엔드포인트)를 OpenAI Vision API (`gpt-4o-mini` + `detail:low`)로 교체한다. OCR 이후 Supervisor 파이프라인 흐름은 변경하지 않는다.

### 1.1 배경

- GLM-OCR는 Zhipu AI의 `/api/paas/v4/layout_parsing` 전용 엔드포인트를 사용하며, 별도의 `GLM_API_KEY`가 필요하다.
- GLM-OCR 과금 문제로 서비스 안정성이 보장되지 않는 상황이다.
- OpenAI Vision API는 이미 프로젝트에서 사용 중인 `OPENAI_API_KEY`로 통합 가능하다.
- `gpt-4o-mini` + `detail:low` 조합으로 이미지당 약 $0.00004의 극저비용 OCR이 가능하다.

### 1.2 관련 SPEC

| SPEC ID | 제목 | 관계 |
|---------|------|------|
| SPEC-IMAGE-001 | 이미지 파이프라인 라우팅 수정 | OCR 텍스트 후처리 관련. 본 SPEC과 독립적 관심사 |
| SPEC-GLM-001 | GLM 모델 마이그레이션 | GLM 의존성 제거 방향과 일치. 본 SPEC이 OCR 부분을 담당 |

## 2. 환경 (Environment)

### 2.1 현재 아키텍처

```
Image Upload -> image_processor_node
  -> httpx.AsyncClient.post(GLM_OCR_ENDPOINT)
  -> GLM-OCR /layout_parsing API (GLM_API_KEY 필요)
  -> response.json()["md_results"] -> extracted_text
  -> input_text (supervisor 전달용)
```

### 2.2 대상 아키텍처

```
Image Upload -> image_processor_node
  -> ChatOpenAI(model="gpt-4o-mini", max_tokens=OCR_MAX_TOKENS)
  -> HumanMessage(content=[image_url(detail=OCR_DETAIL) + text(OCR_PROMPT)])
  -> response.content -> extracted_text
  -> input_text (supervisor 전달용)
```

### 2.3 영향 범위

| 파일 | 변경 유형 | 설명 |
|------|-----------|------|
| `backend/src/tutor/config.py` | 수정 | OCR 설정 필드 추가/변경 |
| `backend/src/tutor/agents/image_processor.py` | 교체 | httpx/GLM-OCR -> ChatOpenAI + HumanMessage |
| `backend/tests/unit/test_agents.py` | 수정 | TestImageProcessorAgent mock 교체 |

## 3. 가정 (Assumptions)

- A1: `OPENAI_API_KEY`는 이미 프로젝트에 설정되어 있으며, Vision API 접근 권한이 포함되어 있다.
- A2: `gpt-4o-mini`는 `detail:low` 모드에서 영어 텍스트가 포함된 교육용 이미지(수능/TOEIC 지문 등)의 OCR에 충분한 정확도를 제공한다.
- A3: LangChain `ChatOpenAI`는 `HumanMessage`의 `image_url` 타입을 통해 Vision 입력을 지원한다.
- A4: `detail:low`는 512x512로 리사이즈하여 85 토큰을 소비하며, 교육용 이미지 텍스트 추출에 적합하다.
- A5: 기존 `GLM_API_KEY` 환경변수는 제거하지 않는다 (다른 GLM 기능에서 사용 가능).

## 4. 요구사항 (Requirements)

### REQ-OCR-001: OpenAI Vision API 사용

**WHEN** 사용자가 이미지를 업로드하면 **THEN** 시스템은 `gpt-4o-mini` 모델과 `detail:low` 설정을 사용하여 OpenAI Vision API로 텍스트를 추출해야 한다.

- `ChatOpenAI(model=settings.OCR_MODEL, max_tokens=settings.OCR_MAX_TOKENS)`를 사용한다.
- `HumanMessage`의 `content`에 `image_url` 타입(base64 data URI + `detail` 파라미터)과 `text` 타입(OCR 프롬프트)을 포함한다.
- 기존 `httpx.AsyncClient`와 GLM-OCR 전용 엔드포인트 호출을 제거한다.
- `get_llm()` 팩토리 함수를 사용하지 않고, `image_processor.py` 내에서 직접 `ChatOpenAI` 인스턴스를 생성한다 (Vision 전용 파라미터 필요).

### REQ-OCR-002: GLM_API_KEY 의존성 제거

시스템은 OCR 기능 동작 시 `GLM_API_KEY` 환경변수에 **의존하지 않아야 한다**.

- OCR은 `OPENAI_API_KEY`만으로 동작해야 한다.
- `image_processor.py`에서 `settings.GLM_API_KEY` 참조를 제거한다.
- `config.py`의 `GLM_API_KEY` 필드 자체는 유지한다 (다른 용도 호환성).

### REQ-OCR-003: OCR 설정의 환경변수 기반 관리

시스템은 **항상** 다음 OCR 설정값을 환경변수를 통해 관리해야 한다.

| 설정 | 필드명 | 기본값 | 설명 |
|------|--------|--------|------|
| OCR 모델 | `OCR_MODEL` | `gpt-4o-mini` | 기본값을 `glm-4.6v`에서 변경 |
| OCR 디테일 | `OCR_DETAIL` | `low` | Vision API detail 파라미터 |
| OCR 최대 토큰 | `OCR_MAX_TOKENS` | `2048` | Vision 응답 최대 토큰 수 |

### REQ-OCR-004: 빈 응답 처리

**WHEN** Vision API 응답에서 추출된 텍스트가 비어있으면 **THEN** 시스템은 `RuntimeError`를 발생시켜야 한다.

- 기존 GLM-OCR의 빈 `md_results` 처리와 동일한 동작을 유지한다.
- 에러 메시지: "이미지에서 텍스트를 찾을 수 없습니다. 영어 텍스트가 포함된 이미지를 업로드해 주세요."

### REQ-OCR-005: 테스트 업데이트

**WHEN** OCR 구현이 변경되면 **THEN** `TestImageProcessorAgent` 테스트 클래스가 LangChain ChatOpenAI mock 기반으로 업데이트되어야 한다.

- 기존 `httpx.AsyncClient` mock을 `ChatOpenAI.ainvoke` mock으로 교체한다.
- 텍스트 추출 성공, 빈 응답 처리 시나리오를 커버한다.
- `get_settings` mock을 통해 `OPENAI_API_KEY` 기반 동작을 검증한다.

## 5. 명세 (Specifications)

### 5.1 OCR 프롬프트

```
Extract only the main reading passage text from this image.
Rules:
- Include: Main passage/article text only
- Exclude: Question numbers, answer choices, instructions, headers
- Preserve: Original paragraph structure and line breaks
- Output: Plain text only, no markdown
```

### 5.2 비용 분석

| 방법 | 입력 토큰/이미지 | 출력 토큰/이미지 | 비용/100이미지 |
|------|-----------------|-----------------|---------------|
| gpt-4o-mini + detail:low | 85 | ~200 | ~$0.004 |
| gpt-4o + detail:low | 85 | ~200 | ~$0.36 |
| GLM-OCR (현재) | N/A | N/A | 과금 문제로 불안정 |

### 5.3 에러 처리

| 에러 유형 | 처리 방식 |
|-----------|-----------|
| `OPENAI_API_KEY` 미설정 | `get_settings()` 검증에서 실패 (기존 동작) |
| Vision API 호출 실패 | `RuntimeError` 발생, 사용자 친화적 메시지 |
| 빈 텍스트 응답 | `RuntimeError` 발생 (REQ-OCR-004) |
| 이미지 데이터 없음 | 빈 문자열 반환 (기존 동작 유지) |

## 6. 추적성 (Traceability)

| 요구사항 | 파일 | 테스트 |
|---------|------|--------|
| REQ-OCR-001 | `image_processor.py` | AC-001 |
| REQ-OCR-002 | `image_processor.py`, `config.py` | AC-003 |
| REQ-OCR-003 | `config.py` | AC-004 |
| REQ-OCR-004 | `image_processor.py` | AC-002 |
| REQ-OCR-005 | `test_agents.py` | AC-001, AC-002 |
