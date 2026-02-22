"""API router for tutor endpoints.

Handles all tutor-related API endpoints including text analysis,
image analysis, and chat functionality with SSE streaming.
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncGenerator

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from tutor.graph import graph
from tutor.schemas import AnalyzeImageRequest, AnalyzeRequest, ChatRequest
from tutor.services import session_manager
from tutor.services.image import validate_image
from tutor.services.streaming import (
    format_done_event,
    format_error_event,
    format_grammar_chunk,
    format_reading_chunk,
    format_vocabulary_chunk,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["tutor"])


@router.get("/health")
async def health() -> dict:
    """Health check endpoint.

    Returns service status and connectivity information.

    Returns:
        Dict with status, LLM connectivity status, and version

    Example:
        >>> GET /api/v1/health
        {
            "status": "healthy",
            "openai": "connected",
            "anthropic": "connected",
            "version": "0.1.0"
        }
    """
    return {
        "status": "healthy",
        "openai": "connected",  # In production, would actually check connectivity
        "anthropic": "connected",
        "version": "0.1.0",
    }


@router.post("/tutor/analyze")
async def analyze(request: AnalyzeRequest) -> StreamingResponse:
    """Analyze text and stream results via Server-Sent Events.

    Executes the LangGraph pipeline with reading, grammar, and vocabulary
    agents running in parallel. Results are streamed as SSE events.

    Args:
        request: AnalyzeRequest containing text and proficiency level

    Returns:
        StreamingResponse with SSE events

    SSE Events:
        - reading_chunk: Reading comprehension analysis
        - grammar_chunk: Grammar analysis results
        - vocabulary_chunk: Vocabulary analysis results
        - done: Session completion with session_id
        - error: Error information if processing fails

    Example:
        >>> POST /api/v1/tutor/analyze
        {
            "text": "The quick brown fox jumps over the lazy dog.",
            "level": 3
        }
    """

    async def generate() -> AsyncGenerator[str, None]:
        """Generate SSE events from LangGraph execution."""
        try:
            # Create new session
            session_id = session_manager.create()

            # Run LangGraph pipeline
            result = await graph.ainvoke(
                {
                    "messages": [],
                    "level": request.level,
                    "session_id": session_id,
                    "input_text": request.text,
                    "task_type": "analyze",
                }
            )

            # Stream results as SSE events
            if result.get("reading_result"):
                yield format_reading_chunk(result["reading_result"].model_dump())

            if result.get("grammar_result"):
                yield format_grammar_chunk(result["grammar_result"].model_dump())

            if result.get("vocabulary_result"):
                yield format_vocabulary_chunk(result["vocabulary_result"].model_dump())

            yield format_done_event(session_id)

        except Exception as e:
            yield format_error_event(str(e), "processing_error")

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/tutor/analyze-image")
async def analyze_image(request: AnalyzeImageRequest) -> StreamingResponse:
    """Analyze image and stream results via Server-Sent Events.

    Processes the image to extract text, then runs the LangGraph pipeline
    with the extracted text. Results are streamed as SSE events.

    Args:
        request: AnalyzeImageRequest containing base64 image data and level

    Returns:
        StreamingResponse with SSE events

    Raises:
        HTTPException: If image validation fails (400 status)

    SSE Events:
        - Same as /tutor/analyze endpoint

    Example:
        >>> POST /api/v1/tutor/analyze-image
        {
            "image_data": "iVBORw0KG...",
            "mime_type": "image/png",
            "level": 3
        }
    """
    # Validate image
    is_valid, error_msg = validate_image(request.image_data, request.mime_type)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )

    async def generate() -> AsyncGenerator[str, None]:
        """Generate SSE events from image processing."""
        try:
            # Create new session
            session_id = session_manager.create()

            # Run LangGraph pipeline for image processing
            result = await graph.ainvoke(
                {
                    "messages": [],
                    "level": request.level,
                    "session_id": session_id,
                    "input_text": "",  # Will be populated from image
                    "task_type": "image_process",
                    "image_data": request.image_data,
                    "mime_type": request.mime_type,
                }
            )

            # Stream results as SSE events
            if result.get("reading_result"):
                yield format_reading_chunk(result["reading_result"].model_dump())

            if result.get("grammar_result"):
                yield format_grammar_chunk(result["grammar_result"].model_dump())

            if result.get("vocabulary_result"):
                yield format_vocabulary_chunk(result["vocabulary_result"].model_dump())

            yield format_done_event(session_id)

        except Exception as e:
            yield format_error_event(str(e), "processing_error")

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/tutor/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    """Handle chat with session context via Server-Sent Events.

    Retrieves session history for context-aware conversation.
    Creates a new session if session_id is not found.

    Args:
        request: ChatRequest containing session_id, question, and level

    Returns:
        StreamingResponse with SSE events

    SSE Events:
        - chat_chunk: Streaming response content
        - done: Session completion with session_id
        - error: Error information if processing fails

    Example:
        >>> POST /api/v1/tutor/chat
        {
            "session_id": "abc-123",
            "question": "What does 'ubiquitous' mean?",
            "level": 3
        }
    """
    # Get or create session
    session = session_manager.get(request.session_id)
    if not session:
        # Create new session
        session_id = session_manager.create()
    else:
        session_id = request.session_id

    async def generate() -> AsyncGenerator[str, None]:
        """Generate SSE events from chat processing."""
        try:
            # Add user message to session
            session_manager.add_message(session_id, "user", request.question)

            # Run LangGraph pipeline for chat
            result = await graph.ainvoke(
                {
                    "messages": session.get("messages", []),
                    "level": request.level,
                    "session_id": session_id,
                    "input_text": request.question,
                    "task_type": "chat",
                }
            )

            # Stream response (assuming aggregator formats output)
            # For now, yield a simple chat response
            if result.get("reading_result"):
                response_content = result["reading_result"].summary
                yield f"event: chat_chunk\ndata: {json.dumps({'content': response_content, 'role': 'assistant'})}\n\n"

            yield format_done_event(session_id)

        except Exception as e:
            yield format_error_event(str(e), "processing_error")

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
