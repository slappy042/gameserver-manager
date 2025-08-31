# Gameserver Manager - Implementation Specification

## Project Overview

Create a modern Python CLI tool for managing game servers on NixOS, replacing a complex 647-line justfile with a clean, type-safe Python implementation using Typer, Rich, and UV package management.

## Context & Requirements

### Current Architecture (to be replaced)
- **Current tool**: justfile with bash scripts (647 lines)
- **Pain points**: 
  - Repetitive JSON validation code
  - Complex bash error handling
  - Function scope issues
  - Limited type safety
  - Difficult to test and maintain

### Current Implementation Reference

<details>
<summary>Current justfile implementation (647 lines) - Click to expand</summary>

```bash
# Gameserver Management Commands
# Usage: just <command>

# Service registry location (created by home-manager)
services_dir := env_var_or_default('HOME', '/home/jeff') + '/services'

# List all game services and their status
status:
    #!/usr/bin/env bash
    echo "=== Game Server Services ==="
    echo ""

    echo "Game Services:"
    if [[ -d {{services_dir}} ]]; then
        for json_file in {{services_dir}}/*.json; do
            if [[ -f "$json_file" ]]; then
                game_id=$(jq -r '.id' "$json_file")
                game_name=$(jq -r '.name' "$json_file")
                unit_name=$(jq -r '.unitName' "$json_file")
                status=$(sudo systemctl is-active "$unit_name" 2>/dev/null || echo "inactive")

                # Check download status
                game_dir=$(jq -r '.gameDir // empty' "$json_file")
                marker_file="$game_dir/.steamcmd-completed"
                download_status="not-downloaded"
                if [[ -f "$marker_file" ]] && jq -e . "$marker_file" >/dev/null 2>&1; then
                    download_status=$(jq -r '.download_status // "unknown"' "$marker_file")
                fi

                echo "  $game_name ($game_id) - Service: $status, Files: $download_status"
            fi
        done
    else
        echo "  (no games configured)"
    fi

    echo ""
    echo "Available commands:"
    echo "  just status              - Show this status"
    echo "  just list                - List available games"
    echo "  just start <game>        - Start a game service"
    echo "  just stop <game>         - Stop a game service"
    echo "  just restart <game>      - Restart a game service"
    echo "  just clean <game>        - Clean/uninstall a game (stop, remove files)"
    echo "  just logs <game>         - Show recent logs"
    echo "  just update <game>       - Update game files"
    echo "  just info <game>         - Show game information"
    echo ""
    echo "Note: Games run as transient systemd units (no persistent auto-start)"

# List available games with details
list:
    #!/usr/bin/env bash
    echo "=== Available Games ==="
    echo ""
    if [[ -d {{services_dir}} ]]; then
        for json_file in {{services_dir}}/*.json; do
            if [[ -f "$json_file" ]]; then
                game_id=$(jq -r '.id' "$json_file")
                game_name=$(jq -r '.name' "$json_file")
                description=$(jq -r '.description' "$json_file")
                steam_app=$(jq -r '.steamApp // "N/A"' "$json_file")

                echo "Game: $game_name ($game_id)"
                echo "  Description: $description"
                echo "  Steam App: $steam_app"
                echo ""
            fi
        done
    else
        echo "No games configured."
    fi

# Show detailed information about a specific game
info game:
    #!/usr/bin/env bash
    set -euo pipefail
    json_file="{{services_dir}}/{{game}}.json"
    if [[ ! -f "$json_file" ]]; then
        echo "Game '{{game}}' not found."
        echo "Available games:"
        find {{services_dir}} -name "*.json" 2>/dev/null | xargs -I {} jq -r '.id' {} || echo "  none"
        exit 1
    fi

    echo "=== $(jq -r '.name' "$json_file") Information ==="
    echo ""
    echo "Game ID: {{game}}"
    echo "Service Name: $(jq -r '.unitName' "$json_file")"
    echo "Steam App: $(jq -r '.steamApp // "N/A"' "$json_file")"
    echo "Game Directory: $(jq -r '.gameDir // "N/A"' "$json_file")"
    echo "Executable: $(jq -r '.executable // "N/A"' "$json_file")"
    echo "Ports: $(jq -r '.ports | join(",") // "N/A"' "$json_file")"
    echo "Config File: $(jq -r '.configFile // "N/A"' "$json_file")"
    echo "Log Directory: $(jq -r '.logDir // "N/A"' "$json_file")"
    echo "Run User: $(jq -r '.user // "N/A"' "$json_file")"
    echo "Group: $(jq -r '.group // "N/A"' "$json_file")"
    echo "Description: $(jq -r '.description // "N/A"' "$json_file")"
    echo ""

    # Show current status
    unit_name=$(jq -r '.unitName' "$json_file")
    status=$(sudo systemctl is-active "$unit_name" 2>/dev/null || echo "inactive")
    echo "Current Status: $status"

    # Show download status if marker exists
    game_dir=$(jq -r '.gameDir' "$json_file")
    marker_file="$game_dir/.steamcmd-completed"
    if [[ -f "$marker_file" ]] && jq -e . "$marker_file" >/dev/null 2>&1; then
        echo ""
        echo "=== Download Status ==="
        echo "Last Updated: $(jq -r '.last_updated' "$marker_file")"
        echo "Steam App: $(jq -r '.steam_app' "$marker_file")"
        echo "Beta Branch: $(jq -r '.beta_branch' "$marker_file")"
        echo "Download Status: $(jq -r '.download_status' "$marker_file")"
        echo "File Count: $(jq -r '.file_count' "$marker_file")"
        echo "Total Size: $(jq -r '.total_size' "$marker_file")"
        echo "Validation: $(jq -r '.validation_status' "$marker_file")"
    else
        echo ""
        echo "=== Download Status ==="
        echo "Status: Not downloaded or invalid marker file"
    fi

    # Show port status if ports are defined
    ports=$(jq -r '.ports[]? // empty' "$json_file")
    if [[ -n "$ports" ]]; then
        echo ""
        echo "=== Port Status ==="
        while IFS= read -r port; do
            if ss -tuln | grep -q ":$port "; then
                echo "  Port $port: LISTENING"
            else
                echo "  Port $port: closed"
            fi
        done <<< "$ports"
    fi

# Update game files using direct steamcmd execution
update game *options="":
    #!/usr/bin/env bash
    set -euo pipefail

    # Helper function to check if download is needed
    _needs_download() {
        local marker_file="$1"
        local steam_app="$2"
        local force="$3"

        if [[ "$force" == "true" ]]; then
            return 0  # Force download
        fi

        if [[ ! -f "$marker_file" ]]; then
            return 0  # Need download - no marker
        fi

        # Check JSON validity
        if ! jq -e . "$marker_file" >/dev/null 2>&1; then
            return 0  # Need download - invalid marker
        fi

        # Check if it's the same steam app
        local stored_app=$(jq -r '.steam_app // empty' "$marker_file")
        if [[ "$stored_app" != "$steam_app" ]]; then
            return 0  # Need download - different version
        fi

        # Check if download was successful
        local status=$(jq -r '.download_status // empty' "$marker_file")
        if [[ "$status" != "success" ]]; then
            return 0  # Need download - previous failure
        fi

        return 1  # No download needed
    }

    # Helper function to create JSON marker file after successful download
    _create_marker_file() {
        local marker_file="$1"
        local steam_app="$2"
        local game_dir="$3"
        local app_id="${steam_app%_*}"
        local beta_branch="${steam_app#*_}"

        # Get some stats about the download
        local file_count=$(find "$game_dir" -type f | wc -l)
        local total_size=$(du -sh "$game_dir" 2>/dev/null | cut -f1 || echo "unknown")

        # Create JSON marker
        jq -n \
            --arg timestamp "$(date -Iseconds)" \
            --arg steam_app "$steam_app" \
            --arg app_id "$app_id" \
            --arg beta_branch "${beta_branch:-stable}" \
            --arg status "success" \
            --arg game_dir "$game_dir" \
            --arg file_count "$file_count" \
            --arg total_size "$total_size" \
            --arg validation "passed" \
            '{
                timestamp: $timestamp,
                steam_app: $steam_app,
                app_id: $app_id,
                beta_branch: $beta_branch,
                download_status: $status,
                game_dir: $game_dir,
                file_count: ($file_count | tonumber),
                total_size: $total_size,
                validation_status: $validation,
                last_updated: $timestamp
            }' > "$marker_file"
    }

    json_file="{{services_dir}}/{{game}}.json"
    if [[ ! -f "$json_file" ]]; then
        echo "Game '{{game}}' not found."
        echo "Available games:"
        find {{services_dir}} -name "*.json" 2>/dev/null | xargs -I {} jq -r '.id' {} || echo "  none"
        exit 1
    fi

    game_name=$(jq -r '.name' "$json_file")
    steam_app=$(jq -r '.steamApp // empty' "$json_file")
    game_dir=$(jq -r '.gameDir' "$json_file")

    # Parse options
    force_update=false
    for option in {{options}}; do
        case "$option" in
            --force) force_update=true ;;
            --help|-h)
                echo "Usage: just update <game> [--force]"
                echo ""
                echo "Options:"
                echo "  --force    Force re-download even if files exist"
                echo ""
                exit 0
                ;;
        esac
    done

    if [[ -z "$steam_app" || "$steam_app" == "null" ]]; then
        echo "No Steam app configured for $game_name"
        exit 1
    fi

    marker_file="$game_dir/.steamcmd-completed"

    # Check if download is needed
    if ! _needs_download "$marker_file" "$steam_app" "$force_update"; then
        last_update=$(jq -r '.last_updated' "$marker_file")
        echo "$game_name is already up to date (last updated: $last_update)"
        echo "Use --force to re-download anyway"
        exit 0
    fi

    echo "Updating $game_name..."
    echo "Steam App: $steam_app"
    echo "Target Directory: $game_dir"
    echo ""

    # Parse steam app (handle beta branches)
    IFS='_' read -r app beta betapass <<< "$steam_app"
    echo "App ID: $app"
    [[ -n "$beta" ]] && echo "Beta Branch: $beta"
    [[ -n "$betapass" ]] && echo "Beta Password: [REDACTED]"
    echo ""

    # Ensure directory exists
    mkdir -p "$game_dir"

    # Remove old marker to indicate download in progress
    rm -f "$marker_file"

    # Build steamcmd command
    cmd=(steamcmd +force_install_dir "$game_dir" +login anonymous)

    if [[ -n "$beta" ]]; then
        cmd+=(+app_update "$app" -beta "$beta")
        [[ -n "$betapass" ]] && cmd+=(-betapassword "$betapass")
    else
        cmd+=(+app_update "$app")
    fi

    cmd+=(validate +quit)

    echo "Executing: ${cmd[*]}"
    echo "=========================================="

    # Execute with proper error handling
    if "${cmd[@]}"; then
        echo "=========================================="
        echo "✓ Download completed successfully"

        # Fix executable permissions (NixOS specific)
        if [[ -d "$game_dir" ]]; then
            for f in "$game_dir"/*; do
                if [[ -f "$f" && -x "$f" ]]; then
                    # Update the interpreter to the path on NixOS
                    patchelf --set-interpreter /nix/store/*/lib/ld-linux-x86-64.so.2 "$f" 2>/dev/null || true
                fi
            done
        fi

        # Create completion marker with metadata
        _create_marker_file "$marker_file" "$steam_app" "$game_dir"
        echo "✓ Created download completion marker"
    else
        echo "=========================================="
        echo "✗ Download failed"
        exit 1
    fi

# Start a game service (with file validation)
start game:
    #!/usr/bin/env bash
    set -euo pipefail

    json_file="{{services_dir}}/{{game}}.json"
    if [[ ! -f "$json_file" ]]; then
        echo "Game '{{game}}' not found."
        exit 1
    fi

    game_name=$(jq -r '.name' "$json_file")
    unit_name=$(jq -r '.unitName' "$json_file")
    steam_app=$(jq -r '.steamApp // empty' "$json_file")
    executable=$(jq -r '.executable' "$json_file")
    user=$(jq -r '.user' "$json_file")
    group=$(jq -r '.group // "'$user'"' "$json_file")
    working_dir=$(jq -r '.workingDirectory // empty' "$json_file")
    game_dir=$(jq -r '.gameDir' "$json_file")

    echo "Starting $game_name..."

    # Check if already running
    if sudo systemctl is-active --quiet "$unit_name" 2>/dev/null; then
        echo "$game_name is already running!"
        exit 1
    fi

    # Validate steam files if steamApp is configured
    if [[ -n "$steam_app" && "$steam_app" != "null" ]]; then
        marker_file="$game_dir/.steamcmd-completed"

        if [[ ! -f "$marker_file" ]]; then
            echo "Game files not found. Run 'just update {{game}}' first."
            exit 1
        fi

        # Validate JSON marker
        if ! jq -e . "$marker_file" >/dev/null 2>&1; then
            echo "Invalid download marker. Run 'just update {{game}}' to repair."
            exit 1
        fi

        # Check download status
        if ! jq -e '.download_status == "success"' "$marker_file" >/dev/null 2>&1; then
            echo "Previous download failed. Run 'just update {{game}}' to retry."
            exit 1
        fi

        # Verify executable exists
        if [[ ! -f "$executable" ]]; then
            echo "Game executable not found: $executable"
            echo "Run 'just update {{game}}' to re-download files."
            exit 1
        fi

        echo "✓ Game files verified"
    fi

    # Build systemd-run command
    cmd=(
        sudo systemd-run
        --unit="$unit_name"
        --uid="$user"
        --gid="$group"
        --property=Restart=always
        --property=RestartSec=5
        --collect
        --remain-after-exit=no
    )

    # Add working directory if specified
    if [[ -n "$working_dir" && "$working_dir" != "null" ]]; then
        cmd+=(--working-directory="$working_dir")
    fi

    # Add environment variables
    env_vars=$(jq -r '.environment // {} | to_entries[] | "--setenv=\(.key)=\(.value)"' "$json_file")
    if [[ -n "$env_vars" ]]; then
        while IFS= read -r env_var; do
            cmd+=("$env_var")
        done <<< "$env_vars"
    fi

    # Add executable and arguments
    cmd+=("$executable")

    # Add arguments
    args=$(jq -r '.args[]? // empty' "$json_file")
    if [[ -n "$args" ]]; then
        while IFS= read -r arg; do
            cmd+=("$arg")
        done <<< "$args"
    fi

    # Execute the command
    "${cmd[@]}"
    echo "$game_name started as systemd unit: $unit_name"

# Stop a game service
stop game:
    #!/usr/bin/env bash
    set -euo pipefail

    json_file="{{services_dir}}/{{game}}.json"
    if [[ ! -f "$json_file" ]]; then
        echo "Game '{{game}}' not found."
        exit 1
    fi

    game_name=$(jq -r '.name' "$json_file")
    unit_name=$(jq -r '.unitName' "$json_file")

    echo "Stopping $game_name..."
    if sudo systemctl is-active --quiet "$unit_name" 2>/dev/null; then
        sudo systemctl stop "$unit_name"
        echo "✓ $game_name stopped"
    else
        echo "$game_name was not running"
    fi

# Restart a game service
restart game:
    just stop {{game}}
    sleep 2
    just start {{game}}

# Show recent logs for a game
logs game *args="--no-pager -n 50":
    #!/usr/bin/env bash
    set -euo pipefail

    json_file="{{services_dir}}/{{game}}.json"
    if [[ ! -f "$json_file" ]]; then
        echo "Game '{{game}}' not found."
        exit 1
    fi

    unit_name=$(jq -r '.unitName' "$json_file")
    sudo journalctl -u "$unit_name" {{args}}

# Show game server ports and network status
network:
    #!/usr/bin/env bash
    echo "=== Network Status ==="
    echo ""

    # Show status for each configured game
    if [[ -d {{services_dir}} ]]; then
        for json_file in {{services_dir}}/*.json; do
            if [[ -f "$json_file" ]]; then
                game_id=$(jq -r '.id' "$json_file")
                game_name=$(jq -r '.name' "$json_file")
                unit_name=$(jq -r '.unitName' "$json_file")
                status=$(sudo systemctl is-active "$unit_name" 2>/dev/null || echo "inactive")

                echo "$game_name ($game_id) - $status:"
                ports=$(jq -r '.ports[]? // empty' "$json_file")
                if [[ -n "$ports" ]]; then
                    while IFS= read -r port; do
                        if ss -tuln | grep -q ":$port "; then
                            echo "  Port $port: LISTENING"
                        else
                            echo "  Port $port: closed"
                        fi
                    done <<< "$ports"
                else
                    echo "  No ports configured"
                fi
                echo ""
            fi
        done
    fi

    echo "All listening ports in game range (26000-28000):"
    ss -tuln | grep -E ":(26[0-9][0-9][0-9]|27[0-9][0-9][0-9])" | sed 's/^/  /' || echo "  No game ports active"

# Clean/uninstall a game (stop, remove files)
clean game *options="":
    #!/usr/bin/env bash
    set -euo pipefail

    json_file="{{services_dir}}/{{game}}.json"
    if [[ ! -f "$json_file" ]]; then
        echo "Game '{{game}}' not found."
        exit 1
    fi

    game_name=$(jq -r '.name' "$json_file")
    unit_name=$(jq -r '.unitName' "$json_file")
    game_dir=$(jq -r '.gameDir // empty' "$json_file")

    # Parse options
    clean_user_data=false
    for option in {{options}}; do
        case "$option" in
            --user-data|--all) clean_user_data=true ;;
            --help|-h)
                echo "Usage: just clean <game> [options]"
                echo ""
                echo "Options:"
                echo "  --user-data    Also remove user data (as defined in service registry)"
                echo "  --all          Clean everything (combines all options)"
                echo ""
                echo "Default: Only stops service and removes game installation directory"
                echo ""
                echo "⚠️  WARNING: --user-data will delete game-specific directories and save files!"
                exit 0
                ;;
        esac
    done

    echo "=== Cleaning $game_name ==="
    echo ""
    echo "⚠️  WARNING: This will permanently delete game files and data!"
    echo "   - Game installation directory: $game_dir"
    if [[ "$clean_user_data" == "true" ]]; then
        echo "   - User data (as defined in service registry)"
    fi
    echo ""

    # 1. Stop the service if running
    echo "1. Stopping service..."
    if sudo systemctl is-active --quiet "$unit_name" 2>/dev/null; then
        sudo systemctl stop "$unit_name"
        echo "   ✓ Service stopped"
    else
        echo "   ✓ Service was not running"
    fi

    # 2. Remove game installation directory
    if [[ -n "$game_dir" && "$game_dir" != "null" && -d "$game_dir" ]]; then
        echo "2. Removing game files..."
        echo "   Directory: $game_dir"
        size=$(du -sh "$game_dir" 2>/dev/null | cut -f1 || echo "unknown")
        echo "   Size: $size"

        read -p "   Remove game installation directory? [y/N] " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$game_dir"
            echo "   ✓ Game files removed"
        else
            echo "   ✓ Game files kept"
        fi
    else
        echo "2. Game directory not found or not specified"
    fi

    # 3. Clean user data if requested
    if [[ "$clean_user_data" == "true" ]]; then
        echo "3. Cleaning user data..."
        clean_filters=$(jq -r '.cleanFilters[]? // empty' "$json_file")
        if [[ -n "$clean_filters" ]]; then
            echo "   Files that would be removed:"
            while IFS= read -r filter_path; do
                if [[ -n "$filter_path" && "$filter_path" != "null" ]]; then
                    expanded_path=$(eval echo "$filter_path")
                    if [[ -e "$expanded_path" ]]; then
                        echo "     - $expanded_path"
                    fi
                fi
            done <<< "$clean_filters"

            read -p "   Remove user data? [y/N] " -n 1 -r
            echo ""
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                while IFS= read -r filter_path; do
                    if [[ -n "$filter_path" && "$filter_path" != "null" ]]; then
                        expanded_path=$(eval echo "$filter_path")
                        if [[ -e "$expanded_path" ]]; then
                            rm -rf "$expanded_path"
                            echo "     ✓ Removed: $expanded_path"
                        fi
                    fi
                done <<< "$clean_filters"
                echo "     ✓ User data cleaned"
            else
                echo "     ✓ User data kept"
            fi
        else
            echo "   ✓ No clean filters defined for this game"
        fi
    fi

    echo ""
    echo "=== Cleanup Complete ==="

# Show disk usage for game files
disk:
    #!/usr/bin/env bash
    echo "=== Disk Usage ==="
    echo ""

    total_size=0
    if [[ -d {{services_dir}} ]]; then
        for json_file in {{services_dir}}/*.json; do
            if [[ -f "$json_file" ]]; then
                game_id=$(jq -r '.id' "$json_file")
                game_name=$(jq -r '.name' "$json_file")
                game_dir=$(jq -r '.gameDir // empty' "$json_file")

                if [[ -n "$game_dir" && "$game_dir" != "null" && -d "$game_dir" ]]; then
                    size=$(du -sh "$game_dir" 2>/dev/null | cut -f1 || echo "unknown")
                    size_bytes=$(du -sb "$game_dir" 2>/dev/null | cut -f1 || echo "0")
                    total_size=$((total_size + size_bytes))

                    # Check if marker file exists for download status
                    marker_file="$game_dir/.steamcmd-completed"
                    download_info=""
                    if [[ -f "$marker_file" ]] && jq -e . "$marker_file" >/dev/null 2>&1; then
                        file_count=$(jq -r '.file_count' "$marker_file")
                        last_update=$(jq -r '.last_updated' "$marker_file")
                        download_info=" ($file_count files, updated: $last_update)"
                    fi

                    echo "$game_name ($game_id): $size$download_info"
                    echo "  Path: $game_dir"
                else
                    echo "$game_name ($game_id): not downloaded"
                fi
                echo ""
            fi
        done

        if [[ $total_size -gt 0 ]]; then
            total_human=$(numfmt --to=iec-i --suffix=B $total_size)
            echo "Total game files: $total_human"
        fi
    else
        echo "No games configured."
    fi
```

