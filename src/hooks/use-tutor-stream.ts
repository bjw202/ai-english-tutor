import { useState, useCallback, useRef } from "react";
import type { VocabularyWordEntry } from "@/types/tutor";

export interface TutorStreamState {
  readingContent: string;
  grammarContent: string;
  vocabularyWords: VocabularyWordEntry[];
  isStreaming: boolean;
  error: Error | null;
}

/**
 * Hook to manage SSE streaming from the tutor API
 * Parses SSE events in format:
 *   event: reading_chunk
 *   data: {"content": "Korean Markdown string"}
 *
 *   event: grammar_chunk
 *   data: {"content": "Korean Markdown string"}
 *
 *   event: vocabulary_chunk
 *   data: {"words": [{"word": "string", "content": "Korean Markdown string"}, ...]}
 *
 *   event: done
 *   data: {}
 */
export function useTutorStream() {
  const [state, setState] = useState<TutorStreamState>({
    readingContent: "",
    grammarContent: "",
    vocabularyWords: [],
    isStreaming: false,
    error: null,
  });

  const abortControllerRef = useRef<AbortController | null>(null);

  const startStream = useCallback(async (fetchFn: () => Promise<Response>) => {
    // Cancel any existing stream
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new abort controller for this stream
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    setState((prev) => ({
      ...prev,
      isStreaming: true,
      error: null,
      readingContent: "",
      grammarContent: "",
      vocabularyWords: [],
    }));

    try {
      const response = await fetchFn();
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error("Response body is not readable");
      }

      let buffer = "";
      let currentEvent = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || ""; // Keep incomplete line in buffer

        for (const line of lines) {
          // Parse event type
          if (line.startsWith("event: ")) {
            currentEvent = line.slice(7).trim();
            continue;
          }

          // Parse data
          if (line.startsWith("data: ")) {
            const dataStr = line.slice(6).trim();

            // Handle done event
            if (currentEvent === "done") {
              setState((prev) => ({
                ...prev,
                isStreaming: false,
              }));
              return;
            }

            // Parse JSON data
            try {
              const data = JSON.parse(dataStr);

              if (currentEvent === "reading_chunk") {
                setState((prev) => ({
                  ...prev,
                  readingContent: data.content || "",
                }));
              } else if (currentEvent === "grammar_chunk") {
                setState((prev) => ({
                  ...prev,
                  grammarContent: data.content || "",
                }));
              } else if (currentEvent === "vocabulary_chunk") {
                setState((prev) => ({
                  ...prev,
                  vocabularyWords: data.words || [],
                }));
              }
            } catch {
              // If JSON parsing fails, treat as plain text
              console.warn("Failed to parse SSE data as JSON:", dataStr);
            }
          }
        }
      }

      // Stream completed
      setState((prev) => ({
        ...prev,
        isStreaming: false,
      }));
    } catch (error) {
      if (error instanceof Error && error.name !== "AbortError") {
        setState((prev) => ({
          ...prev,
          isStreaming: false,
          error,
        }));
      }
    } finally {
      abortControllerRef.current = null;
    }
  }, []);

  const reset = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setState({
      readingContent: "",
      grammarContent: "",
      vocabularyWords: [],
      isStreaming: false,
      error: null,
    });
  }, []);

  return {
    state,
    startStream,
    reset,
  };
}
