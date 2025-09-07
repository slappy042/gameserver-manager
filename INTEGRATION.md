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
            steamcmd.enable = true;  # Optional: enable Steam integration
            
            # Optional: override default directory (defaults to $HOME/games)
            # gamesDir = "/srv/games";
          };
          
          # Required: Manual firewall configuration for your games
          networking.firewall = {
            allowedTCPPorts = [ 26900 26901 26902 25565 ];  # Your game ports
            allowedUDPPorts = [ 26900 26901 26902 25565 ];  # Usually same as TCP
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

### How the Module Works

The NixOS module automatically:
- Sets up environment variables pointing to `$HOME/games` and `$HOME/games/services`
- Creates directory structure in each user's home directory when they first use the tool
- Optionally enables SteamCMD integration system-wide

No user management is required - the tool works with any user's home directory.

### Manual Firewall Configuration (Required)

The module does not automatically configure firewall ports, as this should be declarative. Configure firewall ports explicitly in your NixOS configuration:
```nix
networking.firewall = {
  allowedTCPPorts = [ 26900 26901 26902 ];  # Your game ports
  allowedUDPPorts = [ 26900 26901 26902 ];  # Your game ports
};
```

For a more organized approach, define your game servers as separate NixOS modules that include both the game configuration and required firewall ports.

### Important: This Tool Uses Declarative Game Configurations

**This is not a general-purpose game installer** - you cannot run `gameserver-manager install <random-steam-game>`. Instead, this tool uses **declarative Nix modules** to define game services.

**Proper workflow using Nix modules:**

1. **Create a Nix module** for your game (like `games/valheim.nix`)
2. **The module declaratively defines** the game service configuration
3. **NixOS rebuild generates** the JSON service files automatically
4. **Then use the CLI tools** to manage the declared games

**Example game module:**
```nix
# games/valheim.nix
{ config, lib, pkgs, ... }:
let
  gamingLib = import ./lib.nix { inherit lib config; };
  gameDir = "\${HOME}/games/valheim";
in
{
  # Register the game service declaratively
  imports = [
    (gamingLib.registerGameService {
      id = "valheim";
      name = "Valheim Server";
      description = "Viking survival dedicated server";
      steamApp = "896660";
      gameDir = gameDir;
      executable = "${gameDir}/valheim_server.x86_64";
      args = [ "-name" "MyServer" "-port" "2456" ];
      ports = [ 2456 2457 2458 ];
    })
  ];
  
  # Firewall configuration
  networking.firewall = {
    allowedTCPPorts = [ 2456 ];
    allowedUDPPorts = [ 2456 2457 2458 ];
  };
}
```

**Then in your main config:**
```nix
imports = [ ./games/valheim.nix ];
```

**After rebuild, use the CLI:**
```bash
gameserver-manager update valheim    # Downloads the game
gameserver-manager start valheim     # Starts the server
gameserver-manager status           # Shows all configured games
```

See `docs/examples/7days-to-die.nix` for a complete real-world example.

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

## Debugging and Development on Live Systems

### Method 1: Quick Local Override (Fastest for Hot Fixes)

If you need to quickly test a fix on a live system:

```bash
# On the live system, clone your repo with fixes
git clone https://github.com/slappy042/gameserver-manager /tmp/gameserver-debug
cd /tmp/gameserver-debug

# Install in development mode (editable install)
nix develop
uv pip install -e .

# Test your fixes directly
uv run gameserver-manager status

# Or run with full path to avoid conflicts
/tmp/gameserver-debug/.venv/bin/gameserver-manager status
```

### Method 2: Overlay Override (Proper Testing)

Create a local overlay that points to your development version:

```nix
# local-debug.nix
final: prev: {
  gameserver-manager = prev.gameserver-manager.overrideAttrs (oldAttrs: {
    src = /path/to/your/local/gameserver-manager;
    # Or point to a specific git commit/branch
    # src = builtins.fetchGit {
    #   url = "https://github.com/slappy042/gameserver-manager";
    #   ref = "debug-branch";
    # };
  });
}
```

Then add to your system configuration:

```nix
# configuration.nix or in your flake
{
  nixpkgs.overlays = [ 
    gameserver-manager.overlays.default
    (import ./local-debug.nix)  # This overrides the original
  ];
  
  # Rebuild system
  # sudo nixos-rebuild switch
}
```

### Method 3: Development Flake Override (Best Practice)

Create a development flake that overrides the production one:

```nix
# debug-flake.nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    gameserver-manager.url = "github:slappy042/gameserver-manager";
    # Your development version
    gameserver-manager-dev.url = "path:/home/user/gameserver-manager-dev";
  };
  
  outputs = { nixpkgs, gameserver-manager, gameserver-manager-dev, ... }: {
    nixosConfigurations.yourhostname = nixpkgs.lib.nixosSystem {
      modules = [
        gameserver-manager.nixosModules.default
        {
          # Override the package in the module
          services.gameserver-manager.package = gameserver-manager-dev.packages.x86_64-linux.default;
          
          # Or override via overlay
          nixpkgs.overlays = [ 
            (final: prev: {
              gameserver-manager = gameserver-manager-dev.packages.x86_64-linux.default;
            })
          ];
        }
      ];
    };
  };
}
```

### Method 4: Live Debugging with Nix Shell

Debug without changing the system configuration:

```bash
# Enter a development shell with your debug version
nix develop /path/to/your/debug/gameserver-manager

# Or from git
nix develop github:slappy042/gameserver-manager/debug-branch

# Now you have both versions available:
which gameserver          # System version
which uv                  # Development tools

# Run your debug version
uv run python -m gameserver status

# Debug with more verbose output
uv run python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from gameserver.cli import app
app()
"
```

### Method 5: Container-Based Debugging

Use a Nix container for isolated testing:

```nix
# debug-container.nix
{ pkgs, ... }:
{
  containers.gameserver-debug = {
    autoStart = false;
    config = { config, pkgs, ... }: {
      services.gameserver-manager = {
        enable = true;
        package = pkgs.callPackage /path/to/your/debug/version {};
      };
      
      # Bind mount the services directory for testing
      fileSystems."/var/lib/gameserver-manager" = {
        device = "/host/gameserver-data";
        fsType = "none";
        options = [ "bind" ];
      };
    };
  };
}
```

Start debugging container:
```bash
sudo nixos-container start gameserver-debug
sudo nixos-container root-login gameserver-debug
```

### Method 6: Rollback Safety

Always prepare for rollback when debugging production:

```bash
# Before making changes, note current generation
sudo nix-env --list-generations --profile /nix/var/nix/profiles/system

# After your debug changes, if things break:
sudo nixos-rebuild switch --rollback

# Or rollback to specific generation
sudo nixos-rebuild switch --switch-generation 42
```

### Method 7: Remote Development

Debug from your development machine:

```bash
# On your dev machine, build the debug version
nix build .#gameserver-manager

# Copy to production system  
nix copy --to ssh://production-server ./result

# On production, temporarily override
export PATH="/nix/store/debug-version/bin:$PATH"
gameserver-manager status
```

### Method 8: Live System Logging

Add extensive logging for production debugging:

```nix
# In your NixOS config
{
  services.gameserver-manager = {
    enable = true;
  };
  
  # Enable debug logging
  environment.variables = {
    GAMESERVER_LOG_LEVEL = "DEBUG";
    GAMESERVER_DEBUG = "1";
  };
  
  # Ensure logs go to journal
  services.journald.extraConfig = ''
    MaxRetentionSec=7day
  '';
}
```

Then monitor logs:
```bash
# Follow gameserver logs in real-time
journalctl -f -u gameserver-manager-*

# Or search for specific errors
journalctl -u gameserver-manager-* --since "1 hour ago" | grep ERROR
```

### Best Practices for Production Debugging

1. **Always test in staging first** - Use method 5 (containers) to replicate production
2. **Use feature flags** - Add debug options that can be enabled without code changes
3. **Maintain logging** - Ensure your CLI has verbose logging options
4. **Keep backups** - Back up game data before testing fixes
5. **Document the process** - Keep notes of what you tried for future reference

### Example Debug Session

```bash
# 1. Quick assessment - what's broken?
gameserver-manager status
journalctl -u gameserver-manager-* --since "10 minutes ago"

# 2. Set up debug environment
nix develop github:slappy042/gameserver-manager/main

# 3. Test fix locally first
uv run gameserver-manager --debug status

# 4. If working, apply via overlay override
# (add local-debug.nix as shown above)

# 5. Rebuild system with debug version
sudo nixos-rebuild switch

# 6. Test fix
gameserver-manager status

# 7. If working, push fix and update system to use official version
# If broken, rollback immediately
sudo nixos-rebuild switch --rollback
```
