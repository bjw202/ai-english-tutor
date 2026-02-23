---
id: SPEC-UPDATE-001
title: Korean Tutoring Prompt Redesign
version: 1.2.1
status: Completed
created: 2026-02-22
updated: 2026-02-22
author: jw
priority: High
related_specs:
  - SPEC-BACKEND-001
  - SPEC-FRONTEND-001
  - SPEC-UI-001
lifecycle: spec-anchored
tags: prompt-redesign, korean-tutoring, llm-supervisor, schema-redesign, markdown-normalizer
---

# SPEC-UPDATE-001: Korean Tutoring Prompt Redesign

## HISTORY

| Version | Date       | Author | Description                              |
|---------|------------|--------|------------------------------------------|
| 1.0.0   | 2026-02-22 | jw     | Initial SPEC creation                    |
| 1.1.0   | 2026-02-22 | jw     | R2 요구사항 보충: my-prompt/ 원본의 교육 세부 규칙 전체 반영 |
| 1.1.0   | 2026-02-22 | jw     | Implementation Complete: All requirements R1-R6 implemented and verified (Backend: 165 tests passing, Frontend: 97 tests passing) |
| 1.2.0   | 2026-02-22 | jw     | R7 추가: LLM 출력 Markdown 정규화 (post-processing normalizer) |
| 1.2.1   | 2026-02-23 | jw     | Implementation Complete: R1-R7 all verified. Backend: 207 tests passing (95% cost reduction with gpt-4o-mini unification). SPEC-UPDATE-001 + SPEC-MODEL-001 combined delivery. |

---

## 1. Environment (E)

### 1.1 Project Context

AI English Tutor는 한국 중학생 대상 영어 학습 웹 애플리케이션이다. 현재 시스템은 영어 분석(analysis) 중심으로 설계되어 있으며, 이번 업데이트를 통해 한국어 교육(tutoring) 중심으로 전환한다.

### 1.2 Current Architecture

- **Backend**: FastAPI + LangGraph 멀티 에이전트 시스템 (supervisor, reading, grammar, vocabulary)
- **Frontend**: Next.js + SSE 스트리밍, 탭 기반 결과 표시 (Reading/Grammar/Vocabulary)
- **LLM 모델**: Supervisor(GPT-4o-mini), Reading(Sonnet), Grammar(GPT-4o), Vocabulary(Haiku)

### 1.3 Constraints

- LangGraph의 `Send()` 병렬 dispatch 패턴은 변경하지 않는다 (`graph.py` 유지)
- `get_llm()` 팩토리 함수를 재사용한다 (`models/llm.py` 유지)
- Aggregator의 passthrough 패턴은 새 스키마에서도 동작해야 한다 (`aggregator.py` 유지)
- 구조 비의존적 SSE 포맷터를 유지한다 (`services/streaming.py` 유지)
- `model_dump()` 직렬화 패턴을 유지한다 (`routers/tutor.py` 유지)

### 1.4 Tech Stack (Unchanged)

| Component        | Technology       | Version  |
|------------------|------------------|----------|
| Backend Framework| FastAPI          | 0.115+   |
| AI Orchestration | LangGraph        | 0.3+     |
| LLM Integration  | langchain-openai | 0.3+     |
| LLM Integration  | langchain-anthropic | 0.3+  |
| Data Validation  | Pydantic         | 2.10+    |
| Frontend Framework| Next.js         | 15.x     |
| UI Library       | React            | 19.x     |
| Markdown Rendering| react-markdown  | latest   |

---

## 2. Assumptions (A)

### 2.1 Business Assumptions

- [A1] 한국어 교육 중심 접근이 중학생 학습 효과를 향상시킨다.
- [A2] 어원 네트워크 기반 어휘 학습이 단순 단어-뜻 매핑보다 장기 기억에 효과적이다.
- [A3] 슬래시 읽기(직독직해) 훈련이 독해력과 문법 이해를 동시에 향상시킨다.
- [A4] 문장 단위 분석이 지문 단위 분석보다 교육적 효과가 높다.

### 2.2 Technical Assumptions

