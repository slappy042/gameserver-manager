"""Custom exception classes for gameserver manager."""

from __future__ import annotations


class GameserverError(Exception):
    """Base exception for all gameserver manager errors."""
    
    def __init__(self, message: str, suggestion: str | None = None) -> None:
        self.message = message
        self.suggestion = suggestion
        super().__init__(message)


class GameNotFoundError(GameserverError):
    """Raised when a requested game is not found in the registry."""
    
    def __init__(self, game_id: str, available_games: list[str]) -> None:
        message = f"Game '{game_id}' not found"
        if available_games:
            suggestion = f"Available games: {', '.join(available_games)}"
        else:
            suggestion = "No games configured. Check ~/games/services/ directory."
        super().__init__(message, suggestion)


class ServiceError(GameserverError):
    """Raised when systemd service operations fail."""
    pass


class SteamCMDError(GameserverError):
    """Raised when SteamCMD operations fail."""
    pass


class ValidationError(GameserverError):
    """Raised when file or configuration validation fails."""
    pass


class PermissionError(GameserverError):
    """Raised when permission-related operations fail."""
    pass
