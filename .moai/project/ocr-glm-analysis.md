# GLM OCR 구현 기술 분석

**작성일**: 2026-02-22
**상태**: 구현 계획 수립 완료
**대상**: AI English Tutor OCR 기능

---

## 1. 문제 요약

### 현재 상황

AI English Tutor의 이미지 업로드 기능에서 OCR(광학 문자 인식)이 정상 작동하지 않고 있습니다. 사용자가 이미지를 업로드하면 모든 분석 요청이 **422 Unprocessable Entity** 에러로 실패합니다.

### 주요 문제점

1. **데이터 형식 불일치 (주 원인)**
   - Next.js 프록시가 `multipart/form-data`로 파일을 전송
   - FastAPI 백엔드는 JSON body (`image_data` base64 문자열) 기대
   - 형식 불일치로 인해 모든 요청이 실패

2. **OCR 엔진 제한**
   - 현재: Claude Sonnet 4.5 비전 모델 사용
   - 요청: GLM API의 OCR 기능으로 교체 필요

### 영향 범위

- **프론트엔드**: `src/app/api/tutor/analyze-image/route.ts`
- **백엔드**: 이미지 처리 파이프라인 전체
- **사용자**: 이미지 업로드 및 텍스트 추출 기능 완전 불가

---

## 2. 근본 원인 분석

### 데이터 형식 불일치 상세 분석

#### 현재 (버그) 데이터 흐름

```
Frontend (사용자 이미지 선택)
  ↓
  FormData 생성: { file, level }
  ↓
Next.js API Route (route.ts)
  ↓
  FormData 그대로 전달 ← [문제 1: 변환 없음]
  ↓
FastAPI 백엔드
  ↓
  AnalyzeImageRequest 파싱 시도 (JSON 형식 기대)
  ↓
  422 Unprocessable Entity ❌ [파싱 실패]
```

#### 근본 원인

| 계층 | 송신 형식 | 수신 기대 형식 | 결과 |
|------|---------|--------------|------|
| Next.js | `multipart/form-data` | JSON | ❌ 불일치 |
| FastAPI | - | `{"image_data": "base64...", "mime_type": "...", "level": 3}` | ❌ 파싱 실패 |

### API 계약 불일치

**FastAPI AnalyzeImageRequest 모델**

```
예상 입력:
{
  "image_data": "iVBORw0KGgoAAAANSUhE...",  # base64 인코딩 이미지
  "mime_type": "image/jpeg",                  # 이미지 MIME 타입
  "level": 3                                  # 분석 레벨
}
```

**현재 전송 형식**

```
FormData:
- file: [Binary File Data]
- level: "3"
```

### 에러 메커니즘

1. Next.js가 FormData를 그대로 FastAPI로 전송
2. FastAPI가 JSON 파싱 시도
3. FormData는 JSON 형식이 아니므로 파싱 실패
4. 422 에러 반환

---

## 3. 현재 아키텍처

### 시스템 데이터 흐름 (버그 포함)

```
┌─────────────────────┐
│  Frontend Browser   │
│  (React Component)  │
└──────────┬──────────┘
           │ 1. 사용자가 이미지 선택
           │ FormData 생성: file + level
           ↓
┌──────────────────────────────────┐
│  Next.js API Route               │
│  /api/tutor/analyze-image        │
│  (route.ts)                      │
└──────────┬───────────────────────┘
           │ 2. FormData 그대로 전달 ← [버그]
           │    변환 없이 바로 POST
           ↓
┌──────────────────────────────────┐
│  FastAPI 백엔드                   │
│  POST /api/v1/tutor/analyze-image│
│  (AnalyzeImageRequest 파싱)       │
└──────────┬───────────────────────┘
           │ 3. JSON 파싱 시도
           │    ❌ FormData는 JSON 아님
           ↓
┌──────────────────────────────────┐
│  422 Unprocessable Entity Error   │
│  (파싱 실패)                      │
└──────────────────────────────────┘
```

### 파일 구조

```
ai-english-tutor/
├── src/
│   └── app/
│       └── api/
│           └── tutor/
│               └── analyze-image/
│                   └── route.ts ← [수정 필요]
│
└── backend/
    ├── pyproject.toml ← [zhipuai 추가]
    ├── .env.example ← [GLM_API_KEY 추가]
    └── src/
        └── tutor/
            ├── config.py ← [GLM_API_KEY 필드]
            ├── agents/
            │   └── image_processor.py ← [GLM 서비스 적용]
            └── services/
                └── glm_ocr.py ← [신규 생성]
```