</details>

### Target Architecture
- **New tool**: Python CLI with Nix flake packaging
- **Package manager**: UV for fast dependency management
- **CLI framework**: Typer with Rich for beautiful output
- **Validation**: Pydantic models for JSON configs
- **Distribution**: Nix flake for NixOS integration

## Technical Requirements

### Core Technologies
- **Python 3.11+** with modern type hints
- **UV** for package management (`pyproject.toml`)
- **Typer[all]** for CLI with autocompletion
- **Rich** for progress bars, colors, and beautiful terminal output
- **Pydantic v2** for JSON schema validation and parsing
- **Nix flake** for packaging and distribution

### System Integration
- **SteamCMD**: Direct execution for game downloads (no systemd wrapper)
- **systemd**: Use `systemd-run` for transient game services
- **JSON configs**: Service registry in `~/services/*.json`
- **JSON markers**: Download completion tracking in `.steamcmd-completed`

## Project Structure

```
gameserver-manager/
├── README.md
├── pyproject.toml              # UV project configuration
├── uv.lock                     # Locked dependencies
├── flake.nix                   # Nix flake for packaging
├── flake.lock                  # Nix flake lock file
├── gameserver/
│   ├── __init__.py
│   ├── cli.py                  # Main Typer application
│   ├── models.py               # Pydantic models for configs/markers
│   ├── exceptions.py           # Custom exception classes
│   └── services/
│       ├── __init__.py
│       ├── steam.py            # SteamCMD operations
│       ├── systemd.py          # systemd service management
│       ├── registry.py         # Service registry handling
│       └── validation.py       # File/download validation
├── tests/
│   ├── __init__.py
│   ├── test_steam.py
│   ├── test_systemd.py
│   └── fixtures/
│       └── sample-configs.json
└── docs/
    ├── installation.md
    ├── usage.md
    └── configuration.md
```

