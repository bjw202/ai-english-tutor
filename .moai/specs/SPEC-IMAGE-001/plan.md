---
id: SPEC-IMAGE-001
type: plan
version: 1.0.0
status: Draft
created: 2026-02-23
updated: 2026-02-23
author: jw
tags: [image-processing, ocr, supervisor, langgraph, pipeline-fix]
---

# SPEC-IMAGE-001: Implementation Plan

## Overview

Fix the image processing pipeline so that OCR-extracted text is routed through `supervisor_node` for pre-analysis before reaching analysis agents (`reading`, `grammar`, `vocabulary`).

## Task Decomposition

### TASK-1: Modify `route_after_image` in `graph.py` (Priority High)

**File**: `backend/src/tutor/graph.py`
**Function**: `route_after_image`
**Change Type**: Bug fix - routing logic

**Current Behavior**:
```python
def route_after_image(state: TutorState) -> list[Send]:
    extracted_text = state.get("extracted_text", "")
    if extracted_text:
        return [
            Send("reading", state),
            Send("grammar", state),
            Send("vocabulary", state),
        ]
    return [Send("aggregator", state)]
```

**Required Behavior**:
- When `extracted_text` is non-empty, route to `supervisor` with updated state (`input_text=extracted_text`, `task_type="analyze"`)
- When `extracted_text` is empty, route to `aggregator` (unchanged)

**Key Design Decision**:
Use `Send("supervisor", new_state)` where `new_state` is a copy of the current state with `input_text` and `task_type` overwritten. This reuses the existing `supervisor -> route_by_task -> parallel agents` path, avoiding code duplication.

**Impact Analysis**:
- `supervisor_node` already handles `task_type="analyze"` with non-empty `input_text` (no changes needed)
- `route_by_task` already dispatches `task_type="analyze"` to parallel agents (no changes needed)
- The graph already has `supervisor -> conditional_edges(route_by_task)` wired up (no changes needed)

### TASK-2: Verify `TutorState` Fields in `state.py` (Priority Medium)

**File**: `backend/src/tutor/state.py`
**Change Type**: Verification (no code change expected)

**Verification**:
Confirm that `image_data` and `mime_type` fields exist in `TutorState` as `NotRequired[str | None]`. These fields are already present in the current codebase (lines 49-51). This task formally documents and verifies the requirement.

### TASK-3: Update `route_after_image` Docstring (Priority Low)

**File**: `backend/src/tutor/graph.py`
**Function**: `route_after_image`
**Change Type**: Documentation update

Update the docstring to reflect the new routing behavior: text goes through supervisor for pre-analysis instead of directly to analysis agents.

## Milestones

### Primary Goal: Fix Routing Logic

- Complete TASK-1: Modify `route_after_image` to route through supervisor
- Verify that image pipeline produces `supervisor_analysis` for downstream agents

### Secondary Goal: Verification and Documentation

- Complete TASK-2: Verify `TutorState` field integrity
- Complete TASK-3: Update docstrings to match new behavior

## Technical Approach

### Architecture Decision: Reuse Existing Supervisor Path

Instead of creating a new dedicated node or edge for post-OCR analysis, reuse the existing `supervisor -> route_by_task -> parallel agents` path by sending the OCR-extracted text back to `supervisor` with `task_type="analyze"`.

**Rationale**:
- The supervisor already handles `task_type="analyze"` with LLM-based pre-analysis
- The `route_by_task` function already dispatches to parallel agents for `task_type="analyze"`
- No new nodes, edges, or conditional routing logic needed
- Maintains single responsibility: supervisor always does pre-analysis, `route_by_task` always does dispatch

**Trade-offs**:
- Supervisor is invoked twice for image tasks (first with empty text, skips; second with extracted text, analyzes)
- The first invocation is a no-op (returns `{}` immediately), so minimal overhead
- This is acceptable because the alternative (complex conditional logic to skip first supervisor call) would add unnecessary complexity

### File Change Summary

| File | Change | Lines Affected |
|---|---|---|
| `backend/src/tutor/graph.py` | Modify `route_after_image` function | ~10 lines |
| `backend/src/tutor/state.py` | No change (verification only) | 0 lines |
| `backend/src/tutor/agents/supervisor.py` | No change needed | 0 lines |
| `backend/src/tutor/agents/image_processor.py` | No change needed | 0 lines |

### Dependency Analysis

```
route_after_image (TASK-1)
  |-- depends on: TutorState having image_data/mime_type (TASK-2, already satisfied)
  |-- depends on: supervisor_node handling task_type="analyze" (already working)
  |-- depends on: route_by_task dispatching "analyze" to parallel agents (already working)
  |-- no dependency on: image_processor_node (upstream, no change)
```

## Risks and Mitigation

### Risk 1: Infinite Loop via Supervisor Re-entry

**Severity**: High
**Probability**: Low
**Description**: If `route_after_image` sends to `supervisor`, and supervisor routes back to `image_processor`, an infinite loop could occur.
**Mitigation**: The re-routed state has `task_type="analyze"`, so `route_by_task` will dispatch to analysis agents, not back to `image_processor`. The loop cannot occur because `task_type` is explicitly changed from `"image_process"` to `"analyze"`.

### Risk 2: State Mutation Side Effects

**Severity**: Medium
**Probability**: Low
**Description**: Creating `new_state` with `{**state, "input_text": extracted_text, "task_type": "analyze"}` could have unintended side effects if other state fields interfere.
**Mitigation**: The spread operator creates a shallow copy. `input_text` and `task_type` are the only fields being overwritten. Other fields (`image_data`, `mime_type`, `extracted_text`) remain in state but are not used by supervisor or analysis agents (they only read `input_text`, `level`, `task_type`).

### Risk 3: Supervisor LLM Failure for OCR Text

**Severity**: Low
**Probability**: Low
**Description**: The supervisor's LLM call might fail for OCR-extracted text (e.g., poorly formatted markdown from GLM-OCR).
**Mitigation**: `supervisor_node` already has fallback logic (`_fallback_analysis`) that performs basic period-based sentence splitting when LLM fails. This fallback produces a valid `SupervisorAnalysis` object, so downstream agents will still receive `supervisor_analysis` context.

## Expert Consultation Recommendation

This SPEC involves backend API logic, LangGraph workflow architecture, and agent coordination. Consider consulting with **expert-backend** for:
- LangGraph `Send()` API best practices for re-routing
- State management patterns in conditional edge functions
- Verification that the re-entry pattern is safe in LangGraph's execution model
