import React from "react";
import { cn } from "@/lib/utils";

interface HeaderProps {
  className?: string;
}

/**
 * App header component
 * Displays logo and title
 */
export function Header({ className }: HeaderProps) {
  return (
    <header className={cn("border-b bg-background", className)}>
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 bg-primary rounded-lg">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="text-primary-foreground"
            >
              <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
              <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
            </svg>
          </div>
          <div>
            <h1 className="text-xl font-bold">AI English Tutor</h1>
            <p className="text-xs text-muted-foreground">
              Learn English with AI-powered analysis
            </p>
          </div>
        </div>
      </div>
    </header>
  );
}
