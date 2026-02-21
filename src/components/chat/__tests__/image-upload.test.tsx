import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ImageUpload } from "../image-upload";

describe("ImageUpload", () => {
  const mockOnFileSelect = vi.fn();

  beforeEach(() => {
    mockOnFileSelect.mockClear();
  });

  it("should render file input button", () => {
    render(<ImageUpload onFileSelect={mockOnFileSelect} />);

    const button = screen.getByRole("button", { name: /select image/i });
    expect(button).toBeInTheDocument();
  });

  it("should call onFileSelect when valid file is selected", async () => {
    const file = new File(["test"], "test.jpg", { type: "image/jpeg" });
    const user = userEvent.setup();

    render(<ImageUpload onFileSelect={mockOnFileSelect} />);

    const input = screen.getByTestId("file-input") as HTMLInputElement;
    await user.upload(input, file);

    expect(mockOnFileSelect).toHaveBeenCalledWith(file);
  });

  it("should reject files larger than 10MB", async () => {
    // Create a mock file that's larger than 10MB
    const largeFile = new File(["x"], "large.jpg", { type: "image/jpeg" });
    Object.defineProperty(largeFile, "size", { value: 11 * 1024 * 1024 });

    const user = userEvent.setup();

    render(<ImageUpload onFileSelect={mockOnFileSelect} />);

    const input = screen.getByTestId("file-input") as HTMLInputElement;
    await user.upload(input, largeFile);

    // Verify the file was rejected (onFileSelect not called)
    expect(mockOnFileSelect).not.toHaveBeenCalled();
  });
});
