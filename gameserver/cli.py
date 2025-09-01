"""Main CLI application using Typer."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console

from .exceptions import GameserverError
from .services.downloaders import DownloadManager
from .services.registry import ServiceRegistry
from .services.systemd import SystemdService
from .services.validation import ValidationService

# Initialize Typer app and Rich console
app = typer.Typer(
    name="gameserver",
    help="Modern CLI tool for managing game servers on NixOS",
    no_args_is_help=True,
)
console = Console()

# Global service registry and download manager
registry = ServiceRegistry()
download_manager = DownloadManager()


def handle_error(error: Exception) -> None:
    """Handle and display errors with Rich formatting."""
    if isinstance(error, GameserverError):
        console.print(f"[red]Error: {error.message}[/red]")
        if error.suggestion:
            console.print(f"[yellow]Suggestion: {error.suggestion}[/yellow]")
    else:
        console.print(f"[red]Unexpected error: {error}[/red]")
    raise typer.Exit(1)


@app.command()
def status() -> None:
    """Show all game services and their status."""
    console.print("[bold cyan]=== Game Server Services ===[/bold cyan]")
    console.print()
    
    games = registry.list_games()
    if not games:
        console.print("[yellow](no games configured)[/yellow]")
        console.print()
        console.print("Available commands:")
        console.print("  gameserver status              - Show this status")
        console.print("  gameserver list                - List available games")
        console.print("  gameserver start <game>        - Start a game service")
        console.print("  gameserver stop <game>         - Stop a game service")
        console.print("  gameserver restart <game>      - Restart a game service")
        console.print("  gameserver clean <game>        - Clean/uninstall a game")
        console.print("  gameserver logs <game>         - Show recent logs")
        console.print("  gameserver update <game>       - Update game files")
        console.print("  gameserver info <game>         - Show game information")
        console.print()
        console.print("Note: Games run as transient systemd units (no persistent auto-start)")
        return
    
    console.print("[bold]Game Services:[/bold]")
    
    for config in games:
        service_status = SystemdService.get_status(config.unit_name)
        
        # Check download status
        download_status = "not-downloaded"
        if config.steam_app:
            marker_file = config.game_dir / ".steamcmd-completed"
            try:
                marker = ValidationService.validate_download_marker(marker_file)
                if marker and marker.download_status == "success":
                    download_status = "success"
                elif marker:
                    download_status = marker.download_status
            except Exception:
                download_status = "unknown"
        else:
            download_status = "n/a"
        
        # Color code the status
        service_color = "green" if service_status == "active" else "red" if service_status == "failed" else "yellow"
        download_color = "green" if download_status == "success" else "red" if download_status == "failed" else "yellow"
        
        console.print(f"  {config.name} ({config.id}) - Service: [{service_color}]{service_status}[/{service_color}], Files: [{download_color}]{download_status}[/{download_color}]")
    
    console.print()
    console.print("Available commands:")
    console.print("  gameserver status              - Show this status")
    console.print("  gameserver list                - List available games")
    console.print("  gameserver start <game>        - Start a game service")
    console.print("  gameserver stop <game>         - Stop a game service")
    console.print("  gameserver restart <game>      - Restart a game service")
    console.print("  gameserver clean <game>        - Clean/uninstall a game (stop, remove files)")
    console.print("  gameserver logs <game>         - Show recent logs")
    console.print("  gameserver update <game>       - Update game files")
    console.print("  gameserver info <game>         - Show game information")
    console.print()
    console.print("Note: Games run as transient systemd units (no persistent auto-start)")


@app.command()
def list() -> None:
    """List available games with details."""
    console.print("[bold cyan]=== Available Games ===[/bold cyan]")
    console.print()
    
    games = registry.list_games()
    if not games:
        console.print("No games configured.")
        return
    
    for config in games:
        console.print(f"[bold]Game: {config.name} ({config.id})[/bold]")
        console.print(f"  Description: {config.description}")
        console.print(f"  Steam App: {config.steam_app or 'N/A'}")
        console.print()


@app.command()
def info(game: str) -> None:
    """Show detailed information about a specific game."""
    try:
        config = registry.get_config(game)
    except Exception as e:
        handle_error(e)
    
    console.print(f"[bold cyan]=== {config.name} Information ===[/bold cyan]")
    console.print()
    console.print(f"Game ID: {config.id}")
    console.print(f"Service Name: {config.unit_name}")
    console.print(f"Steam App: {config.steam_app or 'N/A'}")
    console.print(f"Game Directory: {config.game_dir}")
    console.print(f"Executable: {config.executable}")
    console.print(f"Ports: {', '.join(map(str, config.ports)) if config.ports else 'N/A'}")
    console.print(f"Config File: {config.config_file or 'N/A'}")
    console.print(f"Log Directory: {config.log_dir or 'N/A'}")
    console.print(f"Run User: {config.user}")
    console.print(f"Group: {config.group}")
    console.print(f"Description: {config.description}")
    console.print()
    
    # Show current status
    status = SystemdService.get_status(config.unit_name)
    status_color = "green" if status == "active" else "red" if status == "failed" else "yellow"
    console.print(f"Current Status: [{status_color}]{status}[/{status_color}]")
    
    # Show download status if marker exists
    if config.steam_app:
        marker_file = config.game_dir / ".steamcmd-completed"
        try:
            marker = ValidationService.validate_download_marker(marker_file)
            if marker:
                console.print()
                console.print("[bold cyan]=== Download Status ===[/bold cyan]")
                console.print(f"Last Updated: {marker.last_updated}")
                console.print(f"Steam App: {marker.steam_app}")
                console.print(f"Beta Branch: {marker.beta_branch}")
                console.print(f"Download Status: {marker.download_status}")
                console.print(f"File Count: {marker.file_count}")
                console.print(f"Total Size: {marker.total_size}")
                console.print(f"Validation: {marker.validation_status}")
            else:
                console.print()
                console.print("[bold cyan]=== Download Status ===[/bold cyan]")
                console.print("Status: Not downloaded or invalid marker file")
        except Exception:
            console.print()
            console.print("[bold cyan]=== Download Status ===[/bold cyan]")
            console.print("Status: Invalid marker file")
    
    # Show port status if ports are defined
    if config.ports:
        console.print()
        console.print("[bold cyan]=== Port Status ===[/bold cyan]")
        for port in config.ports:
            try:
                result = subprocess.run(
                    ["ss", "-tuln"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                if f":{port} " in result.stdout:
                    console.print(f"  Port {port}: [green]LISTENING[/green]")
                else:
                    console.print(f"  Port {port}: [red]closed[/red]")
            except Exception:
                console.print(f"  Port {port}: [yellow]unknown[/yellow]")


@app.command()
def update(
    game: str,
    force: bool = typer.Option(False, "--force", help="Force re-download even if files exist")
) -> None:
    """Update/download game files using SteamCMD."""
    try:
        config = registry.get_config(game)
        
        if not config.steam_app:
            console.print(f"[red]No Steam app configured for {config.name}[/red]")
            raise typer.Exit(1)
        
        # Check if download is needed
        marker_file = config.game_dir / ".steamcmd-completed"
        if not force and not ValidationService.needs_download(marker_file, config.steam_app, force):
            try:
                marker = ValidationService.validate_download_marker(marker_file)
                if marker:
                    console.print(f"{config.name} is already up to date (last updated: {marker.last_updated})")
                    console.print("Use --force to re-download anyway")
                    return
            except Exception:
                pass
        
        download_manager.download_game(config, force)
        
    except Exception as e:
        handle_error(e)


@app.command()
def start(game: str) -> None:
    """Start a game service."""
    try:
        config = registry.get_config(game)
        
        console.print(f"Starting {config.name}...")
        
        # Validate game files if steam app is configured
        if config.steam_app:
            ValidationService.validate_game_files(config)
            console.print("[green]✓ Game files verified[/green]")
        
        SystemdService.start_service(config)
        
    except Exception as e:
        handle_error(e)


@app.command()
def stop(game: str) -> None:
    """Stop a game service."""
    try:
        config = registry.get_config(game)
        console.print(f"Stopping {config.name}...")
        SystemdService.stop_service(config)
        
    except Exception as e:
        handle_error(e)


@app.command()
def restart(game: str) -> None:
    """Restart a game service."""
    try:
        config = registry.get_config(game)
        SystemdService.restart_service(config)
        
    except Exception as e:
        handle_error(e)


@app.command()
def logs(
    game: str,
    args: Optional[List[str]] = None
) -> None:
    """Show recent logs for a game."""
    try:
        config = registry.get_config(game)
        
        if args is None:
            args = ["--no-pager", "-n", "50"]
        
        SystemdService.get_logs(config.unit_name, args)
        
    except Exception as e:
        handle_error(e)


@app.command()
def clean(
    game: str,
    user_data: bool = typer.Option(False, "--user-data", help="Also remove user data"),
    all_data: bool = typer.Option(False, "--all", help="Clean everything")
) -> None:
    """Clean/uninstall a game (stop service, remove files)."""
    try:
        config = registry.get_config(game)
        
        clean_user_data = user_data or all_data
        
        console.print(f"[bold cyan]=== Cleaning {config.name} ===[/bold cyan]")
        console.print()
        console.print("[red]⚠️  WARNING: This will permanently delete game files and data![/red]")
        console.print(f"   - Game installation directory: {config.game_dir}")
        if clean_user_data:
            console.print("   - User data (as defined in service registry)")
        console.print()
        
        # 1. Stop the service if running
        console.print("1. Stopping service...")
        try:
            SystemdService.stop_service(config)
        except Exception:
            console.print("   [yellow]✓ Service was not running[/yellow]")
        
        # 2. Remove game installation directory
        if config.game_dir.exists():
            console.print("2. Removing game files...")
            console.print(f"   Directory: {config.game_dir}")
            
            # Get directory size
            try:
                result = subprocess.run(
                    ["du", "-sh", str(config.game_dir)],
                    capture_output=True,
                    text=True,
                    check=True
                )
                size = result.stdout.split()[0]
                console.print(f"   Size: {size}")
            except Exception:
                console.print("   Size: unknown")
            
            if typer.confirm("   Remove game installation directory?"):
                import shutil
                shutil.rmtree(config.game_dir)
                console.print("   [green]✓ Game files removed[/green]")
            else:
                console.print("   [yellow]✓ Game files kept[/yellow]")
        else:
            console.print("2. Game directory not found or not specified")
        
        # 3. Clean user data if requested
        if clean_user_data and config.clean_filters:
            console.print("3. Cleaning user data...")
            console.print("   Files that would be removed:")
            
            for filter_path in config.clean_filters:
                expanded_path = Path(filter_path).expanduser()
                if expanded_path.exists():
                    console.print(f"     - {expanded_path}")
            
            if typer.confirm("   Remove user data?"):
                for filter_path in config.clean_filters:
                    expanded_path = Path(filter_path).expanduser()
                    if expanded_path.exists():
                        if expanded_path.is_dir():
                            import shutil
                            shutil.rmtree(expanded_path)
                        else:
                            expanded_path.unlink()
                        console.print(f"     [green]✓ Removed: {expanded_path}[/green]")
                console.print("     [green]✓ User data cleaned[/green]")
            else:
                console.print("     [yellow]✓ User data kept[/yellow]")
        elif clean_user_data:
            console.print("3. [yellow]✓ No clean filters defined for this game[/yellow]")
        
        console.print()
        console.print("[bold cyan]=== Cleanup Complete ===[/bold cyan]")
        
    except Exception as e:
        handle_error(e)


@app.command()
def network() -> None:
    """Show game server ports and network status."""
    console.print("[bold cyan]=== Network Status ===[/bold cyan]")
    console.print()
    
    games = registry.list_games()
    if not games:
        console.print("No games configured.")
        return
    
    for config in games:
        service_status = SystemdService.get_status(config.unit_name)
        status_color = "green" if service_status == "active" else "red" if service_status == "failed" else "yellow"
        
        console.print(f"{config.name} ({config.id}) - [{status_color}]{service_status}[/{status_color}]:")
        
        if config.ports:
            for port in config.ports:
                try:
                    result = subprocess.run(
                        ["ss", "-tuln"],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    if f":{port} " in result.stdout:
                        console.print(f"  Port {port}: [green]LISTENING[/green]")
                    else:
                        console.print(f"  Port {port}: [red]closed[/red]")
                except Exception:
                    console.print(f"  Port {port}: [yellow]unknown[/yellow]")
        else:
            console.print("  No ports configured")
        console.print()
    
    console.print("All listening ports in game range (26000-28000):")
    try:
        result = subprocess.run(
            ["ss", "-tuln"],
            capture_output=True,
            text=True,
            check=True
        )
        
        game_ports = []
        for line in result.stdout.split('\n'):
            for port in range(26000, 28001):
                if f":{port} " in line:
                    game_ports.append(f"  Port {port}: LISTENING")
        
        if game_ports:
            for port_line in game_ports:
                console.print(port_line)
        else:
            console.print("  No game ports active")
    except Exception:
        console.print("  Error checking ports")


@app.command()
def disk() -> None:
    """Show disk usage for game files."""
    console.print("[bold cyan]=== Disk Usage ===[/bold cyan]")
    console.print()
    
    games = registry.list_games()
    if not games:
        console.print("No games configured.")
        return
    
    total_size_bytes = 0
    
    for config in games:
        if config.game_dir.exists():
            try:
                # Get directory size
                result = subprocess.run(
                    ["du", "-sb", str(config.game_dir)],
                    capture_output=True,
                    text=True,
                    check=True
                )
                size_bytes = int(result.stdout.split()[0])
                total_size_bytes += size_bytes
                
                # Get human readable size
                result = subprocess.run(
                    ["du", "-sh", str(config.game_dir)],
                    capture_output=True,
                    text=True,
                    check=True
                )
                size = result.stdout.split()[0]
                
                # Check for download info
                download_info = ""
                marker_file = config.game_dir / ".steamcmd-completed"
                try:
                    marker = ValidationService.validate_download_marker(marker_file)
                    if marker:
                        download_info = f" ({marker.file_count} files, updated: {marker.last_updated.strftime('%Y-%m-%d %H:%M')})"
                except Exception:
                    pass
                
                console.print(f"{config.name} ({config.id}): {size}{download_info}")
                console.print(f"  Path: {config.game_dir}")
            except Exception:
                console.print(f"{config.name} ({config.id}): error reading size")
                console.print(f"  Path: {config.game_dir}")
        else:
            console.print(f"{config.name} ({config.id}): not downloaded")
        console.print()
    
    if total_size_bytes > 0:
        # Convert to human readable
        def format_size(size_bytes: int) -> str:
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if size_bytes < 1024:
                    return f"{size_bytes:.1f}{unit}"
                size_bytes /= 1024
            return f"{size_bytes:.1f}PB"
        
        total_human = format_size(total_size_bytes)
        console.print(f"[bold]Total game files: {total_human}[/bold]")


if __name__ == "__main__":
    app()
