# Cloud domain and Provider policy optimization snapshot

Executed on 2026-11-18 (Asia/Shanghai). This slice closes **OPT-08** and
**OPT-09** from the existing 19-item ledger. It introduces no new optimization
items. The current contract is documented in
[Capability and Provider policy](../architecture/capability-provider-policy.md).

## Dependency direction

Neutral registry/loading primitives now live in skills/_shared/registry.py.
Both hardware and cloud domains consume them. The cloud domain no longer
imports or constructs the hardware Catalog. Public composition preserves lazy
optional Target validation, while direct domain callers must supply a resolver
for explicit Target context. Unknown Targets still fail.

The retained original-source experiment fails with hardware imports prohibited;
the changed implementation passes the same import guard. Cloud discovery also
runs under the guard. New registry files are declared in both native and cloud
graphs; clean exports include them and locked changes are rejected.

## Semantic contract and service policy

All four Capability/Provider contract versions are 2.0.0. Provider policy has
independent schema/version 1/1.0.0; standalone Skill packages remain 1.0.1 and
API v1, with unchanged complete inventories and import provenance.

Stable semantics, including no automatic retry, remain in Capability. Service
limits, declared quota, defaults and archived-output authentication values now
belong to the selected Provider. Schema fragments only narrow declared fields;
unknown constraints, weakened bounds, malformed defaults and incompatible
versions fail. Provider defaults require a Capability annotation and cannot
enable archival. Selection preserves raw configuration while preparation uses
effective configuration and exposes effective input/output schemas.

The actual isolated clients cover all four Capabilities and all operations,
including local/archived media. New boundary cases check ASR valid frequency
endpoints and duration plus invalid channels/sample width/rates/duration/size;
TTS maximum text/default voice and oversized rejection; image maximum prompt,
request dimensions and oversized rejection; and LLM token defaults/overrides.
The initial TTS test asserted the wrong request key; it was corrected to the
unchanged client's response_format field before the passing runs.

Policy-only fixture changes leave the semantic contract hash/version unchanged,
change the Provider graph identity and invalidate the external-project lock.
These fixtures do not establish interchangeability with a second real Provider.
Input byte/protocol checks remain in pinned clients; preparation makes no request
and reads no user credentials or input-file contents. Billing remains declared,
and image tests do not certify decoded output pixel dimensions.

Existing exported projects retain their locked implementation. The documented
2.0.0 migration requires new exports or explicitly reviewed runtime/metadata
updates; no old project or installed Skill is silently changed.

## Validation

The complete gate passed **181/181**: **140 static/host checks**, **33 native
build/source checks**, and **8 clean external-project builds**. All eight current
Target digests matched their receipts before evidence was recorded. No result
was failed or skipped. The before/after inventory retains all **126** previous
static/host check IDs and adds **14**, with no duplicate IDs. The unchanged
native test sources still execute **38 C test functions / 772 scenarios**.

The [retained host receipt](../../devices/sensecap-indicator/tests/logs/20261117194530Z-opt6-host-summary.json) includes exact check IDs,
test hashes, the original dependency failure, unchanged package fingerprints
and the preserved native scenario inventory.

| Target | Native checks | Clean external project | Source-matched record |
| --- | --- | --- | --- |
| esp-idf/respeaker-lite | 3 passed | passed | [record](../../devices/respeaker-lite/tests/records/build-610d4a0ac61a5198.json) |
| esp-idf/reterminal-e1001 | 4 passed | passed | [record](../../devices/reterminal-e1001/tests/records/build-47731ea349a0c076.json) |
| esp-idf/reterminal-e1002 | 4 passed | passed | [record](../../devices/reterminal-e1002/tests/records/build-7ce222096886d205.json) |
| esp-idf/reterminal-sticky | 3 passed | passed | [record](../../devices/reterminal-sticky/tests/records/build-6012deec2d5545ed.json) |
| esp-idf/sensecap-indicator | 3 passed | passed | [record](../../devices/sensecap-indicator/tests/records/build-0f50e21f9c976aef.json) |
| esp-idf/sensecap-watcher | 8 passed | passed | [record](../../devices/sensecap-watcher/tests/records/build-13deb297cc1a9f8a.json) |
| esp-idf/xiao-s3-147 | 3 passed | passed | [record](../../devices/xiao-s3-147/tests/records/build-ad05914dc22cd312.json) |
| linux/reterminal | 5 passed | passed | [record](../../devices/reterminal/tests/records/build-99920c5168693e0d.json) |

The ESP-IDF examples used v6.0.2-dirty with the pre-existing SDK changes retained;
the complete toolchain commit/change/compiler identity is in each record.
Linux checks used Python 3.14.6 and DTC 1.8.1, including overlay compilation.
No Linux hardware demo was executed. Arduino has no registered hardware Target.
README language pairs, English-only engineering guidance, references and
generated-view checks passed.

## Remaining acceptance

On-device verification and real cloud API execution were **not_run**. No device
writes, publishing, live billing observations or new hardware facts are part of
this slice. OPT-10 still needs a genuinely different Provider. Packaging,
public CLI and test-layout work remain open under OPT-11/12/13; adding common
policy tests to the current gate does not close those items. The ledger now has
**8 completed and 11 open** optimization items.
