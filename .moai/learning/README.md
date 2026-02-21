# AI 영어 튜터 백엔드 아키텍처 가이드

> 주니어 개발자를 위한 친절한 설명서
> 작성일: 2026-02-21
> 커버리지: 96%, 통과 테스트: 159개

---

## 문서 구성

이 가이드는 4개의 파트로 구성되어 있습니다:

| 파트 | 파일 | 내용 |
|------|------|------|
| 1부 | [01-backend-overview.md](./01-backend-overview.md) | 전체 백엔드 구조 |
| 2부 | [02-langgraph-deep-dive.md](./02-langgraph-deep-dive.md) | LangGraph 멀티 에이전트 |
| 3부 | [03-testing-guide.md](./03-testing-guide.md) | 파이썬 테스트코드 |
| 4부 | [04-junior-tips.md](./04-junior-tips.md) | 주니어 개발자 팁 |

---

## 빠른 요약

### 프로젝트 개요

**AI 기반 개인 맞춤형 영어 학습 튜터** 백엔드 시스템

```
사용자 입력: "The quick brown fox jumps over the lazy dog."

AI 응답:
  - 요약: 여우가 개를 뛰어넘는 이야기
  - 문법: 현재 시제, 능동태, 단순문
  - 어휘: quick(빠른), jumps(뛰다), lazy(게으른)
```

### 기술 스택

| 기술 | 역할 |
|------|------|
| FastAPI | 웹 프레임워크 |
| LangGraph | 에이전트 오케스트레이션 |
| Pydantic | 데이터 검증 |
| pytest | 테스트 프레임워크 |

### 아키텍처

```
클라이언트 → FastAPI → LangGraph → LLM (Claude, GPT-4o) → SSE 스트리밍
                           │
                    ┌──────┼──────┐
                    │      │      │
                 Reading Grammar Vocabulary
                    │      │      │
                    └──────┼──────┘
                           │
                       Aggregator
```

### 핵심 개념

| 개념 | 설명 |
|------|------|
| State | 에이전트 간 공유 데이터 |
| Send() | 병렬 실행 API |
| Mock | 외부 의존성 격리 |
| Given-When-Then | 테스트 작성 패턴 |

---

## 학습 로드맵

```
Step 1: 1부 읽기 → 전체 구조 이해
   ↓
Step 2: 2부 읽기 → LangGraph 이해
   ↓
Step 3: 코드 따라가기 → graph.py, agents/*.py
   ↓
Step 4: 3부 읽기 → 테스트 코드 이해
   ↓
Step 5: 테스트 실행 → pytest -v
   ↓
Step 6: 4부 읽기 → 개발 팁 습득
```

---

## 빠른 시작

```bash
# 1. 의존성 설치
cd backend && uv sync

# 2. 환경변수 설정
cp .env.example .env
# .env 파일에 API 키 입력

# 3. 서버 실행
uv run uvicorn tutor.main:app --reload

# 4. API 문서 확인
open http://localhost:8000/docs

# 5. 테스트 실행
uv run pytest -v
```

---

## 파일별 읽기 순서

처음 프로젝트를 볼 때 추천하는 순서:

1. `main.py` - 앱 진입점
2. `schemas.py` - 데이터 모델
3. `routers/tutor.py` - API 엔드포인트
4. `state.py` - State 정의
5. `graph.py` - 그래프 구조
6. `agents/*.py` - 각 에이전트

---

## 도움이 필요할 때

1. 각 파트의 상세 설명 참조
2. 테스트 코드에서 실제 사용 예시 확인
3. 에러 발생 시 4부의 "자주 하는 실수" 참조
