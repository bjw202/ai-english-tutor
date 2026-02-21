# LangGraph Reference - Advanced Patterns

Extended documentation for moai-library-langgraph.
Load on demand when SKILL.md patterns are insufficient.

---

## Multi-Provider LLM Setup

```python
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel

def get_llm(provider: str = "openai") -> BaseChatModel:
    if provider == "anthropic":
        return ChatAnthropic(model="claude-3-5-sonnet-20241022")
    return ChatOpenAI(model="gpt-4o-mini")

# Bind tools to specific LLM
llm_with_tools = get_llm("openai").bind_tools(tools)
```

---

## Complete English Tutor Multi-Agent Example

```python
from typing import Annotated, TypedDict
from operator import add
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

class TutorState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    student_input: str
    feedback_items: Annotated[list[dict], add]

class AgentState(TypedDict):
    student_input: str
    feedback: dict

def grammar_agent(state: AgentState) -> dict:
    response = llm.invoke([
        HumanMessage(content=(
            f"As a grammar teacher, analyze this text and return JSON with keys "
            f"'errors' (list) and 'suggestions' (list):\n{state['student_input']}"
        ))
    ])
    return {"feedback_items": [{"type": "grammar", "content": response.content}]}

def vocabulary_agent(state: AgentState) -> dict:
    response = llm.invoke([
        HumanMessage(content=(
            f"As a vocabulary coach, suggest 3 better word choices for:\n"
            f"{state['student_input']}"
        ))
    ])
    return {"feedback_items": [{"type": "vocabulary", "content": response.content}]}

def pronunciation_agent(state: AgentState) -> dict:
    response = llm.invoke([
        HumanMessage(content=(
            f"Identify pronunciation challenges for a non-native speaker in:\n"
            f"{state['student_input']}"
        ))
    ])
    return {"feedback_items": [{"type": "pronunciation", "content": response.content}]}

def supervisor(state: TutorState) -> list[Send]:
    """Dispatch to all specialist agents in parallel."""
    agent_input = {"student_input": state["student_input"]}
    return [
        Send("grammar_agent", agent_input),
        Send("vocabulary_agent", agent_input),
        Send("pronunciation_agent", agent_input),
    ]

def synthesizer(state: TutorState) -> dict:
    """Combine all feedback into a coherent response."""
    feedback_text = "\n".join(
        f"[{item['type'].upper()}]: {item['content']}"
        for item in state["feedback_items"]
    )
    response = llm.invoke([
        HumanMessage(content=(
            f"Synthesize this teaching feedback into a friendly, encouraging message:\n"
            f"{feedback_text}"
        ))
    ])
    return {"messages": [AIMessage(content=response.content)]}

builder = StateGraph(TutorState)
builder.add_node("supervisor", supervisor)
builder.add_node("grammar_agent", grammar_agent)
builder.add_node("vocabulary_agent", vocabulary_agent)
builder.add_node("pronunciation_agent", pronunciation_agent)
builder.add_node("synthesizer", synthesizer)

builder.add_edge(START, "supervisor")
builder.add_conditional_edges("supervisor", lambda s: supervisor(s))
builder.add_edge("grammar_agent", "synthesizer")
builder.add_edge("vocabulary_agent", "synthesizer")
builder.add_edge("pronunciation_agent", "synthesizer")
builder.add_edge("synthesizer", END)

checkpointer = InMemorySaver()
tutor_graph = builder.compile(checkpointer=checkpointer)
```

---

## Subgraph Composition

```python
# Define child graph
child_builder = StateGraph(ChildState)
child_builder.add_node("step1", step1_fn)
child_builder.add_node("step2", step2_fn)
child_builder.add_edge(START, "step1")
child_builder.add_edge("step1", "step2")
child_builder.add_edge("step2", END)
child_graph = child_builder.compile()

# Add as node in parent graph
parent_builder = StateGraph(ParentState)
parent_builder.add_node("child_workflow", child_graph)
parent_builder.add_edge(START, "child_workflow")
parent_builder.add_edge("child_workflow", END)
parent_graph = parent_builder.compile()
```

---

## Human-in-the-Loop (Interrupt)

```python
from langgraph.types import interrupt

def human_review_node(state: AppState) -> dict:
    """Pause graph and wait for human input."""
    decision = interrupt({
        "question": "Approve this response?",
        "draft": state["messages"][-1].content,
    })
    if decision == "approve":
        return {"approved": True}
    return {"approved": False, "revision_needed": True}

# Resume from interrupt
config = {"configurable": {"thread_id": "session-1"}}
graph.invoke(Command(resume="approve"), config)
```

---

## Advanced Streaming: astream_events v2

```python
async def stream_with_events(user_input: str, thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    async for event in graph.astream_events(
        {"messages": [HumanMessage(content=user_input)]},
        config,
        version="v2"
    ):
        kind = event["event"]
        if kind == "on_chain_start":
            node = event.get("metadata", {}).get("langgraph_node", "")
            print(f"Starting node: {node}")
        elif kind == "on_chain_stream":
            data = event.get("data", {})
            if "chunk" in data:
                print(f"Chunk: {data['chunk']}")
        elif kind == "on_chain_end":
            node = event.get("metadata", {}).get("langgraph_node", "")
            print(f"Completed node: {node}")
        elif kind == "on_chat_model_stream":
            content = event["data"]["chunk"].content
            if content:
                yield content
```

