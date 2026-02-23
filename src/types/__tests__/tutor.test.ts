import { describe, it, expect } from "vitest";
import type {
  ReadingResult,
  GrammarResult,
  VocabularyWordEntry,
  VocabularyResult,
  AnalyzeResponse,
} from "../tutor";

describe("Tutor Types", () => {
  describe("ReadingResult", () => {
    it("should have correct structure", () => {
      const result: ReadingResult = {
        content: "## 독해 훈련\n\nThe text discusses climate change and its effects.",
      };

      expect(result.content).toBeTypeOf("string");
    });
  });

  describe("GrammarResult", () => {
    it("should have correct structure", () => {
      const result: GrammarResult = {
        content: "## 문법 구조 이해\n\n문장 구조 분석 내용입니다.",
      };

      expect(result.content).toBeTypeOf("string");
    });
  });

  describe("VocabularyWordEntry", () => {
    it("should have correct structure", () => {
      const entry: VocabularyWordEntry = {
        word: "ephemeral",
        content: "## ephemeral\n\n어원: 라틴어 *ephemerus*에서 유래...",
      };

      expect(entry.word).toBeTypeOf("string");
      expect(entry.content).toBeTypeOf("string");
    });
  });

  describe("VocabularyResult", () => {
    it("should have correct structure", () => {
      const result: VocabularyResult = {
        words: [
          {
            word: "climate",
            content: "## climate\n\n어원 분석...",
          },
        ],
      };

      expect(Array.isArray(result.words)).toBe(true);
      expect(result.words[0].word).toBeTypeOf("string");
      expect(result.words[0].content).toBeTypeOf("string");
    });
  });

  describe("AnalyzeResponse", () => {
    it("should combine all results", () => {
      const response: AnalyzeResponse = {
        reading: {
          content: "독해 훈련 내용",
        },
        grammar: {
          content: "문법 구조 이해 내용",
        },
        vocabulary: {
          words: [],
        },
        sessionId: "550e8400-e29b-41d4-a716-446655440000",
      };

      expect(response.reading).toBeDefined();
      expect(response.grammar).toBeDefined();
      expect(response.vocabulary).toBeDefined();
      expect(response.sessionId).toBeTypeOf("string");
      expect(response.sessionId).toMatch(/^[a-f0-9-]+$/);
    });

    it("should allow null for reading, grammar, and vocabulary", () => {
      const response: AnalyzeResponse = {
        reading: null,
        grammar: null,
        vocabulary: null,
        sessionId: "550e8400-e29b-41d4-a716-446655440000",
      };

      expect(response.reading).toBeNull();
      expect(response.grammar).toBeNull();
      expect(response.vocabulary).toBeNull();
    });
  });
});
