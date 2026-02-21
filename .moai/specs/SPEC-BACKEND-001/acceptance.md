# SPEC-BACKEND-001 인수 기준 (Acceptance Criteria)

> 참조: SPEC-BACKEND-001 (spec.md, plan.md)
> 형식: Given-When-Then (Gherkin 스타일)

---

## 1. 텍스트 분석 시나리오

### Scenario 1-A: 기본 텍스트 분석 요청

```gherkin
Feature: POST /api/v1/tutor/analyze 텍스트 분석

  Scenario: 유효한 영어 텍스트로 분석 요청 시 세 가지 튜터 결과 반환
    Given 다음 조건이 충족됨:
      | 항목 | 값 |
      |------|-----|
      | 입력 텍스트 | "The cat sat on the mat. It was a sunny day." |
      | 이해도 수준 | 2 |
      | 서비스 상태 | 정상 운영 중 |

    When 클라이언트가 POST /api/v1/tutor/analyze를 다음 본문으로 호출:
      ```json
      {
        "text": "The cat sat on the mat. It was a sunny day.",
        "level": 2
      }
      ```

    Then 응답은 다음을 만족해야 함:
      - HTTP 상태 코드: 200
      - Content-Type: text/event-stream
      - SSE 이벤트 스트림에 "reading_chunk" 이벤트 포함
        - 데이터에 "summary", "main_topic", "emotional_tone" 필드 존재
      - SSE 이벤트 스트림에 "grammar_chunk" 이벤트 포함
        - 데이터에 "tenses", "voice", "sentence_structure", "analysis" 필드 존재
      - SSE 이벤트 스트림에 "vocabulary_chunk" 이벤트 포함
        - 데이터에 "words" 배열 존재, 각 항목에 "term", "meaning", "usage", "synonyms" 포함
      - SSE 이벤트 스트림에 "done" 이벤트 포함
        - 데이터에 "session_id" (UUID 형식) 포함
```

**검증 코드 위치:** `tests/integration/test_api.py::test_analyze_text_returns_all_tutor_results`

---

### Scenario 1-B: 긴 텍스트 SSE 스트리밍 응답

```gherkin
  Scenario: 긴 영어 텍스트 분석 시 SSE 스트리밍으로 실시간 응답 전달
    Given 다음 조건이 충족됨:
      | 항목 | 값 |
      |------|-----|
      | 입력 텍스트 | 500자 이상의 영어 에세이 (MEDIUM_TEXT fixture) |
      | 이해도 수준 | 3 |
      | 세 에이전트 응답 지연 | 각 0.5초 (Mock) |

    When 클라이언트가 POST /api/v1/tutor/analyze를 SSE 스트리밍 모드로 호출

    Then 응답은 다음을 만족해야 함:
      - 세 에이전트의 결과가 완료되는 순서대로 개별 SSE 이벤트로 전송됨
      - 모든 청크 이벤트가 수신된 후 "done" 이벤트 전송
      - 전체 응답 시간이 단일 블로킹 호출보다 짧음 (병렬 처리 검증)
      - 스트림 연결이 끊기지 않음 (keepalive 유지)
```

**검증 코드 위치:** `tests/integration/test_api.py::test_analyze_streams_incrementally`

---

### Scenario 1-C: 유효하지 않은 텍스트 입력 거부

```gherkin
  Scenario: 텍스트가 너무 짧은 경우 HTTP 422 반환
    Given 클라이언트가 5자 미만의 텍스트를 요청 본문에 포함

    When POST /api/v1/tutor/analyze 호출

    Then 응답은 다음을 만족해야 함:
      - HTTP 상태 코드: 422
      - 응답 본문에 "text" 필드 관련 유효성 검사 오류 메시지 포함

  Scenario: 이해도 수준이 범위를 벗어난 경우 HTTP 422 반환
    Given 클라이언트가 level=6을 요청 본문에 포함

    When POST /api/v1/tutor/analyze 호출

    Then 응답은 다음을 만족해야 함:
      - HTTP 상태 코드: 422
      - 응답 본문에 "level" 필드 관련 유효성 검사 오류 메시지 포함
```

**검증 코드 위치:** `tests/unit/test_schemas.py::test_analyze_request_validation`

---

## 2. 이미지 분석 시나리오

### Scenario 2-A: 이미지에서 텍스트 추출 후 분석

