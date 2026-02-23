import React from "react";
import ReactMarkdown from "react-markdown";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { GrammarResult } from "@/types/tutor";

interface GrammarPanelProps {
  result: GrammarResult | null;
  className?: string;
  isStreaming?: boolean;
}

/**
 * Grammar structure understanding panel
 * Displays Korean Markdown content for grammar analysis
 */
export function GrammarPanel({ result, className, isStreaming = false }: GrammarPanelProps) {
  if (!result && !isStreaming) {
    return (
      <Card className={className}>
        <CardContent className="p-6 text-center text-muted-foreground">
          No grammar analysis yet
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="text-lg">문법 구조 이해</CardTitle>
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
