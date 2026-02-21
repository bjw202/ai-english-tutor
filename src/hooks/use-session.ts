import { useState, useEffect } from "react";

const SESSION_STORAGE_KEY = "tutor_session_id";

/**
 * Hook to manage user session ID with localStorage persistence
 * @returns Session ID and reset function
 */
export function useSession() {
  const [sessionId, setSessionId] = useState<string>("");

  // Initialize from localStorage on client side only
  useEffect(() => {
    const stored = localStorage.getItem(SESSION_STORAGE_KEY);
    if (stored) {
      setSessionId(stored);
    } else {
      const newId = generateId();
      setSessionId(newId);
      localStorage.setItem(SESSION_STORAGE_KEY, newId);
    }
  }, []);

  const resetSession = () => {
    const newId = generateId();
    setSessionId(newId);
    localStorage.setItem(SESSION_STORAGE_KEY, newId);
  };

  return {
    sessionId,
    resetSession,
  };
}

function generateId(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  // Fallback
  return `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}
