import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { LevelSlider } from "../level-slider";

describe("LevelSlider", () => {
  it("should render slider with current level", () => {
    render(<LevelSlider level={3} onChange={vi.fn()} levelLabel="중급" />);

    expect(screen.getByText("Comprehension Level")).toBeInTheDocument();
    // Both the current level display and the scale label show "중급"
    const levelLabels = screen.getAllByText("중급");
    expect(levelLabels.length).toBeGreaterThanOrEqual(1);
  });

  it("should display correct level label", () => {
    const { rerender } = render(
      <LevelSlider level={1} onChange={vi.fn()} levelLabel="기초" />,
    );
    // "기초" appears both in the current level label and in the scale
    const all기초 = screen.getAllByText("기초");
    expect(all기초.length).toBe(2);

    rerender(<LevelSlider level={5} onChange={vi.fn()} levelLabel="심화" />);
    // "심화" appears both in the current level label and in the scale
    const all심화 = screen.getAllByText("심화");
    expect(all심화.length).toBe(2);
  });

  it("should render slider element", () => {
    render(<LevelSlider level={3} onChange={vi.fn()} levelLabel="중급" />);

    const slider = screen.getByRole("slider");
    expect(slider).toBeInTheDocument();
    expect(slider).toHaveAttribute("aria-valuemin", "1");
    expect(slider).toHaveAttribute("aria-valuemax", "5");
    expect(slider).toHaveAttribute("aria-valuenow", "3");
  });

  it("should display all level labels in the scale", () => {
    render(<LevelSlider level={3} onChange={vi.fn()} levelLabel="중급" />);

    // The scale labels at the bottom
    const scaleContainer = screen.getByText("기초").parentElement;
    expect(scaleContainer).toHaveTextContent("기초");
    expect(scaleContainer).toHaveTextContent("초급");
    expect(scaleContainer).toHaveTextContent("중급");
    expect(scaleContainer).toHaveTextContent("고급");
    expect(scaleContainer).toHaveTextContent("심화");
  });
});
