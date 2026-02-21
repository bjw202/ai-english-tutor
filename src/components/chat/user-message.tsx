import React from "react";
import { formatTimestamp } from "@/lib/utils";
import { cn } from "@/lib/utils";

interface UserMessageProps {
  content: string;
  timestamp: Date;
  className?: string;
}

/**
 * User message bubble component
 * Right-aligned with primary color background
 */
export function UserMessage({ content, timestamp, className }: UserMessageProps) {
  return (
    <div className={cn("flex justify-end mb-4", className)}>
      <div className="max-w-[80%]">
        <div className="bg-primary text-primary-foreground rounded-2xl rounded-br-sm px-4 py-2">
          <p className="text-sm whitespace-pre-wrap break-words">{content}</p>
        </div>
        <p className="text-xs text-muted-foreground mt-1 text-right">
          {formatTimestamp(timestamp)}
        </p>
      </div>
    </div>
  );
}
