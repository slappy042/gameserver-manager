"""systemd service management for game servers."""

import subprocess

from rich.console import Console

from ..exceptions import ServiceError
from ..models import ServiceConfig

console = Console()


class SystemdService:
    """Handles systemd service operations for game servers."""
    
    @staticmethod
    def is_active(unit_name: str) -> bool:
        """Check if a systemd unit is active.
        
        Args:
            unit_name: The systemd unit name
            
        Returns:
            True if the service is active
        """
        try:
            result = subprocess.run(
                ["sudo", "systemctl", "is-active", "--quiet", unit_name],
                capture_output=True,
                check=False
            )
            return result.returncode == 0
        except Exception:
            return False
    
    @staticmethod
    def is_managed(unit_name: str) -> bool:
        """Check if a systemd unit exists and is being managed by systemd.
        
        Args:
            unit_name: The systemd unit name
            
        Returns:
            True if the service exists (in any state: active, activating, failed, etc.)
        """
        try:
            result = subprocess.run(
                ["sudo", "systemctl", "status", unit_name],
                capture_output=True,
                check=False
            )
            # Return code 0 = active, 1 = dead, 3 = failed/activating, 4 = not found
            return result.returncode != 4
        except Exception:
            return False
    
    @staticmethod
    def get_status(unit_name: str) -> str:
        """Get the status of a systemd unit.
        
        Args:
            unit_name: The systemd unit name
            
        Returns:
            Status string (active, inactive, failed, etc.)
        """
        try:
            result = subprocess.run(
                ["sudo", "systemctl", "is-active", unit_name],
                capture_output=True,
                text=True,
                check=False
            )
            return result.stdout.strip() or "inactive"
        except Exception:
            return "unknown"
    
    @staticmethod
    def start_service(config: ServiceConfig) -> None:
        """Start a game service using systemd-run.
        
        Args:
            config: The service configuration
            
        Raises:
            ServiceError: If the service fails to start
        """
        if SystemdService.is_active(config.unit_name):
            raise ServiceError(f"{config.name} is already running!")
        
        # Build systemd-run command
        cmd = [
            "sudo", "systemd-run",
            f"--unit={config.unit_name}",
            f"--uid={config.user}",
            f"--gid={config.group}",
            "--collect"
        ]
        
        # Add working directory if specified
        if config.working_directory:
            cmd.append(f"--working-directory={config.working_directory}")
        
        # Add environment variables
        for key, value in config.environment.items():
            cmd.append(f"--setenv={key}={value}")
        
        # Add executable and arguments
        cmd.append(str(config.executable))
        cmd.extend(config.args)
        
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            console.print(f"[green]✓ {config.name} started as systemd unit: {config.unit_name}[/green]")
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to start {config.name}: {e.stderr}"
            raise ServiceError(error_msg, "Check service configuration and permissions") from e
    
    @staticmethod
    def stop_service(config: ServiceConfig) -> None:
        """Stop a game service.
        
        Args:
            config: The service configuration
            
        Raises:
            ServiceError: If the service fails to stop
        """
        if not SystemdService.is_managed(config.unit_name):
            console.print(f"[yellow]{config.name} is not running or managed by systemd[/yellow]")
            return
        
        try:
            subprocess.run(
                ["sudo", "systemctl", "stop", config.unit_name],
                capture_output=True,
                text=True,
                check=True
            )
            console.print(f"[green]✓ {config.name} stopped[/green]")
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to stop {config.name}: {e.stderr}"
            raise ServiceError(error_msg) from e
    
    @staticmethod
    def restart_service(config: ServiceConfig) -> None:
        """Restart a game service.
        
        Args:
            config: The service configuration
        """
        console.print(f"Restarting {config.name}...")
        SystemdService.stop_service(config)
        import time
        time.sleep(2)
        SystemdService.start_service(config)
    
    @staticmethod
    def get_logs(unit_name: str, args: list[str] | None = None) -> None:
        """Show logs for a service using journalctl.
        
        Args:
            unit_name: The systemd unit name
            args: Additional arguments for journalctl
        """
        if args is None:
            args = ["--no-pager", "-n", "50"]
        
        cmd = ["sudo", "journalctl", "-u", unit_name] + args
        
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            raise ServiceError(f"Failed to get logs: {e}") from e
        except KeyboardInterrupt:
            # Allow user to interrupt log viewing
            pass
