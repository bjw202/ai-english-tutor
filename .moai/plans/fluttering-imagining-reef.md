# SPEC-MODEL-001: LLM 모델 최적화 계획

## Context

AI English Tutor는 현재 Claude(Anthropic) + GPT(OpenAI) 혼합 모델 구조를 사용한다.
두 가지 핵심 문제가 존재한다:

1. **비용 문제**: Reading/Vocabulary 에이전트가 claude-sonnet-4-5를 사용하여 월 ~$150+ 발생 (1,000 req 기준)
2. **설정 버그**: `config.py`에 `SUPERVISOR_MODEL`, `GRAMMAR_MODEL`, `READING_MODEL`, `VOCABULARY_MODEL`이 정의되어 있으나 **에이전트들이 이 값을 전혀 사용하지 않고 모델명을 하드코딩**

목표: Claude 모델 완전 제거 + gpt-4o-mini 통일 + GLM 지원 추가 + 설정 버그 수정으로 95% 비용 절감.

---

## 정밀 비용 분석 (--ultrathink 결과)

### 현재 비용 (월 1,000 요청 기준)

| 에이전트 | 모델 | Input | Output | 월 비용 |
|---------|------|-------|--------|---------|
| Supervisor | claude-haiku-4-5 | 700K × $0.25/M | 300K × $1.25/M | $0.55 |
| Grammar | gpt-4o | 1.5M × $2.50/M | 2.5M × $10.00/M | $28.75 |
| Reading | claude-sonnet-4-5 | 1.7M × $3.00/M | 4.0M × $15.00/M | $65.10 |
| Vocabulary | claude-sonnet-4-5 | 2.0M × $3.00/M | 3.5M × $15.00/M | $58.50 |
| **합계** | | | | **$152.90** |

### 최적화 후 비용 (gpt-4o-mini, $0.15/M input, $0.60/M output)

| 에이전트 | 모델 | Input | Output | 월 비용 |
|---------|------|-------|--------|---------|
| Supervisor | gpt-4o-mini | 700K × $0.15/M | 300K × $0.60/M | $0.29 |
| Grammar | gpt-4o-mini | 1.5M × $0.15/M | 2.5M × $0.60/M | $1.73 |
| Reading | gpt-4o-mini | 1.7M × $0.15/M | 4.0M × $0.60/M | $2.66 |
| Vocabulary | gpt-4o-mini | 2.0M × $0.15/M | 3.5M × $0.60/M | $2.40 |
| **합계** | | | | **$7.08** |

**절감액: ~$145.82/월 (95.4% 절감, 연간 ~$1,750)**

### 왜 gpt-4o-mini인가

튜터 설명 에이전트 요구사항: "정확성 필요, 고도 추론 불필요, 친절한 설명 글쓰기 중요"

- **문법**: 패턴 인식 + 한국어 설명 글쓰기 → mini 충분
- **어휘**: 어원/접두어 사실 지식 + 설명 → mini 충분
- **독해**: 직독직해 구문 분리 (규칙 기반) → mini 충분
- **품질 업그레이드 경로**: 특정 에이전트 품질 부족 시 env var 한 줄 변경으로 gpt-4o 전환 가능

---

## EARS 요구사항

| # | 요구사항 | 형식 |
|---|---------|------|
| R1 | WHEN 환경변수 `SUPERVISOR_MODEL`이 설정될 때, Supervisor 에이전트는 해당 모델을 사용해야 한다 | Event-driven |
| R2 | WHEN 환경변수가 없을 때, 각 에이전트는 config.py의 기본값(gpt-4o-mini)을 사용해야 한다 | Event-driven |
| R3 | WHEN `get_llm()`에 "claude-"로 시작하는 모델명이 전달될 때, `ValueError`를 발생시켜야 한다 | Event-driven |
| R4 | WHEN `get_llm()`에 "glm-"로 시작하는 모델명이 전달될 때, Zhipu AI 엔드포인트를 사용하는 `ChatOpenAI` 인스턴스를 반환해야 한다 | Event-driven |
| R5 | WHERE `GLM_API_KEY`가 환경에 없을 경우, GLM 모델 요청 시 명확한 오류 메시지를 제공해야 한다 | State-driven |
| R6 | WHILE 서버가 실행 중인 경우, `ANTHROPIC_API_KEY` 없이도 정상 동작해야 한다 | Continuous |
| R7 | WHEN Reading/Vocabulary 에이전트가 응답을 생성할 때, 최대 6,144 토큰까지 출력을 허용해야 한다 | Event-driven |

