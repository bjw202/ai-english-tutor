import { describe, it, expect } from "vitest";
import type { Message, UserMessage, TutorMessage, ChatSession } from "../chat";

describe("Chat Types", () => {
  describe("UserMessage", () => {
    it("should have correct structure", () => {
      const message: UserMessage = {
        id: "msg-001",
        role: "user",
        content: "What is photosynthesis?",
        timestamp: new Date("2024-01-01T10:00:00Z"),
      };

      expect(message.id).toBeTypeOf("string");
      expect(message.role).toBe("user");
      expect(message.content).toBeTypeOf("string");
      expect(message.timestamp).toBeInstanceOf(Date);
    });
  });

  describe("TutorMessage", () => {
    it("should have correct structure", () => {
      const message: TutorMessage = {
        id: "msg-002",
        role: "tutor",
        content: "Photosynthesis is the process by which plants...",
        timestamp: new Date("2024-01-01T10:00:01Z"),
        isStreaming: false,
      };

      expect(message.id).toBeTypeOf("string");
      expect(message.role).toBe("tutor");
      expect(message.content).toBeTypeOf("string");
      expect(message.timestamp).toBeInstanceOf(Date);
      expect(message.isStreaming).toBeTypeOf("boolean");
    });

    it("should have isStreaming as optional", () => {
      const message: TutorMessage = {
        id: "msg-003",
        role: "tutor",
        content: "Another response",
        timestamp: new Date(),
      };

      expect(message.isStreaming).toBeUndefined();
    });
  });

  describe("Message type union", () => {
    it("should accept both user and tutor messages", () => {
      const userMessage: Message = {
        id: "msg-001",
        role: "user",
        content: "User text",
        timestamp: new Date(),
      };

      const tutorMessage: Message = {
        id: "msg-002",
        role: "tutor",
        content: "Tutor text",
        timestamp: new Date(),
        isStreaming: false,
      };

      expect(userMessage.role).toBe("user");
      expect(tutorMessage.role).toBe("tutor");
    });

    it("should discriminate by role property", () => {
      const messages: Message[] = [
        {
          id: "msg-001",
          role: "user",
          content: "Question",
          timestamp: new Date(),
        },
        {
          id: "msg-002",
          role: "tutor",
          content: "Answer",
          timestamp: new Date(),
        },
      ];

      const userMessages = messages.filter((m) => m.role === "user");
      const tutorMessages = messages.filter((m) => m.role === "tutor");

      expect(userMessages).toHaveLength(1);
      expect(tutorMessages).toHaveLength(1);
    });
  });

  describe("ChatSession", () => {
    it("should have correct structure", () => {
      const session: ChatSession = {
        sessionId: "session-123",
        messages: [
          {
            id: "msg-001",
            role: "user",
            content: "Hello",
            timestamp: new Date(),
          },
          {
            id: "msg-002",
            role: "tutor",
            content: "Hi there!",
            timestamp: new Date(),
          },
        ],
      };

      expect(session.sessionId).toBeTypeOf("string");
      expect(Array.isArray(session.messages)).toBe(true);
      expect(session.messages).toHaveLength(2);
    });
  });
});
