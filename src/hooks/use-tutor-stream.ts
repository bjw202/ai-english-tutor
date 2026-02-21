import { useState, useCallback, useRef } from "react";

export interface TutorStreamState {
  readingContent: string;
  grammarContent: string;
  vocabularyContent: string;
  isStreaming: boolean;
  error: Error | null;
}

/**
 * Hook to manage SSE streaming from the tutor API
 */
export function useTutorStream() {
  const [state, setState] = useState<TutorStreamState>({
    readingContent: "",
    grammarContent: "",
    vocabularyContent: "",
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
      vocabularyContent: "",
    }));

    try {
      const response = await fetchFn();
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error("Response body is not readable");
      }

      let readingChunks = "";
      let grammarChunks = "";
      let vocabularyChunks = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6).trim();

            if (data === "[DONE]") {
              setState((prev) => ({
                ...prev,
                isStreaming: false,
              }));
              return;
            }

            // Parse agent-specific chunks
            if (data.startsWith("[READING]")) {
              const content = data.slice(9).trim();
              readingChunks += (readingChunks ? " " : "") + content;
              setState((prev) => ({
                ...prev,
                readingContent: readingChunks,
              }));
            } else if (data.startsWith("[GRAMMAR]")) {
              const content = data.slice(9).trim();
              grammarChunks += (grammarChunks ? " " : "") + content;
              setState((prev) => ({
                ...prev,
                grammarContent: grammarChunks,
              }));
            } else if (data.startsWith("[VOCABULARY]")) {
              const content = data.slice(12).trim();
              vocabularyChunks += (vocabularyChunks ? " " : "") + content;
              setState((prev) => ({
                ...prev,
                vocabularyContent: vocabularyChunks,
              }));
            }
          }
        }
      }
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
      vocabularyContent: "",
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
