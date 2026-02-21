import { describe, it, expect } from "vitest";
import { cn, formatTimestamp, generateId } from "../utils";

describe("Utils", () => {
  describe("cn", () => {
    it("should merge class names correctly", () => {
      expect(cn("px-4", "py-2")).toBe("px-4 py-2");
    });

    it("should handle conditional classes", () => {
      expect(cn("base", true && "active", false && "inactive")).toBe("base active");
    });

    it("should handle undefined and null", () => {
      expect(cn("base", undefined, null, "extra")).toBe("base extra");
    });

    it("should deduplicate tailwind classes", () => {
      expect(cn("px-4 px-2")).toBe("px-2");
    });
  });

  describe("formatTimestamp", () => {
    it("should format a date object to readable string", () => {
      const date = new Date("2024-01-15T10:30:00Z");
      const result = formatTimestamp(date);
      expect(result).toBeTruthy();
      expect(typeof result).toBe("string");
    });

    it("should handle different date formats", () => {
      const date1 = new Date("2024-12-25T23:59:59Z");
      const result1 = formatTimestamp(date1);
      expect(result1).toBeTruthy();
    });
  });

  describe("generateId", () => {
    it("should generate a unique ID string", () => {
      const id1 = generateId();
      const id2 = generateId();

      expect(typeof id1).toBe("string");
      expect(typeof id2).toBe("string");
      expect(id1).not.toBe(id2);
    });

    it("should generate IDs with sufficient length", () => {
      const id = generateId();
      expect(id.length).toBeGreaterThan(20);
    });
  });
});
