import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Header } from "../header";

describe("Header", () => {
  it("should render logo and title", () => {
    render(<Header />);

    expect(screen.getByText("AI English Tutor")).toBeInTheDocument();
  });

  it("should have correct class names", () => {
    const { container } = render(<Header />);
    const header = container.querySelector("header");
    expect(header).toHaveClass("border-b");
  });
});
