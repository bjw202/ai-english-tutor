---
id: SPEC-OCR-001
type: acceptance
version: 1.0.0
created: 2026-02-23
updated: 2026-02-23
---

# SPEC-OCR-001: 수용 기준

## AC-001: 이미지에서 텍스트 추출 성공

**요구사항**: REQ-OCR-001, REQ-OCR-005

```gherkin
Scenario: OpenAI Vision API를 통한 이미지 텍스트 추출
  Given 사용자가 영어 텍스트가 포함된 이미지를 업로드한다
  And image_data에 유효한 base64 인코딩 이미지가 포함되어 있다
  And OPENAI_API_KEY가 설정되어 있다
  When image_processor_node가 호출된다
  Then ChatOpenAI(model="gpt-4o-mini")를 사용하여 Vision API를 호출한다
  And HumanMessage에 image_url(detail="low")과 OCR 프롬프트가 포함된다
  And response.content에서 추출된 텍스트가 extracted_text로 반환된다
  And input_text에 동일한 텍스트가 설정된다 (supervisor 전달용)
```

**검증 방법**:
- 단위 테스트: `ChatOpenAI.ainvoke` mock을 통한 반환값 검증
- mock 응답의 `content` 속성에서 텍스트 추출 확인
- `extracted_text`와 `input_text`가 동일한 값인지 검증

---

## AC-002: 빈 이미지 처리 (RuntimeError 발생)

**요구사항**: REQ-OCR-004, REQ-OCR-005

```gherkin
Scenario: 텍스트가 없는 이미지에서 RuntimeError 발생
  Given 사용자가 텍스트가 없는 이미지를 업로드한다
  And image_data에 유효한 base64 인코딩 이미지가 포함되어 있다
  When image_processor_node가 호출된다
  And Vision API 응답의 content가 빈 문자열이다
  Then RuntimeError가 발생한다
  And 에러 메시지에 "이미지에서 텍스트를 찾을 수 없습니다"가 포함된다
```

**검증 방법**:
- 단위 테스트: `ChatOpenAI.ainvoke` mock의 `content`를 빈 문자열로 설정
- `pytest.raises(RuntimeError, match="이미지에서 텍스트를 찾을 수 없습니다")` 검증

---

## AC-003: GLM_API_KEY 없이 동작

**요구사항**: REQ-OCR-002

```gherkin
Scenario: OPENAI_API_KEY만으로 OCR 동작
  Given GLM_API_KEY 환경변수가 설정되지 않았다
  And OPENAI_API_KEY 환경변수가 설정되어 있다
  And image_data에 유효한 base64 인코딩 이미지가 포함되어 있다
  When image_processor_node가 호출된다
  Then 정상적으로 텍스트를 추출한다
  And GLM_API_KEY 검증 로직이 실행되지 않는다
```

**검증 방법**:
- 코드 리뷰: `image_processor.py`에서 `settings.GLM_API_KEY` 참조 없음 확인
- 단위 테스트: `get_settings` mock에서 `GLM_API_KEY=None`으로 설정해도 정상 동작 검증

---

## AC-004: 설정값 환경변수 오버라이드 가능

**요구사항**: REQ-OCR-003

```gherkin
Scenario: OCR 설정의 환경변수 기반 오버라이드
  Given config.py에 OCR_MODEL, OCR_DETAIL, OCR_MAX_TOKENS 필드가 정의되어 있다
  When 환경변수 OCR_MODEL="gpt-4o"가 설정된다
  And 환경변수 OCR_DETAIL="high"가 설정된다
  And 환경변수 OCR_MAX_TOKENS="4096"이 설정된다
  Then Settings 인스턴스에서 해당 값이 오버라이드된다
```

```gherkin
Scenario: OCR 설정의 기본값 사용
  Given OCR 관련 환경변수가 설정되지 않았다
  When Settings 인스턴스가 생성된다
  Then OCR_MODEL은 "gpt-4o-mini"이다
  And OCR_DETAIL은 "low"이다
  And OCR_MAX_TOKENS는 2048이다
```

**검증 방법**:
- 단위 테스트: `monkeypatch`로 환경변수 설정 후 `Settings()` 인스턴스 필드값 검증
- 기본값 테스트: 환경변수 미설정 상태에서 기본값 확인

---

## 품질 게이트 기준

### Definition of Done

- [ ] `image_processor.py`에서 `httpx` 및 GLM-OCR 관련 코드 완전 제거
- [ ] `image_processor.py`에서 `ChatOpenAI` + `HumanMessage` 기반 구현 완료
- [ ] `config.py`에 `OCR_MODEL` 기본값 `"gpt-4o-mini"`, `OCR_DETAIL`, `OCR_MAX_TOKENS` 추가
- [ ] `TestImageProcessorAgent` 테스트가 LangChain mock 기반으로 동작
- [ ] 기존 테스트 시나리오(성공, 빈 응답) 모두 통과
- [ ] `GLM_API_KEY` 없이 OCR 기능 정상 동작
- [ ] 코드에 `settings.GLM_API_KEY` 참조 없음 (image_processor.py 내)
- [ ] ruff 린트 통과
- [ ] mypy/pyright 타입 체크 통과

### 테스트 커버리지 목표

- `image_processor.py`: 85% 이상
- `config.py` (OCR 관련 필드): 100%
