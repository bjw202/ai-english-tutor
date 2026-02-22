# GLM Coding Plan - Extended Reference

## Complete Function Calling Loop

Full example with result submission back to the model:

```python
import json
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["ZAI_API_KEY"],
    base_url="https://api.z.ai/api/paas/v4/"
)

def get_weather(location: str) -> str:
    return f"Weather in {location}: 22C, partly cloudy"

tools = [{"type": "function", "function": {
    "name": "get_weather",
    "description": "Get current weather for a location",
    "parameters": {"type": "object", "properties": {
        "location": {"type": "string", "description": "City name"}
    }, "required": ["location"]}
}}]

messages = [{"role": "user", "content": "What's the weather in Tokyo?"}]

response = client.chat.completions.create(
    model="glm-5", messages=messages, tools=tools, tool_choice="auto"
)

assistant_message = response.choices[0].message
messages.append(assistant_message)

if assistant_message.tool_calls:
    for tool_call in assistant_message.tool_calls:
        func_name = tool_call.function.name
        func_args = json.loads(tool_call.function.arguments)
        if func_name == "get_weather":
            result = get_weather(**func_args)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result
        })

    final_response = client.chat.completions.create(
        model="glm-5", messages=messages
    )
    print(final_response.choices[0].message.content)
```

---

## Chat Completions - Full Parameter Reference

**Endpoint:** `POST https://api.z.ai/api/paas/v4/chat/completions`

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| model | string | Yes | - | Model identifier |
| messages | array | Yes | - | Conversation messages |
| temperature | float | No | 1.0 | Randomness 0.0-2.0 |
| top_p | float | No | 0.95 | Nucleus sampling 0.01-1.0 (alternative to temperature) |
| do_sample | boolean | No | true | Enable sampling strategy |
| max_tokens | integer | No | - | Maximum response tokens |
| stream | boolean | No | false | Enable streaming |
| tools | array | No | - | Function tools (max 128) |
| tool_choice | string/object | No | "auto" | Tool selection: "auto", "none", specific tool |
| response_format | object | No | - | `{"type": "json_object"}` for JSON mode |
| thinking | object | No | - | Enable chain-of-thought reasoning |
| stop | array | No | - | Stop word array |
| request_id | string | No | - | Unique request identifier for tracing |
| user_id | string | No | - | End-user ID for abuse monitoring (6-128 chars) |

**Message content types:**
- `text`: Plain text string or `{"type": "text", "text": "..."}`
- Images: `{"type": "image_url", "image_url": {"url": "..."}}` — jpg/png/jpeg, <5MB, ≤6000×6000px
- Videos: `{"type": "video_url", "video_url": {"url": "..."}}` — mp4/mkv/mov, <200MB
- Files: `{"type": "file", "file": {"url": "..."}}` — pdf/txt/word/xlsx/pptx, up to 50 files

**Full response format:**
```json
{
  "id": "task-id",
  "request_id": "unique-request-id",
  "created": 1234567890,
  "model": "glm-5",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "response text",
      "tool_calls": []
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 100,
    "completion_tokens": 50,
    "total_tokens": 150
  }
}
```

**finish_reason values:** `stop` (natural end), `tool_calls` (model called a tool), `length` (max_tokens reached), `sensitive` (content filtered), `network_error` (network issue)

---

## Audio Transcription - Full Reference

**Endpoint:** `POST https://api.z.ai/api/paas/v4/audio/transcriptions`

**Model:** `glm-asr-2512`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file | binary | No* | Audio file (.wav or .mp3), max 25MB, ≤30 seconds |
| file_base64 | string | No* | Base64-encoded audio (alternative to file) |
| model | string | Yes | Must be "glm-asr-2512" |
| prompt | string | No | Previous transcription as context (<8000 chars) |
| hotwords | array | No | Domain vocabulary list (max 100 items) |
| stream | boolean | No | Enable streaming (default: false) |
| request_id | string | No | Unique request identifier |
| user_id | string | No | End-user identifier (6-128 chars) |

