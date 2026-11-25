# Rust CLI and runtime ownership

The creator entry is the standalone `codecraft` binary (CLI contract 4). Discovery,
Device Markdown parsing, context, project export, source locks and packaging run
in Rust. These commands do not invoke Python, Cargo, platform installers or cloud
services. Data is read from `--root` (the current directory by default), not
compiled into the executable.

## Install and update

Download the appropriate executable from a completed **CodeCraft CLI binaries**
workflow artifact, or build locally once:

```sh
sh tools/cli/install.sh
# Add ~/.local/bin to PATH, or set CODECRAFT_BIN_DIR before installation.
codecraft --version
codecraft --root /path/to/codecraft-ai-hardware discover
```

Windows source installations use `tools/cli/install.ps1`; the default destination
is `%LOCALAPPDATA%/CodeCraft/bin`. A downloaded executable needs neither Rust nor
Python. Source installations require Cargo and a native linker. No binary release
is published automatically by this repository.

Run the installer again after changing Rust implementation/dependencies. It uses
Cargo's incremental release build; normal `codecraft` invocations never run Cargo.
Device data, application code, Markdown and maintenance Python updates do not
rebuild the CLI. Rust sources, Cargo manifests/lock, compiler/configuration or a
new operating-system/architecture target may require a build. CI caches binaries
using those inputs, separately from hardware/data changes. It does not include
Git commit IDs, device files or documentation in the binary cache key.

## Project lifecycle

```sh
codecraft new --target esp-idf/reterminal-e1001 --example epd_hello --output projects/my-app
codecraft verify-project projects/my-app
# Only when preparing a native build, activate the declared SDK first:
codecraft lock-project projects/my-app --toolchain
codecraft build-project projects/my-app
```

Creation and ordinary relocking do not probe the SDK. `--toolchain` explicitly
records the active environment. A missing toolchain prevents a build; it does not
prevent authoring. Existing toolchain identity is preserved during source-only
relocking when the declared requirement is unchanged. No command silently
installs tools or flashes a board.

Project profiles, source graphs and locks use schema 4. The lock separately stores
original import provenance, current source hashes, declared/resolved toolchain
and CLI version/contract/binary hash. A different CLI can inspect source integrity;
building requires reviewing and relocking its identity. Source edits require
relocking but never rebuilding the CLI. Custom application AGENTS rules outside
the generated region survive relocking.

Schema 3 Python-runtime exports are not reinterpreted as schema 4 projects. Keep
their original tooling to reproduce them, or create a fresh schema 4 export and
review/copy application changes. Never rewrite their original evidence or import
hashes. Target schema 3 and authored Device schema 5 are unchanged.

## Python boundaries

Native C/C++ exports contain no CodeCraft Python runtime, Cargo project or Rust
source. Platform `application_inputs` declares portable guidance and native
helpers; maintenance `runtime` describes repository verification dependencies.
Missing declared inputs fail export rather than being filtered out by suffix.

Python remains legitimate in the following explicitly selected scopes:

- ESP-IDF's own SDK tooling, activated before native build/image operations.
- Linux applications whose native example itself is written in Python.
- Explicitly selected standalone cloud Skills whose client is Python. Selection
  verifies and copies their complete released package without executing it.
- Repository maintenance: `codecraft maintenance <command>`, including generation,
  host tests, release tooling and historical/reference conformance fixtures.
  These tools are not exported into creator applications.

The Python conformance backend maintains its own schema 3 reference fixtures;
those are internal audit inputs, not creator exports. `codecraft validate --static`
runs the repository static/host checks. Rust integration tests run through
`cargo test --locked --package codecraft`; their source lives in tests/tools/cli/.

## Evidence compatibility

Rust context currently reports hardware verification as `unknown`; it does not
promote build or physical evidence from the Python reference registry. That
repository-only registry still validates its own schema 3 source graph. Rust
schema 4 application receipts must not be submitted as if they were reference
registry records. Migrating evidence registration/promotion requires an explicit
compiled-CLI identity binding; it is not implemented by this creator migration.
Historical observations and source digests remain unchanged.
