# Host test ownership and execution

Use the public runner for discovery, focused host checks and the static gate:

```sh
python3 codecraft.py test --list
python3 codecraft.py test --path skills/_shared/tests
python3 codecraft.py test --path skills/_cloud/tests/test_protocol.py
python3 codecraft.py test --path platforms/esp-idf/components/codecraft_sht4x/tests
python3 codecraft.py test --path platforms/esp-idf/targets/sensecap-watcher/tests
python3 codecraft.py validate --static
```

Select checks using the [root validation policy](../../AGENTS.md#required-validation-and-delivery).
Documentation and host-only changes do not require native firmware builds when
native inputs/behavior are unchanged. Host tests may compile host fixtures; this
is separate from building board firmware. No-option `python3 codecraft.py validate`
includes all native Targets and clean project builds, so it is reserved for an
explicit full-build request or native changes affecting every Target.

`test` executes host tests only. `--path` selects a repository-relative test file
or owning directory. Empty, escaping or symlink selections fail; they never
report a successful empty suite. `--list` imports test modules and collects IDs
without running test bodies. Imports must therefore have no hardware, network
or repository-mutation side effects. Live services and physical acceptance
remain separate, explicitly scoped workflows.

## Owners

| Location | Responsibility |
| --- | --- |
| `skills/_shared/tests/` | Catalogs, source graph, generation, project exports/locks, evidence and cross-layer orchestration |
| `skills/_cloud/tests/` | Standalone installation/inventory, loopback protocols and reviewed release transactions |
| `skills/codecraft-validate/tests/` | Validation entry, public CLI, test discovery, language/link policy and unique test identities |
| `capabilities/<capability>/tests/`, `capabilities/_tests/` | Semantic contracts, Provider policy and actual prepared-client conformance |
| `platforms/<stack>/tests/` | Platform-wide adapter/registration contracts and shared native test support |
| `platforms/<stack>/components/<component>/tests/` | Shared native implementation and its C fixtures |
| `platforms/<stack>/targets/<device>/tests/` | BSP bindings, board-specific contracts and example callers |
| `devices/<device>/tests/` | Physical acceptance procedures, observations and retained evidence; not automatically run by the host gate |

The runner searches `test_*.py` recursively within the host test owners above.
Shared fixture/compiler helpers stay in their platform's tests directory and
use names such as `host_sensor.py`; C fixtures and SDK doubles are not Python
test entries. `fixtures/`, `stubs/`, build/cache and hidden directories are
excluded. Imported test functions/classes are not collected as new local cases.

Plain module-level `test_*` functions and local `unittest.TestCase` methods are
supported. unittest module/class/case fixtures retain their normal lifecycle;
subtest failures, fixture failures, skips and expected failures do not become
passing results. The JSON envelope and exit codes remain 0 for all passed,
1 for failures and 2 for skipped/unrun checks. A collection failure is reported
and does not silently discard neighboring suites. Asynchronous/pytest-style
fixtures are not an implicit supported test format.

## Coverage

Every discovered case has one owner-qualified ID. Collection rejects duplicate
aliases and reports import/fixture failures. Adding or moving tests must retain
behavioral coverage without forwarding wrappers or duplicate execution.
Release candidates run isolated client conformance in their own workflow; those
checks do not turn offline protocol results into live service acceptance.
