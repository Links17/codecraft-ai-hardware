# Host test ownership and execution

Use the same public runner for discovery, focused checks and the complete gate:

```sh
python3 codecraft.py test --list
python3 codecraft.py test --path skills/_shared/tests
python3 codecraft.py test --path skills/_cloud/tests/test_protocol.py
python3 codecraft.py test --path platforms/esp-idf/components/codecraft_sht4x/tests
python3 codecraft.py test --path platforms/esp-idf/targets/sensecap-watcher/tests
python3 codecraft.py validate --static
python3 codecraft.py validate
```

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
| `skills/codecraft-validate/tests/` | Validation entry, public CLI, test discovery, language/link policy and migration inventory |
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

## OPT-13 migration

The [ID mapping](../../skills/codecraft-validate/tests/migrations/opt-13.json)
preserves all 133 entries from the previous complete gate as 156 explicit
cases. One entry previously wrapped nine unittest methods; those methods now
run directly. Multi-board native functions are split into their owning Target
paths. The same 772 C scenario invocations are retained, with 53 board/component
test functions instead of 38 combined functions. Shared compiler helpers do
not independently execute those scenarios.

Use the new owner path for focused invocation. The former
`python3 skills/_cloud/test_skills.py -v` command is replaced by
`python3 codecraft.py test --path skills/_cloud/tests/test_protocol.py`.
Historical result IDs and retained source hashes remain attributable to their
original snapshots; migration does not rewrite old evidence. The mapping
regression rejects missing or duplicate current IDs. New tests may be added
without deleting preserved cases or registering the same function twice.

Candidate release checks intentionally run their own isolated conformance
workflow. They use the same maintained protocol fixture at its new path; this
is distinct from duplicate discovery within a single host gate. No Skill
package bytes, API versions or native firmware behavior change in this layout
migration.