### 컴포넌트 상호작용

**Next.js API Route (route.ts)**
- 역할: 프론트엔드 요청 처리, FastAPI 프록시
- 현재 문제: FormData를 JSON으로 변환하지 않음
- 필요 수정: File → base64 변환, MIME 타입 추출

**FastAPI 백엔드**
- 역할: 이미지 분석 요청 처리
- 현재: Claude Sonnet 4.5 비전 사용
- 필요 수정: GLM OCR 서비스로 교체

**GLM API**
- 역할: 이미지 OCR 수행 (새로 추가)
- 모델: GLM-4V Plus
- 기능: 이미지에서 텍스트 추출

---

## 4. GLM OCR 구현 계획

### 4.1 수정 파일 목록

#### 파일 1: `src/app/api/tutor/analyze-image/route.ts`

**목적**: FormData를 JSON으로 변환하는 데이터 변환 레이어

**변경 사항**

변경 전 (버그):
```typescript
// FormData를 그대로 전달 - 이것이 근본 원인
const backendFormData = new FormData();
backendFormData.append("file", file);
backendFormData.append("level", level || "3");

const response = await fetch(`${BACKEND_URL}/api/v1/tutor/analyze-image`, {
  method: "POST",
  body: backendFormData,  // ← FormData 그대로
});
```

변경 후 (수정):
```typescript
// File을 base64로 변환 후 JSON 전송
const arrayBuffer = await file.arrayBuffer();
const base64 = Buffer.from(arrayBuffer).toString("base64");
const mimeType = file.type || "image/jpeg";

const response = await fetch(`${BACKEND_URL}/api/v1/tutor/analyze-image`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },  // JSON 명시
  body: JSON.stringify({
    image_data: base64,           // base64 인코딩 이미지
    mime_type: mimeType,          // MIME 타입
    level: parseInt(level as string) || 3,
  }),
});
```

**기술적 이점**
- ✅ 데이터 형식을 FastAPI 기대값과 일치시킴
- ✅ Content-Type 명시로 명확한 통신 계약
- ✅ base64 인코딩으로 안전한 데이터 전송

---

#### 파일 2: `backend/pyproject.toml`

**목적**: GLM API를 사용하기 위한 SDK 의존성 추가

**변경 사항**

```toml
[project]
dependencies = [
    # 기존 의존성들...
    "fastapi>=0.100.0",
    "pydantic>=2.0.0",

    # 신규: GLM API SDK
    "zhipuai>=2.0.0,<3.0.0",  # Zhipu AI (GLM) SDK
]
```

**설치 확인**
```bash
cd backend
uv sync  # 또는 pip install -e .
```

---

#### 파일 3: `backend/.env.example`

**목적**: 환경 설정 예제 파일 업데이트 및 보안 강화

**변경 사항**

변경 전 (보안 취약):
```env
# .env.example에 실제 API 키가 노출되어 있음
GLM_API_KEY=sk-xxxxxxxxxxxxx  # ← 실제 키 노출!
OPENAI_API_KEY=sk-xxxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-xxxxxxxxxxxxx
```

