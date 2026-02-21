import { describe, it, expect } from "vitest";
import type {
  ReadingResult,
  GrammarResult,
  GrammarIssue,
  VocabularyResult,
  VocabularyWord,
  AnalyzeResponse,
} from "../tutor";

describe("Tutor Types", () => {
  describe("GrammarIssue", () => {
    it("should have correct structure", () => {
      const issue: GrammarIssue = {
        issue: "Subject-verb agreement",
        type: "grammar",
        suggestion: "Use 'changes' instead of 'change'",
        position: { start: 10, end: 20 },
      };

      expect(issue.issue).toBeTypeOf("string");
      expect(issue.type).toBeTypeOf("string");
      expect(issue.suggestion).toBeTypeOf("string");
      expect(issue.position?.start).toBeTypeOf("number");
      expect(issue.position?.end).toBeTypeOf("number");
    });
  });

  describe("ReadingResult", () => {
    it("should have correct structure", () => {
      const result: ReadingResult = {
        summary: "The text discusses climate change",
        keyPoints: [
          "Global temperatures are rising",
          "Human activities contribute to greenhouse gases",
        ],
        comprehensionLevel: 3,
      };

      expect(result.summary).toBeTypeOf("string");
      expect(Array.isArray(result.keyPoints)).toBe(true);
      expect(result.comprehensionLevel).toBeGreaterThanOrEqual(1);
      expect(result.comprehensionLevel).toBeLessThanOrEqual(5);
    });
  });

  describe("GrammarResult", () => {
    it("should have correct structure", () => {
      const result: GrammarResult = {
        issues: [
          {
            issue: "Run-on sentence",
            type: "punctuation",
            suggestion: "Break into two sentences",
            position: { start: 0, end: 50 },
          },
        ],
        overallScore: 85,
        suggestions: ["Use shorter sentences for clarity"],
      };

      expect(Array.isArray(result.issues)).toBe(true);
      expect(result.overallScore).toBeGreaterThanOrEqual(0);
      expect(result.overallScore).toBeLessThanOrEqual(100);
      expect(Array.isArray(result.suggestions)).toBe(true);
    });
  });

  describe("VocabularyWord", () => {
    it("should have correct structure", () => {
      const word: VocabularyWord = {
        word: "ephemeral",
        definition: "lasting for a very short time",
        example: "The ephemeral beauty of cherry blossoms",
        difficulty: "advanced",
      };

      expect(word.word).toBeTypeOf("string");
      expect(word.definition).toBeTypeOf("string");
      expect(word.example).toBeTypeOf("string");
      expect(["basic", "intermediate", "advanced"]).toContain(word.difficulty);
    });
  });

  describe("VocabularyResult", () => {
    it("should have correct structure", () => {
      const result: VocabularyResult = {
        words: [
          {
            word: "climate",
            definition: "weather conditions",
            example: "The climate is changing",
            difficulty: "basic",
          },
        ],
        difficultyLevel: 3,
      };

      expect(Array.isArray(result.words)).toBe(true);
      expect(result.difficultyLevel).toBeGreaterThanOrEqual(1);
      expect(result.difficultyLevel).toBeLessThanOrEqual(5);
    });
  });

  describe("AnalyzeResponse", () => {
    it("should combine all results", () => {
      const response: AnalyzeResponse = {
        reading: {
          summary: "Test summary",
          keyPoints: ["Point 1"],
          comprehensionLevel: 3,
        },
        grammar: {
          issues: [],
          overallScore: 90,
          suggestions: [],
        },
        vocabulary: {
          words: [],
          difficultyLevel: 3,
        },
        sessionId: "550e8400-e29b-41d4-a716-446655440000", // Valid UUID format
      };

      expect(response.reading).toBeDefined();
      expect(response.grammar).toBeDefined();
      expect(response.vocabulary).toBeDefined();
      expect(response.sessionId).toBeTypeOf("string");
      expect(response.sessionId).toMatch(/^[a-f0-9-]+$/); // UUID format
    });
  });
});
