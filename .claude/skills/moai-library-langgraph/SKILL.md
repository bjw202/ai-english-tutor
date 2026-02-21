---
name: moai-library-langgraph
description: >
  LangGraph 0.3+ multi-agent orchestration patterns including StateGraph API,
  Supervisor-Worker parallel dispatch with Send(), state management with
  TypedDict reducers, streaming with astream_events, and FastAPI SSE integration.
  Use when building multi-agent AI systems, implementing supervisor patterns,
  or integrating LangGraph with web frameworks.
license: Apache-2.0
compatibility: Designed for Claude Code
user-invocable: false
metadata:
  version: "1.0.0"
  category: "library"
  status: "active"
  updated: "2026-02-20"
  tags: "langgraph, multi-agent, supervisor, streaming, fastapi, langchain"
  context7-libraries: "langchain-ai/langgraph"
  related-skills: "moai-lang-python, moai-domain-backend"

# MoAI Extension: Progressive Disclosure
progressive_disclosure:
  enabled: true
  level1_tokens: 100
  level2_tokens: 5000

# MoAI Extension: Triggers
triggers:
  keywords: ["langgraph", "multi-agent", "supervisor", "StateGraph", "Send", "astream_events", "checkpointer", "MemorySaver"]
  agents: ["expert-backend", "manager-strategy", "manager-ddd", "manager-tdd"]
  phases: ["plan", "run"]
---

# LangGraph 0.3+ Multi-Agent Patterns

## Quick Reference

### Installation
```bash
pip install langgraph langchain-openai langchain-anthropic
```

### Core Imports
```python
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.config import get_stream_writer
from typing import Annotated, TypedDict
from operator import add
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph.message import add_messages
```

### StateGraph Lifecycle
```
StateGraph(State) -> add_node -> add_edge/add_conditional_edges -> compile() -> invoke/stream
```

---

## 1. StateGraph API

```python
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    topic: str

def node_fn(state: State) -> dict:
    # Return partial state update (only changed keys)
    return {"topic": "processed"}

builder = StateGraph(State)
builder.add_node("my_node", node_fn)
builder.add_edge(START, "my_node")
builder.add_edge("my_node", END)

graph = builder.compile()
result = graph.invoke({"messages": [], "topic": "hello"})
```

### Conditional Routing
```python
def route(state: State) -> str:
    if state["topic"] == "grammar":
        return "grammar_node"
    return "conversation_node"

builder.add_conditional_edges("router", route)
# With explicit path map:
builder.add_conditional_edges(
    "router", route,
    {"grammar": "grammar_node", "conversation": "conversation_node"}
)
```

---

## 2. Multi-Agent Supervisor Pattern

### State with Parallel Reducer
```python
from operator import add

class TutorState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    student_input: str
    agent_results: Annotated[list[str], add]  # parallel merge reducer

class WorkerState(TypedDict):
    student_input: str
    result: str
```

### Supervisor + Send() Dispatch
```python
from langgraph.types import Send
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini")

def supervisor(state: TutorState) -> list[Send]:
    """Route to multiple specialist agents in parallel."""
    return [
        Send("grammar_agent", {"student_input": state["student_input"]}),
        Send("vocabulary_agent", {"student_input": state["student_input"]}),
    ]

def grammar_agent(state: WorkerState) -> dict:
    response = llm.invoke([
        HumanMessage(content=f"Check grammar: {state['student_input']}")
    ])
    return {"agent_results": [f"Grammar: {response.content}"]}

def vocabulary_agent(state: WorkerState) -> dict:
    response = llm.invoke([
        HumanMessage(content=f"Check vocabulary: {state['student_input']}")
    ])
    return {"agent_results": [f"Vocab: {response.content}"]}

def aggregator(state: TutorState) -> dict:
    combined = "\n".join(state["agent_results"])
    return {"messages": [AIMessage(content=combined)]}

builder = StateGraph(TutorState)
builder.add_node("supervisor", supervisor)
builder.add_node("grammar_agent", grammar_agent)
builder.add_node("vocabulary_agent", vocabulary_agent)
builder.add_node("aggregator", aggregator)

builder.add_edge(START, "supervisor")
builder.add_conditional_edges("supervisor", lambda s: supervisor(s))
builder.add_edge("grammar_agent", "aggregator")
builder.add_edge("vocabulary_agent", "aggregator")
builder.add_edge("aggregator", END)

graph = builder.compile()
```

