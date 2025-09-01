"""Game download services for different sources."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from ..models import ServiceConfig, DownloadMarker


class BaseDownloader(ABC):
    """Abstract base class for game downloaders."""
    
    @abstractmethod
    def can_handle(self, config: ServiceConfig) -> bool:
        """Check if this downloader can handle the given configuration."""
        pass
    
    @abstractmethod
    def download_game(self, config: ServiceConfig, force: bool = False) -> None:
        """Download or update a game.
        
        Args:
            config: Service configuration
            force: Force download even if files exist
            
        Raises:
            DownloadError: If download fails
        """
        pass
    
    @abstractmethod
    def needs_download(self, config: ServiceConfig, force: bool = False) -> bool:
        """Check if game needs to be downloaded.
        
        Args:
            config: Service configuration
            force: Force download check
            
        Returns:
            True if download is needed
        """
        pass
    
    @abstractmethod
    def validate_game_files(self, config: ServiceConfig) -> bool:
        """Validate that game files are present and valid.
        
        Args:
            config: Service configuration
            
        Returns:
            True if files are valid
        """
        pass
    
    def _load_download_marker(self, marker_file: Path) -> DownloadMarker | None:
        """Load download marker from file.
        
        Args:
            marker_file: Path to the marker file
            
        Returns:
            DownloadMarker object or None if not found/invalid
        """
        try:
            if marker_file.exists():
                return DownloadMarker.model_validate_json(marker_file.read_text())
        except Exception:
            pass
        return None


class DownloadManager:
    """Manages different game download sources."""
    
    def __init__(self):
        self._downloaders: list[BaseDownloader] = []
    
    def register_downloader(self, downloader: BaseDownloader) -> None:
        """Register a new downloader."""
        self._downloaders.append(downloader)
    
    def get_downloader(self, config: ServiceConfig) -> BaseDownloader:
        """Get appropriate downloader for the given configuration."""
        for downloader in self._downloaders:
            if downloader.can_handle(config):
                return downloader
        
        from ..exceptions import GameServerError
        raise GameServerError(
            f"No downloader available for game source: {config.game_source}",
            config.id
        )
    
    def download_game(self, config: ServiceConfig, force: bool = False) -> None:
        """Download a game using the appropriate downloader."""
        downloader = self.get_downloader(config)
        downloader.download_game(config, force)
    
    def needs_download(self, config: ServiceConfig, force: bool = False) -> bool:
        """Check if game needs download using the appropriate downloader."""
        downloader = self.get_downloader(config)
        return downloader.needs_download(config, force)
    
    def validate_game_files(self, config: ServiceConfig) -> bool:
        """Validate game files using the appropriate downloader."""
        downloader = self.get_downloader(config)
        return downloader.validate_game_files(config)


# Global download manager instance
download_manager = DownloadManager()
