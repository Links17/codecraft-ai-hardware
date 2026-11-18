# Source provenance

`NOTICE` records included third-party materials and their applicable notices.
Repository workflow ideas are not listed as included source code.

Source comments use `reference:` and “imported hardware reference” as neutral
labels for the external reference snapshot. These labels, including shortened
board-module and sdkconfig names, are identifiers rather than filesystem paths.
The inspected files and their SHA-256 hashes are listed in
[reference-snapshot.json](reference-snapshot.json). The snapshot commit describes
the files available at this audit; it does not establish the original import
revision. Copyright headers, licenses and recorded modifications remain intact.
Primary vendor URLs continue to identify vendor hardware documentation.

Changing a source label does not establish a new hardware observation or change
a pin, protocol, timing, toolchain or dependency. Historical evidence retains its
original source fingerprints and observations. A historical summary with a
normalized source label explicitly records that redaction and its original
artifact hash; any checksum referencing that artifact must match the retained
bytes. Fresh validation is required before changed sources regain verified
status.

History maintenance changes commit IDs. Old IDs in historical evidence describe
the original run and must not be relabelled as tests of rewritten source. New
validation records use current source fingerprints.
