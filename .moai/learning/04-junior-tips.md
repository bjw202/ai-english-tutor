# AI 영어 튜터 백엔드 가이드 - 4부: 주니어 개발자를 위한 팁

> 실무에서 바로 쓸 수 있는 꿀팁 모음

---

## 1. 코드 읽는 순서

### 1.1 처음 프로젝트를 볼 때

```
읽기 순서:
1. main.py        → 앱이 어떻게 시작되는지
2. schemas.py     → 데이터가 어떻게 생겼는지
3. routers/*.py   → API 엔드포인트가 뭔지
4. state.py       → State 구조 이해
5. graph.py       → 전체 흐름 파악
6. agents/*.py    → 각 에이전트 동작
7. services/*.py  → 비즈니스 로직
8. tests/         → 테스트 코드 (동작 예시)
```

### 1.2 왜 이 순서인가요?

```
main.py → "진입점을 알면 전체를 안다"
  ↓
schemas.py → "데이터 구조를 알면 API를 안다"
  ↓
routers → "엔드포인트를 알면 기능을 안다"
  ↓
graph.py → "흐름을 알면 로직을 안다"
  ↓
agents → "각 컴포넌트를 알면 구현을 안다"
```

---

## 2. 디버깅 팁

### 2.1 로깅 사용

```python
import logging

# 로거 생성
logger = logging.getLogger(__name__)

async def reading_node(state: TutorState) -> dict:
    # 진입 로그
    logger.info(f"Reading node called with text: {state.get('input_text')[:50]}")

    try:
        llm = get_llm("claude-sonnet-4-5")
        logger.debug(f"LLM client created: {llm}")

        result = await structured_llm.ainvoke(prompt)
        logger.info(f"LLM result: {result}")

        return {"reading_result": result}

    except Exception as e:
        # 에러 로그
        logger.error(f"Error in reading_node: {e}", exc_info=True)
        return {"reading_result": None}
```

### 2.2 print 디버깅

```python
async def reading_node(state: TutorState) -> dict:
    # State 확인
    print(f"=== State Keys: {state.keys()} ===")
    print(f"=== input_text: {state.get('input_text')} ===")
    print(f"=== level: {state.get('level')} ===")

    # 중간 결과 확인
    prompt = render_prompt(...)
    print(f"=== Prompt (first 200 chars): {prompt[:200]} ===")

    # LLM 응답 확인
    result = await structured_llm.ainvoke(prompt)
    print(f"=== Result: {result} ===")

    return {"reading_result": result}
```

### 2.3 디버거 사용 (VS Code)

```json
// .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug FastAPI",
            "type": "debugpy",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "tutor.main:app",
                "--reload"
            ],
            "jinjaTemplates": true,
            "justMyCode": false
        }
    ]
}
```

### 2.4 State 시각화

```python
def print_state(state: TutorState, label: str = "State"):
    """State를 보기 좋게 출력"""
    print(f"\n{'='*50}")
    print(f" {label}")
    print(f"{'='*50}")
    for key, value in state.items():
        if isinstance(value, str) and len(value) > 50:
            print(f"  {key}: {value[:50]}...")
        elif isinstance(value, list):
            print(f"  {key}: [{len(value)} items]")
        else:
            print(f"  {key}: {value}")
    print(f"{'='*50}\n")

# 사용
print_state(state, "Before reading_node")
result = await reading_node(state)
print_state(result, "After reading_node")
```

---

## 3. 자주 하는 실수와 해결법

### 3.1 환경 변수 누락

```
증상:
  ValidationError: OPENAI_API_KEY is required

해결:
  1. .env 파일 생성
  2. .env.example 내용 복사
  3. 실제 API 키 입력
```

```bash
# .env
OPENAI_API_KEY=sk-xxx...
ANTHROPIC_API_KEY=sk-ant-xxx...
CORS_ORIGINS=http://localhost:3000
```

