import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ReadingResult } from "@/types/tutor";

interface ReadingPanelProps {
  result: ReadingResult | null;
  className?: string;
}

/**
 * Reading comprehension panel
 * Displays summary, key points, and comprehension level
 */
export function ReadingPanel({ result, className }: ReadingPanelProps) {
  if (!result) {
    return (
      <Card className={className}>
        <CardContent className="p-6 text-center text-muted-foreground">
          No reading analysis yet
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="text-lg">Reading Comprehension</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <h4 className="font-medium mb-2">Summary</h4>
          <p className="text-sm text-muted-foreground">{result.summary}</p>
        </div>

        <div>
          <h4 className="font-medium mb-2">Key Points</h4>
          <ul className="list-disc list-inside space-y-1">
            {result.keyPoints.map((point, index) => (
              <li key={index} className="text-sm text-muted-foreground">
                {point}
              </li>
            ))}
          </ul>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">Level:</span>
          <span className="text-sm text-muted-foreground">
            {result.comprehensionLevel}/5
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
