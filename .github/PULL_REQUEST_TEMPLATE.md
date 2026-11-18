## Problem and resulting behavior

<!-- Explain the concrete problem and the resulting behavior. -->

## Scope and provenance

- Device / revision / Target / Capability / Skill:
- Owning source and reviewer domain:
- Hardware sources and third-party licenses:
- Compatibility, wiring, partitions and persistent-data impact:
- Rollback:

## Validation

Use passed, failed, skipped, not_run or not_supported, with reasons. Do not count missing prerequisites as success.

| Check | Result | Command / evidence / limitations |
| --- | --- | --- |
| Static, knowledge and host (`validate --static`) | | |
| Native build per Target (`validate --target <id>`) | | |
| Clean generated project (`validate --target <id> --projects`) | | |
| Simulator, when registered | | |
| Physical device, with revision and cases | | |
| Complete software gate (`validate`) | | |

A build never establishes physical behavior. Reference retained device test records and list remaining unknowns.

## Contribution checklist

- [ ] Owning source records and generated views are aligned; generate --check passes.
- [ ] README language pairs agree; other engineering documents use English only; referenced files exist.
- [ ] Sources and licenses accompany hardware facts and assets.
- [ ] Maintenance, maturity and evidence status are recorded independently.
- [ ] No credentials, private data, temporary logs or firmware artifacts are included.
- [ ] No cloud runtime or unrelated user changes are included.