- [A5] Claude Haiku는 Supervisor 사전 분석(문장 분리, 난이도 평가, 학습 포커스 추천)에 충분한 성능을 갖는다.
- [A6] Vocabulary 에이전트를 Haiku에서 Sonnet으로 업그레이드하면 한국어 어원 설명 품질이 향상된다.
- [A7] `content: str` 기반 Markdown 결과 스키마가 구조화된 JSON 스키마보다 유연하고 풍부한 교육 콘텐츠를 전달할 수 있다.
- [A8] ReactMarkdown은 에이전트가 생성하는 한국어 Markdown을 정확하게 렌더링할 수 있다.
- [A9] 기존 SSE 스트리밍 구조는 `content: str` 스키마와 호환된다.

### 2.3 Confidence Assessment

| Assumption | Confidence | Risk if Wrong                                    |
|------------|------------|--------------------------------------------------|
| A5         | Medium     | Haiku 품질 부족 시 Sonnet으로 업그레이드 필요      |
| A6         | High       | Sonnet은 이미 Reading에서 검증됨                   |
| A7         | High       | Markdown이 충분히 유연함                           |
| A8         | High       | ReactMarkdown은 표준 Markdown을 완벽 지원         |
| A9         | High       | SSE는 구조 비의존적으로 설계됨                     |

---

## 3. Requirements (R)

### R1: Supervisor 사전 분석 (LLM-Powered Pre-Analyzer)

**WHEN** 사용자가 텍스트를 제출하면, **THEN** 시스템은 Claude Haiku를 사용하여 다음 사전 분석을 수행해야 한다:
- 입력 텍스트를 개별 문장으로 분리 (`sentences: list[SentenceEntry]`)
- 각 문장의 난이도를 5단계로 평가 (`difficulty: int`)
- 학습 포커스를 추천 (`focus: list[str]`)
- 전체 지문 난이도 요약 (`overall_difficulty: int`)

**IF** Supervisor LLM 호출이 실패하면, **THEN** 시스템은 기본 문장 분리(마침표 기준)로 fallback하고 난이도를 level 값으로 설정해야 한다.

시스템은 **항상** Supervisor 분석 결과를 `SupervisorAnalysis` 스키마로 직렬화하여 state에 저장해야 한다.

시스템은 Supervisor 사전 분석 결과를 각 튜터 에이전트(Reading, Grammar, Vocabulary)에 **항상** 전달해야 한다.

### R2: 한국어 교육 프롬프트 (Korean Tutoring Prompts)

시스템은 모든 프롬프트를 **항상** 한국어로 작성해야 한다.

시스템은 few-shot 예시를 프롬프트에 포함하지 **않아야 한다**.

---

#### R2-1: Reading 에이전트 프롬프트 (독해 훈련)

**WHEN** Reading 에이전트가 실행되면, **THEN** 시스템은 다음 한국어 독해 훈련 프롬프트를 사용해야 한다.

**[교육 목표]**

- 학생이 영어 문장을 **스스로 끝까지 읽게 만드는 훈련**
- 해석을 알려주는 것이 아니라 **읽기 동작을 교정**
- 문장 중심은 항상 **동사와 구조**

**[문장별 4단계 구조]** (각 문장마다 반드시 이 구조 유지)

1. **슬래시 직독 끊기**: 영어 원문에 영어식 직독 끊기 표시 (슬래시 / 로 끊기)
2. **단위별 한국어 해석**: 영어 단위별 한국어 해석 (영어 순서 유지)
3. **자연스러운 한국어 해석**: 의미가 전달되도록 자연스러운 한국어 번역 제시
4. **읽기 지시**: 3줄 이내, 핵심만

**[슬래시 직독 끊기 규칙]**

- 주어 / 동사 / 목적어 / 부가정보 순서가 드러나게 끊어라
- with, although, while 등은 구조가 보이게 끊어라
- 긴 명사구는 덩어리 단위로 유지하라
- 불필요하게 잘게 쪼개지 말 것

**[단위별 한국어 해석 규칙]**

- 영어 어순을 유지한 채 한 단위씩 번역
- 한국식으로 자연스럽게 바꾸지 말고 "영어를 따라가며 붙이는 느낌"으로 제시

**[읽기 지시 작성 규칙 — 가장 중요]**

- 반드시 아래 내용 중 하나 포함:
  - 이 문장에서 멈추면 안 되는 지점
  - 핵심 동사/핵심 단어
  - 부가 정보는 흘려야 하는 이유
  - 앞을 확정하지 말고 뒤를 기다려야 하는 이유
  - 대명사 연결 주의
- **3줄 초과 금지**
- 설명형 말투 금지
- 지시형 말투 사용 ("~를 먼저 잡아라", "여기서 멈추지 말 것")

