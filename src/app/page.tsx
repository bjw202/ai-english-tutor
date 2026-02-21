"use client";

import React, { useState } from "react";
import { Header } from "@/components/controls/header";
import { LevelSlider } from "@/components/controls/level-slider";
import { TabbedOutput } from "@/components/tutor/tabbed-output";
import { ChatContainer } from "@/components/chat/chat-container";
import { MessageList } from "@/components/chat/message-list";
import { ChatInput } from "@/components/chat/chat-input";
import { ImageUpload } from "@/components/chat/image-upload";
import { useSession } from "@/hooks/use-session";
import { useLevelConfig } from "@/hooks/use-level-config";
import { useTutorStream } from "@/hooks/use-tutor-stream";
import { analyzeImage } from "@/lib/api";
import type { Message } from "@/types/chat";
import type { TutorStreamState } from "@/hooks/use-tutor-stream";
import { toast } from "sonner";

/**
 * Main page component
 * Combines all chat and tutor components
 */
export default function HomePage() {
  const { sessionId } = useSession();
  const { level, setLevel, levelLabel } = useLevelConfig();

  const [messages, setMessages] = useState<Message[]>([]);
  const [analysisResult, setAnalysisResult] = useState<TutorStreamState>({
    readingContent: "",
    grammarContent: "",
    vocabularyContent: "",
    isStreaming: false,
    error: null,
  });

  const { state: streamState, startStream } = useTutorStream();

  // Show loading state during SSR/hydration when sessionId is not initialized
  if (!sessionId) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  const handleSendMessage = async (text: string) => {
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: text,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);

    try {
      // Start streaming
      await startStream(() =>
        fetch("/api/tutor/analyze", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text, level }),
        })
      );

      // Add tutor message (streaming)
      const tutorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "tutor",
        content: streamState.readingContent || streamState.grammarContent || streamState.vocabularyContent || "",
        timestamp: new Date(),
        isStreaming: true,
      };
      setMessages((prev) => [...prev, tutorMessage]);

      // Update analysis result
      setAnalysisResult({
        readingContent: streamState.readingContent,
        grammarContent: streamState.grammarContent,
        vocabularyContent: streamState.vocabularyContent,
        isStreaming: streamState.isStreaming,
        error: streamState.error,
      });

    } catch (error) {
      toast.error("Failed to send message");
      console.error(error);
    }
  };

  const handleImageSelect = async (file: File) => {
    // Add user message about image
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: `[Image: ${file.name}]`,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);

    try {
      await analyzeImage(file, level);
      toast.success("Image analyzed successfully");
    } catch (error) {
      toast.error("Failed to analyze image");
      console.error(error);
    }
  };

  return (
    <div className="flex flex-col h-screen">
      <Header />

      <div className="flex-1 overflow-hidden">
        <div className="container mx-auto px-4 py-6 h-full">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-full">
            {/* Left Column: Chat */}
            <ChatContainer className="h-full">
              <div className="flex-1 overflow-y-auto p-4">
                <MessageList messages={messages} />
              </div>
              <div className="border-t p-4 space-y-4">
                <ImageUpload onFileSelect={handleImageSelect} />
                <ChatInput
                  onSend={handleSendMessage}
                  disabled={streamState.isStreaming}
                />
              </div>
            </ChatContainer>

            {/* Right Column: Analysis Results */}
            <div className="h-full overflow-y-auto">
              <div className="space-y-4">
                <LevelSlider
                  level={level}
                  onChange={setLevel}
                  levelLabel={levelLabel}
                />
                <TabbedOutput
                  reading={
                    analysisResult.readingContent
                      ? {
                          summary: analysisResult.readingContent,
                          keyPoints: [],
                          comprehensionLevel: level,
                        }
                      : null
                  }
                  grammar={
                    analysisResult.grammarContent
                      ? {
                          issues: [],
                          overallScore: 85,
                          suggestions: [analysisResult.grammarContent],
                        }
                      : null
                  }
                  vocabulary={
                    analysisResult.vocabularyContent
                      ? {
                          words: [],
                          difficultyLevel: level,
                        }
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
