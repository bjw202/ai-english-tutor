import { useState, useCallback, useRef } from "react";
import type { VocabularyWordEntry } from "@/types/tutor";

export interface TutorStreamState {
  readingContent: string;
  grammarContent: string;
  vocabularyWords: VocabularyWordEntry[];
  vocabularyRawContent: string;
  isStreaming: boolean;
  error: Error | null;
  readingStreaming: boolean;
  grammarStreaming: boolean;
  vocabularyStreaming: boolean;
  vocabularyError: string | null;
}

/**
 * Hook to manage SSE streaming from the tutor API
 * Supports token-level streaming events:
 *   event: reading_token
 *   data: {"token": "string"}
 *
 *   event: grammar_token
 *   data: {"token": "string"}
 *
 *   event: reading_done
 *   data: {"section": "reading"}
 *
 *   event: grammar_done
 *   data: {"section": "grammar"}
 *
 * Also supports backward-compatible chunk events:
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
    vocabularyRawContent: "",
    isStreaming: false,
    error: null,
    readingStreaming: false,
    grammarStreaming: false,
    vocabularyStreaming: false,
    vocabularyError: null,
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
      vocabularyRawContent: "",
      readingStreaming: true,
      grammarStreaming: true,
      vocabularyStreaming: true,
      vocabularyError: null,
    }));

    try {
      const response = await fetchFn();

      if (!response.ok) {
        const errorText = await response.text().catch(() => "");
        let errorMessage = `Analysis failed (${response.status})`;
        try {
          const errorData = JSON.parse(errorText);
          errorMessage = errorData.error || errorData.detail || errorMessage;
        } catch {
          // not JSON, use default message
        }
        throw new Error(errorMessage);
      }

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

            // Handle error event from backend
            if (currentEvent === "error") {
              try {
                const errorData = JSON.parse(dataStr);
                const errorMessage =
                  errorData.message || errorData.error || "Analysis failed";
                setState((prev) => ({
                  ...prev,
                  isStreaming: false,
                  readingStreaming: false,
                  grammarStreaming: false,
                  vocabularyStreaming: false,
                  error: new Error(errorMessage),
                }));
              } catch {
                setState((prev) => ({
                  ...prev,
                  isStreaming: false,
                  readingStreaming: false,
                  grammarStreaming: false,
                  vocabularyStreaming: false,
                  error: new Error(dataStr || "Analysis failed"),
                }));
              }
              return;
            }

            // Handle done event
            if (currentEvent === "done") {
              setState((prev) => ({
                ...prev,
                isStreaming: false,
                readingStreaming: false,
                grammarStreaming: false,
                vocabularyStreaming: false,
              }));
              return;
            }

            // Parse JSON data
            try {
              const data = JSON.parse(dataStr);

              // NEW: Token-level streaming events
              if (currentEvent === "reading_token") {
                setState((prev) => ({
                  ...prev,
                  readingContent: prev.readingContent + (data.token || ""),
                }));
              } else if (currentEvent === "grammar_token") {
                setState((prev) => ({
                  ...prev,
                  grammarContent: prev.grammarContent + (data.token || ""),
                }));
              } else if (currentEvent === "vocabulary_token") {
                setState((prev) => ({
                  ...prev,
                  vocabularyRawContent:
                    prev.vocabularyRawContent + (data.token || ""),
                }));
              } else if (currentEvent === "reading_done") {
                setState((prev) => ({
                  ...prev,
                  readingStreaming: false,
                }));
              } else if (currentEvent === "grammar_done") {
                setState((prev) => ({
                  ...prev,
                  grammarStreaming: false,
                }));
              } else if (currentEvent === "reading_chunk") {
                // Backward compatibility: full chunk replacement
                setState((prev) => ({
                  ...prev,
                  readingContent: data.content || "",
                }));
              } else if (currentEvent === "grammar_chunk") {
                // Backward compatibility: full chunk replacement
                setState((prev) => ({
                  ...prev,
                  grammarContent: data.content || "",
                }));
              } else if (currentEvent === "vocabulary_chunk") {
                setState((prev) => ({
                  ...prev,
                  vocabularyWords: data.words || [],
                  vocabularyStreaming: false,
                }));
              } else if (currentEvent === "vocabulary_done") {
                setState((prev) => ({
                  ...prev,
                  vocabularyStreaming: false,
                }));
              } else if (currentEvent === "vocabulary_error") {
                setState((prev) => ({
                  ...prev,
                  vocabularyStreaming: false,
                  vocabularyError: data.message || "Vocabulary analysis failed",
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
        readingStreaming: false,
        grammarStreaming: false,
        vocabularyStreaming: false,
      }));
    } catch (error) {
      if (error instanceof Error && error.name !== "AbortError") {
        setState((prev) => ({
          ...prev,
          isStreaming: false,
          readingStreaming: false,
          grammarStreaming: false,
          vocabularyStreaming: false,
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
      vocabularyRawContent: "",
      isStreaming: false,
      error: null,
      readingStreaming: false,
      grammarStreaming: false,
      vocabularyStreaming: false,
      vocabularyError: null,
    });
  }, []);

  return {
    state,
    startStream,
    reset,
  };
}