**[톤]**

- 담백하게, 군더더기 없이
- 문장당 길이 과도하게 늘리지 말 것
- 구조 훈련이 중심

**[절대 금지]**

- 문법 설명 금지
- 어휘 설명 금지
- 문단 구조 분석 금지
- 출제 의도 분석 금지
- 심리학 개념 확장 금지
- 장황한 설명 금지

---

#### R2-2: Grammar 에이전트 프롬프트 (문법 구조 이해)

**WHEN** Grammar 에이전트가 실행되면, **THEN** 시스템은 다음 한국어 문법 구조 이해 프롬프트를 사용해야 한다.

**[교육 목표]**

- 단순 문법 나열이 아니라 **"구조 이해 중심 문법 해설"**
- **"학생이 구조를 깨닫는 순간이 생기는 해설"**이 최종 목표

**[해설 원칙]**

1. 문장별로 해설한다.
2. 반드시 해당 영어 문장을 먼저 제시한다 (슬래시 읽기 포함).
3. 각 문장은 아래 4단계 구조로 설명한다.

**[문장별 4단계 구조]**

1. **문법 포인트**
   - 중·고등학교 문법 용어를 반드시 사용 (예: 2형식, 3형식, 동명사, 분사구문, 관계대명사 목적격 생략, 명사절, 간접의문문, 수동태 등)
2. **왜 이 구조를 썼는가?**
   - 단순 정의 금지
   - 문법적 이유 설명
   - 문장 구조 관점에서 설명
3. **한국어와의 구조 차이**
   - 한국어식 표현을 예시로 제시
   - 영어와 어순/사고방식 차이를 비교
   - 학생이 헷갈리는 지점을 정확히 짚어줄 것
4. **시험 포인트** (선택)
   - 자주 출제되는 함정 또는 오개념 1줄 요약

**["왜?" 필수 질문]**

- 왜 동명사인가? 왜 수동태인가? 왜 단수 취급인가? 왜 관계대명사가 생략되는가?
- 이 질문에 답하지 못하면 해설이 아니다.

**[영어 구조 중심 언어 전제]**

- 영어는 '구조 중심 언어'임을 전제로 설명하라:
  - 앞핵심 + 뒤수식 구조
  - 주절 중심 구조
  - 동작 명사화 경향
  - 객관 서술에서 수동 선호
- 이 개념을 필요할 때 적극 활용하라.

**[형식 제약]**

- 문단당 **4~6줄 이내** 유지
- 핵심만, 강의하듯 임팩트 있게
- 군더더기 설명 금지

**[절대 금지]**

- 문법 이름만 나열
- 사전식 정의
- 쓸데없이 긴 이론 설명
- "이 문장은 ~이다" 반복형 해설

---

#### R2-3: Vocabulary 에이전트 프롬프트 (어원 네트워크)

**WHEN** Vocabulary 에이전트가 실행되면, **THEN** 시스템은 다음 한국어 어원 네트워크 프롬프트를 사용해야 한다.

**[교육 목표]**

- 단어 뜻 암기가 아니라 **의미 작동 원리 이해**와 **어원 네트워크 기반 장기 기억 형성**

**[단어 선정 원칙]**

- 중학교 2학년 수준에서 설명이 필요한 단어만 선정
- **추상적 의미가 있는 단어를 우선 선택**
- **일상적 의미와 문장 속 의미가 다른 단어를 반드시 포함**
- 단순 명사(apple, book 등)는 제외

**[단어별 6단계 구조]** (각 단어마다 반드시 아래 구조 유지)

1. **기본 뜻**: 한 줄로 간단 명확하게 제시
2. **문장 속 의미 작동 설명**:
   - 이 문장에서 왜 이런 의미로 해석되는지 설명
   - 일반적인 뜻과 차이가 있다면 반드시 비교 설명
   - 단어가 문장 분위기/논리/원인/결과에 어떤 역할을 하는지 설명
   - 단순 해석 금지. **"왜 이 단어가 여기서 이 의미가 되는가"**를 설명할 것
3. **핵심 의미 이미지**: 이 단어의 가장 근본적인 의미를 한 단어 또는 한 문장으로 정리
4. **어원 설명** (필수):
   - 가능한 경우 **PIE(Proto-Indo-European) 어근**까지 제시
   - 게르만어/라틴어/그리스어/고대 영어 등 중간 단계 제시
   - 어원이 어떻게 현재 의미로 발전했는지 **"의미 변화 흐름"**으로 설명
   - 단순 나열 금지. 반드시 **"의미 발전 과정"**을 설명할 것