*Either `file` or `file_base64` is required.

**Sync response:**
```json
{
  "id": "asr_task_123",
  "created": 1234567890,
  "request_id": "unique-id",
  "model": "glm-asr-2512",
  "text": "Transcribed text here"
}
```

**Streaming (SSE) format:**
- Events: `transcript.text.delta` (partial text), `transcript.text.done` (complete text)
- Termination: `data: [DONE]`

```python
# Streaming transcription example
import requests, json

response = requests.post(
    "https://api.z.ai/api/paas/v4/audio/transcriptions",
    headers={"Authorization": f"Bearer {os.environ['ZAI_API_KEY']}"},
    files={"file": open("audio.wav", "rb")},
    data={"model": "glm-asr-2512", "stream": "true"},
    stream=True
)

for line in response.iter_lines():
    if line.startswith(b"data: "):
        data = line[6:]
        if data == b"[DONE]":
            break
        event = json.loads(data)
        print(event.get("text", ""), end="", flush=True)
```

---

## Image Generation - Full Reference

**Endpoint:** `POST https://api.z.ai/api/paas/v4/images/generations`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| model | string | Yes | "glm-image" or "cogview-4-250304" |
| prompt | string | Yes | Image description |
| quality | string | No | "hd" (~20s, detailed) or "standard" (5-10s, fast) |
| size | string | No | Image dimensions (see below) |
| user_id | string | No | End-user identifier (6-128 chars) |

**Size options by model:**

glm-image: 1280x1280 (default), 1568x1056, 1056x1568, 1472x1088, 1088x1472, 1728x960, 960x1728

cogview-4-250304 and other models: 1024x1024 (default), 768x1344, 864x1152, 1152x864, 1344x768, 1024x1792, 1792x1024

Quality defaults: "hd" for glm-image.

**Response:**
```json
{
  "created": 1234567890,
  "data": [{"url": "https://...generated-image-url..."}],
  "content_filter": [{"role": "user", "level": 0}]
}
```

Note: URLs expire after 30 days. Download and store locally for long-term use.

---

## Video Generation - Full Reference

**Endpoint:** `POST https://api.z.ai/api/paas/v4/videos/generations`

### Model Groups

| Model | Type | Resolution | Duration | FPS |
|-------|------|-----------|----------|-----|
| cogvideox-3 | text-to-video or image-to-video | Up to 4K | 5-10s | 30 or 60 |
| viduq1-text | text-to-video | 1920x1080 | 5s | - |
| viduq1-image | image as first frame | - | 5s | - |
| vidu2-image | image as first frame (v2) | - | 5s | - |
| viduq1-start-end | first + last frame interpolation | - | 5s | - |
| vidu2-start-end | first + last frame interpolation (v2) | - | 5s | - |
| vidu2-reference | 1-3 reference images for style | - | 5s | - |

**Common optional parameters:**
- `with_audio` (boolean): Include audio in generated video
- `movement_amplitude` (string): "auto", "small", "medium", "large"

**Submit request:**
```python
response = requests.post(
    "https://api.z.ai/api/paas/v4/videos/generations",
    headers={"Authorization": f"Bearer {os.environ['ZAI_API_KEY']}",
             "Content-Type": "application/json"},
    json={
        "model": "cogvideox-3",
        "prompt": "A panda eating bamboo in a forest",
        "with_audio": True,
        "movement_amplitude": "medium"
    }
)
task = response.json()
# {"model": "cogvideox-3", "id": "task_xxx", "request_id": "...", "task_status": "PROCESSING"}
```

**Poll for result:**
```python
import time

task_id = task["id"]
while True:
    r = requests.get(
        f"https://api.z.ai/api/paas/v4/videos/generations/{task_id}",
        headers={"Authorization": f"Bearer {os.environ['ZAI_API_KEY']}"}
    ).json()
    status = r["task_status"]
    if status == "SUCCESS":
        print("Video URL:", r["video_result"][0]["url"])
        break
    elif status == "FAIL":
        print("Failed:", r)
        break
    time.sleep(5)
```