### Tool-Calling Supervisor (Recommended)
```python
from langchain_core.tools import tool

@tool
def route_to_grammar(input: str) -> str:
    """Route to grammar specialist agent."""
    return input

@tool
def route_to_vocabulary(input: str) -> str:
    """Route to vocabulary specialist agent."""
    return input

supervisor_llm = llm.bind_tools([route_to_grammar, route_to_vocabulary])

def supervisor_node(state: TutorState) -> dict:
    response = supervisor_llm.invoke(state["messages"])
    return {"messages": [response]}

def route_after_supervisor(state: TutorState) -> str:
    last_msg = state["messages"][-1]
    if not last_msg.tool_calls:
        return END
    return last_msg.tool_calls[0]["name"]
```

---

## 3. State Management

### TypedDict + Annotated Reducers
```python
from typing import Annotated
from operator import add
from langgraph.graph.message import add_messages

class AppState(TypedDict):
    # add_messages: merges message lists, deduplicates by id
    messages: Annotated[list[BaseMessage], add_messages]
    # add: appends lists (for parallel worker results)
    results: Annotated[list[str], add]
    # No annotation: last-write-wins
    current_step: str

# Custom reducer for parallel safety
def merge_dicts(a: dict, b: dict) -> dict:
    return {**a, **b}

class ParallelState(TypedDict):
    feedback: Annotated[dict, merge_dicts]
```

### Subgraph State Isolation
```python
# Parent graph keys flow down; child adds its own keys
class ParentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    student_id: str

class ChildState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    student_id: str        # inherited from parent
    internal_score: float  # child-only, not returned to parent

def child_node(state: ChildState) -> dict:
    # Only return keys that exist in ParentState
    return {"messages": [AIMessage(content="feedback")]}
```

---

## 4. Streaming

### stream_mode Options
```python
# "updates": only changed state after each node
for chunk in graph.stream(inputs, stream_mode="updates"):
    node_name, data = list(chunk.items())[0]
    print(f"[{node_name}] {data}")

# "values": full state after each node
for chunk in graph.stream(inputs, stream_mode="values"):
    print(chunk["messages"][-1].content)

# "messages": LLM tokens + metadata (best for real-time UI)
for msg_chunk, metadata in graph.stream(inputs, stream_mode="messages"):
    if msg_chunk.content and metadata["langgraph_node"] == "grammar_agent":
        print(msg_chunk.content, end="", flush=True)

# Multiple modes simultaneously
for mode, chunk in graph.stream(inputs, stream_mode=["updates", "messages"]):
    print(f"[{mode}] {chunk}")
```

### Custom Streaming from Node
```python
from langgraph.config import get_stream_writer

def streaming_node(state: AppState) -> dict:
    writer = get_stream_writer()
    writer({"status": "analyzing", "progress": 0})
    # ... do work ...
    writer({"status": "complete", "progress": 100})
    return {"current_step": "done"}

for chunk in graph.stream(inputs, stream_mode="custom"):
    print(chunk)  # {"status": "analyzing", "progress": 0}
```

### Async Streaming (astream)
```python
async def stream_graph(student_input: str):
    async for msg, metadata in graph.astream(
        {"messages": [HumanMessage(content=student_input)]},
        stream_mode="messages"
    ):
        if msg.content and metadata["langgraph_node"] == "grammar_agent":
            yield msg.content
```

---

## 5. Checkpointer / Session Memory

### Development Setup (InMemorySaver)
```python
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "student-session-123"}}

# Turn 1
graph.invoke(
    {"messages": [HumanMessage(content="My name is Alice")]},
    config
)

# Turn 2 - context preserved automatically
result = graph.invoke(
    {"messages": [HumanMessage(content="What's my name?")]},
    config
)
# Model knows the name is Alice

# Inspect state
state = graph.get_state(config)
history = list(graph.get_state_history(config))
```

### Production Setup (PostgreSQL)
```python
from langgraph.checkpoint.postgres import PostgresSaver

with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    graph = builder.compile(checkpointer=checkpointer)
```

---

## 6. FastAPI SSE Integration

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

async def sse_generator(student_input: str, thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    async for msg, metadata in graph.astream(
        {"messages": [HumanMessage(content=student_input)]},
        config,
        stream_mode="messages"
    ):
        if msg.content and not isinstance(msg, HumanMessage):
            node = metadata.get("langgraph_node", "unknown")
            data = json.dumps({"node": node, "content": msg.content})
            yield f"data: {data}\n\n"
    yield "data: [DONE]\n\n"

@app.post("/tutor/stream")
async def stream_tutor(request: dict):
    return StreamingResponse(
        sse_generator(request["input"], request["thread_id"]),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
```

See reference.md for advanced patterns: multi-provider LLM setup, subgraph composition, interrupt/human-in-the-loop, and production deployment.

---

## Works Well With

- `moai-lang-python`: Python async patterns and type hints
- `moai-domain-backend`: FastAPI patterns and async best practices
- Context7 MCP: `/langchain-ai/langgraph` for latest API docs