5. **같은 어원 파생 단어** (최소 3개):
   - 현재 학습자가 알고 있을 가능성이 높은 단어 포함
   - 각각의 **공통 핵심 이미지를 짧게 연결** 설명
6. **기억 연결 팁**: 학생이 나중에 단어를 외울 때 도움이 되도록 "어근 네트워크 방식"으로 기억하는 방법을 1~2줄 제시

**[설명 톤]**

- 지나치게 학술적으로 쓰지 말 것
- 그러나 의미의 정확성은 유지할 것
- 비유를 사용하되 과도하게 감성적으로 쓰지 말 것
- 교육 목적이므로 구조적 설명 우선

**[출력 형식]**

- 번호를 붙여 정리
- 가독성 좋게 구분선 사용 가능
- 불필요한 이모지 과다 사용 금지

**[절대 금지]**

- 단어 뜻만 나열하지 말 것
- 어원만 나열하고 현재 의미 연결을 생략하지 말 것
- 파생어를 나열만 하고 공통 이미지 설명을 생략하지 말 것
- 추상어를 단순 번역으로 끝내지 말 것

---

#### R2-4: Supervisor 에이전트 프롬프트 (사전 분석)

**WHEN** Supervisor 에이전트가 실행되면, **THEN** 시스템은 한국어 사전 분석 프롬프트를 사용해야 한다:
- 문장 분리, 난이도 평가, 학습 포커스 추천 지시
- JSON 구조화 출력 요구

### R3: 스키마 재설계 (Schema Redesign)

시스템은 **항상** 다음 새로운 스키마를 사용해야 한다:

**Backend 스키마 (`schemas.py`)**:
- `SentenceEntry`: 개별 문장 엔트리 (`text: str`, `difficulty: int`, `focus: list[str]`)
- `SupervisorAnalysis`: Supervisor 분석 결과 (`sentences: list[SentenceEntry]`, `overall_difficulty: int`, `focus_summary: list[str]`)
- `VocabularyWordEntry`: 어휘 단어 엔트리 (`word: str`, `content: str`)
- `ReadingResult`: 독해 결과 (`content: str` - 한국어 Markdown)
- `GrammarResult`: 문법 결과 (`content: str` - 한국어 Markdown)
- `VocabularyResult`: 어휘 결과 (`words: list[VocabularyWordEntry]`)

**Backend State (`state.py`)**:
- `supervisor_analysis: NotRequired[SupervisorAnalysis | None]` 추가
- `reading_result`, `grammar_result`, `vocabulary_result` 타입을 새 스키마로 변경

**Frontend 타입 (`types/tutor.ts`)**:
- `ReadingResult`: `{ content: string }`
- `GrammarResult`: `{ content: string }`
- `VocabularyResult`: `{ words: VocabularyWordEntry[] }` 또는 `{ content: string }` (Markdown fallback)

### R4: 모델 업그레이드 (Model Upgrade)

시스템은 **항상** Vocabulary 에이전트에 Claude Sonnet 모델을 사용해야 한다 (기존 Haiku에서 업그레이드).

**WHILE** Vocabulary 에이전트가 활성화된 상태에서, 시스템은 Claude Sonnet을 통해 한국어 어원 네트워크 기반 설명을 생성해야 한다.

**WHERE** 비용 최적화 기능이 존재하면, 시스템은 Supervisor에 Claude Haiku를 유지하여 비용 효율을 확보해야 한다.

| Agent      | Current Model   | New Model       | Reason                              |
|------------|----------------|-----------------|-------------------------------------|
| Supervisor | GPT-4o-mini    | Claude Haiku    | LLM 사전 분석 전환, 비용 효율       |
| Reading    | Claude Sonnet  | Claude Sonnet   | 변경 없음                           |
| Grammar    | GPT-4o         | GPT-4o          | 변경 없음                           |
| Vocabulary | Claude Haiku   | Claude Sonnet   | 한국어 어원 설명 품질 향상          |

### R5: 프론트엔드 한국어 렌더링 (Frontend Korean Rendering)

**WHEN** 분석 결과가 수신되면, **THEN** 모든 패널(독해, 문법, 어휘)은 ReactMarkdown으로 한국어 Markdown을 렌더링해야 한다.

