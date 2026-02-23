import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ReadingPanel } from "../reading-panel";

describe("ReadingPanel", () => {
  const mockData = {
    content: "This is the reading training content.",
  };

  it("should render reading data correctly", () => {
    render(<ReadingPanel result={mockData} />);

    expect(screen.getByText("독해 훈련")).toBeInTheDocument();
    expect(screen.getByText(/reading training content/)).toBeInTheDocument();
  });

  it("should show placeholder when result is null", () => {
    render(<ReadingPanel result={null} />);

    expect(screen.getByText("No reading analysis yet")).toBeInTheDocument();
  });
});