변경 후 (보안 강화):
```env
# GLM (Zhipu AI) API Configuration
GLM_API_KEY=your_glm_api_key_here

# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic API Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

**보안 주의사항**
- ⚠️ 현재 `.env.example`에 실제 API 키가 노출되어 있음
- ⚠️ Git 커밋 이력에서 노출된 키를 찾아 즉시 폐기해야 함
- ✅ 변경 후: 플레이스홀더만 포함

---

#### 파일 4: `backend/src/tutor/config.py`

**목적**: GLM API 키 설정 필드 추가

**변경 사항**

```python
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 기존 설정들...
    BACKEND_URL: str = Field(default="http://localhost:8000")

    # 신규: GLM API Key (이미지 OCR용)
    GLM_API_KEY: str = Field(
        default="",
        alias="GLM_API_KEY",
        description="Zhipu AI GLM API Key for image OCR"
    )

    # 기존 설정들...
    OPENAI_API_KEY: str = Field(default="", alias="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: str = Field(default="", alias="ANTHROPIC_API_KEY")

    class Config:
        env_file = ".env"
        case_sensitive = True

def get_settings() -> Settings:
    return Settings()
```

**동작 방식**
- `.env` 파일에서 `GLM_API_KEY` 읽음
- 런타임에 `settings.GLM_API_KEY`로 접근 가능
- 값이 없으면 빈 문자열 (또는 검증 로직으로 필수 체크)

---

#### 파일 5: `backend/src/tutor/services/glm_ocr.py` (신규)

**목적**: GLM-4V Plus 모델을 사용한 OCR 서비스 구현

**전체 코드**

```python
"""GLM OCR service using Zhipu AI's vision model.

This module provides OCR functionality using Zhipu AI's GLM-4V Plus vision model,
which is optimized for text extraction from images.
"""
import asyncio
import logging
from typing import Optional

from zhipuai import ZhipuAI

from tutor.config import get_settings

logger = logging.getLogger(__name__)


async def extract_text_with_glm(
    image_data: str,
    mime_type: str,
    timeout: int = 30
) -> str:
    """
    Extract text from image using GLM-4V Plus vision model.

    Args:
        image_data: Base64 encoded image data
        mime_type: MIME type of the image (e.g., 'image/jpeg', 'image/png')
        timeout: Request timeout in seconds (default: 30)

    Returns:
        Extracted text from the image

    Raises:
        ValueError: If GLM_API_KEY is not configured
        Exception: If GLM API call fails

    Example:
        >>> image_data = "iVBORw0KGgoAAAANSUhE..."  # base64
        >>> text = await extract_text_with_glm(image_data, "image/jpeg")
        >>> print(text)
        "Extracted text from image"
    """
    settings = get_settings()

    # Validate API key
    if not settings.GLM_API_KEY:
        raise ValueError(
            "GLM_API_KEY is not configured. "
            "Please set it in .env file or environment variables."
        )

    # Initialize GLM client
    client = ZhipuAI(api_key=settings.GLM_API_KEY)

    def _sync_call() -> str:
        """Execute synchronous GLM API call."""
        try:
            response = client.chat.completions.create(
                model="glm-4v-plus",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_data}"
                                }
                            },
                            {
                                "type": "text",
                                "text": (
                                    "Extract all text from this image. "
                                    "Return only the extracted text without any "
                                    "additional commentary or formatting."
                                )
                            }
                        ]
                    }
                ],
                temperature=0.1,  # Low temperature for consistent output
                top_p=0.95,
            )

            extracted_text = response.choices[0].message.content.strip()
            logger.info("Successfully extracted text from image using GLM")
            return extracted_text

        except Exception as e:
            logger.error(f"GLM API error: {str(e)}")
            raise

    # Run synchronous call in executor to avoid blocking
    loop = asyncio.get_event_loop()
    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(None, _sync_call),
            timeout=timeout
        )
        return result
    except asyncio.TimeoutError:
        logger.error("GLM OCR request timed out")
        raise TimeoutError(f"GLM OCR request exceeded {timeout}s timeout")
```

**핵심 기능**

| 항목 | 설명 |
|------|------|
| 모델 | GLM-4V Plus (Zhipu AI 최신 비전 모델) |
| 입력 | base64 인코딩 이미지 + MIME 타입 |
| 출력 | 추출된 텍스트 문자열 |
| 타임아웃 | 30초 (조정 가능) |
| 에러 처리 | API 키 검증, 예외 처리, 로깅 |

---

#### 파일 6: `backend/src/tutor/agents/image_processor.py`

**목적**: 기존 Claude 비전에서 GLM OCR로 변경

**변경 사항**

변경 전 (Claude Sonnet 4.5 비전):
```python
from tutor.models.llm import get_llm
from langchain_core.messages import HumanMessage

async def process_image(image_data: str, mime_type: str) -> str:
    """이미지에서 텍스트 추출 (Claude Sonnet 4.5 비전)"""
    llm = get_llm("claude-sonnet-4-5")

    message = HumanMessage(
        content=[
            {
                "type": "image_url",
                "image_url": f"data:{mime_type};base64,{image_data}"
            },
            {"type": "text", "text": "Extract all text from this image"}
        ]
    )

    response = await llm.ainvoke([message])
    return response.content.strip()
```

변경 후 (GLM OCR):
```python
from tutor.services.glm_ocr import extract_text_with_glm

async def process_image(image_data: str, mime_type: str) -> str:
    """이미지에서 텍스트 추출 (GLM-4V Plus)"""
    # GLM OCR 서비스 직접 호출
    extracted_text = await extract_text_with_glm(image_data, mime_type)
    return extracted_text
