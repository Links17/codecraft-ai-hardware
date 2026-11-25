# Host test ownership and execution

All repository-maintained tests, fixtures and mocks live under root tests/.
The subdirectories mirror the behavior owner; production modules retain their
implementation and reference material. Do not add module-local test directories,
forwarding wrappers or duplicate fixture copies. Dependencies' own tests inside
ignored SDK or package installations are not maintained repository suites.

Use the public runner for discovery, focused host checks and the static gate:

```sh
codecraft maintenance test --list
codecraft maintenance test --path tests/tools/codecraft
codecraft maintenance test --path tests/tools/skill_packages/test_protocol.py
codecraft maintenance test --path tests/platforms/esp-idf/components/codecraft_sht4x
codecraft maintenance test --path tests/devices/sensecap-watcher/targets
codecraft validate --static
```

The full host gate needs a C11 compiler, pthreads and `dtc` on PATH. Public CLI
integration tests compile the Linux overlay and validate locked application
exports. On Ubuntu, install `build-essential` and `device-tree-compiler`; the
contracts CI job installs both before discovery and execution.

Cloud protocol tests additionally need Python 3.11+, curl, Pillow and websockets.
Use a private virtual environment and install the exact package-owned pins through
tests/requirements.txt before test discovery or release checks:

```sh
export CODECRAFT_TEST_ENV="${TMPDIR:-/tmp}/codecraft-host-tests-env"
python3 -m venv "$CODECRAFT_TEST_ENV"
. "$CODECRAFT_TEST_ENV/bin/activate"
python3 -m pip install -r tests/requirements.txt
python3 -m pip check
```

These are host test dependencies, not MCU runtime or native toolchain requirements.
The onboarding suite compiles a temporary C/C++ authentication fixture only;
protocol tests use synthetic credentials and loopback services. Missing optional
client dependencies must be reported rather than silently skipping their cases.

Select checks using the [root validation policy](../../AGENTS.md#required-validation-and-delivery).
Documentation and host-only changes do not require native firmware builds when
native inputs/behavior are unchanged. Host tests may compile host fixtures; this
is separate from building board firmware. No-option `codecraft validate`
includes all native Targets and clean project builds, so it is reserved for an
explicit full-build request or native changes affecting every Target.

`test` executes host tests only; native host suites compile C fixtures and need
a C compiler. `validate --static` includes those suites. For a task that excludes
compilation, use discovery and explicitly selected Python-only checks; do not
report the host or complete gate as passed. `--path` selects a repository-relative test file
or owning directory. Empty, escaping or symlink selections fail; they never
report a successful empty suite. `--list` imports test modules and collects IDs
without running test bodies. Imports must therefore have no hardware, network
or repository-mutation side effects. Live services and physical acceptance
remain separate, explicitly scoped workflows.

## Owners

| Location | Responsibility |
| --- | --- |
| `tests/tools/cli/` | Rust creator CLI, standalone authoring, source locks and native orchestration; run `cargo test --locked --package codecraft` |
| `tests/tools/codecraft/` | Python conformance fixtures: Device Markdown parsing/validation, catalogs, source graph, generation, project exports/locks, evidence, public CLI, test discovery, documentation rules and cross-layer orchestration |
| `tests/tools/skill_packages/` | Standalone installation/inventory, loopback protocols and reviewed release transactions |
| `tests/skills/<skill-id>/` | Semantic contracts and direct standalone-client conformance |
| `tests/platforms/<stack>/` | Platform-wide adapter/registration contracts and shared native test support |
| `tests/platforms/<stack>/components/<component>/` | Shared native implementation and its C fixtures |
| `tests/devices/<device>/targets/` | BSP bindings, board-specific contracts and example callers |
| `tests/devices/<device>/{observations.md,records/,logs/}` | Dated observations, structured evidence and original logs; excluded from host discovery |

Device acceptance procedures are authored directly in
devices/<device>/AGENTS.md; see [Device document rules](device-documents.md). Its knowledge, implementation references and assets
remain in the device directory. The central evidence area follows
[tests/AGENTS.md](../../tests/AGENTS.md). Only each Device's targets/ subtree is a host-test owner; observations, records and logs are never collected as tests.

The runner searches `test_*.py` recursively within the host test owners above.
For Device tests, platform filtering reads devices/<device>/targets/target.json;
it does not infer the software stack from the test folder name. Missing or
mismatched Target ownership fails discovery. Platform filtering includes the
selected tests/platforms/<stack>/ tree and Device tests bound to that stack.
Shared Tool, Skill and contract tests run for every platform scope.
Shared fixture/compiler helpers live in tests/platforms/<stack>/ and
use names such as `host_sensor.py`; C fixtures and SDK doubles are not Python
test entries. `fixtures/`, `stubs/`, `mocks/`, build/cache and hidden directories are
excluded. Imported test functions/classes are not collected as new local cases.

Plain module-level `test_*` functions and local `unittest.TestCase` methods are
supported. unittest module/class/case fixtures retain their normal lifecycle;
subtest failures, fixture failures, skips and expected failures do not become
passing results. The JSON envelope and exit codes remain 0 for all passed,
1 for failures and 2 for skipped/unrun checks. A collection failure is reported
and does not silently discard neighboring suites. Asynchronous/pytest-style
fixtures are not an implicit supported test format.

## Coverage

CI selection cases in tests/tools/codecraft/test_ci.py cover native inputs across
all three platforms, shared resources, both sides of deletions/renames, internal
configuration links, new/removed Targets, event baselines and aggregate-job failures.
Run them with `codecraft maintenance test --path tests/tools/codecraft/test_ci.py`.
Public CLI tests also verify that repository-only CI commands are unavailable in
native application exports. See [CI selection](ci.md) for the workflow contract.

Every discovered case has one owner-qualified ID. Collection rejects duplicate
aliases and reports import/fixture failures. Adding or moving tests must retain
behavioral coverage without forwarding wrappers or duplicate execution.
Release candidates run isolated client conformance in their own workflow; those
checks do not turn offline protocol results into live service acceptance.
Their source graph explicitly includes the four per-Skill conformance directories and the shared standalone
protocol fixture. Native application exports include production dependencies
and cited Device observations, not test code, fixtures, records or logs.

## Rust CLI checks

Run `cargo fmt --all -- --check`, `cargo clippy --locked --package codecraft --all-targets -- -D warnings` and `cargo test --locked --package codecraft` after Rust changes.
The Python recursive runner does not discover Rust tests. CI compiles their explicit
Cargo targets only on cache misses and runs the cached executables against current
Device data on every run. `codecraft validate --static` runs repository Python
static/host checks; the Rust suite is a separate required CI job.
