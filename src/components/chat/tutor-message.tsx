import React from "react";
import { formatTimestamp } from "@/lib/utils";
import { cn } from "@/lib/utils";

interface TutorMessageProps {
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
  className?: string;
}

/**
 * Tutor/AI message bubble component
 * Left-aligned with muted background
 */
export function TutorMessage({ content, timestamp, isStreaming, className }: TutorMessageProps) {
  return (
    <div className={cn("flex justify-start mb-4", className)}>
      <div className="max-w-[80%]">
        <div className="bg-muted text-foreground rounded-2xl rounded-bl-sm px-4 py-2">
          <p className="text-sm whitespace-pre-wrap break-words">
            {content}
            {isStreaming && (
              <span className="inline-block ml-1 animate-pulse">...</span>
            )}
          </p>
        </div>
        <p className="text-xs text-muted-foreground mt-1">
          {formatTimestamp(timestamp)}
        </p>
      </div>
    </div>
  );
}
