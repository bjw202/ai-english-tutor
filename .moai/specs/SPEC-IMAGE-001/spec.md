---
id: SPEC-IMAGE-001
version: 1.0.0
status: Completed
created: 2026-02-23
updated: 2026-02-23
author: jw
priority: High
tags: [image-processing, ocr, supervisor, langgraph, pipeline-fix]
related_specs: [SPEC-GLM-001]
lifecycle: spec-anchored
---

# SPEC-IMAGE-001: Image Processing Pipeline - Supervisor Re-routing Fix

## Environment

- **Runtime**: Python 3.13+, FastAPI backend
- **Workflow Engine**: LangGraph StateGraph with Send() API
- **OCR Service**: GLM-OCR (`/layout_parsing` endpoint)
- **LLM (Supervisor)**: Claude Haiku (pre-analysis)
- **Target Files**:
  - `backend/src/tutor/graph.py` - Workflow graph definition
  - `backend/src/tutor/state.py` - TutorState TypedDict
  - `backend/src/tutor/agents/image_processor.py` - OCR agent
  - `backend/src/tutor/agents/supervisor.py` - Supervisor agent

## Assumptions

1. `image_data` and `mime_type` fields are already added to `TutorState` (confirmed in current codebase, lines 49-51 of `state.py`)
2. `supervisor_node` already handles `task_type="image_process"` in its guard condition (line 59 of `supervisor.py`), but skips when `input_text` is empty
3. GLM-OCR `image_processor_node` already returns `extracted_text` and `input_text` correctly
4. The `route_by_task` function correctly routes `task_type="image_process"` to `image_processor` node
5. Analysis agents (`reading`, `grammar`, `vocabulary`) depend on `supervisor_analysis` for sentence-level difficulty scoring and focus area recommendations
6. The graph structure supports `Send()` for dynamic routing from conditional edges

## Requirements

### REQ-IMG-001: OCR-Extracted Text Must Pass Through Supervisor

**WHEN** `image_processor_node` completes OCR extraction and `extracted_text` is non-empty,
**THEN** the system shall route the extracted text to `supervisor_node` with `task_type="analyze"` and `input_text` set to the extracted text, before dispatching to analysis agents.

### REQ-IMG-002: Supervisor Analysis Available to Analysis Agents

**WHEN** `supervisor_node` receives re-routed OCR text with `task_type="analyze"` and non-empty `input_text`,
**THEN** the system shall produce a `supervisor_analysis` result containing sentence segmentation, difficulty scores, and focus recommendations, making it available to downstream `reading`, `grammar`, and `vocabulary` agents.

### REQ-IMG-003: Empty OCR Result Handling

**IF** `image_processor_node` returns empty `extracted_text` (OCR failure or image without text),
**THEN** the system shall route directly to `aggregator_node`, skipping both supervisor re-analysis and analysis agents.

### REQ-IMG-004: State Field Integrity

The system shall **always** include `image_data` and `mime_type` as optional fields in `TutorState` so that LangGraph does not silently drop these values from `input_state`.

### REQ-IMG-005: No Duplicate Supervisor Execution for Text Input

**WHEN** `task_type` is `"analyze"` (direct text input, not image),
**THEN** the system shall execute `supervisor_node` exactly once, following the existing flow without re-routing.

## Specifications

### Current Architecture (Broken)

```
START -> supervisor(task_type="image_process", input_text="") -> SKIPS (empty input)
      |
route_by_task("image_process")
      |
image_processor (GLM-OCR) -> extracted_text="..."
      |
route_after_image (extracted_text non-empty)
      |
reading/grammar/vocabulary (PARALLEL, NO supervisor_analysis)
      |
aggregator -> END
```

**Root Cause**: `supervisor_node` (line 59) has guard `if task_type not in ("analyze", "image_process") or not input_text: return {}`. For image tasks, `input_text` is initially empty, so supervisor always returns `{}`. After OCR extracts text, `route_after_image` sends directly to analysis agents, bypassing supervisor entirely.

### Target Architecture (Correct)

```
START -> supervisor(task_type="image_process", input_text="") -> SKIPS (empty input)
      |
route_by_task("image_process")
      |
image_processor (GLM-OCR) -> extracted_text="..."
      |
route_after_image (extracted_text non-empty)
      |
Send("supervisor", {input_text=extracted_text, task_type="analyze"})
      |
supervisor(task_type="analyze", input_text=extracted_text) -> supervisor_analysis
      |
route_by_task("analyze")
      |
reading/grammar/vocabulary (PARALLEL, WITH supervisor_analysis)
      |
aggregator -> END
```

### Implementation Details

#### 1. `route_after_image` Modification (`graph.py`)

The `route_after_image` function must be updated to route through `supervisor` instead of directly to analysis agents:

- **WHEN** `extracted_text` is non-empty: Return `[Send("supervisor", new_state)]` where `new_state` includes `input_text=extracted_text` and `task_type="analyze"`
- **WHEN** `extracted_text` is empty: Return `[Send("aggregator", state)]` (unchanged)

This ensures extracted text goes through supervisor for pre-analysis before reaching analysis agents.

#### 2. `TutorState` Fields (`state.py`)

`image_data: NotRequired[str | None]` and `mime_type: NotRequired[str | None]` are already present. This SPEC formally documents the requirement and ensures they remain in the state definition.

#### 3. No Changes Required

- `supervisor_node` (`supervisor.py`): Already handles `task_type="analyze"` with non-empty `input_text` correctly. No modification needed.
- `image_processor_node` (`image_processor.py`): Already returns `extracted_text` and `input_text`. No modification needed.
- `route_by_task` (`graph.py`): Already routes `task_type="analyze"` to parallel analysis agents. No modification needed.

### Constraints

- The fix must not alter behavior for `task_type="analyze"` (direct text input) flow
- The fix must not alter behavior for `task_type="chat"` flow
- Supervisor must not be called more than once per image processing request (first call skips, second call with extracted text performs analysis)
- The `Send()` API must be used for dynamic routing (LangGraph requirement)

## Traceability

| Requirement | Plan Reference | Acceptance Reference |
|---|---|---|
| REQ-IMG-001 | TASK-1 | AC-001 |
| REQ-IMG-002 | TASK-1 | AC-001 |
| REQ-IMG-003 | TASK-1 | AC-002 |
| REQ-IMG-004 | TASK-2 | AC-003 |
| REQ-IMG-005 | TASK-1 | AC-004 |
