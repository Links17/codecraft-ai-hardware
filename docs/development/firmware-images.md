# Firmware image delivery

Firmware merging is an optional post-build Platform operation. Device owns
sourced hardware facts; Target declares image support; Platform owns native
layout parsing, merging and verification; shared Skill code owns orchestration
and provenance. Cloud Capabilities are unchanged.

## Scope

The first delivery supports unsigned, unencrypted ESP-IDF factory BIN images.
Addresses and Flash settings come from native build metadata, with partition
and chip checks. Source packaging retains its existing meaning. Merge never
builds, flashes, uploads or changes a project lock.

Arduino image support, other output formats, signed/encrypted images and OTA
packages are separate follow-up work. Linux MCU image merging is unsupported.
Unsupported operations must return `not_supported`; missing tools return
`not_run`. Neither status is success.

## Implementation TODO

- [x] Bind each successful native build to source/lock identity, selected
  example/variant, actual tools, configuration and firmware input hashes.
  Invalidate the previous receipt before a new build attempt.
- [x] Implement ESP-IDF native layout discovery and factory BIN merging using
  the activated toolchain's esptool. Validate partitions, capacity, chip,
  security mode, overlaps and all native flash inputs.
- [x] Add public `firmware plan`, `firmware merge` and `firmware verify`
  operations, with immutable input snapshots, drift rejection and publication
  that never replaces an existing output.
- [x] Export the complete pipeline with independent applications and verify
  both repository and project builds use the same artifact contract.
- [x] Replace the board-local merge entry with the Platform operation, update
  references and Skills, and retain no compatibility forwarding entry.
- [x] Cover stale/failed builds, input/configuration drift, wrong selections,
  invalid layouts, unsupported profiles, missing tools and partial outputs
  with owner-local host tests.
- [x] Run the complete software gate and real merge/verify checks for every
  ESP-IDF Target, including Indicator DX/GX and clean exported applications.

## Deferred TODO

- [ ] Establish sourced Arduino bootloader/application layouts per Target
  before enabling firmware merge for those Targets.
- [ ] Add HEX/UF2 only with native-tool and output-verifier coverage.
- [ ] Specify signing, encryption and OTA contracts separately before enabling
  those image types.

## Acceptance

Identical inputs and tools produce identical image bytes. A failed build or
changed source, configuration, binary, variant or tool must not reuse a prior
successful plan. Outputs include a versioned manifest with hashes, Flash write
address/ranges, fill policy and build provenance. Image validation does not
establish physical verification or preservation of existing device data.

Factory images include padding between segments. Their write range can cover
data partitions even when no input file populated those partitions. Consumers
must use the declared factory purpose and ranges, not treat the result as an
application-only update.

