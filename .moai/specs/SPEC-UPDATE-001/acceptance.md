---
spec_id: SPEC-UPDATE-001
title: Korean Tutoring Prompt Redesign - Acceptance Criteria
version: 1.0.0
created: 2026-02-22
updated: 2026-02-22
author: jw
tags: TAG-SUP-01, TAG-PROMPT-01, TAG-SCHEMA-01, TAG-MODEL-01, TAG-FRONT-01, TAG-LEVEL-01
---

# Acceptance Criteria: SPEC-UPDATE-001

## 1. Acceptance Scenarios

### Scenario 1: Supervisor LLM 사전 분석 (R1)

```gherkin
Feature: Supervisor LLM Pre-Analysis

  Scenario: 정상적인 텍스트 사전 분석
    Given 사용자가 영어 텍스트를 제출한다
      """
      Hananuma Masakichi is a Japanese sculptor most famous for creating
      a life-size statue of himself. Masakichi began his masterpiece in
      the 1880s, believing that he was about to die.
      """
    And 레벨이 3으로 설정되어 있다
    When Supervisor 에이전트가 Claude Haiku로 사전 분석을 수행한다
    Then SupervisorAnalysis 결과가 state에 저장된다
    And sentences 배열에 최소 2개의 SentenceEntry가 포함된다
    And 각 SentenceEntry에 text, difficulty(1-5), focus 필드가 존재한다
    And overall_difficulty가 1-5 범위 내 정수이다
    And focus_summary가 비어있지 않은 문자열 리스트이다

  Scenario: Supervisor LLM 호출 실패 시 Fallback
    Given 사용자가 영어 텍스트를 제출한다
    And Claude Haiku API 호출이 실패한다 (네트워크 오류 또는 타임아웃)
    When Supervisor 에이전트가 fallback 로직을 실행한다
    Then 마침표 기준으로 문장이 분리된다
    And 각 문장의 difficulty가 사용자 설정 level 값으로 설정된다
    And focus_summary가 기본값 ["reading", "grammar", "vocabulary"]로 설정된다
    And 후속 에이전트(Reading, Grammar, Vocabulary)가 정상 실행된다

  Scenario: 단일 문장 입력 처리
    Given 사용자가 단일 영어 문장을 제출한다
      """
      The cat sat on the mat.
      """
    When Supervisor 에이전트가 사전 분석을 수행한다
    Then sentences 배열에 정확히 1개의 SentenceEntry가 포함된다
    And 해당 문장의 difficulty가 1-5 범위 내에 있다
```

### Scenario 2: 한국어 독해 훈련 프롬프트 (R2 - Reading)

```gherkin
Feature: Korean Reading Training Output

  Scenario: 독해 에이전트 한국어 슬래시 읽기 출력
    Given Supervisor 분석이 완료되고 sentences가 전달된다
    And Reading 에이전트가 Claude Sonnet으로 실행된다
    When 독해 분석 결과가 생성된다
    Then ReadingResult.content에 한국어 Markdown이 포함된다
    And 각 문장에 대해 슬래시(/) 직독 끊기가 포함된다
    And 각 문장에 대해 단위별 한국어 해석이 영어 어순으로 제시된다
    And 각 문장에 대해 자연스러운 한국어 해석이 포함된다
    And 각 문장에 대해 읽기 지시가 지시형 말투로 포함된다
      """
      예: "동사 is 먼저 잡아라", "여기서 멈추지 말 것"
      """
    And 결과에 문법 설명이 포함되지 않는다
    And 결과에 어휘 설명이 포함되지 않는다
```

### Scenario 3: 한국어 문법 구조 이해 프롬프트 (R2 - Grammar)

```gherkin
Feature: Korean Grammar Structure Output

  Scenario: 문법 에이전트 한국어 구조 분석 출력
    Given Supervisor 분석이 완료되고 sentences가 전달된다
    And Grammar 에이전트가 GPT-4o로 실행된다
    When 문법 분석 결과가 생성된다
    Then GrammarResult.content에 한국어 Markdown이 포함된다
    And 각 문장에 대해 문법 포인트가 중고등학교 문법 용어로 제시된다
      """
      예: "2형식", "분사구문", "관계대명사 목적격 생략"
      """
    And 각 문장에 대해 "왜 이 구조를 썼는가" 설명이 포함된다
    And 각 문장에 대해 한국어와의 구조 차이 비교가 포함된다
    And 각 문장에 슬래시(/) 읽기가 포함된다
```

