"""
LangGraph workflow graph for AI English Tutor.

Defines the multi-agent workflow graph using LangGraph's StateGraph
with Send() API for parallel agent dispatch.
"""

from __future__ import annotations

from langgraph.constants import END, START
from langgraph.graph import StateGraph
from langgraph.types import Send

from tutor.agents.aggregator import aggregator_node
from tutor.agents.grammar import grammar_node
from tutor.agents.image_processor import image_processor_node
from tutor.agents.reading import reading_node
from tutor.agents.supervisor import supervisor_node
from tutor.agents.vocabulary import vocabulary_node
from tutor.state import TutorState


def route_by_task(state: TutorState) -> list[Send]:
    """
    Route to appropriate nodes based on task_type.

    This routing function uses LangGraph's Send() API to dispatch
    agents either in parallel or sequentially based on the task_type.

    Args:
        state: Current TutorState containing task_type field

    Returns:
        List of Send objects for parallel dispatch:
        - analyze: 3 Send objects (reading, grammar, vocabulary) in parallel
        - image_process: 1 Send object (image_processor)
        - chat: 1 Send object (chat)
        - unknown: Empty list

    Examples:
        >>> route_by_task({"task_type": "analyze", ...})
        [Send('reading', {...}), Send('grammar', {...}), Send('vocabulary', {...})]

        >>> route_by_task({"task_type": "image_process", ...})
        [Send('image_processor', {...})]
    """
    task_type = state.get("task_type", "analyze")

    if task_type == "analyze":
        # Dispatch all three tutor agents in parallel
        return [
            Send("reading", state),
            Send("grammar", state),
            Send("vocabulary", state),
        ]
    elif task_type == "image_process":
        # Route to image processor first
        return [Send("image_processor", state)]
    elif task_type == "chat":
        # Route to chat handler
        return [Send("chat", state)]

    # Unknown task type - return empty list
    return []


def create_graph():
    """
    Create and compile the LangGraph workflow.

    Builds a StateGraph with the following structure:

        [START]
          ↓
        [supervisor]  ← task_type 판단
          ↓ (조건부 엣지 via route_by_task)
          ├─ "analyze" → Send(3 튜터) [병렬 실행]
          ├─ "image_process" → [image_processor] → [aggregator]
          └─ "chat" → [chat]
          ↓
        [aggregator]  ← 병렬 결과 수집
          ↓
        [END]

    Nodes:
        - supervisor: Entry point that determines routing based on task_type
        - reading: Reading comprehension analysis (parallel for analyze)
        - grammar: Grammar analysis (parallel for analyze)
        - vocabulary: Vocabulary analysis (parallel for analyze)
        - image_processor: OCR and text extraction from images
        - aggregator: Combines results from all agents into unified response

    Returns:
        Compiled StateGraph ready for invocation or streaming

    Example:
        >>> graph = create_graph()
        >>> result = await graph.ainvoke({
        ...     "messages": [],
        ...     "level": 3,
        ...     "session_id": "abc-123",
        ...     "input_text": "Hello world",
        ...     "task_type": "analyze"
        ... })
    """
    workflow = StateGraph(TutorState)

    # Add all nodes to the graph
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("reading", reading_node)
    workflow.add_node("grammar", grammar_node)
    workflow.add_node("vocabulary", vocabulary_node)
    workflow.add_node("image_processor", image_processor_node)
    workflow.add_node("aggregator", aggregator_node)

    # Set entry point from START to supervisor
    workflow.add_edge(START, "supervisor")

    # Add conditional edges from supervisor based on task_type
    # The route_by_task function returns a list of Send objects
    # that will be dispatched in parallel
    workflow.add_conditional_edges("supervisor", route_by_task)

    # All tutor nodes lead to aggregator for result collection
    workflow.add_edge("reading", "aggregator")
    workflow.add_edge("grammar", "aggregator")
    workflow.add_edge("vocabulary", "aggregator")
    workflow.add_edge("image_processor", "aggregator")

    # Exit point from aggregator to END
    workflow.add_edge("aggregator", END)

    # Compile and return the graph
    return workflow.compile()


# Global graph instance for convenient importing
# This can be imported as: from tutor.graph import graph
graph = create_graph()