## Command Interface (preserve existing UX)

The CLI should maintain the same command structure as the current justfile:

```bash
gameserver status                    # Show all services status
gameserver list                      # List available games
gameserver info <game>               # Show detailed game info
gameserver update <game> [--force]   # Update/download game files
gameserver start <game>              # Start game service  
gameserver stop <game>               # Stop game service
gameserver restart <game>            # Restart game service
gameserver clean <game> [--user-data] # Clean/uninstall game
gameserver logs <game> [args...]     # Show service logs
gameserver network                   # Show network status
gameserver disk                      # Show disk usage
```

## Data Models (Pydantic)

### Service Registry Schema (`~/services/*.json`)
```json
{
  "id": "7dtd",
  "name": "7 Days to Die",
  "description": "Survival game server",
  "unitName": "game-7dtd",
  "steamApp": "294420_stable",
  "gameDir": "/home/sevendtd/games/steam/7dtd",
  "executable": "/home/sevendtd/games/steam/7dtd/7DaysToDieServer.x86_64",
  "user": "sevendtd",
  "group": "sevendtd",
  "workingDirectory": "/home/sevendtd/games/steam/7dtd",
  "args": ["-configfile=serverconfig.xml", "-logfile=logs/output.log"],
  "environment": {
    "LD_LIBRARY_PATH": "/home/sevendtd/games/steam/7dtd"
  },
  "ports": [26900, 26901, 26902],
  "configFile": "/home/sevendtd/games/steam/7dtd/serverconfig.xml",
  "logDir": "/home/sevendtd/games/steam/7dtd/logs",
  "cleanFilters": [
    "/home/sevendtd/.local/share/7DaysToDie"
  ]
}
```

