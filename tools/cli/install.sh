#!/bin/sh
# Explicit developer installation; ordinary codecraft commands never invoke Cargo.
set -eu
repo=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$repo"
codecraft_host_target=$(rustc -vV | sed -n 's/^host: //p')
[ -n "$codecraft_host_target" ] || { printf 'Cannot determine Rust host target.\n' >&2; exit 1; }
cargo build --release --locked --package codecraft --target-dir .codecraft/cargo --target "$codecraft_host_target"
install_dir=${CODECRAFT_BIN_DIR:-"$HOME/.local/bin"}
mkdir -p "$install_dir"
install -m 755 ".codecraft/cargo/$codecraft_host_target/release/codecraft" "$install_dir/codecraft"
printf 'Installed %s/codecraft. Add this directory to PATH.\n' "$install_dir"
