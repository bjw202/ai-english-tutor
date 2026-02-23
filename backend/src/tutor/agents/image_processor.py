"""
Image processing agent.

Uses OpenAI Vision API to extract text from images.
Supports JPEG, PNG, and WebP image formats.
"""

from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from tutor.config import get_settings
from tutor.state import TutorState

logger = logging.getLogger(__name__)

OCR_PROMPT = """Extract only the main reading passage text from this image.
Rules:
- Include: Main passage/article text only
- Exclude: Question numbers, answer choices, instructions, headers
- Preserve: Original paragraph structure and line breaks
- Output: Plain text only, no markdown"""


async def image_processor_node(state: TutorState) -> dict:
    """
    Extract text from image using OpenAI Vision API.

    Sends the base64 image to ChatOpenAI with a text extraction prompt.
    Returns extracted text or raises RuntimeError on failure.

    Args:
        state: TutorState containing image_data (base64) and mime_type fields

    Returns:
        Dictionary with "extracted_text" and "input_text" keys
    """
    try:
        image_data = state.get("image_data", "")
        mime_type = state.get("mime_type", "image/jpeg")

        if not image_data:
            logger.warning("No image_data provided to image_processor_node")
            return {"extracted_text": "", "input_text": ""}

        settings = get_settings()

        # @MX:NOTE: [AUTO] Uses ChatOpenAI directly (not get_llm factory) for Vision-specific parameters (detail, image_url content type).
        # @MX:REASON: get_llm() factory does not support Vision-specific HumanMessage image_url format.
        llm = ChatOpenAI(
            model=settings.OCR_MODEL,
            max_tokens=settings.OCR_MAX_TOKENS,
            api_key=settings.OPENAI_API_KEY,
        )
        message = HumanMessage(content=[
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{image_data}",
                    "detail": settings.OCR_DETAIL,
                },
            },
            {"type": "text", "text": OCR_PROMPT},
        ])
        response = await llm.ainvoke([message])
        extracted_text = response.content.strip()

        if not extracted_text:
            logger.info("OpenAI Vision returned empty response")
            raise RuntimeError("이미지에서 텍스트를 찾을 수 없습니다. 영어 텍스트가 포함된 이미지를 업로드해 주세요.")

        logger.info(f"OpenAI Vision extracted {len(extracted_text)} characters")
        return {"extracted_text": extracted_text, "input_text": extracted_text}

    except RuntimeError:
        raise
    except Exception as e:
        logger.error(f"Error in image_processor_node: {e}")
        raise RuntimeError("이미지 처리 중 오류가 발생했습니다. 다시 시도해 주세요.")