```

**변경의 이점**
- ✅ 전용 OCR 엔진 사용으로 정확도 향상
- ✅ 코드 단순화 (LangChain 의존성 제거)
- ✅ API 비용 최적화 (GLM OCR이 더 저렴)

---

### 4.2 테스트 수정 전략

#### 1. `backend/tests/unit/test_agents.py`

**수정 내용**: `image_processor_node` 테스트 업데이트

```python
# 변경 전: Claude LLM mock
@patch("tutor.models.llm.get_llm")
async def test_process_image(mock_get_llm):
    mock_llm = AsyncMock()
    mock_llm.ainvoke.return_value.content = "Extracted text"
    mock_get_llm.return_value = mock_llm

    result = await process_image(test_image_data, "image/jpeg")
    assert result == "Extracted text"

# 변경 후: GLM OCR mock
@patch("tutor.services.glm_ocr.extract_text_with_glm")
async def test_process_image(mock_extract_glm):
    mock_extract_glm.return_value = "Extracted text"

    result = await process_image(test_image_data, "image/jpeg")
    assert result == "Extracted text"

    # GLM이 올바른 인자로 호출되었는지 확인
    mock_extract_glm.assert_called_once_with(test_image_data, "image/jpeg")
```

#### 2. `backend/tests/unit/test_services.py`

**신규 테스트**: GLM OCR 서비스 단위 테스트

```python
import pytest
from unittest.mock import patch, AsyncMock
from tutor.services.glm_ocr import extract_text_with_glm


class TestGLMOCRService:
    """GLM OCR 서비스 단위 테스트"""

    @pytest.mark.asyncio
    @patch("tutor.services.glm_ocr.ZhipuAI")
    async def test_extract_text_success(self, mock_zhipuai):
        """정상 케이스: 텍스트 추출 성공"""
        # Mock 설정
        mock_client = AsyncMock()
        mock_zhipuai.return_value = mock_client

        mock_response = AsyncMock()
        mock_response.choices[0].message.content = "Extracted text"
        mock_client.chat.completions.create.return_value = mock_response

        # 실행
        result = await extract_text_with_glm("base64_data", "image/jpeg")

        # 검증
        assert result == "Extracted text"
        mock_client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_text_missing_api_key(self):
        """에러 케이스: GLM_API_KEY 미설정"""
        with patch("tutor.services.glm_ocr.get_settings") as mock_settings:
            mock_settings.return_value.GLM_API_KEY = ""

            with pytest.raises(ValueError) as exc_info:
                await extract_text_with_glm("base64_data", "image/jpeg")

            assert "GLM_API_KEY is not configured" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("tutor.services.glm_ocr.ZhipuAI")
    async def test_extract_text_api_error(self, mock_zhipuai):
        """에러 케이스: API 호출 실패"""
        mock_client = AsyncMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_zhipuai.return_value = mock_client

        with pytest.raises(Exception) as exc_info:
            await extract_text_with_glm("base64_data", "image/jpeg")

        assert "API Error" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("tutor.services.glm_ocr.ZhipuAI")
    async def test_extract_text_timeout(self, mock_zhipuai):
        """에러 케이스: 요청 타임아웃"""
        mock_client = AsyncMock()

        # 타임아웃 시뮬레이션
        async def slow_call(*args, **kwargs):
            await asyncio.sleep(60)

        mock_client.chat.completions.create = slow_call
        mock_zhipuai.return_value = mock_client

        with pytest.raises(TimeoutError):
            await extract_text_with_glm("base64_data", "image/jpeg", timeout=1)
```

---

## 5. 보안 주의사항

### 5.1 현재 보안 취약점

#### ⚠️ `.env.example` 파일의 실제 API 키 노출

현재 상태:
```env
GLM_API_KEY=sk-xxxxxxxxxxxxx  # ← 실제 키
OPENAI_API_KEY=sk-xxxxxxxxxxxxx  # ← 실제 키
ANTHROPIC_API_KEY=sk-xxxxxxxxxxxxx  # ← 실제 키
```

**위험 수준**: 🔴 **CRITICAL**

**영향**:
- `.env.example`은 버전 관리에 추적됨 (Git)
- 누구나 저장소 이력을 보면 키 접근 가능
- 키를 이용한 API 비용 도용 가능
- 보안 감사에서 적발 대상

### 5.2 해결 방안

#### Step 1: `.env.example` 즉시 수정

```env
# GLM (Zhipu AI) API Configuration
GLM_API_KEY=your_glm_api_key_here

# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic API Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

#### Step 2: Git 이력에서 노출된 키 제거

```bash
# 노출된 키 찾기
cd /path/to/repo
git log -S "sk-" --all -- "*.example"

# 해당 키를 즉시 폐기하고 새 키 생성
# (각 API 제공자의 대시보드에서 처리)
```

