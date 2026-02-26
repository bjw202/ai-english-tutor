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

from tutor.agents.grammar import grammar_node
from tutor.agents.reading import reading_node
from tutor.agents.supervisor import supervisor_node
from tutor.agents.vocabulary import vocabulary_node
from tutor.graph import graph
from tutor.schemas import AnalyzeImageRequest, AnalyzeRequest, ChatRequest
from tutor.services import session_manager
from tutor.services.image import validate_image
from tutor.services.streaming import (
    format_done_event,
    format_error_event,
    format_grammar_error,
    format_grammar_token,
    format_reading_error,
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


async def _merge_agent_streams(
    reading_queue: asyncio.Queue,
    grammar_queue: asyncio.Queue,
    vocab_queue: asyncio.Queue,
) -> AsyncGenerator[str, None]:
    """Merge 3 agent token queues into a single SSE stream using FIRST_COMPLETED.

    Each agent delivers tokens via its queue. A None sentinel signals completion.
    Uses asyncio.wait(FIRST_COMPLETED) to interleave tokens in arrival order.

    Args:
        reading_queue: Queue for reading agent tokens
        grammar_queue: Queue for grammar agent tokens
        vocab_queue: Queue for vocabulary agent tokens

    Yields:
        Formatted SSE event strings (reading_token, grammar_token, vocabulary_token)
        or SSE heartbeat comments on timeout.
    """
    queues = {
        "reading": reading_queue,
        "grammar": grammar_queue,
        "vocabulary": vocab_queue,
    }
    formatters = {
        "reading": format_reading_token,
        "grammar": format_grammar_token,
        "vocabulary": format_vocabulary_token,
    }
    active = set(queues.keys())

    while active:
        get_tasks = {
            name: asyncio.create_task(queues[name].get())
            for name in active
        }

        done, pending = await asyncio.wait(
            list(get_tasks.values()),
            timeout=_HEARTBEAT_INTERVAL_SECONDS,
            return_when=asyncio.FIRST_COMPLETED,
        )

        if not done:
            # Timeout: no tokens arrived -> emit heartbeat
            yield _SSE_HEARTBEAT_COMMENT
            for t in pending:
                t.cancel()
            continue

        # Map task back to agent name
        task_to_name = {v: k for k, v in get_tasks.items()}
        for task in done:
            agent_name = task_to_name[task]
            try:
                token = task.result()
            except Exception:
                # Task failed - treat as sentinel
                active.discard(agent_name)
                continue
            if token is None:
                active.discard(agent_name)
            else:
                yield formatters[agent_name](token)

        for t in pending:
            t.cancel()


async def _stream_analyze_events(
    input_state: dict,
    session_id: str,
) -> AsyncGenerator[str, None]:
    """Stream analyze flow events using direct asyncio.Task parallel execution.

    Bypasses LangGraph for the analyze flow. Calls supervisor directly,
    then runs reading, grammar, vocabulary as concurrent asyncio.Tasks,
    each streaming tokens via their own asyncio.Queue.

    Args:
        input_state: The state dict with input_text, level, supervisor_analysis (optional), etc.
        session_id: Session ID for the done event

    Yields:
        Formatted SSE event strings
    """
    try:
        # Step 1: Supervisor direct call (skip if supervisor_analysis already in state)
        supervisor_analysis = input_state.get("supervisor_analysis")
        if supervisor_analysis is None:
            supervisor_result = await supervisor_node(cast(TutorState, input_state))
            supervisor_analysis = supervisor_result.get("supervisor_analysis")

        agent_state = {**input_state, "supervisor_analysis": supervisor_analysis}

        # Step 2: Create per-agent queues
        reading_queue: asyncio.Queue = asyncio.Queue()
        grammar_queue: asyncio.Queue = asyncio.Queue()
        vocab_queue: asyncio.Queue = asyncio.Queue()

        # Step 3: Launch 3 agent tasks concurrently
        reading_task = asyncio.create_task(
            reading_node(cast(TutorState, agent_state), token_queue=reading_queue)
        )
        grammar_task = asyncio.create_task(
            grammar_node(cast(TutorState, agent_state), token_queue=grammar_queue)
        )
        vocab_task = asyncio.create_task(
            vocabulary_node(cast(TutorState, agent_state), token_queue=vocab_queue)
        )

        # Step 4: Merge token streams from all 3 queues
        async for sse_event in _merge_agent_streams(reading_queue, grammar_queue, vocab_queue):
            yield sse_event

        # Step 5: Await all results (exceptions captured, not raised)
        results = await asyncio.gather(
            reading_task, grammar_task, vocab_task, return_exceptions=True
        )

        # Step 6: Emit section done + error events
        # Reading result
        if isinstance(results[0], Exception):
            yield format_reading_error(str(results[0]))
        yield format_section_done("reading")

        # Grammar result
        if isinstance(results[1], Exception):
            yield format_grammar_error(str(results[1]))
        yield format_section_done("grammar")

        # Vocabulary result
        if isinstance(results[2], Exception):
            yield format_vocabulary_error(str(results[2]))
        else:
            vocab_result = results[2]
            if isinstance(vocab_result, dict):
                vocab_error = vocab_result.get("vocabulary_error")
                vocabulary_result = vocab_result.get("vocabulary_result")
                if vocab_error:
                    yield format_vocabulary_error(vocab_error)
                elif vocabulary_result and hasattr(vocabulary_result, "model_dump"):
                    data = vocabulary_result.model_dump()
                    if data.get("words"):
                        yield format_vocabulary_chunk(data)
        yield format_section_done("vocabulary")

        yield format_done_event(session_id)

    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.error(f"Error in _stream_analyze_events: {e}")
        yield format_error_event(str(e), "processing_error")


async def _stream_graph_events(input_state: dict, session_id: str) -> AsyncGenerator[str, None]:
    """Stream graph events as SSE tokens.

    For analyze task_type: Uses direct asyncio.Task parallel execution (SPEC-VOCAB-003).
    Reading, grammar, and vocabulary agents are run as concurrent asyncio.Tasks,
    each streaming tokens via their own asyncio.Queue.

    For image_process task_type: Streams LangGraph events for OCR+supervisor,
    then delegates to _stream_analyze_events with captured state.

    Args:
        input_state: The initial state dict
        session_id: The session ID for the done event

    Yields:
        Formatted SSE event strings
    """
    task_type = input_state.get("task_type", "analyze")

    if task_type == "analyze":
        # Direct asyncio.Task execution, no LangGraph
        async for event in _stream_analyze_events(input_state, session_id):
            yield event
        return

    # image_process: run image_processor + supervisor via LangGraph
    # then delegate to _stream_analyze_events with captured state
    extracted_text = ""
    supervisor_analysis = None

    try:
        async for event in _stream_with_heartbeat(input_state):
            if event is None:
                yield _SSE_HEARTBEAT_COMMENT
                continue

            kind = event["event"]

            # Capture extracted text from image_processor
            if kind == "on_chain_end" and event.get("name") == "image_processor":
                output = event.get("data", {}).get("output", {})
                extracted_text = output.get("extracted_text", "")

            # Capture supervisor analysis (may fire twice; take the latest)
            if kind == "on_chain_end" and event.get("name") == "supervisor":
                output = event.get("data", {}).get("output", {})
                analysis = output.get("supervisor_analysis")
                if analysis is not None:
                    supervisor_analysis = analysis

        # Graph stream ended. Now stream the analyze phase.
        if not extracted_text:
            # No text was extracted from the image - emit done event only
            yield format_done_event(session_id)
            return

        analyze_state = {
            **input_state,
            "input_text": extracted_text,
            "task_type": "analyze",
            "supervisor_analysis": supervisor_analysis,
        }
        async for event in _stream_analyze_events(analyze_state, session_id):
            yield event

    except asyncio.CancelledError:
        raise
    except Exception as e:
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

    Executes reading, grammar, and vocabulary agents as concurrent asyncio.Tasks
    (SPEC-VOCAB-003), bypassing LangGraph for the analyze flow. Results are
    streamed as SSE events in real-time as each agent produces tokens.

    Args:
        request: AnalyzeRequest containing text and proficiency level

    Returns:
        StreamingResponse with SSE events

    SSE Events:
        - reading_token: Individual token from reading agent LLM stream
        - grammar_token: Individual token from grammar agent LLM stream
        - vocabulary_token: Individual token from vocabulary agent LLM stream
        - reading_done: Reading section complete
        - grammar_done: Grammar section complete
        - vocabulary_done: Vocabulary section complete
        - vocabulary_chunk: Final vocabulary structured data
        - reading_error: Error from reading agent (if any)
        - grammar_error: Error from grammar agent (if any)
        - vocabulary_error: Error from vocabulary agent (if any)
        - done: Session completion with session_id
        - error: Critical error information if processing fails

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
