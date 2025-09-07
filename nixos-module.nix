{ config, lib, pkgs, ... }:

with lib;

let
  cfg = config.services.gameserver-manager;
  
  # Import the package from the flake
  gameserver-manager = 
    if cfg.package != null 
    then cfg.package
    else pkgs.gameserver-manager or (throw "gameserver-manager package not found. Please add overlay or set services.gameserver-manager.package");
    
in {
  options.services.gameserver-manager = {
    enable = mkEnableOption "gameserver-manager service for managing game servers";
    
    package = mkOption {
      type = types.nullOr types.package;
      default = null;
      description = "The gameserver-manager package to use. Defaults to pkgs.gameserver-manager if available.";
    };
    
    gamesDir = mkOption {
      type = types.path; 
      default = "\${HOME}/games";
      description = "Directory where game files are stored (defaults to \$HOME/games)";
    };
    
    steamcmd = {
      enable = mkEnableOption "SteamCMD integration";
    };
  };
  
  config = mkIf cfg.enable {
    # Ensure required system packages are available
    environment.systemPackages = [ 
      gameserver-manager 
      pkgs.systemd  # For systemctl commands
    ] ++ optionals cfg.steamcmd.enable [
      pkgs.steamcmd
    ];
    
    # Create required directories (using environment variables for user paths)
    systemd.tmpfiles.rules = [
      "d %h/games/services 0755 - - -"
      "d %h/games 0755 - - -"
      "d /var/log/gameserver-manager 0755 - - -"
    ];
    
    # Add gameserver-manager to PATH for all users
    environment.variables = {
      GAMESERVER_SERVICES_DIR = "\${HOME}/games/services";
      GAMESERVER_GAMES_DIR = "\${HOME}/games";
    };
    # Optional: SteamCMD setup
    programs.steam.enable = mkIf cfg.steamcmd.enable true;
    
    # Add shell completion
    environment.pathsToLink = [ "/share/bash-completion" "/share/zsh" "/share/fish" ];
  };
  
  meta = {
    maintainers = with lib.maintainers; [ /* add maintainer info */ ];
    doc = ./nixos-module.md;
  };
}