---

## 수용 기준 (Acceptance Criteria)

- [ ] `ANTHROPIC_API_KEY` 환경변수 없이 `uvicorn` 서버가 정상 시작됨
- [ ] `get_llm("claude-sonnet-4-5")` 호출 시 `ValueError: Claude models are not supported. Use OpenAI or GLM models.` 발생
- [ ] `get_llm("glm-4v-flash")` 호출 시 `base_url="https://open.bigmodel.cn/api/paas/v4/"` 설정된 `ChatOpenAI` 반환
- [ ] `GRAMMAR_MODEL=gpt-4o` 환경변수 설정 시 Grammar 에이전트가 gpt-4o 사용
- [ ] 기존 단위 테스트 100% 통과 (test_llm.py, test_agents.py, test_schemas.py 등)
- [ ] 신규 테스트 커버리지 85% 이상

---

## 기술적 접근 방식

### GLM 연동: ChatOpenAI + base_url (추가 패키지 불필요)

GLM API는 OpenAI 호환 형식을 제공하므로 `ChatOpenAI`에 `base_url`과 `api_key`만 교체:

```python
# llm.py 변경사항 예시
if model_name.startswith("glm-"):
    return ChatOpenAI(
        model=model_name,
        timeout=timeout,
        max_retries=2,
        max_tokens=max_tokens if max_tokens is not None else 4096,
        api_key=settings.GLM_API_KEY,
        base_url="https://open.bigmodel.cn/api/paas/v4/",
    )
```

### 에이전트 수정 패턴 (4개 동일)

```python
# 변경 전 (예: grammar.py)
llm = get_llm("gpt-4o")

# 변경 후
from tutor.config import get_settings
settings = get_settings()
llm = get_llm(settings.GRAMMAR_MODEL)
```

---

## 구현 계획 (TDD Hybrid 방식)

> 새 코드(GLM 지원)는 TDD, 기존 코드 수정(에이전트 config 연동)은 DDD

### Phase 1: RED - 실패 테스트 먼저 작성

**`backend/tests/unit/test_llm.py` 추가:**

```python
def test_get_llm_claude_raises_value_error():
    """Claude 모델 요청 시 ValueError"""
    with pytest.raises(ValueError, match="Claude models are not supported"):
        get_llm("claude-sonnet-4-5")

def test_get_llm_glm_returns_chatmodel(mock_settings):
    """GLM 모델 요청 시 ChatOpenAI (GLM base_url) 반환"""
    mock_settings.GLM_API_KEY = "test-glm-key"
    llm = get_llm("glm-4v-flash")
    assert isinstance(llm, ChatOpenAI)

def test_get_llm_glm_uses_zhipu_endpoint(mock_settings):
    """GLM 모델의 base_url이 Zhipu AI 엔드포인트"""
    mock_settings.GLM_API_KEY = "test-key"
    llm = get_llm("glm-4v")
    assert "bigmodel.cn" in str(llm.openai_api_base)
```

**`backend/tests/unit/test_agents.py` 추가:**

```python
def test_grammar_agent_uses_config_model(mocker):
    """Grammar 에이전트가 GRAMMAR_MODEL config 사용"""
    mock_get_llm = mocker.patch("tutor.agents.grammar.get_llm")
    # 에이전트 초기화 트리거
    mock_get_llm.assert_called_with(settings.GRAMMAR_MODEL)
# Supervisor, Reading, Vocabulary에도 동일 패턴
```

### Phase 2: GREEN - 구현

**수정 파일 및 변경 사항:**

#### `backend/src/tutor/config.py`