```gherkin
Feature: POST /api/v1/tutor/analyze-image 이미지 분석

  Scenario: 영어 텍스트가 포함된 이미지 분석 시 OCR + 튜터 결과 반환
    Given 다음 조건이 충족됨:
      | 항목 | 값 |
      |------|-----|
      | 이미지 | "Hello, World! Today is a good day." 텍스트가 포함된 PNG |
      | 이미지 크기 | 1MB 미만 |
      | MIME 타입 | "image/png" |
      | 이해도 수준 | 1 |

    When 클라이언트가 POST /api/v1/tutor/analyze-image를 다음 본문으로 호출:
      ```json
      {
        "image_data": "<base64_encoded_image>",
        "mime_type": "image/png",
        "level": 1
      }
      ```

    Then 응답은 다음을 만족해야 함:
      - HTTP 상태 코드: 200
      - Content-Type: text/event-stream
      - ImageProcessor가 이미지에서 텍스트를 추출하여 state.extracted_text에 저장
      - 추출된 텍스트로 세 튜터 에이전트가 순차적으로 분석 수행
      - SSE 이벤트 스트림에 "reading_chunk", "grammar_chunk", "vocabulary_chunk", "done" 이벤트 포함
```

**검증 코드 위치:** `tests/integration/test_api.py::test_analyze_image_extracts_text_and_analyzes`

---

### Scenario 2-B: 잘못된 이미지 형식 거부

```gherkin
  Scenario: 지원하지 않는 이미지 형식 업로드 시 HTTP 400 반환
    Given 클라이언트가 GIF 형식의 이미지를 "image/gif" MIME 타입으로 전송

    When POST /api/v1/tutor/analyze-image 호출

    Then 응답은 다음을 만족해야 함:
      - HTTP 상태 코드: 400
      - 응답 본문에 "Unsupported image format" 또는 유사한 오류 메시지 포함

  Scenario: 10MB 초과 이미지 업로드 시 HTTP 400 반환
    Given 클라이언트가 11MB 크기의 JPEG 이미지를 base64 인코딩하여 전송

    When POST /api/v1/tutor/analyze-image 호출

    Then 응답은 다음을 만족해야 함:
      - HTTP 상태 코드: 400
      - 응답 본문에 "Image size exceeds 10MB limit" 또는 유사한 오류 메시지 포함
```

**검증 코드 위치:** `tests/unit/test_services.py::test_image_validation`

---

## 3. 후속 질문 시나리오

### Scenario 3-A: 유효한 세션으로 후속 질문

```gherkin
Feature: POST /api/v1/tutor/chat 후속 질문

  Scenario: 이전 분석 세션에서 후속 질문 시 컨텍스트 기반 답변 반환
    Given 다음 조건이 충족됨:
      | 항목 | 값 |
      |------|-----|
      | 세션 ID | 이전 /analyze 요청으로 생성된 유효한 UUID |
      | 세션 내 대화 내역 | "The cat sat on mat" 텍스트 분석 결과 저장됨 |

    When 클라이언트가 POST /api/v1/tutor/chat를 다음 본문으로 호출:
      ```json
      {
        "session_id": "550e8400-e29b-41d4-a716-446655440000",
        "question": "What does 'sat' mean in Korean?",
        "level": 2
      }
      ```

    Then 응답은 다음을 만족해야 함:
      - HTTP 상태 코드: 200
      - Content-Type: text/event-stream
      - SSE 이벤트에 "chat_chunk" 이벤트 포함
        - 응답 내용이 이전 분석 컨텍스트("cat", "mat")를 참조함
      - SSE 이벤트에 "done" 이벤트 포함
      - 세션 내 메시지 내역이 업데이트됨 (질문 + 답변 추가)
```

**검증 코드 위치:** `tests/integration/test_api.py::test_chat_uses_session_context`

---

### Scenario 3-B: 존재하지 않는 세션 ID로 질문

```gherkin
  Scenario: 존재하지 않는 session_id로 질문 시 새 세션 생성 후 응답
    Given 클라이언트가 데이터베이스에 존재하지 않는 session_id를 사용

    When POST /api/v1/tutor/chat를 존재하지 않는 session_id로 호출:
      ```json
      {
        "session_id": "00000000-0000-0000-0000-000000000000",
        "question": "What is grammar?",
        "level": 3
      }
      ```

    Then 응답은 다음을 만족해야 함:
      - HTTP 상태 코드: 200 (오류가 아닌 정상 처리)
      - 새 세션이 생성됨
      - SSE 이벤트 스트림에 "chat_chunk"와 "done" 이벤트 포함
      - "done" 이벤트의 session_id가 새로 생성된 UUID 형식
```

**검증 코드 위치:** `tests/integration/test_api.py::test_chat_creates_new_session_if_not_found`

