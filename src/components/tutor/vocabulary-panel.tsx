import React from "react";
import ReactMarkdown from "react-markdown";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { VocabularyResult } from "@/types/tutor";

interface VocabularyPanelProps {
  result: VocabularyResult | null;
  className?: string;
  isStreaming?: boolean;
  error?: string | null;
  rawContent?: string;
}

/**
 * Vocabulary etymology learning panel
 * Displays list of words with Korean Markdown etymology explanations.
 * While streaming, shows raw Markdown tokens as they arrive (when available),
 * replacing the skeleton loader with live text. Once vocabulary_chunk arrives,
 * switches to the structured per-word display.
 */
export function VocabularyPanel({
  result,
  className,
  isStreaming = false,
  error,
  rawContent = "",
}: VocabularyPanelProps) {
  if (error) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="rounded-lg bg-destructive/10 p-4 text-sm text-destructive">
            어휘 분석 중 오류가 발생했습니다: {error}
          </div>
        </CardContent>
      </Card>
    );
  }

  if ((!result || !result.words || result.words.length === 0) && !isStreaming) {
    if (rawContent) {
      return (
        <Card className={className}>
          <CardHeader>
            <CardTitle className="text-lg">어휘 어원 학습</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown>{rawContent}</ReactMarkdown>
            </div>
          </CardContent>
        </Card>
      );
    }
    return (
      <Card className={className}>
        <CardContent className="p-6 text-center text-muted-foreground">
          아직 어휘 분석이 없습니다
        </CardContent>
      </Card>
    );
  }

  if (isStreaming && (!result || !result.words || result.words.length === 0)) {
    // Show live raw Markdown tokens if available, otherwise show skeleton
    if (rawContent) {
      return (
        <Card className={className}>
          <CardHeader>
            <CardTitle className="text-lg">어휘 어원 학습</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown>{rawContent}</ReactMarkdown>
            </div>
          </CardContent>
        </Card>
      );
    }
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="text-lg">어휘 어원 학습</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse space-y-2">
              <div className="h-4 bg-muted rounded w-1/4" />
              <div className="h-3 bg-muted rounded w-3/4" />
              <div className="h-3 bg-muted rounded w-1/2" />
            </div>
          ))}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="text-lg">어휘 어원 학습</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {result!.words.map((entry, index) => (
          <div key={index}>
            {index > 0 && <hr className="mb-6" />}
            <h3 className="text-base font-semibold mb-2">{entry.word}</h3>
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown>{entry.content}</ReactMarkdown>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
