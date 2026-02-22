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
export function AnalysisView({ streamState, level }: AnalysisViewProps) {
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
              ? {
                  summary: streamState.readingContent,
                  keyPoints: [],
                  comprehensionLevel: level,
                }
              : null
          }
          grammar={
            streamState.grammarContent
              ? {
                  issues: [],
                  overallScore: 85,
                  suggestions: [streamState.grammarContent],
                }
              : null
          }
          vocabulary={null}
          vocabularyRawContent={streamState.vocabularyContent}
        />
      </div>
    </div>
  );
}