### Scenario 4: 한국어 어원 네트워크 프롬프트 (R2 - Vocabulary)

```gherkin
Feature: Korean Etymology Network Output

  Scenario: 어휘 에이전트 한국어 어원 네트워크 출력
    Given Supervisor 분석이 완료되고 sentences가 전달된다
    And Vocabulary 에이전트가 Claude Sonnet으로 실행된다
    When 어휘 분석 결과가 생성된다
    Then VocabularyResult.words에 최소 1개의 VocabularyWordEntry가 포함된다
    And 각 VocabularyWordEntry.content에 한국어 Markdown이 포함된다
    And 각 단어에 대해 6단계 구조가 포함된다:
      | 단계 | 내용                           |
      | 1    | 기본 뜻                        |
      | 2    | 문장 속 의미 작동 설명          |
      | 3    | 핵심 의미 이미지               |
      | 4    | 어원 설명 (PIE 포함 가능)      |
      | 5    | 같은 어원 파생 단어 (최소 3개) |
      | 6    | 기억 연결 팁                   |
    And 단순 명사(apple, book 등)는 선정되지 않는다
    And 단어 뜻만 나열하는 형태가 아니다

  Scenario: Vocabulary 모델이 Sonnet인지 확인
    Given Vocabulary 에이전트가 초기화된다
    When LLM 모델이 로드된다
    Then 사용되는 모델이 Claude Sonnet이다 (Haiku가 아님)
```

### Scenario 5: 스키마 호환성 (R3)

```gherkin
Feature: Schema Compatibility

  Scenario: Backend 스키마 직렬화 검증
    Given 새로운 ReadingResult(content="## 문장 1\n슬래시 읽기...")가 생성된다
    When model_dump()로 직렬화한다
    Then {"content": "## 문장 1\n슬래시 읽기..."} JSON이 반환된다

  Scenario: SupervisorAnalysis 스키마 검증
    Given SupervisorAnalysis가 다음 데이터로 생성된다:
      | Field              | Value                                      |
      | sentences          | [{"text": "Hello.", "difficulty": 1, "focus": ["grammar"]}] |
      | overall_difficulty | 2                                          |
      | focus_summary      | ["grammar", "vocabulary"]                  |
    When Pydantic 유효성 검사를 수행한다
    Then 검증이 성공한다
    And model_dump()가 올바른 JSON을 반환한다

  Scenario: 잘못된 difficulty 값 거부
    Given SentenceEntry에 difficulty가 6으로 설정된다
    When Pydantic 유효성 검사를 수행한다
    Then ValidationError가 발생한다

  Scenario: Aggregator passthrough 호환성
    Given 새 스키마의 reading_result, grammar_result, vocabulary_result가 state에 존재한다
    When aggregator.py가 state를 통과시킨다
    Then 모든 결과가 손실 없이 전달된다
    And AnalyzeResponse로 직렬화가 성공한다
```

### Scenario 6: 프론트엔드 한국어 렌더링 (R5)

