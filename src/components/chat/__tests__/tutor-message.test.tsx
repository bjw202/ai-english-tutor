import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { TutorMessage } from "../tutor-message";

describe("TutorMessage", () => {
  it("should render message content", () => {
    render(<TutorMessage content="Test response" timestamp={new Date()} />);

    expect(screen.getByText("Test response")).toBeInTheDocument();
  });

  it("should have left-aligned styling", () => {
    const { container } = render(
      <TutorMessage content="Test" timestamp={new Date()} />
    );

    const messageBubble = container.querySelector(".bg-muted");
    expect(messageBubble).toBeInTheDocument();
  });

  it("should show streaming indicator when isStreaming is true", () => {
    render(
      <TutorMessage
        content="Test"
        timestamp={new Date()}
        isStreaming={true}
      />
    );

    // Should have some streaming indicator (cursor or dots)
    const streamingIndicator = screen.queryByText(/\.\.\./);
    expect(streamingIndicator).toBeInTheDocument();
  });

  it("should not show streaming indicator when isStreaming is false", () => {
    render(
      <TutorMessage
        content="Test"
        timestamp={new Date()}
        isStreaming={false}
      />
    );

    const streamingIndicator = screen.queryByText(/\.\.\./);
    expect(streamingIndicator).not.toBeInTheDocument();
  });

  it("should display timestamp", () => {
    const date = new Date("2024-01-01T10:30:00Z");
    render(<TutorMessage content="Test" timestamp={date} />);

    const timeElement = screen.queryByText(/\d{1,2}:\d{2}/);
    expect(timeElement).toBeInTheDocument();
  });
});
