import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ChatContainer } from "../chat-container";

describe("ChatContainer", () => {
  it("should render children components", () => {
    render(
      <ChatContainer>
        <div data-testid="test-child">Test Content</div>
      </ChatContainer>
    );

    expect(screen.getByTestId("test-child")).toBeInTheDocument();
    expect(screen.getByText("Test Content")).toBeInTheDocument();
  });

  it("should have correct container classes", () => {
    const { container } = render(
      <ChatContainer>
        <div>Content</div>
      </ChatContainer>
    );

    const chatContainer = container.firstChild as HTMLElement;
    expect(chatContainer).toHaveClass("flex");
    expect(chatContainer).toHaveClass("flex-col");
  });
});
