/**
 * User message in the chat
 */
export interface UserMessage {
  id: string;
  role: "user";
  content: string;
  timestamp: Date;
}

/**
 * Tutor/AI message in the chat
 */
export interface TutorMessage {
  id: string;
  role: "tutor";
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
}

/**
 * Union type for all message types
 */
export type Message = UserMessage | TutorMessage;

/**
 * Complete chat session with messages
 */
export interface ChatSession {
  sessionId: string;
  messages: Message[];
}