### 3.2 Pydantic 검증 실패

```
증상:
  HTTP 422 Unprocessable Entity

원인:
  - text가 10자 미만
  - level이 1-5 범위 밖
  - 필수 필드 누락

해결:
  요청 데이터 확인
```

```python
# 올바른 요청
{
    "text": "This is at least ten characters.",
    "level": 3
}

# 잘못된 요청
{
    "text": "short",  # 10자 미만
    "level": 10       # 1-5 범위 밖
}
```

### 3.3 Mock 설정 오류

```python
# 잘못된 예
with patch("tutor.models.llm.get_llm", return_value=mock_llm):
    # 원본 모듈이 아니라 사용되는 위치를 패치해야 함!

# 올바른 예
with patch("tutor.agents.reading.get_llm", return_value=mock_llm):
    # reading.py에서 import한 get_llm을 패치
```

### 3.4 비동기 함수 실수

```python
# 잘못된 예 - await 없음
result = reading_node(state)  # coroutine 객체 반환

# 올바른 예
result = await reading_node(state)  # 실제 결과 반환

# 테스트에서
@pytest.mark.asyncio
async def test_xxx():
    result = await reading_node(state)  # async 테스트
```

---

## 4. 좋은 커밋 메시지 작성법

### 4.1 Conventional Commits

```
형식: <type>: <subject>

type 종류:
  feat:     새로운 기능
  fix:      버그 수정
  docs:     문서 변경
  style:    포맷팅 (코드 변경 없음)
  refactor: 리팩토링
  test:     테스트 추가/수정
  chore:    빌드, 설정 등
```

### 4.2 예시

```bash
# 좋은 예
git commit -m "feat: LangGraph 병렬 실행 구현"
git commit -m "fix: Schema validation 버그 수정"
git commit -m "test: Reading agent 테스트 추가"
git commit -m "docs: API 문서 업데이트"
git commit -m "refactor: 에이전트 구조 개선"

# 나쁜 예
git commit -m "수정"
git commit -m "버그 픽스"
git commit -m "asdf"
```

---

## 5. 유용한 명령어 모음

### 5.1 개발 명령어

```bash
# 서버 실행
cd backend && uv run uvicorn tutor.main:app --reload

# 서버 실행 (다른 포트)
uv run uvicorn tutor.main:app --reload --port 8080

# API 문서 확인
open http://localhost:8000/docs      # Swagger UI
open http://localhost:8000/redoc     # ReDoc
```

### 5.2 테스트 명령어

```bash
# 모든 테스트
uv run pytest -v

# 특정 파일
uv run pytest tests/unit/test_agents.py -v

# 특정 테스트
uv run pytest tests/unit/test_agents.py::TestReadingAgent -v

# 커버리지
uv run pytest --cov=src/tutor --cov-report=html

# 실패한 테스트만 재실행
uv run pytest --lf
```

### 5.3 코드 품질

```bash
# 린트 검사
uv run ruff check src/

# 린트 자동 수정
uv run ruff check src/ --fix

# 포맷팅
uv run ruff format src/

# 타입 검사
uv run mypy src/
```

### 5.4 패키지 관리

```bash
# 패키지 추가
uv add fastapi

# 개발 의존성 추가
uv add --dev pytest

# 패키지 제거
uv remove package-name

# 의존성 동기화
uv sync
```

---

## 6. 확장 포인트

### 6.1 새로운 에이전트 추가

```
1단계: 스키마 정의 (schemas.py)
```
```python
class PronunciationResult(BaseModel):
    word: str
    phonetic: str
    audio_url: str
```

```
2단계: 에이전트 구현 (agents/pronunciation.py)
```
```python
async def pronunciation_node(state: TutorState) -> dict:
    llm = get_llm("claude-sonnet-4-5")
    # ...
    return {"pronunciation_result": result}
```

