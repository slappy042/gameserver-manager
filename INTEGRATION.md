# Gameserver Manager Integration Examples

This document shows different ways to integrate gameserver-manager into your NixOS system.

## Method 1: Direct Flake Usage (Simplest)

```nix
# flake.nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    gameserver-manager.url = "github:slappy042/gameserver-manager";
  };
  
  outputs = { nixpkgs, gameserver-manager, ... }: {
    nixosConfigurations.yourhostname = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      modules = [
        {
          environment.systemPackages = [ 
            gameserver-manager.packages.x86_64-linux.default 
          ];
        }
      ];
    };
  };
}
```

## Method 2: Using the Overlay (More Flexible)

```nix
# flake.nix  
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    gameserver-manager.url = "github:slappy042/gameserver-manager";
  };
  
  outputs = { nixpkgs, gameserver-manager, ... }: {
    nixosConfigurations.yourhostname = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      modules = [
        {
          nixpkgs.overlays = [ gameserver-manager.overlays.default ];
          
          # Now available as regular package
          environment.systemPackages = with pkgs; [ 
            gameserver-manager 
            # Can also customize it
            (gameserver-manager.override { 
              # Override dependencies if needed
            })
          ];
        }
      ];
    };
  };
}
```

## Method 3: Full NixOS Module Integration (Recommended)

```nix
# flake.nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    gameserver-manager.url = "github:slappy042/gameserver-manager";
  };
  
  outputs = { nixpkgs, gameserver-manager, ... }: {
    nixosConfigurations.yourhostname = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      modules = [
        # Include the NixOS module
        gameserver-manager.nixosModules.default
        
        {
          # Enable the service
          services.gameserver-manager = {
            enable = true;
            steamcmd.enable = true;
            openFirewall = true;
            
            # Optional customization
            gamesDir = "/srv/gameserver/games";
            servicesDir = "/etc/gameserver/services";
          };
          
          # The package is automatically available
          environment.systemPackages = with pkgs; [
            # Other packages...
          ];
        }
      ];
    };
  };
}
```

## Method 4: Legacy Nix (No Flakes)

```nix
# configuration.nix
{ config, pkgs, ... }:

let
  gameserver-manager-src = builtins.fetchGit {
    url = "https://github.com/slappy042/gameserver-manager";
    ref = "main";
  };
  
  gameserver-manager-overlay = import "${gameserver-manager-src}/overlay.nix";
  
in {
  nixpkgs.overlays = [ gameserver-manager-overlay ];
  
  environment.systemPackages = with pkgs; [
    gameserver-manager
  ];
  
  # Optional: import and use the module  
  imports = [ "${gameserver-manager-src}/nixos-module.nix" ];
  
  services.gameserver-manager = {
    enable = true;
    steamcmd.enable = true;
  };
}
```

## Usage After Installation

Once installed via any method above:

```bash
# Check status of all game servers
gameserver status

# List available games  
gameserver list

# Download/update a game
gameserver update minecraft-server

# Start a game server
gameserver start minecraft-server

# View logs
gameserver logs minecraft-server
```

## Why Use Each Method?

### Direct Flake Usage
- **Pros**: Simple, explicit, no extra configuration
- **Cons**: Can't easily customize or override
- **Best for**: Quick testing, simple deployments

### Overlay  
- **Pros**: Integrates with existing package management, allows customization
- **Cons**: Slightly more complex
- **Best for**: When you want to treat it like any other package

### NixOS Module
- **Pros**: Full system integration, automatic user/permission setup, proper service management
- **Cons**: More opinionated about system configuration  
- **Best for**: Production deployments, managed servers

### Legacy Nix
- **Pros**: Works without flakes
- **Cons**: More verbose, harder to update
- **Best for**: Existing non-flake systems
