import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TabbedOutput } from "../tabbed-output";

describe("TabbedOutput", () => {
  const mockReading = {
    summary: "Test summary",
    keyPoints: ["Point 1"],
    comprehensionLevel: 3,
  };

  const mockGrammar = {
    issues: [],
    overallScore: 85,
    suggestions: ["Good job!"],
  };

  const mockVocabulary = {
    words: [],
    difficultyLevel: 3,
  };

  it("should render tabs correctly", () => {
    render(
      <TabbedOutput
        reading={mockReading}
        grammar={mockGrammar}
        vocabulary={mockVocabulary}
      />,
    );

    expect(screen.getByRole("tab", { name: "Reading" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Grammar" })).toBeInTheDocument();
    expect(
      screen.getByRole("tab", { name: "Vocabulary" }),
    ).toBeInTheDocument();
  });

  it("should show reading panel by default", () => {
    render(
      <TabbedOutput
        reading={mockReading}
        grammar={mockGrammar}
        vocabulary={mockVocabulary}
      />,
    );

    expect(screen.getByText("Test summary")).toBeInTheDocument();
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

    const grammarTab = screen.getByRole("tab", { name: "Grammar" });
    await user.click(grammarTab);

    expect(screen.getByText("Good job!")).toBeInTheDocument();
  });

  it("should switch to vocabulary tab when clicked", async () => {
    const user = userEvent.setup();

    const mockVocabWithData = {
      words: [
        {
          word: "test",
          definition: "A test",
          example: "Test example",
          difficulty: "basic" as const,
        },
      ],
      difficultyLevel: 1,
    };

    render(
      <TabbedOutput
        reading={mockReading}
        grammar={mockGrammar}
        vocabulary={mockVocabWithData}
      />,
    );

    const vocabTab = screen.getByRole("tab", { name: "Vocabulary" });
    await user.click(vocabTab);

    expect(screen.getByText("test")).toBeInTheDocument();
  });

  it("should show message when all data is null", () => {
    render(
      <TabbedOutput
        reading={null}
        grammar={null}
        vocabulary={null}
      />,
    );

    // When all data is null, tabs are not rendered, only the message
    expect(screen.queryByRole("tab", { name: "Reading" })).not.toBeInTheDocument();
    expect(
      screen.getByText("Submit text or upload an image to see analysis results"),
    ).toBeInTheDocument();
  });
});
