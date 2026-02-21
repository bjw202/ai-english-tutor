import { describe, it, expect, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useSession } from "../use-session";

describe("useSession", () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
  });

  it("should generate a new session ID on first use", () => {
    const { result } = renderHook(() => useSession());

    expect(result.current.sessionId).toBeTruthy();
    expect(typeof result.current.sessionId).toBe("string");
    expect(result.current.sessionId.length).toBeGreaterThan(20);
  });

  it("should persist session ID to localStorage", () => {
    const { result } = renderHook(() => useSession());

    const storedValue = localStorage.getItem("tutor_session_id");
    expect(storedValue).toBe(result.current.sessionId);
  });

  it("should restore existing session ID from localStorage", () => {
    const existingId = "existing-session-id-12345";
    localStorage.setItem("tutor_session_id", existingId);

    const { result } = renderHook(() => useSession());

    expect(result.current.sessionId).toBe(existingId);
  });

  it("should reset session and generate new ID", () => {
    const { result } = renderHook(() => useSession());
    const originalId = result.current.sessionId;

    act(() => {
      result.current.resetSession();
    });

    expect(result.current.sessionId).not.toBe(originalId);
    expect(localStorage.getItem("tutor_session_id")).toBe(result.current.sessionId);
  });
});