---

## 4. 에이전트 라우팅 시나리오

### Scenario 4-A: 텍스트 입력 시 3개 에이전트 병렬 실행

```gherkin
Feature: LangGraph Supervisor 라우팅

  Scenario: 텍스트 입력 시 Supervisor가 세 에이전트를 병렬 디스패치
    Given LangGraph 그래프가 초기화됨
    And task_type이 "analyze"로 설정됨
    And Reading, Grammar, Vocabulary 에이전트 모두 Mock으로 대체됨

    When 그래프의 supervisor_node가 실행됨

    Then 다음을 검증해야 함:
      - supervisor가 Send() API를 통해 "reading", "grammar", "vocabulary" 노드를 동시에 디스패치
      - 세 Mock 에이전트 모두 각 1회 호출됨
      - aggregator_node가 세 에이전트 결과를 모두 수신한 후 실행됨
      - 최종 TutorState에 reading_result, grammar_result, vocabulary_result 모두 존재
```

**검증 코드 위치:** `tests/unit/test_graph.py::test_supervisor_dispatches_parallel_agents`

---

### Scenario 4-B: 이미지 입력 시 ImageProcessor 선행 실행

```gherkin
  Scenario: 이미지 입력 시 ImageProcessor가 먼저 실행된 후 세 에이전트 실행
    Given LangGraph 그래프가 초기화됨
    And task_type이 "image_process"로 설정됨
    And 모든 에이전트가 Mock으로 대체됨

    When 그래프의 supervisor_node가 실행됨

    Then 다음을 검증해야 함:
      - supervisor가 먼저 "image_processor" 노드를 디스패치
      - image_processor_node가 완료된 후 extracted_text가 state에 설정됨
      - image_processor 완료 후 "reading", "grammar", "vocabulary" 노드가 병렬 디스패치됨
      - 병렬 에이전트들이 input_text 대신 extracted_text를 사용하여 분석
```

**검증 코드 위치:** `tests/unit/test_graph.py::test_supervisor_routes_image_to_processor_first`

---

## 5. 이해도 수준 시나리오

### Scenario 5-A: Level 1 설정 시 간단한 설명 제공

```gherkin
Feature: 이해도 수준별 맞춤 설명

  Scenario: Level 1로 설정 시 중학생 눈높이의 간단한 설명 제공
    Given 이해도 수준이 1로 설정됨
    And level_instructions.yaml에서 Level 1 지침이 로드됨

    When Reading 에이전트에 다음 텍스트 분석 요청:
      "The sun rises in the east every morning."

    Then 에이전트 프롬프트는 다음을 포함해야 함:
      - Level 1 지침 텍스트 (기초 수준 설명 방식)
      - 복잡한 학술 용어 사용 금지 지침

    And Mock 응답을 사용한 결과 검증:
      - ReadingResult의 summary가 짧고 간결한 문장으로 구성됨
      - emotional_tone이 단순한 형용사로 표현됨
```

**검증 코드 위치:** `tests/unit/test_agents.py::test_reading_agent_level_1_prompt_injection`

---

### Scenario 5-B: Level 5 설정 시 전문적 분석 제공

```gherkin
  Scenario: Level 5로 설정 시 수능/토익 수준의 전문 분석 제공
    Given 이해도 수준이 5로 설정됨
    And level_instructions.yaml에서 Level 5 지침이 로드됨

    When Grammar 에이전트에 복잡한 문장 분석 요청:
      "Had the experiment succeeded, the findings would have revolutionized our understanding."

    Then 에이전트 프롬프트는 다음을 포함해야 함:
      - Level 5 지침 텍스트 (고급 분석 방식)
      - 시제/가정법 분석 포함 지침

    And Mock 응답을 사용한 결과 검증:
      - GrammarResult에 "subjunctive mood" 또는 "가정법" 관련 분석 포함
      - tenses 필드에 "past perfect" 포함
```

**검증 코드 위치:** `tests/unit/test_agents.py::test_grammar_agent_level_5_prompt_injection`

---

## 6. 실제 LLM 통합 테스트 시나리오

### Scenario 6-A: 실제 API로 단일 에이전트 검증

```gherkin
Feature: 실제 LLM API 통합 테스트 (integration 마커)

  @pytest.mark.integration
  Scenario: 실제 Claude Sonnet API로 Reading 에이전트 Pydantic 스키마 검증 통과
    Given 환경 변수에 유효한 ANTHROPIC_API_KEY가 설정됨
    And Reading 에이전트가 실제 Claude Sonnet 모델로 초기화됨

    When SIMPLE_TEXT fixture를 level=2로 분석 요청

    Then 다음을 검증해야 함:
      - 반환값이 ReadingResult Pydantic 모델 인스턴스임
      - summary 필드가 비어있지 않은 문자열
      - main_topic 필드가 비어있지 않은 문자열
      - emotional_tone 필드가 비어있지 않은 문자열
      - Pydantic 스키마 검증 오류 없음
```

