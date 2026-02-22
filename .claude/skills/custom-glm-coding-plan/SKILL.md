---
name: custom-glm-coding-plan
description: >
  Provides guidance for using z.ai GLM API with the GLM Coding Plan subscription.
  Covers API authentication, model selection, chat completions, streaming, function
  calling, vision inputs, audio transcription, image/video generation, web search,
  web reader, tokenizer, agents API, and IDE/coding tool integration (Claude Code,
  Cursor, Cline). Use when working with GLM models, setting up z.ai API access,
  integrating GLM into coding workflows, or configuring GLM Coding Plan for
  development tools.
license: Apache-2.0
compatibility: Designed for Claude Code
allowed-tools: Read Grep Glob WebFetch
user-invocable: true
metadata:
  version: "1.1.0"
  category: "domain"
  status: "active"
  updated: "2026-02-22"
  tags: "glm, z.ai, llm, api, coding-plan, zai, audio, image, video, web-search"
  argument-hint: "[topic: setup|models|chat|streaming|function-calling|vision|audio|image|video|web-search|reader|tokenizer|agents|sdk]"
---

# GLM Coding Plan

Practical guide for using z.ai GLM API with the GLM Coding Plan subscription.

## Quick Reference

### Endpoints

General API base URL: `https://api.z.ai/api/paas/v4`

GLM Coding Plan exclusive endpoint: `https://api.z.ai/api/coding/paas/v4`

Agents API: `https://api.z.ai/api/v1/agents` (note: v1, not v4)

The coding endpoint is only for coding plan subscribers and is required for IDE integrations (Claude Code, Cursor, Cline).

### Authentication

All requests require a Bearer token header:

```
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

Store the API key in an environment variable, never hardcode it:

```bash
export ZAI_API_KEY="your-api-key-here"
```

### Available Models (Coding Plan)

GLM-5: Flagship model targeting Agentic Engineering. Best for complex reasoning, code generation, and multi-step tasks.

GLM-4.7: High-performance model balancing speed and quality. Recommended for most coding tasks.

GLM-4.6V: Multimodal model with 128K context window. Supports text, images, audio, and video inputs.

GLM-4.6: Efficient text model. Good for straightforward code generation and Q&A.

GLM-OCR: Lightweight OCR model (0.9B params) for document/image text extraction, table parsing, and layout analysis. Uses dedicated `/layout_parsing` endpoint.

GLM-ASR-2512: Audio transcription model. Supports WAV/MP3, max 25MB, max 30 seconds.

GLM-Image / CogView-4-250304: Text-to-image generation models.

CogVideoX-3 / Vidu models: Video generation model families.

For coding tasks, prefer glm-5 or glm-4.7. For image understanding, use glm-4.6v. For document text extraction, use glm-ocr. For audio transcription, use glm-asr-2512.

---

## Implementation Guide

### Setup: Install SDKs

Native Python SDK:

```bash
pip install zai-sdk
```

OpenAI-compatible Python SDK (drop-in replacement):

```bash
pip install openai
```

Node.js (OpenAI-compatible):

```bash
npm install openai
```

### Basic Chat Completion

Using the native zai-sdk:

```python
import os
from zai import ZaiClient

client = ZaiClient(api_key=os.environ["ZAI_API_KEY"])

response = client.chat.completions.create(
    model="glm-4.7",
    messages=[
        {"role": "system", "content": "You are a helpful coding assistant."},
        {"role": "user", "content": "Write a Python function to flatten a nested list."}
    ]
)

print(response.choices[0].message.content)
```

Using the OpenAI-compatible SDK:

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["ZAI_API_KEY"],
    base_url="https://api.z.ai/api/paas/v4/"
)

response = client.chat.completions.create(
    model="glm-4.7",
    messages=[{"role": "user", "content": "Explain async/await in Python."}],
    temperature=0.7,
    top_p=0.95,
    max_tokens=2048
)
print(response.choices[0].message.content)
```

Additional chat parameters: `top_p` (0.01-1.0, default 0.95), `do_sample` (bool, default true), `thinking` (enable chain-of-thought), `request_id` (unique request ID), `user_id` (6-128 chars), `stop` (stop word array). See reference.md for full parameter table.

### Streaming Responses

Streaming delivers tokens in real-time, essential for responsive coding assistants:

```python
stream = client.chat.completions.create(
    model="glm-4.7",
    messages=[{"role": "user", "content": "Generate a FastAPI CRUD application."}],
    stream=True
)

for chunk in stream:
    delta = chunk.choices[0].delta
    if delta.content:
        print(delta.content, end="", flush=True)
```

