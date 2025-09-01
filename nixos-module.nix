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
    
    servicesDir = mkOption {
      type = types.path;
      default = "/var/lib/gameserver-manager/services";
      description = "Directory containing game service configuration files";
    };
    
    gamesDir = mkOption {
      type = types.path; 
      default = "/var/lib/gameserver-manager/games";
      description = "Directory where game files are stored";
    };
    
    user = mkOption {
      type = types.str;
      default = "gameserver";
      description = "User account for running game servers";
    };
    
    group = mkOption {
      type = types.str;
      default = "gameserver";
      description = "Group for the game server user";
    };
    
    extraGroups = mkOption {
      type = types.listOf types.str;
      default = [];
      description = "Additional groups for the game server user";
    };
    
    openFirewall = mkOption {
      type = types.bool;
      default = false;
      description = "Whether to automatically open firewall ports for configured games";
    };
    
    steamcmd = {
      enable = mkEnableOption "SteamCMD integration";
      
      user = mkOption {
        type = types.str;
        default = cfg.user;
        description = "User for SteamCMD operations";
      };
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
    
    # Create game server user and group
    users.groups.${cfg.group} = {};
    
    users.users.${cfg.user} = {
      isSystemUser = true;
      group = cfg.group;
      extraGroups = cfg.extraGroups;
      home = cfg.gamesDir;
      createHome = true;
      description = "Game server management user";
    };
    
    # Create required directories
    systemd.tmpfiles.rules = [
      "d ${cfg.servicesDir} 0755 ${cfg.user} ${cfg.group} -"
      "d ${cfg.gamesDir} 0755 ${cfg.user} ${cfg.group} -"
      "d /var/log/gameserver-manager 0755 ${cfg.user} ${cfg.group} -"
    ];
    
    # Add gameserver-manager to PATH for all users
    environment.variables = {
      GAMESERVER_SERVICES_DIR = cfg.servicesDir;
      GAMESERVER_GAMES_DIR = cfg.gamesDir;
    };
    
    # Security: Allow game server user to manage systemd services
    security.sudo.extraRules = [{
      users = [ cfg.user ];
      commands = [
        {
          command = "${pkgs.systemd}/bin/systemctl";
          options = [ "NOPASSWD" ];
        }
        {
          command = "${pkgs.systemd}/bin/journalctl";
          options = [ "NOPASSWD" ];  
        }
      ];
    }];
    
    # Optional: SteamCMD setup
    programs.steam.enable = mkIf cfg.steamcmd.enable true;
    
    # Add shell completion
    environment.pathsToLink = [ "/share/bash-completion" "/share/zsh" "/share/fish" ];
    
    # Firewall configuration (if enabled)
    networking.firewall = mkIf cfg.openFirewall {
      # This would need to be populated based on actual game configurations
      # For now, just ensure the framework is there
      allowedTCPPorts = []; 
      allowedUDPPorts = [];
    };
    
    # Create a systemd service for potential background operations
    systemd.services.gameserver-manager-setup = {
      description = "Gameserver Manager Initial Setup";
      wantedBy = [ "multi-user.target" ];
      serviceConfig = {
        Type = "oneshot";
        User = cfg.user;
        Group = cfg.group;
        ExecStart = "${pkgs.coreutils}/bin/mkdir -p ${cfg.servicesDir} ${cfg.gamesDir}";
        RemainAfterExit = true;
      };
    };
  };
  
  meta = {
    maintainers = with lib.maintainers; [ /* add maintainer info */ ];
    doc = ./nixos-module.md;
  };
}