**검증 코드 위치:** `tests/integration/test_real_llm.py::test_reading_agent_schema_validation`

---

### Scenario 6-B: 전체 그래프 E2E 실제 API 테스트

```gherkin
  @pytest.mark.integration
  Scenario: 실제 API 키로 전체 LangGraph E2E 실행 시 SSE 이벤트 정상 수신
    Given 환경 변수에 유효한 OPENAI_API_KEY와 ANTHROPIC_API_KEY가 설정됨
    And create_graph()로 전체 LangGraph 파이프라인 초기화됨
    And 입력: SIMPLE_TEXT (30자 내외), level=1

    When 그래프를 astream() 비동기 스트리밍 모드로 실행

    Then 다음을 검증해야 함:
      - "reading" 노드 완료 이벤트 수신
      - "grammar" 노드 완료 이벤트 수신
      - "vocabulary" 노드 완료 이벤트 수신
      - "aggregator" 노드 완료 이벤트 수신
      - 최종 state에 reading_result, grammar_result, vocabulary_result 모두 None이 아님
      - 모든 결과가 Pydantic 스키마 검증 통과
      - 전체 실행 완료 (TimeoutError 없음, 제한: 60초)
```

**검증 코드 위치:** `tests/integration/test_real_llm.py::test_full_graph_e2e_sse`

---

## 7. 헬스 체크 시나리오

### Scenario 7-A: 정상 상태 헬스 체크

```gherkin
Feature: GET /api/v1/health 헬스 체크

  Scenario: 서비스 정상 운영 시 헬스 체크 성공 응답
    Given FastAPI 앱이 정상 실행 중
    And OpenAI, Anthropic API 키가 모두 설정됨

    When GET /api/v1/health 호출

    Then 응답은 다음을 만족해야 함:
      - HTTP 상태 코드: 200
      - Content-Type: application/json
      - 응답 본문:
        ```json
        {
          "status": "healthy",
          "openai": "connected",
          "anthropic": "connected",
          "version": "1.0.0"
        }
        ```
```

**검증 코드 위치:** `tests/integration/test_api.py::test_health_endpoint`

---

## 8. 품질 게이트 기준 (Quality Gate Criteria)

### 코드 커버리지

| 모듈 | 최소 커버리지 | 측정 방법 |
|------|--------------|-----------|
| `schemas.py` | 95% | `pytest --cov` |
| `services/*.py` | 90% | `pytest --cov` |
| `agents/*.py` | 85% | `pytest --cov` (Mock 기반) |
| `graph.py` | 85% | `pytest --cov` |
| `routers/*.py` | 80% | `pytest --cov` |
| **전체** | **85%** | `pytest --cov-fail-under=85` |

### 린트 및 타입 검사

| 도구 | 기준 | 실행 명령 |
|------|------|-----------|
| `ruff` 린트 | 오류 0개 | `uv run ruff check src/` |
| `ruff` 포맷 | 포맷 위반 0개 | `uv run ruff format --check src/` |
| Pydantic 타입 오류 | 0개 | 모든 스키마 검증 테스트 통과 |

### 테스트 통과 기준

| 카테고리 | 기준 |
|----------|------|
| 단위 테스트 | 100% 통과 |
| 통합 테스트 (Mock) | 100% 통과 |
| 실제 LLM 테스트 | 수동 실행 시 100% 통과 |

### Definition of Done (완료 정의)

- [ ] 11개 Task 모두 구현 완료
- [ ] 전체 코드 커버리지 85% 이상 달성
- [ ] `uv run pytest` 모든 단위/통합(Mock) 테스트 통과
- [ ] `uv run ruff check src/ tests/` 오류 0개
- [ ] `uv run ruff format --check src/ tests/` 위반 0개
- [ ] 모든 Pydantic 스키마 검증 테스트 통과
- [ ] SSE 스트리밍 이벤트 순서 검증 통과
- [ ] SPEC-BACKEND-001의 모든 EARS 요구사항 추적성 태그 연결 확인
- [ ] `/api/v1/health` 엔드포인트 정상 응답 확인
- [ ] `.env.example` 파일에 모든 필수 환경 변수 문서화 완료