### Download Marker Schema (`.steamcmd-completed`)
```json
{
  "timestamp": "2024-01-01T10:00:00+00:00",
  "steam_app": "294420_stable",
  "app_id": "294420",
  "beta_branch": "stable",
  "download_status": "success",
  "game_dir": "/home/sevendtd/games/steam/7dtd",
  "file_count": 1247,
  "total_size": "2.1G",
  "validation_status": "passed",
  "last_updated": "2024-01-01T10:00:00+00:00"
}
```

## Key Implementation Details

### SteamCMD Integration
- **Direct execution**: No systemd service wrapper
- **Progress tracking**: Use Rich progress bars during downloads
- **Error handling**: Proper exception handling with user-friendly messages
- **Beta branch support**: Parse `steamApp` format `appid_branch_password`
- **NixOS compatibility**: Use `patchelf` to fix executables after download

### systemd Integration  
- **Transient services**: Use `systemd-run` for game servers
- **Service validation**: Check if service exists before operations
- **Log integration**: Seamless `journalctl` integration
- **Status monitoring**: Real-time service status checking

### File Operations
- **Atomic operations**: Safe JSON file writing
- **Path validation**: Ensure paths exist and are accessible  
- **Permission handling**: Proper user/group permission management
- **Cleanup operations**: Safe removal with confirmation prompts

