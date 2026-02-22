import React from "react";
import { Header } from "@/components/controls/header";
import { CameraView } from "@/components/mobile/camera-view";
import { AnalysisView } from "@/components/mobile/analysis-view";
import type { TutorStreamState } from "@/hooks/use-tutor-stream";

interface MobileLayoutProps {
  // Active tab state
  activeTab: "camera" | "analysis";
  onTabChange: (tab: "camera" | "analysis") => void;
  // Camera/Upload view props
  onImageSelect: (file: File) => void;
  onSendMessage: (text: string) => void;
  level: number;
  onLevelChange: (level: number) => void;
  levelLabel: string;
  isStreaming: boolean;
  // Analysis view props
  streamState: TutorStreamState;
}

/**
 * Mobile layout with bottom tab navigation
 * Switches between camera/upload view and analysis results view
 */
export function MobileLayout({
  activeTab,
  onTabChange,
  onImageSelect,
  onSendMessage,
  level,
  onLevelChange,
  levelLabel,
  isStreaming,
  streamState,
}: MobileLayoutProps) {
  return (
    <div className="flex flex-col h-screen overflow-hidden">
      {/* Compact header */}
      <Header />

      {/* Tab content area */}
      <main className="flex-1 overflow-y-auto">
        {activeTab === "camera" ? (
          <CameraView
            onImageSelect={onImageSelect}
            onSendMessage={onSendMessage}
            level={level}
            onLevelChange={onLevelChange}
            levelLabel={levelLabel}
            isStreaming={isStreaming}
          />
        ) : (
          <AnalysisView
            streamState={streamState}
            level={level}
          />
        )}
      </main>

      {/* Bottom tab bar */}
      <nav
        className="flex border-t bg-background flex-shrink-0"
        role="tablist"
        aria-label="메인 탭 내비게이션"
      >
        {/* Camera tab */}
        <button
          role="tab"
          aria-selected={activeTab === "camera"}
          aria-controls="camera-panel"
          aria-label="카메라 탭"
          className={`flex-1 flex flex-col items-center justify-center py-3 gap-1 text-sm transition-colors ${
            activeTab === "camera"
              ? "text-primary font-medium"
              : "text-muted-foreground"
          }`}
          onClick={() => onTabChange("camera")}
        >
          {/* Camera icon */}
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="22"
            height="22"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z" />
            <circle cx="12" cy="13" r="3" />
          </svg>
          <span>카메라</span>
        </button>

        {/* Analysis tab */}
        <button
          role="tab"
          aria-selected={activeTab === "analysis"}
          aria-controls="analysis-panel"
          aria-label="분석 탭"
          className={`flex-1 flex flex-col items-center justify-center py-3 gap-1 text-sm transition-colors ${
            activeTab === "analysis"
              ? "text-primary font-medium"
              : "text-muted-foreground"
          }`}
          onClick={() => onTabChange("analysis")}
        >
          {/* Bar chart icon */}
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="22"
            height="22"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <line x1="18" x2="18" y1="20" y2="10" />
            <line x1="12" x2="12" y1="20" y2="4" />
            <line x1="6" x2="6" y1="20" y2="14" />
          </svg>
          <span>분석</span>
        </button>
      </nav>
    </div>
  );
}
