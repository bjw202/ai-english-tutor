"""Session management service for AI English Tutor.

Provides in-memory session management with TTL support.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from tutor.config import Settings

# Global session manager instance (lazy-initialized)
_session_manager: SessionManager | None = None


class SessionManager:
    """In-memory session management with TTL."""

    def __init__(self, ttl_hours: int = 24) -> None:
        """Initialize the session manager.

        Args:
            ttl_hours: Time-to-live for sessions in hours (default: 24)
        """
        self._sessions: dict[str, dict] = {}
        self._ttl = timedelta(hours=ttl_hours)

    def create(self) -> str:
        """Create a new session and return session_id.

        Returns:
            A unique session ID (UUID4 string)
        """
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = {
            "id": session_id,
            "messages": [],
            "created_at": datetime.now(),
            "expires_at": datetime.now() + self._ttl,
        }
        return session_id

    def get(self, session_id: str) -> dict | None:
        """Get session by ID, return None if not found or expired.

        Args:
            session_id: The session ID to retrieve

        Returns:
            The session dict if found and not expired, None otherwise
        """
        session = self._sessions.get(session_id)
        if not session:
            return None
        if datetime.now() > session["expires_at"]:
            del self._sessions[session_id]
            return None
        return session

    def add_message(self, session_id: str, role: str, content: str) -> bool:
        """Add a message to session history.

        Args:
            session_id: The session ID to add the message to
            role: The role of the message sender (e.g., "user", "assistant")
            content: The message content

        Returns:
            True if the message was added, False if session not found
        """
        session = self.get(session_id)
        if not session:
            return False
        session["messages"].append({"role": role, "content": content})
        return True

    def delete(self, session_id: str) -> bool:
        """Delete a session.

        Args:
            session_id: The session ID to delete

        Returns:
            True if the session was deleted, False if not found
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False


def get_session_manager() -> SessionManager:
    """Get or create the global session manager instance.

    Uses lazy initialization to avoid loading settings during module import.

    Returns:
        The global SessionManager instance
    """
    global _session_manager
    if _session_manager is None:
        settings = Settings()
        _session_manager = SessionManager(ttl_hours=settings.SESSION_TTL_HOURS)
    return _session_manager


# Backward compatibility: provide a module-level property
class _SessionManagerProxy:
    """Proxy for lazy session manager initialization."""

    def __getattr__(self, name: str):  # noqa: D105
        return getattr(get_session_manager(), name)

    def __setattr__(self, name: str, value):  # noqa: D105
        setattr(get_session_manager(), name, value)


session_manager = _SessionManagerProxy()
