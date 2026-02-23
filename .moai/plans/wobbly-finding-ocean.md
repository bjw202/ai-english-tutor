# AI English Tutor Prompt Redesign Plan

## Context

AI English Tutor는 한국 중2 대상 영어 튜터링 앱으로 3개 LLM 에이전트(vocabulary, grammar, reading)로 구성되어 있다. 현재 프롬프트는 영문 분석/평가용("Extract vocabulary", "Identify grammar errors")으로 작성되어 있어 실제 튜터링을 하지 못한다.

사용자가 `my-prompt/`에 검증된 한국어 네이티브 튜터링 프롬프트를 준비했다:
- **Vocabulary**: 어원 네트워크 기반 의미 작동 원리 학습
- **Grammar**: "왜?" 중심 구조 이해 해설
- **Reading**: 슬래시 직독 끊기 + 읽기 지시 훈련

**Goal**: 프롬프트 전면 재작성 + 슈퍼바이저 사전분석 도입으로 품질/효율 동시 개선.

---

## Design Decisions (User Confirmed)

1. **Few-shot 제외**: 규칙/구조만 레퍼런스 수준으로 상세히 기술. 예시 출력 미포함.
2. **Grammar/Reading 슬래시 끊기 겹침 허용**: 두 에이전트 모두 슬래시 끊기 포함하되 초점이 다름.
3. **프롬프트 한국어 작성**: 모든 시스템 프롬프트는 한국어로 작성.
4. **프롬프트 상세도**: 레퍼런스의 시스템 프롬프트 수준으로 규칙/구조/금지사항 상세 기술.
5. **LLM 사전분석 슈퍼바이저**: Haiku로 문장 분리 + 난이도 판단 + 레벨별 초점 선정 후 3개 에이전트에 전달.

---

## Implementation Plan

### Phase 1: Backend Schema Redesign

**File**: `backend/src/tutor/schemas.py`

#### 1-1. Supervisor 출력 스키마 (신규)

```python
class SentenceEntry(BaseModel):
    number: int              # 문장 번호 (1-indexed)
    text: str                # 영어 원문

class SupervisorAnalysis(BaseModel):
    sentences: list[SentenceEntry]          # 분리된 문장 목록
    text_difficulty: int                    # 텍스트 난이도 (1-5)
    effective_level: int                    # 조정된 설명 레벨
    vocabulary_focus: list[str]             # 설명할 단어 후보
    grammar_focus: list[int]               # 문법 설명 집중 문장 번호
    teaching_notes: str                    # 에이전트에게 전달할 교수 지침
```

#### 1-2. 에이전트 출력 스키마 (변경)

Hybrid approach: 인덱스 메타데이터 + `content` 마크다운 필드.

```python
class VocabularyWordEntry(BaseModel):
    term: str                # 영어 단어
    basic_meaning: str       # 한국어 한 줄 뜻

class VocabularyResult(BaseModel):
    words: list[VocabularyWordEntry]   # 인덱스
    content: str                       # 전체 한국어 마크다운 어휘 해설

class GrammarResult(BaseModel):
    sentence_count: int                # 분석 문장 수
    content: str                       # 전체 한국어 마크다운 문법 해설

class ReadingResult(BaseModel):
    sentence_count: int                # 분석 문장 수
    content: str                       # 전체 한국어 마크다운 독해 훈련
```

### Phase 2: Supervisor Redesign

현재 supervisor_node는 LLM 호출 없는 단순 라우터. LLM 사전분석 기능으로 업그레이드.

#### 2-1. `backend/src/tutor/prompts/supervisor.md` (전면 재작성)

```
Role: 영어 지문 사전 분석기
Input: {text}, {level}
Output: SupervisorAnalysis (structured)

Tasks:
1. 지문을 문장 단위로 분리 (번호 부여)
2. 텍스트 난이도 판단 (1-5)
3. 학생 레벨 vs 텍스트 난이도 비교 → effective_level 결정
4. vocabulary_focus: 해당 레벨에서 설명이 필요한 단어 선정
5. grammar_focus: 문법적으로 유의미한 문장 번호 선정
6. teaching_notes: 3개 에이전트에게 전달할 교수 방향 요약
```