### Error Handling
- **Custom exceptions**: Game-specific error types
- **Rich error display**: Beautiful error formatting with Rich
- **Recovery suggestions**: Actionable error messages
- **Logging**: Structured logging for debugging

## Configuration Files

### `pyproject.toml`
```toml
[project]
name = "gameserver-manager"
version = "0.1.0"
description = "Modern CLI tool for managing game servers on NixOS"
authors = [{name = "Your Name", email = "your@email.com"}]
readme = "README.md"
license = {file = "LICENSE"}
requires-python = ">=3.11"
dependencies = [
    "typer[all]>=0.9.0",
    "rich>=13.0.0", 
    "pydantic>=2.0.0",
]

[project.scripts]
gameserver = "gameserver.cli:app"

[project.urls]
Homepage = "https://github.com/yourusername/gameserver-manager"
Repository = "https://github.com/yourusername/gameserver-manager"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "mypy>=1.0.0",
    "ruff>=0.1.0",
]
```

### `flake.nix`
```nix
{
  description = "Modern CLI tool for managing game servers on NixOS";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python311;
      in
      {
        packages.default = python.pkgs.buildPythonApplication {
          pname = "gameserver-manager";
          version = "0.1.0";
          src = ./.;
          pyproject = true;
          
          nativeBuildInputs = with python.pkgs; [
            hatchling
          ];
          
          propagatedBuildInputs = with python.pkgs; [
            typer
            rich
            pydantic
          ];

          # Ensure steamcmd and systemd tools are available at runtime
          makeWrapperArgs = [
            "--prefix PATH : ${pkgs.lib.makeBinPath [ 
              pkgs.steamcmd 
              pkgs.systemd 
              pkgs.patchelf
              pkgs.jq
            ]}"
          ];

          meta = with pkgs.lib; {
            description = "Modern CLI tool for managing game servers on NixOS";
            homepage = "https://github.com/yourusername/gameserver-manager";
            license = licenses.mit;
            maintainers = with maintainers; [ /* your name */ ];
          };
        };

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            python
            uv
            steamcmd
            systemd
            patchelf
            jq
          ];
          
          shellHook = ''
            echo "Development environment for gameserver-manager"
            echo "Run 'uv sync' to install dependencies"
          '';
        };
      });
}
```

