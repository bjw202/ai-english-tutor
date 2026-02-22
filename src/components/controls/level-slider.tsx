import React from "react";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { cn } from "@/lib/utils";

interface LevelSliderProps {
  level: number;
  onChange: (level: number) => void;
  levelLabel: string;
  className?: string;
  variant?: "default" | "compact";
}

/**
 * Level slider component
 * Allows users to select comprehension level (1-5)
 *
 * Variants:
 * - default: Full-width layout with step labels (기초/초급/중급/고급/심화)
 * - compact: Single-line inline layout showing only current level number
 */
export function LevelSlider({
  level,
  onChange,
  levelLabel,
  className,
  variant = "default",
}: LevelSliderProps) {
  const handleLevelChange = (value: number[]) => {
    onChange(value[0]);
  };

  if (variant === "compact") {
    return (
      <div className={cn("flex items-center gap-3", className)}>
        <Label htmlFor="level-slider" className="text-sm font-medium whitespace-nowrap">
          Lv.{level}
        </Label>
        <Slider
          id="level-slider"
          min={1}
          max={5}
          step={1}
          value={[level]}
          onValueChange={handleLevelChange}
          className="flex-1"
        />
      </div>
    );
  }

  // default variant - full layout with step labels
  return (
    <div className={cn("space-y-2", className)}>
      <div className="flex justify-between items-center">
        <Label htmlFor="level-slider" className="text-sm font-medium">
          Comprehension Level
        </Label>
        <span className="text-sm text-muted-foreground">{levelLabel}</span>
      </div>

      <Slider
        id="level-slider"
        min={1}
        max={5}
        step={1}
        value={[level]}
        onValueChange={handleLevelChange}
        className="w-full"
      />

      <div className="flex justify-between text-xs text-muted-foreground">
        <span>기초</span>
        <span>초급</span>
        <span>중급</span>
        <span>고급</span>
        <span>심화</span>
      </div>
    </div>
  );
}
