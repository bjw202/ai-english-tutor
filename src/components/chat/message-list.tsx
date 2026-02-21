import { useEffect, useRef } from "react";
import React from "react";
import type { Message } from "@/types/chat";
import { UserMessage } from "./user-message";
import { TutorMessage } from "./tutor-message";

interface MessageListProps {
  messages: Message[];
  className?: string;
}

/**
 * List of chat messages with auto-scroll to bottom
 */
export function MessageList({ messages, className }: MessageListProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  if (messages.length === 0) {
    return null;
  }

  return (
    <div className={className}>
      {messages.map((message) => {
        if (message.role === "user") {
          return <UserMessage key={message.id} content={message.content} timestamp={message.timestamp} />;
        }
        return (
          <TutorMessage
            key={message.id}
            content={message.content}
            timestamp={message.timestamp}
            isStreaming={message.isStreaming}
          />
        );
      })}
      <div ref={scrollRef} />
    </div>
  );
}
