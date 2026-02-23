"use client";

import React, { useState } from "react";
import { useSession } from "@/hooks/use-session";
import { useLevelConfig } from "@/hooks/use-level-config";
import { useTutorStream } from "@/hooks/use-tutor-stream";
import { useMediaQuery } from "@/hooks/use-media-query";
import { DesktopLayout } from "@/components/layout/desktop-layout";
import { MobileLayout } from "@/components/layout/mobile-layout";
import type { Message } from "@/types/chat";
import { toast } from "sonner";

/**
 * Main page component
 * Combines all chat and tutor components with responsive layout support
 */
export default function HomePage() {
  const { sessionId } = useSession();
  const { level, setLevel, levelLabel } = useLevelConfig();

  const [messages, setMessages] = useState<Message[]>([]);
  const [activeMobileTab, setActiveMobileTab] = useState<"camera" | "analysis">("camera");

  const { state: streamState, startStream } = useTutorStream();
  const isDesktop = useMediaQuery("(min-width: 1024px)");

  // Show loading state during SSR/hydration when sessionId is not initialized
  if (!sessionId) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  // Show loading skeleton while media query resolves (SSR/pre-hydration)
  if (isDesktop === null) {
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

    // Auto-switch to analysis tab on mobile
    if (!isDesktop) {
      setActiveMobileTab("analysis");
    }

    try {
      await startStream(() =>
        fetch("/api/tutor/analyze", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text, level }),
        })
      );
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

    // Auto-switch to analysis tab on mobile
    if (!isDesktop) {
      setActiveMobileTab("analysis");
    }

    try {
      const imageFormData = new FormData();
      imageFormData.append("file", file);
      imageFormData.append("level", String(level));

      await startStream(() =>
        fetch("/api/tutor/analyze-image", {
          method: "POST",
          body: imageFormData,
        })
      );
    } catch (error) {
      toast.error("Failed to analyze image");
      console.error(error);
    }
  };

  if (!isDesktop) {
    return (
      <MobileLayout
        activeTab={activeMobileTab}
        onTabChange={setActiveMobileTab}
        onImageSelect={handleImageSelect}
        onSendMessage={handleSendMessage}
        level={level}
        onLevelChange={setLevel}
        levelLabel={levelLabel}
        isStreaming={streamState.isStreaming}
        streamState={streamState}
      />
    );
  }

  return (
    <DesktopLayout
      sessionId={sessionId}
      messages={messages}
      streamState={streamState}
      level={level}
      onLevelChange={setLevel}
      levelLabel={levelLabel}
      onSendMessage={handleSendMessage}
      onImageSelect={handleImageSelect}
    />
  );
}
