"""Pydantic models for service configurations and download markers."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Type alias for supported game source types
GameSourceType = Literal["steam", "gog", "lutris", "direct", "manual"]


class GameSource(BaseModel):
    """Model for game source information."""
    
    type: GameSourceType = Field(..., description="Type of game source")
    source_id: str = Field(..., description="Source-specific identifier (e.g., Steam app ID)")
    metadata: dict[str, str] = Field(default_factory=dict, description="Source-specific metadata")
    
    model_config = ConfigDict(populate_by_name=True)


class ServiceConfig(BaseModel):
    """Model for game service configuration files."""
    
    id: str = Field(..., description="Unique game identifier")
    name: str = Field(..., description="Human-readable game name")
    description: str = Field(..., description="Game description")
    unit_name: str = Field(..., alias="unitName", description="systemd unit name")
    
    # Game source and download configuration
    game_source: GameSource = Field(..., description="Source for game downloads")
    
    # Installation and execution
    game_dir: Path = Field(..., alias="gameDir", description="Game installation directory")
    executable: Path = Field(..., description="Game server executable path")
    user: str = Field(..., description="User to run the service as")
    group: str | None = Field(None, description="Group to run the service as")
    working_directory: Path | None = Field(None, alias="workingDirectory", description="Working directory for the service")
    args: list[str] = Field(default_factory=list, description="Command line arguments")
    environment: dict[str, str] = Field(default_factory=dict, description="Environment variables")
    ports: list[int] = Field(default_factory=list, description="Ports used by the game server")
    config_file: Path | None = Field(None, alias="configFile", description="Game configuration file path")
    log_dir: Path | None = Field(None, alias="logDir", description="Log directory path")
    clean_filters: list[str] = Field(default_factory=list, alias="cleanFilters", description="Paths to clean during uninstall")
    shutdown_command: list[str] | None = Field(None, alias="shutdownCommand", description="Custom shutdown command (if not using systemctl stop)")
    
    @field_validator("group")
    @classmethod
    def default_group(cls, v: str | None, info) -> str:
        """Default group to user if not specified."""
        return v or info.data.get("user", "")
    
    @field_validator("ports")
    @classmethod
    def validate_ports(cls, v: list[int]) -> list[int]:
        """Validate port numbers are in valid range."""
        for port in v:
            if not (1 <= port <= 65535):
                raise ValueError(f"Port {port} is not in valid range 1-65535")
        return v
    
    @field_validator("game_source")
    @classmethod
    def validate_game_source(cls, v: GameSource) -> GameSource:
        """Validate game source configuration."""
        if v.type == "steam" and not v.source_id.isdigit():
            raise ValueError("Steam source_id must be a numeric app ID")
        return v
    
    model_config = ConfigDict(populate_by_name=True)


class DownloadMarker(BaseModel):
    """Model for download completion marker files."""
    
    timestamp: datetime = Field(..., description="When the download was initiated")
    game_source: GameSource = Field(..., description="Source used for download")
    download_status: str = Field(..., description="Download status (success/failed)")
    game_dir: Path = Field(..., description="Game installation directory")
    file_count: int = Field(..., description="Number of files downloaded")
    total_size: str = Field(..., description="Total download size")
    validation_status: str = Field(..., description="Validation status")
    last_updated: datetime = Field(..., description="Last update timestamp")
    
    @field_validator("download_status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate download status values."""
        valid_statuses = {"success", "failed", "partial", "validating"}
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        return v


class GameStatus(BaseModel):
    """Model for game status information."""
    
    id: str
    name: str
    service_status: str
    download_status: str
    
    
class NetworkPort(BaseModel):
    """Model for network port status."""
    
    port: int
    status: str  # "LISTENING" or "closed"
    

class GameNetworkStatus(BaseModel):
    """Model for game network status."""
    
    id: str
    name: str
    service_status: str
    ports: list[NetworkPort]


class DiskUsage(BaseModel):
    """Model for disk usage information."""
    
    id: str
    name: str
    size: str
    size_bytes: int
    file_count: int | None = None
    last_updated: datetime | None = None
    path: Path
    downloaded: bool
