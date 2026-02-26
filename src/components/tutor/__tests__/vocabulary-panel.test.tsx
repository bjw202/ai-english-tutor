import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { VocabularyPanel } from "../vocabulary-panel";

describe("VocabularyPanel", () => {
  const mockData = {
    words: [
      {
        word: "ephemeral",
        content: "**어원:** 그리스어 *ephemeros*에서 유래.",
      },
      {
        word: "abundant",
        content: "**어원:** 라틴어 *abundans*에서 유래.",
      },
    ],
  };

  it("should render vocabulary data correctly", () => {
    render(<VocabularyPanel result={mockData} />);

    expect(screen.getByText("어휘 어원 학습")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "ephemeral" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "abundant" })).toBeInTheDocument();
  });

  it("should render etymology content for each word", () => {
    render(<VocabularyPanel result={mockData} />);

    expect(screen.getByText(/ephemeros/)).toBeInTheDocument();
    expect(screen.getByText(/abundans/)).toBeInTheDocument();
  });

  it("should show Korean empty state when result is null", () => {
    render(<VocabularyPanel result={null} />);

    expect(screen.getByText("아직 어휘 분석이 없습니다")).toBeInTheDocument();
  });

  it("should show Korean empty state when words array is empty", () => {
    render(<VocabularyPanel result={{ words: [] }} />);

    expect(screen.getByText("아직 어휘 분석이 없습니다")).toBeInTheDocument();
  });

  it("should display error message when error prop is provided", () => {
    render(<VocabularyPanel result={null} error="LLM API failed" />);

    expect(screen.getByText(/오류가 발생했습니다/)).toBeInTheDocument();
    expect(screen.getByText(/LLM API failed/)).toBeInTheDocument();
  });

  it("should show error state instead of empty state when error is provided", () => {
    render(<VocabularyPanel result={null} error="Some error" />);

    expect(screen.queryByText("아직 어휘 분석이 없습니다")).not.toBeInTheDocument();
  });
});