## Implementation Phases

### Phase 1: Core Structure
1. Initialize UV project with `pyproject.toml`
2. Create Pydantic models for service configs and markers
3. Implement basic Typer CLI structure with all commands
4. Create Nix flake for packaging

### Phase 2: Service Management
1. Implement service registry loading and validation
2. Add systemd integration (start/stop/restart/status)
3. Implement log viewing with journalctl integration
4. Add network status checking

### Phase 3: SteamCMD Integration
1. Implement direct steamcmd execution with Rich progress bars
2. Add download validation and marker creation
3. Handle beta branches and authentication
4. Add NixOS-specific patchelf integration

### Phase 4: Advanced Features  
1. Implement clean/uninstall functionality
2. Add disk usage reporting
3. Implement comprehensive error handling
4. Add shell completion generation

### Phase 5: Polish & Documentation
1. Add comprehensive tests
2. Create detailed documentation
3. Add examples and usage guides
4. Optimize performance and UX

## Expected Benefits

### For Users
- **Intuitive CLI**: Type-safe commands with autocompletion
- **Rich output**: Progress bars, colors, and clear status information  
- **Better errors**: Actionable error messages with recovery suggestions
- **Reliable operations**: Proper error handling and atomic operations

### For Developers  
- **Type safety**: Full mypy compliance with Pydantic models
- **Testable**: Unit tests for all core functionality
- **Maintainable**: Clean separation of concerns
- **Extensible**: Easy to add new games and features

