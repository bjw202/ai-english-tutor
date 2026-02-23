---
id: SPEC-OCR-001
type: plan
version: 1.0.0
created: 2026-02-23
updated: 2026-02-23
---

# SPEC-OCR-001: 구현 계획

## 1. 개요

GLM-OCR에서 OpenAI Vision API로의 전환을 3개 태스크로 분리하여 순차적으로 구현한다.

## 2. 마일스톤

### Primary Goal: config.py + image_processor.py 교체

핵심 구현 변경. OCR 엔진을 GLM-OCR에서 OpenAI Vision으로 전환한다.

### Secondary Goal: 테스트 업데이트

기존 TestImageProcessorAgent의 mock 구조를 LangChain 기반으로 교체한다.

### Final Goal: 통합 검증

전체 이미지 업로드 -> OCR -> Supervisor 파이프라인 동작 확인.

## 3. 태스크 상세

### Task 1: config.py 수정

**우선순위**: Primary Goal
**의존성**: 없음

변경 사항:
1. `OCR_MODEL` 기본값을 `"glm-4.6v"`에서 `"gpt-4o-mini"`로 변경
2. `OCR_DETAIL: str = "low"` 필드 추가 (Vision API detail 파라미터)
3. `OCR_MAX_TOKENS: int = 2048` 필드 추가 (Vision 응답 최대 토큰)
4. `OCR_MODEL` 주석을 Vision API 용도로 업데이트

영향 받는 파일:
- `backend/src/tutor/config.py` (수정)

참고:
- `GLM_API_KEY` 필드는 제거하지 않는다 (다른 GLM 기능 호환성 유지)
- 기존 환경변수 오버라이드 패턴(`SettingsConfigDict`)을 그대로 활용

### Task 2: image_processor.py 교체

**우선순위**: Primary Goal
**의존성**: Task 1 (config.py의 새 설정값 사용)

변경 사항:
1. `httpx` import 제거
2. `langchain_openai.ChatOpenAI` 및 `langchain_core.messages.HumanMessage` import 추가
3. `GLM_OCR_ENDPOINT`, `GLM_OCR_MODEL` 상수 제거
4. `OCR_PROMPT` 상수 추가 (텍스트 추출 전용 프롬프트)
5. `image_processor_node` 함수 본문 교체:
   - `ChatOpenAI` 인스턴스 생성 (`model=settings.OCR_MODEL`, `max_tokens=settings.OCR_MAX_TOKENS`)
   - `HumanMessage` 구성 (`image_url` + `text` content 배열)
   - `await llm.ainvoke([message])` 호출
   - `response.content.strip()` 으로 텍스트 추출
6. `settings.GLM_API_KEY` 참조 제거
7. 에러 처리 패턴 유지 (빈 텍스트 -> RuntimeError, 일반 예외 -> RuntimeError)
8. `httpx.HTTPStatusError` 처리를 일반 예외 처리로 대체
9. 기존 `@MX:NOTE` 태그를 새 구현에 맞게 업데이트

영향 받는 파일:
- `backend/src/tutor/agents/image_processor.py` (교체)

기술적 접근:
```python
# 새 구현 핵심 구조
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

llm = ChatOpenAI(
    model=settings.OCR_MODEL,
    max_tokens=settings.OCR_MAX_TOKENS,
    api_key=settings.OPENAI_API_KEY,
)
message = HumanMessage(content=[
    {"type": "image_url", "image_url": {
        "url": f"data:{mime_type};base64,{image_data}",
        "detail": settings.OCR_DETAIL,
    }},
    {"type": "text", "text": OCR_PROMPT},
])
response = await llm.ainvoke([message])
extracted_text = response.content.strip()
```

### Task 3: test_agents.py 업데이트

**우선순위**: Secondary Goal
**의존성**: Task 2 (새 image_processor 구현에 대한 테스트)

변경 사항:
1. `TestImageProcessorAgent` 클래스 내 테스트 메서드 교체
2. `httpx.AsyncClient` mock 제거
3. `ChatOpenAI` mock 추가 (`ainvoke` 반환값 mock)
4. 기존 테스트 시나리오 유지:
   - `test_image_processor_extracts_text`: 성공 케이스 (response.content로 텍스트 추출)
   - `test_image_processor_handles_no_text_found`: 빈 응답 케이스 (RuntimeError 발생)
5. mock 구조 변경:
   - `patch("tutor.agents.image_processor.ChatOpenAI")` 사용
   - `mock_llm.ainvoke.return_value` = `MagicMock(content="extracted text")`

영향 받는 파일:
- `backend/tests/unit/test_agents.py` (수정 - TestImageProcessorAgent 클래스)

## 4. 의존성 그래프

```
Task 1 (config.py) --> Task 2 (image_processor.py) --> Task 3 (test_agents.py)
```

모든 태스크는 순차 실행이 필요하다. Task 2는 Task 1의 새 설정 필드를 사용하고, Task 3는 Task 2의 새 구현을 테스트한다.

## 5. 리스크 분석

### Risk 1: OCR 텍스트 품질 변화

- **설명**: `detail:low`는 512x512 리사이즈를 수행하며, 고해상도 이미지의 작은 텍스트를 놓칠 수 있다.
- **영향**: 수능/TOEIC 지문 이미지에서 텍스트 추출 정확도 저하 가능성
- **완화**: `OCR_DETAIL` 환경변수로 `high`로 전환 가능 (비용 증가 트레이드오프). 실제 테스트 이미지로 정확도 검증 필요.

### Risk 2: API 응답 형식 차이

- **설명**: GLM-OCR는 `md_results` (마크다운 형식)를 반환했으나, Vision API는 자유 형식 텍스트를 반환한다.
- **영향**: 하류 에이전트(Supervisor, Reading 등)가 마크다운 포맷에 의존하는 경우 문제 가능성
- **완화**: OCR 프롬프트에서 "Plain text only, no markdown" 지시로 일관된 출력 보장. Supervisor는 텍스트 내용만 분석하므로 포맷 의존성 낮음.

### Risk 3: 비용 예측 불확실성

- **설명**: `detail:low` 기준 이미지당 ~$0.00004로 극저비용이나, 출력 토큰은 이미지 복잡도에 따라 변동 가능.
- **영향**: 예상보다 높은 출력 토큰 소비
- **완화**: `OCR_MAX_TOKENS=2048`로 상한 제한. 모니터링 후 조정 가능.

## 6. 마이그레이션 노트

- `GLM_API_KEY` 환경변수는 `.env`에서 제거할 필요 없음 (config.py에서 `Optional`로 유지)
- 기존 `httpx` 패키지는 프로젝트의 다른 부분에서 사용하지 않는다면 `pyproject.toml`에서 제거 가능 (별도 확인 필요)
- `OCR_MODEL` 환경변수를 명시적으로 설정하지 않은 기존 배포 환경은 자동으로 `gpt-4o-mini`로 전환됨

## 7. 추적성

| 태스크 | 요구사항 | 수용 기준 |
|--------|---------|-----------|
| Task 1 | REQ-OCR-003 | AC-004 |
| Task 2 | REQ-OCR-001, REQ-OCR-002, REQ-OCR-004 | AC-001, AC-002, AC-003 |
| Task 3 | REQ-OCR-005 | AC-001, AC-002 |