```python
# 변경사항
SUPERVISOR_MODEL: str = "gpt-4o-mini"    # 유지
GRAMMAR_MODEL: str = "gpt-4o-mini"       # gpt-4o → 변경
READING_MODEL: str = "gpt-4o-mini"       # claude-sonnet-4-5 → 변경
VOCABULARY_MODEL: str = "gpt-4o-mini"    # claude-haiku-4-5 → 변경 (config와 일치)
OCR_MODEL: str = "glm-4v-flash"          # 신규 추가

# 제거
ANTHROPIC_API_KEY: str  # Required → 완전 제거

# 추가
GLM_API_KEY: Optional[str] = None        # OCR용, Optional
```

#### `backend/src/tutor/models/llm.py`

- `if model_name.startswith("claude-")` 블록 → ValueError 블록으로 교체
- `ChatAnthropic` import 제거
- `if model_name.startswith("glm-")` 블록 추가
- `anthropic` 라이브러리 import 제거

#### 에이전트 4개 (supervisor.py, grammar.py, reading.py, vocabulary.py)

- 각 파일에서 하드코딩된 모델명 제거
- `from tutor.config import get_settings` 추가
- `get_llm(settings.SUPERVISOR_MODEL)` 등으로 변경
- Reading/Vocabulary: `max_tokens=6144` 명시 (기존 8192 → 6144로 조정, mini 모델 적정값)

### Phase 3: REFACTOR

- `langchain-anthropic` 의존성 `pyproject.toml`에서 제거
- 오류 메시지 명확화: `"Claude models are not supported. Configure GRAMMAR_MODEL to use an OpenAI or GLM model."`
- `.env.example` 업데이트: ANTHROPIC_API_KEY 주석화, GLM_API_KEY 추가

---

## 리스크 및 대응

| 리스크 | 대응 |
|--------|------|
| gpt-4o-mini 설명 품질 부족 | env var 한 줄 변경으로 특정 에이전트만 gpt-4o 업그레이드 |
| ChatOpenAI base_url 파라미터 버전 이슈 | 구현 시 LangChain 버전 확인 후 `openai_api_base` vs `base_url` 선택 |
| max_tokens 응답 잘림 | Reading/Vocabulary에 6144 명시, 필요 시 조정 |
| 기존 테스트 Mock 패턴 깨짐 | 에이전트 수정과 테스트 동시 업데이트 |

---

## 검증 절차

1. **단위 테스트**: `cd backend && python -m pytest tests/unit/ -v`
2. **커버리지**: `python -m pytest tests/unit/ --cov=tutor --cov-report=term-missing`
3. **서버 시작**: `ANTHROPIC_API_KEY` 없이 `uvicorn` 실행 → 정상 시작 확인
4. **API 호출**: 문법/어휘/독해 각 엔드포인트 실제 호출 → gpt-4o-mini 응답 확인
5. **통합 테스트**: `python -m pytest tests/integration/ -v`

---

## 제외 범위 (Out of Scope)

- GLM OCR 서비스 구현 (`backend/src/tutor/services/glm_ocr.py`) → SPEC-GLM-001
- 이미지 업로드 422 에러 수정 → 별도 작업
- 프론트엔드 변경 없음
- 모델 품질 A/B 테스트 자동화 → 추후 계획

---

## 수정 대상 파일 요약

| 파일 | 변경 유형 | 주요 변경 |
|------|---------|---------|
| `backend/src/tutor/config.py` | 수정 | 기본값 변경, ANTHROPIC 제거, GLM 추가 |
| `backend/src/tutor/models/llm.py` | 수정 | Claude 제거, GLM 지원 추가 |
| `backend/src/tutor/agents/supervisor.py` | 수정 | settings.SUPERVISOR_MODEL 사용 |
| `backend/src/tutor/agents/grammar.py` | 수정 | settings.GRAMMAR_MODEL 사용 |
| `backend/src/tutor/agents/reading.py` | 수정 | settings.READING_MODEL 사용 |
| `backend/src/tutor/agents/vocabulary.py` | 수정 | settings.VOCABULARY_MODEL 사용 |
| `backend/tests/unit/test_llm.py` | 수정 | Claude 오류 테스트, GLM 테스트 추가 |
| `backend/tests/unit/test_agents.py` | 수정 | config 기반 모델 사용 테스트 |
| `.env.example` | 수정 | ANTHROPIC 제거, GLM 추가 |
