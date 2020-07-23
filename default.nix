{ pkgs ? import (
    builtins.fetchTarball {
      name = "nixos-20.03-2020-07-18";
      url = "https://github.com/nixos/nixpkgs/archive/2b417708c282d84316366f4125b00b29c49df10f.tar.gz";
      # Hash obtained using `nix-prefetch-url --unpack <url>`
      sha256 = "0426qaxw09h0kkn5zwh126hfb2j12j5xan6ijvv2c905pqi401zq";
    }
  ) {}
}:
let
  machnix = import (
    builtins.fetchGit {
      url = "https://github.com/DavHau/mach-nix/";
      ref = "2.1.0";
    }
  );
in
machnix.buildPythonApplication rec {
  pname = "discord-talkingstick-bot";
  version = "0.1.0";
  src = builtins.path { path = ./.; name = pname; };
  requirements = builtins.readFile "${src}/requirements.in";

  checkPhase = ''
    python -m unittest tests/*.py
  '';
}
