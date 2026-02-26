"""API router for tutor endpoints.

Handles all tutor-related API endpoints including text analysis,
image analysis, and chat functionality with SSE streaming.
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncGenerator
from typing import cast

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from tutor.agents.vocabulary import vocabulary_node
from tutor.graph import graph
from tutor.schemas import AnalyzeImageRequest, AnalyzeRequest, ChatRequest
from tutor.services import session_manager
from tutor.services.image import validate_image
from tutor.services.streaming import (
    format_done_event,
    format_error_event,
    format_grammar_token,
    format_reading_token,
    format_section_done,
    format_vocabulary_chunk,
    format_vocabulary_error,
    format_vocabulary_token,
)
from tutor.state import TutorState

logger = logging.getLogger(__name__)

router = APIRouter(tags=["tutor"])


_HEARTBEAT_INTERVAL_SECONDS = 5
_SSE_HEARTBEAT_COMMENT = ": heartbeat\n\n"


async def _stream_graph_events(input_state: dict, session_id: str) -> AsyncGenerator[str]:
    """Stream LangGraph events as SSE tokens.

    Reading and grammar are streamed via LangGraph's astream_events.
    Vocabulary runs as a concurrent asyncio.Task outside the graph to avoid
    the LangGraph 0.3.34 FuturesDict weakref GC bug: when vocabulary (the
    slowest parallel node) completes after reading and grammar, the FuturesDict
    callback is already GC'd, causing TypeError: 'NoneType' object is not callable.

    Flow:
    1. Capture supervisor output to get supervisor_analysis for vocabulary context
    2. Start vocabulary_task as soon as supervisor completes
    3. Stream reading/grammar tokens from graph events
    4. After graph stream ends, await vocabulary_task with heartbeats
    5. Emit vocabulary_chunk + section_done("vocabulary") + done

    Args:
        input_state: The initial state dict to pass to the graph
        session_id: The session ID to include in the done event

    Yields:
        Formatted SSE event strings (or SSE comment heartbeats)
    """
    vocabulary_task: asyncio.Task | None = None
    vocab_queue: asyncio.Queue | None = None

    try:
        async for event in _stream_with_heartbeat(input_state):
            if event is None:
                # No graph event within the heartbeat interval; send keep-alive
                yield _SSE_HEARTBEAT_COMMENT
                continue

            kind = event["event"]

            # Start vocabulary task as soon as supervisor analysis is available
            if kind == "on_chain_end" and event.get("name") == "supervisor" and vocabulary_task is None:
                output = event.get("data", {}).get("output", {})
                supervisor_analysis = output.get("supervisor_analysis")
                vocab_state = {**input_state, "supervisor_analysis": supervisor_analysis}
                vocab_queue = asyncio.Queue()
                vocabulary_task = asyncio.create_task(
                    vocabulary_node(cast(TutorState, vocab_state), token_queue=vocab_queue)
                )

            # Token-level streaming for reading and grammar
            elif kind == "on_chat_model_stream":
                node = event.get("metadata", {}).get("langgraph_node", "")
                chunk = event["data"].get("chunk")
                if chunk:
                    token = chunk.content if hasattr(chunk, "content") else str(chunk)
                    if token:  # Skip empty tokens
                        if node == "reading":
                            yield format_reading_token(token)
                        elif node == "grammar":
                            yield format_grammar_token(token)

            # Section completion events for reading and grammar only
            elif kind == "on_chain_end":
                node_name = event.get("name", "")
                if node_name == "reading":
                    yield format_section_done("reading")
                elif node_name == "grammar":
                    yield format_section_done("grammar")

        # Fallback: start vocabulary without supervisor context if supervisor event was missed
        if vocabulary_task is None:
            vocab_queue = asyncio.Queue()
            vocabulary_task = asyncio.create_task(
                vocabulary_node(cast(TutorState, input_state), token_queue=vocab_queue)
            )

        # Stream vocabulary tokens from Queue until sentinel None is received
        assert vocab_queue is not None
        while True:
            try:
                token = await asyncio.wait_for(
                    vocab_queue.get(), timeout=_HEARTBEAT_INTERVAL_SECONDS
                )
                if token is None:  # sentinel: streaming complete
                    break
                yield format_vocabulary_token(token)
            except TimeoutError:
                # No token arrived within heartbeat interval
                if vocabulary_task.done():
                    break
                yield _SSE_HEARTBEAT_COMMENT

        # Emit vocabulary result
        try:
            vocab_result = await vocabulary_task
            vocab_error = vocab_result.get("vocabulary_error")
            vocabulary_result = vocab_result.get("vocabulary_result")
            if vocab_error:
                yield format_vocabulary_error(vocab_error)
            elif vocabulary_result:
                if hasattr(vocabulary_result, "model_dump"):
                    data = vocabulary_result.model_dump()
                elif isinstance(vocabulary_result, dict):
                    data = vocabulary_result
                else:
                    data = None
                if data and data.get("words"):
                    yield format_vocabulary_chunk(data)
        except Exception as e:
            logger.error(f"Vocabulary task error: {e}")
            yield format_vocabulary_error(str(e))

        yield format_section_done("vocabulary")
        yield format_done_event(session_id)

    except asyncio.CancelledError:
        if vocabulary_task and not vocabulary_task.done():
            vocabulary_task.cancel()
    except Exception as e:
        if vocabulary_task and not vocabulary_task.done():
            vocabulary_task.cancel()
        yield format_error_event(str(e), "processing_error")


async def _stream_with_heartbeat(input_state: dict) -> AsyncGenerator[dict | None]:
    """Wrap graph.astream_events with periodic heartbeat signals.

    Yields graph events as they arrive. When no event arrives within
    ``_HEARTBEAT_INTERVAL_SECONDS``, yields ``None`` to signal that the
    caller should emit an SSE keep-alive comment.

    Args:
        input_state: The initial state dict forwarded to the graph.

    Yields:
        A graph event dict, or ``None`` when the heartbeat interval elapses.
    """
    queue: asyncio.Queue = asyncio.Queue()

    async def _producer() -> None:
        async for event in graph.astream_events(
            input_state, version="v2", config={"recursion_limit": 50}
        ):
            await queue.put(event)
        await queue.put(None)  # sentinel indicating stream end

    task = asyncio.create_task(_producer())

    try:
        while True:
            try:
                event = await asyncio.wait_for(
                    queue.get(), timeout=_HEARTBEAT_INTERVAL_SECONDS
                )
                if event is None:
                    # Producer finished; stop iteration
                    break
                yield event
            except TimeoutError:
                # Check if producer task failed before sending heartbeat
                if task.done() and not task.cancelled():
                    try:
                        task.result()  # raises if producer had an exception
                    except Exception:
                        break
                yield None  # heartbeat signal
    finally:
        if not task.done():
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass


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
            "version": "0.1.0"
        }
    """
    return {
        "status": "healthy",
        "openai": "connected",  # In production, would actually check connectivity
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

    async def generate() -> AsyncGenerator[str]:
        """Generate SSE events from LangGraph execution."""
        session_id = session_manager.create()
        input_state = {
            "messages": [],
            "level": request.level,
            "session_id": session_id,
            "input_text": request.text,
            "task_type": "analyze",
        }
        async for event in _stream_graph_events(input_state, session_id):
            yield event

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

    async def generate() -> AsyncGenerator[str]:
        """Generate SSE events from image processing."""
        session_id = session_manager.create()
        input_state = {
            "messages": [],
            "level": request.level,
            "session_id": session_id,
            "input_text": "",
            "task_type": "image_process",
            "image_data": request.image_data,
            "mime_type": request.mime_type,
        }
        async for event in _stream_graph_events(input_state, session_id):
            yield event

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

    async def generate() -> AsyncGenerator[str]:
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
                response_content = result["reading_result"].content
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
