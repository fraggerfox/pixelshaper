{
  description = "pixelshaper — shaping-aware pixel fonts from OpenType donors (uv dev shell)";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        # Native libs the pip/uv-installed wheels dlopen or link at runtime.
        libs = with pkgs; [
          stdenv.cc.cc.lib # libstdc++ — numpy, uharfbuzz, pillow
          zlib # numpy, pillow
          freetype # freetype-py dlopens libfreetype
          libGL # occasionally pulled by pillow-style wheels
        ];
      in
      {
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            python313
            uv
          ];
          shellHook = ''
            export LD_LIBRARY_PATH=${pkgs.lib.makeLibraryPath libs}''${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
            # Use the Nix Python instead of a uv-downloaded portable one, so the
            # venv links against this shell's glibc/LD_LIBRARY_PATH.
            export UV_PYTHON_PREFERENCE=only-system
            export UV_PYTHON=${pkgs.python313}/bin/python3.13
            uv sync 2>/dev/null || true
            source .venv/bin/activate
            echo "pixelshaper dev shell"
            echo "  pixelshaper -C <project> {trace,build,render,status}"
            echo "  (after editing pyproject.toml, run 'uv sync' or use 'uv run')"
          '';
        };
      });
}
