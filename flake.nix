{
  description = "A CLI tool for managing Nix-defined game services";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs {
        inherit system;
        config.allowUnfree = true;
      };
      python = pkgs.python313;
    in
    {
      packages.${system} = {
        default = python.pkgs.buildPythonApplication {
          pname = "gameserver-manager";
          version = "0.1.0";
          src = ./.;
          
          pyproject = true;
          
          build-system = with python.pkgs; [
            hatchling
          ];
          
          dependencies = with python.pkgs; [
            typer
            rich
            pydantic
            psutil
            requests
          ];
          
          # Runtime system dependencies
          propagatedBuildInputs = with pkgs; [
            steamcmd
            systemd
            patchelf
            gnutar
            unzip
          ];
          
          pythonImportsCheck = [ "gameserver" ];
          
          meta = with pkgs.lib; {
            description = "Modern CLI tool for managing game servers on NixOS";
            homepage = "https://github.com/slappy042/gameserver-manager";
            license = licenses.mit;
            platforms = [ "x86_64-linux" ];
            mainProgram = "gameserver-manager";
          };
        };
        
        gameserver-manager = self.packages.${system}.default;
      };

      devShells.${system}.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          python
          uv
          just
          steamcmd
          systemd
          ruff
          mypy
          patchelf
          gnutar
          unzip
          curl
        ] ++ (with python.pkgs; [
          pytest
          pytest-cov
          black
          isort
        ]);
        
        shellHook = ''
          echo "🎮 Gameserver Manager Development Environment"
          echo "Python: ${python.version}"
          echo "Available commands:"
          echo "  just --list     - See all available commands"
          echo "  uv run gameserver-manager --help  - Run the CLI tool"
          mkdir -p ./services
        '';
      };

      apps.${system}.default = {
        type = "app";
        program = "${self.packages.${system}.default}/bin/gameserver-manager";
      };

      # System-agnostic outputs
      overlays.default = import ./overlay.nix;
      
      nixosModules = 
        let
          module = { config, lib, pkgs, ... }: 
            import ./nixos-module.nix { 
              inherit config lib pkgs; 
              gameserver-manager-package = self.packages.${system}.default; 
            };
        in {
          default = module;
          gameserver-manager = module;
        };
    };
}
