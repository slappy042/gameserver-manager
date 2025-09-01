# Configuration Guide

## Service Registry

Game configurations are stored as JSON files in the `~/services/` directory. Each game has its own `.json` file.

## Service Configuration Schema

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

## Field Descriptions

### Required Fields

- **`id`** (string): Unique identifier for the game. Used in CLI commands.
- **`name`** (string): Human-readable game name for display.
- **`description`** (string): Brief description of the game/server.
- **`unitName`** (string): systemd unit name (should be unique).
- **`gameDir`** (string): Directory where game files are installed.
- **`executable`** (string): Full path to the game server executable.
- **`user`** (string): System user to run the service as.

### Optional Fields

- **`steamApp`** (string): Steam app ID with optional beta branch.
  - Format: `appid` or `appid_branch` or `appid_branch_password`
  - Examples: `"294420"`, `"294420_experimental"`, `"294420_beta_secret123"`
- **`group`** (string): System group (defaults to `user` if not specified).
- **`workingDirectory`** (string): Working directory for the service.
- **`args`** (array): Command line arguments for the executable.
- **`environment`** (object): Environment variables as key-value pairs.
- **`ports`** (array): List of ports used by the server.
- **`configFile`** (string): Path to the game's main configuration file.
- **`logDir`** (string): Directory where the game stores logs.
- **`cleanFilters`** (array): Paths to remove during cleanup (user data).

## Steam App Configuration

### Standard Steam Apps

For regular Steam apps, use just the app ID:

```json
{
  "steamApp": "294420"
}
```

### Beta Branches

For beta branches, append the branch name:

```json
{
  "steamApp": "294420_experimental"
}
```

### Password-Protected Betas

For password-protected betas:

```json
{
  "steamApp": "294420_experimental_secretpassword"
}
```

### Non-Steam Games

If your game doesn't use Steam, omit the `steamApp` field:

```json
{
  "steamApp": null
}
```

## User and Permissions

### Dedicated Game Users

It's recommended to create dedicated users for each game:

```bash
# Create a dedicated user for the game
sudo useradd -r -s /bin/false -d /home/gameuser gameuser
sudo mkdir -p /home/gameuser
sudo chown gameuser:gameuser /home/gameuser
```

### Directory Structure

Example directory structure for a game:

```
/home/gameuser/
├── games/
│   └── steam/
│       └── gamename/          # gameDir
│           ├── gameserver     # executable
│           ├── config.cfg     # configFile
│           ├── logs/          # logDir
│           └── .steamcmd-completed
└── .local/
    └── share/
        └── GameName/          # cleanFilters
```

## Environment Variables

Common environment variables for games:

```json
{
  "environment": {
    "LD_LIBRARY_PATH": "/home/gameuser/games/steam/gamename",
    "GAME_CONFIG_DIR": "/home/gameuser/.config/gamename",
    "DISPLAY": ":0"
  }
}
```

## Clean Filters

Clean filters specify what to remove during `gameserver clean --user-data`:

```json
{
  "cleanFilters": [
    "/home/gameuser/.local/share/GameName",
    "/home/gameuser/.config/gamename",
    "/tmp/gamename-*"
  ]
}
```

Paths support shell expansion (`~`, `*`, etc.).

## Download Markers

The tool creates `.steamcmd-completed` files to track downloads:

```json
{
  "timestamp": "2024-01-01T10:00:00+00:00",
  "steam_app": "294420_stable",
  "app_id": "294420",
  "beta_branch": "stable",
  "download_status": "success",
  "game_dir": "/home/gameuser/games/steam/gamename",
  "file_count": 1247,
  "total_size": "2.1G",
  "validation_status": "passed",
  "last_updated": "2024-01-01T10:00:00+00:00"
}
```

These files are automatically managed by the tool.

## Example Configurations

### Minecraft Server

```json
{
  "id": "minecraft",
  "name": "Minecraft Server",
  "description": "Vanilla Minecraft server",
  "unitName": "game-minecraft",
  "gameDir": "/home/minecraft/server",
  "executable": "/home/minecraft/server/server.jar",
  "user": "minecraft",
  "args": ["-Xmx2G", "-Xms1G", "-jar", "server.jar", "nogui"],
  "environment": {
    "JAVA_HOME": "/usr/lib/jvm/java-17-openjdk"
  },
  "ports": [25565],
  "configFile": "/home/minecraft/server/server.properties",
  "logDir": "/home/minecraft/server/logs"
}
```

### Terraria Server

```json
{
  "id": "terraria",
  "name": "Terraria Server",
  "description": "Terraria dedicated server",
  "unitName": "game-terraria",
  "steamApp": "105600",
  "gameDir": "/home/terraria/games/steam/terraria",
  "executable": "/home/terraria/games/steam/terraria/TerrariaServer.bin.x86_64",
  "user": "terraria",
  "workingDirectory": "/home/terraria/games/steam/terraria",
  "args": ["-config", "serverconfig.txt"],
  "ports": [7777],
  "configFile": "/home/terraria/games/steam/terraria/serverconfig.txt",
  "cleanFilters": [
    "/home/terraria/.local/share/Terraria"
  ]
}
```

## Validation

The tool validates configurations when loading. Common issues:

- **Missing executable**: Run `gameserver update <game>` to download files.
- **Invalid paths**: Ensure all paths exist and are accessible.
- **Permission issues**: Ensure the specified user can access all paths.
- **Invalid JSON**: Use a JSON validator to check syntax.

## Migration from justfile

To migrate from the existing justfile setup:

1. Copy existing service JSON files to `~/services/`
2. Update any deprecated field names (the tool handles most aliases)
3. Test each game: `gameserver info <game>`
4. Verify functionality: `gameserver status`
