import React from "react";
import ReactMarkdown from "react-markdown";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import type { GrammarResult } from "@/types/tutor";

interface GrammarPanelProps {
  result: GrammarResult | null;
  className?: string;
}

/**
 * Grammar analysis panel
 * Displays issues, overall score, and suggestions
 */
export function GrammarPanel({ result, className }: GrammarPanelProps) {
  if (!result) {
    return (
      <Card className={className}>
        <CardContent className="p-6 text-center text-muted-foreground">
          No grammar analysis yet
        </CardContent>
      </Card>
    );
  }

  // Score-based styling (for future use)
  void result.overallScore;

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="text-lg">Grammar Analysis</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium">Overall Score</span>
            <span className="text-sm font-bold">{result.overallScore}/100</span>
          </div>
          <Progress value={result.overallScore} className="h-2" />
        </div>

        {result.issues.length > 0 && (
          <div>
            <h4 className="font-medium mb-2">Issues Found</h4>
            <div className="space-y-2">
              {result.issues.map((issue, index) => (
                <div
                  key={index}
                  className="p-3 bg-muted rounded-lg text-sm space-y-1"
                >
                  <div className="flex justify-between">
                    <span className="font-medium">{issue.issue}</span>
                    <span className="text-xs text-muted-foreground">
                      {issue.type}
                    </span>
                  </div>
                  <p className="text-muted-foreground">{issue.suggestion}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {result.suggestions.length > 0 && (
          <div>
            <h4 className="font-medium mb-2">Analysis</h4>
            <div className="prose prose-sm dark:prose-invert max-w-none">
              {result.suggestions.map((suggestion, index) => (
                <ReactMarkdown key={index}>{suggestion}</ReactMarkdown>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
