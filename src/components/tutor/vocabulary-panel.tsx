import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { VocabularyResult } from "@/types/tutor";

interface VocabularyPanelProps {
  result: VocabularyResult | null;
  className?: string;
}

/**
 * Vocabulary analysis panel
 * Displays vocabulary words with definitions and difficulty level
 */
export function VocabularyPanel({ result, className }: VocabularyPanelProps) {
  if (!result) {
    return (
      <Card className={className}>
        <CardContent className="p-6 text-center text-muted-foreground">
          No vocabulary analysis yet
        </CardContent>
      </Card>
    );
  }

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case "basic":
        return "bg-green-500";
      case "intermediate":
        return "bg-yellow-500";
      case "advanced":
        return "bg-red-500";
      default:
        return "bg-gray-500";
    }
  };

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="text-lg">Vocabulary Analysis</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">Difficulty Level:</span>
          <span className="text-sm text-muted-foreground">
            {result.difficultyLevel}/5
          </span>
        </div>

        {result.words.length > 0 && (
          <div className="space-y-3">
            {result.words.map((word, index) => (
              <div
                key={index}
                className="p-3 bg-muted rounded-lg text-sm space-y-2"
              >
                <div className="flex justify-between items-start">
                  <span className="font-semibold text-base">{word.word}</span>
                  <Badge className={getDifficultyColor(word.difficulty)}>
                    {word.difficulty}
                  </Badge>
                </div>
                <p className="text-muted-foreground">{word.definition}</p>
                {word.example && (
                  <p className="text-xs italic text-muted-foreground">
                    &quot;{word.example}&quot;
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
