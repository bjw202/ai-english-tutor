import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { UserMessage } from "../user-message";

describe("UserMessage", () => {
  it("should render message content", () => {
    render(<UserMessage content="Test message" timestamp={new Date()} />);

    expect(screen.getByText("Test message")).toBeInTheDocument();
  });

  it("should have right-aligned styling", () => {
    const { container } = render(
      <UserMessage content="Test" timestamp={new Date()} />
    );

    const messageBubble = container.querySelector(".bg-primary");
    expect(messageBubble).toBeInTheDocument();
  });

  it("should display timestamp", () => {
    const date = new Date("2024-01-01T10:30:00Z");
    render(<UserMessage content="Test" timestamp={date} />);

    // Timestamp should be rendered
    const timeElement = screen.queryByText(/\d{1,2}:\d{2}/);
    expect(timeElement).toBeInTheDocument();
  });
});
