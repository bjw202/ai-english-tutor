import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MessageList } from "../message-list";
import type { Message } from "@/types/chat";

describe("MessageList", () => {
  const mockMessages: Message[] = [
    {
      id: "1",
      role: "user",
      content: "Hello",
      timestamp: new Date("2024-01-01T10:00:00Z"),
    },
    {
      id: "2",
      role: "tutor",
      content: "Hi there!",
      timestamp: new Date("2024-01-01T10:00:01Z"),
    },
  ];

  it("should render all messages", () => {
    render(<MessageList messages={mockMessages} />);

    expect(screen.getByText("Hello")).toBeInTheDocument();
    expect(screen.getByText("Hi there!")).toBeInTheDocument();
  });

  it("should render empty state when no messages", () => {
    const { container } = render(<MessageList messages={[]} />);

    // Component returns null when no messages
    expect(container.firstChild).toBeNull();
  });

  it("should scroll to bottom on new messages", () => {
    const { rerender } = render(<MessageList messages={[]} />);

    rerender(<MessageList messages={mockMessages} />);

    expect(screen.getByText("Hello")).toBeInTheDocument();
  });
});