---

## Web Search - Full Reference

**Endpoint:** `POST https://api.z.ai/api/paas/v4/web_search`

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| search_query | string | Yes | - | Search query string |
| search_engine | string | No | "search-prime" | Search engine identifier |
| count | integer | No | 10 | Number of results (1-50) |
| search_domain_filter | string | No | - | Restrict results to domain |
| search_recency_filter | enum | No | noLimit | oneDay, oneWeek, oneMonth, oneYear, noLimit |
| request_id | string | No | - | Unique request identifier |
| user_id | string | No | - | End-user identifier (6-128 chars) |

**Response:**
```json
{
  "id": "search_123",
  "created": 1234567890,
  "search_result": [
    {
      "title": "Page Title",
      "content": "Snippet text...",
      "link": "https://example.com/page",
      "media": "https://example.com/image.jpg",
      "icon": "https://example.com/favicon.ico",
      "refer": "refer-id",
      "publish_date": "2025-01-15"
    }
  ]
}
```

---

## Web Reader - Full Reference

**Endpoint:** `POST https://api.z.ai/api/paas/v4/reader`

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| url | string | Yes | - | URL to fetch and parse |
| timeout | integer | No | 20 | Request timeout in seconds |
| no_cache | boolean | No | false | Bypass cache |
| return_format | string | No | "markdown" | "markdown" or "text" |
| retain_images | boolean | No | true | Keep image references |
| no_gfm | boolean | No | false | Disable GitHub Flavored Markdown |
| keep_img_data_url | boolean | No | false | Keep image data URLs |
| with_images_summary | boolean | No | false | Include image descriptions |
| with_links_summary | boolean | No | false | Include link summaries |

**Response:**
```json
{
  "id": "reader_123",
  "created": 1234567890,
  "request_id": "unique-id",
  "model": "reader",
  "reader_result": {
    "content": "# Page Title\n\nParsed content in markdown...",
    "title": "Page Title",
    "description": "Meta description",
    "url": "https://example.com/page",
    "metadata": {"author": "...", "published": "..."},
    "external": {}
  }
}
```

---

## Tokenizer - Full Reference

**Endpoint:** `POST https://api.z.ai/api/paas/v4/tokenizer`

Supported models: `glm-4.6`, `glm-4.6v`, `glm-4.5`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| model | string | Yes | Model to tokenize for |
| messages | array | Yes | Standard message objects |
| tools | array | No | Function tools (max 128 functions) |
| request_id | string | No | Unique request identifier |
| user_id | string | No | End-user identifier (6-128 chars) |

**Response:**
```json
{
  "id": "tokenizer_123",
  "created": 1234567890,
  "request_id": "unique-id",
  "usage": {
    "prompt_tokens": 150,
    "image_tokens": 0,
    "video_tokens": 0,
    "total_tokens": 150
  }
}
```

---

## Agents API - Full Reference

**Endpoint:** `POST https://api.z.ai/api/v1/agents`

Note: This uses `/api/v1/agents`, NOT `/api/paas/v4/`.

### Translation Agent

```python
response = requests.post(
    "https://api.z.ai/api/v1/agents",
    headers={"Authorization": f"Bearer {os.environ['ZAI_API_KEY']}",
             "Content-Type": "application/json"},
    json={
        "agent_id": "general_translation",
        "messages": [{"role": "user", "content": "Translate to French: Hello world"}],
        "meta_data": {
            "glossary": [{"source": "Hello", "target": "Bonjour"}]
        }
    }
)
```

Features: Multi-strategy translation (direct, back-translation, reflection), glossary support.

### Special Effects Videos Agent

```python
response = requests.post(
    "https://api.z.ai/api/v1/agents",
    headers={"Authorization": f"Bearer {os.environ['ZAI_API_KEY']}",
             "Content-Type": "application/json"},
    json={
        "agent_id": "vidu_template_agent",
        "messages": [{"role": "user", "content": "Apply french_kiss effect"}],
        "meta_data": {
            "template": "french_kiss",  # or "bodyshake", "sexy_me"
            "image_url": "https://example.com/face.jpg"
        }
    }
)
```

