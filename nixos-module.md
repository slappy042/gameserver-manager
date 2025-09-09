# Gameserver Manager NixOS Module {#gameserver-manager-nixos-module}

This NixOS module provides system-level integration for the gameserver-manager tool.

## Usage {#usage}

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
          };
        }
      ];
    };
  };
}
```

## Configuration Options {#configuration-options}

### `services.gameserver-manager.enable` {#services-gameserver-manager-enable}
- **Type**: boolean
- **Default**: false
- **Description**: Enable the gameserver-manager service

### `services.gameserver-manager.gamesDir` {#services-gameserver-manager-gamesdir}
- **Type**: path
- **Default**: "\$HOME/games"
- **Description**: Directory where game files are stored

### `services.gameserver-manager.servicesDir` (read-only) {#services-gameserver-manager-servicesdir}
- **Type**: path (automatically derived)
- **Value**: "\$HOME/games/services"
- **Description**: Directory containing game service configuration files (automatically set to gamesDir/services)

### `services.gameserver-manager.steamcmd.enable` {#services-gameserver-manager-steamcmd-enable}
- **Type**: boolean  
- **Default**: false
- **Description**: Enable SteamCMD integration and Steam support

## What the Module Provides {#what-the-module-provides}

- **Directory Setup**: Sets up required directories with proper permissions in users' home directories
- **Environment**: Sets up environment variables for the tool
- **SteamCMD**: Optional integration with Steam for downloading games  

**Note**: The module uses each user's `$HOME/games` directory automatically. No user management required.

## Example Full Configuration {#example-full-configuration}

```nix
services.gameserver-manager = {
  enable = true;
  
  # Optional: custom games directory (defaults to $HOME/games)
  gamesDir = "/srv/games";
  # Note: servicesDir will automatically be /srv/games/services
  
  # Enable Steam support
  steamcmd.enable = true;
};
```

## Security Considerations {#security-considerations}

The module sets up directory permissions but does not grant any special privileges. Users manage game servers with their own user permissions.

Game servers will run with the permissions of the user who starts them.

## Firewall Configuration {#firewall-configuration}

This module does not automatically configure firewall ports, as NixOS firewall configuration should be declarative. Instead, configure firewall ports in your NixOS configuration alongside your game service definitions.

Example for a 7 Days to Die server:

```nix
{
  services.gameserver-manager.enable = true;
  
  # Configure firewall ports for your specific games
  networking.firewall = {
    allowedTCPPorts = [ 26900 ];
    allowedUDPPorts = [ 26900 26901 26902 ];
  };
}
```

For a more organized approach, define your game servers as separate NixOS modules that include both the game configuration and required firewall ports.

## Directory Structure {#directory-structure}

After enabling, each user will have:

```
$HOME/games/
├── services/          # Game configuration files  
├── <game1>/          # Game installation directories
├── <game2>/          # Game installation directories
└── ...
```

And system logs in:
```
/var/log/gameserver-manager/     # Game server logs
```