effective_level 로직:
- 텍스트 난이도 ≈ 학생 레벨 → effective_level = level (정상)
- 텍스트 난이도 > 학생 레벨+1 → effective_level = level (기초 집중, 핵심만)
- 텍스트 난이도 < 학생 레벨-1 → effective_level = level (심화 집중, 고급 패턴)

#### 2-2. `backend/src/tutor/agents/supervisor.py` (전면 재작성)

```python
async def supervisor_node(state: TutorState) -> dict:
    # 1. Haiku LLM 호출로 텍스트 사전 분석
    llm = get_llm("claude-haiku-4-5")
    prompt = render_prompt("supervisor.md", text=..., level=...)
    analysis = llm.with_structured_output(SupervisorAnalysis).ainvoke(prompt)

    # 2. 분석 결과를 state에 저장
    return {
        "supervisor_analysis": analysis,
        "task_type": state.get("task_type", "analyze")
    }
```

#### 2-3. `backend/src/tutor/state.py` (필드 추가)

```python
class TutorState(TypedDict):
    # ... existing fields ...
    supervisor_analysis: NotRequired[SupervisorAnalysis | None]  # 신규
```

#### 2-4. `backend/src/tutor/graph.py` (변경 없음)

그래프 구조 자체는 변경 없음:
- START → supervisor → route_by_task → [reading, grammar, vocabulary] → aggregator → END
- supervisor_node가 이제 LLM을 호출하고 state에 분석 결과를 저장할 뿐

### Phase 3: Prompt Rewrite (4 files)

각 프롬프트에 `{supervisor_analysis}` 변수 추가. 슈퍼바이저가 전달한 문장 목록/초점 정보를 활용.

#### 3-1. `backend/src/tutor/prompts/vocabulary.md`

Based on `my-prompt/vocabulary-prompt.md`:

```
너는 한국 중학생을 가르치는 영어 어휘 전문 강사다.
목표는 단어 뜻 암기가 아니라 **의미 작동 원리 이해**와 **어원 네트워크 기반 장기 기억 형성**이다.

## 사전 분석 결과
{supervisor_analysis}

## 학생 수준
학생 레벨: {level}, 적용 레벨: {effective_level}
{level_instructions}

## 분석할 지문
{text}

## 단어 선정 원칙
* 사전 분석에서 제시된 vocabulary_focus 단어를 우선 설명한다.
* 추가로 필요한 단어가 있으면 선정할 수 있다.
* 추상적 의미, 일상 의미와 문장 속 의미가 다른 단어 우선.
* 단순 명사(apple, book 등)는 제외.

## 각 단어 해설 형식 (반드시 6단계 구조 유지)
① 기본 뜻 - 한 줄 명확
② 문장 속 의미 작동 설명 - "왜 이 의미인가"
③ 핵심 의미 이미지 - 한 단어/한 문장
④ 어원 설명 (필수) - PIE 어근, 의미 변화 흐름
⑤ 같은 어원 파생 단어 (최소 3개) - 공통 핵심 이미지 연결
⑥ 기억 연결 팁 - 어근 네트워크 기억법

## 설명 톤
[레퍼런스 수준으로 상세 기술]

## 절대 금지
[레퍼런스 수준으로 상세 기술]
```

#### 3-2. `backend/src/tutor/prompts/grammar.md`

Based on `my-prompt/grammar-prompt.md`, adapted to 중2 default:

```
너는 한국 중학생을 가르치는 영어 문법 전문 강사다.
목표는 단순 문법 나열이 아니라, "구조 이해 중심 문법 해설"이다.

## 사전 분석 결과
{supervisor_analysis}

## 학생 수준
학생 레벨: {level}, 적용 레벨: {effective_level}
{level_instructions}

## 분석할 지문
{text}

## 해설 원칙
1. 사전 분석의 sentences 목록 번호를 그대로 사용한다.
2. grammar_focus 문장을 우선 상세 분석한다.
3. 각 문장은 아래 4단계 구조:
   ① 문법 포인트 (레벨에 맞는 문법 용어)
   ② 왜 이 구조를 썼는가?
   ③ 한국어와의 구조 차이
   ④ 시험 포인트 (선택)
4. 슬래시 끊기 + 단위별 한국어 해석 포함
5. "왜?" 반드시 설명

## 절대 금지
[레퍼런스 수준으로 상세 기술]
```

#### 3-3. `backend/src/tutor/prompts/reading.md`

Based on `my-prompt/reading-prompt.md`:

