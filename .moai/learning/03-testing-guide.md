# AI 영어 튜터 백엔드 가이드 - 3부: 파이썬 테스트코드

> pytest 완벽 가이드: 기초부터 실전까지

---

## 1. 테스트가 왜 필요한가요?

### 1.1 테스트 없는 코드의 문제

```
개발 과정:
  코드 작성 → 브라우저에서 테스트 → 버그 발견 → 수정 → 다시 테스트...

문제점:
  1. 시간이 많이 걸림
  2. 모든 케이스를 확인하기 어려움
  3. 나중에 수정하면 예전 기능이 깨질 수 있음
```

### 1.2 테스트 코드의 장점

```
┌────────────────────────────────────────────────────────┐
│                    테스트 코드의 장점                    │
├────────────────────────────────────────────────────────┤
│ 1. 버그 조기 발견   - 개발 중 바로 문제 확인            │
│ 2. 리팩토링 안전망  - 코드 수정 후에도 동작 보장        │
│ 3. 문서 역할       - 테스트 코드가 사용 예시가 됨       │
│ 4. 자신감          - "이 코드는 작동합니다" 증명        │
│ 5. 협업            - 다른 개발자가 코드 이해하기 쉬움   │
└────────────────────────────────────────────────────────┘
```

### 1.3 테스트 종류

| 종류 | 범위 | 속도 | 예시 |
|------|------|------|------|
| 단위 테스트 | 함수/클래스 | 빠름 | `test_add()` |
| 통합 테스트 | 여러 컴포넌트 | 보통 | `test_api_endpoint()` |
| E2E 테스트 | 전체 시스템 | 느림 | 브라우저 테스트 |

**이 프로젝트:**
- `tests/unit/` - 단위 테스트 (96% 커버리지)
- `tests/integration/` - 통합 테스트

---

## 2. pytest 기초

### 2.1 설치 및 실행

```bash
# 설치
uv add pytest pytest-asyncio pytest-cov

# 기본 실행
pytest

# 상세 출력
pytest -v

# 특정 파일
pytest tests/unit/test_agents.py

# 특정 테스트
pytest tests/unit/test_agents.py::TestReadingAgent::test_reading_agent_returns_reading_result

# 커버리지 측정
pytest --cov=src/tutor --cov-report=html

# 실패한 테스트만 다시 실행
pytest --lf
```

### 2.2 기본 테스트 작성

```python
# tests/unit/test_example.py

def test_addition():
    """덧셈 테스트"""
    result = 1 + 1
    assert result == 2  # assert: 참이어야 함

def test_string_concat():
    """문자열 연결 테스트"""
    result = "hello" + " " + "world"
    assert result == "hello world"

def test_list_length():
    """리스트 길이 테스트"""
    items = [1, 2, 3, 4, 5]
    assert len(items) == 5
```

### 2.3 assert 문법

```python
# 비교
assert a == b      # 같음
assert a != b      # 다름
assert a > b       # 크다
assert a >= b      # 크거나 같다
assert a < b       # 작다
assert a <= b      # 작거나 같다

# 멤버십
assert item in list      # 포함됨
assert item not in list  # 포함 안 됨

# 타입
assert isinstance(obj, Class)

# 불리언
assert condition         # 참
assert not condition     # 거짓

# 예외
with pytest.raises(ValueError):
    int("not a number")

# 예외 메시지 확인
with pytest.raises(ValueError) as exc_info:
    int("not a number")
assert "invalid literal" in str(exc_info.value)
```

---

## 3. Given-When-Then 패턴

### 3.1 패턴 설명

```
GIVEN (준비): 테스트할 상황을 설정
WHEN (실행): 테스트할 동작을 수행
THEN (검증): 예상한 결과가 나오는지 확인
```

### 3.2 실제 예시

```python
# tests/unit/test_agents.py

def test_supervisor_routes_to_analyze():
    """
    GIVEN: task_type이 'analyze'인 상태
    WHEN: supervisor_node를 호출하면
    THEN: reading, grammar, vocabulary로 라우팅해야 함
    """
    # GIVEN (준비)
    state = {
        "messages": [],
        "level": 3,
        "session_id": "test-123",
        "input_text": "Hello world",
        "task_type": "analyze",
    }

    # WHEN (실행)
    result = supervisor_node(state)

    # THEN (검증)
    assert "next_nodes" in result
    assert set(result["next_nodes"]) == {"reading", "grammar", "vocabulary"}
```

