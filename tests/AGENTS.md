# Tests and evidence

All repository-maintained tests, fixtures and mocks live under this directory.
Keep their ownership aligned with the source tree:

- `devices/<device>/targets/`: BSPs, board bindings and native examples.
- `platforms/<stack>/`: adapters, shared helpers and SDK doubles;
  `components/<component>/` contains shared component cases and fixtures.
- `capabilities/`: shared policy tests and client harness;
  `<capability>/` contains its contract and client conformance cases.
- `skills/`: `_shared/` for orchestration, `_cloud/` for standalone client and
  release tests, and `codecraft-validate/` for the public CLI and validation gate.

Read [test ownership and execution](../docs/development/testing.md) before
changing test placement, imports or discovery. That guide owns the commands and
runner rules. Never add a second test root, duplicate a fixture or retain a
forwarding test module. Production code and exported applications must not import
test support; the repository's isolated release checker may consume it explicitly.

## Device observations

Retain Device observations and source-bound evidence in `devices/<device>/`
relative to this directory:

- `observations.md`: dated, attributed physical observations when available.
- `records/`: structured build, simulator or physical evidence registered by
  `python3 codecraft.py record-evidence --file <record>`.
- `logs/`: sanitized original logs referenced by those records and their hashes.
- `targets/`: executable board-specific host tests, native fixtures and
  test doubles for devices/<device>/targets/.

The repository's `devices/AGENTS.md` is the device directory index. Each
`devices/<device>/AGENTS.md` owns the device knowledge and acceptance procedures;
reference material and assets stay with that Device. Do not duplicate those
maintained inputs here or infer a physical pass from a build or directory move.

Keep original log bytes, observed results, timestamps, toolchain, revision and
source identity intact. Correct storage locators when files move, recompute
content-derived record filenames and update links. A location change is not a
new observation. Never refresh a source digest to make old evidence current.

The public host runner discovers only targets/ within each Device's
test directory. Observations, records and logs are evidence, not runnable tests.
Device writes need the authorization specified in the root repository contract.
