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
});
