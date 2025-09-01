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
        python = pkgs.python313;
        
        gameserver-manager = python.pkgs.buildPythonApplication {
          pname = "gameserver-manager";
          version = "0.1.0";
          src = ./.;
          
          build-system = with python.pkgs; [
            hatchling
          ];
          
          dependencies = with python.pkgs; [
            typer
            rich
            pydantic
          ];
          
          pythonImportsCheck = [ "gameserver" ];
          
          meta = with pkgs.lib; {
            description = "Modern CLI tool for managing game servers on NixOS";
            homepage = "https://github.com/slappy042/gameserver-manager";
            license = licenses.mit;
            maintainers = [ ];
          };
        };
      in
      {
        packages.default = gameserver-manager;
        packages.gameserver-manager = gameserver-manager;
        
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            python
            uv
            just
            # System dependencies for game servers
            steamcmd
            systemd
          ];
          
          shellHook = ''
            echo "🎮 Gameserver Manager Development Environment"
            echo "Python: ${python.version}"
            echo "Run 'just setup' to initialize the project"
            echo "Run 'just --list' to see available commands"
          '';
        };
        
        apps.default = flake-utils.lib.mkApp {
          drv = gameserver-manager;
        };
      });
}
