import { describe, it, expect } from "vitest";
import { API_ENDPOINTS, LEVEL_DEFINITIONS, DEFAULT_SETTINGS } from "../constants";

describe("Constants", () => {
  describe("API_ENDPOINTS", () => {
    it("should have all required endpoints", () => {
      expect(API_ENDPOINTS.analyze).toBe("/api/tutor/analyze");
      expect(API_ENDPOINTS.analyzeImage).toBe("/api/tutor/analyze-image");
      expect(API_ENDPOINTS.chat).toBe("/api/tutor/chat");
    });

    it("should have consistent base path", () => {
      const basePath = "/api/tutor";
      expect(API_ENDPOINTS.analyze).toContain(basePath);
      expect(API_ENDPOINTS.analyzeImage).toContain(basePath);
      expect(API_ENDPOINTS.chat).toContain(basePath);
    });
  });

  describe("LEVEL_DEFINITIONS", () => {
    it("should have exactly 5 levels", () => {
      expect(LEVEL_DEFINITIONS).toHaveLength(5);
    });

    it("should have levels 1 through 5", () => {
      LEVEL_DEFINITIONS.forEach((level, index) => {
        expect(level.level).toBe(index + 1);
      });
    });

    it("should have valid Korean labels", () => {
      const labels = LEVEL_DEFINITIONS.map((l) => l.label);
      expect(labels).toContain("기초");
      expect(labels).toContain("초급");
      expect(labels).toContain("중급");
      expect(labels).toContain("고급");
      expect(labels).toContain("심화");
    });

    it("should have descriptions for each level", () => {
      LEVEL_DEFINITIONS.forEach((level) => {
        expect(level.label).toBeTruthy();
        expect(level.description).toBeTruthy();
        expect(level.description.length).toBeGreaterThan(10);
      });
    });
  });

  describe("DEFAULT_SETTINGS", () => {
    it("should have default level of 3", () => {
      expect(DEFAULT_SETTINGS.level).toBe(3);
    });

    it("should have max file size of 10MB", () => {
      expect(DEFAULT_SETTINGS.maxFileSize).toBe(10 * 1024 * 1024);
    });

    it("should have valid level range", () => {
      expect(DEFAULT_SETTINGS.level).toBeGreaterThanOrEqual(1);
      expect(DEFAULT_SETTINGS.level).toBeLessThanOrEqual(5);
    });
  });

  describe("getLevelLabel helper", () => {
    it("should return correct Korean label for each level", () => {
      // This will be implemented with the constants
      const level1 = LEVEL_DEFINITIONS.find((l) => l.level === 1);
      const level3 = LEVEL_DEFINITIONS.find((l) => l.level === 3);
      const level5 = LEVEL_DEFINITIONS.find((l) => l.level === 5);

      expect(level1?.label).toBe("기초");
      expect(level3?.label).toBe("중급");
      expect(level5?.label).toBe("심화");
    });
  });
});