시스템은 **항상** 탭 라벨을 한국어로 표시해야 한다:
- Reading -> "독해"
- Grammar -> "문법"
- Vocabulary -> "어휘"

**WHEN** 독해(Reading) 패널이 활성화되면, **THEN** `content` 필드의 한국어 Markdown을 ReactMarkdown으로 렌더링해야 한다.

**WHEN** 문법(Grammar) 패널이 활성화되면, **THEN** `content` 필드의 한국어 Markdown을 ReactMarkdown으로 렌더링해야 한다.

**WHEN** 어휘(Vocabulary) 패널이 활성화되면, **THEN** 각 `VocabularyWordEntry`의 `content` 필드를 ReactMarkdown으로 렌더링해야 한다.

시스템은 기존 구조화된 결과 렌더링 로직(GrammarIssue 목록, VocabularyWord 테이블 등)을 **제거**해야 한다.

### R6: 레벨 지시문 재작성 (Level Instructions Rewrite)

시스템은 **항상** 5단계 레벨 지시문을 한국어 교육학적 설명으로 제공해야 한다.

**WHEN** 레벨이 변경되면, **THEN** 해당 레벨의 한국어 교육 지시문이 각 에이전트 프롬프트에 주입되어야 한다.

시스템은 `level_instructions.yaml` 파일에 한국어 레벨별 지시문을 정의해야 한다:
- Level 1 (초급): 가장 쉬운 설명, 영어 용어 최소화
- Level 2 (입문): 기본 문법 용어 사용, 쉬운 비유
- Level 3 (기초): 표준 교육 설명, 문법 용어 포함
- Level 4 (중급): 상세 분석, 시험 포인트 포함
- Level 5 (고급): 전문적 분석, 고급 문법 개념, 대학 수준

### R7: Markdown 출력 정규화 (LLM Output Post-Processing)

**WHEN** LLM이 에이전트 응답을 생성하면, **THEN** 시스템은 정규화 함수를 통해 잘못된 헤더 형식을 올바른 Markdown 헤더로 변환해야 한다.

**WHERE** 정규화가 적용되면, 시스템은 **항상** 다음 패턴을 변환해야 한다:

**Reading/Grammar 에이전트 (`### 문장 N` 정규화)**:
- `**문장 N**`, `**문장 N**:`, `문장 N:`, `## 문장 N`, `#### 문장 N` → `### 문장 N`
- `**단위별 해석**:`, `**단위별 해석**`, `단위별 해석:` → `#### 단위별 해석`
- `**자연스러운 해석**:`, `**자연스러운 해석**` → `#### 자연스러운 해석`
- `**읽기 지시**:`, `**읽기 지시**` → `#### 읽기 지시`
- `**문법 포인트**:`, `**문법 포인트**` → `#### 문법 포인트`
- `**왜 이 구조?**:`, `**왜 이 구조?**` → `#### 왜 이 구조?`
- `**한국어와의 차이**:`, `**한국어와의 차이**` → `#### 한국어와의 차이`
- `**시험 포인트**:`, `**시험 포인트**` → `#### 시험 포인트`

**Vocabulary 에이전트 (`## [단어]` 정규화)**:
- `### [단어]`, `#### [단어]` (영어 단어명, 숫자/한국어 아닌 것) → `## [단어]`
- `**단어**:`, `**단어**` (영어 단어명) → `## 단어`
- `**1. 기본 뜻**:`, `1. 기본 뜻:` → `### 1. 기본 뜻`
- `**2. 문장 속 의미**:`, `2. 문장 속 의미:` → `### 2. 문장 속 의미`
- `**3. 핵심 의미 이미지**:`, `3. 핵심 의미 이미지:` → `### 3. 핵심 의미 이미지`
- `**4. 어원...**:`, `4. 어원...:` → `### 4. 어원 (PIE 어근까지)`
- `**5. 같은 어원 파생 단어...**:`, `5. 같은 어원 파생 단어...:` → `### 5. 같은 어원 파생 단어 (최소 3개)`
- `**6. 기억 연결 팁**:`, `6. 기억 연결 팁:` → `### 6. 기억 연결 팁`

**WHILE** 정규화가 실행되면, 시스템은 **항상** 헤더 바로 다음 줄이 비어있지 않으면 빈 줄을 삽입해야 한다.

시스템은 정규화를 **항상** 각 에이전트 LLM 호출 직후, 결과를 state에 저장하기 전에 적용해야 한다.