Available templates: `french_kiss`, `bodyshake`, `sexy_me`.

### GLM Slide Agent

```python
response = requests.post(
    "https://api.z.ai/api/v1/agents",
    headers={"Authorization": f"Bearer {os.environ['ZAI_API_KEY']}",
             "Content-Type": "application/json"},
    json={
        "agent_id": "slides_glm_agent",
        "messages": [{"role": "user", "content": "Create a 10-slide presentation about AI trends in 2025"}]
    }
)
```

Features: Multi-phase thinking for slides, structured output with speaker notes.

### Agent Conversation History

For `slides_glm_agent`, continue a conversation using:

**Endpoint:** `POST https://api.z.ai/api/v1/agents/conversation`

```python
response = requests.post(
    "https://api.z.ai/api/v1/agents/conversation",
    headers={"Authorization": f"Bearer {os.environ['ZAI_API_KEY']}",
             "Content-Type": "application/json"},
    json={
        "agent_id": "slides_glm_agent",
        "conversation_id": "prev_conversation_id",
        "messages": [{"role": "user", "content": "Add more detail to slide 3"}]
    }
)
```

---

## Error Codes - Full Reference

### HTTP Status Codes

| Status | Meaning | Recommended Action |
|--------|---------|-------------------|
| 200 | Success | - |
| 400 | Parameter error or file anomalies | Check request body format and file constraints |
| 401 | Authentication failure or token timeout | Verify API key; generate new JWT if expired |
| 404 | Feature unavailable or task not found | Check endpoint URL and subscription level |
| 429 | Rate limits, balance issues, or account violations | Implement exponential backoff; check account balance |
| 434 | Beta API access restricted | Request beta access or use stable endpoints |
| 435 | File size exceeds 100MB | Compress or split the file |
| 500 | Server errors | Retry after delay |

### Business Error Codes

| Code Range | Category | Examples |
|------------|----------|---------|
| 1000 | Auth failed | Invalid credentials |
| 1001 | Missing auth headers | No Authorization header |
| 1002 | Invalid token format | Malformed Bearer token |
| 1003 | Token expired | JWT or session expired |
| 1004 | Insufficient permissions | Feature not in subscription |
| 1110 | Inactive account | Account not activated |
| 1111 | Non-existent account | Account deleted or not found |
| 1112 | Locked account | Account suspended |
| 1113 | Account in arrears | Insufficient balance |
| 1121 | Subscription expired | Plan renewal required |
| 1210 | Invalid parameters | Missing required fields |
| 1211 | Model not found | Invalid model ID |
| 1212 | Unsupported method | HTTP method not allowed |
| 1213 | Permission denied | Insufficient API permissions |
| 1214 | Network error | Upstream service failure |
| 1234 | API call error | Generic API error |
| 1300 | Unsafe content | Input/output policy violation |
| 1301 | Rate limit exceeded | Too many requests per minute |
| 1302 | Daily limit exceeded | Daily quota exhausted |
| 1310 | Subscription expired | Feature requires active subscription |

---

## LangChain Integration

```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

llm = ChatOpenAI(
    model="glm-4.7",
    openai_api_key=os.environ["ZAI_API_KEY"],
    openai_api_base="https://api.z.ai/api/paas/v4/",
    streaming=True
)

messages = [
    SystemMessage(content="You are an expert Python developer."),
    HumanMessage(content="Refactor this to use dataclasses: ...")
]

response = llm.invoke(messages)
print(response.content)
```

LangChain streaming with callbacks:

```python
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

llm_streaming = ChatOpenAI(
    model="glm-5",
    openai_api_key=os.environ["ZAI_API_KEY"],
    openai_api_base="https://api.z.ai/api/paas/v4/",
    streaming=True,
    callbacks=[StreamingStdOutCallbackHandler()]
)
llm_streaming.invoke([HumanMessage(content="Generate a complete REST API with FastAPI.")])
```

