import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TabbedOutput } from "../tabbed-output";

describe("TabbedOutput", () => {
  const mockReading = {
    content: "Test reading content.",
  };

  const mockGrammar = {
    content: "Grammar analysis here.",
  };

  const mockVocabulary = {
    words: [
      {
        word: "test",
        content: "테스트 어원 설명.",
      },
    ],
  };

  it("should render Korean tab labels correctly", () => {
    render(
      <TabbedOutput
        reading={mockReading}
        grammar={mockGrammar}
        vocabulary={mockVocabulary}
      />,
    );

    expect(screen.getByRole("tab", { name: "독해" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "문법" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "어휘" })).toBeInTheDocument();
  });

  it("should show reading panel by default", () => {
    render(
      <TabbedOutput
        reading={mockReading}
        grammar={mockGrammar}
        vocabulary={mockVocabulary}
      />,
    );

    expect(screen.getByText("독해 훈련")).toBeInTheDocument();
  });

  it("should switch to grammar tab when clicked", async () => {
    const user = userEvent.setup();

    render(
      <TabbedOutput
        reading={mockReading}
        grammar={mockGrammar}
        vocabulary={mockVocabulary}
      />,
    );

    const grammarTab = screen.getByRole("tab", { name: "문법" });
    await user.click(grammarTab);

    expect(screen.getByText("문법 구조 이해")).toBeInTheDocument();
  });

  it("should switch to vocabulary tab when clicked", async () => {
    const user = userEvent.setup();

    render(
      <TabbedOutput
        reading={mockReading}
        grammar={mockGrammar}
        vocabulary={mockVocabulary}
      />,
    );

    const vocabTab = screen.getByRole("tab", { name: "어휘" });
    await user.click(vocabTab);

    expect(screen.getByText("어휘 어원 학습")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "test" })).toBeInTheDocument();
  });

  it("should show Korean message when all data is null", () => {
    render(
      <TabbedOutput
        reading={null}
        grammar={null}
        vocabulary={null}
      />,
    );

    expect(screen.queryByRole("tab", { name: "독해" })).not.toBeInTheDocument();
    expect(
      screen.getByText("텍스트를 입력하거나 이미지를 업로드하면 분석 결과가 여기에 표시됩니다"),
    ).toBeInTheDocument();
  });
});