```gherkin
Feature: Frontend Korean Markdown Rendering

  Scenario: 독해 패널 Markdown 렌더링
    Given ReadingResult의 content가 한국어 슬래시 읽기 Markdown이다
    When reading-panel 컴포넌트가 렌더링된다
    Then ReactMarkdown으로 한국어 Markdown이 올바르게 표시된다
    And 슬래시(/) 구분, 볼드(**), 화살표(→) 등 Markdown 서식이 적용된다

  Scenario: 문법 패널 Markdown 렌더링
    Given GrammarResult의 content가 한국어 문법 분석 Markdown이다
    When grammar-panel 컴포넌트가 렌더링된다
    Then ReactMarkdown으로 한국어 Markdown이 올바르게 표시된다
    And 문법 용어가 볼드 처리되어 표시된다

  Scenario: 어휘 패널 단어별 Markdown 렌더링
    Given VocabularyResult에 3개의 VocabularyWordEntry가 있다
    When vocabulary-panel 컴포넌트가 렌더링된다
    Then 각 단어의 content가 ReactMarkdown으로 개별 렌더링된다
    And 6단계 어원 분석 구조가 시각적으로 구분되어 표시된다

  Scenario: 탭 라벨 한국어 표시
    Given tabbed-output 컴포넌트가 렌더링된다
    When 탭 목록이 표시된다
    Then 첫 번째 탭 라벨이 "독해"이다
    And 두 번째 탭 라벨이 "문법"이다
    And 세 번째 탭 라벨이 "어휘"이다

  Scenario: 빈 결과 상태 처리
    Given 아직 분석 결과가 없다
    When tabbed-output 컴포넌트가 렌더링된다
    Then 한국어 안내 메시지가 표시된다
```

### Scenario 7: 레벨 지시문 (R6)

```gherkin
Feature: Level Instructions

  Scenario: 레벨별 한국어 지시문 주입
    Given level_instructions.yaml에 5개 레벨이 한국어로 정의되어 있다
    And 사용자가 레벨 3을 선택한다
    When Reading 에이전트 프롬프트가 생성된다
    Then {level_instructions} 플레이스홀더에 레벨 3 한국어 지시문이 주입된다
    And 지시문에 "표준 교육 설명" 관련 내용이 포함된다

  Scenario: 레벨 1 초급 지시문 확인
    Given 사용자가 레벨 1을 선택한다
    When 에이전트 프롬프트에 레벨 지시문이 주입된다
    Then 지시문에 "가장 쉬운 설명" 관련 내용이 포함된다
    And 영어 전문 용어 사용이 최소화되도록 지시된다

  Scenario: 레벨 5 고급 지시문 확인
    Given 사용자가 레벨 5를 선택한다
    When 에이전트 프롬프트에 레벨 지시문이 주입된다
    Then 지시문에 "전문적 분석" 관련 내용이 포함된다
    And 고급 문법 개념 포함이 지시된다
```

---

## 2. Edge Cases

### Edge Case 1: 극단적 입력

| Case                          | Expected Behavior                                      |
|-------------------------------|--------------------------------------------------------|
| 단일 단어 입력 ("Hello")      | Supervisor가 1문장으로 처리, 각 에이전트가 최소 분석 생성 |
| 매우 긴 텍스트 (5000자)       | Supervisor가 다수 문장 분리, 각 에이전트가 중요 문장 선별 |
| 특수문자만 포함된 입력        | AnalyzeRequest의 min_length=10 검증에서 거부              |
| 한국어 텍스트 입력            | 에이전트가 영어 텍스트가 아님을 감지, 적절한 안내 생성    |
| 혼합 언어 입력 (영한 혼용)    | Supervisor가 영어 부분만 추출하여 분석                    |

### Edge Case 2: LLM 응답 품질

| Case                                  | Expected Behavior                               |
|---------------------------------------|--------------------------------------------------|
| Supervisor JSON 파싱 실패             | Fallback: 마침표 기준 문장 분리                   |
| 에이전트 Markdown 포맷 불량           | ReactMarkdown이 raw text로 렌더링 (graceful)     |
| Vocabulary에서 단어를 선정하지 못함   | VocabularyResult.words가 빈 배열로 반환           |
| Reading 에이전트가 슬래시 없이 응답   | content를 그대로 Markdown 렌더링 (기능 저하)     |

### Edge Case 3: SSE 스트리밍

| Case                              | Expected Behavior                                  |
|-----------------------------------|----------------------------------------------------|
| 스트리밍 중 연결 끊김             | 기존 fallback 로직 유지 (재연결 또는 에러 표시)    |
| 부분 Markdown 수신 중 탭 전환    | 현재까지 수신된 content를 렌더링                    |
| 동시에 3개 에이전트 스트리밍      | 각 탭이 독립적으로 content 누적 및 렌더링           |

---

## 3. Quality Criteria

### 3.1 Functional Quality