### Multi-Turn Conversation

Maintain conversation history by appending messages to the messages list:

```python
messages = [{"role": "system", "content": "You are a senior software engineer."}]

def chat(user_input: str) -> str:
    messages.append({"role": "user", "content": user_input})
    response = client.chat.completions.create(model="glm-4.7", messages=messages)
    reply = response.choices[0].message.content
    messages.append({"role": "assistant", "content": reply})
    return reply
```

### Function Calling (Tool Use)

GLM models support up to 128 function tools per request:

```python
tools = [{"type": "function", "function": {
    "name": "run_code",
    "description": "Execute Python code in a sandbox",
    "parameters": {"type": "object", "properties": {
        "code": {"type": "string", "description": "The Python code to execute"}
    }, "required": ["code"]}
}}]

response = client.chat.completions.create(
    model="glm-5",
    messages=[{"role": "user", "content": "Calculate the first 10 Fibonacci numbers."}],
    tools=tools,
    tool_choice="auto"
)
```

`finish_reason` values: `stop`, `tool_calls`, `length`, `sensitive`, `network_error`.

See reference.md for the complete function calling loop with result submission.

### Vision (Multimodal Input)

GLM-4.6V accepts images (jpg/png/jpeg, <5MB, ≤6000×6000px), videos (mp4/mkv/mov, <200MB), and files (pdf/txt/word/xlsx/pptx, up to 50 files):

```python
import base64

with open("screenshot.png", "rb") as f:
    image_data = base64.b64encode(f.read()).decode("utf-8")

response = client.chat.completions.create(
    model="glm-4.6v",
    messages=[{"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}},
        {"type": "text", "text": "Review this code screenshot and identify any bugs."}
    ]}]
)
```

### Audio Transcription

Uses `glm-asr-2512` with a dedicated endpoint. Supports WAV/MP3, max 25MB, max 30 seconds:

```python
import requests

# Option 1: File upload
with open("audio.wav", "rb") as f:
    response = requests.post(
        "https://api.z.ai/api/paas/v4/audio/transcriptions",
        headers={"Authorization": f"Bearer {os.environ['ZAI_API_KEY']}"},
        files={"file": f},
        data={"model": "glm-asr-2512"}
    )
print(response.json()["text"])

# Option 2: Base64
import base64
audio_b64 = base64.b64encode(open("audio.mp3", "rb").read()).decode()
response = requests.post(
    "https://api.z.ai/api/paas/v4/audio/transcriptions",
    headers={"Authorization": f"Bearer {os.environ['ZAI_API_KEY']}",
             "Content-Type": "application/json"},
    json={"model": "glm-asr-2512", "file_base64": audio_b64}
)
```

Optional params: `prompt` (context from previous transcript, <8000 chars), `hotwords` (domain vocabulary array, max 100 items), `stream` (boolean). See reference.md for streaming SSE format.

### Image Generation

```python
response = client.images.generate(
    model="glm-image",   # or "cogview-4-250304"
    prompt="A futuristic Python development environment",
    quality="hd",        # "hd" (~20s) or "standard" (5-10s); default "hd" for glm-image
    size="1280x1280"     # glm-image default; see reference.md for all size options
)
print(response.data[0].url)  # URL expires after 30 days
```

### Video Generation

Video generation is async. Submit a job, then poll for results:

```python
# Submit job
response = requests.post(
    "https://api.z.ai/api/paas/v4/videos/generations",
    headers={"Authorization": f"Bearer {os.environ['ZAI_API_KEY']}",
             "Content-Type": "application/json"},
    json={"model": "cogvideox-3", "prompt": "A cat typing on a keyboard"}
)
task = response.json()
task_id = task["id"]

# Poll for result
import time
while True:
    status = requests.get(
        f"https://api.z.ai/api/paas/v4/videos/generations/{task_id}",
        headers={"Authorization": f"Bearer {os.environ['ZAI_API_KEY']}"}
    ).json()
    if status["task_status"] in ("SUCCESS", "FAIL"):
        break
    time.sleep(5)
```

5 model groups: cogvideox-3, viduq1-text, viduq1-image/vidu2-image, viduq1-start-end/vidu2-start-end, vidu2-reference. See reference.md for details.

### Web Search

