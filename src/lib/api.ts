import type { AnalyzeResponse } from "@/types/tutor";

/**
 * Custom API error class
 */
export class ApiError extends Error {
  constructor(
    public status: number,
    public message: string,
    public code?: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/**
 * Analyze English text and return comprehensive analysis
 */
export async function analyzeText(
  text: string,
  level: number
): Promise<AnalyzeResponse> {
  const response = await fetch("/api/tutor/analyze", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ text, level }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ message: "Unknown error" }));
    throw new ApiError(response.status, errorData.message || "Analysis failed", errorData.code);
  }

  return response.json() as Promise<AnalyzeResponse>;
}

/**
 * Analyze text from an uploaded image using OCR
 */
export async function analyzeImage(
  file: File,
  level: number
): Promise<AnalyzeResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("level", String(level));

  const response = await fetch("/api/tutor/analyze-image", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ message: "Unknown error" }));
    throw new ApiError(response.status, errorData.message || "Image analysis failed", errorData.code);
  }

  return response.json() as Promise<AnalyzeResponse>;
}

/**
 * Send a follow-up chat message with session context
 */
export async function sendChat(
  sessionId: string,
  message: string,
  level: number
): Promise<AnalyzeResponse> {
  const response = await fetch("/api/tutor/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ sessionId, message, level }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ message: "Unknown error" }));
    throw new ApiError(response.status, errorData.message || "Chat request failed", errorData.code);
  }

  return response.json() as Promise<AnalyzeResponse>;
}

/**
 * SSE stream reader for real-time analysis updates
 */
export async function* streamAnalysis(
  fetchPromise: Promise<Response>
): AsyncGenerator<string, void, unknown> {
  const response = await fetchPromise;
  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  if (!reader) {
    throw new Error("Response body is not readable");
  }

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split("\n");

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data = line.slice(6);
          if (data === "[DONE]") return;
          yield data;
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
