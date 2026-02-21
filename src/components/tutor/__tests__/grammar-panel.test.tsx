import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { GrammarPanel } from "../grammar-panel";

describe("GrammarPanel", () => {
  const mockData = {
    issues: [
      {
        issue: "Subject-verb agreement",
        type: "grammar",
        suggestion: "He walks to school.",
      },
      {
        issue: "Tense consistency",
        type: "grammar",
        suggestion: "She went to the store yesterday.",
      },
    ],
    overallScore: 75,
    suggestions: ["Use consistent tense throughout your writing."],
  };

  it("should render grammar data correctly", () => {
    render(<GrammarPanel result={mockData} />);

    expect(screen.getByText("Grammar Analysis")).toBeInTheDocument();
    expect(screen.getByText("Overall Score")).toBeInTheDocument();
    expect(screen.getByText("75/100")).toBeInTheDocument();
  });

  it("should render all grammar issues", () => {
    render(<GrammarPanel result={mockData} />);

    expect(screen.getByText("Subject-verb agreement")).toBeInTheDocument();
    expect(screen.getByText("Tense consistency")).toBeInTheDocument();
    expect(screen.getByText("Issues Found")).toBeInTheDocument();
  });

  it("should render suggestions", () => {
    render(<GrammarPanel result={mockData} />);

    expect(
      screen.getByText("Use consistent tense throughout your writing."),
    ).toBeInTheDocument();
    expect(screen.getByText("Suggestions")).toBeInTheDocument();
  });

  it("should show placeholder when result is null", () => {
    render(<GrammarPanel result={null} />);

    expect(screen.getByText("No grammar analysis yet")).toBeInTheDocument();
  });
});
