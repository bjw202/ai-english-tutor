# LLM 모델 GLM 마이그레이션 계획

## Context

이 프로젝트는 현재 OpenAI (GPT-4o, GPT-4o-mini)와 Anthropic (Claude Sonnet 4.5, Claude Haiku 4.5) 모델을 사용하여 AI 영어 교육 서비스를 제공합니다. 비용 절감과 한국어 처리 최적화를 위해 Zhipu AI의 GLM 모델로 마이그레이션을 계획합니다.

### 현재 사용 모델

| Agent | 모델 | 용도 |
|-------|------|------|
| Supervisor | gpt-4o-mini | 텍스트 사전 분석 |
| Grammar | gpt-4o | 문법 설명 생성 |
| Reading | claude-sonnet-4-5 | 독해 훈련 생성 |
| Vocabulary | claude-haiku-4-5 | 어휘 어원 설명 |

### 비용 비교 (대략적)

| 모델 | 입력 가격 | 출력 가격 |
|------|----------|----------|
| GPT-4o | $3/1M tokens | $15/1M tokens |
| Claude Sonnet 4.5 | $3/1M tokens | $15/1M tokens |
| GLM-4-Flash | ¥0.1/1K tokens | ¥0.1/1K tokens |
| GLM-4-Plus | ¥0.5/1K tokens | ¥0.5/1K tokens |

GLM-4-Flash는 약 70-90% 더 저렴하며, 한국어 처리에 최적화되어 있습니다.

---

## 추천 접근법

LangChain의 `ChatOpenAI` 클래스는 OpenAI 호환 API를 지원합니다. Zhipu AI의 GLM API는 OpenAI 형식과 호환되므로, `base_url` 파라미터만 변경하여 기존 코드 구조를 유지하면서 GLM 모델을 사용할 수 있습니다.

### 기술적 이점

1. **최소 코드 변경**: `ChatOpenAI`에 `base_url`과 `api_key`만 전달
2. **기존 구조 유지**: LangChain 추상화 계층 활용
3. **쉬운 롤백**: 환경 변수만으로 원래 모델로 복귀 가능
4. **점진적 마이그레이션**: 일부 agent만 GLM으로 테스트 가능

---

## 모델 매핑

| 기존 모델 | GLM 대체 모델 | 비고 |
|----------|--------------|------|
| gpt-4o-mini | glm-4-flash | 빠르고 저렴, 사전 분석용 |
| gpt-4o | glm-4-plus | 고성능, 복잡한 생성용 |
| claude-haiku-4-5 | glm-4-flash | 빠른 응답 |
| claude-sonnet-4-5 | glm-4-plus | 고품질 생성 |

---

## 수정 파일 목록

### 1. `backend/pyproject.toml`

**변경 사항**: zhipuai 의존성 추가

```toml
dependencies = [
    # 기존 의존성들...
    "langchain-openai>=0.3.0,<0.4.0",
    "langchain-anthropic>=0.3.0,<0.4.0",

    # 신규 추가
    "zhipuai>=2.0.0,<3.0.0",
]
```

---

### 2. `backend/src/tutor/config.py`

**변경 사항**: GLM API 키 필드와 GLM 모델 설정 추가

```python
class Settings(BaseSettings):
    # 기존 LLM API Keys
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str

    # 신규: GLM API Key
    GLM_API_KEY: str = ""  # 선택사항: GLM 사용 시에만 필요

    # Model Configuration (기존)
    SUPERVISOR_MODEL: str = "gpt-4o-mini"
    READING_MODEL: str = "claude-sonnet-4-5"
    GRAMMAR_MODEL: str = "gpt-4o"
    VOCABULARY_MODEL: str = "claude-haiku-4-5"

    # 신규: GLM 전용 설정
    GLM_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4/"
```

---

### 3. `backend/src/tutor/models/llm.py`

**변경 사항**: GLM 모델 지원 추가

