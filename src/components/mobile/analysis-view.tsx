import React from "react";
import { TabbedOutput } from "@/components/tutor/tabbed-output";
import type { TutorStreamState } from "@/hooks/use-tutor-stream";

interface AnalysisViewProps {
  streamState: TutorStreamState;
  level: number;
}

/**
 * Full-screen analysis results wrapper for mobile
 * Displays streaming status, errors, and tabbed analysis output
 */
export function AnalysisView({ streamState }: AnalysisViewProps) {
  return (
    <div className="flex flex-col h-full p-4">
      {/* Streaming indicator */}
      {streamState.isStreaming && (
        <div className="p-3 bg-primary/10 rounded-lg text-sm text-primary mb-4 flex-shrink-0">
          분석 중... 잠시 기다려주세요
        </div>
      )}

      {/* Error display */}
      {streamState.error && (
        <div className="p-3 bg-destructive/10 rounded-lg text-sm text-destructive mb-4 flex-shrink-0">
          오류: {streamState.error.message}
        </div>
      )}

      {/* TabbedOutput - full remaining height */}
      <div className="flex-1 min-h-0 overflow-hidden">
        <TabbedOutput
          reading={
            streamState.readingContent
              ? { content: streamState.readingContent }
              : null
          }
          grammar={
            streamState.grammarContent
              ? { content: streamState.grammarContent }
              : null
          }
          vocabulary={
            streamState.vocabularyWords && streamState.vocabularyWords.length > 0
              ? { words: streamState.vocabularyWords }
              : null
          }
          isStreaming={streamState.isStreaming}
          readingStreaming={streamState.readingStreaming}
          grammarStreaming={streamState.grammarStreaming}
          vocabularyStreaming={streamState.vocabularyStreaming}
          vocabularyError={streamState.vocabularyError}
          vocabularyRawContent={streamState.vocabularyRawContent}
        />
      </div>
    </div>
  );
}