**IF** 정규화 중 예외가 발생하면, **THEN** 시스템은 원본 content를 그대로 반환해야 한다 (정규화 실패가 에이전트 응답을 중단시켜서는 안 된다).

---

## 4. Specifications (S)

### 4.1 Backend File Changes

#### 4.1.1 Foundation Files (2)

| File          | Change Type | Description                                    |
|---------------|-------------|------------------------------------------------|
| `schemas.py`  | Major Rewrite | SentenceEntry, SupervisorAnalysis, VocabularyWordEntry 추가; ReadingResult/GrammarResult를 content 기반으로 변경 |
| `state.py`    | Modify | supervisor_analysis 필드 추가, result 타입 업데이트 |

#### 4.1.2 Prompt Infrastructure Files (6)

| File                      | Change Type | Description                                |
|---------------------------|-------------|---------------------------------------------|
| `prompts.py`              | Modify      | 새 프롬프트 파일 로딩 로직 추가             |
| `level_instructions.yaml` | Rewrite     | 한국어 교육학적 레벨 지시문 전면 재작성     |
| `prompts/supervisor.md`   | Rewrite     | 한국어 사전 분석 프롬프트 (문장 분리 + 난이도)  |
| `prompts/vocabulary_tutor.md` | Rewrite | 6단계 어원 네트워크 프롬프트              |
| `prompts/grammar_tutor.md`| Rewrite     | 4단계 구조 이해 프롬프트 (슬래시 읽기 포함) |
| `prompts/reading_tutor.md`| Rewrite     | 4단계 읽기 훈련 프롬프트 (슬래시 읽기 중심) |

#### 4.1.3 Agent Files (4)

| File                 | Change Type | Description                                    |
|----------------------|-------------|------------------------------------------------|
| `agents/supervisor.py` | Major Rewrite | 순수 라우터에서 LLM 사전 분석기로 전환 (Claude Haiku) |
| `agents/vocabulary.py` | Modify      | 모델 Haiku->Sonnet, 새 프롬프트 적용, 결과 스키마 변경 |
| `agents/grammar.py`    | Modify      | 새 프롬프트 적용, 결과 스키마 content 기반으로 변경 |
| `agents/reading.py`    | Modify      | 새 프롬프트 적용, 결과 스키마 content 기반으로 변경 |

#### 4.1.4 Utility Files (2) — R7 신규

| File                                  | Change Type | Description                                         |
|---------------------------------------|-------------|-----------------------------------------------------|
| `utils/markdown_normalizer.py`        | New         | LLM 출력 Markdown 정규화 유틸리티 (reading/grammar/vocabulary 각 함수 제공) |
| `tests/unit/test_markdown_normalizer.py` | New      | 정규화 함수 단위 테스트 (각 패턴별 케이스 포함)     |

### 4.2 Frontend File Changes

#### 4.2.1 Types and Hooks (2)

| File                          | Change Type | Description                              |
|-------------------------------|-------------|------------------------------------------|
| `types/tutor.ts`              | Major Rewrite | content 기반 결과 타입으로 전면 변경      |
| `hooks/use-tutor-stream.ts`   | Modify      | 새 스키마에 맞는 파싱 로직 업데이트       |

#### 4.2.2 Panel Components (4)

| File                                    | Change Type | Description                           |
|-----------------------------------------|-------------|---------------------------------------|
| `components/tutor/reading-panel.tsx`    | Rewrite     | ReactMarkdown 렌더링으로 전환          |
| `components/tutor/grammar-panel.tsx`    | Rewrite     | ReactMarkdown 렌더링으로 전환          |
| `components/tutor/vocabulary-panel.tsx` | Rewrite     | ReactMarkdown 렌더링으로 전환          |
| `components/tutor/tabbed-output.tsx`    | Modify      | 탭 라벨 한국어화 (독해/문법/어휘)       |

#### 4.2.3 Layout Components (2)

| File                                      | Change Type | Description                         |
|-------------------------------------------|-------------|-------------------------------------|
| `components/layout/desktop-layout.tsx`    | Modify      | 새 타입에 맞는 props 조정            |
| `components/mobile/analysis-view.tsx`     | Modify      | 새 타입에 맞는 props 조정            |

### 4.3 Files NOT Changed (Preserved)

