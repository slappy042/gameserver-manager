"""Tests for SteamCMD service."""

from pathlib import Path

from gameserver.models import GameSource, ServiceConfig
from gameserver.services.steam import SteamCMDService


class TestSteamCMDService:
    """Test SteamCMD service functionality."""
    
    def test_build_steamcmd_command_simple(self):
        """Test building SteamCMD command for simple app."""
        config = ServiceConfig(
            id="test-game",
            name="Test Game",
            description="A test game",
            unit_name="test-game",
            game_source=GameSource(
                type="steam",
                source_id="294420"
            ),
            game_dir=Path("/games/test"),
            executable=Path("/games/test/server"),
            user="gameserver"
        )
        
        cmd = SteamCMDService.build_steamcmd_command(config, "294420", "", "")
        
        expected = [
            "steamcmd",
            "+force_install_dir", "/games/test",
            "+login", "anonymous",
            "+app_update", "294420", "validate",
            "+quit"
        ]
        assert cmd == expected
    
    def test_build_steamcmd_command_with_beta(self):
        """Test building SteamCMD command with beta branch."""
        config = ServiceConfig(
            id="test-game",
            name="Test Game",
            description="A test game",
            unit_name="test-game",
            game_source=GameSource(
                type="steam",
                source_id="294420",
                metadata={
                    "beta_branch": "experimental"
                }
            ),
            game_dir=Path("/games/test"),
            executable=Path("/games/test/server"),
            user="gameserver"
        )
        
        cmd = SteamCMDService.build_steamcmd_command(config, "294420", "experimental", "")
        
        expected = [
            "steamcmd",
            "+force_install_dir", "/games/test",
            "+login", "anonymous",
            "+app_update", "294420", "-beta", "experimental", "validate",
            "+quit"
        ]
        assert cmd == expected