| Criteria                                   | Target                          |
|--------------------------------------------|---------------------------------|
| Supervisor 사전 분석 성공률                | >= 95% (fallback 포함 100%)     |
| 한국어 프롬프트 적용 여부                  | 모든 4개 에이전트 100%          |
| 스키마 호환성                              | Pydantic 검증 통과 100%         |
| 탭 라벨 한국어화                           | 3개 탭 모두 한국어              |
| ReactMarkdown 렌더링 정상                  | 3개 패널 모두 정상              |

### 3.2 Performance Quality

| Criteria                                   | Target                          |
|--------------------------------------------|---------------------------------|
| Supervisor LLM 호출 추가 지연             | < 2초 (Haiku 기준)             |
| 전체 분석 응답 시간 (SSE 첫 바이트)       | < 5초                           |
| Vocabulary Sonnet 응답 시간               | < 10초                          |
| ReactMarkdown 렌더링 시간                 | < 100ms (per panel)             |

### 3.3 Code Quality

| Criteria                                   | Target                          |
|--------------------------------------------|---------------------------------|
| 테스트 커버리지                            | >= 85%                          |
| Ruff 린트 에러                             | 0                               |
| TypeScript 타입 에러                       | 0                               |
| ESLint 에러                                | 0                               |

---

## 4. Verification Methods

### 4.1 Unit Tests

| Test Target              | Method                                           |
|--------------------------|--------------------------------------------------|
| SentenceEntry 스키마     | Pydantic model_validate + 경계값 테스트           |
| SupervisorAnalysis 스키마| Pydantic model_validate + 필수 필드 검증          |
| ReadingResult 스키마     | content 필드 존재 및 문자열 검증                  |
| VocabularyWordEntry 스키마| word + content 필드 검증                         |
| Supervisor fallback 로직 | LLM 호출 mock + 에러 시나리오 테스트             |
| 프롬프트 로딩            | 파일 존재 확인 + 변수 치환 검증                  |
| 레벨 지시문 주입         | 각 레벨별 올바른 텍스트 주입 검증                |

### 4.2 Integration Tests

| Test Target              | Method                                           |
|--------------------------|--------------------------------------------------|
| Supervisor -> 에이전트 흐름 | LangGraph 실행 + state 검증                     |
| SSE 스트리밍 데이터 포맷   | 스트리밍 응답의 새 스키마 호환성 검증            |
| Frontend 컴포넌트 렌더링   | React Testing Library + Markdown 콘텐츠 검증    |

### 4.3 Manual Verification

| Test Target              | Method                                           |
|--------------------------|--------------------------------------------------|
| 한국어 교육 품질         | 실제 영어 지문으로 결과 품질 검토                |
| 슬래시 읽기 정확성       | 교육 전문가 관점에서 직독직해 구분 검토          |
| 어원 네트워크 정확성     | 어원 정보의 사실적 정확성 검토                   |
| UI/UX 한국어 표시        | 한국어 Markdown 렌더링 시각적 검토               |

---

## 5. Definition of Done

- [ ] 모든 22개 프로덕션 파일이 변경 완료
- [ ] Supervisor가 Claude Haiku로 LLM 사전 분석 수행
- [ ] 4개 에이전트 모두 한국어 교육 프롬프트 적용
- [ ] Vocabulary 모델이 Sonnet으로 업그레이드
- [ ] Backend 스키마가 content 기반으로 전환
- [ ] Frontend 타입이 새 스키마에 맞게 업데이트
- [ ] 3개 패널 모두 ReactMarkdown으로 한국어 렌더링
- [ ] 탭 라벨이 한국어(독해/문법/어휘)로 표시
- [ ] level_instructions.yaml이 한국어로 재작성
- [ ] Supervisor fallback 로직 구현 및 테스트
- [ ] 기존 테스트가 새 스키마에 맞게 업데이트
- [ ] 테스트 커버리지 85% 이상
- [ ] Ruff 린트 에러 0개
- [ ] TypeScript/ESLint 에러 0개
- [ ] E2E 통합 테스트 통과 (텍스트 입력 -> 한국어 결과 표시)
