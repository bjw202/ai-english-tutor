import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ChatInput } from "../chat-input";

describe("ChatInput", () => {
  it("should render textarea input", () => {
    render(<ChatInput onSend={vi.fn()} disabled={false} />);

    const textarea = screen.getByRole("textbox");
    expect(textarea).toBeInTheDocument();
  });

  it("should call onSend with message when send button clicked", async () => {
    const onSend = vi.fn();
    const user = userEvent.setup();

    render(<ChatInput onSend={onSend} disabled={false} />);

    const textarea = screen.getByRole("textbox");
    await user.type(textarea, "Test message");

    const sendButton = screen.getByRole("button");
    await user.click(sendButton);

    expect(onSend).toHaveBeenCalledWith("Test message");
  });

  it("should call onSend when Enter key is pressed (without Shift)", async () => {
    const onSend = vi.fn();
    const user = userEvent.setup();

    render(<ChatInput onSend={onSend} disabled={false} />);

    const textarea = screen.getByRole("textbox");
    await user.type(textarea, "Test message{Enter}");

    expect(onSend).toHaveBeenCalledWith("Test message");
  });

  it("should not call onSend when Shift+Enter is pressed", async () => {
    const onSend = vi.fn();
    const user = userEvent.setup();

    render(<ChatInput onSend={onSend} disabled={false} />);

    const textarea = screen.getByRole("textbox");
    await user.type(textarea, "Line 1{Shift>}{Enter}{/Shift}Line 2");

    // Should still have content, not sent
    expect(onSend).not.toHaveBeenCalled();
    expect(textarea).toHaveValue("Line 1\nLine 2");
  });

  it("should be disabled when disabled prop is true", () => {
    render(<ChatInput onSend={vi.fn()} disabled={true} />);

    const textarea = screen.getByRole("textbox");
    expect(textarea).toBeDisabled();
  });

  it("should clear input after sending", async () => {
    const onSend = vi.fn();
    const user = userEvent.setup();

    render(<ChatInput onSend={onSend} disabled={false} />);

    const textarea = screen.getByRole("textbox") as HTMLTextAreaElement;
    await user.type(textarea, "Test message");

    const sendButton = screen.getByRole("button");
    await user.click(sendButton);

    expect(textarea.value).toBe("");
  });

  it("should not send empty messages", async () => {
    const onSend = vi.fn();
    const user = userEvent.setup();

    render(<ChatInput onSend={onSend} disabled={false} />);

    const sendButton = screen.getByRole("button");
    await user.click(sendButton);

    expect(onSend).not.toHaveBeenCalled();
  });
});
