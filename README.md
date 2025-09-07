# Gameserver Manager

Modern Python CLI tool for managing game servers on NixOS, replacing a complex 647-line justfile with a clean, type-safe Python implementation.

## Features

- **Type-safe CLI** with Typer and Rich for beautiful terminal output
- **Pydantic models** for JSON configuration validation
- **Direct SteamCMD integration** with progress bars
- **systemd service management** using transient units
- **Nix flake packaging** for easy NixOS integration
- **Comprehensive error handling** with recovery suggestions

## Installation

### Using Nix Flakes (Recommended)

```bash
# Run directly from GitHub
nix run github:slappy042/gameserver-manager -- status

# Add to your NixOS configuration
{
  inputs.gameserver-manager.url = "github:slappy042/gameserver-manager";
  # ... then add to systemPackages
}
```

### Development Setup

```bash
# Clone and enter development shell
git clone https://github.com/slappy042/gameserver-manager
cd gameserver-manager
nix develop

# Install dependencies
uv sync

# Run the tool
uv run gameserver-manager status
```

## Usage

The CLI maintains the same command structure as the original justfile:

```bash
# Show all services status
gameserver-manager status

# List available games
gameserver-manager list

# Show detailed game information
gameserver-manager info <game>

# Update/download game files
gameserver-manager update <game> [--force]

# Service management
gameserver-manager start <game>
gameserver-manager stop <game>
gameserver-manager restart <game>

# Maintenance
gameserver-manager clean <game> [--user-data]
gameserver-manager logs <game> [args...]
gameserver-manager network
gameserver-manager disk
```

## Configuration

Game configurations are stored as JSON files in `~/services/*.json`. See the [configuration documentation](docs/configuration.md) for details.

## Development

```bash
# Run tests
uv run pytest

# Type checking
uv run mypy gameserver/

# Linting
uv run ruff check gameserver/

# Format code
uv run ruff format gameserver/
```

## License

MIT License - see [LICENSE](LICENSE) for details.