#### Step 3: 환경 변수 관리 정책

**권장 방식**:
```bash
# 로컬 개발 환경
# 1. .env 파일은 .gitignore에 추가 (절대 커밋 금지)
# 2. .env.example 유지 (플레이스홀더만)
# 3. 개발자 온보딩 문서에 .env 설정 방법 기술

# CI/CD 환경
# 1. GitHub Secrets에 실제 API 키 저장
# 2. GitHub Actions에서 환경 변수로 주입
# 3. 배포 시에만 실제 키 사용
```

---

## 6. 구현 순서 (7단계)

### 단계 1: 데이터 흐름 버그 수정 (우선순위: 🔴 CRITICAL)

**작업**: `src/app/api/tutor/analyze-image/route.ts` 수정

```bash
파일: /Users/byunjungwon/Dev/my-project-01/ai-english-tutor/src/app/api/tutor/analyze-image/route.ts
변경: FormData → base64 JSON 변환
예상 시간: 15분
```

**체크리스트**
- [ ] FormData를 base64로 변환
- [ ] MIME 타입 추출 추가
- [ ] JSON body로 전송
- [ ] Content-Type 헤더 설정

---

### 단계 2: 의존성 추가

**작업**: `backend/pyproject.toml`에 `zhipuai` 패키지 추가

```bash
파일: /Users/byunjungwon/Dev/my-project-01/ai-english-tutor/backend/pyproject.toml
변경: dependencies에 "zhipuai>=2.0.0,<3.0.0" 추가
실행: cd backend && uv sync
예상 시간: 10분
```

**체크리스트**
- [ ] `zhipuai>=2.0.0,<3.0.0` 추가
- [ ] 파이썬 버전 호환성 확인
- [ ] `uv sync` 실행 성공 확인

---

### 단계 3: 환경 설정 필드 추가

**작업**: `backend/src/tutor/config.py`에 GLM_API_KEY 필드 추가

```bash
파일: /Users/byunjungwon/Dev/my-project-01/ai-english-tutor/backend/src/tutor/config.py
변경: Settings 클래스에 GLM_API_KEY 필드 추가
예상 시간: 10분
```

**체크리스트**
- [ ] GLM_API_KEY 필드 추가
- [ ] Field 데이터 타입 설정
- [ ] 기본값 설정
- [ ] env 파일 매핑 확인

---

### 단계 4: `.env.example` 보안 강화 (우선순위: 🔴 CRITICAL)

**작업**: `.env.example` 업데이트 및 보안 감시

```bash
파일: /Users/byunjungwon/Dev/my-project-01/ai-english-tutor/backend/.env.example
변경: 실제 API 키 → 플레이스홀더로 교체
예상 시간: 20분
```

**체크리스트**
- [ ] 모든 실제 API 키를 플레이스홀더로 교체
- [ ] Git 이력에서 노출된 키 확인
- [ ] 노출된 키 즉시 폐기
- [ ] 새 API 키 생성 및 `.env` 파일에 설정
- [ ] `.env` 파일이 `.gitignore`에 포함되어 있는지 확인

---

### 단계 5: GLM OCR 서비스 구현 (신규)

**작업**: `backend/src/tutor/services/glm_ocr.py` 신규 생성

```bash
파일: /Users/byunjungwon/Dev/my-project-01/ai-english-tutor/backend/src/tutor/services/glm_ocr.py (신규)
내용: GLM-4V Plus를 사용한 비동기 OCR 함수
예상 시간: 30분
```

**체크리스트**
- [ ] `extract_text_with_glm` 함수 구현
- [ ] base64 데이터 처리
- [ ] API 키 검증
- [ ] 에러 처리 (API 오류, 타임아웃)
- [ ] 로깅 추가
- [ ] 타입 힌팅 적용
- [ ] 문서 문자열(docstring) 작성

---

### 단계 6: 이미지 처리 에이전트 수정

**작업**: `backend/src/tutor/agents/image_processor.py` 업데이트

```bash
파일: /Users/byunjungwon/Dev/my-project-01/ai-english-tutor/backend/src/tutor/agents/image_processor.py
변경: Claude 비전 → GLM OCR 서비스로 교체
예상 시간: 20분
```

**체크리스트**
- [ ] `extract_text_with_glm` import 추가
- [ ] `get_llm` 호출 제거
- [ ] GLM 서비스 호출로 변경
- [ ] 에러 처리 확인
- [ ] 기존 코드 테스트 (회귀)

