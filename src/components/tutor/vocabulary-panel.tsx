import React from "react";
import ReactMarkdown from "react-markdown";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { VocabularyResult } from "@/types/tutor";

interface VocabularyPanelProps {
  result: VocabularyResult | null;
  className?: string;
}

/**
 * Vocabulary etymology learning panel
 * Displays list of words with Korean Markdown etymology explanations
 */
export function VocabularyPanel({ result, className }: VocabularyPanelProps) {
  if (!result || !result.words || result.words.length === 0) {
    return (
      <Card className={className}>
        <CardContent className="p-6 text-center text-muted-foreground">
          아직 어휘 분석이 없습니다
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
        {result.words.map((entry, index) => (
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
