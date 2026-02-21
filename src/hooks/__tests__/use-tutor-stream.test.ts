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
    expect(result.current.state.vocabularyContent).toBe("");
    expect(result.current.state.isStreaming).toBe(false);
    expect(result.current.state.error).toBeNull();
  });

  it("should parse READING chunks and update reading content", async () => {
    const chunks = [
      "data: [READING] First sentence\n\n",
      "data: [READING] Second sentence\n\n",
      "data: [DONE]\n\n",
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

    expect(result.current.state.readingContent).toContain("First sentence");
    expect(result.current.state.readingContent).toContain("Second sentence");
  });

  it("should parse GRAMMAR chunks and update grammar content", async () => {
    const chunks = [
      "data: [GRAMMAR] Grammar issue found\n\n",
      "data: [DONE]\n\n",
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

    expect(result.current.state.grammarContent).toContain("Grammar issue found");
  });

  it("should parse VOCABULARY chunks and update vocabulary content", async () => {
    const chunks = [
      "data: [VOCABULARY] New word definition\n\n",
      "data: [DONE]\n\n",
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

    expect(result.current.state.vocabularyContent).toContain("New word definition");
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
      "data: [READING] Content\n\n",
      "data: [DONE]\n\n",
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

    expect(result.current.state.readingContent).toBe("Content");

    act(() => {
      result.current.reset();
    });

    expect(result.current.state.readingContent).toBe("");
    expect(result.current.state.grammarContent).toBe("");
    expect(result.current.state.vocabularyContent).toBe("");
    expect(result.current.state.error).toBeNull();
  });
});
