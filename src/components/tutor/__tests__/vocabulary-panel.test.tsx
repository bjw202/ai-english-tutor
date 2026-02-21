import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { VocabularyPanel } from "../vocabulary-panel";

describe("VocabularyPanel", () => {
  const mockData = {
    words: [
      {
        word: "ephemeral",
        definition: "Lasting for a very short time.",
        example: "The ephemeral beauty of cherry blossoms.",
        difficulty: "advanced" as const,
      },
      {
        word: "abundant",
        definition: "Existing in large quantities; plentiful.",
        example: "The forest has abundant wildlife.",
        difficulty: "intermediate" as const,
      },
      {
        word: "happy",
        definition: "Feeling pleasure.",
        example: "I am happy today.",
        difficulty: "basic" as const,
      },
    ],
    difficultyLevel: 3,
  };

  it("should render vocabulary data correctly", () => {
    render(<VocabularyPanel result={mockData} />);

    expect(screen.getByText("Vocabulary Analysis")).toBeInTheDocument();
    expect(screen.getByText("ephemeral")).toBeInTheDocument();
    expect(screen.getByText("abundant")).toBeInTheDocument();
    expect(screen.getByText("happy")).toBeInTheDocument();
  });

  it("should render definitions and examples", () => {
    render(<VocabularyPanel result={mockData} />);

    expect(
      screen.getByText("Lasting for a very short time."),
    ).toBeInTheDocument();
    // The example is wrapped in quotes in the component
    expect(
      screen.getByText(/The ephemeral beauty of cherry blossoms/),
    ).toBeInTheDocument();
  });

  it("should display difficulty badges", () => {
    render(<VocabularyPanel result={mockData} />);

    expect(screen.getByText("advanced")).toBeInTheDocument();
    expect(screen.getByText("intermediate")).toBeInTheDocument();
    expect(screen.getByText("basic")).toBeInTheDocument();
  });

  it("should show placeholder when result is null", () => {
    render(<VocabularyPanel result={null} />);

    expect(screen.getByText("No vocabulary analysis yet")).toBeInTheDocument();
  });
});
