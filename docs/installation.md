# Installation Guide

## Using Nix Flakes (Recommended)

### Quick Run

You can run the tool directly from GitHub without installing:

```bash
nix run github:slappy042/gameserver-manager -- status
```

### System Installation

Add to your NixOS configuration:

```nix
{
  inputs.gameserver-manager.url = "github:slappy042/gameserver-manager";
  
  # In your system configuration:
  environment.systemPackages = [
    inputs.gameserver-manager.packages.${pkgs.system}.default
  ];
}
```

### User Installation

Install for your user profile:

```bash
nix profile install github:slappy042/gameserver-manager
```

## Development Setup

### Prerequisites

- Nix with flakes enabled
- UV (will be available in the dev shell)

### Clone and Setup

```bash
git clone https://github.com/slappy042/gameserver-manager
cd gameserver-manager

# Enter development shell (provides Python, UV, and system tools)
nix develop

# Install Python dependencies
uv sync

# Run the tool
uv run gameserver-manager status
```

### Available Commands in Dev Shell

```bash
# Run the tool
uv run gameserver-manager <command>

# Run tests
uv run pytest

# Type checking
uv run mypy gameserver/

# Linting and formatting
uv run ruff check gameserver/
uv run ruff format gameserver/

# Build the package
nix build
```

## System Requirements

- NixOS (for full functionality)
- Python 3.11+
- systemd (for service management)
- SteamCMD (provided by Nix flake)

## Runtime Dependencies

The following tools are automatically available when using the Nix package:

- `steamcmd` - For downloading games
- `systemctl` - For service management
- `journalctl` - For viewing logs
- `patchelf` - For fixing executables on NixOS
- `ss` - For checking network ports
- `du` - For disk usage calculations

## Troubleshooting

### Permission Issues

The tool requires sudo access for systemd operations. Ensure your user can run:

```bash
sudo systemctl status
sudo journalctl
```

### SteamCMD Issues

If SteamCMD fails, ensure you have a working internet connection and the Steam app ID is correct.

### Missing Game Configurations

Game configurations should be stored in `~/services/*.json`. See the [Configuration Guide](configuration.md) for details.