---

## FastAPI SSE with Session Management

```python
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
import json
import uuid

app = FastAPI(title="AI English Tutor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

checkpointer = InMemorySaver()
graph = tutor_graph  # from above

class TutorRequest(BaseModel):
    student_input: str
    thread_id: str | None = None
    stream: bool = True

async def sse_generator(student_input: str, thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    try:
        async for msg, metadata in graph.astream(
            {
                "messages": [HumanMessage(content=student_input)],
                "student_input": student_input,
                "feedback_items": [],
            },
            config,
            stream_mode="messages",
        ):
            if not msg.content or isinstance(msg, HumanMessage):
                continue
            node = metadata.get("langgraph_node", "unknown")
            payload = json.dumps({
                "node": node,
                "content": msg.content,
                "thread_id": thread_id,
            })
            yield f"data: {payload}\n\n"
    except Exception as e:
        error_payload = json.dumps({"error": str(e)})
        yield f"data: {error_payload}\n\n"
    finally:
        yield "data: [DONE]\n\n"

@app.post("/tutor/chat")
async def chat(request: TutorRequest):
    thread_id = request.thread_id or str(uuid.uuid4())

    if not request.stream:
        config = {"configurable": {"thread_id": thread_id}}
        result = graph.invoke(
            {
                "messages": [HumanMessage(content=request.student_input)],
                "student_input": request.student_input,
                "feedback_items": [],
            },
            config,
        )
        return {
            "thread_id": thread_id,
            "response": result["messages"][-1].content,
        }

    return StreamingResponse(
        sse_generator(request.student_input, thread_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

@app.get("/tutor/history/{thread_id}")
async def get_history(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    try:
        state = graph.get_state(config)
        messages = [
            {"role": "user" if isinstance(m, HumanMessage) else "assistant",
             "content": m.content}
            for m in state.values.get("messages", [])
        ]
        return {"thread_id": thread_id, "messages": messages}
    except Exception:
        raise HTTPException(status_code=404, detail="Thread not found")

@app.delete("/tutor/session/{thread_id}")
async def delete_session(thread_id: str):
    checkpointer.delete_thread(thread_id)
    return {"deleted": thread_id}
```

---

## Production Patterns

### PostgreSQL Checkpointer for Production
```python
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

async def create_production_graph():
    DB_URI = "postgresql+asyncpg://user:pass@host:5432/db"
    async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
        await checkpointer.setup()  # Create tables on first run
        graph = builder.compile(checkpointer=checkpointer)
        return graph
```

### Graph Compilation with Interrupt Points
```python
graph = builder.compile(
    checkpointer=checkpointer,
    interrupt_before=["human_review_node"],  # Pause before these nodes
    interrupt_after=["grammar_agent"],        # Pause after these nodes
)
```

### State Schema Validation
```python
from pydantic import BaseModel, field_validator

class ValidatedState(BaseModel):
    student_input: str
    feedback_items: list[dict] = []

    @field_validator("student_input")
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("student_input cannot be empty")
        return v.strip()
```

---

## Key API Reference

| Method | Signature | Purpose |
|--------|-----------|---------|
| `add_node` | `(name, fn)` | Register node function |
| `add_edge` | `(src, dst)` | Fixed transition |
| `add_conditional_edges` | `(src, fn, map?)` | Dynamic routing |
| `compile` | `(checkpointer?, interrupt_before?, interrupt_after?)` | Build executable graph |
| `invoke` | `(input, config?)` | Sync execution |
| `stream` | `(input, config?, stream_mode?)` | Sync streaming |
| `astream` | `(input, config?, stream_mode?)` | Async streaming |
| `astream_events` | `(input, config?, version?)` | Async event streaming |
| `get_state` | `(config)` | Current checkpoint state |
| `get_state_history` | `(config)` | All checkpoints for thread |

| Class | Import | Purpose |
|-------|--------|---------|
| `StateGraph` | `langgraph.graph` | Graph builder |
| `START`, `END` | `langgraph.graph` | Entry/exit nodes |
| `Send` | `langgraph.types` | Parallel dispatch |
| `InMemorySaver` | `langgraph.checkpoint.memory` | Dev checkpointer |
| `add_messages` | `langgraph.graph.message` | Message list reducer |
| `get_stream_writer` | `langgraph.config` | Custom stream emitter |

---

## Common Errors

**`ValueError: Node X not found`**: Node referenced in edge not added via `add_node`.

**`InvalidUpdateError`**: Node returning keys not in state TypedDict. Only return keys defined in state schema.

**`RecursionError: Graph recursion limit`**: Add recursion_limit to config:
```python
graph.invoke(input, {"recursion_limit": 50})
```

**Parallel results not aggregating**: Missing `Annotated[list, add]` reducer on state key receiving parallel writes.

**Thread context not preserved**: Missing `checkpointer` in `compile()` or wrong `thread_id` in config.