```
3단계: 그래프에 추가 (graph.py)
```
```python
workflow.add_node("pronunciation", pronunciation_node)

def route_by_task(state: TutorState) -> list[Send]:
    if task_type == "analyze":
        return [
            Send("reading", state),
            Send("grammar", state),
            Send("vocabulary", state),
            Send("pronunciation", state),  # 추가
        ]

workflow.add_edge("pronunciation", "aggregator")
```

```
4단계: 테스트 작성 (tests/unit/test_agents.py)
```
```python
class TestPronunciationAgent:
    @pytest.mark.asyncio
    async def test_pronunciation_agent(self):
        # 테스트 구현
        pass
```

### 6.2 새로운 API 엔드포인트 추가

```python
# routers/tutor.py

@router.post("/tutor/translate")
async def translate(request: TranslateRequest) -> StreamingResponse:
    """번역 엔드포인트"""

    async def generate():
        result = await graph.ainvoke({
            "messages": [],
            "level": request.level,
            "session_id": session_id,
            "input_text": request.text,
            "task_type": "translate",
        })
        yield format_translate_chunk(result)

    return StreamingResponse(generate(), media_type="text/event-stream")
```

---

## 7. 학습 로드맵

### 7.1 기초 (이미 완료해야 함)

- [ ] Python 기본 문법
- [ ] 비동기 프로그래밍 (async/await)
- [ ] 타입 힌트 (Type Hints)

### 7.2 중급 (이 프로젝트에서 학습)

- [ ] FastAPI 프레임워크
- [ ] Pydantic 데이터 검증
- [ ] pytest 테스팅
- [ ] LangGraph 에이전트

### 7.3 고급 (다음 단계)

- [ ] Docker 컨테이너화
- [ ] CI/CD 파이프라인
- [ ] 데이터베이스 연동
- [ ] 캐싱 (Redis)
- [ ] 모니터링 (Prometheus, Grafana)

---

## 8. 추천 학습 자료

### 8.1 공식 문서

| 주제 | 링크 |
|------|------|
| FastAPI | https://fastapi.tiangolo.com/ |
| LangGraph | https://langchain-ai.github.io/langgraph/ |
| pytest | https://docs.pytest.org/ |
| Pydantic | https://docs.pydantic.dev/ |
| uv | https://docs.astral.sh/uv/ |

### 8.2 추천 도서

- "파이썬 클린 코드" - 마리아노 아니고
- "테스트 주도 개발" - 켄트 벡
- "실용주의 프로그래머" - 앤드류 헌트

---

## 9. 질문하기 가이드

### 9.1 좋은 질문 예시

```
질문: "reading_node에서 Claude API 호출 시 타임아웃이 발생합니다.

시도해본 것:
1. timeout=120으로 늘려봄
2. 재시도 로직 추가

에러 메시지:
TimeoutError: Request timed out after 60 seconds

환경:
- Python 3.13
- Claude Sonnet 4.5
- 입력 텍스트: 4000자

어떻게 해결하나요?"
```

### 9.2 질문 전 체크리스트

- [ ] 에러 메시지를 포함했나요?
- [ ] 시도해본 것을 적었나요?
- [ ] 환경 정보를 포함했나요?
- [ ] 재현 가능한 예시가 있나요?

---

## 10. 요약

### 개발 워크플로우

```
1. 코드 읽기: main.py → schemas → routers → graph → agents
2. 개발하기: TDD (테스트 먼저 작성)
3. 디버깅하기: 로깅 → print → 디버거
4. 커밋하기: Conventional Commits
5. 테스트하기: pytest -v
6. 배포하기: 품질 게이트 통과 확인
```

### 핵심 기억할 것

1. **State**는 에이전트 간 공유 데이터
2. **Send()**로 병렬 실행
3. **Mock**으로 외부 의존성 격리
4. **Given-When-Then**으로 테스트 작성
5. **Conventional Commits**로 커밋 작성
