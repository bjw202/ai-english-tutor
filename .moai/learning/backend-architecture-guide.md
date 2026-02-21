# AI 영어 튜터 백엔드 아키텍처 가이드

> 주니어 개발자를 위한 친절한 설명서
> 작성일: 2026-02-21
> 커버리지: 96%, 통과 테스트: 159개

---

## 목차

1. [전체 백엔드 구조](#1-전체-백엔드-구조)
2. [LangGraph 멀티 에이전트 구조](#2-langgraph-멀티-에이전트-구조)
3. [파이썬 테스트코드 완벽 가이드](#3-파이썬-테스트코드-완벽-가이드)
4. [주니어 개발자를 위한 팁](#4-주니어-개발자를-위한-팁)

---

## 1. 전체 백엔드 구조

### 1.1 프로젝트가 무엇인가요?

이 프로젝트는 **AI 기반 개인 맞춤형 영어 학습 튜터**의 백엔드 시스템입니다. 중학생이 영어 문장을 입력하면, AI가 읽기 이해, 문법, 어휘를 분석해서 설명해줍니다.

**간단한 사용 예시:**
```
사용자 입력: "The quick brown fox jumps over the lazy dog."
AI 응답:
  - 요약: 여우가 개를 뛰어넘는 이야기입니다.
  - 문법: 현재 시제, 능동태, 단순문
  - 어휘: quick(빠른), jumps(뛰다), lazy(게으른)
```

### 1.2 기술 스택 (어떤 기술을 썼나요?)

| 기술 | 버전 | 왜 썼나요? |
|------|------|-----------|
| **Python** | 3.13+ | 가장 널리 쓰이는 AI/ML 언어 |
| **FastAPI** | 0.115+ | 빠르고 현대적인 웹 프레임워크 |
| **LangGraph** | 0.3+ | AI 에이전트들을 조율하는 도구 |
| **Pydantic** | 2.10+ | 데이터 검증 (잘못된 입력 방지) |
| **uv** | 0.6+ | pip보다 10배 빠른 패키지 관리자 |
| **pytest** | 8.3+ | 테스트 코드 실행 도구 |

### 1.3 디렉토리 구조

```
backend/
├── pyproject.toml          # 프로젝트 설정 (package.json 같은 것)
├── .env.example            # 환경변수 예시
├── src/tutor/              # 메인 소스 코드
│   ├── main.py             # FastAPI 앱 진입점
│   ├── config.py           # 설정 관리
│   ├── schemas.py          # 데이터 모델 (요청/응답 형태)
│   ├── state.py            # LangGraph 상태 정의
│   ├── graph.py            # LangGraph 그래프 정의
│   ├── agents/             # AI 에이전트들
│   │   ├── supervisor.py   # 작업 분배 담당
│   │   ├── reading.py      # 읽기 분석
│   │   ├── grammar.py      # 문법 분석
│   │   ├── vocabulary.py   # 어휘않을 following content is too long and was truncated. Let me write a new comprehensive document.