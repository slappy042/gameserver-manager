"""Custom exception classes for gameserver manager."""

from __future__ import annotations


class GameServerError(Exception):
    """Base exception for all gameserver manager errors."""
    
    def __init__(self, message: str, suggestion: str | None = None) -> None:
        self.message = message
        self.suggestion = suggestion
        super().__init__(message)


class GameNotFoundError(GameServerError):
    """Raised when a requested game is not found in the registry."""
    
    def __init__(self, game_id: str, available_games: list[str]) -> None:
        message = f"Game '{game_id}' not found"
        if available_games:
            suggestion = f"Available games: {', '.join(available_games)}"
        else:
            suggestion = "No games configured. Check ~/games/services/ directory."
        super().__init__(message, suggestion)


class ServiceError(GameServerError):
    """Raised when systemd service operations fail."""
    pass


class SteamCMDError(GameServerError):
    """Raised when SteamCMD operations fail."""
    pass


class ValidationError(GameServerError):
    """Raised when file or configuration validation fails."""
    pass


class PermissionError(GameServerError):
    """Raised when permission-related operations fail."""
    pass