```python
from langchain_openai import ChatOpenAI

def get_llm(model_name: str, max_tokens: int | None = None, timeout: int = 120) -> BaseChatModel:
    settings = get_settings()

    # GLM 모델 지원 (신규)
    if model_name.startswith("glm-"):
        return ChatOpenAI(
            model=model_name,
            base_url=settings.GLM_BASE_URL,
            api_key=settings.GLM_API_KEY,
            timeout=timeout,
            max_retries=2,
            max_tokens=max_tokens if max_tokens is not None else 4096,
        )

    # 기존 코드 유지
    if model_name.startswith("gpt-"):
        return ChatOpenAI(
            model=model_name,
            timeout=timeout,
            max_retries=2,
            max_tokens=max_tokens if max_tokens is not None else 4096,
            api_key=settings.OPENAI_API_KEY,
        )
    if model_name.startswith("claude-"):
        return ChatAnthropic(
            model=model_name,
            timeout=timeout,
            max_retries=2,
            max_tokens=max_tokens if max_tokens is not None else 8192,
            api_key=settings.ANTHROPIC_API_KEY,
        )
    raise ValueError(f"Unknown model: {model_name}")
```

---

### 4. Agent 파일들 (환경 변수 사용)

**변경 사항**: 하드코딩된 모델 이름을 환경 변수에서 읽도록 변경

#### `backend/src/tutor/agents/supervisor.py`

```python
# 변경 전
llm = get_llm("claude-haiku-4-5", max_tokens=1024, timeout=30)

# 변경 후
settings = get_settings()
llm = get_llm(settings.SUPERVISOR_MODEL, max_tokens=1024, timeout=30)
```

#### `backend/src/tutor/agents/grammar.py`

```python
# 변경 전
llm = get_llm("gpt-4o")

# 변경 후
settings = get_settings()
llm = get_llm(settings.GRAMMAR_MODEL)
```

#### `backend/src/tutor/agents/reading.py`

```python
# 변경 전
llm = get_llm("claude-sonnet-4-5")

# 변경 후
settings = get_settings()
llm = get_llm(settings.READING_MODEL)
```

#### `backend/src/tutor/agents/vocabulary.py`

```python
# 변경 전
llm = get_llm("claude-sonnet-4-5")

# 변경 후
settings = get_settings()
llm = get_llm(settings.VOCABULARY_MODEL)
```

---

### 5. `backend/.env.example`

**변경 사항**: GLM 관련 환경 변수 예제 추가

```env
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic API Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# GLM (Zhipu AI) API Configuration (신규)
GLM_API_KEY=your_glm_api_key_here
GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/

# Model Configuration (GLM으로 변경 예시)
SUPERVISOR_MODEL=glm-4-flash
READING_MODEL=glm-4-plus
GRAMMAR_MODEL=glm-4-plus
VOCABULARY_MODEL=glm-4-flash
```

---

## 구현 순서

### Phase 1: 브랜치 생성 및 환경 설정

```bash
# 메인 브랜치 확인
git checkout main
git pull origin main

# 기능 브랜치 생성
git checkout -b feature/glm-migration
```

### Phase 2: 의존성 및 설정 추가

1. `pyproject.toml`에 zhipuai 추가
2. `uv sync` 실행
3. `config.py`에 GLM 설정 필드 추가
4. `.env` 파일에 GLM_API_KEY 설정

### Phase 3: LLM 팩토리 수정

1. `llm.py`에 GLM 모델 지원 추가
2. 단위 테스트 실행: `pytest tests/unit/test_llm.py -v`

### Phase 4: Agent 파일 수정

1. 각 agent 파일에서 환경 변수로 모델 이름 읽도록 수정
2. 단위 테스트 실행: `pytest tests/unit/test_agents.py -v`

### Phase 5: 통합 테스트

1. `.env` 파일에서 모델을 GLM로 설정
2. 백엔드 실행: `uv run uvicorn tutor.main:app --reload`
3. 통합 테스트: `pytest tests/integration/test_api.py -v`
4. 프론트엔드에서 수동 테스트