| File                    | Reason                                           |
|-------------------------|--------------------------------------------------|
| `graph.py`              | Send() 병렬 dispatch 패턴 유지                   |
| `agents/aggregator.py`  | passthrough 동작이 새 스키마와 호환               |
| `services/streaming.py` | 구조 비의존적 SSE 포맷터 유지                     |
| `routers/tutor.py`      | model_dump() 직렬화 패턴 유지                     |

> **Note**: `models/llm.py`는 v1.1.0 구현 중 `max_tokens` 기본값 버그(1024 제한) 수정을 위해 이미 변경됨. Anthropic 기본값 8192, OpenAI 기본값 4096, timeout 120s.

### 4.4 Dependency Graph

```
schemas.py (R3)
    |
    v
state.py (R3)
    |
    v
prompts/ (R2, R6)                    types/tutor.ts (R3)
    |                                      |
    v                                      v
agents/supervisor.py (R1, R4)        hooks/use-tutor-stream.ts (R3)
agents/reading.py (R2)                    |
agents/grammar.py (R2)                    v
agents/vocabulary.py (R2, R4)        panels (R5)
    |                                tabbed-output.tsx (R5)
    v                                desktop-layout.tsx (R5)
utils/markdown_normalizer.py (R7) <- analysis-view.tsx (R5)
    ^
    |
agents/reading.py (R7 적용)
agents/grammar.py (R7 적용)
agents/vocabulary.py (R7 적용)
    |
    v
[graph.py - unchanged]
```

---

## 5. Traceability

| TAG         | Requirement | Files                                            |
|-------------|-------------|--------------------------------------------------|
| TAG-SUP-01  | R1          | schemas.py, state.py, agents/supervisor.py, prompts/supervisor.md |
| TAG-PROMPT-01 | R2        | prompts/reading_tutor.md, prompts/grammar_tutor.md, prompts/vocabulary_tutor.md, agents/reading.py, agents/grammar.py, agents/vocabulary.py |
| TAG-SCHEMA-01 | R3        | schemas.py, state.py, types/tutor.ts, hooks/use-tutor-stream.ts |
| TAG-MODEL-01 | R4         | agents/supervisor.py, agents/vocabulary.py        |
| TAG-FRONT-01 | R5         | reading-panel.tsx, grammar-panel.tsx, vocabulary-panel.tsx, tabbed-output.tsx, desktop-layout.tsx, analysis-view.tsx |
| TAG-LEVEL-01 | R6         | level_instructions.yaml, prompts.py               |
| TAG-NORM-01  | R7         | utils/markdown_normalizer.py, agents/reading.py, agents/grammar.py, agents/vocabulary.py, tests/unit/test_markdown_normalizer.py |

---

## Implementation Notes (v1.2.1)

### What Was Actually Implemented

This SPEC was successfully completed on 2026-02-23. All requirements R1-R7 have been fully implemented and verified across backend and frontend.

**Backend Implementation Summary:**
- **R1 (Supervisor)**: LLM-powered pre-analyzer using gpt-4o-mini (document parsing, sentence segmentation, difficulty evaluation)
- **R2 (Prompts)**: Comprehensive Korean tutoring prompts for Reading (slash reading), Grammar (structure-based), Vocabulary (etymology network)
- **R3 (Schema)**: New content-based Markdown schema with SupervisorAnalysis, VocabularyWordEntry
- **R4 (Model Upgrade)**: Unified all agents to gpt-4o-mini (from mixed Claude/GPT)
- **R5 (Frontend Rendering)**: ReactMarkdown integration for all panels
- **R6 (Level Instructions)**: 5-level Korean educational framework
- **R7 (Markdown Normalization)**: Post-processing utility with pattern-based header and formatting fixes

**Test Coverage:**
- Backend: 207 tests passing (97% modal consistency)
- Frontend: 97 tests passing with mobile UI
- Coverage: 83% (backend), 91.98% (frontend)

**Cost Impact:**
- **Pre-SPEC-UPDATE-001**: Mixed models (Claude Sonnet + Haiku + GPT-4o/mini) = ~$152/month
- **Post-SPEC-UPDATE-001**: gpt-4o-mini unified = ~$7/month
- **Savings**: 95% cost reduction

**Related Work:**
This implementation also incorporates findings from SPEC-MODEL-001 (LLM model optimization):
- Removed Anthropic/Claude dependency
- Standardized on OpenAI API (gpt-4o-mini)
- Added GLM support framework (for future OCR)
- Environment variables now configuration-driven (no hardcoding)
