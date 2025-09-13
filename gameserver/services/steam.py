"""SteamCMD operations for downloading and updating games."""

import contextlib
import json
import subprocess
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..exceptions import SteamCMDError
from ..models import DownloadMarker, ServiceConfig
from .downloaders import BaseDownloader, register_downloader

console = Console()


@register_downloader
class SteamCMDService(BaseDownloader):
    """Handles SteamCMD operations for game downloads."""
    
    def can_handle(self, config: ServiceConfig) -> bool:
        """Check if this service can handle the given configuration."""
        return config.game_source.type == "steam"
    
    def needs_download(self, config: ServiceConfig, force: bool = False) -> bool:
        """Check if game needs to be downloaded."""
        if force:
            return True
        
        marker_file = config.game_dir / ".steamcmd-completed"
        if not marker_file.exists():
            return True
        
        try:
            marker = self._load_download_marker(marker_file)
            if not marker:
                return True
            
            # Check if it's the same steam app
            if marker.game_source.source_id != config.game_source.source_id:
                return True
            
            # Check if download was successful
            return marker.download_status != "success"
        except Exception:
            return True
    
    def validate_game_files(self, config: ServiceConfig) -> bool:
        """Validate that Steam game files are present and valid."""
        if not config.executable.exists():
            return False
        
        marker_file = config.game_dir / ".steamcmd-completed"
        if not marker_file.exists():
            return False
        
        try:
            marker = self._load_download_marker(marker_file)
            return marker is not None and marker.download_status == "success"
        except Exception:
            return False
    
    @staticmethod
    def build_steamcmd_command(config: ServiceConfig, app_id: str, beta_branch: str, beta_password: str) -> list[str]:
        """Build the steamcmd command for downloading a game.
        
        Args:
            config: Service configuration
            app_id: Steam application ID
            beta_branch: Beta branch name (empty for stable)
            beta_password: Beta branch password (empty if none)
            
        Returns:
            List of command arguments
        """
        cmd = [
            "steamcmd",
            "+force_install_dir", str(config.game_dir),
            "+login", "anonymous"
        ]
        
        if beta_branch:
            cmd.extend(["+app_update", app_id, "-beta", beta_branch])
            if beta_password:
                cmd.extend(["-betapassword", beta_password])
        else:
            cmd.extend(["+app_update", app_id])
        
        cmd.extend(["validate", "+quit"])
        return cmd
    
    @staticmethod
    def fix_executables_nixos(game_dir: Path) -> None:
        """Fix executable permissions and interpreters for NixOS.
        
        Args:
            game_dir: Game installation directory
        """
        try:
            # Find the correct glibc path by using ldd on /bin/ls (which is always available)
            ldd_result = subprocess.run(
                ["ldd", "/bin/ls"],
                capture_output=True,
                text=True,
                check=False
            )
            
            interpreter_path = None
            if ldd_result.returncode == 0:
                # Look for the ld-linux-x86-64.so.2 line in ldd output
                for line in ldd_result.stdout.split('\n'):
                    if 'ld-linux-x86-64.so.2' in line and '=>' in line:
                        # Extract the path after '=>'
                        interpreter_path = line.split('=>')[1].strip().split()[0]
                        break
            
            # Fallback: try to find it directly in nix store
            if not interpreter_path:
                find_result = subprocess.run(
                    ["find", "/nix/store", "-maxdepth", "2", "-name", "glibc-*"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                if find_result.returncode == 0 and find_result.stdout.strip():
                    glibc_dir = find_result.stdout.strip().split('\n')[0]
                    potential_path = f"{glibc_dir}/lib64/ld-linux-x86-64.so.2"
                    if Path(potential_path).exists():
                        interpreter_path = potential_path
            
            if interpreter_path and Path(interpreter_path).exists():
                for file_path in game_dir.rglob("*"):
                    if file_path.is_file() and file_path.stat().st_mode & 0o111:
                        # Check if it's an ELF executable that needs patching
                        file_result = subprocess.run(
                            ["file", str(file_path)],
                            capture_output=True,
                            text=True,
                            check=False
                        )
                        
                        if ("ELF" in file_result.stdout and 
                            "dynamically linked" in file_result.stdout and
                            "x86-64" in file_result.stdout):
                            # Try to patch the interpreter for NixOS
                            subprocess.run(
                                ["patchelf", "--set-interpreter", interpreter_path, str(file_path)],
                                capture_output=True,
                                check=False
                            )
        except Exception:
            # Patchelf might fail on some files, that's okay
            pass
    
    def download_game(self, config: ServiceConfig, force: bool = False) -> None:  # noqa: ARG004
        """Download or update a game using SteamCMD.
        
        Args:
            config: Service configuration
            force: Force download even if files exist (not yet implemented)
            
        Raises:
            SteamCMDError: If download fails
        """
        if config.game_source.type != "steam":
            raise SteamCMDError(
                f"Invalid game source '{config.game_source.type}' for Steam downloader",
                "Use game_source.type = 'steam'"
            )
        
        app_id = config.game_source.source_id
        beta_branch = config.game_source.metadata.get("beta_branch")
        beta_password = config.game_source.metadata.get("beta_password")
        
        console.print(f"[bold]Updating {config.name}...[/bold]")
        console.print(f"Steam App ID: {app_id}")
        console.print(f"Target Directory: {config.game_dir}")
        if beta_branch:
            console.print(f"Beta Branch: {beta_branch}")
        if beta_password:
            console.print("Beta Password: [REDACTED]")
        console.print()
        
        # Ensure directory exists
        config.game_dir.mkdir(parents=True, exist_ok=True)
        
        # Remove old marker to indicate download in progress
        marker_file = config.game_dir / ".steamcmd-completed"
        if marker_file.exists():
            marker_file.unlink()
        
        # Build and execute command
        cmd = SteamCMDService.build_steamcmd_command(config, app_id, beta_branch, beta_password)
        
        console.print(f"Executing: {' '.join(cmd)}")
        console.print("=" * 50)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Downloading game files...", total=None)
            
            try:
                subprocess.run(
                    cmd,
                    cwd=config.game_dir,
                    check=True,
                    capture_output=False  # Show output in real time
                )
                
                progress.update(task, description="[green]Download completed successfully[/green]")
                
            except subprocess.CalledProcessError as e:
                progress.update(task, description="[red]Download failed[/red]")
                raise SteamCMDError(
                    f"SteamCMD failed with exit code {e.returncode}",
                    "Check your internet connection and Steam app ID"
                ) from e
        
        console.print("=" * 50)
        console.print("[green]✓ Download completed successfully[/green]")
        
        # Fix executables for NixOS
        console.print("Fixing executables for NixOS...")
        SteamCMDService.fix_executables_nixos(config.game_dir)
        
        # Create download completion marker
        self._create_download_marker(config)
        
        console.print("[green]✓ Download completed successfully[/green]")
    
    def _create_download_marker(self, config: ServiceConfig) -> None:
        """Create a download completion marker file."""
        # Get download statistics
        file_count = 0
        total_size_bytes = 0
        
        if config.game_dir.exists():
            for file_path in config.game_dir.rglob("*"):
                if file_path.is_file():
                    file_count += 1
                    with contextlib.suppress(OSError):
                        total_size_bytes += file_path.stat().st_size
        
        # Format size in human-readable format
        def format_size(size_bytes: int) -> str:
            for unit in ['B', 'K', 'M', 'G', 'T']:
                if size_bytes < 1024:
                    return f"{size_bytes:.1f}{unit}"
                size_bytes /= 1024
            return f"{size_bytes:.1f}P"
        
        total_size = format_size(total_size_bytes)
        
        # Create marker data
        now = datetime.now()
        marker = DownloadMarker(
            timestamp=now,
            game_source=config.game_source,
            download_status="success",
            game_dir=config.game_dir,
            file_count=file_count,
            total_size=total_size,
            validation_status="passed",
            last_updated=now
        )
        
        # Write marker file
        marker_file = config.game_dir / ".steamcmd-completed"
        with open(marker_file, 'w') as f:
            json.dump(marker.model_dump(), f, indent=2, default=str)