```python
response = requests.post(
    "https://api.z.ai/api/paas/v4/web_search",
    headers={"Authorization": f"Bearer {os.environ['ZAI_API_KEY']}",
             "Content-Type": "application/json"},
    json={
        "search_query": "Python async best practices 2025",
        "count": 10,
        "search_recency_filter": "oneMonth"  # oneDay|oneWeek|oneMonth|oneYear|noLimit
    }
)
results = response.json()["search_result"]
for r in results:
    print(r["title"], r["link"])
```

### Web Reader

```python
response = requests.post(
    "https://api.z.ai/api/paas/v4/reader",
    headers={"Authorization": f"Bearer {os.environ['ZAI_API_KEY']}",
             "Content-Type": "application/json"},
    json={
        "url": "https://docs.python.org/3/library/asyncio.html",
        "return_format": "markdown",  # "markdown" or "text"
        "retain_images": False
    }
)
content = response.json()["reader_result"]["content"]
```

### Tokenizer

Count tokens before making expensive API calls:

```python
response = requests.post(
    "https://api.z.ai/api/paas/v4/tokenizer",
    headers={"Authorization": f"Bearer {os.environ['ZAI_API_KEY']}",
             "Content-Type": "application/json"},
    json={
        "model": "glm-4.6",  # glm-4.6, glm-4.6v, or glm-4.5
        "messages": [{"role": "user", "content": "Hello, how are you?"}]
    }
)
usage = response.json()["usage"]
print(f"Prompt tokens: {usage['prompt_tokens']}, Total: {usage['total_tokens']}")
```

### Agents API

The Agents API (v1 endpoint) provides pre-built agents for specialized tasks:

```python
# Translation Agent
response = requests.post(
    "https://api.z.ai/api/v1/agents",
    headers={"Authorization": f"Bearer {os.environ['ZAI_API_KEY']}",
             "Content-Type": "application/json"},
    json={
        "agent_id": "general_translation",
        "messages": [{"role": "user", "content": "Translate to Japanese: Hello world"}]
    }
)
```

Available agent IDs: `general_translation` (multi-strategy translation with glossary), `vidu_template_agent` (special effects videos: french_kiss/bodyshake/sexy_me), `slides_glm_agent` (presentation generation). See reference.md for details.

### OCR - Document & Image Text Extraction

GLM-OCR uses a dedicated endpoint. Supports PDF (up to 100 pages, 50MB) and images (JPG/PNG, 10MB):

```python
result = client.layout_parsing.create(
    model="glm-ocr",
    file="https://example.com/document.png"
)
print(result.md_results)
```

See reference.md for full response schema and advanced use cases.

---

## Advanced Patterns

### Claude Code Integration (Coding Plan)

```bash
export ANTHROPIC_API_KEY="your-zai-api-key"
export ANTHROPIC_BASE_URL="https://api.z.ai/api/coding/paas/v4"
```

### Cursor / Cline Integration

In Cursor settings: API Endpoint `https://api.z.ai/api/coding/paas/v4`, API Key, Model: glm-4.7 or glm-5.

For Cline (VS Code): API Provider: OpenAI Compatible, Base URL: `https://api.z.ai/api/coding/paas/v4`.

### JWT Authentication (High-Security)

```python
import time, jwt

api_key = os.environ["ZAI_API_KEY"]
api_id, api_secret = api_key.split(".")
token = jwt.encode(
    {"api_key": api_id, "exp": int(time.time()) + 3600, "timestamp": int(time.time())},
    api_secret, algorithm="HS256"
)
# Use token in: Authorization: Bearer {token}
```

### Error Handling with Retry

```python
import time
from openai import RateLimitError, APIError

def robust_completion(client, **kwargs):
    for attempt in range(3):
        try:
            return client.chat.completions.create(**kwargs)
        except RateLimitError:
            time.sleep(2 ** attempt)
        except APIError as e:
            if e.status_code >= 500:
                time.sleep(1)
            else:
                raise
    raise RuntimeError("Max retries exceeded")
```

### Error Codes Summary

HTTP: 200 (success), 400 (param error), 401 (auth failure), 404 (unavailable), 429 (rate limit/balance), 434 (beta restricted), 435 (file >100MB), 500 (server error).

Business codes: 1000-1004 (auth), 1110-1121 (account), 1210-1234 (API calls), 1300-1310 (policy/rate limits). See reference.md for the full error code table.

---

## Works Well With

- reference.md: Complete parameter tables, function calling loop, LangChain, Java SDK, OCR advanced usage, audio/video/agents details, full error codes
- Z.AI Documentation: https://docs.z.ai
- Z.AI Platform: https://z.ai (API key management, subscription)
- OpenAI Python SDK docs for compatible usage patterns