### For NixOS Community
- **Reusable**: Others can use with `nix run github:you/gameserver-manager`
- **Best practices**: Modern Python packaging with Nix integration
- **Documentation**: Complete example of Python CLI + Nix flake

## Integration with Existing NixOS Config

After implementation, the existing justfile would be replaced with:

```bash
# Simple justfile wrapper (optional)
# All commands delegate to the Python CLI

status:
    gameserver status

update game *options="":  
    gameserver update {{game}} {{options}}

start game:
    gameserver start {{game}}

# ... etc for all commands
```

And the NixOS config would import the package:

```nix
# hosts/common/optional/gaming/serving/default.nix
{ inputs, pkgs, ... }: {
  environment.systemPackages = [
    inputs.gameserver-manager.packages.${pkgs.system}.default
  ];
}
```

## Success Criteria

- [ ] All existing justfile commands work identically
- [ ] Type-safe operation with mypy compliance  
- [ ] Rich terminal output with progress bars
- [ ] Comprehensive error handling with recovery suggestions
- [ ] Unit tests covering core functionality
- [ ] Nix flake builds successfully
- [ ] Integration works with existing service configs
- [ ] Performance equal or better than bash version
- [ ] Documentation complete with examples

## Notes

This specification preserves all existing functionality while modernizing the implementation. The goal is a drop-in replacement that's more maintainable, testable, and user-friendly than the current bash-heavy justfile approach.