```
너는 한국 중학생을 가르치는 영어 독해 전문 강사다.
목표는 "문장 독해력 훈련"이다.

## 사전 분석 결과
{supervisor_analysis}

## 학생 수준
학생 레벨: {level}, 적용 레벨: {effective_level}
{level_instructions}

## 분석할 지문
{text}

## 형식 — 문장당 반드시 이 구조 유지
1. 사전 분석의 sentences 목록 번호를 그대로 사용한다.
2. 각 문장마다:
   - 영어식 직독 끊기 (슬래시 / 로 끊기)
   - 영어 단위별 한국어 (영어 순서 유지)
   - 자연스러운 한국어 해석
   - 읽기 지시 (3줄 이내, 지시형 말투)

## 직독 끊기 규칙, 읽기 지시 규칙
[레퍼런스 수준으로 상세 기술]

## 절대 금지
[레퍼런스 수준으로 상세 기술]
```

#### 3-4. `backend/src/tutor/prompts/level_instructions.yaml`

Complete rewrite in Korean, aligned with tutoring pedagogy:

- Level 1 (초등 고학년): 쉬운 어원만, 주어/동사 수준, 격려 톤
- Level 2 (중1): 라틴어/그리스어까지, 1~3형식, 한국어 지원 충분히
- Level 3 (중2-3, default): PIE 어근 포함, 2~5형식 용어, "왜?" 강조
- Level 4 (고등): 가정법/도치/강조구문, 수능 시험 포인트
- Level 5 (수능/토익): 학술 어휘, 수능 전략 연결

### Phase 4: Agent Node Updates (3 files)

3개 에이전트 모두 `state["supervisor_analysis"]`를 프롬프트에 주입하도록 변경.

#### 4-1. `backend/src/tutor/agents/vocabulary.py`

- `supervisor_analysis`를 state에서 가져와 프롬프트 변수로 전달
- 새 스키마 import (`VocabularyResult`, `VocabularyWordEntry`)
- `_parse_vocabulary_from_raw` fallback 제거/간소화
- `json_instruction` append 제거

#### 4-2. `backend/src/tutor/agents/grammar.py`

- `supervisor_analysis`를 state에서 가져와 프롬프트 변수로 전달
- 새 스키마 import (`GrammarResult`)

#### 4-3. `backend/src/tutor/agents/reading.py`

- `supervisor_analysis`를 state에서 가져와 프롬프트 변수로 전달
- 새 스키마 import (`ReadingResult`)

#### 4-4. `backend/src/tutor/prompts.py`

- `render_prompt()`에 `supervisor_analysis`, `effective_level` 변수 지원 추가
- SupervisorAnalysis 객체를 문자열로 포매팅하는 헬퍼 함수 추가

### Phase 5: Frontend Updates

#### 5-1. `src/types/tutor.ts`

```typescript
interface VocabularyWordEntry { term: string; basic_meaning: string; }
interface VocabularyResult { words: VocabularyWordEntry[]; content: string; }
interface GrammarResult { sentence_count: number; content: string; }
interface ReadingResult { sentence_count: number; content: string; }
```

#### 5-2. `src/hooks/use-tutor-stream.ts`

- 모든 에이전트에서 `data.content` 추출로 통일
- `formatVocabularyData` 헬퍼 제거

#### 5-3. Panel Components (3 files)

- `reading-panel.tsx`: `ReactMarkdown`으로 `content` 렌더링
- `grammar-panel.tsx`: `ReactMarkdown`으로 `content` 렌더링
- `vocabulary-panel.tsx`: 단어 Badge 인덱스 + `ReactMarkdown`으로 `content` 렌더링

#### 5-4. Layout Components

- `desktop-layout.tsx`: stream state → panel props 매핑 업데이트
- `analysis-view.tsx`: 동일 업데이트
- `tabbed-output.tsx`: 탭 라벨 한국어로 (독해/문법/어휘)

### Phase 6: Test Updates

- `backend/tests/unit/test_schemas.py`: 새 스키마 필드 테스트
- `backend/tests/unit/test_agents.py`: mock 반환값 업데이트 (supervisor_analysis 포함)
- Frontend component tests: 새 인터페이스에 맞춰 테스트 데이터 업데이트

---

## Critical Files Summary

