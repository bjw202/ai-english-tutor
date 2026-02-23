import React from "react";
import ReactMarkdown from "react-markdown";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ReadingResult } from "@/types/tutor";

interface ReadingPanelProps {
  result: ReadingResult | null;
  className?: string;
  isStreaming?: boolean;
}

/**
 * Reading training panel
 * Displays Korean Markdown content for reading comprehension training
 */
export function ReadingPanel({ result, className, isStreaming = false }: ReadingPanelProps) {
  if (!result && !isStreaming) {
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
        <CardTitle className="text-lg">독해 훈련</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="prose prose-sm dark:prose-invert max-w-none">
          <ReactMarkdown>{result?.content || ""}</ReactMarkdown>
          {isStreaming && (
            <span className="inline-block w-2 h-4 bg-primary animate-pulse ml-0.5" />
          )}
        </div>
      </CardContent>
    </Card>
  );
}
