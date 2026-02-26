import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useTutorStream } from "../use-tutor-stream";

// Mock fetch for SSE streaming
const mockFetch = vi.fn();
global.fetch = mockFetch as unknown as typeof fetch;

describe("useTutorStream", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("should have initial state with empty content and not streaming", () => {
    const { result } = renderHook(() => useTutorStream());

    expect(result.current.state.readingContent).toBe("");
    expect(result.current.state.grammarContent).toBe("");
    expect(result.current.state.vocabularyWords).toEqual([]);
    expect(result.current.state.vocabularyRawContent).toBe("");
    expect(result.current.state.isStreaming).toBe(false);
    expect(result.current.state.error).toBeNull();
  });

  it("should parse reading_chunk events and update reading content", async () => {
    const chunks = [
      'event: reading_chunk\ndata: {"content": "## 독해 훈련\\n\\n첫 번째 문장"}\n\n',
      'event: done\ndata: {}\n\n',
    ];

    const mockReader = {
      read: vi.fn(),
    };

    chunks.forEach((chunk) => {
      mockReader.read.mockResolvedValueOnce({
        done: false,
        value: new TextEncoder().encode(chunk),
      });
    });

    mockReader.read.mockResolvedValueOnce({ done: true });

    mockFetch.mockResolvedValueOnce({
      ok: true,
      body: {
        getReader: () => mockReader,
      },
    });

    const { result } = renderHook(() => useTutorStream());

    await act(async () => {
      await result.current.startStream(() => fetch("/api/test"));
    });

    expect(result.current.state.readingContent).toContain("독해 훈련");
  });

  it("should parse grammar_chunk events and update grammar content", async () => {
    const chunks = [
      'event: grammar_chunk\ndata: {"content": "## 문법 구조\\n\\n분석 내용"}\n\n',
      'event: done\ndata: {}\n\n',
    ];

    const mockReader = {
      read: vi.fn(),
    };

    chunks.forEach((chunk) => {
      mockReader.read.mockResolvedValueOnce({
        done: false,
        value: new TextEncoder().encode(chunk),
      });
    });

    mockReader.read.mockResolvedValueOnce({ done: true });

    mockFetch.mockResolvedValueOnce({
      ok: true,
      body: {
        getReader: () => mockReader,
      },
    });

    const { result } = renderHook(() => useTutorStream());

    await act(async () => {
      await result.current.startStream(() => fetch("/api/test"));
    });

    expect(result.current.state.grammarContent).toContain("문법 구조");
  });

  it("should parse vocabulary_chunk events and update vocabularyWords", async () => {
    const words = [
      { word: "ephemeral", content: "## ephemeral\n\n어원 설명" },
      { word: "abundant", content: "## abundant\n\n어원 설명" },
    ];
    const chunks = [
      `event: vocabulary_chunk\ndata: ${JSON.stringify({ words })}\n\n`,
      'event: done\ndata: {}\n\n',
    ];

    const mockReader = {
      read: vi.fn(),
    };

    chunks.forEach((chunk) => {
      mockReader.read.mockResolvedValueOnce({
        done: false,
        value: new TextEncoder().encode(chunk),
      });
    });

    mockReader.read.mockResolvedValueOnce({ done: true });

    mockFetch.mockResolvedValueOnce({
      ok: true,
      body: {
        getReader: () => mockReader,
      },
    });

    const { result } = renderHook(() => useTutorStream());

    await act(async () => {
      await result.current.startStream(() => fetch("/api/test"));
    });

    expect(result.current.state.vocabularyWords).toHaveLength(2);
    expect(result.current.state.vocabularyWords[0].word).toBe("ephemeral");
    expect(result.current.state.vocabularyWords[1].word).toBe("abundant");
  });

  it("should handle stream errors", async () => {
    mockFetch.mockRejectedValueOnce(new Error("Network error"));

    const { result } = renderHook(() => useTutorStream());

    await act(async () => {
      try {
        await result.current.startStream(() => fetch("/api/test"));
      } catch {
        // Expected
      }
    });

    expect(result.current.state.error).toBeTruthy();
    expect(result.current.state.isStreaming).toBe(false);
  });

  it("should reset state when reset is called", async () => {
    const chunks = [
      'event: reading_chunk\ndata: {"content": "독해 내용"}\n\n',
      'event: done\ndata: {}\n\n',
    ];

    const mockReader = {
      read: vi.fn(),
    };

    chunks.forEach((chunk) => {
      mockReader.read.mockResolvedValueOnce({
        done: false,
        value: new TextEncoder().encode(chunk),
      });
    });

    mockReader.read.mockResolvedValueOnce({ done: true });

    mockFetch.mockResolvedValueOnce({
      ok: true,
      body: {
        getReader: () => mockReader,
      },
    });

    const { result } = renderHook(() => useTutorStream());

    await act(async () => {
      await result.current.startStream(() => fetch("/api/test"));
    });

    expect(result.current.state.readingContent).toBe("독해 내용");

    act(() => {
      result.current.reset();
    });

    expect(result.current.state.readingContent).toBe("");
    expect(result.current.state.grammarContent).toBe("");
    expect(result.current.state.vocabularyWords).toEqual([]);
    expect(result.current.state.error).toBeNull();
  });

  it("should append reading tokens sequentially via reading_token events", async () => {
    const chunks = [
      'event: reading_token\ndata: {"token": "Hello "}\n\n',
      'event: reading_token\ndata: {"token": "world"}\n\n',
      'event: done\ndata: {}\n\n',
    ];
    const mockReader = { read: vi.fn() };
    chunks.forEach((chunk) => {
      mockReader.read.mockResolvedValueOnce({
        done: false,
        value: new TextEncoder().encode(chunk),
      });
    });
    mockReader.read.mockResolvedValueOnce({ done: true });
    mockFetch.mockResolvedValueOnce({
      ok: true,
      body: { getReader: () => mockReader },
    });

    const { result } = renderHook(() => useTutorStream());
    await act(async () => {
      await result.current.startStream(() => fetch("/api/test"));
    });

    expect(result.current.state.readingContent).toBe("Hello world");
  });

  it("should append grammar tokens sequentially via grammar_token events", async () => {
    const chunks = [
      'event: grammar_token\ndata: {"token": "Grammar "}\n\n',
      'event: grammar_token\ndata: {"token": "analysis"}\n\n',
      'event: done\ndata: {}\n\n',
    ];
    const mockReader = { read: vi.fn() };
    chunks.forEach((chunk) => {
      mockReader.read.mockResolvedValueOnce({
        done: false,
        value: new TextEncoder().encode(chunk),
      });
    });
    mockReader.read.mockResolvedValueOnce({ done: true });
    mockFetch.mockResolvedValueOnce({
      ok: true,
      body: { getReader: () => mockReader },
    });

    const { result } = renderHook(() => useTutorStream());
    await act(async () => {
      await result.current.startStream(() => fetch("/api/test"));
    });

    expect(result.current.state.grammarContent).toBe("Grammar analysis");
  });

  it("should set readingStreaming to false on reading_done event", async () => {
    const chunks = [
      'event: reading_token\ndata: {"token": "text"}\n\n',
      'event: reading_done\ndata: {"section": "reading"}\n\n',
      'event: done\ndata: {}\n\n',
    ];
    const mockReader = { read: vi.fn() };
    chunks.forEach((chunk) => {
      mockReader.read.mockResolvedValueOnce({
        done: false,
        value: new TextEncoder().encode(chunk),
      });
    });
    mockReader.read.mockResolvedValueOnce({ done: true });
    mockFetch.mockResolvedValueOnce({
      ok: true,
      body: { getReader: () => mockReader },
    });

    const { result } = renderHook(() => useTutorStream());
    await act(async () => {
      await result.current.startStream(() => fetch("/api/test"));
    });

    expect(result.current.state.readingStreaming).toBe(false);
    expect(result.current.state.readingContent).toBe("text");
  });

  it("should set grammarStreaming to false on grammar_done event", async () => {
    const chunks = [
      'event: grammar_token\ndata: {"token": "analysis"}\n\n',
      'event: grammar_done\ndata: {"section": "grammar"}\n\n',
      'event: done\ndata: {}\n\n',
    ];
    const mockReader = { read: vi.fn() };
    chunks.forEach((chunk) => {
      mockReader.read.mockResolvedValueOnce({
        done: false,
        value: new TextEncoder().encode(chunk),
      });
    });
    mockReader.read.mockResolvedValueOnce({ done: true });
    mockFetch.mockResolvedValueOnce({
      ok: true,
      body: { getReader: () => mockReader },
    });

    const { result } = renderHook(() => useTutorStream());
    await act(async () => {
      await result.current.startStream(() => fetch("/api/test"));
    });

    expect(result.current.state.grammarStreaming).toBe(false);
    expect(result.current.state.grammarContent).toBe("analysis");
  });

  it("should set vocabularyStreaming to false on vocabulary_chunk event", async () => {
    const words = [{ word: "test", content: "content" }];
    const chunks = [
      `event: vocabulary_chunk\ndata: ${JSON.stringify({ words })}\n\n`,
      'event: done\ndata: {}\n\n',
    ];
    const mockReader = { read: vi.fn() };
    chunks.forEach((chunk) => {
      mockReader.read.mockResolvedValueOnce({
        done: false,
        value: new TextEncoder().encode(chunk),
      });
    });
    mockReader.read.mockResolvedValueOnce({ done: true });
    mockFetch.mockResolvedValueOnce({
      ok: true,
      body: { getReader: () => mockReader },
    });

    const { result } = renderHook(() => useTutorStream());
    await act(async () => {
      await result.current.startStream(() => fetch("/api/test"));
    });

    expect(result.current.state.vocabularyStreaming).toBe(false);
    expect(result.current.state.vocabularyWords).toHaveLength(1);
  });

  it("should have section streaming flags as false in initial state", () => {
    const { result } = renderHook(() => useTutorStream());

    expect(result.current.state.readingStreaming).toBe(false);
    expect(result.current.state.grammarStreaming).toBe(false);
    expect(result.current.state.vocabularyStreaming).toBe(false);
  });

  it("should set vocabularyStreaming to false on vocabulary_done event", async () => {
    const chunks = [
      'event: vocabulary_done\ndata: {"section": "vocabulary"}\n\n',
      'event: done\ndata: {}\n\n',
    ];
    const mockReader = { read: vi.fn() };
    chunks.forEach((chunk) => {
      mockReader.read.mockResolvedValueOnce({
        done: false,
        value: new TextEncoder().encode(chunk),
      });
    });
    mockReader.read.mockResolvedValueOnce({ done: true });
    mockFetch.mockResolvedValueOnce({
      ok: true,
      body: { getReader: () => mockReader },
    });

    const { result } = renderHook(() => useTutorStream());
    await act(async () => {
      await result.current.startStream(() => fetch("/api/test"));
    });

    expect(result.current.state.vocabularyStreaming).toBe(false);
  });

  it("should handle vocabulary_error event and set error state", async () => {
    const chunks = [
      'event: vocabulary_error\ndata: {"message": "LLM API failed", "code": "vocabulary_error"}\n\n',
      'event: vocabulary_done\ndata: {"section": "vocabulary"}\n\n',
      'event: done\ndata: {}\n\n',
    ];
    const mockReader = { read: vi.fn() };
    chunks.forEach((chunk) => {
      mockReader.read.mockResolvedValueOnce({
        done: false,
        value: new TextEncoder().encode(chunk),
      });
    });
    mockReader.read.mockResolvedValueOnce({ done: true });
    mockFetch.mockResolvedValueOnce({
      ok: true,
      body: { getReader: () => mockReader },
    });

    const { result } = renderHook(() => useTutorStream());
    await act(async () => {
      await result.current.startStream(() => fetch("/api/test"));
    });

    expect(result.current.state.vocabularyError).toBe("LLM API failed");
    expect(result.current.state.vocabularyStreaming).toBe(false);
  });

  it("should accumulate vocabularyRawContent via vocabulary_token events", async () => {
    const chunks = [
      'event: vocabulary_token\ndata: {"token": "## ephemeral"}\n\n',
      'event: vocabulary_token\ndata: {"token": "\\n어원 설명"}\n\n',
      'event: done\ndata: {}\n\n',
    ];
    const mockReader = { read: vi.fn() };
    chunks.forEach((chunk) => {
      mockReader.read.mockResolvedValueOnce({
        done: false,
        value: new TextEncoder().encode(chunk),
      });
    });
    mockReader.read.mockResolvedValueOnce({ done: true });
    mockFetch.mockResolvedValueOnce({
      ok: true,
      body: { getReader: () => mockReader },
    });

    const { result } = renderHook(() => useTutorStream());
    await act(async () => {
      await result.current.startStream(() => fetch("/api/test"));
    });

    expect(result.current.state.vocabularyRawContent).toBe("## ephemeral\n어원 설명");
    expect(result.current.state.vocabularyStreaming).toBe(false);
  });

  it("should keep vocabularyStreaming true while vocabulary_token events arrive", async () => {
    const chunks = [
      'event: vocabulary_token\ndata: {"token": "## test"}\n\n',
      'event: vocabulary_done\ndata: {"section": "vocabulary"}\n\n',
      'event: done\ndata: {}\n\n',
    ];
    const mockReader = { read: vi.fn() };
    chunks.forEach((chunk) => {
      mockReader.read.mockResolvedValueOnce({
        done: false,
        value: new TextEncoder().encode(chunk),
      });
    });
    mockReader.read.mockResolvedValueOnce({ done: true });
    mockFetch.mockResolvedValueOnce({
      ok: true,
      body: { getReader: () => mockReader },
    });

    const { result } = renderHook(() => useTutorStream());
    await act(async () => {
      await result.current.startStream(() => fetch("/api/test"));
    });

    // After vocabulary_done, vocabularyStreaming should be false
    expect(result.current.state.vocabularyStreaming).toBe(false);
    // Raw content accumulated
    expect(result.current.state.vocabularyRawContent).toBe("## test");
  });

  it("should set vocabularyWords from vocabulary_chunk after vocabulary_token events", async () => {
    const words = [{ word: "ephemeral", content: "어원 설명" }];
    const chunks = [
      'event: vocabulary_token\ndata: {"token": "## ephemeral"}\n\n',
      `event: vocabulary_chunk\ndata: ${JSON.stringify({ words })}\n\n`,
      'event: done\ndata: {}\n\n',
    ];
    const mockReader = { read: vi.fn() };
    chunks.forEach((chunk) => {
      mockReader.read.mockResolvedValueOnce({
        done: false,
        value: new TextEncoder().encode(chunk),
      });
    });
    mockReader.read.mockResolvedValueOnce({ done: true });
    mockFetch.mockResolvedValueOnce({
      ok: true,
      body: { getReader: () => mockReader },
    });

    const { result } = renderHook(() => useTutorStream());
    await act(async () => {
      await result.current.startStream(() => fetch("/api/test"));
    });

    // vocabulary_chunk should populate words and stop streaming
    expect(result.current.state.vocabularyWords).toHaveLength(1);
    expect(result.current.state.vocabularyWords[0].word).toBe("ephemeral");
    expect(result.current.state.vocabularyStreaming).toBe(false);
    // Raw content also accumulated from prior token events
    expect(result.current.state.vocabularyRawContent).toBe("## ephemeral");
  });

  it("should reset vocabularyRawContent when a new stream starts", async () => {
    // First stream: accumulate raw content
    const firstChunks = [
      'event: vocabulary_token\ndata: {"token": "previous content"}\n\n',
      'event: done\ndata: {}\n\n',
    ];
    const firstReader = { read: vi.fn() };
    firstChunks.forEach((chunk) => {
      firstReader.read.mockResolvedValueOnce({
        done: false,
        value: new TextEncoder().encode(chunk),
      });
    });
    firstReader.read.mockResolvedValueOnce({ done: true });
    mockFetch.mockResolvedValueOnce({
      ok: true,
      body: { getReader: () => firstReader },
    });

    const { result } = renderHook(() => useTutorStream());
    await act(async () => {
      await result.current.startStream(() => fetch("/api/test"));
    });

    expect(result.current.state.vocabularyRawContent).toBe("previous content");

    // Second stream: vocabularyRawContent should be reset at start
    const secondChunks = ['event: done\ndata: {}\n\n'];
    const secondReader = { read: vi.fn() };
    secondChunks.forEach((chunk) => {
      secondReader.read.mockResolvedValueOnce({
        done: false,
        value: new TextEncoder().encode(chunk),
      });
    });
    secondReader.read.mockResolvedValueOnce({ done: true });
    mockFetch.mockResolvedValueOnce({
      ok: true,
      body: { getReader: () => secondReader },
    });

    await act(async () => {
      await result.current.startStream(() => fetch("/api/test"));
    });

    expect(result.current.state.vocabularyRawContent).toBe("");
  });

  it("should handle reading_error event: set readingStreaming to false and readingError message", async () => {
    const chunks = [
      'event: reading_token\ndata: {"token": "partial "}\n\n',
      'event: reading_error\ndata: {"message": "LLM failed", "code": "reading_error"}\n\n',
      'event: done\ndata: {}\n\n',
    ];
    const mockReader = { read: vi.fn() };
    chunks.forEach((chunk) => {
      mockReader.read.mockResolvedValueOnce({
        done: false,
        value: new TextEncoder().encode(chunk),
      });
    });
    mockReader.read.mockResolvedValueOnce({ done: true });
    mockFetch.mockResolvedValueOnce({
      ok: true,
      body: { getReader: () => mockReader },
    });

    const { result } = renderHook(() => useTutorStream());
    await act(async () => {
      await result.current.startStream(() => fetch("/api/test"));
    });

    expect(result.current.state.readingError).toBe("LLM failed");
    expect(result.current.state.readingStreaming).toBe(false);
    // Other agents' streaming states should not be affected by reading_error alone
    expect(result.current.state.grammarError).toBeNull();
    expect(result.current.state.vocabularyError).toBeNull();
  });

  it("should handle grammar_error event: set grammarStreaming to false and grammarError message", async () => {
    const chunks = [
      'event: grammar_token\ndata: {"token": "partial "}\n\n',
      'event: grammar_error\ndata: {"message": "LLM failed", "code": "grammar_error"}\n\n',
      'event: done\ndata: {}\n\n',
    ];
    const mockReader = { read: vi.fn() };
    chunks.forEach((chunk) => {
      mockReader.read.mockResolvedValueOnce({
        done: false,
        value: new TextEncoder().encode(chunk),
      });
    });
    mockReader.read.mockResolvedValueOnce({ done: true });
    mockFetch.mockResolvedValueOnce({
      ok: true,
      body: { getReader: () => mockReader },
    });

    const { result } = renderHook(() => useTutorStream());
    await act(async () => {
      await result.current.startStream(() => fetch("/api/test"));
    });

    expect(result.current.state.grammarError).toBe("LLM failed");
    expect(result.current.state.grammarStreaming).toBe(false);
    // Other agents' streaming states should not be affected by grammar_error alone
    expect(result.current.state.readingError).toBeNull();
    expect(result.current.state.vocabularyError).toBeNull();
  });

  it("should not affect other agents when one agent fails independently", async () => {
    const words = [{ word: "test", content: "content" }];
    const chunks = [
      'event: reading_error\ndata: {"message": "Reading failed", "code": "reading_error"}\n\n',
      `event: vocabulary_chunk\ndata: ${JSON.stringify({ words })}\n\n`,
      'event: done\ndata: {}\n\n',
    ];
    const mockReader = { read: vi.fn() };
    chunks.forEach((chunk) => {
      mockReader.read.mockResolvedValueOnce({
        done: false,
        value: new TextEncoder().encode(chunk),
      });
    });
    mockReader.read.mockResolvedValueOnce({ done: true });
    mockFetch.mockResolvedValueOnce({
      ok: true,
      body: { getReader: () => mockReader },
    });

    const { result } = renderHook(() => useTutorStream());
    await act(async () => {
      await result.current.startStream(() => fetch("/api/test"));
    });

    // Reading failed independently
    expect(result.current.state.readingError).toBe("Reading failed");
    expect(result.current.state.readingStreaming).toBe(false);
    // Vocabulary succeeded independently
    expect(result.current.state.vocabularyWords).toHaveLength(1);
    expect(result.current.state.vocabularyStreaming).toBe(false);
    // Grammar streaming was stopped by done event, error remains null
    expect(result.current.state.grammarError).toBeNull();
  });

  it("should reset vocabularyRawContent when reset is called", async () => {
    const chunks = [
      'event: vocabulary_token\ndata: {"token": "some content"}\n\n',
      'event: done\ndata: {}\n\n',
    ];
    const mockReader = { read: vi.fn() };
    chunks.forEach((chunk) => {
      mockReader.read.mockResolvedValueOnce({
        done: false,
        value: new TextEncoder().encode(chunk),
      });
    });
    mockReader.read.mockResolvedValueOnce({ done: true });
    mockFetch.mockResolvedValueOnce({
      ok: true,
      body: { getReader: () => mockReader },
    });

    const { result } = renderHook(() => useTutorStream());
    await act(async () => {
      await result.current.startStream(() => fetch("/api/test"));
    });

    expect(result.current.state.vocabularyRawContent).toBe("some content");

    act(() => {
      result.current.reset();
    });

    expect(result.current.state.vocabularyRawContent).toBe("");
  });
});
