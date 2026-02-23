# 플랜: GLM OCR 구현 (이미지 → 텍스트 변환)

## Context

현재 이미지 업로드 후 OCR이 동작하지 않는다. 두 가지 문제가 존재한다:

1. **데이터 형식 불일치 (근본 원인)**: Next.js 프록시가 `multipart/form-data`로 파일을 전송하지만, FastAPI 백엔드는 JSON body(`image_data` base64 문자열)를 기대한다. 결과적으로 모든 이미지 분석 요청이 **422 Unprocessable Entity**로 실패한다.

2. **OCR 엔진 교체**: 현재 `image_processor.py`는 Claude Sonnet 4.5 비전을 사용하는데, 사용자가 GLM API의 OCR로 대체하길 원한다.

**목표**: 데이터 흐름 버그를 수정하고, GLM-4V Plus를 OCR 엔진으로 적용한다.

---

## 현재 데이터 흐름 (버그 있음)

```
Frontend → [FormData: file + level]
   → Next.js route.ts → [FormData: file + level]  ← 그대로 전달
   → FastAPI → AnalyzeImageRequest 파싱 시도 (JSON 기대) → 422 Error ❌
```

## 수정 후 데이터 흐름

```
Frontend → [FormData: file + level]
   → Next.js route.ts → File→base64 변환 + mime_type 추출 → [JSON: image_data + mime_type + level]
   → FastAPI → AnalyzeImageRequest 파싱 성공 → GLM OCR 실행 ✅
```

---

## 수정 파일 목록

### 1. `src/app/api/tutor/analyze-image/route.ts` (수정)

**변경 내용**: FormData를 백엔드로 그대로 전달하는 대신, File을 base64로 변환하여 JSON body로 전송.

```typescript
// 기존: FormData 그대로 전달 (버그)
const backendFormData = new FormData();
backendFormData.append("file", file);
backendFormData.append("level", level || "3");
const response = await fetch(`${BACKEND_URL}/api/v1/tutor/analyze-image`, {
  method: "POST",
  body: backendFormData,
});

// 수정: File → base64 변환 후 JSON 전송
const arrayBuffer = await file.arrayBuffer();
const base64 = Buffer.from(arrayBuffer).toString("base64");
const mimeType = file.type || "image/jpeg";
const response = await fetch(`${BACKEND_URL}/api/v1/tutor/analyze-image`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    image_data: base64,
    mime_type: mimeType,
    level: parseInt(level as string) || 3,
  }),
});
```

### 2. `backend/pyproject.toml` (수정)

**변경 내용**: `zhipuai` 패키지 추가.

```toml
dependencies = [
    ...
    "zhipuai>=2.0.0,<3.0.0",  # GLM API SDK 추가
]
```

### 3. `backend/.env.example` (수정)

**변경 내용**: GLM API 키 항목 추가 + 기존 실제 키 제거 (보안).

```env
# GLM (Zhipu AI) API Configuration
GLM_API_KEY=your_glm_api_key_here

# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic API Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

> **보안 주의**: 현재 `.env.example`에 실제 API 키가 노출되어 있음. 플레이스홀더로 교체 필요.

### 4. `backend/src/tutor/config.py` (수정)

**변경 내용**: `GLM_API_KEY` 설정 필드 추가.

```python
# GLM API Key (Required for image OCR)
GLM_API_KEY: str = Field(default="", alias="GLM_API_KEY")
```

### 5. `backend/src/tutor/services/glm_ocr.py` (신규 생성)

**변경 내용**: GLM-4V Plus를 사용한 OCR 서비스.

```python
"""GLM OCR service using Zhipu AI's vision model."""
import asyncio
import logging
from zhipuai import ZhipuAI
from tutor.config import get_settings

logger = logging.getLogger(__name__)

async def extract_text_with_glm(image_data: str, mime_type: str) -> str:
    """Extract text from image using GLM-4V Plus vision model."""
    settings = get_settings()
    client = ZhipuAI(api_key=settings.GLM_API_KEY)

    def _sync_call():
        response = client.chat.completions.create(
            model="glm-4v-plus",
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{image_data}"}
                    },
                    {
                        "type": "text",
                        "text": "Extract all text from this image. Return only the extracted text without any additional commentary."
                    }
                ]
            }]
        )
        return response.choices[0].message.content.strip()

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_call)
```

### 6. `backend/src/tutor/agents/image_processor.py` (수정)

**변경 내용**: Claude 비전 제거, GLM OCR 서비스 사용.

```python
# 기존: LangChain + Claude Sonnet 4.5 비전
from tutor.models.llm import get_llm
llm = get_llm("claude-sonnet-4-5")
message = HumanMessage(content=[...])
response = await llm.ainvoke([message])
extracted_text = response.content.strip()

# 수정: GLM OCR 서비스 직접 호출
from tutor.services.glm_ocr import extract_text_with_glm
extracted_text = await extract_text_with_glm(image_data, mime_type)
```

---

## 테스트 수정

### `backend/tests/unit/test_agents.py`

`image_processor_node` 테스트에서 `get_llm` mock을 제거하고, `glm_ocr.extract_text_with_glm` mock으로 교체.

### `backend/tests/unit/test_services.py`

새 파일 `glm_ocr.py`에 대한 단위 테스트 추가:
- `extract_text_with_glm` 성공 케이스
- API 오류 처리 케이스

---

## 검증 방법

1. **백엔드 단위 테스트**:
   ```bash
   cd backend && uv run pytest tests/unit/test_agents.py tests/unit/test_services.py -v
   ```

2. **통합 테스트**:
   ```bash
   cd backend && uv run pytest tests/integration/test_api.py::TestAnalyzeImageEndpoint -v
   ```

3. **실제 동작 확인**:
   - 백엔드 실행: `cd backend && uv run uvicorn tutor.main:app --reload`
   - 프론트엔드 실행: `pnpm dev`
   - 이미지 업로드 → 텍스트 추출 → 분석 결과 확인

---

## 구현 순서

1. Next.js `route.ts` 수정 (데이터 흐름 버그 수정)
2. `pyproject.toml`에 `zhipuai` 추가
3. `config.py`에 `GLM_API_KEY` 추가
4. `.env.example` 업데이트 (실제 키 제거 + GLM 키 추가)
5. `services/glm_ocr.py` 신규 생성
6. `agents/image_processor.py` 수정
7. 테스트 업데이트
