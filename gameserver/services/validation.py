"""File and download validation services."""

import json
from pathlib import Path

from rich.console import Console

from ..exceptions import ValidationError
from ..models import DownloadMarker, ServiceConfig

console = Console()


class ValidationService:
    """Handles file and download validation."""
    
    @staticmethod
    def validate_download_marker(marker_file: Path) -> DownloadMarker | None:
        """Validate and parse a download marker file.
        
        Args:
            marker_file: Path to the marker file
            
        Returns:
            DownloadMarker if valid, None if not found
            
        Raises:
            ValidationError: If marker file is invalid
        """
        if not marker_file.exists():
            return None
        
        try:
            with open(marker_file, 'r') as f:
                data = json.load(f)
            return DownloadMarker(**data)
        except (json.JSONDecodeError, ValueError) as e:
            raise ValidationError(
                f"Invalid download marker file: {marker_file}",
                "Run 'gameserver update <game>' to repair"
            ) from e
    
    @staticmethod
    def validate_game_files(config: ServiceConfig) -> None:
        """Validate that game files are properly downloaded and accessible.
        
        Args:
            config: The service configuration
            
        Raises:
            ValidationError: If validation fails
        """
        # Check if executable exists
        if not config.executable.exists():
            raise ValidationError(
                f"Game executable not found: {config.executable}",
                f"Run 'gameserver update {config.id}' to download files"
            )
        
        # Check if executable is actually executable
        if not config.executable.is_file():
            raise ValidationError(
                f"Executable path is not a file: {config.executable}"
            )
        
        # If steam app is configured, validate download marker
        if config.steam_app:
            marker_file = config.game_dir / ".steamcmd-completed"
            marker = ValidationService.validate_download_marker(marker_file)
            
            if marker is None:
                raise ValidationError(
                    "Game files not found",
                    f"Run 'gameserver update {config.id}' first"
                )
            
            if marker.download_status != "success":
                raise ValidationError(
                    "Previous download failed",
                    f"Run 'gameserver update {config.id}' to retry"
                )
            
            # Validate that the steam app matches
            if marker.steam_app != config.steam_app:
                raise ValidationError(
                    f"Steam app mismatch: expected {config.steam_app}, got {marker.steam_app}",
                    f"Run 'gameserver update {config.id}' to update"
                )
    
    @staticmethod
    def needs_download(marker_file: Path, steam_app: str, force: bool = False) -> bool:
        """Check if a download is needed.
        
        Args:
            marker_file: Path to the download marker
            steam_app: Steam app ID with branch
            force: Force download even if files exist
            
        Returns:
            True if download is needed
        """
        if force:
            return True
        
        try:
            marker = ValidationService.validate_download_marker(marker_file)
            if marker is None:
                return True
            
            # Check if it's the same steam app
            if marker.steam_app != steam_app:
                return True
            
            # Check if download was successful
            return marker.download_status != "success"
        except ValidationError:
            return True
