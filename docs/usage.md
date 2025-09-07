# Usage Guide

## Basic Commands

### Status Overview

Show all configured games and their status:

```bash
gameserver-manager status
```

This displays:
- Service status (active/inactive/failed)
- Download status (success/not-downloaded/failed)
- Available commands

### List Games

List all available games with descriptions:

```bash
gameserver-manager list
```

### Game Information

Show detailed information about a specific game:

```bash
gameserver-manager info <game-id>
```

Example:
```bash
gameserver-manager info 7dtd
```

This shows:
- All configuration details
- Current service status
- Download status and statistics
- Port status (listening/closed)

## Game Management

### Downloading Games

Download or update game files using SteamCMD:

```bash
# Download if needed
gameserver-manager update <game-id>

# Force re-download
gameserver-manager update <game-id> --force
```

The tool automatically:
- Checks if download is needed
- Shows download progress
- Fixes executables for NixOS
- Creates completion markers

### Service Control

Start, stop, and restart game services:

```bash
# Start a game server
gameserver-manager start <game-id>

# Stop a game server
gameserver-manager stop <game-id>

# Restart a game server
gameserver-manager restart <game-id>
```

The tool automatically:
- Validates game files before starting
- Uses systemd transient units
- Handles proper user/group permissions
- Sets up environment variables

### Viewing Logs

Show recent logs from a game service:

```bash
# Show last 50 lines
gameserver-manager logs <game-id>

# Show last 100 lines
gameserver-manager logs <game-id> -n 100

# Follow logs in real-time
gameserver-manager logs <game-id> -f

# Show logs since yesterday
gameserver-manager logs <game-id> --since yesterday
```

Additional `journalctl` arguments are passed through.

## Maintenance

### Cleaning Games

Remove game files and optionally user data:

```bash
# Remove only game installation
gameserver-manager clean <game-id>

# Remove game files and user data
gameserver-manager clean <game-id> --user-data

# Remove everything
gameserver-manager clean <game-id> --all
```

The clean command:
1. Stops the service
2. Prompts before removing game files
3. Optionally removes user data (based on cleanFilters)
4. Shows confirmation for each step

### Network Status

Check port status for all games:

```bash
gameserver-manager network
```

This shows:
- Service status for each game
- Port status (listening/closed) for configured ports
- All active ports in the game range (26000-28000)

### Disk Usage

Show disk usage for all game installations:

```bash
gameserver-manager disk
```

This displays:
- Size of each game installation
- File count and last update (if available)
- Total disk usage across all games

## Advanced Usage

### Bash Completion

Enable bash completion for the CLI:

```bash
# Add to your .bashrc
eval "$(_GAMESERVER_COMPLETE=bash_source gameserver)"
```

### Zsh Completion

For zsh users:

```bash
# Add to your .zshrc
eval "$(_GAMESERVER_COMPLETE=zsh_source gameserver)"
```

### Integration with Scripts

The tool returns appropriate exit codes:

```bash
#!/bin/bash

# Check if a game is running
if gameserver-manager info mygame | grep -q "Status: active"; then
    echo "Game is running"
else
    echo "Game is not running"
    gameserver-manager start mygame
fi
```

### JSON Output

For script integration, you can parse the JSON configuration:

```bash
# Get game directory
game_dir=$(jq -r '.gameDir' ~/services/mygame.json)

# Get ports
ports=$(jq -r '.ports[]' ~/services/mygame.json)
```

## Common Workflows

### Setting Up a New Game

1. Create configuration file in `~/services/`:
   ```bash
   vim ~/services/newgame.json
   ```

2. Test configuration:
   ```bash
   gameserver-manager info newgame
   ```

3. Download game files:
   ```bash
   gameserver-manager update newgame
   ```

4. Start the server:
   ```bash
   gameserver-manager start newgame
   ```

5. Check status:
   ```bash
   gameserver-manager status
   ```

### Troubleshooting a Game

1. Check detailed info:
   ```bash
   gameserver-manager info problematic-game
   ```

2. View recent logs:
   ```bash
   gameserver-manager logs problematic-game
   ```

3. Stop and clean download:
   ```bash
   gameserver-manager stop problematic-game
   gameserver-manager update problematic-game --force
   ```

4. Restart:
   ```bash
   gameserver-manager start problematic-game
   ```

### Maintenance Tasks

Weekly maintenance routine:

```bash
# Check status of all games
gameserver-manager status

# Check disk usage
gameserver-manager disk

# Check network status
gameserver-manager network

# Update any games that need it
for game in $(jq -r '.id' ~/services/*.json); do
    gameserver-manager update "$game"
done
```

## Error Handling

The tool provides helpful error messages:

- **Game not found**: Lists available games
- **Download failures**: Suggests checking internet/Steam app ID
- **Permission errors**: Suggests checking user permissions
- **Service failures**: Shows systemd error details

All errors include suggestions for resolution.

## Migration from justfile

The CLI maintains the same command structure as the original justfile:

| justfile command | gameserver-manager command |
|---|---|
| `just status` | `gameserver-manager status` |
| `just list` | `gameserver-manager list` |
| `just info <game>` | `gameserver-manager info <game>` |
| `just update <game>` | `gameserver-manager update <game>` |
| `just start <game>` | `gameserver-manager start <game>` |
| `just stop <game>` | `gameserver-manager stop <game>` |
| `just restart <game>` | `gameserver-manager restart <game>` |
| `just clean <game>` | `gameserver-manager clean <game>` |
| `just logs <game>` | `gameserver-manager logs <game>` |
| `just network` | `gameserver-manager network` |
| `just disk` | `gameserver-manager disk` |

The behavior should be identical, but with improved error handling and output formatting.
