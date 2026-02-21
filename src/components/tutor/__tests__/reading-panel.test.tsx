import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ReadingPanel } from "../reading-panel";

describe("ReadingPanel", () => {
  const mockData = {
    summary: "This is a summary of the text.",
    keyPoints: ["Point 1", "Point 2", "Point 3"],
    comprehensionLevel: 3,
  };

  it("should render reading data correctly", () => {
    render(<ReadingPanel result={mockData} />);

    expect(screen.getByText("Reading Comprehension")).toBeInTheDocument();
    expect(screen.getByText("Summary")).toBeInTheDocument();
    expect(screen.getByText("This is a summary of the text.")).toBeInTheDocument();
    expect(screen.getByText("Key Points")).toBeInTheDocument();
  });

  it("should render all key points", () => {
    render(<ReadingPanel result={mockData} />);

    expect(screen.getByText("Point 1")).toBeInTheDocument();
    expect(screen.getByText("Point 2")).toBeInTheDocument();
    expect(screen.getByText("Point 3")).toBeInTheDocument();
  });

  it("should display comprehension level", () => {
    render(<ReadingPanel result={mockData} />);

    expect(screen.getByText("Level:")).toBeInTheDocument();
    expect(screen.getByText("3/5")).toBeInTheDocument();
  });

  it("should show placeholder when result is null", () => {
    render(<ReadingPanel result={null} />);

    expect(screen.getByText("No reading analysis yet")).toBeInTheDocument();
  });
});