---

## HTTP API Direct Usage

```bash
# Standard API
curl https://api.z.ai/api/paas/v4/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ZAI_API_KEY" \
  -d '{
    "model": "glm-4.7",
    "messages": [{"role": "user", "content": "Hello"}]
  }'

# Coding Plan endpoint
curl https://api.z.ai/api/coding/paas/v4/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ZAI_API_KEY" \
  -d '{
    "model": "glm-4.7",
    "messages": [{"role": "user", "content": "Write a merge sort in Python"}],
    "stream": false
  }'
```

---

## Model Selection Guide

| Task | Recommended Model | Reason |
|------|------------------|--------|
| Complex reasoning, agents | glm-5 | Flagship agentic model |
| Daily code generation | glm-4.7 | Balance of quality and speed |
| Code review with screenshots | glm-4.6v | Multimodal, 128K context |
| Simple completions | glm-4.6 | Efficient, cost-effective |
| Image generation | glm-image | Best quality, HD support |
| Fast image generation | cogview-4-250304 | Standard quality, faster |
| Audio transcription | glm-asr-2512 | Dedicated ASR model |
| Video generation | cogvideox-3 | Up to 4K, 60fps |
| Token counting | Use tokenizer endpoint | Supports glm-4.6, 4.6v, 4.5 |
| Document extraction | glm-ocr | Structured layout output |

---

## Coding Plan: IDE Setup Details

### Claude Code (Official)

Method 1 - Environment variables (recommended):
```bash
# Add to ~/.zshrc or ~/.bashrc
export ANTHROPIC_API_KEY="your-zai-api-key"
export ANTHROPIC_BASE_URL="https://api.z.ai/api/coding/paas/v4"
```

Method 2 - Claude Code settings file:
```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://api.z.ai/api/coding/paas/v4",
    "ANTHROPIC_API_KEY": "your-zai-api-key"
  }
}
```

### Cursor

1. Open Cursor Settings (Cmd+Shift+J on macOS)
2. Navigate to Models > Add Model
3. Set Base URL: `https://api.z.ai/api/coding/paas/v4`
4. Set API Key: your-zai-api-key
5. Model name: glm-4.7 (or glm-5 for best quality)

### Cline (VS Code Extension)

1. Open VS Code Settings
2. Search for "Cline API"
3. API Provider: OpenAI Compatible
4. OpenAI Base URL: `https://api.z.ai/api/coding/paas/v4`
5. OpenAI API Key: your-zai-api-key
6. Model: glm-4.7

### Goose

Configure in `~/.config/goose/profiles.yaml`:
```yaml
default:
  provider: openai
  model: glm-4.7
  api_key: your-zai-api-key
  base_url: https://api.z.ai/api/coding/paas/v4
```

---

## Context Caching

GLM API supports context caching to reduce latency and cost for repeated large context requests. Cache a large system prompt or document once, then reference it across multiple requests.

Check the Z.AI documentation at https://docs.z.ai/guides/features for the latest context caching API specification.

---

## Structured Output / JSON Mode

Force JSON output for data extraction tasks:

```python
response = client.chat.completions.create(
    model="glm-4.7",
    messages=[{
        "role": "user",
        "content": "Extract name, email, and role from: 'Alice (alice@example.com) is our backend engineer'"
    }],
    response_format={"type": "json_object"}
)

import json
data = json.loads(response.choices[0].message.content)
# {"name": "Alice", "email": "alice@example.com", "role": "backend engineer"}
```

---

## Java SDK Usage

```java
// Maven: com.zhipu.oapi:oapi-java-sdk
import com.zhipu.oapi.ClientV4;
import com.zhipu.oapi.service.v4.model.*;

ClientV4 client = new ClientV4.Builder(System.getenv("ZAI_API_KEY")).build();

List<ChatMessage> messages = new ArrayList<>();
messages.add(new ChatMessage(ChatMessageRole.USER.value(), "Write a Spring Boot controller."));

ChatCompletionRequest request = ChatCompletionRequest.builder()
    .model("glm-4.7")
    .messages(messages)
    .build();

ModelApiResponse response = client.invokeModelApi(request);
System.out.println(response.getData().getChoices().get(0).getMessage().getContent());
```

