import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

// React JSX transform requires React to be in scope for older JSX transforms
// In Next.js 15 with app directory, this may not be strictly necessary
// but we keep it for compatibility
import React from "react";

interface ChatContainerProps {
  children: ReactNode;
  className?: string;
}

/**
 * Container component for the chat interface
 * Provides flex column layout with proper spacing
 */
export function ChatContainer({ children, className }: ChatContainerProps) {
  return (
    <div className={cn("flex flex-col h-full", className)}>
      {children}
    </div>
  );
}