Native references: [ESP-IDF merge-bin](https://docs.espressif.com/projects/esp-idf/en/release-v6.0/esp32/api-guides/tools/idf-py.html#merge-binaries-merge-bin)
and [esptool](https://docs.espressif.com/projects/esptool/en/latest/esp32/esptool/basic-commands.html#merge-binaries-for-flashing-merge-bin).

## Commands

Keep the Target's declared ESP-IDF environment activated. Repository builds:

```sh
python3 codecraft.py validate --target esp-idf/sensecap-watcher --example battery_status
python3 codecraft.py firmware plan --target esp-idf/sensecap-watcher --example battery_status --output .codecraft/plan.json
python3 codecraft.py firmware merge --plan .codecraft/plan.json --output .codecraft/release
python3 codecraft.py firmware verify .codecraft/release
```

For Indicator, pass --variant dx or --variant gx during build and planning.
Omitting the variant during planning selects the Target's declared build
default; it does not identify the physical panel.

An exported application uses `python3 codecraft.py build-project .`, followed
by `python3 codecraft.py firmware plan --project . --output .codecraft/plan.json`.
The merge and verify commands are identical. Plans and release directories
must be new paths. In-tree releases belong under .codecraft/ so they cannot
enter source locks or source packages.

The release contains firmware.bin and manifest.json. The directory is reserved
exclusively, validated bytes are linked into it, and the manifest is published
last as the completion marker. Existing outputs are never replaced; failed
publication removes only files created by that attempt. Hashes detect drift
and corruption; unsigned manifests do not establish authenticity.

Verification is offline (no network/device access) and requires the native
ESP-IDF/esptool installation. It does not need the original source tree or
build directory, and does not require old source hashes to match current code.
The CLI still needs a catalog containing the release's Target. Plan and merge
require the original current build and matching recorded tools.

Configured capacity is checked against known Device Flash limits. If the
physical capacity is unresolved, the manifest preserves physical_flash.status
as unknown while validating the configured memory map. In particular,
reTerminal Sticky's physical Flash size remains unresolved; merging does not
resolve that hardware evidence gap.

Build and merge operations for the same Target are mutually exclusive. A forcefully
terminated process can leave an empty .codecraft/firmware/locks/ directory entry.
Confirm that its operation has stopped before removing that exact lock directory;
a retry never removes another operation's lock automatically.

## Verified software scope

The 2026-11-18 local validation covers the following source-bound builds and
clean exported projects. Target links point to retained build evidence.

| Target | Native cases | Clean exports | Factory BIN cases |
| --- | ---: | ---: | ---: |
| [arduino/grove-beginner-kit](../../devices/grove-beginner-kit/tests/records/build-b6d185de42254228.json) | 11 | 1 | not_supported |
| [arduino/wio-terminal](../../devices/wio-terminal/tests/records/build-f08aae3381a622b3.json) | 10 | 1 | not_supported |
| [esp-idf/respeaker-lite](../../devices/respeaker-lite/tests/records/build-78941920b04c3845.json) | 3 | 1 | 3 |
| [esp-idf/reterminal-e1001](../../devices/reterminal-e1001/tests/records/build-965dea5578207f5c.json) | 4 | 1 | 4 |
| [esp-idf/reterminal-e1002](../../devices/reterminal-e1002/tests/records/build-b37c471ec80bb4cc.json) | 4 | 1 | 4 |
| [esp-idf/reterminal-sticky](../../devices/reterminal-sticky/tests/records/build-f689d09532522b37.json) | 3 | 1 | 3 |
| [esp-idf/sensecap-indicator](../../devices/sensecap-indicator/tests/records/build-75fc3647a8875c80.json) | 6 | 2 | 6 |
| [esp-idf/sensecap-watcher](../../devices/sensecap-watcher/tests/records/build-657556827f4f7b8a.json) | 8 | 1 | 8 |
| [esp-idf/xiao-s3-147](../../devices/xiao-s3-147/tests/records/build-af2c2542a26cae9d.json) | 3 | 1 | 3 |
| [linux/reterminal](../../devices/reterminal/tests/records/build-9cd1e59a31fa9df2.json) | 5 | 1 | not_supported |

Every factory BIN case passed plan, merge and offline verification. Repeating
the merge with the same inputs and recorded tools produced identical image
SHA-256 values for all 31 cases. The eight ESP-IDF clean exports also ran these
commands through their own copied public CLI.

Tools: ESP-IDF v6.0.2-dirty (existing local SDK changes recorded in evidence),
Xtensa GCC 15.2.0, esptool 5.3.1 and Python 3.14.6; Arduino CLI 1.5.0 with AVR
1.8.8 and Seeeduino SAMD 1.8.6; Linux overlay checks used dtc 1.8.1. The initial
full gate could not find the isolated Arduino core/libraries; selecting the
existing tool directories and rerunning both complete Target/project checks
resolved all 23 not_run results. Raw initial and retry reports remain separate.

No device flashing, physical verification or live cloud API calls were performed.
Factory image verification does not resolve unknown board revisions or physical
Flash capacity. Deferred formats/platforms above remain unsupported.
