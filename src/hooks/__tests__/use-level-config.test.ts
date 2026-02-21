import { describe, it, expect, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useLevelConfig } from "../use-level-config";

describe("useLevelConfig", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("should have default level of 3", () => {
    const { result } = renderHook(() => useLevelConfig());

    expect(result.current.level).toBe(3);
  });

  it("should display correct label for level 3", () => {
    const { result } = renderHook(() => useLevelConfig());

    expect(result.current.levelLabel).toBe("중급");
  });

  it("should update level when setLevel is called", () => {
    const { result } = renderHook(() => useLevelConfig());

    act(() => {
      result.current.setLevel(5);
    });

    expect(result.current.level).toBe(5);
    expect(result.current.levelLabel).toBe("심화");
  });

  it("should persist level to localStorage", () => {
    const { result } = renderHook(() => useLevelConfig());

    act(() => {
      result.current.setLevel(1);
    });

    expect(localStorage.getItem("tutor_level")).toBe("1");
  });

  it("should restore level from localStorage on mount", () => {
    localStorage.setItem("tutor_level", "4");

    const { result } = renderHook(() => useLevelConfig());

    expect(result.current.level).toBe(4);
    expect(result.current.levelLabel).toBe("고급");
  });

  it("should validate level is between 1 and 5", () => {
    const { result } = renderHook(() => useLevelConfig());

    act(() => {
      result.current.setLevel(1);
    });
    expect(result.current.level).toBe(1);

    act(() => {
      result.current.setLevel(5);
    });
    expect(result.current.level).toBe(5);
  });

  it("should have correct labels for all levels", () => {
    const { result: r1 } = renderHook(() => useLevelConfig());
    act(() => r1.current.setLevel(1));
    expect(r1.current.levelLabel).toBe("기초");

    const { result: r2 } = renderHook(() => useLevelConfig());
    act(() => r2.current.setLevel(2));
    expect(r2.current.levelLabel).toBe("초급");

    const { result: r3 } = renderHook(() => useLevelConfig());
    act(() => r3.current.setLevel(3));
    expect(r3.current.levelLabel).toBe("중급");

    const { result: r4 } = renderHook(() => useLevelConfig());
    act(() => r4.current.setLevel(4));
    expect(r4.current.levelLabel).toBe("고급");

    const { result: r5 } = renderHook(() => useLevelConfig());
    act(() => r5.current.setLevel(5));
    expect(r5.current.levelLabel).toBe("심화");
  });
});
