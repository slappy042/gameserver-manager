final: prev: {
  gameserver-manager = final.python3.pkgs.buildPythonApplication {
    pname = "gameserver-manager";
    version = "0.1.0";
    src = ./.;
    
    build-system = with final.python3.pkgs; [
      hatchling
    ];
    
    dependencies = with final.python3.pkgs; [
      typer
      rich
      pydantic
      psutil
      requests
    ];
    
    # Runtime system dependencies
    propagatedBuildInputs = with final; [
      steamcmd
      systemd
      patchelf
      gnutar
      unzip
    ];
    
    pythonImportsCheck = [ "gameserver" ];
    
    meta = with final.lib; {
      description = "Modern CLI tool for managing game servers on NixOS";
      homepage = "https://github.com/slappy042/gameserver-manager";
      license = licenses.mit;
      maintainers = with maintainers; [ /* add your maintainer info here */ ];
      platforms = platforms.linux;
      mainProgram = "gameserver-manager";
    };
  };
}
