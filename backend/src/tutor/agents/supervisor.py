"""
Supervisor agent for task routing.

Determines which agents to execute based on the task_type field in the state:
- "analyze": Routes to parallel execution of Reading, Grammar, and Vocabulary agents
- "image_process": Routes to ImageProcessor agent first
- "chat": Routes to chat handling node
"""

from __future__ import annotations

from tutor.state import TutorState


def supervisor_node(state: TutorState) -> dict:
    """
    Determine next action based on task_type.

    This routing function examines the task_type field and returns
    a list of node names that should be executed next.

    Args:
        state: Current TutorState containing task_type and other fields

    Returns:
        Dictionary with "next_nodes" key containing list of node names

    Examples:
        >>> supervisor_node({"task_type": "analyze", ...})
        {"next_nodes": ["reading", "grammar", "vocabulary"]}

        >>> supervisor_node({"task_type": "image_process", ...})
        {"next_nodes": ["image_processor"]}

        >>> supervisor_node({"task_type": "chat", ...})
        {"next_nodes": ["chat"]}
    """
    task_type = state.get("task_type", "analyze")

    if task_type == "analyze":
        return {"next_nodes": ["reading", "grammar", "vocabulary"]}
    elif task_type == "image_process":
        return {"next_nodes": ["image_processor"]}
    elif task_type == "chat":
        return {"next_nodes": ["chat"]}

    return {"next_nodes": []}