### 3.3 또 다른 예시

```python
def test_analyze_request_text_too_short():
    """
    GIVEN: 10자 미만의 텍스트
    WHEN: AnalyzeRequest를 생성하면
    THEN: ValidationError가 발생해야 함
    """
    # GIVEN & WHEN & THEN
    with pytest.raises(ValidationError) as exc_info:
        AnalyzeRequest(text="short", level=3)

    # 추가 검증
    errors = exc_info.value.errors()
    assert any(e["loc"] == ("text",) for e in errors)
```

---

## 4. Fixture (테스트 데이터 공유)

### 4.1 기본 Fixture

```python
# tests/conftest.py (공통 fixture)
import pytest
from pathlib import Path

@pytest.fixture
def project_root() -> Path:
    """프로젝트 루트 경로"""
    return Path(__file__).parent.parent

@pytest.fixture
def base_state() -> dict:
    """테스트용 기본 State"""
    return {
        "messages": [],
        "level": 3,
        "session_id": "test-session-123",
        "input_text": "Hello, world!",
        "task_type": "analyze",
    }
```

### 4.2 Fixture 사용

```python
# tests/unit/test_agents.py

def test_supervisor_routes_to_analyze(base_state: dict):
    """Fixture를 매개변수로 받음"""
    # GIVEN
    base_state["task_type"] = "analyze"

    # WHEN
    result = supervisor_node(base_state)

    # THEN
    assert set(result["next_nodes"]) == {"reading", "grammar", "vocabulary"}

def test_supervisor_routes_to_chat(base_state: dict):
    """같은 Fixture 재사용"""
    # GIVEN
    base_state["task_type"] = "chat"

    # WHEN
    result = supervisor_node(base_state)

    # THEN
    assert result["next_nodes"] == ["chat"]
```

### 4.3 autouse Fixture

```python
# tests/conftest.py

@pytest.fixture(autouse=True)
def set_test_env():
    """모든 테스트 전에 자동 실행"""
    import os
    os.environ["OPENAI_API_KEY"] = "test-key"
    os.environ["ANTHROPIC_API_KEY"] = "test-key"
    yield  # 테스트 실행
    # 테스트 후 정리
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ.pop("ANTHROPIC_API_KEY", None)
```

### 4.4 Fixture 스코프

```python
# function: 각 테스트마다 새로 생성 (기본)
@pytest.fixture(scope="function")
def fresh_data():
    return {"count": 0}

# class: 클래스 내 모든 테스트가 공유
@pytest.fixture(scope="class")
def shared_data():
    return {"count": 0}

# module: 모듈 내 모든 테스트가 공유
@pytest.fixture(scope="module")
def expensive_resource():
    return create_expensive_resource()

# session: 테스트 세션 전체에서 공유
@pytest.fixture(scope="session")
def database():
    db = create_database()
    yield db
    db.close()
```

---

## 5. Mock (가짜 객체)

### 5.1 Mock이 왜 필요한가요?

```
문제:
  - LLM API 호출 → 비용 발생
  - 데이터베이스 연결 → 테스트 환경 필요
  - 외부 서비스 → 불안정

해결:
  - Mock으로 "가짜" 객체 생성
  - 실제 호출 없이 테스트
```

### 5.2 기본 Mock 사용법

```python
from unittest.mock import Mock, MagicMock

# 기본 Mock
mock = Mock()
mock.method()  # 아무 일도 하지 않음
mock.method.return_value = "hello"
result = mock.method()  # "hello"

# 호출 확인
mock.method.assert_called()
mock.method.assert_called_once()
mock.method.assert_called_with("arg1", "arg2")

# MagicMock (매직 메서드 지원)
mock = MagicMock()
len(mock)  # 작동함
mock[0]    # 작동함
```

### 5.3 AsyncMock (비동기 함수)

```python
from unittest.mock import AsyncMock

# 비동기 Mock
async_mock = AsyncMock()
async_mock.return_value = "async result"

# await으로 호출
result = await async_mock()  # "async result"
```

### 5.4 patch (모듈 교체)

