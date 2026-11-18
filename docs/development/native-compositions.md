# ESP-IDF BSP composition and layout

Each ESP-IDF example declares the native implementation it builds. These are
Target/BSP interfaces, not cloud Skill Capabilities. Device facts, pins and
hardware revisions retain their separate ownership.

```text
platforms/esp-idf/
  composition.py                 # metadata/build-output checks
  cmake/bsp.cmake                 # load the example's native composition
  targets/<board>/
    target.json                  # common and per-example source/dependency scope
    bsp/
      CMakeLists.txt             # native component registration stays here
      idf_component.yml          # no unconditional optional managed packages
      include/                   # public headers and sourced pins
      src/                       # implementation and private headers
    examples/<example>/
      CMakeLists.txt             # minimal native build, selected local components
      bsp.cmake                  # selected BSP sources and native requirements
      sdkconfig.defaults
      dependencies.lock
      main/
        CMakeLists.txt           # application and required system components
        idf_component.yml        # this example's managed package dependencies
        main.c
```

## Native build contract

`bsp.cmake` declares two explicit lists: `CODECRAFT_BSP_SOURCES` uses paths
relative to the board BSP, such as `src/bsp_knob.c`; `CODECRAFT_BSP_REQUIRES`
lists its native component requirements. Shared board resources appear in
each composition that needs them. For example, Watcher knob input includes
the I/O expander, and Watcher touch includes display and expander support.
There is no implicit all-peripheral fallback.

The board's component-root `CMakeLists.txt` loads the shared helper, then calls
`idf_component_register` from the BSP directory. Public include visibility is
`include/`; private visibility is `src/`. Registering from the shared helper
instead would change ESP-IDF's relative-path context.

Projects enable `MINIMAL_BUILD`, name only selected local component directories,
and explicitly declare application requirements. PSRAM-enabled configurations
retain `esp_psram`; the Wi-Fi example explicitly retains networking and NVS.
These choices follow the [ESP-IDF v6.0.2 build-system contract](https://docs.espressif.com/projects/esp-idf/en/v6.0.2/esp32s3/api-guides/build-system.html), including CMake 3.22 or newer.

Optional managed packages belong to the example's `main/idf_component.yml`.
Version constraints and dependency locks are reviewed independently of directory
layout. During this migration, direct package versions are fixed to the prior
verified lock versions; unused packages leave the selected dependency graph.
Use ESP-IDF Component Manager to update `dependencies.lock`; do not hand-edit
its resolution or hashes. A native configure step can change the lock, so
complete that step before freezing sources for final validation/evidence.

## Metadata, exports and checks

Target common inputs contain only common BSP build files and pins. Per-example
inputs contain the selected implementation and required public/private headers;
per-example dependencies contain its lock, managed manifest and selected shared
components. Existing `example_implementation` scopes expose only native
interfaces available in that example. Stable source assertions and operations
still point to the same public contracts.

Shared component `resource.json` files define their runtime source closure,
including native build files, headers, implementation and retained attribution.
Owner-local host tests and SDK doubles remain in the repository and are not
implicitly shipped as runtime application inputs.

`composition.py` checks profile syntax, local header/implementation closure,
Target declarations and native component-directory selection. After a successful
compiler command, the adapter checks `project_description.json` for the actual
BSP sources and requirements. A compiler exit of zero with the wrong composition
is a failed validation result. The actual component list is retained with each
native build result; registration counts alone do not establish firmware size,
build-time improvement or physical behavior.

Use `python3 codecraft.py context --target <id> --example <name>` to inspect
the chosen closure, and `new --target <id> --example <name> --output <new-path>`
to export it. The export carries the native profile, helper and validator in its
source graph and lock. Missing inputs fail rather than being silently omitted.

When adding an interface to an external application, import the required native
sources, headers and dependencies, then update that application's composition,
Target example scope and native manifests together. Review and explicitly
relock the application before building. An unchanged original reference-project
lock is not approval for new sources or dependencies.

For repository changes, run the composition tests, affected native and external
project builds, then the full gate:

```sh
python3 codecraft.py test --path platforms/esp-idf/tests/test_composition.py
python3 codecraft.py validate --target esp-idf/<board> --projects
python3 codecraft.py validate
```

## Compatibility and limits

The migration preserves public header names and signatures, driver/private-header
bytes, pins, SDK defaults and selected managed package versions. Implementation
paths move from `bsp/*.c` to `bsp/src/*.c`; scripts that compile source files
directly must use the new paths. Existing external projects retain their old
locked source and build behavior. A new export adopts the selected composition;
it does not automatically acquire every peripheral on the board.

Build success and host fault tests do not establish revision compatibility,
combined-peripheral resource budgets or on-device recovery. Those acceptance
items remain separately tracked in the optimization ledger.
