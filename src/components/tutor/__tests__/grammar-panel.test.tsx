import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { GrammarPanel } from "../grammar-panel";

describe("GrammarPanel", () => {
  const mockData = {
    content: "주어-동사 일치에 주의하세요.",
  };

  it("should render grammar data correctly", () => {
    render(<GrammarPanel result={mockData} />);

    expect(screen.getByText("문법 구조 이해")).toBeInTheDocument();
    expect(screen.getByText(/주어-동사 일치/)).toBeInTheDocument();
  });

  it("should show placeholder when result is null", () => {
    render(<GrammarPanel result={null} />);

    expect(screen.getByText("No grammar analysis yet")).toBeInTheDocument();
  });
});