```python
from unittest.mock import patch, MagicMock, AsyncMock

@pytest.mark.asyncio
async def test_reading_agent_with_mock():
    """LLM 호출을 Mock으로 대체"""

    # GIVEN: 가짜 LLM 응답
    expected_result = ReadingResult(
        summary="A fox jumps over a dog.",
        main_topic="Animal behavior",
        emotional_tone="Playful"
    )

    # Mock 설정
    mock_structured_llm = AsyncMock()
    mock_structured_llm.ainvoke.return_value = expected_result

    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured_llm

    # WHEN: patch로 실제 get_llm을 Mock으로 교체
    with patch("tutor.agents.reading.get_llm", return_value=mock_llm):
        result = await reading_node({
            "input_text": "test",
            "level": 3
        })

    # THEN
    assert result["reading_result"].summary == "A fox jumps over a dog."
```

### 5.5 patch 위치 중요!

```python
# 잘못된 예 - 원본 모듈을 패치
with patch("tutor.models.llm.get_llm", return_value=mock_llm):
    # 작동하지 않을 수 있음!

# 올바른 예 - 사용되는 위치를 패치
with patch("tutor.agents.reading.get_llm", return_value=mock_llm):
    # reading.py에서 import한 get_llm을 Mock으로 교체
```

---

## 6. pytest-asyncio

### 6.1 비동기 테스트

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """비동기 함수 테스트"""
    result = await some_async_function()
    assert result == expected

@pytest.mark.asyncio
async def test_with_fixture(base_state: dict):
    """Fixture와 함께 사용"""
    result = await async_node(base_state)
    assert result is not None
```

### 6.2 async fixture

```python
@pytest.fixture
async def async_setup():
    """비동기 Fixture"""
    resource = await create_resource()
    yield resource
    await resource.close()

@pytest.mark.asyncio
async def test_with_async_fixture(async_setup):
    result = await do_something(async_setup)
    assert result is not None
```

---

## 7. 이 프로젝트의 테스트 구조

### 7.1 디렉토리 구조

```
tests/
├── conftest.py              # 공통 fixture
├── __init__.py
├── unit/                    # 단위 테스트
│   ├── __init__.py
│   ├── test_schemas.py      # Pydantic 모델 테스트
│   ├── test_agents.py       # 에이전트 테스트
│   ├── test_services.py     # 서비스 테스트
│   ├── test_graph.py        # 그래프 테스트
│   ├── test_state.py        # State 테스트
│   └── test_config.py       # 설정 테스트
└── integration/             # 통합 테스트
    ├── __init__.py
    └── test_api.py          # API 엔드포인트 테스트
```

### 7.2 conftest.py

```python
# tests/conftest.py
import os
from pathlib import Path
import pytest

@pytest.fixture(autouse=True)
def set_test_env():
    """모든 테스트에 환경변수 설정"""
    os.environ["OPENAI_API_KEY"] = "test-key-for-testing"
    os.environ["ANTHROPIC_API_KEY"] = "test-key-for-testing"
    os.environ["CORS_ORIGINS"] = "http://localhost:3000"
    yield
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ.pop("ANTHROPIC_API_KEY", None)
    os.environ.pop("CORS_ORIGINS", None)

@pytest.fixture
def project_root() -> Path:
    return Path(__file__).parent.parent

@pytest.fixture
def src_dir(project_root: Path) -> Path:
    return project_root / "src"
```

### 7.3 Schema 테스트 예시

```python
# tests/unit/test_schemas.py
import pytest
from pydantic import ValidationError
from tutor.schemas import AnalyzeRequest, ReadingResult, GrammarResult

class TestAnalyzeRequest:
    """AnalyzeRequest 스키마 테스트"""

    def test_analyze_request_valid(self):
        """유효한 요청"""
        request = AnalyzeRequest(
            text="This is a valid text for analysis.",
            level=3
        )
        assert request.text == "This is a valid text for analysis."
        assert request.level == 3

    def test_analyze_request_text_too_short(self):
        """텍스트가 너무 짧음"""
        with pytest.raises(ValidationError) as exc_info:
            AnalyzeRequest(text="short", level=3)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("text",) for e in errors)

    def test_analyze_request_invalid_level_low(self):
        """레벨이 너무 낮음"""
        with pytest.raises(ValidationError):
            AnalyzeRequest(text="Valid text input", level=0)

    def test_analyze_request_invalid_level_high(self):
        """레벨이 너무 높음"""
        with pytest.raises(ValidationError):
            AnalyzeRequest(text="Valid text input", level=6)

    def test_analyze_request_all_valid_levels(self):
        """모든 유효한 레벨"""
        for level in [1, 2, 3, 4, 5]:
            request = AnalyzeRequest(text="Valid text for testing.", level=level)
            assert request.level == level
