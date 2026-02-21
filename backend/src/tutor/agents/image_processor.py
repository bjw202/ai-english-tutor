"""
Image processing agent.

Uses vision-capable LLM to extract text from images.
Supports JPEG, PNG, and WebP image formats.
"""

from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage

from tutor.models.llm import get_llm
from tutor.state import TutorState

logger = logging.getLogger(__name__)


async def image_processor_node(state: TutorState) -> dict:
    """
    Extract text from image using vision capabilities.

    Uses Claude Sonnet with vision capabilities to process images
    and extract any text content found in them.

    Args:
        state: TutorState containing image_data and mime_type fields

    Returns:
        Dictionary with "extracted_text" key containing extracted text or empty string
    """
    try:
        # Get image data from state
        # Note: This extends TutorState with temporary fields for image processing
        image_data = state.get("image_data", "")
        mime_type = state.get("mime_type", "image/jpeg")

        if not image_data:
            logger.warning("No image_data provided to image_processor_node")
            return {"extracted_text": ""}

        # Get vision-capable LLM
        llm = get_llm("claude-sonnet-4-5")

        # Create message with image content
        # Note: image_data should already be base64 encoded
        message = HumanMessage(
            content=[
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{image_data}"},
                },
                {
                    "type": "text",
                    "text": "Extract all text from this image. Return only the extracted text without any additional commentary.",
                },
            ]
        )

        # Call LLM
        response = await llm.ainvoke([message])

        # Extract text from response
        extracted_text = response.content.strip()

        # Handle "no text found" responses
        if extracted_text.lower() in ["no text found", "no text", ""]:
            return {"extracted_text": ""}

        return {"extracted_text": extracted_text}

    except Exception as e:
        logger.error(f"Error in image_processor_node: {e}")
        return {"extracted_text": ""}
