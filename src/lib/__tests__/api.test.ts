import { describe, it, expect, vi, beforeEach } from "vitest";
import { analyzeText, analyzeImage, sendChat } from "../api";
import type { AnalyzeResponse } from "@/types/tutor";

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch as unknown as typeof fetch;

describe("API Client", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("analyzeText", () => {
    it("should send POST request to analyze endpoint", async () => {
      const mockResponse = {
        ok: true,
        json: async () => ({}),
      } as Response;
      mockFetch.mockResolvedValueOnce(mockResponse);

      await analyzeText("Test text", 3);

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/tutor/analyze",
        expect.objectContaining({
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: expect.stringContaining("Test text"),
        })
      );
    });

    it("should include level in request body", async () => {
      const mockResponse = {
        ok: true,
        json: async () => ({}),
      } as Response;
      mockFetch.mockResolvedValueOnce(mockResponse);

      await analyzeText("Test", 5);

      const callArgs = mockFetch.mock.calls[0];
      const options = callArgs[1] as RequestInit;
      const body = JSON.parse(options.body as string);
      expect(body.level).toBe(5);
    });

    it("should handle API errors", async () => {
      const mockResponse = {
        ok: false,
        status: 500,
        json: async () => ({ message: "Internal Server Error" }),
      } as Response;
      mockFetch.mockResolvedValueOnce(mockResponse);

      await expect(analyzeText("Test", 3)).rejects.toThrow();
    });

    it("should return response data on success", async () => {
      const mockData: AnalyzeResponse = {
        reading: {
          content: "## 독해 훈련\n\nTest summary",
        },
        grammar: {
          content: "## 문법 구조 이해\n\nGrammar analysis",
        },
        vocabulary: {
          words: [],
        },
        sessionId: "test-session-id",
      };

      const mockResponse = {
        ok: true,
        json: async () => mockData,
      } as Response;
      mockFetch.mockResolvedValueOnce(mockResponse);

      const result = await analyzeText("Test", 3);
      expect(result).toEqual(mockData);
    });
  });

  describe("analyzeImage", () => {
    it("should send FormData with image and level", async () => {
      const mockResponse = {
        ok: true,
        json: async () => ({}),
      } as Response;
      mockFetch.mockResolvedValueOnce(mockResponse);

      const file = new File(["test"], "test.jpg", { type: "image/jpeg" });
      await analyzeImage(file, 2);

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/tutor/analyze-image",
        expect.objectContaining({
          method: "POST",
          body: expect.any(FormData),
        })
      );
    });

    it("should include file and level in FormData", async () => {
      const mockResponse = {
        ok: true,
        json: async () => ({}),
      } as Response;
      mockFetch.mockResolvedValueOnce(mockResponse);

      const file = new File(["test"], "test.jpg", { type: "image/jpeg" });
      await analyzeImage(file, 4);

      const callArgs = mockFetch.mock.calls[0];
      const options = callArgs[1] as RequestInit;
      const formData = options.body as FormData;

      expect(formData.get("file")).toBe(file);
      expect(formData.get("level")).toBe("4");
    });
  });

  describe("sendChat", () => {
    it("should send POST request to chat endpoint", async () => {
      const mockResponse = {
        ok: true,
        json: async () => ({}),
      } as Response;
      mockFetch.mockResolvedValueOnce(mockResponse);

      await sendChat("session-123", "Hello", 3);

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/tutor/chat",
        expect.objectContaining({
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
        })
      );
    });

    it("should include sessionId, message, and level in request body", async () => {
      const mockResponse = {
        ok: true,
        json: async () => ({}),
      } as Response;
      mockFetch.mockResolvedValueOnce(mockResponse);

      await sendChat("session-123", "Test message", 5);

      const callArgs = mockFetch.mock.calls[0];
      const options = callArgs[1] as RequestInit;
      const body = JSON.parse(options.body as string);

      expect(body.sessionId).toBe("session-123");
      expect(body.message).toBe("Test message");
      expect(body.level).toBe(5);
    });
  });
});
