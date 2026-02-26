# Lesson Learned: Production Vocabulary Analysis Failure

Date: 2026-02-26
Bug: Vocabulary analysis works locally but fails on Railway + Vercel production

## Timeline

| Step | Action | Result |
|------|--------|--------|
| 1st analysis | Code-only static analysis, diagnosed `hasattr` bug | **Misdiagnosis** |
| 1st fix | Changed hasattr to handle both Pydantic and dict | Deployed, **same issue persists** |
| User hint | "Use Railway CLI to find the cause" | **Turning point** |
| 2nd analysis | `railway logs --filter` revealed actual error | **Root cause found** - uvloop crash |
| 2nd fix | Added `--loop asyncio` flag to uvicorn | **Resolved** |

## 1. Why AI Failed in Initial Analysis

### Static Analysis Limitations

AI read source code only and reasoned "which part could go wrong?" The `hasattr` bug was **logically possible** but was NOT the **actual production error**.

**Core mistake**: Approached "works locally, fails in production" as a **code difference** problem. But the code was identical - the **runtime environment** was different.

### Static vs Dynamic Analysis

| Approach | Can detect | Cannot detect |
|----------|-----------|---------------|
| Code reading (static) | Logic bugs, type errors, design flaws | Runtime env differences, library internal bugs |
| Log inspection (dynamic) | Actual errors, stack traces, timing | Code structure understanding |

AI performed static analysis only, skipping dynamic analysis (production logs).

### Why AI Didn't Think of Railway CLI

- Did not check if Railway CLI was installed
- Did not follow the basic principle: "locally unreproducible problem -> must check production logs"
- Code analysis gave a plausible answer, so AI moved to fix without verification

## 2. What Context Was Missing

### Key Clue the User Provided

> "With the same sentence, vocabulary analysis works on local dev server"

This contained the decisive clue: **"same code, different environment"**. But AI interpreted it as "code has an environment-dependent bug" rather than "the runtime environment itself is different."

### The Fundamental Issue

Users should not be expected to provide perfect information. **AI should recognize "this cannot be verified by code alone" and suggest checking production logs first.**

## 3. Collaboration Protocol for Future

### "Local OK, Production NG" Checklist

```
Step 1: Check production logs FIRST
  - railway logs --filter "@level:error"
  - railway logs --filter "keyword" (problem domain)
  -> Get actual error messages and stack traces

Step 2: Compare environment differences
  - Python version (local vs production)
  - Event loop (asyncio vs uvloop)
  - Environment variables (CORS, API keys, model config)
  - OS (macOS vs Linux)

Step 3: Code analysis (if needed)
  - Analyze based on ACTUAL errors from steps 1-2
  - Evidence-based debugging, not guesswork
```

### Effective Bug Report Template for Users

```
Symptom: [What doesn't work]
Scope: [What works, what doesn't]
Environment: [Local / Production / Both]
Reproducibility: [Always / Intermittent]
Recent changes: [What was last changed]
Logs: [Error messages if available]
```

### Principles AI Must Follow

1. **"Local OK, Production NG" -> production logs before code analysis**
2. **Don't settle on one plausible hypothesis** - fixing without verification wastes time
3. **Explore available tools first** - check `which railway`, `which vercel` for CLI availability
4. **Verify after fix** - don't say "please check after deploy", check logs directly

## 4. Technical Lessons

| Lesson | Detail |
|--------|--------|
| uvloop caution | LangGraph 0.3.34 + uvloop crashes in `FuturesDict` callback |
| Event loop difference | macOS uvicorn uses default asyncio; Linux auto-detects uvloop |
| `--loop asyncio` | Forces standard event loop in uvicorn when uvloop causes issues |
| `hasattr` defense | LangGraph astream_events on_chain_end output needs Pydantic/dict dual handling (still a valid improvement) |

## 5. Actual Root Cause

```
File "uvloop/cbhandles.pyx", line 63, in uvloop.loop.Handle._run
File "langgraph/pregel/runner.py", line 98, in on_done
    self.callback()(task, _exception(fut))
TypeError: 'NoneType' object is not callable
```

- Vocabulary node completes successfully (parses 10 words)
- LangGraph's `FuturesDict.on_done` callback crashes under uvloop
- Vocabulary result is LOST - never becomes an SSE event
- Frontend never receives `vocabulary_chunk`, shows "No vocabulary analysis yet"

## 6. Summary

**Root failure**: Tried to solve a runtime environment (dynamic) problem with code analysis (static).

**Turning point**: User directed to use Railway CLI, enabling actual production log inspection.

**Core principle**: For production-only bugs, production logs are truth. Code is just hypothesis.