### Phase 6: 검증 및 병합

1. 모든 테스트 통과 확인
2. 수동 테스트 완료
3. main 브랜치로 병합:
   ```bash
   git checkout main
   git merge feature/glm-migration
   git push origin main
   git branch -d feature/glm-migration
   ```

---

## 검증 방법

### 1. 단위 테스트

```bash
cd backend
pytest tests/unit/test_llm.py -v
pytest tests/unit/test_agents.py -v
```

### 2. 통합 테스트

```bash
pytest tests/integration/test_api.py -v
```

### 3. 수동 테스트 시나리오

1. 백엔드와 프론트엔드 실행
2. 영어 문장 입력 후 분석 요청
3. 각 agent 결과 확인:
   - Supervisor: 문장 분할 및 난이도 평가
   - Grammar: 한국어 문법 설명
   - Reading: 슬래시 독해
   - Vocabulary: 어휘 어원 설명

### 4. 롤백 테스트

- `.env` 파일에서 모델 이름을 다시 gpt-*/claude-*로 변경
- 서비스 재시작 후 정상 작동 확인

---

## 롤백 전략

문제 발생 시 즉시 롤백 가능:

1. **환경 변수만 변경**: `.env`에서 모델 이름을 원래대로 변경
2. **브랜치 삭제**: feature 브랜치 삭제로 변경 사항 폐기
3. **main 브랜치는 안전**: 모든 변경 사항은 feature 브랜치에서만 수행

```bash
# 롤백 시나리오
git checkout main
git branch -D feature/glm-migration
```

---

## 참고 자료

- **Zhipu AI 공식 문서**: https://open.bigmodel.cn/
- **GLM-4 모델 리스트**: https://open.bigmodel.cn/dev/api#glm-4
- **LangChain ChatOpenAI**: https://python.langchain.com/docs/integrations/providers/openai/

---

## 결정: CANCELLED

**상태**: 취소됨 (CANCELLED)
**취소 일자**: 2026-02-23
**취소 사유**: GLM 모델의 영어 설명 수준에서 할루시네이션이 과다하여 교육 서비스 품질 저하 우려

### 취소 결정 배경

1. **품질 문제**: GLM 모델이 영어 문법/독해/어휘 설명에서 사실과 다른 내용을 생성하는 할루시네이션 현상 다수 발견
2. **교육적 적합성**: 영어 교육 서비스는 높은 정확도가 요구되며, 할루시네이션은 학습자에게 혼란을 야기할 수 있음
3. **비용 vs 품질 트레이드오프**: 비용 절감(70-90%)이 있으나, 서비스 품질 저하가 더 큰 리스크로 판단됨

### 보관 사유

이 계획 문서는 다음 사유로 보관됨:
1. 향후 GLM 모델의 품질 개선 시 재검토 가능
2. 기술적 구현 패턴(LangChain ChatOpenAI base_url 활용)은 다른 호환 API에 적용 가능
3. 비용 최적화 시도의 기록으로 프로젝트 역사 보존

### 대안 고려사항

1. **현재 모델 유지**: OpenAI/Anthropic 모델의 높은 품질 활용
2. **부분적 최적화**: 비용 효율이 높은 특정 agent에만 저렴한 모델 사용 검토
3. **캐싱 전략**: 반응형 캐싱으로 API 호출 횟수 감소

---

## 원래 요약 (보관용)

1. **최소 8개 파일 수정**: pyproject.toml, config.py, llm.py, 4개 agent 파일, .env.example
2. **기존 구조 유지**: LangChain 추상화 활용으로 코드 변경 최소화
3. **안전한 브랜치 전략**: feature/glm-migration 브랜치에서 개발
4. **쉬운 롤백**: 환경 변수 또는 브랜치 삭제로 즉시 복귀
5. **비용 절감**: GLM 모델 사용으로 약 70-90% 비용 절감 예상
6. **취소 사유**: 할루시네이션 문제로 인한 품질 우려