| # | File | Change |
|---|------|--------|
| 1 | `backend/src/tutor/schemas.py` | SupervisorAnalysis 신규 + 3개 Result 스키마 변경 |
| 2 | `backend/src/tutor/prompts/supervisor.md` | LLM 사전분석 프롬프트로 전면 재작성 |
| 3 | `backend/src/tutor/prompts/vocabulary.md` | 한국어 어원 네트워크 프롬프트 전면 재작성 |
| 4 | `backend/src/tutor/prompts/grammar.md` | 한국어 구조 이해 프롬프트 전면 재작성 |
| 5 | `backend/src/tutor/prompts/reading.md` | 한국어 읽기 훈련 프롬프트 전면 재작성 |
| 6 | `backend/src/tutor/prompts/level_instructions.yaml` | 한국어 레벨 지침 전면 재작성 |
| 7 | `backend/src/tutor/agents/supervisor.py` | Haiku LLM 호출 + SupervisorAnalysis 생성 |
| 8 | `backend/src/tutor/agents/vocabulary.py` | supervisor_analysis 주입 + 스키마 변경 |
| 9 | `backend/src/tutor/agents/grammar.py` | supervisor_analysis 주입 + 스키마 변경 |
| 10 | `backend/src/tutor/agents/reading.py` | supervisor_analysis 주입 + 스키마 변경 |
| 11 | `backend/src/tutor/prompts.py` | supervisor_analysis 포매팅 헬퍼 추가 |
| 12 | `backend/src/tutor/state.py` | supervisor_analysis 필드 추가 |
| 13 | `src/types/tutor.ts` | TypeScript 인터페이스 재작성 |
| 14 | `src/hooks/use-tutor-stream.ts` | SSE 파싱 → content 추출로 통일 |
| 15 | `src/components/tutor/*-panel.tsx` (3) | ReactMarkdown 렌더링 |
| 16 | `src/components/layout/desktop-layout.tsx` | 데이터 매핑 업데이트 |
| 17 | `src/components/mobile/analysis-view.tsx` | 데이터 매핑 업데이트 |

---

## Reusable (No Changes Needed)

- `backend/src/tutor/graph.py`: LangGraph 워크플로우 구조 유지 (supervisor → Send → aggregator)
- `backend/src/tutor/models/llm.py`: `get_llm()` 팩토리 그대로 사용
- `backend/src/tutor/agents/aggregator.py`: 패스스루 집계 유지
- `vocabulary-panel.tsx:61-74`: 기존 ReactMarkdown 폴백 패턴 재활용

---

## Supervisor Value Proposition

| 효과 | 설명 |
|------|------|
| 일관성 | 3개 에이전트가 동일한 문장 번호/경계 사용 |
| 토큰 절약 | 에이전트가 독립적 텍스트 분석 생략, 초점 영역만 처리 |
| 레벨 실질화 | 레벨이 단순 텍스트 주입이 아닌 실제 분석 범위/깊이 제어 |
| 품질 향상 | 단어 선정, 문법 초점이 레벨에 맞게 사전 필터링 |
| 비용 | Haiku 1회 호출 ~1000 토큰 (낮음) |

---

## Additional Notes

- **Model concern**: Vocabulary가 Haiku 사용 중. 풍부한 한국어 어원 설명에 Sonnet이 더 적합할 수 있음. 품질 확인 후 결정.
- **3 agents differentiation**:
  - Reading = HOW to read (읽기 훈련, 읽기 지시)
  - Grammar = WHY the structure (구조 이해, "왜?")
  - Vocabulary = WHAT words mean (의미 작동 원리, 어원 네트워크)

---

## Verification

1. **Unit tests**: `pytest backend/tests/` - 모든 스키마/에이전트 테스트 통과
2. **Supervisor test**: SupervisorAnalysis가 올바른 문장 분리/난이도/초점 생성하는지 확인
3. **Prompt rendering**: `render_prompt()`에 supervisor_analysis 포함 5개 레벨 렌더링 확인
4. **End-to-end**: Masakichi 지문을 level 3으로 전송, `my-prompt/` 레퍼런스와 품질 비교
5. **Frontend**: ReactMarkdown이 슬래시 끊기 한국어 콘텐츠를 정상 렌더링하는지 확인
6. **Level variation**: Level 1, 3, 5로 테스트하여 설명 깊이 차이 검증
7. **Consistency check**: 3개 에이전트 출력에서 동일 문장 번호 사용 확인
