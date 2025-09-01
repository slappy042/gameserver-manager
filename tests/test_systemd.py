"""Tests for systemd service."""

from gameserver.services.systemd import SystemdService


class TestSystemdService:
    """Test systemd service functionality."""
    
    def test_is_active_nonexistent_service(self):
        """Test checking status of non-existent service."""
        # This should not raise an exception and return False
        result = SystemdService.is_active("nonexistent-service-12345")
        assert result is False
    
    def test_get_status_nonexistent_service(self):
        """Test getting status of non-existent service."""
        status = SystemdService.get_status("nonexistent-service-12345")
        assert status in ["inactive", "unknown"]
