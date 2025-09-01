"""Service registry handling for game configurations."""

import json
from pathlib import Path

from rich.console import Console

from ..exceptions import GameNotFoundError, ValidationError
from ..models import ServiceConfig

console = Console()


class ServiceRegistry:
    """Handles loading and managing game service configurations."""
    
    def __init__(self, services_dir: Path | None = None) -> None:
        """Initialize the service registry.
        
        Args:
            services_dir: Directory containing service JSON files. 
                         Defaults to ~/services
        """
        if services_dir is None:
            services_dir = Path.home() / "services"
        self.services_dir = services_dir
        self._configs: dict[str, ServiceConfig] = {}
        self._load_configs()
    
    def _load_configs(self) -> None:
        """Load all service configurations from the services directory."""
        self._configs.clear()
        
        if not self.services_dir.exists():
            console.print(f"[yellow]Services directory not found: {self.services_dir}[/yellow]")
            return
            
        json_files = list(self.services_dir.glob("*.json"))
        if not json_files:
            console.print(f"[yellow]No service configurations found in {self.services_dir}[/yellow]")
            return
        
        for json_file in json_files:
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                config = ServiceConfig(**data)
                self._configs[config.id] = config
            except Exception as e:
                console.print(f"[red]Error loading {json_file}: {e}[/red]")
    
    def reload(self) -> None:
        """Reload all configurations from disk."""
        self._load_configs()
    
    def get_config(self, game_id: str) -> ServiceConfig:
        """Get configuration for a specific game.
        
        Args:
            game_id: The game identifier
            
        Returns:
            ServiceConfig for the game
            
        Raises:
            GameNotFoundError: If the game is not found
        """
        if game_id not in self._configs:
            available = list(self._configs.keys())
            raise GameNotFoundError(game_id, available)
        return self._configs[game_id]
    
    def list_games(self) -> list[ServiceConfig]:
        """Get all available game configurations.
        
        Returns:
            List of all service configurations
        """
        return list(self._configs.values())
    
    def get_game_ids(self) -> list[str]:
        """Get all available game IDs.
        
        Returns:
            List of game identifiers
        """
        return list(self._configs.keys())
    
    def has_game(self, game_id: str) -> bool:
        """Check if a game exists in the registry.
        
        Args:
            game_id: The game identifier
            
        Returns:
            True if the game exists
        """
        return game_id in self._configs
    
    def validate_config(self, config: ServiceConfig) -> None:
        """Validate a service configuration.
        
        Args:
            config: The configuration to validate
            
        Raises:
            ValidationError: If validation fails
        """
        # Check if executable exists
        if not config.executable.exists():
            raise ValidationError(
                f"Executable not found: {config.executable}",
                f"Run 'gameserver update {config.id}' to download game files"
            )
        
        # Check if game directory exists
        if not config.game_dir.exists():
            raise ValidationError(
                f"Game directory not found: {config.game_dir}",
                f"Run 'gameserver update {config.id}' to download game files"
            )
        
        # Check if working directory exists (if specified)
        if config.working_directory and not config.working_directory.exists():
            raise ValidationError(
                f"Working directory not found: {config.working_directory}"
            )
