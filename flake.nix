{
  description = "A CLI tool for managing Nix-defined game services";

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
          
          pyproject = true;
          
          build-system = with python.pkgs; [
            hatchling
          ];
          
          dependencies = with python.pkgs; [
            typer
            rich
            pydantic
            # Additional dependencies for full functionality
            psutil          # For process management and system info
            requests        # For potential future web API calls
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
            maintainers = with maintainers; [ /* add your maintainer info here */ ];
            platforms = platforms.linux; # Specifically for Linux/NixOS
            mainProgram = "gameserver";
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
            # Development tools
            ruff          # Fast Python linter and formatter
            mypy          # Type checking
            # Additional system tools that game servers might need
            patchelf      # For fixing NixOS executables
            gnutar        # For extracting game archives
            unzip         # For extracting zip files
            curl          # For downloads
          ] ++ (with python.pkgs; [
            # Python development dependencies
            pytest
            pytest-cov
            black
            isort
          ]);
          
          shellHook = ''
            echo "🎮 Gameserver Manager Development Environment"
            echo "Python: ${python.version}"
            echo "SteamCMD: $(steamcmd --version 2>/dev/null | head -1 || echo 'available')"
            echo ""
            echo "Available commands:"
            echo "  just setup      - Initialize the project"
            echo "  just test       - Run tests"
            echo "  just lint       - Run linting"
            echo "  just --list     - See all available commands"
            echo "  uv run gameserver --help  - Run the CLI tool"
            echo ""
            # Ensure services directory exists for development
            mkdir -p ./services
          '';
        };
        
        apps.default = flake-utils.lib.mkApp {
          drv = gameserver-manager;
        };
      }) // {
      # System-agnostic outputs (overlays and NixOS modules)
      overlays.default = import ./overlay.nix;
      
      nixosModules.default = { pkgs, ... }: 
        import ./nixos-module.nix { 
          inherit pkgs; 
          gameserver-manager-package = gameserver-manager; 
        };
      nixosModules.gameserver-manager = nixosModules.default;
    };
}
