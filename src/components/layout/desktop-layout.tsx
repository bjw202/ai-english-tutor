import React from "react";
import { Header } from "@/components/controls/header";
import { LevelSlider } from "@/components/controls/level-slider";
import { TabbedOutput } from "@/components/tutor/tabbed-output";
import { ChatContainer } from "@/components/chat/chat-container";
import { MessageList } from "@/components/chat/message-list";
import { ChatInput } from "@/components/chat/chat-input";
import { ImageUpload } from "@/components/chat/image-upload";
import type { Message } from "@/types/chat";
import type { TutorStreamState } from "@/hooks/use-tutor-stream";

interface DesktopLayoutProps {
  // Session
  sessionId: string;
  // Messages
  messages: Message[];
  // Stream state
  streamState: TutorStreamState;
  // Level
  level: number;
  onLevelChange: (level: number) => void;
  levelLabel: string;
  // Handlers
  onSendMessage: (text: string) => void;
  onImageSelect: (file: File) => void;
}

/**
 * Desktop 2-column layout component
 * Left column: Chat interface
 * Right column: Analysis results with level slider
 */
export function DesktopLayout({
  messages,
  streamState,
  level,
  onLevelChange,
  levelLabel,
  onSendMessage,
  onImageSelect,
}: DesktopLayoutProps) {
  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <Header />

      <div className="flex-1 overflow-hidden">
        <div className="container mx-auto px-4 py-6 h-full">
          <div className="grid grid-cols-2 gap-6 h-[calc(100%-3rem)]">
            {/* Left Column: Chat */}
            <ChatContainer className="h-full overflow-hidden">
              <div className="flex-1 overflow-y-auto p-4 min-h-0">
                <MessageList messages={messages} />
              </div>
              <div className="border-t p-4 space-y-4 flex-shrink-0">
                <ImageUpload onFileSelect={onImageSelect} />
                <ChatInput
                  onSend={onSendMessage}
                  disabled={streamState.isStreaming}
                />
              </div>
            </ChatContainer>

            {/* Right Column: Analysis Results */}
            <div className="h-full flex flex-col overflow-hidden">
              <div className="space-y-4 flex-shrink-0">
                <LevelSlider
                  level={level}
                  onChange={onLevelChange}
                  levelLabel={levelLabel}
                />

                {/* Streaming indicator */}
                {streamState.isStreaming && (
                  <div className="p-4 bg-primary/10 rounded-lg text-sm text-primary">
                    분석 중... 잠시 기다려주세요
                  </div>
                )}

                {/* Error display */}
                {streamState.error && (
                  <div className="p-4 bg-destructive/10 rounded-lg text-sm text-destructive">
                    오류: {streamState.error.message}
                  </div>
                )}
              </div>

              {/* TabbedOutput with proper flex constraints */}
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
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
