"""Session-scoped in-memory conversation history for chat requests."""

from threading import RLock

ConversationMessage = dict[str, str]

_histories: dict[str, list[ConversationMessage]] = {}
_lock = RLock()


def get_history(session_id: str) -> list[ConversationMessage]:
    """Return a copy of a session's history, creating the session if needed."""
    with _lock:
        history = _histories.setdefault(session_id, [])
        return [message.copy() for message in history]


def add_user_message(session_id: str, message: str) -> None:
    """Append a user message to a session's history."""
    _add_message(session_id, "user", message)


def add_assistant_message(session_id: str, message: str) -> None:
    """Append an assistant message to a session's history."""
    _add_message(session_id, "assistant", message)


def clear_history(session_id: str) -> None:
    """Remove all conversation history for a session."""
    with _lock:
        _histories.pop(session_id, None)


def _add_message(session_id: str, role: str, message: str) -> None:
    with _lock:
        _histories.setdefault(session_id, []).append({"role": role, "content": message})
