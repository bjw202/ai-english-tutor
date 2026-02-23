---
id: SPEC-IMAGE-001
type: acceptance
version: 1.0.0
status: Draft
created: 2026-02-23
updated: 2026-02-23
author: jw
tags: [image-processing, ocr, supervisor, langgraph, pipeline-fix]
---

# SPEC-IMAGE-001: Acceptance Criteria

## AC-001: Image with Text - Full Pipeline with Supervisor Analysis

### Scenario 1: Image containing English text is processed through complete pipeline

```gherkin
Given the user submits an image containing English text
  And task_type is "image_process"
  And input_text is empty
  And the image contains readable English sentences

When the graph executes the workflow

Then supervisor_node is called first with task_type="image_process" and empty input_text
  And supervisor_node returns {} (skips pre-analysis due to empty input_text)
  And route_by_task routes to image_processor_node
  And image_processor_node calls GLM-OCR and extracts text from the image
  And route_after_image detects non-empty extracted_text
  And route_after_image sends to supervisor_node with task_type="analyze" and input_text=extracted_text
  And supervisor_node performs LLM pre-analysis on the extracted text
  And supervisor_node returns supervisor_analysis with sentences, difficulty scores, and focus areas
  And route_by_task dispatches to reading, grammar, and vocabulary agents in parallel
  And all three analysis agents receive supervisor_analysis in their state
  And aggregator collects results from all three agents
  And the final result contains reading_result, grammar_result, and vocabulary_result
```

### Verification Method

```python
async def test_image_pipeline_produces_supervisor_analysis():
    """Verify image pipeline routes through supervisor for pre-analysis."""
    graph = create_graph()

    result = await graph.ainvoke({
        "messages": [],
        "level": 3,
        "session_id": "test-session-001",
        "input_text": "",
        "task_type": "image_process",
        "image_data": "<valid-base64-image-data>",
        "mime_type": "image/jpeg",
    })

    # Supervisor analysis must be present
    assert result.get("supervisor_analysis") is not None
    assert len(result["supervisor_analysis"].sentences) > 0
    assert result["supervisor_analysis"].overall_difficulty >= 1
    assert result["supervisor_analysis"].overall_difficulty <= 5

    # All three analysis results must be present
    assert result.get("reading_result") is not None
    assert result.get("grammar_result") is not None
    assert result.get("vocabulary_result") is not None
```

## AC-002: Image without Text - Direct to Aggregator

### Scenario 2: Image without readable text skips analysis entirely

```gherkin
Given the user submits an image that contains no readable text
  And task_type is "image_process"
  And input_text is empty

When the graph executes the workflow

Then supervisor_node is called first and returns {} (skips due to empty input_text)
  And route_by_task routes to image_processor_node
  And image_processor_node calls GLM-OCR and returns empty extracted_text
  And route_after_image detects empty extracted_text
  And route_after_image sends directly to aggregator_node
  And supervisor_node is NOT called a second time
  And reading, grammar, and vocabulary agents are NOT executed
  And the final result contains no analysis results
```

### Verification Method

```python
async def test_image_without_text_skips_analysis():
    """Verify empty OCR result routes directly to aggregator."""
    graph = create_graph()

    result = await graph.ainvoke({
        "messages": [],
        "level": 3,
        "session_id": "test-session-002",
        "input_text": "",
        "task_type": "image_process",
        "image_data": "<base64-blank-image>",
        "mime_type": "image/png",
    })

    # No supervisor analysis (second pass never happened)
    # supervisor_analysis may be None or missing
    supervisor = result.get("supervisor_analysis")
    assert supervisor is None or supervisor == {}

    # No analysis results (agents were not dispatched)
    assert result.get("reading_result") is None
    assert result.get("grammar_result") is None
    assert result.get("vocabulary_result") is None
```

## AC-003: TutorState Fields Preserved

### Scenario 3: image_data and mime_type are not dropped by LangGraph

```gherkin
Given TutorState includes image_data and mime_type as NotRequired fields
  And the user provides image_data and mime_type in the initial state

When the graph starts execution

Then image_data and mime_type are available in the state at image_processor_node
  And image_processor_node can read state.get("image_data") with the provided value
  And image_processor_node can read state.get("mime_type") with the provided value
```

### Verification Method

```python
def test_tutor_state_includes_image_fields():
    """Verify TutorState has image_data and mime_type fields."""
    from tutor.state import TutorState
    import typing

    hints = typing.get_type_hints(TutorState, include_extras=True)
    assert "image_data" in hints, "TutorState must include image_data field"
    assert "mime_type" in hints, "TutorState must include mime_type field"
```

## AC-004: Direct Text Input Not Affected

### Scenario 4: Regular text analysis flow remains unchanged

```gherkin
Given the user submits text directly (not via image)
  And task_type is "analyze"
  And input_text contains English text

When the graph executes the workflow

Then supervisor_node is called exactly once with task_type="analyze" and non-empty input_text
  And supervisor_node produces supervisor_analysis
  And route_by_task dispatches to reading, grammar, and vocabulary agents in parallel
  And all three agents receive supervisor_analysis
  And aggregator collects all results
  And the behavior is identical to the pre-fix flow for text input
```

### Verification Method

```python
async def test_text_analysis_flow_unchanged():
    """Verify direct text input still works correctly after the fix."""
    graph = create_graph()

    result = await graph.ainvoke({
        "messages": [],
        "level": 3,
        "session_id": "test-session-003",
        "input_text": "The quick brown fox jumps over the lazy dog.",
        "task_type": "analyze",
    })

    # Supervisor analysis must be present
    assert result.get("supervisor_analysis") is not None

    # All analysis results must be present
    assert result.get("reading_result") is not None
    assert result.get("grammar_result") is not None
    assert result.get("vocabulary_result") is not None
```

## AC-005: Supervisor Fallback on LLM Failure

### Scenario 5: Supervisor LLM failure for OCR text triggers fallback analysis

```gherkin
Given image_processor_node extracted text successfully
  And route_after_image routed to supervisor with extracted text
  And supervisor LLM call fails (network error, timeout, invalid response)

When supervisor_node handles the exception

Then supervisor_node uses _fallback_analysis with the extracted text
  And supervisor_analysis is still produced (basic period-based splitting)
  And analysis agents still receive supervisor_analysis context
  And the pipeline does not fail entirely
```

## Quality Gates

### Definition of Done

- [ ] `route_after_image` routes non-empty OCR text through supervisor with `task_type="analyze"`
- [ ] `route_after_image` routes empty OCR text directly to aggregator
- [ ] Direct text analysis (`task_type="analyze"`) flow is not affected
- [ ] `TutorState` includes `image_data` and `mime_type` fields
- [ ] `supervisor_analysis` is present in final result for image tasks with text
- [ ] No infinite loop possible in the graph (verified by `task_type` transition)
- [ ] Unit tests cover all 5 acceptance criteria scenarios
- [ ] Test coverage >= 85% for modified files

### Test Coverage Requirements

| File | Minimum Coverage |
|---|---|
| `backend/src/tutor/graph.py` | 85% |
| `backend/src/tutor/state.py` | 90% |
| `backend/src/tutor/agents/supervisor.py` | 85% |
| `backend/src/tutor/agents/image_processor.py` | 85% |