---

## GLM-OCR: Document & Image Text Extraction

**Endpoint:** `POST https://api.z.ai/api/paas/v4/layout_parsing`

Note: This is a separate endpoint from chat completions. It does NOT use `/chat/completions`.

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| model | string | Yes | Must be `"glm-ocr"` |
| file | string | Yes | Image/PDF URL or base64-encoded content |
| return_crop_images | boolean | No | Include cropped element screenshots (default: false) |
| need_layout_visualization | boolean | No | Return layout visualization image (default: false) |
| start_page_id | integer | No | PDF start page (min: 1) |
| end_page_id | integer | No | PDF end page (min: 1) |
| request_id | string | No | Custom request identifier |
| user_id | string | No | End-user ID for abuse monitoring (6-128 chars) |

### File Constraints

- Formats: PDF, JPG, PNG
- Single image: max 10MB
- PDF: max 50MB, max 100 pages
- Languages: Chinese, English, French, Spanish, Russian, German, Japanese, Korean, and more

### Response Format

```json
{
  "id": "task_123456789",
  "created": 1727156815,
  "model": "GLM-OCR",
  "md_results": "# Document Title\n\nExtracted text in markdown format...",
  "layout_details": [
    {
      "index": 0,
      "label": "text",
      "bbox_2d": [0.05, 0.02, 0.95, 0.08],
      "content": "Extracted text content here",
      "width": 2480,
      "height": 3508
    },
    {
      "index": 1,
      "label": "table",
      "bbox_2d": [0.1, 0.15, 0.9, 0.45],
      "content": "<table><tr><td>Cell</td></tr></table>",
      "width": 2480,
      "height": 3508
    }
  ],
  "usage": {
    "prompt_tokens": 1234,
    "completion_tokens": 567,
    "total_tokens": 1801
  }
}
```

### Layout Element Types

| label | Description | content format |
|-------|-------------|----------------|
| text | Regular text block | Plain text / Markdown |
| table | Table structure | HTML `<table>` |
| image | Image element | URL to cropped image |
| formula | Mathematical formula | LaTeX notation |

`bbox_2d` coordinates: `[x1, y1, x2, y2]` — Normalized 0-1 range. Multiply by `width`/`height` for pixel coordinates.

### Capabilities and Performance

- Printed/handwritten text recognition
- Table structure detection with HTML conversion
- Mathematical formula extraction (LaTeX)
- Card/receipt/form information extraction as JSON
- Multi-page PDF batch processing
- RAG-friendly markdown output

Performance: ~1.86 pages/second (PDF), ~0.67 images/second. Pricing: $0.03 per million tokens.

### OCR Examples

```python
# From URL
result = client.layout_parsing.create(model="glm-ocr", file="https://example.com/doc.png")
print(result.md_results)

# PDF page range
result = client.layout_parsing.create(
    model="glm-ocr", file="https://example.com/report.pdf",
    start_page_id=5, end_page_id=10
)

# Base64 input
import base64
with open("document.png", "rb") as f:
    image_b64 = base64.b64encode(f.read()).decode("utf-8")
result = client.layout_parsing.create(
    model="glm-ocr", file=f"data:image/png;base64,{image_b64}"
)
```

---

## External Links

- Z.AI Platform: https://z.ai
- Z.AI Documentation: https://docs.z.ai
- Quick Start Guide: https://docs.z.ai/guides/overview/quick-start
- API Reference: https://docs.z.ai/api-reference/
- API Key Management: https://z.ai/manage-apikey
- GLM Coding Plan Subscription: https://z.ai/subscribe
- Python SDK (zai-sdk): https://pypi.org/project/zai-sdk/
- Z.AI GitHub: Check docs.z.ai for official repository links
