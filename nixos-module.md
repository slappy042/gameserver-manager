# Gameserver Manager NixOS Module

This NixOS module provides system-level integration for the gameserver-manager tool.

## Usage

Add to your `flake.nix`:

```nix
{
  inputs.gameserver-manager.url = "github:slappy042/gameserver-manager";
  
  outputs = { nixpkgs, gameserver-manager, ... }: {
    nixosConfigurations.yourhostname = nixpkgs.lib.nixosSystem {
      modules = [
        gameserver-manager.nixosModules.default
        {
          services.gameserver-manager = {
            enable = true;
            steamcmd.enable = true;
            openFirewall = true;  # Optional: auto-open ports
          };
        }
      ];
    };
  };
}
```

## Configuration Options

### `services.gameserver-manager.enable`
- **Type**: boolean
- **Default**: false
- **Description**: Enable the gameserver-manager service

### `services.gameserver-manager.servicesDir`
- **Type**: path
- **Default**: "/var/lib/gameserver-manager/services"  
- **Description**: Directory containing game service configuration files

### `services.gameserver-manager.gamesDir`
- **Type**: path
- **Default**: "/var/lib/gameserver-manager/games"
- **Description**: Directory where game files are stored

### `services.gameserver-manager.user`
- **Type**: string
- **Default**: "gameserver"
- **Description**: User account for running game servers

### `services.gameserver-manager.steamcmd.enable`
- **Type**: boolean  
- **Default**: false
- **Description**: Enable SteamCMD integration and Steam support

### `services.gameserver-manager.openFirewall`
- **Type**: boolean
- **Default**: false
- **Description**: Automatically open firewall ports for configured games

## What the Module Provides

- **System User**: Creates a dedicated `gameserver` user and group
- **Directories**: Sets up required directories with proper permissions
- **Permissions**: Configures sudo access for systemd service management
- **Environment**: Sets up environment variables for the tool
- **SteamCMD**: Optional integration with Steam for downloading games
- **Firewall**: Optional automatic firewall configuration

## Example Full Configuration

```nix
services.gameserver-manager = {
  enable = true;
  
  # Custom directories
  servicesDir = "/etc/gameserver/services";
  gamesDir = "/srv/games";
  
  # Custom user
  user = "games";
  group = "games";
  extraGroups = [ "audio" "video" ];  # If games need these
  
  # Enable Steam support
  steamcmd.enable = true;
  
  # Auto-configure firewall
  openFirewall = true;
};
```

## Security Considerations

The module grants the gameserver user `sudo` access to `systemctl` and `journalctl` commands without a password. This is necessary for managing transient systemd services but should be considered in your security model.

## Directory Structure

After enabling, you'll have:

```
/var/lib/gameserver-manager/
├── services/          # Game configuration files
├── games/            # Game installation directories
└── logs/             # Game server logs
```