---

### 단계 7: 테스트 업데이트 및 검증

**작업**: 단위 테스트 및 통합 테스트 수정

```bash
파일1: /Users/byunjungwon/Dev/my-project-01/ai-english-tutor/backend/tests/unit/test_agents.py (수정)
파일2: /Users/byunjungwon/Dev/my-project-01/ai-english-tutor/backend/tests/unit/test_services.py (수정)
파일3: /Users/byunjungwon/Dev/my-project-01/ai-english-tutor/backend/tests/integration/test_api.py (검증)
예상 시간: 40분
```

**테스트 체크리스트**
- [ ] `extract_text_with_glm` 성공 케이스 테스트
- [ ] API 키 미설정 에러 테스트
- [ ] GLM API 호출 실패 에러 테스트
- [ ] 타임아웃 에러 테스트
- [ ] `image_processor_node` 테스트 업데이트

**검증 단계**
- [ ] 백엔드 단위 테스트: `pytest tests/unit/test_agents.py tests/unit/test_services.py -v`
- [ ] 통합 테스트: `pytest tests/integration/test_api.py::TestAnalyzeImageEndpoint -v`
- [ ] 실제 기능 테스트:
  - [ ] 백엔드 실행: `cd backend && uv run uvicorn tutor.main:app --reload`
  - [ ] 프론트엔드 실행: `pnpm dev`
  - [ ] 이미지 업로드 → 텍스트 추출 → 분석 결과 확인

---

### 구현 순서 타임라인

```
┌─────────────────────────────────────────────────┐
│ 단계 1: 데이터 흐름 버그 수정 (15분) 🔴 우선   │
│ → route.ts 수정 완료 (FormData → JSON)          │
└──────────────┬──────────────────────────────────┘
               ↓
┌──────────────────────────────────────────────────┐
│ 단계 2: 의존성 추가 (10분)                        │
│ → pyproject.toml에 zhipuai 추가                  │
└──────────────┬──────────────────────────────────┘
               ↓
┌──────────────────────────────────────────────────┐
│ 단계 3: 환경 설정 필드 추가 (10분)               │
│ → config.py에 GLM_API_KEY 필드 추가              │
└──────────────┬──────────────────────────────────┘
               ↓
┌──────────────────────────────────────────────────┐
│ 단계 4: .env.example 보안 강화 (20분) 🔴 우선  │
│ → 실제 키 → 플레이스홀더 교체 + 키 폐기         │
└──────────────┬──────────────────────────────────┘
               ↓
┌──────────────────────────────────────────────────┐
│ 단계 5: GLM OCR 서비스 구현 (30분)              │
│ → glm_ocr.py 신규 생성                          │
└──────────────┬──────────────────────────────────┘
               ↓
┌──────────────────────────────────────────────────┐
│ 단계 6: 이미지 처리 에이전트 수정 (20분)        │
│ → image_processor.py 업데이트                    │
└──────────────┬──────────────────────────────────┘
               ↓
┌──────────────────────────────────────────────────┐
│ 단계 7: 테스트 업데이트 및 검증 (40분)          │
│ → 단위/통합 테스트 + 실제 기능 테스트            │
└──────────────────────────────────────────────────┘

⏱️  예상 총 소요 시간: 145분 (약 2.5시간)
```

---

## 7. 기술 스택 요약

| 항목 | 현재 | 변경 후 | 이유 |
|------|------|--------|------|
| OCR 엔진 | Claude Sonnet 4.5 비전 | GLM-4V Plus | 사용자 요청 + 비용 최적화 |
| 데이터 형식 | multipart/form-data | JSON (base64) | 데이터 형식 일치 |
| SDK | langchain | zhipuai | 전용 GLM 지원 |
| 에러 처리 | 기본 | 상세 (타임아웃, API 오류) | 안정성 향상 |

---

## 8. 참고 자료

### 공식 문서
- **Zhipu AI (GLM)**: https://open.bigmodel.cn/
- **GLM-4V Plus 문서**: https://open.bigmodel.cn/dev/api/ai-models/glm-4v

### 기술 링크
- **FastAPI 문서**: https://fastapi.tiangolo.com/
- **Next.js API Routes**: https://nextjs.org/docs/app/building-your-application/routing/route-handlers
- **Base64 인코딩**: https://developer.mozilla.org/en-US/docs/Glossary/Base64

---

**문서 끝**

작성일: 2026-02-22
상태: 구현 대기 중
검토자: jw
