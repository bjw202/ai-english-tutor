import { useState, useEffect } from "react";
import { getLevelLabel } from "@/lib/constants";

const LEVEL_STORAGE_KEY = "tutor_level";

/**
 * Hook to manage comprehension level (1-5) with localStorage persistence
 * @returns Level config state and setters
 */
export function useLevelConfig() {
  const [level, setLevelState] = useState<number>(3); // Default level

  // Initialize from localStorage on client side only
  useEffect(() => {
    const stored = localStorage.getItem(LEVEL_STORAGE_KEY);
    if (stored) {
      const parsed = parseInt(stored, 10);
      if (parsed >= 1 && parsed <= 5) {
        setLevelState(parsed);
      }
    }
  }, []);

  // Update localStorage when level changes
  useEffect(() => {
    localStorage.setItem(LEVEL_STORAGE_KEY, String(level));
  }, [level]);

  const setLevel = (newLevel: number) => {
    if (newLevel >= 1 && newLevel <= 5) {
      setLevelState(newLevel);
    }
  };

  const levelLabel = getLevelLabel(level);

  return {
    level,
    setLevel,
    levelLabel,
  };
}