```

### 7.4 Agent 테스트 예시

```python
# tests/unit/test_agents.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from tutor.schemas import ReadingResult
from tutor.state import TutorState

class TestReadingAgent:
    """Reading 에이전트 테스트"""

    @pytest.fixture
    def reading_state(self) -> TutorState:
        return {
            "messages": [],
            "level": 3,
            "session_id": "test-session-123",
            "input_text": "The quick brown fox jumps over the lazy dog.",
            "task_type": "analyze",
        }

    @pytest.mark.asyncio
    async def test_reading_agent_returns_reading_result(
        self, reading_state: TutorState
    ):
        """ReadingResult 반환 테스트"""
        from tutor.agents.reading import reading_node

        # GIVEN
        expected_result = ReadingResult(
            summary="A fox jumps over a dog.",
            main_topic="Animal behavior",
            emotional_tone="Playful"
        )

        mock_structured_llm = AsyncMock()
        mock_structured_llm.ainvoke.return_value = expected_result

        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured_llm

        # WHEN
        with patch("tutor.agents.reading.get_llm", return_value=mock_llm), \
             patch("tutor.agents.reading.render_prompt", return_value="Test prompt"):
            result = await reading_node(reading_state)

        # THEN
        assert "reading_result" in result
        assert result["reading_result"].summary == "A fox jumps over a dog."

    @pytest.mark.asyncio
    async def test_reading_agent_handles_error(self, reading_state: TutorState):
        """에러 처리 테스트"""
        from tutor.agents.reading import reading_node

        with patch("tutor.agents.reading.get_llm", side_effect=Exception("API Error")):
            result = await reading_node(reading_state)

        assert result["reading_result"] is None
```

---

## 8. 테스트 커버리지

### 8.1 커버리지란?

```
커버리지 = (테스트가 실행한 코드 줄 수) / (전체 코드 줄 수) × 100%

이 프로젝트: 96%
```

### 8.2 커버리지 실행

```bash
# 커버리지 측정
pytest --cov=src/tutor --cov-report=term-missing

# HTML 리포트 생성
pytest --cov=src/tutor --cov-report=html
open htmlcov/index.html
```

### 8.3 커버리지 리포트 예시

```
Name                              Stmts   Miss  Cover   Missing
---------------------------------------------------------------
src/tutor/__init__.py                 1      0   100%
src/tutor/agents/__init__.py          1      0   100%
src/tutor/agents/reading.py          25      1    96%   62
src/tutor/agents/grammar.py          25      0   100%
src/tutor/agents/vocabulary.py       25      0   100%
src/tutor/agents/aggregator.py       20      0   100%
src/tutor/schemas.py                 45      0   100%
---------------------------------------------------------------
TOTAL                               250     10    96%
```

---

## 9. 테스트 작성 체크리스트

### 좋은 테스트의 조건

- [ ] **명확한 이름**: `test_supervisor_routes_to_analyze`
- [ ] **Given-When-Then**: 준비-실행-검증 구조
- [ ] **단일 책임**: 하나의 테스트는 하나의 동작만 검증
- [ ] **독립적**: 다른 테스트에 의존하지 않음
- [ ] **반복 가능**: 여러 번 실행해도 같은 결과
- [ ] **빠른 실행**: 1초 이내

### 피해야 할 것

- [ ] ~~외부 서비스 실제 호출~~ → Mock 사용
- [ ] ~~테스트 간 상태 공유~~ → Fixture 스코프 주의
- [ ] ~~너무 큰 테스트~~ → 작은 단위로 분리
- [ ] ~~구현 내용 테스트~~ → 동작(behavior) 테스트

---

## 10. 요약

### pytest 핵심
1. `def test_xxx()` 함수로 테스트 작성
2. `assert`로 검증
3. `pytest -v`로 실행

### Fixture 핵심
1. `@pytest.fixture`로 재사용 가능한 데이터 정의
2. 매개변수로 받아서 사용
3. `conftest.py`에 공통 fixture

### Mock 핵심
1. 외부 의존성을 가짜로 대체
2. `patch()`로 모듈 교체
3. `return_value`로 반환값 설정
4. `AsyncMock`으로 비동기 함수 Mock

### 이 프로젝트
1. 159개 테스트 통과
2. 96% 커버리지
3. 모든 에이전트 Mock 테스트
